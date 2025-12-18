"""Room detection and management - Hybrid Event-Driven System.

Room Types:
- COVERED: Has roof above + enclosed by walls/doors. Open walls OK if has roof.
  Used for: Salvager's Bench, Generator
- ENCLOSED: Fully walled (doors/windows OK) + floor + roof.
  Used for: Stove, advanced workstations

Detection Strategy:
- Rooms are detected via flood-fill when tiles change (wall/door built/removed)
- Changes are BATCHED: mark dirty during tick, process ALL at end of tick
- This gives RimWorld-like behavior with Factorio-like performance

How it works:
1. Tile changes (wall built, door placed, etc.) → mark_tile_dirty(x, y, z)
2. End of tick → process_dirty_rooms(grid) merges dirty tiles into regions
3. Each region gets ONE flood-fill pass to detect/update rooms
4. Rooms auto-subdivide when internal walls are added
5. Rooms auto-merge when walls are removed

Supports multi-Z levels and arbitrary room shapes (L, U, etc.)
"""

from typing import Dict, List, Set, Tuple, Optional
from collections import deque
from enum import Enum


class RoomType(Enum):
    """Room enclosure types."""
    NONE = "none"           # Not a room (outdoors)
    COVERED = "covered"     # Has roof above, enclosed by walls/doors
    ENCLOSED = "enclosed"   # Fully walled + floor + roof


Coord = Tuple[int, int]
Coord3D = Tuple[int, int, int]  # (x, y, z)

# Room storage: room_id -> {"tiles": [(x,y),...], "z": z_level, ...}
_ROOMS: Dict[int, dict] = {}

# Reverse lookup: (x, y, z) -> room_id
_TILE_TO_ROOM: Dict[Coord3D, int] = {}

# Roof layer: tracks which tiles have roofs
# Key: (x, y, z), Value: room_id that owns this roof (-1 for manual placement)
_ROOF_TILES: Dict[Coord3D, int] = {}

# Next room ID to assign
_next_room_id = 1

# =============================================================================
# DIRTY TILE TRACKING - Batched room updates
# =============================================================================

# Tiles that changed this tick - will be processed at end of tick
_DIRTY_TILES: Set[Coord3D] = set()

# Maximum flood-fill size to prevent runaway on huge open areas
MAX_ROOM_TILES = 200


def mark_tile_dirty(x: int, y: int, z: int) -> None:
    """Mark a tile as needing room recalculation.
    
    Call this when:
    - Wall/door is built or demolished
    - Roof is placed or removed
    - Any structural change that could affect room boundaries
    
    The actual recalculation happens at end of tick via process_dirty_rooms().
    """
    _DIRTY_TILES.add((x, y, z))


def process_dirty_rooms(grid) -> None:
    """Process all dirty tiles and update affected rooms.
    
    Call this ONCE at the end of each tick (not per tile change).
    Merges nearby dirty tiles into regions and runs flood-fill once per region.
    """
    global _DIRTY_TILES
    
    if not _DIRTY_TILES:
        return
    
    # Copy and clear dirty set
    dirty = _DIRTY_TILES.copy()
    _DIRTY_TILES.clear()
    
    print(f"[Room] Processing {len(dirty)} dirty tiles: {list(dirty)[:5]}...")
    
    # Group dirty tiles by Z-level
    by_z: Dict[int, Set[Coord]] = {}
    for x, y, z in dirty:
        if z not in by_z:
            by_z[z] = set()
        by_z[z].add((x, y))
    
    # Process each Z-level
    for z, tiles_2d in by_z.items():
        _process_dirty_region(grid, tiles_2d, z)


