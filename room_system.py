"""Manual Room Designation System.

Player-driven room creation:
1. Player clicks "Create Room" button
2. Selects room type from menu
3. Drags rectangle on grid
4. Game validates requirements
5. If valid: room created with effects
6. If invalid: error message shown

No auto-detection. No placement restrictions on workstations.
Pure designation layer on top of existing tiles.
"""

from typing import Dict, List, Tuple, Optional, Set
from enum import Enum

Coord = Tuple[int, int]
Coord3D = Tuple[int, int, int]

# =============================================================================
# ROOM DATA STORAGE
# =============================================================================

# Room registry: room_id -> room data
_ROOMS: Dict[int, dict] = {}

# Reverse lookup: (x, y, z) -> room_id
_TILE_TO_ROOM: Dict[Coord3D, int] = {}

# Next room ID
_next_room_id = 1


# =============================================================================
# ROOM TYPE DEFINITIONS
# =============================================================================

# Furniture category mapping for Social Venues
VENUE_FURNITURE_CATEGORIES = {
    "bar_furniture": [
        "bar_stool",
        "scrap_bar_counter",
        "finished_bar",
        "gutter_still",
        "finished_gutter_still",
    ],
    "music_equipment": [
        "scrap_guitar_placed",
        "drum_kit_placed",
        "synth_placed",
        "harmonica_placed",
        "amp_placed",
        "stage",
        "finished_stage",
    ],
    "seating": [
        "comfort_chair",
        "bar_stool",
        "crash_bed",  # Lounge seating
    ],
    "tables": [
        "dining_table",
        "workshop_table",
        "gutter_slab",
    ],
    "luxury": [
        # Future: pool, chandelier, fountain, etc.
    ],
}

