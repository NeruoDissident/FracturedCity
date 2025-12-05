"""Building definitions and construction helpers.

Buildings now require materials to construct. This module tracks:
- building definitions with material requirements
- construction sites with material delivery tracking
- supply job creation for hauling materials to construction sites
"""

from __future__ import annotations
from typing import Dict, Tuple, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from grid import Grid

from jobs import add_job, remove_job_at
import resources
import zones

Coord3D = Tuple[int, int, int]  # (x, y, z)

# Building type definitions
# Each type specifies: name, materials needed, work to construct, drag constraints
BUILDING_TYPES = {
    "wall": {
        "name": "Wall",
        "tile_type": "wall",
        "materials": {"wood": 1, "mineral": 1},
        "construction_work": 100,
        "walkable": False,
    },
    "wall_advanced": {
        "name": "Reinforced Wall",
        "tile_type": "wall_advanced",
        "materials": {"mineral": 2},
        "construction_work": 150,
        "walkable": False,
    },
    "door": {
        "name": "Door",
        "tile_type": "door",
        "materials": {"wood": 1, "metal": 1},
        "construction_work": 80,
        "walkable": True,  # Doors are walkable when open
    },
    "floor": {
        "name": "Floor",
        "tile_type": "floor",
        "materials": {"wood": 1},
        "construction_work": 40,
        "walkable": True,
    },
    "fire_escape": {
        "name": "Fire Escape",
        "tile_type": "fire_escape",
        "materials": {"wood": 1, "metal": 1},
        "construction_work": 120,
        "walkable": True,  # Colonists can traverse it
    },
    "window": {
        "name": "Window",
        "tile_type": "window",
        "materials": {"wood": 1, "mineral": 1},
        "construction_work": 80,
        "walkable": True,  # Windows are passable (like doors, but slower)
    },
    "bridge": {
        "name": "Bridge",
        "tile_type": "bridge",
        "materials": {"wood": 2, "metal": 1},
        "construction_work": 60,
        "walkable": True,  # Colonists can walk on bridges
    },
    "salvagers_bench": {
        "name": "Salvager's Bench",
        "tile_type": "salvagers_bench",
        "materials": {"wood": 3, "scrap": 2},
        "construction_work": 100,
        "walkable": False,  # Workstation blocks movement
        "workstation": True,  # This is a workstation
        "recipe": {"input": {"scrap": 2}, "output": {"metal": 1}, "work_time": 60},
    },
    "generator": {
        "name": "Generator",
        "tile_type": "generator",
        "materials": {"wood": 2, "metal": 2},
        "construction_work": 120,
        "walkable": False,  # Workstation blocks movement
        "workstation": True,  # This is a workstation
        "recipe": {"input": {"wood": 3}, "output": {"power": 1}, "work_time": 80},
    },
    "stove": {
        "name": "Stove",
        "tile_type": "stove",
        "materials": {"metal": 2, "mineral": 1},
        "construction_work": 100,
        "walkable": False,  # Workstation blocks movement
        "workstation": True,  # This is a workstation
        "recipe": {"input": {"raw_food": 1, "power": 1}, "output": {"cooked_meal": 1}, "work_time": 60},
    },
}

# Track door states (open/closed)
# Key: (x, y, z), Value: {"open": bool, "close_timer": int}
_DOOR_STATES: Dict[Coord3D, dict] = {}

# Track window states (open/closed) - similar to doors but slower
# Key: (x, y, z), Value: {"open": bool, "close_timer": int}
_WINDOW_STATES: Dict[Coord3D, dict] = {}

# Ticks before door auto-closes after being opened
DOOR_CLOSE_DELAY = 30
# Ticks before window auto-closes (longer than doors)
WINDOW_CLOSE_DELAY = 45

# Track construction sites and their material delivery status
# Key: (x, y, z), Value: {"type": str, "materials_delivered": {"wood": 3}, "materials_needed": {"wood": 5}}
# For backwards compatibility, z=0 sites can use (x, y) or (x, y, 0)
_CONSTRUCTION_SITES: Dict[Coord3D, dict] = {}

# Track fire escapes - these allow z-level transitions
# Key: (x, y, z), Value: {"platform_dir": (dx, dy), "platform_pos": (px, py), "z": z, "complete": bool}
_FIRE_ESCAPES: Dict[Coord3D, dict] = {}

# Track workstations (Salvager's Bench, etc.)
# Key: (x, y, z), Value: {"type": str, "reserved": bool, "working": bool, "progress": int, "input_items": {}}
_WORKSTATIONS: Dict[Coord3D, dict] = {}


def get_workstation(x: int, y: int, z: int = 0) -> Optional[dict]:
    """Get workstation data at position, or None if no workstation."""
    return _WORKSTATIONS.get((x, y, z))


def get_all_workstations() -> Dict[Coord3D, dict]:
    """Get all workstations for iteration."""
    return _WORKSTATIONS.copy()


def is_workstation_available(x: int, y: int, z: int = 0) -> bool:
    """Check if workstation exists and is not reserved."""
    ws = _WORKSTATIONS.get((x, y, z))
    return ws is not None and not ws.get("reserved", False)


