"""
Crop growth system for Fractured City.

Crops are grown in plant beds (workstations) and progress through growth stages:
- Seedling (just planted)
- Growing (mid-growth)
- Mature (ready to harvest)

Growth is automatic and tick-based. When mature, a harvest job is created.
"""

from typing import Dict, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from grid import Grid

# Crop definitions
CROPS = {
    "tomato": {
        "name": "Tomato",
        "seed_item": "tomato_seed",
        "harvest_item": "tomato",
        "category": "vegetable",  # Category for tag-based recipe matching
        "growth_stages": 3,
        "ticks_per_stage": 3000,  # 3 in-game hours per stage (9 hours total, 1000 ticks/hour)
        "sprites": [
            "crop_tomato_seedling",
            "crop_tomato_growing", 
            "crop_tomato_mature"
        ],
        "harvest_yield": 2,  # Number of tomatoes harvested
    }
}

# Track active crops: {(x, y, z): crop_data}
_ACTIVE_CROPS: Dict[Tuple[int, int, int], dict] = {}


def plant_crop(x: int, y: int, z: int, crop_type: str, game_tick: int = 0) -> bool:
    """Plant a crop at the given position.
    
    Returns True if successful, False if invalid crop type or position occupied.
    """
    if crop_type not in CROPS:
        return False
    
    if (x, y, z) in _ACTIVE_CROPS:
        return False  # Already has a crop
    
    _ACTIVE_CROPS[(x, y, z)] = {
        "crop_type": crop_type,
        "stage": 0,
        "growth_timer": 0,
        "planted_tick": game_tick,
    }
    
    # Mark tile dirty so seedling sprite appears
    from grid_arcade import mark_tile_dirty_global
    mark_tile_dirty_global(x, y, z)
    
    print(f"[Crops] Planted {crop_type} at ({x}, {y}, {z}) - starting at stage 0 (seedling)")
    return True


def get_crop_at(x: int, y: int, z: int) -> Optional[dict]:
    """Get crop data at position, or None."""
    return _ACTIVE_CROPS.get((x, y, z))


def remove_crop(x: int, y: int, z: int) -> None:
    """Remove crop at position (after harvest or destruction)."""
    if (x, y, z) in _ACTIVE_CROPS:
        del _ACTIVE_CROPS[(x, y, z)]
        # Mark tile dirty so crop sprite is removed from renderer
        from grid_arcade import mark_tile_dirty_global
        mark_tile_dirty_global(x, y, z)
        print(f"[Crops] Removed crop at ({x}, {y}, {z})")


def is_crop_mature(x: int, y: int, z: int) -> bool:
    """Check if crop is ready to harvest."""
    crop = _ACTIVE_CROPS.get((x, y, z))
    if crop is None:
        return False
    
    crop_def = CROPS.get(crop["crop_type"])
    if crop_def is None:
        return False
    
    return crop["stage"] >= crop_def["growth_stages"] - 1


def get_crop_sprite(x: int, y: int, z: int) -> Optional[str]:
    """Get the sprite name for the crop at this position."""
    crop = _ACTIVE_CROPS.get((x, y, z))
    if crop is None:
        return None
    
    crop_def = CROPS.get(crop["crop_type"])
    if crop_def is None:
        return None
    
    stage = crop["stage"]
    sprites = crop_def["sprites"]
    
    if stage >= len(sprites):
        stage = len(sprites) - 1
    
    return sprites[stage]


def tick_crop_growth(game_tick: int) -> None:
    """Update all crops' growth timers and advance stages.
    
    Call this every game tick from main loop.
    """
    from jobs import add_job, Job
    
    mature_crops = []
    
    for pos, crop in _ACTIVE_CROPS.items():
        crop_def = CROPS.get(crop["crop_type"])
        if crop_def is None:
            continue
        
        # Check if already at max stage
        if crop["stage"] >= crop_def["growth_stages"] - 1:
            # Crop is mature - check if harvest job exists
            if not crop.get("harvest_job_created", False):
                mature_crops.append(pos)
            continue
        
        # Increment growth timer
        crop["growth_timer"] += 1
        
        # Check if ready to advance stage
        if crop["growth_timer"] >= crop_def["ticks_per_stage"]:
            crop["stage"] += 1
            crop["growth_timer"] = 0
            
            stage_name = ["seedling", "growing", "mature"][min(crop["stage"], 2)]
            print(f"[Crops] {crop['crop_type']} at {pos} advanced to {stage_name} (stage {crop['stage']})")
            
            # Mark tile dirty for renderer update
            x, y, z = pos
            from grid_arcade import mark_tile_dirty_global
            mark_tile_dirty_global(x, y, z)
            
            # Check if now mature
            if crop["stage"] >= crop_def["growth_stages"] - 1:
                mature_crops.append(pos)
    
    # Create harvest jobs for newly mature crops
    for pos in mature_crops:
        crop = _ACTIVE_CROPS[pos]
        if not crop.get("harvest_job_created", False):
            x, y, z = pos
            from jobs import add_job
            add_job("harvest_crop", x, y, required=60, category="farming", z=z, pressure=5)
            crop["harvest_job_created"] = True
            print(f"[Crops] Created harvest job for {crop['crop_type']} at ({x}, {y}, {z})")


def harvest_crop(x: int, y: int, z: int) -> Optional[Tuple[str, int, str]]:
    """Harvest a mature crop and return (item_id, quantity, crop_type).
    
    Returns None if no crop or crop not mature.
    """
    crop = _ACTIVE_CROPS.get((x, y, z))
    if crop is None:
        return None
    
    crop_def = CROPS.get(crop["crop_type"])
    if crop_def is None:
        return None
    
    if crop["stage"] < crop_def["growth_stages"] - 1:
        return None  # Not mature yet
    
    harvest_item = crop_def["harvest_item"]
    harvest_yield = crop_def.get("harvest_yield", 1)
    crop_type = crop["crop_type"]  # Get crop type for metadata
    
    # Remove crop
    remove_crop(x, y, z)
    
    return (harvest_item, harvest_yield, crop_type)


def get_all_crops() -> Dict[Tuple[int, int, int], dict]:
    """Get all active crops for iteration."""
    return _ACTIVE_CROPS.copy()


def get_crop_count() -> int:
    """Get total number of active crops."""
    return len(_ACTIVE_CROPS)


# =============================================================================
# SAVE/LOAD
# =============================================================================

def get_save_state() -> dict:
    """Get crop system state for saving."""
    crops_data = {}
    for coord, crop in _ACTIVE_CROPS.items():
        key = f"{coord[0]},{coord[1]},{coord[2]}"
        crops_data[key] = {
            "crop_type": crop["crop_type"],
            "stage": crop["stage"],
            "growth_timer": crop["growth_timer"],
            "planted_tick": crop.get("planted_tick", 0),
            "harvest_job_created": crop.get("harvest_job_created", False),
        }
    
    return {"crops": crops_data}


def load_save_state(state: dict) -> None:
    """Restore crop system state from save."""
    global _ACTIVE_CROPS
    
    _ACTIVE_CROPS.clear()
    
    for key, crop_data in state.get("crops", {}).items():
        parts = key.split(",")
        coord = (int(parts[0]), int(parts[1]), int(parts[2]))
        _ACTIVE_CROPS[coord] = {
            "crop_type": crop_data["crop_type"],
            "stage": crop_data["stage"],
            "growth_timer": crop_data["growth_timer"],
            "planted_tick": crop_data.get("planted_tick", 0),
            "harvest_job_created": crop_data.get("harvest_job_created", False),
        }
