"""Room detection and management.

Detects enclosed areas of floor tiles surrounded by walls/doors.
Each room is assigned a unique ID and tracked as a list of tiles.
Automatically manages roof tiles for enclosed rooms.

Supports multi-Z levels:
- Rooms can be detected on any Z-level
- Roofs are created on Z+1 for each room
- Fire escapes can be built on any level to access the next level up
"""

from typing import Dict, List, Set, Tuple
from collections import deque

Coord = Tuple[int, int]
Coord3D = Tuple[int, int, int]  # (x, y, z)

# Room storage: room_id -> {"tiles": [(x,y),...], "z": z_level, ...}
_ROOMS: Dict[int, dict] = {}

# Reverse lookup: (x, y, z) -> room_id
_TILE_TO_ROOM: Dict[Coord3D, int] = {}

# Roof layer: tracks which tiles have roofs
# Key: (x, y, z), Value: room_id that owns this roof
_ROOF_TILES: Dict[Coord3D, int] = {}

# Next room ID to assign
_next_room_id = 1

 # Dirty flag - set when construction completes to trigger re-detection
_needs_update = False


# ============================================================================
# Data-driven room classification and effects
# ============================================================================

# Each rule can define:
# - id: internal identifier
# - label: human-readable name (stored as room_type)
# - requires: {tile_type: min_count}
# - requires_any: [tile_type, ...] (optional)
# - forbid_any: [tile_type, ...] (optional)
# - min_stockpile_tiles: minimum number of tiles in stockpile zones (optional)
# - effects: arbitrary dict of room-level effects (stored on room data)
ROOM_RULES: List[dict] = [
    {
        "id": "Kitchen",
        "label": "Kitchen",
        # Requires at least one finished stove and one gutter slab in the room
        "requires": {"finished_stove": 1, "gutter_slab": 1},
        # Forbid any other crafting workstations in the same room
        "forbid_any": [
            "finished_salvagers_bench",
            "finished_gutter_forge",
            "finished_skinshop_loom",
            "finished_cortex_spindle",
        ],
        # Effects are a placeholder for future systemic bonuses
        "effects": {},
    },
    {
        "id": "SalvageBay",
        "label": "Salvage Bay",
        # Salvage station + at least 4 stockpile tiles in the room
        "requires": {"finished_salvagers_bench": 1},
        "min_stockpile_tiles": 4,
        # Keep it focused on salvage (no stove or other crafting benches)
        "forbid_any": [
            "finished_stove",
            "gutter_slab",
            "finished_gutter_forge",
            "finished_skinshop_loom",
            "finished_cortex_spindle",
        ],
        "effects": {},
    },
    {
        "id": "ForgeDen",
        "label": "Forge Den",
        # Gutter Forge + Gutter Slab = weapon/tool workshop
        "requires": {"finished_gutter_forge": 1, "gutter_slab": 1},
        # Avoid mixing with other major craft benches for now
        "forbid_any": [
            "finished_salvagers_bench",
            "finished_stove",
            "finished_skinshop_loom",
            "finished_cortex_spindle",
        ],
        "effects": {},
    },
    {
        "id": "SkinShop",
        "label": "Skin Shop",
        # Skinshop Loom + Gutter Slab = armor/loom room
        "requires": {"finished_skinshop_loom": 1, "gutter_slab": 1},
        "forbid_any": [
            "finished_salvagers_bench",
            "finished_stove",
            "finished_gutter_forge",
            "finished_cortex_spindle",
        ],
        "effects": {},
    },
    {
        "id": "CortexCell",
        "label": "Cortex Cell",
        # Cortex Spindle + Gutter Slab = implant/ripperdoc lab
        "requires": {"finished_cortex_spindle": 1, "gutter_slab": 1},
        "forbid_any": [
            "finished_salvagers_bench",
            "finished_stove",
            "finished_gutter_forge",
            "finished_skinshop_loom",
        ],
        "effects": {},
    },
    {
        "id": "CrashPad",
        "label": "Crash Pad",
        # Shared bedroom: at least one Crash Bed and two or more entrances
        "requires": {"crash_bed": 1},
        "min_exits": 2,
        "effects": {},
    },
    {
        "id": "CoffinNook",
        "label": "Coffin Nook",
        # Private bedroom: Crash Bed with a single entrance
        "requires": {"crash_bed": 1},
        "max_exits": 1,
        "effects": {},
    },
]