def reserve_workstation(x: int, y: int, z: int = 0) -> bool:
    """Reserve a workstation. Returns True if successful."""
    ws = _WORKSTATIONS.get((x, y, z))
    if ws is None or ws.get("reserved", False):
        return False
    ws["reserved"] = True
    return True


def release_workstation(x: int, y: int, z: int = 0) -> None:
    """Release a workstation reservation."""
    ws = _WORKSTATIONS.get((x, y, z))
    if ws is not None:
        ws["reserved"] = False
        ws["working"] = False
        ws["progress"] = 0
        ws["input_items"] = {}


def add_input_to_workstation(x: int, y: int, z: int, resource_type: str, amount: int) -> bool:
    """Add input materials to a workstation. Returns True if successful."""
    ws = _WORKSTATIONS.get((x, y, z))
    if ws is None:
        return False
    if "input_items" not in ws:
        ws["input_items"] = {}
    ws["input_items"][resource_type] = ws["input_items"].get(resource_type, 0) + amount
    return True


def workstation_has_inputs(x: int, y: int, z: int = 0) -> bool:
    """Check if workstation has all required inputs for its recipe."""
    ws = _WORKSTATIONS.get((x, y, z))
    if ws is None:
        return False
    
    building_def = BUILDING_TYPES.get(ws.get("type", ""))
    if building_def is None or "recipe" not in building_def:
        return False
    
    recipe = building_def["recipe"]
    inputs_needed = recipe.get("input", {})
    inputs_have = ws.get("input_items", {})
    
    for res_type, amount in inputs_needed.items():
        if inputs_have.get(res_type, 0) < amount:
            return False
    return True


def consume_workstation_inputs(x: int, y: int, z: int = 0) -> bool:
    """Consume inputs and produce outputs. Returns True if successful."""
    ws = _WORKSTATIONS.get((x, y, z))
    if ws is None:
        return False
    
    building_def = BUILDING_TYPES.get(ws.get("type", ""))
    if building_def is None or "recipe" not in building_def:
        return False
    
    recipe = building_def["recipe"]
    inputs_needed = recipe.get("input", {})
    
    # Consume inputs
    for res_type, amount in inputs_needed.items():
        ws["input_items"][res_type] = ws["input_items"].get(res_type, 0) - amount
    
    # Clear empty entries
    ws["input_items"] = {k: v for k, v in ws["input_items"].items() if v > 0}
    
    return True


def get_workstation_recipe(x: int, y: int, z: int = 0) -> Optional[dict]:
    """Get the recipe for a workstation."""
    ws = _WORKSTATIONS.get((x, y, z))
    if ws is None:
        return None
    
    building_def = BUILDING_TYPES.get(ws.get("type", ""))
    if building_def is None:
        return None
    
    return building_def.get("recipe")


def place_building(grid: Grid, x: int, y: int, building_type: str, z: int = 0) -> bool:
    """Place a construction site for any building type.
    
    If there's a resource node on the tile, it will be cleared and its
    resources dropped as items (marked for hauling). The node won't respawn.
    If there's a stockpile zone on the tile, it will be removed.
    
    Args:
        grid: The game grid
        x, y: Tile coordinates
        building_type: Type of building to place
        z: Z-level (0=ground, 1=rooftop)
    
    Returns True if placement succeeded.
    """
    # Check current tile
    current_tile = grid.get_tile(x, y, z)
    
    # Prevent building walls on fire_escape_platform (would block vertical access)
    if current_tile == "fire_escape_platform" and building_type in ("wall", "wall_advanced"):
        return False
    
    # Allow placement on empty tiles, resource nodes, finished floors, or walkable roof tiles (z=1)
    if current_tile == "resource_node":
        # Clear the resource node - drops items and prevents respawn
        resources.clear_node_for_construction(x, y)
        # Cancel any gathering job on this tile
        remove_job_at(x, y)
    elif current_tile in ("roof_floor", "roof_access"):
        # Allow building on walkable rooftop surfaces (z=1)
        pass
    elif current_tile not in ("empty", None, "finished_floor"):
        # Can't build on other occupied tiles
        return False
    
    building_def = BUILDING_TYPES.get(building_type)
    if building_def is None:
        return False
    
    # Mark stockpile zone for removal (walls/doors can't have zones)
    if building_type in ("wall", "wall_advanced", "door", "window"):
        zones.mark_tile_for_removal(x, y, z)
    
    # Create construction site - materials will be delivered by supply jobs
    site = {
        "type": building_type,
        "materials_needed": building_def["materials"].copy(),
        "materials_delivered": {k: 0 for k in building_def["materials"]},
        "awaiting_stockpile_clear": zones.is_pending_removal(x, y, z),
        "z": z,
    }
    _CONSTRUCTION_SITES[(x, y, z)] = site
    
    # Set tile to the building's tile type
    tile_type = building_def.get("tile_type", building_type)
    grid.set_tile(x, y, tile_type, z=z)
    
    # Create construction job with z-level
    add_job("construction", x, y, required=building_def["construction_work"], category=building_type, z=z)
    return True


