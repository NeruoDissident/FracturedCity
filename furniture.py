"""
Furniture placement system.

Handles placing furniture items (from stockpiles) as building tiles.
"""

from typing import Optional
from grid import Grid
import items
import jobs as jobs_module


# Mapping of furniture item IDs to their building tile types
FURNITURE_TILE_MAPPING = {
    "crash_bed": "crash_bed",
    "comfort_chair": "comfort_chair",
    "bar_stool": "bar_stool",
    "storage_locker": "storage_locker",
    "scrap_guitar": "scrap_guitar_placed",
    "drum_kit": "drum_kit_placed",
    "synth": "synth_placed",
    "harmonica": "harmonica_placed",
    "amp": "amp_placed",
}

# Furniture size definitions (width, height) in tiles
# Items not listed default to 1x1
FURNITURE_SIZES = {
    "crash_bed": (1, 2),  # 1x2 vertical bed
    # Future: Add more multi-tile furniture as needed
}


def get_furniture_size(item_id: str) -> tuple:
    """Get the size (width, height) of a furniture item.
    
    Returns:
        (width, height) tuple in tiles. Defaults to (1, 1) if not specified.
    """
    return FURNITURE_SIZES.get(item_id, (1, 1))


def can_place_furniture(grid: Grid, x: int, y: int, z: int, item_id: str) -> bool:
    """Check if furniture can be placed at the given location.
    
    For multi-tile furniture, (x, y) is the bottom-left origin tile.
    All tiles in the footprint must be valid floor tiles.
    
    Args:
        grid: The game grid
        x, y, z: Target coordinates (origin for multi-tile)
        item_id: ID of the furniture item to place
        
    Returns:
        True if furniture can be placed here
    """
    # Check if item is valid furniture
    if item_id not in FURNITURE_TILE_MAPPING:
        return False
    
    # Get size (defaults to 1x1)
    width, height = get_furniture_size(item_id)
    
    # Check all tiles in footprint
    for dy in range(height):
        for dx in range(width):
            check_x = x + dx
            check_y = y + dy
            
            if not grid.in_bounds(check_x, check_y, z):
                return False
            
            # Must be on a floor or stage tile
            tile = grid.get_tile(check_x, check_y, z)
            if tile not in ("finished_floor", "floor", "finished_stage", "finished_stage_stairs"):
                return False
            
            # Tile must be walkable (not blocked)
            if not grid.is_walkable(check_x, check_y, z):
                return False
    
    return True


def place_furniture_from_stockpile(grid: Grid, x: int, y: int, z: int, item_id: str) -> bool:
    """Create a job to place furniture from stockpile at the given location.
    
    Args:
        grid: The game grid
        x, y, z: Target coordinates
        item_id: ID of the furniture item to place
        
    Returns:
        True if placement job was created
    """
    if not can_place_furniture(grid, x, y, z, item_id):
        return False
    
    # Check if there's already a job here
    if jobs_module.get_job_at(x, y, z) is not None:
        return False
    
    # Get the building tile type for this furniture
    tile_type = FURNITURE_TILE_MAPPING.get(item_id)
    if tile_type is None:
        return False
    
    # Create a "place_furniture" job
    # Colonist will fetch the item from stockpile and place it
    jobs_module.add_job(
        "place_furniture",
        x, y,
        required=20,  # Quick placement job
        furniture_item=item_id,
        furniture_tile=tile_type,
        z=z,
    )
    
    return True


def place_furniture_direct(grid: Grid, x: int, y: int, z: int, item_id: str) -> bool:
    """Directly place furniture (for world items already at location).
    
    Args:
        grid: The game grid
        x, y, z: Target coordinates
        item_id: ID of the furniture item
        
    Returns:
        True if furniture was placed
    """
    if not can_place_furniture(grid, x, y, z, item_id):
        return False
    
    tile_type = FURNITURE_TILE_MAPPING.get(item_id)
    if tile_type is None:
        return False
    
    # Store original tile type before placing furniture (for rendering background)
    original_tile = grid.get_tile(x, y, z)
    if original_tile and original_tile not in ("empty", "air"):
        grid.base_tiles[(x, y, z)] = original_tile
        print(f"[Furniture] Storing base tile at ({x}, {y}, {z}): {original_tile}")
    
    # Place the furniture tile
    grid.set_tile(x, y, tile_type, z=z)
    
    # Mark as walkable or not based on furniture type
    # Beds and large furniture block movement
    if item_id in ("crash_bed", "comfort_chair", "storage_locker", "drum_kit", "synth"):
        grid.walkable[z][y][x] = False
    else:
        # Small items like stools, guitars, harmonicas don't block
        grid.walkable[z][y][x] = True
    
    return True