def _classify_room_from_contents(contents: Dict[str, int], tiles: List[Coord], z: int, grid, entrances: List[Coord]) -> tuple[str | None, Dict[str, float]]:
    """Apply ROOM_RULES to determine room type and effects.

    Returns (room_type, effects_dict).
    room_type is a human-readable label or None if no rule matches.
    effects_dict is the rule's effects mapping (may be empty).
    """
    stockpile_tiles: int | None = None
    exit_count = len(entrances)
    for rule in ROOM_RULES:
        requires: Dict[str, int] = rule.get("requires", {}) or {}
        if any(contents.get(tile, 0) < amount for tile, amount in requires.items()):
            continue

        requires_any = rule.get("requires_any")
        if requires_any:
            if not any(contents.get(tile, 0) > 0 for tile in requires_any):
                continue

        forbid_any = rule.get("forbid_any", []) or []
        if any(contents.get(tile, 0) > 0 for tile in forbid_any):
            continue

        min_stockpile = rule.get("min_stockpile_tiles")
        if min_stockpile:
            if stockpile_tiles is None:
                # Lazily compute number of stockpile tiles in this room
                try:
                    import zones
                    count = 0
                    for tx, ty in tiles:
                        if zones.is_stockpile_zone(tx, ty, z):
                            count += 1
                    stockpile_tiles = count
                except Exception:
                    stockpile_tiles = 0
            if stockpile_tiles < min_stockpile:
                continue

        min_exits = rule.get("min_exits")
        if min_exits is not None and exit_count < min_exits:
            continue

        max_exits = rule.get("max_exits")
        if max_exits is not None and exit_count > max_exits:
            continue

        label = rule.get("label") or rule.get("id")
        effects = rule.get("effects", {}) or {}
        return label, effects

    return None, {}


def get_room_at(x: int, y: int, z: int = 0) -> int | None:
    """Get the room ID for a tile, or None if not in a room."""
    return _TILE_TO_ROOM.get((x, y, z))


def get_room_tiles(room_id: int) -> List[Coord]:
    """Get all tiles belonging to a room (2D coords)."""
    room = _ROOMS.get(room_id)
    if room is None:
        return []
    return room.get("tiles", [])


def get_room_z(room_id: int) -> int | None:
    """Get the Z-level of a room."""
    room = _ROOMS.get(room_id)
    if room is None:
        return None
    return room.get("z", 0)


def get_all_rooms() -> Dict[int, dict]:
    """Get all rooms for debug/rendering."""
    return _ROOMS.copy()


def has_roof(x: int, y: int, z: int = 1) -> bool:
    """Check if a tile has a roof at the specified Z-level."""
    return (x, y, z) in _ROOF_TILES


def get_roof_room(x: int, y: int, z: int = 1) -> int | None:
    """Get the room ID that owns the roof at (x, y, z), or None."""
    return _ROOF_TILES.get((x, y, z))


def get_all_roof_tiles() -> Dict[Coord3D, int]:
    """Get all roof tiles for rendering (3D coords)."""
    return _ROOF_TILES.copy()