def place_wall(grid: Grid, x: int, y: int, z: int = 0) -> bool:
    """Place a basic wall construction site at (x, y, z)."""
    return place_building(grid, x, y, "wall", z)


def place_wall_advanced(grid: Grid, x: int, y: int, z: int = 0) -> bool:
    """Place an advanced wall construction site at (x, y, z)."""
    return place_building(grid, x, y, "wall_advanced", z)


def place_door(grid: Grid, x: int, y: int, z: int = 0) -> bool:
    """Place a door construction site at (x, y, z)."""
    if place_building(grid, x, y, "door", z):
        # Initialize door state as closed
        _DOOR_STATES[(x, y, z)] = {"open": False, "close_timer": 0}
        return True
    return False


def place_floor(grid: Grid, x: int, y: int, z: int = 0) -> bool:
    """Place a floor construction site at (x, y, z)."""
    return place_building(grid, x, y, "floor", z)


def place_window(grid: Grid, x: int, y: int, z: int = 0) -> bool:
    """Place a window construction site at (x, y, z)."""
    return place_building(grid, x, y, "window", z)


def can_place_salvagers_bench(grid: Grid, x: int, y: int, z: int = 0) -> bool:
    """Check if a Salvager's Bench can be placed at (x, y, z).
    
    Requirements:
    - Must be on a finished floor tile
    - Must be inside a valid room (has roof above)
    """
    import rooms
    
    tile = grid.get_tile(x, y, z)
    if tile not in ("finished_floor", "roof_floor", "roof_access"):
        return False
    
    # Must be inside a room (has roof above)
    if not rooms.has_roof(x, y, z + 1):
        return False
    
    return True


def place_salvagers_bench(grid: Grid, x: int, y: int, z: int = 0) -> bool:
    """Place a Salvager's Bench construction site at (x, y, z)."""
    if not can_place_salvagers_bench(grid, x, y, z):
        return False
    return place_building(grid, x, y, "salvagers_bench", z)


def can_place_generator(grid: Grid, x: int, y: int, z: int = 0) -> bool:
    """Check if a Generator can be placed at (x, y, z).
    
    Same requirements as Salvager's Bench:
    - Must be on finished floor
    - Must be inside a room (has roof above)
    """
    return can_place_salvagers_bench(grid, x, y, z)


def place_generator(grid: Grid, x: int, y: int, z: int = 0) -> bool:
    """Place a Generator construction site at (x, y, z)."""
    if not can_place_generator(grid, x, y, z):
        return False
    return place_building(grid, x, y, "generator", z)


def can_place_stove(grid: Grid, x: int, y: int, z: int = 0) -> bool:
    """Check if a Stove can be placed at (x, y, z).
    
    Same requirements as other workstations:
    - Must be on finished floor
    - Must be inside a room (has roof above)
    """
    return can_place_salvagers_bench(grid, x, y, z)


def place_stove(grid: Grid, x: int, y: int, z: int = 0) -> bool:
    """Place a Stove construction site at (x, y, z)."""
    if not can_place_stove(grid, x, y, z):
        return False
    return place_building(grid, x, y, "stove", z)


def register_workstation(x: int, y: int, z: int, workstation_type: str) -> None:
    """Register a completed workstation."""
    _WORKSTATIONS[(x, y, z)] = {
        "type": workstation_type,
        "reserved": False,
        "working": False,
        "progress": 0,
        "input_items": {},
    }


# Tiles that can be demolished
DEMOLISHABLE_TILES = {
    # Walls
    "wall", "finished_wall", "wall_advanced", "finished_wall_advanced",
    # Entrances
    "door", "window", "finished_window", "window_tile",
    # Floors
    "floor", "finished_floor",
    # Fire escapes and bridges
    "fire_escape", "fire_escape_platform", "bridge", "finished_bridge",
    # Construction sites (cancel)
    "building",
}


def demolish_tile(grid: Grid, x: int, y: int, z: int = 0) -> bool:
    """Demolish a structure at (x, y, z), returning it to empty.
    
    Removes the tile and any associated state (door states, window states, etc.)
    Also removes any construction site or pending jobs.
    
    Returns True if something was demolished.
    """
    from jobs import remove_job_at
    from rooms import mark_rooms_dirty
    
    tile = grid.get_tile(x, y, z)
    
    if tile is None or tile not in DEMOLISHABLE_TILES:
        return False
    
    # Remove construction site if exists
    if (x, y, z) in _CONSTRUCTION_SITES:
        remove_construction_site(x, y, z)
    
    # Remove any job at this location
    remove_job_at(x, y, z)
    
    # Remove door state if it was a door
    if (x, y, z) in _DOOR_STATES:
        del _DOOR_STATES[(x, y, z)]
    
    # Remove window state if it was a window
    if (x, y, z) in _WINDOW_STATES:
        del _WINDOW_STATES[(x, y, z)]
    
    # Remove fire escape data if applicable
    if (x, y, z) in _FIRE_ESCAPES:
        # Also remove the platform
        escape_data = _FIRE_ESCAPES[(x, y, z)]
        platform_pos = escape_data.get("platform_pos")
        if platform_pos:
            px, py = platform_pos
            # Clear platform on current Z and Z+1
            if grid.get_tile(px, py, z) == "fire_escape_platform":
                grid.set_tile(px, py, "empty", z=z)
            if grid.get_tile(px, py, z + 1) == "fire_escape_platform":
                grid.set_tile(px, py, "empty", z=z + 1)
        del _FIRE_ESCAPES[(x, y, z)]
    
    # Set tile back to empty
    grid.set_tile(x, y, "empty", z=z)
    
    # Trigger room re-detection
    mark_rooms_dirty()
    
    print(f"[Demolish] Removed {tile} at ({x}, {y}, z={z})")
    return True