def _process_dirty_region(grid, dirty_tiles: Set[Coord], z: int) -> None:
    """Process dirty tiles on a single Z-level.
    
    Expands each dirty tile to a small region, merges overlapping regions,
    then runs flood-fill to detect rooms in the affected area.
    """
    if not dirty_tiles:
        return
    
    # Expand dirty tiles to influence region (5x5 around each)
    expanded: Set[Coord] = set()
    for x, y in dirty_tiles:
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                nx, ny = x + dx, y + dy
                if grid.in_bounds(nx, ny, z):
                    expanded.add((nx, ny))
    
    # Find rooms that might be affected (tiles in expanded region)
    affected_room_ids: Set[int] = set()
    for x, y in expanded:
        room_id = _TILE_TO_ROOM.get((x, y, z))
        if room_id is not None:
            affected_room_ids.add(room_id)
    
    # Also check tiles adjacent to dirty tiles for rooms
    for x, y in dirty_tiles:
        for nx, ny in _get_neighbors(x, y):
            room_id = _TILE_TO_ROOM.get((nx, ny, z))
            if room_id is not None:
                affected_room_ids.add(room_id)
    
    # Clear old room data for affected tiles
    tiles_to_clear: Set[Coord] = set()
    for room_id in affected_room_ids:
        room = _ROOMS.get(room_id)
        if room and room.get("z") == z:
            tiles_to_clear.update(room.get("tiles", []))
    
    # Add expanded region to tiles to reprocess
    tiles_to_clear.update(expanded)
    
    # Clear mappings for these tiles
    for x, y in tiles_to_clear:
        if (x, y, z) in _TILE_TO_ROOM:
            del _TILE_TO_ROOM[(x, y, z)]
    
    # Remove affected rooms
    for room_id in affected_room_ids:
        if room_id in _ROOMS:
            _remove_roof_for_room(room_id, grid)
            del _ROOMS[room_id]
    
    # Now flood-fill from interior tiles in the region to find new rooms
    visited: Set[Coord] = set()
    
    for x, y in tiles_to_clear:
        if (x, y) in visited:
            continue
        
        if _is_interior_tile(grid, x, y, z):
            # Found an unvisited interior tile - flood fill to find potential room
            interior_tiles, boundary_tiles, is_enclosed, has_entrance = _flood_fill_room(
                grid, x, y, z, visited, max_tiles=MAX_ROOM_TILES
            )
            
            # Debug output
            if interior_tiles and len(interior_tiles) < 50:  # Only log small areas
                print(f"[Room Debug] Flood-fill from ({x},{y},z={z}): {len(interior_tiles)} tiles, enclosed={is_enclosed}, entrance={has_entrance}")
            
            # Room requires: enclosed + has entrance (door/window) + has interior tiles
            # Also need roof above for it to count as a room
            if is_enclosed and has_entrance and interior_tiles:
                # Check if room has roof
                has_roof = _check_tiles_have_roof(grid, interior_tiles, z)
                if has_roof:
                    _create_room_from_tiles(grid, interior_tiles, boundary_tiles, z)
                else:
                    print(f"[Room Debug] Area has no roof - not creating room")


def _check_tiles_have_roof(grid, tiles: List[Coord], z: int) -> bool:
    """Check if all tiles have roof above."""
    for x, y in tiles:
        if not _has_roof_above(grid, x, y, z):
            return False
    return True


def _create_room_from_tiles(grid, interior_tiles: List[Coord], boundary_tiles: List[Coord], z: int) -> int:
    """Create a room from flood-fill results."""
    global _next_room_id
    
    room_id = _next_room_id
    _next_room_id += 1
    
    # Find entrances (doors/windows) on the boundary
    entrances: List[Coord] = []
    for bx, by in boundary_tiles:
        if _is_entrance_tile(grid, bx, by, z):
            entrances.append((bx, by))
    
    # Collect contents by tile type
    contents: Dict[str, int] = {}
    for tx, ty in interior_tiles:
        tile_type = grid.get_tile(tx, ty, z)
        if tile_type:
            contents[tile_type] = contents.get(tile_type, 0) + 1
    
    # Determine room enclosure type
    has_floor = all(_has_floor(grid, tx, ty, z) for tx, ty in interior_tiles)
    room_type_enum = RoomType.ENCLOSED if has_floor else RoomType.COVERED
    
    # Classify room type based on contents
    room_type, room_effects = _classify_room_from_contents(contents, interior_tiles, z, grid, entrances)
    
    # Store room
    _ROOMS[room_id] = {
        "tiles": interior_tiles,
        "z": z,
        "boundary": boundary_tiles,
        "room_type_enum": room_type_enum,
        "room_type": room_type,
        "entrances": entrances,
        "contents": contents,
        "effects": room_effects,
    }
    
    # Update tile-to-room mapping
    for tx, ty in interior_tiles:
        _TILE_TO_ROOM[(tx, ty, z)] = room_id
        # Update env data
        grid.set_env_param(tx, ty, z, "room_id", room_id)
        grid.set_env_param(tx, ty, z, "exit_count", len(entrances))
    
    # Add roof for this room
    all_roof_tiles = interior_tiles + boundary_tiles
    _add_roof_for_room(room_id, all_roof_tiles, z, grid)
    
    enclosure_str = "enclosed" if room_type_enum == RoomType.ENCLOSED else "covered"
    type_str = f" [{room_type}]" if room_type else ""
    print(f"[Room] Created room {room_id}: {len(interior_tiles)} tiles, {len(entrances)} exits, {enclosure_str}{type_str}")
    
    return room_id