ROOM_TYPES = {
    "Bedroom": {
        "name": "Bedroom",
        "description": "Private sleeping quarters",
        "requirements": {
            "min_size": 4,
            "max_size": 100,
            "required_furniture": {"crash_bed": 1},
            "max_entrances": 2,
            "must_be_enclosed": True,
            "must_have_roof": True,
        },
        "quality_factors": {
            # Furniture bonuses (per item)
            "cabinet": 5,
            "desk": 8,
            "statue": 10,
            "lamp": 3,
            # Size bonus: +1 per tile over minimum
            "size_bonus": 1,
        },
        "effects": {
            # Effects are calculated from quality score (0-100)
            "sleep_quality_mult": 0.01,  # 1.0 + (quality * 0.01) = 1.0 to 2.0
            "mood_bonus": 0.1,  # quality * 0.1 = 0 to 10
        },
        "can_assign_owner": True,
    },
    
    "Kitchen": {
        "name": "Kitchen",
        "description": "Food preparation area",
        "requirements": {
            "min_size": 6,
            "required_furniture": {"finished_stove": 1},
            "must_be_enclosed": True,
            "must_have_roof": True,
        },
        "quality_factors": {
            "fridge": 10,
            "counter": 5,
            "size_bonus": 1,
        },
        "effects": {
            "cooking_speed_mult": 0.002,  # 1.0 + (quality * 0.002) = 1.0 to 1.2
            "food_quality_mult": 0.001,  # 1.0 + (quality * 0.001) = 1.0 to 1.1
        },
        "can_assign_owner": True,
    },
    
    "Workshop": {
        "name": "Workshop",
        "description": "Crafting and manufacturing space",
        "requirements": {
            "min_size": 8,
            "required_furniture_any": [
                "finished_gutter_forge",
                "finished_skinshop_loom",
                "finished_cortex_spindle",
                "finished_salvagers_bench"
            ],
            "must_be_enclosed": True,
            "must_have_roof": True,
        },
        "quality_factors": {
            "workbench": 8,
            "storage": 5,
            "size_bonus": 1,
        },
        "effects": {
            "craft_speed_mult": 0.0015,  # 1.0 to 1.15
            "skill_gain_mult": 0.002,  # 1.0 to 1.2
        },
        "can_assign_owner": True,
    },
    
    "Barracks": {
        "name": "Barracks",
        "description": "Military training and sleeping quarters",
        "requirements": {
            "min_size": 12,
            "required_furniture": {
                "crash_bed": 2,
                "finished_barracks": 1
            },
            "must_be_enclosed": True,
            "must_have_roof": True,
            "wall_type": "reinforced",
        },
        "quality_factors": {
            "locker": 5,
            "weapon_rack": 8,
            "size_bonus": 1,
        },
        "effects": {
            "sleep_quality_mult": -0.001,  # 0.9 (worse than bedroom)
            "training_speed_mult": 0.003,  # 1.0 to 1.3
            "discipline_mult": 0.001,  # 1.0 to 1.1
        },
        "can_assign_owner": False,  # Shared space
    },
    
    "Prison": {
        "name": "Prison Cell",
        "description": "Secure holding cell for prisoners",
        "requirements": {
            "min_size": 4,
            "max_size": 20,
            "required_furniture": {"crash_bed": 1},
            "max_entrances": 1,
            "must_be_enclosed": True,
            "must_have_roof": True,
            "door_type": "reinforced",
        },
        "quality_factors": {
            "size_bonus": -2,  # Smaller is worse
        },
        "effects": {
            "escape_chance_mult": -0.005,  # -0.5 at quality 100
            "mood_penalty": -0.1,  # -10 at quality 100
        },
        "can_assign_owner": True,  # Assign prisoner
    },
    
    "Hospital": {
        "name": "Hospital",
        "description": "Medical treatment facility",
        "requirements": {
            "min_size": 16,
            "required_furniture": {"crash_bed": 3},
            "must_be_enclosed": True,
            "must_have_roof": True,
        },
        "quality_factors": {
            "medicine_cabinet": 15,
            "clean_floor": 10,
            "size_bonus": 2,
        },
        "effects": {
            "healing_rate_mult": 0.005,  # 1.0 to 1.5
            "infection_resist_mult": 0.003,  # 1.0 to 1.3
        },
        "can_assign_owner": False,
    },
    
    "Social Venue": {
        "name": "Social Venue",  # Dynamic - changes based on furniture
        "description": "Entertainment and social space that evolves with furnishings",
        "requirements": {
            "min_size": 10,
            "must_be_enclosed": True,
            "must_have_roof": True,
        },
        "quality_factors": {
            # Category-based scoring (calculated dynamically)
            "bar_furniture": 15,
            "music_equipment": 20,
            "seating": 5,
            "tables": 5,
            "luxury": 30,
            "size_bonus": 2,
        },
        "effects": {
            "recreation_mult": 0.004,  # 1.0 to 1.4
            "mood_bonus": 0.08,  # 0 to 8
            "social_bonus": 0.002,  # 1.0 to 1.2
        },
        "can_assign_owner": False,
        "dynamic_naming": True,  # Flag for dynamic tier naming
    },
    
    "Dining Hall": {
        "name": "Dining Hall",
        "description": "Communal eating area",
        "requirements": {
            "min_size": 12,
            "required_furniture": {"table": 2},
            "must_be_enclosed": True,
            "must_have_roof": True,
        },
        "quality_factors": {
            "chair": 2,
            "table": 5,
            "decoration": 8,
            "size_bonus": 1,
        },
        "effects": {
            "meal_mood_mult": 0.002,  # Better meals = better mood
            "social_mult": 0.001,  # Social interaction bonus
        },
        "can_assign_owner": False,
    },
}


# =============================================================================
# ROOM VALIDATION
# =============================================================================