def can_place_fire_escape(grid: Grid, x: int, y: int, z: int = 0) -> Tuple[bool, Optional[Tuple[int, int]]]:
    """Check if a fire escape can be placed at (x, y, z).
    
    Requirements:
    - Must be on a finished wall
    - Must have a roof tile above (z+1)
    - Must have an adjacent tile for the external platform
    
    Returns (can_place, platform_direction) where platform_direction is (dx, dy)
    pointing to where the external platform would be.
    
    The platform MUST be placed on the EXTERIOR side (opposite from interior floor).
    """
    import rooms
    
    # Must be a finished wall on the specified Z-level
    tile = grid.get_tile(x, y, z)
    if tile not in ("finished_wall", "finished_wall_advanced"):
        return False, None
    
    # Interior tiles (inside the building)
    interior_tiles = {"finished_floor", "roof_access", "roof_floor", "floor"}
    # Placeable exterior tiles (outside the building)
    placeable_tiles = {"empty", "roof"}
    
    # Check all four directions
    # Priority: Find a direction where ONE side is interior and the OTHER side is exterior
    # This ensures the window_tile replaces the wall and platform goes outside
    for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
        # One side of the wall
        side_a_x, side_a_y = x + dx, y + dy
        # Opposite side of the wall
        side_b_x, side_b_y = x - dx, y - dy
        
        if not grid.in_bounds(side_a_x, side_a_y, z) or not grid.in_bounds(side_b_x, side_b_y, z):
            continue
        
        tile_a = grid.get_tile(side_a_x, side_a_y, z)
        tile_b = grid.get_tile(side_b_x, side_b_y, z)
        
        # Case 1: Side A is interior, Side B is exterior (platform goes to B)
        if tile_a in interior_tiles and tile_b in placeable_tiles:
            return True, (-dx, -dy)  # Platform direction is AWAY from interior
        
        # Case 2: Side B is interior, Side A is exterior (platform goes to A)
        if tile_b in interior_tiles and tile_a in placeable_tiles:
            return True, (dx, dy)  # Platform direction is AWAY from interior
    
    # Fallback: If no clear interior/exterior distinction, find any placeable exterior
    for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
        px, py = x + dx, y + dy
        if not grid.in_bounds(px, py, z):
            continue
        
        platform_tile = grid.get_tile(px, py, z)
        
        # Platform must be placeable (empty ground or roof)
        if platform_tile in placeable_tiles:
            return True, (dx, dy)
    
    return False, None


def place_fire_escape(grid: Grid, x: int, y: int, z: int = 0) -> bool:
    """Place a fire escape on a finished wall at (x, y, z).
    
    The fire escape creates:
    - WindowTile at (x, y, z): passable wall opening
    - Platform at (px, py, z): external walkable platform
    - Vertical link to platform at (px, py, z+1)
    
    Path: Floor(Z) → WindowTile(Z) → Platform(Z) → Platform(Z+1)
    """
    can_place, platform_dir = can_place_fire_escape(grid, x, y, z)
    if not can_place or platform_dir is None:
        return False
    
    building_def = BUILDING_TYPES.get("fire_escape")
    if building_def is None:
        return False
    
    # Calculate platform position
    dx, dy = platform_dir
    platform_x, platform_y = x + dx, y + dy
    
    # Double-check platform tile is valid (safety check)
    # Platform can be on empty (air/ground) or roof (exterior roof)
    platform_tile = grid.get_tile(platform_x, platform_y, z)
    if platform_tile not in ("empty", "roof"):
        return False
    
    # Create construction site
    site = {
        "type": "fire_escape",
        "materials_needed": building_def["materials"].copy(),
        "materials_delivered": {k: 0 for k in building_def["materials"]},
        "awaiting_stockpile_clear": False,
        "platform_dir": platform_dir,
        "platform_pos": (platform_x, platform_y),
        "z": z,
    }
    _CONSTRUCTION_SITES[(x, y, z)] = site
    
    # Set tile to fire_escape (under construction)
    grid.set_tile(x, y, "fire_escape", z=z)
    
    # Track fire escape location with platform info and Z-level
    _FIRE_ESCAPES[(x, y, z)] = {
        "platform_dir": platform_dir,
        "platform_pos": (platform_x, platform_y),
        "z": z,
        "complete": False,
    }
    
    # Create construction job
    from jobs import add_job
    add_job("construction", x, y, required=building_def["construction_work"], category="fire_escape", z=z)
    return True