def _add_roof_for_room(room_id: int, tiles: List[Coord], room_z: int, grid=None) -> None:
    """Add roof tiles for a room.
    
    Creates roof on Z+1 level for a room on Z level.
    Only sets roof on empty tiles - preserves any existing structures or allowed tiles.
    
    Args:
        room_id: The room's ID
        tiles: List of (x, y) tiles that make up the room
        room_z: The Z-level the room is on
        grid: The game grid (optional)
    """
    roof_z = room_z + 1
    
    # Check if we can create roofs at this level
    if grid is not None and roof_z >= grid.depth:
        print(f"[Rooms] Cannot add roof for room {room_id} - Z={roof_z} exceeds grid depth")
        return
    
    for coord in tiles:
        _ROOF_TILES[(coord[0], coord[1], roof_z)] = room_id
        # Set roof tile on Z+1 level, but ONLY if the tile is empty
        # This preserves: walls, doors, floors, roof_access, fire_escape_platform, etc.
        if grid is not None:
            tile_above = grid.get_tile(coord[0], coord[1], z=roof_z)
            if tile_above == "empty":
                grid.set_tile(coord[0], coord[1], "roof", z=roof_z)
    print(f"[Rooms] Added roof over room {room_id} on Z={roof_z} ({len(tiles)} tiles)")


def _remove_roof_for_room(room_id: int, grid=None) -> None:
    """Remove all roof tiles belonging to a room.
    
    Clears roof tiles at their stored Z-level.
    Only clears actual roof tiles - preserves any structures or allowed tiles.
    """
    # Roof tiles are stored as (x, y, z) 3D coords
    tiles_to_remove = [coord for coord, rid in _ROOF_TILES.items() if rid == room_id]
    for coord in tiles_to_remove:
        x, y, z = coord
        del _ROOF_TILES[coord]
        # Clear roof tile, but ONLY if it's actually a roof tile
        # This preserves: walls, doors, floors, roof_access, fire_escape_platform, etc.
        if grid is not None:
            tile = grid.get_tile(x, y, z)
            if tile == "roof":
                grid.set_tile(x, y, "empty", z=z)
    if tiles_to_remove:
        print(f"[Rooms] Removed roof from room {room_id} ({len(tiles_to_remove)} tiles)")


def _get_neighbors(x: int, y: int) -> List[Coord]:
    """Get 4-directional neighbors."""
    return [(x-1, y), (x+1, y), (x, y-1), (x, y+1)]


def _get_all_neighbors(x: int, y: int) -> List[Coord]:
    """Get 8-directional neighbors (including diagonals)."""
    return [
        (x-1, y), (x+1, y), (x, y-1), (x, y+1),  # Cardinal
        (x-1, y-1), (x+1, y-1), (x-1, y+1), (x+1, y+1)  # Diagonal
    ]


def _is_enclosing_tile(grid, x: int, y: int, z: int = 0) -> bool:
    """Check if a tile acts as a room boundary (wall, door, or out of bounds)."""
    if not grid.in_bounds(x, y, z):
        return True  # Out of bounds counts as enclosed
    
    tile = grid.get_tile(x, y, z)
    # Walls, doors, windows, and window_tiles form room boundaries
    # window_tile is a passable wall (fire escape window) but still counts as wall for room detection
    # finished_window is a regular window that blocks movement but encloses rooms
    return tile in ("wall", "finished_wall", "wall_advanced", "finished_wall_advanced", "door", "window_tile", "window", "finished_window")


def _is_interior_tile(grid, x: int, y: int, z: int = 0) -> bool:
    """Check if a tile can be part of a room's interior.
    
    Room interiors can be:
    - Any walkable tile (grass, empty, finished_floor, roof_access, etc.)
    - NOT walls, doors, windows (those are boundaries)
    """
    if not grid.in_bounds(x, y, z):
        return False
    tile = grid.get_tile(x, y, z)
    # Boundary tiles are NOT interior
    if tile in ("wall", "finished_wall", "wall_advanced", "finished_wall_advanced", 
                "door", "window_tile", "window", "finished_window"):
        return False
    # Everything else can be interior (grass, empty, floor, roof_access, etc.)
    return True