def validate_room(grid, tiles: List[Coord], z: int, room_type: str) -> Tuple[bool, List[str]]:
    """Check if area meets requirements for room type.
    
    Args:
        grid: Grid instance
        tiles: List of (x, y) coordinates in room
        z: Z-level
        room_type: Type of room to validate
    
    Returns:
        (valid: bool, errors: List[str])
    """
    if room_type not in ROOM_TYPES:
        return (False, [f"Unknown room type: {room_type}"])
    
    rules = ROOM_TYPES[room_type]["requirements"]
    errors = []
    
    # Size check
    if len(tiles) < rules.get("min_size", 0):
        errors.append(f"Too small (min {rules['min_size']} tiles, got {len(tiles)})")
    if len(tiles) > rules.get("max_size", 999):
        errors.append(f"Too large (max {rules['max_size']} tiles, got {len(tiles)})")
    
    # Scan contents
    contents = {}
    for x, y in tiles:
        tile = grid.get_tile(x, y, z)
        contents[tile] = contents.get(tile, 0) + 1
    
    # Required furniture (all must be present)
    for item, count in rules.get("required_furniture", {}).items():
        if contents.get(item, 0) < count:
            errors.append(f"Requires {count}x {item} (found {contents.get(item, 0)})")
    
    # Required furniture (any of list)
    if "required_furniture_any" in rules:
        has_any = any(contents.get(item, 0) > 0 for item in rules["required_furniture_any"])
        if not has_any:
            item_names = ", ".join(rules["required_furniture_any"])
            errors.append(f"Requires one of: {item_names}")
    
    # Enclosed check
    if rules.get("must_be_enclosed"):
        if not _is_area_enclosed(grid, tiles, z):
            errors.append("Must be fully enclosed by walls/doors")
    
    # Roof check
    if rules.get("must_have_roof"):
        if not _area_has_roof(grid, tiles, z):
            errors.append("Must have roof above")
    
    # Wall type check
    if "wall_type" in rules:
        if not _check_wall_type(grid, tiles, z, rules["wall_type"]):
            errors.append(f"Requires {rules['wall_type']} walls")
    
    # Entrance count
    if "max_entrances" in rules:
        entrance_count = _count_entrances(grid, tiles, z)
        if entrance_count > rules["max_entrances"]:
            errors.append(f"Too many entrances (max {rules['max_entrances']}, found {entrance_count})")
    
    # Door type check
    if "door_type" in rules:
        if not _check_door_type(grid, tiles, z, rules["door_type"]):
            errors.append(f"Requires {rules['door_type']} doors")
    
    return (len(errors) == 0, errors)


def _is_area_enclosed(grid, tiles: List[Coord], z: int) -> bool:
    """Check if area is fully enclosed by walls/doors."""
    tile_set = set(tiles)
    
    for x, y in tiles:
        # Check all 4 cardinal directions
        for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
            nx, ny = x + dx, y + dy
            
            # If neighbor is not in room, check if it's a wall/door
            if (nx, ny) not in tile_set:
                neighbor_tile = grid.get_tile(nx, ny, z)
                if neighbor_tile not in ("finished_wall", "finished_wall_advanced", "door", "finished_window"):
                    return False
    
    return True


def _area_has_roof(grid, tiles: List[Coord], z: int) -> bool:
    """Check if all tiles have roof above."""
    for x, y in tiles:
        roof_tile = grid.get_tile(x, y, z + 1)
        if roof_tile != "roof":
            return False
    return True


def _check_wall_type(grid, tiles: List[Coord], z: int, wall_type: str) -> bool:
    """Check if surrounding walls match required type."""
    tile_set = set(tiles)
    
    if wall_type == "reinforced":
        required_walls = ("finished_wall_advanced", "wall_advanced")
    else:
        required_walls = ("finished_wall", "wall")
    
    for x, y in tiles:
        for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
            nx, ny = x + dx, y + dy
            if (nx, ny) not in tile_set:
                neighbor_tile = grid.get_tile(nx, ny, z)
                if "wall" in neighbor_tile and neighbor_tile not in required_walls:
                    return False
    
    return True


def _count_entrances(grid, tiles: List[Coord], z: int) -> int:
    """Count number of doors/windows leading into room."""
    tile_set = set(tiles)
    entrances = 0
    
    for x, y in tiles:
        for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
            nx, ny = x + dx, y + dy
            if (nx, ny) not in tile_set:
                neighbor_tile = grid.get_tile(nx, ny, z)
                if neighbor_tile in ("door", "finished_window"):
                    entrances += 1
    
    return entrances


def _check_door_type(grid, tiles: List[Coord], z: int, door_type: str) -> bool:
    """Check if doors match required type."""
    # For now, all doors are the same type
    # Future: add reinforced doors
    return True


# =============================================================================
# ROOM QUALITY CALCULATION
# =============================================================================