def get_fire_escape(x: int, y: int, z: int = 0) -> Optional[dict]:
    """Get fire escape data at (x, y, z) or None."""
    return _FIRE_ESCAPES.get((x, y, z))


def get_all_fire_escapes() -> Dict[Coord3D, dict]:
    """Get all fire escapes for pathfinding."""
    return _FIRE_ESCAPES.copy()


def is_fire_escape(x: int, y: int, z: int = 0) -> bool:
    """Check if there's a fire escape at (x, y, z)."""
    return (x, y, z) in _FIRE_ESCAPES


def is_fire_escape_complete(x: int, y: int, z: int = 0) -> bool:
    """Check if fire escape at (x, y, z) is fully constructed."""
    escape = _FIRE_ESCAPES.get((x, y, z))
    if escape is None:
        return False
    return escape.get("complete", False)


def mark_fire_escape_complete(x: int, y: int, z: int = 0) -> None:
    """Mark a fire escape as complete after construction finishes."""
    if (x, y, z) in _FIRE_ESCAPES:
        _FIRE_ESCAPES[(x, y, z)]["complete"] = True


def get_fire_escape_platform(x: int, y: int, z: int = 0) -> Optional[Tuple[int, int]]:
    """Get the platform position for a fire escape at (x, y, z)."""
    escape = _FIRE_ESCAPES.get((x, y, z))
    if escape is None:
        return None
    return escape.get("platform_pos")


# --- Bridge functions ---

def _is_bridge_anchor(grid: Grid, x: int, y: int, z: int) -> bool:
    """Check if a tile can anchor a bridge (fire escape platform or another bridge)."""
    tile = grid.get_tile(x, y, z)
    return tile in ("fire_escape_platform", "bridge", "finished_bridge")


def can_place_bridge(grid: Grid, x: int, y: int, z: int = 0) -> bool:
    """Check if a bridge can be placed at (x, y, z).
    
    Requirements:
    - Must be on Z=1 or higher (bridges are elevated walkways)
    - Can be placed on empty space (air), roof_access, or roof tiles
    - Must be adjacent to a fire escape platform or another bridge
    
    Bridges create traversable platforms in mid-air, connecting buildings.
    """
    # Bridges only on Z=1 and above (elevated walkways between buildings)
    if z < 1:
        return False
    
    if not grid.in_bounds(x, y, z):
        return False
    
    tile = grid.get_tile(x, y, z)
    
    # Can't place on walls, doors, windows, or existing structures
    if tile in ("wall", "finished_wall", "wall_advanced", "finished_wall_advanced",
                "door", "window", "finished_window", "window_tile",
                "fire_escape", "fire_escape_platform", "bridge", "finished_bridge",
                "finished_floor", "floor"):
        return False
    
    # Can place on: empty/None (air), roof_access, roof tiles
    # This allows bridges to span across open air between buildings
    if tile not in (None, "empty", "roof_access", "roof"):
        return False
    
    # Must be adjacent to a fire escape platform or another bridge
    has_anchor = False
    for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
        nx, ny = x + dx, y + dy
        if grid.in_bounds(nx, ny, z) and _is_bridge_anchor(grid, nx, ny, z):
            has_anchor = True
            break
    
    if not has_anchor:
        return False
    
    # Check no existing construction site
    if get_construction_site(x, y, z) is not None:
        return False
    
    return True


def place_bridge(grid: Grid, x: int, y: int, z: int = 0) -> bool:
    """Place a bridge construction site at (x, y, z).
    
    Bridges connect fire escape platforms and allow colonists to walk between buildings.
    """
    if not can_place_bridge(grid, x, y, z):
        return False
    
    building_def = BUILDING_TYPES.get("bridge")
    if building_def is None:
        return False
    
    # Set tile to bridge (under construction)
    grid.set_tile(x, y, "bridge", z=z)
    
    # Create construction site
    _CONSTRUCTION_SITES[(x, y, z)] = {
        "type": "bridge",
        "materials_needed": building_def["materials"].copy(),
        "materials_delivered": {},
        "z": z,
    }
    
    # Create construction job
    from jobs import add_job
    add_job("construction", x, y, required=building_def["construction_work"], category="bridge", z=z)
    
    print(f"[Build] Bridge placed at ({x}, {y}, z={z})")
    return True


def get_construction_costs(x: int, y: int, z: int = 0) -> Dict[str, int]:
    """Get the material costs for a construction site."""
    site = get_construction_site(x, y, z)
    if site is None:
        return {}
    return site.get("materials_needed", {})


# --- Door functions ---

def is_door(x: int, y: int, z: int = 0) -> bool:
    """Check if tile at (x, y, z) is a door."""
    return (x, y, z) in _DOOR_STATES


def is_door_open(x: int, y: int, z: int = 0) -> bool:
    """Check if door at (x, y, z) is open."""
    door = _DOOR_STATES.get((x, y, z))
    return door is not None and door.get("open", False)


def open_door(x: int, y: int, z: int = 0) -> None:
    """Open the door at (x, y, z) and reset close timer."""
    door = _DOOR_STATES.get((x, y, z))
    if door is not None:
        door["open"] = True
        door["close_timer"] = DOOR_CLOSE_DELAY


