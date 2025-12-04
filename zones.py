"""Zone management for stockpiles and other designated areas.

Zones are rectangular areas on the grid that have special behaviors:
- Stockpile zones: Where hauled resources are stored
- Future: Growing zones, dumping zones, etc.

Stockpile tiles have per-tile storage:
- Each tile can hold one resource type
- Each tile has a capacity (e.g., 10 units)
- Visual representation shows stack level

Stockpile filters:
- Each zone has resource filters (allow_wood, allow_mineral, etc.)
- Hauling respects these filters when selecting destination

All coordinates are 3D (x, y, z) to support multi-level buildings.
"""

from typing import Dict, List, Tuple, Optional, Set

Coord3D = Tuple[int, int, int]  # (x, y, z)


class ZoneType:
    STOCKPILE = "stockpile"


# Capacity per stockpile tile (high for testing - burst harvest and build)
STOCKPILE_TILE_CAPACITY = 1000

# Registry of all zones: {zone_id: zone_data}
_ZONES: Dict[int, dict] = {}
_NEXT_ZONE_ID = 1

# Quick lookup: coord -> zone_id for tiles that belong to zones
_TILE_TO_ZONE: Dict[Coord3D, int] = {}

# Per-tile storage: {(x, y, z): {"type": "wood", "amount": 5}}
_TILE_STORAGE: Dict[Coord3D, dict] = {}

# Tiles pending removal - items need to be relocated before zone is fully removed
# Key: (x, y, z), Value: True if pending
_PENDING_REMOVAL: Dict[Coord3D, bool] = {}


# Tiles that are NEVER valid for stockpiles (walls, doors, windows, workstations)
_FORBIDDEN_STOCKPILE_TILES = {
    "wall", "finished_wall", "wall_advanced", "finished_wall_advanced",
    "door", "finished_window", "window", "window_tile",
    "salvagers_bench", "finished_salvagers_bench",
    "generator", "finished_generator",
    "stove", "finished_stove",
    "roof",  # Unallowed roof tiles
}

# Tiles valid for stockpiles on Z > 0 (must be explicitly walkable/allowed)
_VALID_UPPER_STOCKPILE_TILES = {
    "finished_floor", "floor", "roof_access", "roof_floor", "fire_escape_platform",
}


def _is_valid_stockpile_tile(grid, x: int, y: int, z: int = 0) -> bool:
    """Check if a tile can have a stockpile zone.
    
    Z=0 (ground): Any walkable tile except walls/doors/windows/workstations
    Z>0 (upper): Only floor tiles and allowed roof tiles
    """
    if grid is None:
        return True
    tile = grid.get_tile(x, y, z)
    
    # Always forbidden
    if tile in _FORBIDDEN_STOCKPILE_TILES:
        return False
    
    if z == 0:
        # Ground level: any walkable tile is valid
        return grid.is_walkable(x, y, z)
    else:
        # Upper levels: only specific floor/allowed tiles
        return tile in _VALID_UPPER_STOCKPILE_TILES


def create_stockpile_zone(tiles: List[Coord3D], grid=None, z: int = 0) -> int:
    """Create a new stockpile zone covering the given tiles.
    
    Args:
        tiles: List of (x, y) or (x, y, z) coordinates
        grid: Grid for validation
        z: Default Z-level if tiles are 2D
    
    Returns the zone ID.
    """
    global _NEXT_ZONE_ID
    
    zone_id = _NEXT_ZONE_ID
    _NEXT_ZONE_ID += 1
    
    # Normalize tiles to 3D coordinates
    tiles_3d = []
    for t in tiles:
        if len(t) == 2:
            tiles_3d.append((t[0], t[1], z))
        else:
            tiles_3d.append(t)
    
    # Filter out tiles that are already in a zone or have walls/doors
    valid_tiles = [t for t in tiles_3d if t not in _TILE_TO_ZONE and _is_valid_stockpile_tile(grid, t[0], t[1], t[2])]
    
    if not valid_tiles:
        return -1  # No valid tiles
    
    _ZONES[zone_id] = {
        "type": ZoneType.STOCKPILE,
        "tiles": set(valid_tiles),
        "stored": {},  # {resource_type: amount} stored in this zone
        "z": z,  # Primary Z-level of this zone
        # Resource filters - all enabled by default
        "allow_wood": True,
        "allow_mineral": True,
        "allow_scrap": True,
        "allow_metal": True,
        "allow_power": True,
        "allow_raw_food": True,
        "allow_cooked_meal": True,
    }
    
    # Register tiles
    for tile in valid_tiles:
        _TILE_TO_ZONE[tile] = zone_id
    
    return zone_id