def calculate_room_quality(grid, tiles: List[Coord], z: int, room_type: str) -> int:
    """Calculate room quality score (0-100).
    
    Based on:
    - Size (bonus for larger rooms)
    - Furniture quality/quantity
    - Cleanliness (future)
    - Beauty/decorations (future)
    """
    if room_type not in ROOM_TYPES:
        return 0
    
    quality_factors = ROOM_TYPES[room_type].get("quality_factors", {})
    score = 50  # Base score
    
    # Scan contents
    contents = {}
    for x, y in tiles:
        tile = grid.get_tile(x, y, z)
        contents[tile] = contents.get(tile, 0) + 1
    
    # Check if this is a Social Venue (uses category-based scoring)
    if room_type == "Social Venue":
        # Count furniture by category
        category_counts = _count_venue_furniture_categories(contents)
        
        # Add category bonuses
        for category, bonus in quality_factors.items():
            if category == "size_bonus":
                continue
            count = category_counts.get(category, 0)
            score += bonus * count
    else:
        # Standard item-based scoring
        for item, bonus in quality_factors.items():
            if item == "size_bonus":
                continue
            if item in contents:
                score += bonus * contents[item]
    
    # Add size bonus
    size_bonus = quality_factors.get("size_bonus", 0)
    min_size = ROOM_TYPES[room_type]["requirements"].get("min_size", 0)
    extra_tiles = max(0, len(tiles) - min_size)
    score += size_bonus * extra_tiles
    
    # Clamp to 0-100
    return max(0, min(100, score))


def _count_venue_furniture_categories(contents: dict) -> dict:
    """Count furniture items by category for Social Venues.
    
    Args:
        contents: Dict of {tile_type: count}
    
    Returns:
        Dict of {category: count}
    """
    category_counts = {}
    
    for category, furniture_list in VENUE_FURNITURE_CATEGORIES.items():
        count = 0
        for furniture_item in furniture_list:
            count += contents.get(furniture_item, 0)
        if count > 0:
            category_counts[category] = count
    
    return category_counts


def get_venue_tier_name(quality: int, contents: dict) -> str:
    """Determine Social Venue tier name based on quality and furniture.
    
    Args:
        quality: Room quality score (0-100)
        contents: Dict of {tile_type: count}
    
    Returns:
        Venue tier name (e.g., "Nightclub", "Bar", etc.)
    """
    # Count furniture by category
    category_counts = _count_venue_furniture_categories(contents)
    
    # Check what furniture is present
    has_bar = category_counts.get("bar_furniture", 0) > 0
    has_music = category_counts.get("music_equipment", 0) > 0
    has_luxury = category_counts.get("luxury", 0) > 0
    
    # Check for specific items
    has_stage = any(item in contents for item in ["stage", "finished_stage"])
    has_instruments = any(item in contents for item in 
                         ["scrap_guitar_placed", "drum_kit_placed", "synth_placed"])
    
    # Tier by quality + content
    if quality >= 81 and has_luxury:
        return "Grand Hall"
    elif quality >= 61 and has_music and has_stage:
        return "Nightclub"
    elif quality >= 41 and has_music:
        return "Music Venue"
    elif quality >= 21 and has_bar:
        return "Bar"
    else:
        return "Dive Bar"


# =============================================================================
# ROOM CREATION & MANAGEMENT
# =============================================================================

def create_room(grid, tiles: List[Coord], z: int, room_type: str) -> Tuple[bool, Optional[int], List[str]]:
    """Create a new room.
    
    Args:
        grid: Grid instance
        tiles: List of (x, y) coordinates
        z: Z-level
        room_type: Type of room
    
    Returns:
        (success: bool, room_id: Optional[int], errors: List[str])
    """
    global _next_room_id
    
    # Validate
    valid, errors = validate_room(grid, tiles, z, room_type)
    if not valid:
        return (False, None, errors)
    
    # Check for overlaps
    for x, y in tiles:
        if (x, y, z) in _TILE_TO_ROOM:
            existing_id = _TILE_TO_ROOM[(x, y, z)]
            existing_type = _ROOMS[existing_id].get("type", "Unknown")
            errors.append(f"Overlaps with existing room (ID {existing_id}: {existing_type})")
            return (False, None, errors)
    
    # Calculate quality
    quality = calculate_room_quality(grid, tiles, z, room_type)
    
    # Create room
    room_id = _next_room_id
    _next_room_id += 1
    
    # Calculate bounds
    xs = [x for x, y in tiles]
    ys = [y for x, y in tiles]
    bounds = (min(xs), min(ys), max(xs), max(ys))
    
    # Count entrances
    entrance_count = _count_entrances(grid, tiles, z)
    
    # Determine display name (dynamic for Social Venues)
    display_name = ROOM_TYPES[room_type]["name"]
    if ROOM_TYPES[room_type].get("dynamic_naming", False):
        # Scan contents for dynamic naming
        contents = {}
        for x, y in tiles:
            tile = grid.get_tile(x, y, z)
            contents[tile] = contents.get(tile, 0) + 1
        print(f"[Room Debug] Contents: {contents}")
        print(f"[Room Debug] Quality: {quality}")
        display_name = get_venue_tier_name(quality, contents)
        print(f"[Room Debug] Venue name: {display_name}")
    
    _ROOMS[room_id] = {
        "id": room_id,
        "type": room_type,
        "tiles": tiles.copy(),
        "z": z,
        "bounds": bounds,
        "size": len(tiles),
        "quality": quality,
        "entrance_count": entrance_count,
        "owner": None,
        "name": display_name,  # Dynamic name for Social Venues
        "restricted": False,
        "effects": _calculate_room_effects(room_type, quality),
    }
    
    # Update reverse lookup
    for x, y in tiles:
        _TILE_TO_ROOM[(x, y, z)] = room_id
    
    print(f"[Room] Created {room_type} (ID {room_id}) with {len(tiles)} tiles, quality {quality}")
    
    return (True, room_id, [])