def close_door(x: int, y: int, z: int = 0) -> None:
    """Close the door at (x, y, z)."""
    door = _DOOR_STATES.get((x, y, z))
    if door is not None:
        door["open"] = False
        door["close_timer"] = 0


def update_doors() -> None:
    """Update door timers and auto-close doors. Call once per tick."""
    for (x, y, z), door in _DOOR_STATES.items():
        if door["open"] and door["close_timer"] > 0:
            door["close_timer"] -= 1
            if door["close_timer"] <= 0:
                door["open"] = False


def get_all_door_states() -> Dict[Coord3D, dict]:
    """Get all door states for rendering."""
    return _DOOR_STATES.copy()


# --- Window functions ---

def register_window(x: int, y: int, z: int = 0) -> None:
    """Register a new window at (x, y, z). Called when window construction completes."""
    _WINDOW_STATES[(x, y, z)] = {"open": False, "close_timer": 0}


def is_window(x: int, y: int, z: int = 0) -> bool:
    """Check if tile at (x, y, z) is a window."""
    return (x, y, z) in _WINDOW_STATES


def is_window_open(x: int, y: int, z: int = 0) -> bool:
    """Check if window at (x, y, z) is open."""
    window = _WINDOW_STATES.get((x, y, z))
    return window is not None and window.get("open", False)


def open_window(x: int, y: int, z: int = 0) -> None:
    """Open the window at (x, y, z) and reset close timer."""
    window = _WINDOW_STATES.get((x, y, z))
    if window is not None:
        window["open"] = True
        window["close_timer"] = WINDOW_CLOSE_DELAY


def close_window(x: int, y: int, z: int = 0) -> None:
    """Close the window at (x, y, z)."""
    window = _WINDOW_STATES.get((x, y, z))
    if window is not None:
        window["open"] = False
        window["close_timer"] = 0


def update_windows() -> None:
    """Update window timers and auto-close windows. Call once per tick."""
    for (x, y, z), window in _WINDOW_STATES.items():
        if window["open"] and window["close_timer"] > 0:
            window["close_timer"] -= 1
            if window["close_timer"] <= 0:
                window["open"] = False


def get_all_window_states() -> Dict[Coord3D, dict]:
    """Get all window states for rendering."""
    return _WINDOW_STATES.copy()


def get_construction_site(x: int, y: int, z: int = 0) -> Optional[dict]:
    """Return construction site data at (x, y, z), if any."""
    return _CONSTRUCTION_SITES.get((x, y, z))


def remove_construction_site(x: int, y: int, z: int = 0) -> None:
    """Remove construction site when building is complete."""
    _CONSTRUCTION_SITES.pop((x, y, z), None)


def is_awaiting_stockpile_clear(x: int, y: int, z: int = 0) -> bool:
    """Check if construction site is waiting for stockpile items to be relocated."""
    site = get_construction_site(x, y, z)
    if site is None:
        return False
    return site.get("awaiting_stockpile_clear", False)


def clear_stockpile_wait(x: int, y: int, z: int = 0) -> None:
    """Clear the awaiting_stockpile_clear flag after items are relocated."""
    site = get_construction_site(x, y, z)
    if site is not None:
        site["awaiting_stockpile_clear"] = False


def has_required_materials(x: int, y: int, z: int = 0) -> bool:
    """Check if construction site has all required materials delivered."""
    site = get_construction_site(x, y, z)
    if site is None:
        return True
    
    needed = site.get("materials_needed", {})
    delivered = site.get("materials_delivered", {})
    
    for resource, amount in needed.items():
        if delivered.get(resource, 0) < amount:
            return False
    return True


def get_missing_materials(x: int, y: int, z: int = 0) -> Dict[str, int]:
    """Get materials still needed at a construction site.
    
    Returns {resource_type: amount_still_needed}
    """
    site = get_construction_site(x, y, z)
    if site is None:
        return {}
    
    needed = site.get("materials_needed", {})
    delivered = site.get("materials_delivered", {})
    
    missing = {}
    for resource, amount in needed.items():
        still_need = amount - delivered.get(resource, 0)
        if still_need > 0:
            missing[resource] = still_need
    return missing


def deliver_material(x: int, y: int, resource_type: str, amount: int, z: int = 0) -> int:
    """Deliver materials to a construction site.
    
    Returns the amount actually delivered (may be less if not needed).
    """
    site = get_construction_site(x, y, z)
    if site is None:
        return 0
    
    needed = site.get("materials_needed", {}).get(resource_type, 0)
    delivered = site.get("materials_delivered", {}).get(resource_type, 0)
    
    still_need = needed - delivered
    actual_delivered = min(amount, still_need)
    
    if actual_delivered > 0:
        site["materials_delivered"][resource_type] = delivered + actual_delivered
    
    return actual_delivered


def get_all_construction_sites() -> Dict[Coord3D, dict]:
    """Return all construction sites for iteration."""
    return _CONSTRUCTION_SITES.copy()