def mark_tile_for_removal(x: int, y: int, z: int = 0) -> bool:
    """Mark a stockpile tile for removal. Items will be relocated first.
    
    Returns True if tile was marked, False if not a stockpile tile.
    """
    coord = (x, y, z)
    if coord not in _TILE_TO_ZONE:
        return False
    
    # Check if there are items to relocate
    storage = _TILE_STORAGE.get(coord)
    if storage is not None and storage.get("amount", 0) > 0:
        # Has items - mark for pending removal
        _PENDING_REMOVAL[coord] = True
        return True
    else:
        # No items - can remove immediately
        return remove_zone_at(x, y, z)


def is_pending_removal(x: int, y: int, z: int = 0) -> bool:
    """Check if a stockpile tile is pending removal (waiting for items to relocate)."""
    return _PENDING_REMOVAL.get((x, y, z), False)


def get_pending_removal_tiles() -> List[Coord3D]:
    """Get all tiles that are pending removal."""
    return list(_PENDING_REMOVAL.keys())


def complete_tile_removal(x: int, y: int, z: int = 0) -> bool:
    """Complete removal of a tile after items have been relocated.
    
    Called when all items have been moved from a pending removal tile.
    Returns True if removal was completed.
    """
    coord = (x, y, z)
    if coord not in _PENDING_REMOVAL:
        return False
    
    # Remove pending flag
    del _PENDING_REMOVAL[coord]
    
    # Now actually remove the zone
    return remove_zone_at(x, y, z)


def remove_zone_at(x: int, y: int, z: int = 0) -> bool:
    """Remove zone membership from a single tile immediately.
    
    WARNING: This will lose any items on the tile. Use mark_tile_for_removal
    to safely relocate items first.
    
    Returns True if a zone was removed from this tile.
    """
    coord = (x, y, z)
    zone_id = _TILE_TO_ZONE.get(coord)
    if zone_id is None:
        return False
    
    # Remove from tile lookup
    del _TILE_TO_ZONE[coord]
    
    # Remove from zone's tile set
    zone = _ZONES.get(zone_id)
    if zone:
        zone["tiles"].discard(coord)
        # If zone is now empty, remove it entirely
        if not zone["tiles"]:
            del _ZONES[zone_id]
    
    # Clear any storage on this tile
    _TILE_STORAGE.pop(coord, None)
    
    # Clear pending removal flag if set
    _PENDING_REMOVAL.pop(coord, None)
    
    return True


def get_zone_at(x: int, y: int, z: int = 0) -> Optional[dict]:
    """Return the zone data at (x, y, z), if any."""
    zone_id = _TILE_TO_ZONE.get((x, y, z))
    if zone_id is None:
        return None
    return _ZONES.get(zone_id)


def get_zone_id_at(x: int, y: int, z: int = 0) -> Optional[int]:
    """Return the zone ID at (x, y, z), if any."""
    return _TILE_TO_ZONE.get((x, y, z))


def is_stockpile_zone(x: int, y: int, z: int = 0) -> bool:
    """Return True if (x, y, z) is part of a stockpile zone."""
    zone = get_zone_at(x, y, z)
    return zone is not None and zone.get("type") == ZoneType.STOCKPILE


def get_all_stockpile_tiles() -> Set[Coord3D]:
    """Return all tiles that are part of stockpile zones."""
    tiles = set()
    for zone_id, zone in _ZONES.items():
        if zone.get("type") == ZoneType.STOCKPILE:
            tiles.update(zone.get("tiles", set()))
    return tiles


def _zone_allows_resource(zone: dict, resource_type: str) -> bool:
    """Check if a zone's filters allow a resource type."""
    filter_key = f"allow_{resource_type}"
    # Default to True if filter doesn't exist (backwards compatibility)
    return zone.get(filter_key, True)