# Legacy compatibility - these now just mark dirty
def mark_rooms_dirty() -> None:
    """Legacy: Mark rooms as needing update. Now a no-op - use mark_tile_dirty instead."""
    pass


def update_rooms(grid) -> None:
    """Legacy: Process room updates. Now calls process_dirty_rooms."""
    process_dirty_rooms(grid)


def rooms_need_update() -> bool:
    """Legacy: Check if rooms need update."""
    return len(_DIRTY_TILES) > 0


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


def reclassify_room(room_id: int, grid) -> None:
    """Reclassify a room based on its current contents.
    
    Call this when anything changes inside a room (workstation built,
    furniture placed, etc.) to update the room type (Kitchen, etc.).
    """
    room = _ROOMS.get(room_id)
    if room is None:
        return
    
    tiles = room.get("tiles", [])
    z = room.get("z", 0)
    entrances = room.get("entrances", [])
    
    if not tiles:
        return
    
    # Collect contents by tile type
    contents: Dict[str, int] = {}
    for tx, ty in tiles:
        tile_type = grid.get_tile(tx, ty, z)
        if tile_type:
            contents[tile_type] = contents.get(tile_type, 0) + 1
    
    # Classify and update
    room_type, room_effects = _classify_room_from_contents(contents, tiles, z, grid, entrances)
    
    old_type = room.get("room_type")
    room["room_type"] = room_type
    room["effects"] = room_effects
    room["contents"] = contents
    
    if room_type and room_type != old_type:
        print(f"[Room] Room {room_id} classified as: {room_type}")


def reclassify_room_at(x: int, y: int, z: int, grid) -> None:
    """Reclassify the room containing tile (x, y, z), if any.
    
    Call this after any construction completes to update room classification.
    """
    room_id = get_room_at(x, y, z)
    if room_id is not None:
        reclassify_room(room_id, grid)


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