# Track supply jobs that have been created to avoid duplicates
# Key: (construction_x, construction_y, construction_z, resource_type)
_PENDING_SUPPLY_JOBS: set = set()


def mark_supply_job_created(dest_x: int, dest_y: int, dest_z: int, resource_type: str) -> None:
    """Mark that a supply job has been created for this site/resource."""
    _PENDING_SUPPLY_JOBS.add((dest_x, dest_y, dest_z, resource_type))


def mark_supply_job_completed(dest_x: int, dest_y: int, dest_z: int, resource_type: str) -> None:
    """Mark that a supply job has been completed."""
    _PENDING_SUPPLY_JOBS.discard((dest_x, dest_y, dest_z, resource_type))


def has_pending_supply_job(dest_x: int, dest_y: int, dest_z: int, resource_type: str) -> bool:
    """Check if there's already a supply job for this site/resource."""
    return (dest_x, dest_y, dest_z, resource_type) in _PENDING_SUPPLY_JOBS


def debug_supply_status() -> None:
    """Print debug info about supply job status."""
    if not _CONSTRUCTION_SITES:
        return
    
    print(f"\n=== SUPPLY DEBUG ===")
    print(f"Pending supply jobs: {_PENDING_SUPPLY_JOBS}")
    for (x, y, z), site in _CONSTRUCTION_SITES.items():
        needed = site.get("materials_needed", {})
        delivered = site.get("materials_delivered", {})
        print(f"  Site ({x},{y},z={z}): needed={needed}, delivered={delivered}")


def process_supply_jobs(jobs_module, zones_module) -> int:
    """Create supply jobs for construction sites that need materials.
    
    Called each tick from main loop.
    Returns number of jobs created.
    """
    # First, clean up stale pending flags for jobs that no longer exist
    _cleanup_stale_pending_jobs(jobs_module)
    
    jobs_created = 0
    
    for (x, y, z), site in _CONSTRUCTION_SITES.items():
        missing = get_missing_materials(x, y, z)
        
        for resource_type, amount_needed in missing.items():
            # Skip if we already have a supply job pending for this
            if has_pending_supply_job(x, y, z, resource_type):
                continue
            
            # Find stockpile with this resource (prefer same Z-level)
            source = zones_module.find_stockpile_with_resource(resource_type, z=z)
            if source is None:
                # No stockpile has this resource
                continue
            
            source_x, source_y, source_z = source
            
            # Create supply job (pickup from stockpile, deliver to construction)
            jobs_module.add_job(
                "supply",
                source_x, source_y,  # Pickup location
                required=10,  # Quick job
                resource_type=resource_type,
                dest_x=x,
                dest_y=y,
                dest_z=z,  # Construction site Z-level
                z=source_z,  # Pickup Z-level
            )
            mark_supply_job_created(x, y, z, resource_type)
            jobs_created += 1
    
    return jobs_created


def _cleanup_stale_pending_jobs(jobs_module) -> None:
    """Remove pending flags for supply jobs that no longer exist in the queue."""
    # Build set of actual supply jobs in queue
    actual_supply_jobs = set()
    for job in jobs_module.JOB_QUEUE:
        if job.type == "supply" and job.dest_x is not None and job.dest_y is not None:
            actual_supply_jobs.add((job.dest_x, job.dest_y, job.dest_z, job.resource_type))
    
    # Find stale pending flags
    stale = _PENDING_SUPPLY_JOBS - actual_supply_jobs
    
    # Remove stale flags
    for key in stale:
        _PENDING_SUPPLY_JOBS.discard(key)


# ============================================================================
# CRAFTING JOBS
# ============================================================================

# Track pending crafting jobs to avoid duplicates
_PENDING_CRAFTING_JOBS: set = set()  # Set of (x, y, z) workstation coords


def has_pending_crafting_job(x: int, y: int, z: int) -> bool:
    """Check if a crafting job is already pending for this workstation."""
    return (x, y, z) in _PENDING_CRAFTING_JOBS


def mark_crafting_job_created(x: int, y: int, z: int) -> None:
    """Mark that a crafting job has been created for this workstation."""
    _PENDING_CRAFTING_JOBS.add((x, y, z))


def mark_crafting_job_completed(x: int, y: int, z: int) -> None:
    """Mark that a crafting job has been completed."""
    _PENDING_CRAFTING_JOBS.discard((x, y, z))


def process_crafting_jobs(jobs_module, zones_module) -> int:
    """Create crafting jobs for available workstations with resources.
    
    Called each tick from main loop.
    Returns number of jobs created.
    """
    jobs_created = 0
    
    for (x, y, z), ws in _WORKSTATIONS.items():
        # Skip if already reserved or has pending job
        if ws.get("reserved", False):
            continue
        if has_pending_crafting_job(x, y, z):
            continue
        
        # Get recipe for this workstation
        recipe = get_workstation_recipe(x, y, z)
        if recipe is None:
            continue
        
        # Check if stockpile has required inputs
        inputs_needed = recipe.get("input", {})
        can_craft = True
        
        for res_type, amount in inputs_needed.items():
            source = zones_module.find_stockpile_with_resource(res_type, z=z)
            if source is None:
                can_craft = False
                break
        
        if not can_craft:
            continue
        
        # Create crafting job at workstation location
        # Determine job category based on workstation type
        workstation_type = ws.get("type", "")
        if workstation_type == "stove":
            job_category = "cooking"
        else:
            job_category = "crafting"
        
        work_time = recipe.get("work_time", 60)
        jobs_module.add_job(
            "crafting",
            x, y,
            required=work_time,
            category=job_category,
            z=z,
        )
        mark_crafting_job_created(x, y, z)
        jobs_created += 1
    
    return jobs_created