def find_stockpile_tile_for_resource(resource_type: str, exclude_pending: bool = True, z: int = None, from_x: int = None, from_y: int = None) -> Optional[Coord3D]:
    """Find the nearest valid stockpile tile to store a resource.
    
    Priority:
    1. Nearest tile already storing this resource type with space
    2. Nearest empty stockpile tile
    
    Args:
        resource_type: Type of resource to store
        exclude_pending: If True, exclude tiles marked for removal
        z: If specified, prefer tiles on this Z-level
        from_x, from_y: Source position for distance calculation (Manhattan)
    
    Returns coordinates (x, y, z) of an available tile, or None if no space.
    """
    # Collect all valid candidates: (distance, priority, tile)
    # priority: 0 = same resource type (stack), 1 = empty tile
    candidates = []
    
    for zone_id, zone in _ZONES.items():
        if zone.get("type") != ZoneType.STOCKPILE:
            continue
        
        # Check zone filter
        if not _zone_allows_resource(zone, resource_type):
            continue
        
        for tile in zone.get("tiles", set()):
            # Skip tiles pending removal
            if exclude_pending and tile in _PENDING_REMOVAL:
                continue
            
            # Calculate distance (Manhattan, same Z preferred)
            tx, ty, tz = tile
            if from_x is not None and from_y is not None:
                dist = abs(tx - from_x) + abs(ty - from_y)
                # Penalize different Z-level
                if z is not None and tz != z:
                    dist += 100
            else:
                dist = 0
                if z is not None and tz != z:
                    dist = 100
            
            storage = _TILE_STORAGE.get(tile)
            
            if storage is None:
                # Empty tile - priority 1
                candidates.append((dist, 1, tile))
            elif storage.get("type") == resource_type:
                # Same resource type - check capacity, priority 0 (prefer stacking)
                if storage.get("amount", 0) < STOCKPILE_TILE_CAPACITY:
                    candidates.append((dist, 0, tile))
    
    if not candidates:
        return None
    
    # Sort by distance first, then by priority (same-type preferred at equal distance)
    candidates.sort(key=lambda x: (x[0], x[1]))
    return candidates[0][2]


def get_tile_storage(x: int, y: int, z: int = 0) -> Optional[dict]:
    """Get storage info for a stockpile tile."""
    return _TILE_STORAGE.get((x, y, z))


def get_all_tile_storage() -> Dict[Coord3D, dict]:
    """Get all tile storage for rendering."""
    return _TILE_STORAGE.copy()


def add_to_tile_storage(x: int, y: int, z: int, resource_type: str, amount: int) -> int:
    """Add resources to a specific stockpile tile.
    
    Returns the amount actually stored (may be less if capacity reached).
    """
    if not is_stockpile_zone(x, y, z):
        return 0
    
    coord = (x, y, z)
    storage = _TILE_STORAGE.get(coord)
    
    if storage is None:
        # Empty tile - start new stack
        stored = min(amount, STOCKPILE_TILE_CAPACITY)
        _TILE_STORAGE[coord] = {"type": resource_type, "amount": stored}
        return stored
    
    if storage.get("type") != resource_type:
        # Different resource type - can't mix
        return 0
    
    # Same type - add up to capacity
    current = storage.get("amount", 0)
    space = STOCKPILE_TILE_CAPACITY - current
    stored = min(amount, space)
    storage["amount"] = current + stored
    return stored


def remove_from_tile_storage(x: int, y: int, z: int, amount: int) -> Optional[dict]:
    """Remove resources from a stockpile tile.
    
    Returns {"type": str, "amount": int} of what was removed, or None.
    """
    coord = (x, y, z)
    storage = _TILE_STORAGE.get(coord)
    if storage is None:
        return None
    
    current = storage.get("amount", 0)
    removed = min(amount, current)
    
    if removed <= 0:
        return None
    
    result = {"type": storage["type"], "amount": removed}
    
    storage["amount"] = current - removed
    if storage["amount"] <= 0:
        del _TILE_STORAGE[coord]
    
    return result


def add_to_zone_storage(x: int, y: int, z: int, resource_type: str, amount: int) -> bool:
    """Add resources to the zone's storage at (x, y, z).
    
    This updates both per-tile storage and zone totals.
    Returns True if successful.
    """
    stored = add_to_tile_storage(x, y, z, resource_type, amount)
    if stored <= 0:
        return False
    
    # Also update zone totals
    coord = (x, y, z)
    zone_id = _TILE_TO_ZONE.get(coord)
    if zone_id is not None:
        zone = _ZONES.get(zone_id)
        if zone is not None:
            if resource_type not in zone["stored"]:
                zone["stored"][resource_type] = 0
            zone["stored"][resource_type] += stored
    
    return True