def _is_entrance_tile(grid, x: int, y: int, z: int = 0) -> bool:
    """Check if a tile is an entrance (door or window - required for room detection).
    
    Doors and windows both count as valid entrances for a room.
    Windows are used for fire escape access points.
    """
    if not grid.in_bounds(x, y, z):
        return False
    tile = grid.get_tile(x, y, z)
    # Doors and windows (including fire escape window_tile) count as entrances
    return tile in ("door", "window", "finished_window", "window_tile")


def _flood_fill_room(grid, start_x: int, start_y: int, z: int, visited: Set[Coord]) -> Tuple[List[Coord], List[Coord], bool, bool]:
    """
    Flood fill from an interior tile to find connected interior tiles and boundary.
    
    Args:
        grid: The game grid
        start_x, start_y: Starting position
        z: Z-level to scan
        visited: Set of already visited tiles (modified in place)
    
    Returns:
        (interior_tiles, boundary_tiles, is_enclosed, has_entrance): 
        - interior_tiles: List of interior tiles (2D coords)
        - boundary_tiles: List of wall/door tiles forming the room boundary (2D coords)
        - is_enclosed: Whether the room is fully enclosed by walls/doors
        - has_entrance: Whether the boundary contains at least one entrance (door or window)
    """
    interior_tiles: List[Coord] = []
    boundary_tiles: Set[Coord] = set()  # Use set to avoid duplicates
    is_enclosed = True
    has_entrance = False
    queue = deque([(start_x, start_y)])
    local_visited: Set[Coord] = set()
    
    while queue:
        x, y = queue.popleft()
        
        if (x, y) in local_visited:
            continue
        local_visited.add((x, y))
        
        if not grid.in_bounds(x, y, z):
            # Reached edge of map without hitting a wall - not enclosed
            is_enclosed = False
            continue
        
        if _is_interior_tile(grid, x, y, z):
            interior_tiles.append((x, y))
            visited.add((x, y))
            
            # Check cardinal neighbors for flood fill
            for nx, ny in _get_neighbors(x, y):
                if (nx, ny) not in local_visited:
                    queue.append((nx, ny))
            
            # Check ALL neighbors (including diagonals) for boundary/corner tiles
            for nx, ny in _get_all_neighbors(x, y):
                if _is_enclosing_tile(grid, nx, ny, z):
                    boundary_tiles.add((nx, ny))
                    if _is_entrance_tile(grid, nx, ny, z):
                        has_entrance = True
        elif _is_enclosing_tile(grid, x, y, z):
            # Hit a wall/door/window - track it as boundary tile
            boundary_tiles.add((x, y))
            if _is_entrance_tile(grid, x, y, z):
                has_entrance = True
        else:
            # Hit something unexpected - not enclosed
            is_enclosed = False
    
    return interior_tiles, list(boundary_tiles), is_enclosed, has_entrance