def _cleanup_stale_crafting_jobs(jobs_module) -> None:
    """Remove pending flags for crafting jobs that no longer exist."""
    actual_crafting_jobs = set()
    for job in jobs_module.JOB_QUEUE:
        if job.type == "crafting":
            actual_crafting_jobs.add((job.x, job.y, job.z))
    
    stale = _PENDING_CRAFTING_JOBS - actual_crafting_jobs
    for key in stale:
        _PENDING_CRAFTING_JOBS.discard(key)


# --- Save/Load ---

def get_save_state() -> dict:
    """Get buildings state for saving."""
    # Construction sites
    sites_data = {}
    for coord, site in _CONSTRUCTION_SITES.items():
        key = f"{coord[0]},{coord[1]},{coord[2]}"
        sites_data[key] = {
            "building_type": site.get("building_type"),
            "materials_delivered": site.get("materials_delivered", {}),
            "work_progress": site.get("work_progress", 0),
        }
    
    # Workstations
    workstations_data = {}
    for coord, ws in _WORKSTATIONS.items():
        key = f"{coord[0]},{coord[1]},{coord[2]}"
        workstations_data[key] = {
            "type": ws.get("type"),
            "progress": ws.get("progress", 0),
            "reserved": ws.get("reserved", False),
            "inputs_consumed": ws.get("inputs_consumed", False),
        }
    
    # Doors and windows
    doors_data = {f"{d[0]},{d[1]},{d[2]}": {"open": _DOOR_STATES.get(d, False), "timer": _DOOR_TIMERS.get(d, 0)} for d in _DOOR_STATES}
    windows_data = {f"{w[0]},{w[1]},{w[2]}": {"open": _WINDOW_STATES.get(w, False), "timer": _WINDOW_TIMERS.get(w, 0)} for w in _WINDOW_STATES}
    
    # Fire escapes
    fire_escapes_data = [list(fe) for fe in _FIRE_ESCAPES]
    
    return {
        "construction_sites": sites_data,
        "workstations": workstations_data,
        "doors": doors_data,
        "windows": windows_data,
        "fire_escapes": fire_escapes_data,
    }


def load_save_state(state: dict):
    """Restore buildings state from save."""
    global _CONSTRUCTION_SITES, _WORKSTATIONS, _DOOR_STATES, _DOOR_TIMERS, _WINDOW_STATES, _WINDOW_TIMERS, _FIRE_ESCAPES
    global _PENDING_SUPPLY_JOBS, _PENDING_CRAFTING_JOBS
    
    _CONSTRUCTION_SITES.clear()
    _WORKSTATIONS.clear()
    _DOOR_STATES.clear()
    _DOOR_TIMERS.clear()
    _WINDOW_STATES.clear()
    _WINDOW_TIMERS.clear()
    _FIRE_ESCAPES.clear()
    _PENDING_SUPPLY_JOBS.clear()
    _PENDING_CRAFTING_JOBS.clear()
    
    # Restore construction sites
    for key, site_data in state.get("construction_sites", {}).items():
        parts = key.split(",")
        coord = (int(parts[0]), int(parts[1]), int(parts[2]))
        _CONSTRUCTION_SITES[coord] = {
            "building_type": site_data.get("building_type"),
            "materials_delivered": site_data.get("materials_delivered", {}),
            "work_progress": site_data.get("work_progress", 0),
        }
    
    # Restore workstations
    for key, ws_data in state.get("workstations", {}).items():
        parts = key.split(",")
        coord = (int(parts[0]), int(parts[1]), int(parts[2]))
        _WORKSTATIONS[coord] = {
            "type": ws_data.get("type"),
            "progress": ws_data.get("progress", 0),
            "reserved": False,  # Reset reservations on load
            "inputs_consumed": ws_data.get("inputs_consumed", False),
        }
    
    # Restore doors
    for key, door_data in state.get("doors", {}).items():
        parts = key.split(",")
        coord = (int(parts[0]), int(parts[1]), int(parts[2]))
        _DOOR_STATES[coord] = door_data.get("open", False)
        _DOOR_TIMERS[coord] = door_data.get("timer", 0)
    
    # Restore windows
    for key, window_data in state.get("windows", {}).items():
        parts = key.split(",")
        coord = (int(parts[0]), int(parts[1]), int(parts[2]))
        _WINDOW_STATES[coord] = window_data.get("open", False)
        _WINDOW_TIMERS[coord] = window_data.get("timer", 0)
    
    # Restore fire escapes
    for fe in state.get("fire_escapes", []):
        _FIRE_ESCAPES.add(tuple(fe))