def get_zone_storage(zone_id: int) -> Dict[str, int]:
    """Get the stored resources in a zone."""
    zone = _ZONES.get(zone_id)
    if zone is None:
        return {}
    return zone.get("stored", {}).copy()


def remove_zone(zone_id: int) -> bool:
    """Remove a zone and unregister its tiles."""
    zone = _ZONES.get(zone_id)
    if zone is None:
        return False
    
    # Unregister tiles
    for tile in zone.get("tiles", set()):
        _TILE_TO_ZONE.pop(tile, None)
    
    del _ZONES[zone_id]
    return True


def get_all_zones() -> Dict[int, dict]:
    """Return all zones for rendering/debugging."""
    return _ZONES.copy()


def find_stockpile_with_resource(resource_type: str, z: int = None) -> Optional[Coord3D]:
    """Find a stockpile tile that has the specified resource.
    
    Used for construction supply - colonists need to fetch materials.
    
    Args:
        resource_type: Type of resource to find
        z: If specified, prefer tiles on this Z-level
    
    Returns coordinates (x, y, z) of a tile with the resource, or None.
    """
    preferred = None
    fallback = None
    
    for coord, storage in _TILE_STORAGE.items():
        if storage.get("type") == resource_type and storage.get("amount", 0) > 0:
            if z is not None and coord[2] == z:
                preferred = coord
            elif fallback is None:
                fallback = coord
    
    return preferred or fallback


def get_total_stored(resource_type: str) -> int:
    """Get total amount of a resource stored across all stockpiles."""
    total = 0
    for storage in _TILE_STORAGE.values():
        if storage.get("type") == resource_type:
            total += storage.get("amount", 0)
    return total


def process_stockpile_relocation(jobs_module) -> int:
    """Create relocation jobs for items in tiles pending removal.
    
    Called each tick from main loop.
    Returns number of jobs created.
    """
    jobs_created = 0
    
    for coord in list(_PENDING_REMOVAL.keys()):
        x, y, z = coord
        storage = _TILE_STORAGE.get(coord)
        
        if storage is None or storage.get("amount", 0) <= 0:
            # No items left - complete the removal
            complete_tile_removal(x, y, z)
            # Also clear any construction site wait flag
            import buildings
            buildings.clear_stockpile_wait(x, y, z)
            continue
        
        # Check if there's already a relocation job for this tile
        if jobs_module.has_job_of_type_at(x, y, z, "relocate"):
            continue
        
        # Find nearest valid destination for this resource type
        resource_type = storage.get("type", "")
        dest = find_stockpile_tile_for_resource(resource_type, exclude_pending=True, z=z, from_x=x, from_y=y)
        
        if dest is None:
            # No available stockpile - can't relocate yet
            continue
        
        # Create relocation job (uses haul job type)
        jobs_module.add_job(
            "relocate",
            x, y,
            required=10,  # Quick job
            resource_type=resource_type,
            dest_x=dest[0],
            dest_y=dest[1],
            dest_z=dest[2],
            z=z,
            category="haul",
        )
        jobs_created += 1
    
    return jobs_created


def process_filter_mismatch_relocation(jobs_module) -> int:
    """Create relocation jobs for resources on stockpiles that no longer allow them.
    
    Called each tick from main loop. If a player changes a stockpile filter to
    disallow a resource type, this will move those resources to a valid stockpile.
    
    Returns number of jobs created.
    """
    jobs_created = 0
    
    for coord, storage in list(_TILE_STORAGE.items()):
        x, y, z = coord
        resource_type = storage.get("type", "")
        amount = storage.get("amount", 0)
        
        if amount <= 0:
            continue
        
        # Get the zone this tile belongs to
        zone_id = _TILE_TO_ZONE.get(coord)
        if zone_id is None:
            continue
        
        zone = _ZONES.get(zone_id)
        if zone is None:
            continue
        
        # Check if this zone still allows this resource type
        if _zone_allows_resource(zone, resource_type):
            continue  # Filter still allows it, no action needed
        
        # Resource is on a stockpile that no longer allows it!
        # Check if there's already a relocation job for this tile
        if jobs_module.has_job_of_type_at(x, y, z, "relocate"):
            continue
        
        # Find nearest valid destination that DOES allow this resource
        dest = find_stockpile_tile_for_resource(resource_type, exclude_pending=True, z=z, from_x=x, from_y=y)
        
        if dest is None:
            # No stockpile allows this resource - leave it where it is
            continue
        
        # Create relocation job
        jobs_module.add_job(
            "relocate",
            x, y,
            required=10,  # Quick job
            resource_type=resource_type,
            dest_x=dest[0],
            dest_y=dest[1],
            dest_z=dest[2],
            z=z,
            category="haul",
        )
        jobs_created += 1
        print(f"[Stockpile] Relocating {resource_type} from ({x},{y}) - filter changed")
    
    return jobs_created