def _calculate_room_effects(room_type: str, quality: int) -> dict:
    """Calculate room effects from quality score."""
    if room_type not in ROOM_TYPES:
        return {}
    
    effect_formulas = ROOM_TYPES[room_type].get("effects", {})
    effects = {}
    
    for effect_name, multiplier in effect_formulas.items():
        effects[effect_name] = quality * multiplier
    
    return effects


def delete_room(room_id: int) -> bool:
    """Delete a room."""
    if room_id not in _ROOMS:
        return False
    
    room = _ROOMS[room_id]
    
    # Remove from reverse lookup
    for x, y in room["tiles"]:
        z = room["z"]
        if (x, y, z) in _TILE_TO_ROOM:
            del _TILE_TO_ROOM[(x, y, z)]
    
    # Remove room
    del _ROOMS[room_id]
    
    print(f"[Room] Deleted room {room_id}")
    return True


def get_room_at(x: int, y: int, z: int) -> Optional[int]:
    """Get room ID at location."""
    return _TILE_TO_ROOM.get((x, y, z))


def get_room_data(room_id: int) -> Optional[dict]:
    """Get room data by ID."""
    return _ROOMS.get(room_id)


def refresh_venue_name(grid, room_id: int) -> bool:
    """Refresh the name of a Social Venue based on current furniture.
    
    Call this when furniture is added/removed from a Social Venue.
    
    Args:
        grid: Grid instance
        room_id: Room ID to refresh
    
    Returns:
        True if name was updated, False if not a Social Venue or doesn't exist
    """
    room = _ROOMS.get(room_id)
    if not room:
        return False
    
    room_type = room.get("type")
    if room_type != "Social Venue":
        return False
    
    # Recalculate quality and name
    tiles = room.get("tiles", [])
    z = room.get("z", 0)
    
    # Scan contents
    contents = {}
    for x, y in tiles:
        tile = grid.get_tile(x, y, z)
        contents[tile] = contents.get(tile, 0) + 1
    
    # Recalculate quality
    quality = calculate_room_quality(grid, tiles, z, room_type)
    
    # Get new name
    new_name = get_venue_tier_name(quality, contents)
    
    # Update room data
    old_name = room.get("name", "Social Venue")
    room["quality"] = quality
    room["name"] = new_name
    room["effects"] = _calculate_room_effects(room_type, quality)
    
    if new_name != old_name:
        print(f"[Room] Venue upgraded: {old_name} → {new_name} (quality {quality})")
    
    return True


def get_all_rooms() -> Dict[int, dict]:
    """Get all rooms."""
    return _ROOMS.copy()


def assign_room_owner(room_id: int, colonist_id: Optional[str]) -> bool:
    """Assign room to colonist."""
    if room_id not in _ROOMS:
        return False
    
    room_type = _ROOMS[room_id]["type"]
    if not ROOM_TYPES[room_type].get("can_assign_owner", False):
        return False
    
    _ROOMS[room_id]["owner"] = colonist_id
    return True


def set_room_name(room_id: int, name: Optional[str]) -> bool:
    """Set custom room name."""
    if room_id not in _ROOMS:
        return False
    
    _ROOMS[room_id]["name"] = name
    return True


def set_room_restricted(room_id: int, restricted: bool) -> bool:
    """Set room access restriction."""
    if room_id not in _ROOMS:
        return False
    
    _ROOMS[room_id]["restricted"] = restricted
    return True