def detect_rooms(grid) -> None:
    """
    Scan the grid and detect all rooms on ALL Z-levels.
    
    A room is defined as:
    - An enclosed space (surrounded by walls/doors/windows)
    - With at least one entrance (door or window)
    
    No floor requirement - rooms can be on grass, roof_access, or any interior tile.
    Also manages roof tiles - adds roofs on Z+1 for new rooms, removes for destroyed rooms.
    
    Call this after construction completes to update room data.
    """
    global _next_room_id
    
    # Store old rooms for comparison
    old_rooms = _ROOMS.copy()
    old_tile_to_room = _TILE_TO_ROOM.copy()
    old_room_ids = set(old_rooms.keys())
    
    # Clear current room data
    _ROOMS.clear()
    _TILE_TO_ROOM.clear()
    
    # Reset grid env_data for room-related fields before re-detecting
    # This ensures hover/tooltips and AI see up-to-date room info.
    for z_level in range(grid.depth):
        for y in range(grid.height):
            for x in range(grid.width):
                # Clear room assignment
                grid.set_env_param(x, y, z_level, "room_id", None)
                # Recompute base tile-level exits (adjacent walkable tiles)
                base_exits = grid.calculate_exit_count(x, y, z_level)
                grid.set_env_param(x, y, z_level, "exit_count", base_exits)
    
    # Track which rooms are new vs continuing
    new_room_ids: Set[int] = set()
    
    # Scan all Z-levels (except the top one - can't have roof above max Z)
    for z in range(grid.depth - 1):
        # Track visited interior tiles per Z-level
        visited: Set[Coord] = set()
        
        # Scan all tiles for interior tiles on this Z-level
        for y in range(grid.height):
            for x in range(grid.width):
                if (x, y) in visited:
                    continue
                
                if _is_interior_tile(grid, x, y, z):
                    # Found an unvisited interior tile - flood fill to find potential room
                    interior_tiles, boundary_tiles, is_enclosed, has_entrance = _flood_fill_room(grid, x, y, z, visited)
                    
                    # Room requires: enclosed + has entrance (door/window) + has interior tiles
                    if is_enclosed and has_entrance and interior_tiles:
                        # This is a valid room
                        room_id = _next_room_id
                        _next_room_id += 1
                        
                        # Compute entrances (doors/windows) on the room boundary
                        entrances: List[Coord] = []
                        for bx, by in boundary_tiles:
                            if _is_entrance_tile(grid, bx, by, z):
                                entrances.append((bx, by))

                        # Collect simple contents by tile type for interior tiles
                        contents: Dict[str, int] = {}
                        for tx, ty in interior_tiles:
                            tile_type = grid.get_tile(tx, ty, z)
                            if tile_type is None:
                                continue
                            contents[tile_type] = contents.get(tile_type, 0) + 1
                        
                        # Classify room type and compute room-level effects from contents
                        room_type, room_effects = _classify_room_from_contents(contents, interior_tiles, z, grid, entrances)
                        
                        # Store room with Z-level info, entrances, contents, classification, and effects
                        _ROOMS[room_id] = {
                            "tiles": interior_tiles,
                            "z": z,
                            "entrances": entrances,
                            "contents": contents,
                            "room_type": room_type,
                            "effects": room_effects,
                        }
                        for tx, ty in interior_tiles:
                            _TILE_TO_ROOM[(tx, ty, z)] = room_id
                            # Update env data so hover/AI can see room membership
                            grid.set_env_param(tx, ty, z, "room_id", room_id)
                            # For interior tiles, use room-level exit count (number of entrances)
                            grid.set_env_param(tx, ty, z, "exit_count", len(entrances))
                        
                        new_room_ids.add(room_id)
                        z_info = f" on Z={z}" if z > 0 else ""
                        print(f"[Rooms] Created room {room_id} with {len(interior_tiles)} tile(s){z_info}")
                        
                        # Add roof for this room on Z+1 - covers interior AND boundary walls/doors
                        all_roof_tiles = interior_tiles + boundary_tiles
                        _add_roof_for_room(room_id, all_roof_tiles, z, grid)
    
    # Find destroyed rooms and remove their roofs
    destroyed_rooms: Set[int] = set()
    for coord, old_room_id in old_tile_to_room.items():
        if coord not in _TILE_TO_ROOM:
            # This tile lost its room
            if old_room_id not in destroyed_rooms:
                print(f"[Rooms] Room {old_room_id} destroyed (tile {coord} no longer enclosed)")
                destroyed_rooms.add(old_room_id)
                # Remove roof for destroyed room
                _remove_roof_for_room(old_room_id, grid)


def mark_rooms_dirty() -> None:
    """Mark rooms as needing re-detection. Call when construction completes."""
    global _needs_update
    _needs_update = True


def update_rooms(grid) -> None:
    """
    Update room detection if needed.
    Only re-detects when marked dirty (after construction completes).
    """
    global _needs_update
    if _needs_update:
        detect_rooms(grid)
        _needs_update = False


def get_room_count() -> int:
    """Get the number of active rooms."""
    return len(_ROOMS)