# ============================================================================
# Zone Filter Management
# ============================================================================

def get_zone_filters(zone_id: int) -> Optional[Dict[str, bool]]:
    """Get the resource filters for a zone.
    
    Returns dict like {"wood": True, "mineral": False, ...} or None if zone not found.
    """
    zone = _ZONES.get(zone_id)
    if zone is None:
        return None
    
    return {
        "wood": zone.get("allow_wood", True),
        "mineral": zone.get("allow_mineral", True),
        "scrap": zone.get("allow_scrap", True),
        "metal": zone.get("allow_metal", True),
        "power": zone.get("allow_power", True),
        "raw_food": zone.get("allow_raw_food", True),
        "cooked_meal": zone.get("allow_cooked_meal", True),
    }


def set_zone_filter(zone_id: int, resource_type: str, allowed: bool) -> bool:
    """Set a resource filter for a zone.
    
    Returns True if successful.
    """
    zone = _ZONES.get(zone_id)
    if zone is None:
        return False
    
    filter_key = f"allow_{resource_type}"
    zone[filter_key] = allowed
    return True


def toggle_zone_filter(zone_id: int, resource_type: str) -> Optional[bool]:
    """Toggle a resource filter for a zone.
    
    Returns the new value, or None if zone not found.
    """
    zone = _ZONES.get(zone_id)
    if zone is None:
        return None
    
    filter_key = f"allow_{resource_type}"
    current = zone.get(filter_key, True)
    zone[filter_key] = not current
    return not current


def get_zone_info(zone_id: int) -> Optional[dict]:
    """Get full zone info including filters and tile count."""
    zone = _ZONES.get(zone_id)
    if zone is None:
        return None
    
    return {
        "id": zone_id,
        "type": zone.get("type"),
        "tile_count": len(zone.get("tiles", set())),
        "z": zone.get("z", 0),
        "filters": get_zone_filters(zone_id),
        "stored": zone.get("stored", {}),
    }


# --- Save/Load ---

def get_save_state() -> dict:
    """Get zones state for saving."""
    # Convert sets to lists for JSON serialization
    zones_data = {}
    for zone_id, zone in _ZONES.items():
        zones_data[str(zone_id)] = {
            "type": zone.get("type"),
            "z": zone.get("z", 0),
            "tiles": [list(t) for t in zone.get("tiles", set())],
            "filters": {k: v for k, v in zone.items() if k.startswith("allow_")},
        }
    
    # Tile storage
    storage_data = {}
    for coord, storage in _TILE_STORAGE.items():
        key = f"{coord[0]},{coord[1]},{coord[2]}"
        storage_data[key] = storage
    
    return {
        "zones": zones_data,
        "tile_storage": storage_data,
        "next_zone_id": _NEXT_ZONE_ID,
    }


def load_save_state(state: dict):
    """Restore zones state from save."""
    global _ZONES, _TILE_TO_ZONE, _TILE_STORAGE, _PENDING_REMOVAL, _NEXT_ZONE_ID
    
    _ZONES.clear()
    _TILE_TO_ZONE.clear()
    _TILE_STORAGE.clear()
    _PENDING_REMOVAL.clear()
    
    _NEXT_ZONE_ID = state.get("next_zone_id", 1)
    
    # Restore zones
    for zone_id_str, zone_data in state.get("zones", {}).items():
        zone_id = int(zone_id_str)
        tiles = set(tuple(t) for t in zone_data.get("tiles", []))
        
        zone = {
            "type": zone_data.get("type"),
            "z": zone_data.get("z", 0),
            "tiles": tiles,
        }
        # Restore filters
        for k, v in zone_data.get("filters", {}).items():
            zone[k] = v
        
        _ZONES[zone_id] = zone
        
        # Rebuild tile-to-zone lookup
        for tile in tiles:
            _TILE_TO_ZONE[tile] = zone_id
    
    # Restore tile storage
    for key, storage in state.get("tile_storage", {}).items():
        parts = key.split(",")
        coord = (int(parts[0]), int(parts[1]), int(parts[2]))
        _TILE_STORAGE[coord] = storage