def _flood_fill_room(grid, start_x: int, start_y: int, z: int, visited: Set[Coord], max_tiles: int = 200) -> Tuple[List[Coord], List[Coord], bool, bool]:
    """
    Flood fill from an interior tile to find connected interior tiles and boundary.
    
    Args:
        grid: The game grid
        start_x, start_y: Starting position
        z: Z-level to scan
        visited: Set of already visited tiles (modified in place)
        max_tiles: Maximum interior tiles before giving up (prevents runaway on open areas)
    
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
        
        # Check max tiles limit
        if len(interior_tiles) >= max_tiles:
            is_enclosed = False  # Too big, treat as not enclosed
            break
        
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
    DISABLED: Old auto-room detection system.
    Manual room system (room_system.py) is now used instead.
    
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
    """DISABLED: Old auto-room detection system. Manual room system (room_system.py) is now used instead."""
    # Disabled - manual room system is now used
    pass


def update_rooms(grid) -> None:
    """
    DISABLED: Old auto-room detection system.
    Manual room system (room_system.py) is now used instead.
    
    Update room detection if needed.
    Only re-detects when marked dirty (after construction completes).
    """
    # Disabled - manual room system is now used
    pass


def get_room_count() -> int:
    """Get the number of active rooms."""
    return len(_ROOMS)


# =============================================================================
# On-Demand Room Type Checking
# =============================================================================
# These functions check room type at a specific tile WITHOUT full map scanning.
# Used when placing workstations, colonist actions, etc.

def _has_roof_above(grid, x: int, y: int, z: int) -> bool:
    """Check if tile has a roof on Z+1."""
    roof_z = z + 1
    if roof_z >= grid.depth:
        return False
    # Check our roof tracking OR actual roof tile
    if (x, y, roof_z) in _ROOF_TILES:
        return True
    tile_above = grid.get_tile(x, y, roof_z)
    return tile_above == "roof"


def _has_floor(grid, x: int, y: int, z: int) -> bool:
    """Check if tile has a floor."""
    tile = grid.get_tile(x, y, z)
    return tile in ("finished_floor", "floor", "roof_access", "roof_floor")


def _is_wall_or_corner(grid, x: int, y: int, z: int) -> bool:
    """Check if tile is a wall (can serve as corner post)."""
    if not grid.in_bounds(x, y, z):
        return False
    tile = grid.get_tile(x, y, z)
    return tile in ("wall", "finished_wall", "wall_advanced", "finished_wall_advanced")


def _find_room_bounds(grid, x: int, y: int, z: int, max_search: int = 20) -> Optional[Tuple[int, int, int, int]]:
    """Find the bounding box of enclosing tiles around a tile.
    
    Searches outward from (x, y) to find enclosing tiles (walls, doors, windows).
    Returns (min_x, min_y, max_x, max_y) of the bounds, or None if not enclosed.
    """
    min_x = max_x = x
    min_y = max_y = y
    
    # Search left for any enclosing tile
    for dx in range(1, max_search):
        if _is_enclosing_tile(grid, x - dx, y, z):
            min_x = x - dx
            break
    else:
        return None  # No enclosing tile found
    
    # Search right
    for dx in range(1, max_search):
        if _is_enclosing_tile(grid, x + dx, y, z):
            max_x = x + dx
            break
    else:
        return None
    
    # Search up
    for dy in range(1, max_search):
        if _is_enclosing_tile(grid, x, y - dy, z):
            min_y = y - dy
            break
    else:
        return None
    
    # Search down
    for dy in range(1, max_search):
        if _is_enclosing_tile(grid, x, y + dy, z):
            max_y = y + dy
            break
    else:
        return None
    
    return (min_x, min_y, max_x, max_y)


def _check_four_corners(grid, bounds: Tuple[int, int, int, int], z: int) -> bool:
    """Check if all 4 corners of bounds have enclosing tiles (walls, doors, windows)."""
    min_x, min_y, max_x, max_y = bounds
    corners = [
        (min_x, min_y),
        (max_x, min_y),
        (min_x, max_y),
        (max_x, max_y),
    ]
    # For COVERED rooms, corners just need to be enclosing tiles
    return all(_is_enclosing_tile(grid, cx, cy, z) for cx, cy in corners)


def _check_fully_enclosed(grid, bounds: Tuple[int, int, int, int], z: int) -> bool:
    """Check if all edges of bounds are walled (doors/windows OK)."""
    min_x, min_y, max_x, max_y = bounds
    
    # Check top and bottom edges
    for x in range(min_x, max_x + 1):
        if not _is_enclosing_tile(grid, x, min_y, z):
            return False
        if not _is_enclosing_tile(grid, x, max_y, z):
            return False
    
    # Check left and right edges
    for y in range(min_y, max_y + 1):
        if not _is_enclosing_tile(grid, min_x, y, z):
            return False
        if not _is_enclosing_tile(grid, max_x, y, z):
            return False
    
    return True


def _check_has_floor(grid, bounds: Tuple[int, int, int, int], z: int) -> bool:
    """Check if interior of bounds has floor tiles."""
    min_x, min_y, max_x, max_y = bounds
    
    # Check interior tiles (excluding walls)
    for y in range(min_y + 1, max_y):
        for x in range(min_x + 1, max_x):
            if not _has_floor(grid, x, y, z):
                return False
    return True


def _check_has_roof(grid, bounds: Tuple[int, int, int, int], z: int) -> bool:
    """Check if interior of bounds has roof above."""
    min_x, min_y, max_x, max_y = bounds
    
    # Check interior tiles have roof
    for y in range(min_y + 1, max_y):
        for x in range(min_x + 1, max_x):
            if not _has_roof_above(grid, x, y, z):
                return False
    return True


def get_room_type_at(grid, x: int, y: int, z: int = 0, debug: bool = False) -> RoomType:
    """Check what type of room exists at a tile (on-demand, no caching).
    
    Returns:
        RoomType.ENCLOSED - Fully walled + floor + roof
        RoomType.COVERED - 4 corners + roof (open walls OK)
        RoomType.NONE - Not in a room
    """
    # First check if we have roof above
    if not _has_roof_above(grid, x, y, z):
        if debug:
            print(f"[Room Debug] ({x}, {y}, {z}): No roof above")
        return RoomType.NONE
    
    # Find enclosing walls
    bounds = _find_room_bounds(grid, x, y, z)
    if bounds is None:
        if debug:
            print(f"[Room Debug] ({x}, {y}, {z}): Could not find room bounds")
        return RoomType.NONE
    
    if debug:
        print(f"[Room Debug] ({x}, {y}, {z}): Found bounds {bounds}")
    
    # Check for 4 corners (minimum for COVERED)
    if not _check_four_corners(grid, bounds, z):
        if debug:
            min_x, min_y, max_x, max_y = bounds
            corners = [(min_x, min_y), (max_x, min_y), (min_x, max_y), (max_x, max_y)]
            for cx, cy in corners:
                tile = grid.get_tile(cx, cy, z) if grid.in_bounds(cx, cy, z) else "OOB"
                is_wall = _is_wall_or_corner(grid, cx, cy, z)
                print(f"[Room Debug]   Corner ({cx}, {cy}): {tile}, is_wall={is_wall}")
        return RoomType.NONE
    
    # At this point we have roof + 4 corners = COVERED
    # Now check if it's fully ENCLOSED
    is_enclosed = _check_fully_enclosed(grid, bounds, z)
    has_floor = _check_has_floor(grid, bounds, z)
    
    if debug:
        print(f"[Room Debug] ({x}, {y}, {z}): is_enclosed={is_enclosed}, has_floor={has_floor}")
        if not is_enclosed:
            min_x, min_y, max_x, max_y = bounds
            # Check edges for gaps
            for ex in range(min_x, max_x + 1):
                for ey in [min_y, max_y]:
                    if not _is_enclosing_tile(grid, ex, ey, z):
                        tile = grid.get_tile(ex, ey, z)
                        print(f"[Room Debug]   Gap at ({ex}, {ey}): {tile}")
            for ey in range(min_y, max_y + 1):
                for ex in [min_x, max_x]:
                    if not _is_enclosing_tile(grid, ex, ey, z):
                        tile = grid.get_tile(ex, ey, z)
                        print(f"[Room Debug]   Gap at ({ex}, {ey}): {tile}")
        if not has_floor:
            min_x, min_y, max_x, max_y = bounds
            for fy in range(min_y + 1, max_y):
                for fx in range(min_x + 1, max_x):
                    if not _has_floor(grid, fx, fy, z):
                        tile = grid.get_tile(fx, fy, z)
                        print(f"[Room Debug]   Missing floor at ({fx}, {fy}): {tile}")
    
    if is_enclosed and has_floor:
        return RoomType.ENCLOSED
    
    return RoomType.COVERED


def is_covered_room(grid, x: int, y: int, z: int = 0) -> bool:
    """Check if tile is in at least a covered room (has roof above).
    
    Simplified check: just needs roof above the tile.
    """
    # First check if tile is in a registered room
    room_id = _TILE_TO_ROOM.get((x, y, z))
    if room_id is not None:
        room = _ROOMS.get(room_id)
        if room:
            room_type_enum = room.get("room_type_enum")
            if room_type_enum in (RoomType.COVERED, RoomType.ENCLOSED):
                return True
    
    # Simple fallback: just check for roof above
    return _has_roof_above(grid, x, y, z)


def is_enclosed_room(grid, x: int, y: int, z: int = 0) -> bool:
    """Check if tile is in a fully enclosed room (floor + roof).
    
    Simplified check: needs floor tile AND roof above.
    """
    # First check if tile is in a registered room
    room_id = _TILE_TO_ROOM.get((x, y, z))
    if room_id is not None:
        room = _ROOMS.get(room_id)
        if room:
            room_type_enum = room.get("room_type_enum")
            if room_type_enum == RoomType.ENCLOSED:
                return True
            elif room_type_enum == RoomType.COVERED:
                return False  # Explicitly covered, not enclosed
    
    # Simple fallback: floor + roof = enclosed
    return _has_floor(grid, x, y, z) and _has_roof_above(grid, x, y, z)


# =============================================================================
# Manual Roof Placement
# =============================================================================

def can_place_roof_area(grid, start_x: int, start_y: int, end_x: int, end_y: int, z: int = 0) -> Tuple[bool, str]:
    """Check if a roof can be placed over a rectangular area.
    
    Requirements:
    - Must have 4 corner walls at the bounds
    - Area must be at least 3x3 (1 interior tile + walls)
    
    Args:
        grid: The game grid
        start_x, start_y: One corner of the selection
        end_x, end_y: Opposite corner of the selection
        z: Z-level to place roof on (roof goes on z+1)
    
    Returns:
        (can_place, reason_string)
    """
    # Normalize bounds
    min_x = min(start_x, end_x)
    max_x = max(start_x, end_x)
    min_y = min(start_y, end_y)
    max_y = max(start_y, end_y)
    
    # Check minimum size (at least 3x3 for 1 interior tile)
    width = max_x - min_x + 1
    height = max_y - min_y + 1
    if width < 3 or height < 3:
        return False, "Area too small (minimum 3x3)"
    
    # Check 4 corners have walls
    corners = [
        (min_x, min_y, "top-left"),
        (max_x, min_y, "top-right"),
        (min_x, max_y, "bottom-left"),
        (max_x, max_y, "bottom-right"),
    ]
    
    for cx, cy, name in corners:
        if not _is_wall_or_corner(grid, cx, cy, z):
            return False, f"Missing wall at {name} corner ({cx}, {cy})"
    
    # Check roof level is valid
    roof_z = z + 1
    if roof_z >= grid.depth:
        return False, f"Cannot place roof - Z={roof_z} exceeds grid depth"
    
    return True, "OK"


def place_roof_area(grid, start_x: int, start_y: int, end_x: int, end_y: int, z: int = 0) -> bool:
    """Place roof tiles over a rectangular area.
    
    Creates roof on z+1 level. Requires 4 corner walls.
    Room detection happens automatically via dirty tile processing.
    
    Returns True if roof was placed.
    """
    can_place, reason = can_place_roof_area(grid, start_x, start_y, end_x, end_y, z)
    if not can_place:
        print(f"[Roof] Cannot place roof: {reason}")
        return False
    
    # Normalize bounds
    min_x = min(start_x, end_x)
    max_x = max(start_x, end_x)
    min_y = min(start_y, end_y)
    max_y = max(start_y, end_y)
    roof_z = z + 1
    
    # Place roof tiles on z+1
    tiles_placed = 0
    
    for y in range(min_y, max_y + 1):
        for x in range(min_x, max_x + 1):
            # Check if tile above is empty or already roof
            tile_above = grid.get_tile(x, y, roof_z)
            if tile_above in ("empty", "roof"):
                grid.set_tile(x, y, "roof", z=roof_z)
                _ROOF_TILES[(x, y, roof_z)] = -1  # -1 = manually placed roof
                tiles_placed += 1
    
    # Mark center tile dirty - flood-fill will detect the room
    center_x = (min_x + max_x) // 2
    center_y = (min_y + max_y) // 2
    mark_tile_dirty(center_x, center_y, z)
    
    print(f"[Roof] Placed {tiles_placed} roof tiles at Z={roof_z}")
    return True


def remove_roof_at(grid, x: int, y: int, z: int) -> bool:
    """Remove a roof tile and mark for room re-detection.
    
    Args:
        x, y: Position of roof tile
        z: Z-level of the roof tile (not the room below)
    
    Returns True if roof was removed.
    """
    if (x, y, z) not in _ROOF_TILES:
        return False
    
    del _ROOF_TILES[(x, y, z)]
    
    # Clear the tile
    tile = grid.get_tile(x, y, z)
    if tile == "roof":
        grid.set_tile(x, y, "empty", z=z)
    
    # Mark tile below dirty - room detection will handle cleanup
    room_z = z - 1
    if room_z >= 0:
        mark_tile_dirty(x, y, room_z)
    
    print(f"[Roof] Removed roof tile at ({x}, {y}, z={z})")
    return True
