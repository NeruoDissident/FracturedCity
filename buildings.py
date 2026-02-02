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

# Debug mode - free building without material requirements
FREE_BUILD_MODE = False

def toggle_free_build_mode() -> bool:
    """Toggle free build mode. Returns new state."""
    global FREE_BUILD_MODE
    FREE_BUILD_MODE = not FREE_BUILD_MODE
    return FREE_BUILD_MODE

# Building type definitions
# Each type specifies: name, materials needed, work to construct, drag constraints
#
# === CRAFTING SYSTEM TYPES ===
# Type 1: STATIC RECIPES (most workstations)
#   - Recipes defined in "recipes" list with explicit inputs/outputs
#   - "input": {} = fungible resources (wood, metal, power, raw_food)
#   - "input_items": {} = items with metadata (corpse, meat, components)
#   - "output": {} = resource outputs (power, cooked_meal)
#   - "output_item": str = single item output (work_gloves, hard_hat)
#   - Execution: colonist.py::_crafting_work_at_bench() lines 4016-4075
#
# Type 2: DYNAMIC RECIPES (bio_matter_salvage_station)
#   - Recipe has empty "output": {} (dynamic generation)
#   - Actual outputs determined by input metadata (corpse species)
#   - Species data in animals.py::AnimalSpecies (meat_yield, materials)
#   - Execution: colonist.py::_crafting_work_at_bench() lines 4080-4130
#   - Metadata preserved: source_species, harvested_by
#
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
    "bar_door": {
        "name": "Bar Door",
        "tile_type": "bar_door",
        "materials": {"scrap": 2, "wood": 1},
        "construction_work": 70,
        "walkable": True,  # Swinging saloon-style door
    },
    "floor": {
        "name": "Floor",
        "tile_type": "floor",
        "materials": {"wood": 1},
        "construction_work": 40,
        "walkable": True,
    },
    "stage": {
        "name": "Stage",
        "tile_type": "stage",
        "materials": {"wood": 2, "scrap": 1},
        "construction_work": 50,
        "walkable": True,  # Walkable but needs stairs to access
    },
    "stage_stairs": {
        "name": "Stage Stairs",
        "tile_type": "stage_stairs",
        "materials": {"wood": 1, "scrap": 1},
        "construction_work": 30,
        "walkable": True,  # Stairs allow access to stage
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
    "scrap_bar_counter": {
        "name": "Scrap Bar Counter",
        "tile_type": "scrap_bar_counter",
        "materials": {"scrap": 2, "wood": 1},
        "construction_work": 60,
        "walkable": False,  # Counter blocks movement like a wall
    },
    "gutter_still": {
        "name": "Gutter Still",
        "tile_type": "gutter_still",
        "materials": {"scrap": 3, "metal": 2},
        "construction_work": 100,
        "walkable": False,
        "workstation": True,  # Bartender crafts drinks here
        "multi_recipe": True,
        "size": (3, 3),  # 3x3 tiles (width, height)
        "recipes": [
            {"id": "brew_swill", "name": "Brew Swill", "input": {"raw_food": 2, "scrap": 1}, "output_item": "swill", "work_time": 120},
            {"id": "distill_guttershine", "name": "Distill Guttershine", "input": {"raw_food": 3, "scrap": 2}, "output_item": "guttershine", "work_time": 180},
        ],
    },
    "spark_bench": {
        "name": "Spark Bench",
        "tile_type": "spark_bench",
        "materials": {"metal": 3, "mineral": 2, "scrap": 2},
        "construction_work": 120,
        "walkable": False,
        "workstation": True,
        "multi_recipe": True,
        "recipes": [
            {"id": "craft_wire", "name": "Salvage Wire", "input": {"scrap": 1}, "output_item": "wire", "work_time": 40},
            {"id": "craft_resistor", "name": "Craft Resistor", "input": {"scrap": 1, "mineral": 1}, "output_item": "resistor", "work_time": 50},
            {"id": "craft_capacitor", "name": "Craft Capacitor", "input": {"scrap": 1, "metal": 1}, "output_item": "capacitor", "work_time": 50},
            {"id": "craft_chip", "name": "Craft Circuit Chip", "input": {"metal": 2, "mineral": 1, "wire": 2}, "output_item": "chip", "work_time": 90},
            {"id": "craft_led", "name": "Craft LED", "input": {"mineral": 1, "wire": 1}, "output_item": "led", "work_time": 45},
        ],
    },
    "tinker_station": {
        "name": "Tinker Station",
        "tile_type": "tinker_station",
        "materials": {"wood": 3, "metal": 2, "scrap": 2},
        "construction_work": 100,
        "walkable": False,
        "workstation": True,
        "multi_recipe": True,
        "recipes": [
            {"id": "craft_scrap_guitar", "name": "Scrap Guitar", "input": {"wood": 2, "metal": 1, "wire": 2}, "output_item": "scrap_guitar", "work_time": 100},
            {"id": "craft_drum_kit", "name": "Drum Kit", "input": {"scrap": 3, "wood": 2}, "output_item": "drum_kit", "work_time": 90},
            {"id": "craft_synth", "name": "Synth Keyboard", "input": {"chip": 2, "wire": 3, "scrap": 2}, "output_item": "synth", "work_time": 120},
            {"id": "craft_harmonica", "name": "Harmonica", "input": {"metal": 1, "scrap": 1}, "output_item": "harmonica", "work_time": 50},
            {"id": "craft_amp", "name": "Amplifier", "input": {"chip": 1, "wire": 2, "metal": 2}, "output_item": "amp", "work_time": 80},
            {"id": "craft_vending_machine", "name": "Vending Machine", "input": {"metal": 3, "chip": 2, "led": 1}, "output_item": "vending_machine", "work_time": 150},
        ],
    },
    "salvagers_bench": {
        "name": "Salvager's Bench",
        "tile_type": "salvagers_bench",
        "materials": {"wood": 3, "scrap": 2},
        "construction_work": 100,
        "walkable": False,  # Workstation blocks movement
        "workstation": True,  # This is a workstation
        "multi_recipe": True,  # Supports multiple recipes
        "recipes": [
            {"id": "scrap_to_metal", "name": "Refine Metal", "input": {"scrap": 2}, "output": {"metal": 1}, "work_time": 60},
            {"id": "metal_components", "name": "Metal Components", "input": {"metal": 1}, "output": {"scrap": 3}, "work_time": 50},
        ],
    },
    "generator": {
        "name": "Generator",
        "tile_type": "generator",
        "materials": {"wood": 2, "metal": 2},
        "construction_work": 120,
        "walkable": False,  # Workstation blocks movement
        "workstation": True,  # This is a workstation
        "multi_recipe": True,  # Supports multiple recipes
        "size": (2, 2),  # 2x2 tiles (width, height)
        "recipes": [
            {"id": "power_from_wood", "name": "Burn Wood for Power", "input": {"wood": 3}, "output": {"power": 1}, "work_time": 80},
            {"id": "power_from_scrap", "name": "Burn Scrap for Power", "input": {"scrap": 4}, "output": {"power": 1}, "work_time": 90},
        ],
    },
    "stove": {
        "name": "Stove",
        "tile_type": "stove",
        "materials": {"metal": 2, "mineral": 1},
        "construction_work": 100,
        "walkable": False,  # Workstation blocks movement
        "workstation": True,  # This is a workstation
        "multi_recipe": True,  # Supports multiple recipes
        "size": (2, 1),  # 2x1 tiles (width, height) - horizontal
        "recipes": [
            # TYPE 1 RECIPE: Resource-based (raw_food is fungible resource)
            {"id": "simple_meal", "name": "Simple Meal", "input": {"raw_food": 2, "power": 1}, "output": {"cooked_meal": 1}, "work_time": 40},
            
            # TYPE 1 RECIPES: Item-based with tag matching (@ prefix = any item with that tag)
            # @meat matches: scrap_meat, poultry_meat, high_quality_meat, etc.
            # @vegetable matches: tomato, carrot, potato, etc.
            # Note: Metadata is currently NOT propagated to cooked_meal (future feature)
            {"id": "grilled_scraps", "name": "Grilled Scraps", "input_items": {"@meat": 1}, "input": {"power": 1}, "output": {"cooked_meal": 1}, "work_time": 50},
            {"id": "meat_stew", "name": "Meat Stew", "input_items": {"@meat": 2}, "input": {"power": 1}, "output": {"cooked_meal": 1}, "work_time": 80},
            {"id": "hearty_roast", "name": "Hearty Roast", "input_items": {"@meat": 2, "@vegetable": 1}, "input": {"power": 2}, "output": {"cooked_meal": 1}, "work_time": 100},
            {"id": "poultry_roast", "name": "Poultry Roast", "input_items": {"@meat": 2}, "input": {"power": 1}, "output": {"cooked_meal": 1}, "work_time": 70},
            {"id": "vegetable_stew", "name": "Vegetable Stew", "input_items": {"@vegetable": 2}, "input": {"power": 1}, "output": {"cooked_meal": 1}, "work_time": 60},
        ],
    },
    # === Item Crafting Stations ===
    "gutter_forge": {
        "name": "Gutter Forge",
        "tile_type": "gutter_forge",
        "materials": {"metal": 3, "scrap": 2},
        "construction_work": 120,
        "walkable": False,
        "workstation": True,
        "multi_recipe": True,  # Supports multiple recipes
        "size": (3, 3),  # 3x3 tiles (width, height)
        "recipes": [
            # Tools & Gloves
            {"id": "salvage_tool", "name": "Salvage Tool", "input": {"metal": 2, "scrap": 1}, "output_item": "salvage_tool", "work_time": 80},
            {"id": "work_gloves", "name": "Work Gloves", "input": {"scrap": 2}, "output_item": "work_gloves", "work_time": 60},
            {"id": "signal_gauntlet", "name": "Signal Gauntlet", "input": {"metal": 2, "power": 1}, "output_item": "signal_gauntlet", "work_time": 100},
            # Wearable Armor & Clothing
            {"id": "hard_hat", "name": "Hard Hat", "input": {"scrap": 2}, "output_item": "hard_hat", "work_time": 60},
            {"id": "work_vest", "name": "Work Vest", "input": {"scrap": 2, "wood": 1}, "output_item": "work_vest", "work_time": 70},
            {"id": "padded_jacket", "name": "Padded Jacket", "input": {"scrap": 3}, "output_item": "padded_jacket", "work_time": 90},
            {"id": "work_boots", "name": "Work Boots", "input": {"scrap": 2}, "output_item": "work_boots", "work_time": 60},
            {"id": "scrap_armor", "name": "Scrap Armor", "input": {"metal": 3, "scrap": 2}, "output_item": "scrap_armor", "work_time": 120},
            {"id": "armor_plate", "name": "Armor Plate", "input": {"metal": 3}, "output_item": "armor_plate", "work_time": 70},
            # Weapons
            {"id": "pipe_weapon", "name": "Pipe Weapon", "input": {"metal": 3, "scrap": 1}, "output_item": "pipe_weapon", "work_time": 100},
            {"id": "scrap_blade", "name": "Scrap Blade", "input": {"metal": 2, "scrap": 2}, "output_item": "scrap_blade", "work_time": 90},
        ],
    },
    "skinshop_loom": {
        "name": "Skinshop Loom",
        "tile_type": "skinshop_loom",
        "materials": {"wood": 3, "scrap": 2},
        "construction_work": 100,
        "walkable": False,
        "workstation": True,
        "multi_recipe": True,
        "recipes": [
            # Furniture Only
            {"id": "crash_bed", "name": "Crash Bed", "input": {"scrap": 2, "wood": 2}, "output_item": "crash_bed", "work_time": 90},
            {"id": "comfort_chair", "name": "Comfort Chair", "input": {"wood": 2, "scrap": 1}, "output_item": "comfort_chair", "work_time": 80},
            {"id": "bar_stool", "name": "Bar Stool", "input": {"scrap": 1, "wood": 1}, "output_item": "bar_stool", "work_time": 60},
            {"id": "storage_locker", "name": "Storage Locker", "input": {"wood": 3, "metal": 1}, "output_item": "storage_locker", "work_time": 90},
            {"id": "dining_table", "name": "Dining Table", "input": {"wood": 4}, "output_item": "dining_table", "work_time": 100},
            {"id": "wall_lamp", "name": "Wall Lamp", "input": {"metal": 1, "power": 1}, "output_item": "wall_lamp", "work_time": 50},
        ],
    },
    "bio_matter_salvage_station": {
        "name": "Bio-Matter Salvage Station",
        "tile_type": "bio_matter_salvage_station",
        "materials": {"metal": 3, "scrap": 2},
        "construction_work": 100,
        "walkable": False,
        "placement_rule": "floor_only",
        "workstation": True,
        "multi_recipe": False,
        "size": (2, 1),  # 2x1 horizontal like stove
        # TYPE 2 RECIPE: Dynamic butchering (empty output = dynamic generation)
        # Actual outputs determined by corpse metadata (source_species)
        # See: animals.py::AnimalSpecies for meat_yield and materials
        # Execution: colonist.py::_crafting_work_at_bench() lines 4080-4130
        # Example outputs:
        #   Rat corpse → 1-2 scrap_meat, 1 rat_pelt
        #   Bird corpse → 2-3 poultry_meat, 1-2 feathers
        #   Cat corpse → 2-3 scrap_meat, 1 cat_pelt
        "recipe": {"id": "butcher", "name": "Butcher Corpse", "input_items": {"corpse": 1}, "output": {}, "work_time": 60},
        "description": "Cuts up rats and pigeons and shit.",
    },
    "cortex_spindle": {
        "name": "Cortex Spindle",
        "tile_type": "cortex_spindle",
        "materials": {"metal": 2, "mineral": 2, "power": 1},
        "construction_work": 120,
        "walkable": False,
        "placement_rule": "floor_only",
        "workstation": True,
        "multi_recipe": True,
        "recipes": [
            {"id": "focus_chip", "name": "Focus Chip", "input": {"metal": 2, "mineral": 1}, "output_item": "focus_chip", "work_time": 100},
            {"id": "echo_dampener", "name": "Echo Dampener", "input": {"metal": 1, "mineral": 2}, "output_item": "echo_dampener", "work_time": 100},
            {"id": "lucky_coin", "name": "Lucky Coin", "input": {"metal": 1}, "output_item": "lucky_coin", "work_time": 40},
            {"id": "memory_locket", "name": "Memory Locket", "input": {"metal": 1, "mineral": 1}, "output_item": "memory_locket", "work_time": 60},
            {"id": "signal_stone", "name": "Signal Stone", "input": {"mineral": 2, "power": 1}, "output_item": "signal_stone", "work_time": 80},
            {"id": "medical_scanner", "name": "Medical Scanner", "input": {"metal": 2, "mineral": 2, "power": 1}, "output_item": "medical_scanner", "work_time": 120},
            {"id": "stim_injector", "name": "Stim Injector", "input": {"metal": 1, "mineral": 2}, "output_item": "stim_injector", "work_time": 90},
            {"id": "neural_interface", "name": "Neural Interface", "input": {"metal": 3, "mineral": 3, "power": 2}, "output_item": "neural_interface", "work_time": 150},
            {"id": "data_slate", "name": "Data Slate", "input": {"metal": 1, "mineral": 1}, "output_item": "data_slate", "work_time": 60},
        ],
    },
    # === Military/Training ===
    "barracks": {
        "name": "Barracks",
        "tile_type": "barracks",
        "materials": {"wood": 4, "metal": 2},
        "construction_work": 120,
        "walkable": False,
        "workstation": True,  # Acts like a workstation for training job spawning
        "training_station": True,  # Special flag for training
    },
    # === Hunting & Animal Processing ===
    "butcher_shop": {
        "name": "Butcher Shop",
        "tile_type": "butcher_shop",
        "materials": {"wood": 3, "metal": 2},
        "construction_work": 100,
        "walkable": False,
        "workstation": True,
        "multi_recipe": True,
        "size": (2, 1),  # 2x1 horizontal
        "recipes": [
            {"id": "butcher_rat", "name": "Butcher Rat", "input": {"rat_corpse": 1}, "output": {"scrap_meat": 2, "rough_hide": 1}, "work_time": 60},
            {"id": "butcher_bird", "name": "Butcher Bird", "input": {"bird_corpse": 1}, "output": {"poultry_meat": 3, "feathers": 2}, "work_time": 70},
        ],
    },
    # === Farming ===
    "plant_bed": {
        "name": "Plant Bed",
        "tile_type": "plant_bed",
        "materials": {"wood": 2, "scrap": 1},
        "construction_work": 60,
        "walkable": False,
        "workstation": True,
        "multi_recipe": True,
        "size": (2, 1),  # 2x1 horizontal
        "placement_rule": "rooftop_only",
        "recipes": [
            {"id": "grow_tomato", "name": "Plant Tomato", "input_items": {"tomato_seed": 1}, "work_time": 1},
        ],
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
    
    # Get the current recipe (handles both single and multi-recipe stations)
    recipe = get_workstation_recipe(x, y, z)
    if recipe is None:
        return False
    
    # Check resource inputs (power, wood, etc.)
    resource_inputs_needed = recipe.get("input", {})
    inputs_have = ws.get("input_items", {})
    
    for res_type, amount in resource_inputs_needed.items():
        if inputs_have.get(res_type, 0) < amount:
            return False
    
    # Check item inputs (meat, corpses, etc.) - stored in equipment_items
    item_inputs_needed = recipe.get("input_items", {})
    equipment_have = ws.get("equipment_items", {})
    
    for item_requirement, amount_needed in item_inputs_needed.items():
        # Check if this is a tag-based requirement (e.g., @vegetable)
        if item_requirement.startswith("@"):
            # Tag-based matching - sum up all items with this tag
            tag_to_find = item_requirement[1:]
            total_with_tag = 0
            
            from items import get_item_def
            for item_id, item_count in equipment_have.items():
                item_def = get_item_def(item_id)
                if item_def and tag_to_find in item_def.tags:
                    total_with_tag += item_count
            
            if total_with_tag < amount_needed:
                return False
        else:
            # Exact ID matching
            if equipment_have.get(item_requirement, 0) < amount_needed:
                return False
    
    return True


def consume_workstation_inputs(x: int, y: int, z: int = 0) -> bool:
    """Consume inputs and produce outputs. Returns True if successful."""
    ws = _WORKSTATIONS.get((x, y, z))
    if ws is None:
        return False
    
    # Get the current recipe (handles both single and multi-recipe stations)
    recipe = get_workstation_recipe(x, y, z)
    if recipe is None:
        return False
    
    # Consume resource inputs (power, wood, etc.)
    resource_inputs_needed = recipe.get("input", {})
    for res_type, amount in resource_inputs_needed.items():
        ws["input_items"][res_type] = ws["input_items"].get(res_type, 0) - amount
    
    # Clear empty resource entries
    ws["input_items"] = {k: v for k, v in ws["input_items"].items() if v > 0}
    
    # Consume item inputs (meat, corpses, etc.)
    item_inputs_needed = recipe.get("input_items", {})
    if "equipment_items" not in ws:
        ws["equipment_items"] = {}
    
    for item_requirement, amount_needed in item_inputs_needed.items():
        # Check if this is a tag-based requirement (e.g., @vegetable)
        if item_requirement.startswith("@"):
            # Tag-based consumption - consume items that have this tag
            tag_to_find = item_requirement[1:]
            remaining_to_consume = amount_needed
            
            from items import get_item_def
            # Consume items with this tag until we've consumed enough
            for item_id in list(ws["equipment_items"].keys()):
                if remaining_to_consume <= 0:
                    break
                
                item_def = get_item_def(item_id)
                if item_def and tag_to_find in item_def.tags:
                    available = ws["equipment_items"][item_id]
                    to_consume = min(available, remaining_to_consume)
                    ws["equipment_items"][item_id] -= to_consume
                    remaining_to_consume -= to_consume
        else:
            # Exact ID consumption
            ws["equipment_items"][item_requirement] = ws["equipment_items"].get(item_requirement, 0) - amount_needed
    
    # Clear empty equipment entries
    ws["equipment_items"] = {k: v for k, v in ws["equipment_items"].items() if v > 0}
    
    # Clear corpse metadata after consumption
    if "corpse_metadata" in ws and ws["corpse_metadata"]:
        ws["corpse_metadata"].pop(0)
    
    return True


def get_workstation_recipe(x: int, y: int, z: int = 0) -> Optional[dict]:
    """Get the current recipe for a workstation.
    
    For single-recipe stations, returns the 'recipe' field.
    For multi-recipe stations, returns the selected recipe from 'recipes' list.
    """
    ws = _WORKSTATIONS.get((x, y, z))
    if ws is None:
        return None
    
    building_def = BUILDING_TYPES.get(ws.get("type", ""))
    if building_def is None:
        return None
    
    # Check for multi-recipe station
    if building_def.get("multi_recipe", False):
        selected_id = ws.get("selected_recipe")
        recipes = building_def.get("recipes", [])
        for recipe in recipes:
            if recipe["id"] == selected_id:
                return recipe
        # Fallback to first recipe
        return recipes[0] if recipes else None
    
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
    
    # Tiles that can NEVER be built on (existing structures)
    blocked_tiles = {
        "wall", "finished_wall", "wall_advanced", "finished_wall_advanced",
        "door", "window", "finished_window", "window_tile",
        "salvagers_bench", "finished_salvagers_bench",
        "generator", "finished_generator",
        "stove", "finished_stove",
        "gutter_forge", "finished_gutter_forge",
        "skinshop_loom", "finished_skinshop_loom",
        "cortex_spindle", "finished_cortex_spindle",
        "barracks", "finished_barracks",
        "bridge", "finished_bridge",
        "fire_escape", "fire_escape_platform",
    }
    
    if current_tile in blocked_tiles:
        return False
    
    # Handle resource nodes - clear them for construction
    if current_tile == "resource_node":
        # Clear the resource node - drops items and prevents respawn
        resources.clear_node_for_construction(x, y)
        # Cancel any gathering job on this tile
        remove_job_at(x, y)
    elif current_tile in ("roof", "roof_floor", "roof_access"):
        # Allow building on walkable rooftop surfaces (z>0)
        pass
    elif z == 0:
        # Z0: Allow building on any walkable ground tile (weeds, debris, scorched, streets, etc.)
        if not grid.is_walkable(x, y, z):
            return False
    elif current_tile not in ("empty", None, "finished_floor"):
        # Z>0: Stricter - only empty/floor tiles
        return False
    
    building_def = BUILDING_TYPES.get(building_type)
    if building_def is None:
        return False
    
    # Mark stockpile zone for removal (walls/doors can't have zones)
    if building_type in ("wall", "wall_advanced", "door", "window"):
        zones.mark_tile_for_removal(x, y, z)
    
    # Create construction site - materials will be delivered by supply jobs
    # In FREE_BUILD_MODE, skip material requirements
    if FREE_BUILD_MODE:
        materials_needed = {}
        materials_delivered = {}
    else:
        materials_needed = building_def["materials"].copy()
        materials_delivered = {k: 0 for k in building_def["materials"]}
    
    site = {
        "type": building_type,
        "materials_needed": materials_needed,
        "materials_delivered": materials_delivered,
        "awaiting_stockpile_clear": zones.is_pending_removal(x, y, z),
        "z": z,
    }
    _CONSTRUCTION_SITES[(x, y, z)] = site
    
    # Get size for multi-tile structures
    width, height = building_def.get("size", (1, 1))
    tile_type = building_def.get("tile_type", building_type)
    
    # For multi-tile structures, only set origin tile
    # For workstations, preserve the floor layer
    is_workstation = building_def.get("workstation", False)
    
    # Store original floor tile for workstations (so they render on top)
    if is_workstation:
        original_tile = grid.get_tile(x, y, z)
        if original_tile and original_tile in ("finished_floor", "floor", "roof_floor", "roof_access"):
            if not hasattr(grid, 'base_tiles'):
                grid.base_tiles = {}
            grid.base_tiles[(x, y, z)] = original_tile
    
    # Set tile_type ONLY on origin tile
    grid.set_tile(x, y, tile_type, z=z)
    
    # Keep multi-tile construction sites WALKABLE during construction
    # Colonists need to access the site to deliver materials and build
            # Will be marked unwalkable when construction completes
    
    # Determine subtype for job priority
    # Priority order: workstation > door > wall > floor
    if building_def.get("workstation", False):
        subtype = "workstation"
    elif building_type == "door":
        subtype = "door"
    elif building_type in ("wall", "wall_advanced"):
        subtype = "wall"
    elif building_type == "floor":
        subtype = "floor"
    else:
        subtype = None
    
    # Create construction job with z-level and subtype for priority
    add_job("construction", x, y, required=building_def["construction_work"], category="construction", subtype=subtype, z=z)
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


def place_bar_door(grid: Grid, x: int, y: int, z: int = 0) -> bool:
    """Place a bar door construction site at (x, y, z)."""
    if place_building(grid, x, y, "bar_door", z):
        # Initialize door state as closed
        _DOOR_STATES[(x, y, z)] = {"open": False, "close_timer": 0}
        return True
    return False


def place_floor(grid: Grid, x: int, y: int, z: int = 0) -> bool:
    """Place a floor construction site at (x, y, z)."""
    return place_building(grid, x, y, "floor", z)


def place_stage(grid: Grid, x: int, y: int, z: int = 0) -> bool:
    """Place a stage construction site at (x, y, z)."""
    return place_building(grid, x, y, "stage", z)


def place_stage_stairs(grid: Grid, x: int, y: int, z: int = 0) -> bool:
    """Place stage stairs construction site at (x, y, z)."""
    return place_building(grid, x, y, "stage_stairs", z)


def place_window(grid: Grid, x: int, y: int, z: int = 0) -> bool:
    """Place a window construction site at (x, y, z)."""
    return place_building(grid, x, y, "window", z)


def place_scrap_bar_counter(grid: Grid, x: int, y: int, z: int = 0) -> bool:
    """Place a scrap bar counter construction site at (x, y, z)."""
    return place_building(grid, x, y, "scrap_bar_counter", z)


def place_bar_stool(grid: Grid, x: int, y: int, z: int = 0) -> bool:
    """Place a bar stool construction site at (x, y, z)."""
    return place_building(grid, x, y, "bar_stool", z)


def place_gutter_still(grid: Grid, x: int, y: int, z: int = 0) -> bool:
    """Place a gutter still construction site at (x, y, z)."""
    return place_building(grid, x, y, "gutter_still", z)


def can_place_salvagers_bench(grid: Grid, x: int, y: int, z: int = 0) -> bool:
    """Check if a Salvager's Bench can be placed at (x, y, z)."""
    tile = grid.get_tile(x, y, z)
    if tile not in ("finished_floor", "roof_floor", "roof_access"):
        print(f"[Build Debug] Tile at ({x},{y}) is '{tile}', need floor")
        return False
    return True


def place_salvagers_bench(grid: Grid, x: int, y: int, z: int = 0) -> bool:
    """Place a Salvager's Bench construction site at (x, y, z)."""
    if not can_place_salvagers_bench(grid, x, y, z):
        return False
    return place_building(grid, x, y, "salvagers_bench", z)


def can_place_generator(grid: Grid, x: int, y: int, z: int = 0) -> bool:
    """Check if a Generator can be placed at (x, y, z)."""
    tile = grid.get_tile(x, y, z)
    if tile not in ("finished_floor", "roof_floor", "roof_access"):
        print(f"[Build Debug] Tile at ({x},{y}) is '{tile}', need floor")
        return False
    return True


def place_generator(grid: Grid, x: int, y: int, z: int = 0) -> bool:
    """Place a Generator construction site at (x, y, z)."""
    if not can_place_generator(grid, x, y, z):
        return False
    return place_building(grid, x, y, "generator", z)


def can_place_stove(grid: Grid, x: int, y: int, z: int = 0) -> bool:
    """Check if a Stove can be placed at (x, y, z)."""
    tile = grid.get_tile(x, y, z)
    if tile not in ("finished_floor", "roof_floor", "roof_access"):
        print(f"[Build Debug] Tile at ({x},{y}) is '{tile}', need floor")
        return False
    return True


def place_stove(grid: Grid, x: int, y: int, z: int = 0) -> bool:
    """Place a Stove construction site at (x, y, z)."""
    if not can_place_stove(grid, x, y, z):
        return False
    return place_building(grid, x, y, "stove", z)


# === Item Crafting Stations ===

def can_place_gutter_forge(grid: Grid, x: int, y: int, z: int = 0) -> bool:
    """Check if a Gutter Forge can be placed at (x, y, z)."""
    tile = grid.get_tile(x, y, z)
    if tile not in ("finished_floor", "roof_floor", "roof_access"):
        print(f"[Build Debug] Tile at ({x},{y}) is '{tile}', need floor")
        return False
    return True


def place_gutter_forge(grid: Grid, x: int, y: int, z: int = 0) -> bool:
    """Place a Gutter Forge construction site at (x, y, z)."""
    if not can_place_gutter_forge(grid, x, y, z):
        return False
    return place_building(grid, x, y, "gutter_forge", z)


def can_place_skinshop_loom(grid: Grid, x: int, y: int, z: int = 0) -> bool:
    """Check if a Skinshop Loom can be placed at (x, y, z)."""
    tile = grid.get_tile(x, y, z)
    if tile not in ("finished_floor", "roof_floor", "roof_access"):
        print(f"[Build Debug] Tile at ({x},{y}) is '{tile}', need floor")
        return False
    return True


def place_skinshop_loom(grid: Grid, x: int, y: int, z: int = 0) -> bool:
    """Place a Skinshop Loom construction site at (x, y, z)."""
    if not can_place_skinshop_loom(grid, x, y, z):
        return False
    return place_building(grid, x, y, "skinshop_loom", z)


def can_place_cortex_spindle(grid: Grid, x: int, y: int, z: int = 0) -> bool:
    """Check if a Cortex Spindle can be placed at (x, y, z)."""
    tile = grid.get_tile(x, y, z)
    if tile not in ("finished_floor", "roof_floor", "roof_access"):
        print(f"[Build Debug] Tile at ({x},{y}) is '{tile}', need floor")
        return False
    return True


def place_cortex_spindle(grid: Grid, x: int, y: int, z: int = 0) -> bool:
    """Place a Cortex Spindle construction site at (x, y, z)."""
    if not can_place_cortex_spindle(grid, x, y, z):
        return False
    return place_building(grid, x, y, "cortex_spindle", z)


def can_place_barracks(grid: Grid, x: int, y: int, z: int = 0) -> bool:
    """Check if a Barracks can be placed at (x, y, z).
    
    Requirements:
    - Must be on a floor tile only (anarchist mode - place anywhere)
    """
    tile = grid.get_tile(x, y, z)
    if tile not in ("finished_floor", "roof_floor", "roof_access"):
        print(f"[Build Debug] Barracks: Tile at ({x},{y}) is '{tile}', need floor")
        return False
    
    return True


def place_barracks(grid: Grid, x: int, y: int, z: int = 0) -> bool:
    """Place a Barracks construction site at (x, y, z)."""
    if not can_place_barracks(grid, x, y, z):
        return False
    return place_building(grid, x, y, "barracks", z)


def get_building_size(building_type: str) -> tuple:
    """Get the size (width, height) of a building/workstation/furniture.
    
    Returns:
        (width, height) tuple in tiles. Defaults to (1, 1) if not specified.
    """
    # Strip 'finished_' prefix if present (renderer passes finished tile types)
    lookup_type = building_type.replace("finished_", "")
    building_def = BUILDING_TYPES.get(lookup_type)
    if building_def is None:
        return (1, 1)
    return building_def.get("size", (1, 1))


def place_workstation_generic(grid: Grid, x: int, y: int, building_type: str, z: int = 0) -> bool:
    """Generic placement helper for workstations (supports multi-tile).
    
    For multi-tile structures, (x, y) is the bottom-left origin tile.
    All tiles in the footprint must be valid floor tiles.
    """
    building_def = BUILDING_TYPES.get(building_type)
    if building_def is None or not building_def.get("workstation", False):
        return False
    
    # Get size (defaults to 1x1 for backward compatibility)
    width, height = building_def.get("size", (1, 1))
    
    # Check all tiles in footprint
    for dy in range(height):
        for dx in range(width):
            check_x = x + dx
            check_y = y + dy
            
            if not grid.in_bounds(check_x, check_y, z):
                print(f"[Build Debug] {building_type}: tile ({check_x},{check_y}) out of bounds")
                return False
            
            tile = grid.get_tile(check_x, check_y, z)
            if tile not in ("finished_floor", "roof_floor", "roof_access"):
                print(f"[Build Debug] {building_type}: tile at ({check_x},{check_y}) is '{tile}', need floor")
                return False
    
    # Place at origin tile - multi-tile rendering will handle the rest
    return place_building(grid, x, y, building_type, z)


def request_furniture_install(grid: Grid, dest_x: int, dest_y: int, dest_z: int, item_id: str) -> bool:
    """Request installation of a furniture item at the given tile.
    
    Creates an install_furniture job that will fetch the item from
    equipment stockpiles and install it at the destination.
    """
    # Allow furniture on any walkable tile
    tile = grid.get_tile(dest_x, dest_y, dest_z)
    # Block placement on walls, doors, windows, and other non-walkable structures
    blocked_tiles = ("wall", "finished_wall", "wall_advanced", "finished_wall_advanced",
                     "door", "window", "finished_window", "window_tile")
    if tile in blocked_tiles:
        print(f"[Furniture] Cannot install {item_id} at ({dest_x},{dest_y},z={dest_z}) - blocked by {tile}")
        return False
    
    # Find stored equipment item matching this furniture ID
    all_equipment = zones.get_all_stored_equipment()
    best_source = None
    best_dist = None
    for (sx, sy, sz), items in all_equipment.items():
        for stored in items:
            if stored.get("id") == item_id:
                dist = abs(sx - dest_x) + abs(sy - dest_y)
                # Small penalty for different Z-level to prefer same level
                if sz != dest_z:
                    dist += 5
                if best_dist is None or dist < best_dist:
                    best_dist = dist
                    best_source = (sx, sy, sz)
                break
    
    if best_source is None:
        print(f"[Furniture] No {item_id} available in equipment stockpiles for install")
        return False
    
    src_x, src_y, src_z = best_source
    work_time = 30  # Time to prepare/pick up furniture
    add_job(
        "install_furniture",
        src_x,
        src_y,
        required=work_time,
        resource_type=item_id,
        dest_x=dest_x,
        dest_y=dest_y,
        dest_z=dest_z,
        z=src_z,
    )
    print(f"[Furniture] Install {item_id} from ({src_x},{src_y},z={src_z}) to ({dest_x},{dest_y},z={dest_z})")
    return True


def register_workstation(x: int, y: int, z: int, workstation_type: str) -> None:
    """Register a completed workstation."""
    building_def = BUILDING_TYPES.get(workstation_type, {})
    is_multi_recipe = building_def.get("multi_recipe", False)
    recipes = building_def.get("recipes", [])
    
    ws_data = {
        "type": workstation_type,
        "reserved": False,
        "working": False,
        "progress": 0,
        "input_items": {},
        "orders": [],  # New order system
    }
    
    # For multi-recipe stations, default to first recipe
    if is_multi_recipe and recipes:
        ws_data["selected_recipe"] = recipes[0]["id"]
    
    _WORKSTATIONS[(x, y, z)] = ws_data


def set_workstation_recipe(x: int, y: int, z: int, recipe_id: str) -> bool:
    """Set the selected recipe for a multi-recipe workstation."""
    ws = _WORKSTATIONS.get((x, y, z))
    if ws is None:
        return False
    
    building_def = BUILDING_TYPES.get(ws["type"], {})
    recipes = building_def.get("recipes", [])
    
    # Validate recipe exists
    for recipe in recipes:
        if recipe["id"] == recipe_id:
            ws["selected_recipe"] = recipe_id
            # Clear any in-progress work when changing recipe
            ws["input_items"] = {}
            ws["progress"] = 0
            ws["working"] = False
            return True
    
    return False


def get_workstation_recipes(x: int, y: int, z: int) -> list:
    """Get available recipes for a workstation."""
    ws = _WORKSTATIONS.get((x, y, z))
    if ws is None:
        return []
    
    building_def = BUILDING_TYPES.get(ws["type"], {})
    
    # For multi-recipe stations, return recipes list
    if building_def.get("multi_recipe", False):
        return building_def.get("recipes", [])
    
    # For single-recipe stations, return recipe as a list
    recipe = building_def.get("recipe")
    if recipe:
        return [recipe]
    
    return []


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
    from rooms import mark_tile_dirty
    
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
    
    # Mark tile dirty for room re-detection (batched at end of tick)
    mark_tile_dirty(x, y, z)
    
    print(f"[Demolish] Removed {tile} at ({x}, {y}, z={z})")
    return True


def can_place_fire_escape(grid: Grid, x: int, y: int, z: int = 0) -> Tuple[bool, Optional[Tuple[int, int]]]:
    """Check if a fire escape can be placed at (x, y, z).
    
    Simplified: Just needs to be on a wall with an adjacent empty/walkable tile.
    """
    # Must be a wall tile
    tile = grid.get_tile(x, y, z)
    if "wall" not in tile:
        print(f"[FireEscape] Cannot place - tile at ({x},{y},{z}) is '{tile}', need wall")
        return False, None
    
    # Find adjacent tiles for platform placement
    # Prefer EXTERIOR tiles (empty, roof, outdoor) over INTERIOR tiles (floors)
    exterior_candidates = []
    interior_candidates = []
    
    for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
        px, py = x + dx, y + dy
        if not grid.in_bounds(px, py, z):
            continue
        
        platform_tile = grid.get_tile(px, py, z)
        
        # Skip walls - platform can't go on walls
        if platform_tile and "wall" in platform_tile:
            continue
        
        # Categorize as exterior or interior
        # Exterior: empty, roof, outdoor tiles
        # Interior: floor tiles (inside building)
        if platform_tile in ("empty", "roof", "roof_access", "roof_floor", None):
            exterior_candidates.append((dx, dy))
        elif "floor" in platform_tile:
            interior_candidates.append((dx, dy))
        else:
            # Other tiles (streets, etc.) - treat as exterior
            exterior_candidates.append((dx, dy))
    
    # Prefer exterior placement (platform goes OUTSIDE building)
    if exterior_candidates:
        dx, dy = exterior_candidates[0]
        px, py = x + dx, y + dy
        print(f"[FireEscape] Can place at ({x},{y},{z}), platform will be at ({px},{py}) [EXTERIOR]")
        return True, (dx, dy)
    
    # Fallback to interior if no exterior available
    if interior_candidates:
        dx, dy = interior_candidates[0]
        px, py = x + dx, y + dy
        print(f"[FireEscape] Can place at ({x},{y},{z}), platform will be at ({px},{py}) [INTERIOR - fallback]")
        return True, (dx, dy)
    
    print(f"[FireEscape] Cannot place - no valid adjacent tile for platform")
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
    
    # Platform can go on any tile (we already validated in can_place_fire_escape)
    # This allows platforms on floors, roofs, empty tiles, etc.
    
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
    job = add_job("construction", x, y, required=building_def["construction_work"], category="construction", subtype="fire_escape", z=z)
    print(f"[FireEscape] Created construction job at ({x}, {y}, {z}) - Job ID in queue, work required: {building_def['construction_work']}")
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
    add_job("construction", x, y, required=building_def["construction_work"], category="construction", subtype="bridge", z=z)
    
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
    """Create batch supply jobs for construction sites that need materials.
    
    Called each tick from main loop.
    Batches multiple construction sites needing the same resource into one job.
    A colonist will pick up a stack and deliver to multiple sites in sequence.
    
    Returns number of jobs created.
    """
    # First, clean up stale pending flags for jobs that no longer exist
    _cleanup_stale_pending_jobs(jobs_module)
    
    jobs_created = 0
    
    # Group sites by resource type and Z-level for batching
    # Key: (resource_type, z_level), Value: list of (x, y, z, amount_needed)
    sites_by_resource: dict[tuple[str, int], list[tuple[int, int, int, int]]] = {}
    
    for (x, y, z), site in _CONSTRUCTION_SITES.items():
        missing = get_missing_materials(x, y, z)
        
        for resource_type, amount_needed in missing.items():
            # Skip if we already have a supply job pending for this site/resource
            if has_pending_supply_job(x, y, z, resource_type):
                continue
            
            key = (resource_type, z)
            if key not in sites_by_resource:
                sites_by_resource[key] = []
            sites_by_resource[key].append((x, y, z, amount_needed))
    
    # Create batch supply jobs for each resource type
    MAX_CARRY_AMOUNT = 20  # Max items a colonist can carry in one trip
    
    for (resource_type, z_level), sites in sites_by_resource.items():
        if not sites:
            continue
        
        # Find stockpile with this resource (prefer same Z-level)
        source = zones_module.find_stockpile_with_resource(resource_type, z=z_level)
        if source is None:
            continue
        
        source_x, source_y, source_z = source
        
        # Calculate total needed and build delivery queue
        # Sort sites by distance from source for efficient delivery route
        sites_sorted = sorted(sites, key=lambda s: abs(s[0] - source_x) + abs(s[1] - source_y))
        
        # Build batches that fit within carry limit
        current_batch = []
        current_total = 0
        
        for site_x, site_y, site_z, amount in sites_sorted:
            if current_total + amount > MAX_CARRY_AMOUNT and current_batch:
                # Create job for current batch
                _create_batch_supply_job(
                    jobs_module, source_x, source_y, source_z,
                    resource_type, current_batch, current_total
                )
                jobs_created += 1
                current_batch = []
                current_total = 0
            
            current_batch.append((site_x, site_y, site_z, amount))
            current_total += amount
        
        # Create job for remaining batch
        if current_batch:
            _create_batch_supply_job(
                jobs_module, source_x, source_y, source_z,
                resource_type, current_batch, current_total
            )
            jobs_created += 1
    
    return jobs_created


def _create_batch_supply_job(
    jobs_module, 
    source_x: int, source_y: int, source_z: int,
    resource_type: str,
    delivery_sites: list[tuple[int, int, int, int]],
    total_amount: int
) -> None:
    """Create a batch supply job that delivers to multiple sites."""
    if not delivery_sites:
        return
    
    # First destination is the primary dest_x/dest_y
    first_site = delivery_sites[0]
    
    job = jobs_module.add_job(
        "supply",
        source_x, source_y,  # Pickup location
        required=10,  # Quick job
        resource_type=resource_type,
        dest_x=first_site[0],
        dest_y=first_site[1],
        dest_z=first_site[2],
        z=source_z,
    )
    
    # Set batch delivery data
    job.delivery_queue = list(delivery_sites)  # [(x, y, z, amount), ...]
    job.pickup_amount = total_amount
    
    # Mark all sites as having pending supply jobs
    for site_x, site_y, site_z, _ in delivery_sites:
        mark_supply_job_created(site_x, site_y, site_z, resource_type)


def _cleanup_stale_pending_jobs(jobs_module) -> None:
    """Remove pending flags for supply jobs that no longer exist in the queue."""
    # Build set of actual supply jobs in queue (including all sites in delivery_queue)
    actual_supply_jobs = set()
    for job in jobs_module.JOB_QUEUE:
        if job.type == "supply":
            # Check delivery_queue for batch jobs
            if job.delivery_queue:
                for site_x, site_y, site_z, _ in job.delivery_queue:
                    actual_supply_jobs.add((site_x, site_y, site_z, job.resource_type))
            elif job.dest_x is not None and job.dest_y is not None:
                # Legacy single-destination job
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
        
        # Check orders list for this workstation
        orders = ws.get("orders", [])
        if not orders:
            continue
        
        # Get first order (FIFO)
        current_order = orders[0]
        order_recipe_id = current_order.get("recipe_id")
        
        # Skip if this order's recipe doesn't match the workstation's current recipe
        if recipe["id"] != order_recipe_id:
            # Try to set the correct recipe for this order
            if not set_workstation_recipe(x, y, z, order_recipe_id):
                continue
            recipe = get_workstation_recipe(x, y, z)
            if recipe is None or recipe["id"] != order_recipe_id:
                continue
        
        # Check if order is complete
        quantity_type = current_order.get("quantity_type", "single")
        completed = current_order.get("completed", 0)
        target = current_order.get("target", 1)
        
        allow_craft = False
        
        if quantity_type == "infinite":
            # Always craft for infinite orders
            allow_craft = True
        elif quantity_type == "single":
            # Single order: craft once
            if completed < 1:
                allow_craft = True
        elif quantity_type == "target":
            # Target order: craft until target reached
            if completed < target:
                allow_craft = True
        
        if not allow_craft:
            # This order is complete, remove it and continue to next
            orders.pop(0)
            continue
        
        # Check if stockpile has required inputs (both regular and item inputs)
        inputs_needed = recipe.get("input", {})
        item_inputs_needed = recipe.get("input_items", {})
        can_craft = True
        missing = []
        
        # Check regular resource inputs
        for res_type, amount in inputs_needed.items():
            source = zones_module.find_stockpile_with_resource(res_type, z=z)
            if source is None:
                can_craft = False
                missing.append(res_type)
        
        # Check item inputs (seeds, corpses, etc.)
        for item_type, amount in item_inputs_needed.items():
            source = zones_module.find_stockpile_with_resource(item_type, z=z)
            if source is None:
                can_craft = False
                missing.append(item_type)
        
        if not can_craft:
            # Log once per order to avoid spam
            if not current_order.get("logged_missing"):
                ws_type = ws.get("type", "unknown")
                print(f"[Crafting] {ws_type} at ({x},{y},{z}) waiting for: {missing} (recipe: {recipe['id']})")
                current_order["logged_missing"] = True
            continue
        
        # Clear logged flag when resources become available
        if current_order.get("logged_missing"):
            current_order["logged_missing"] = False
        
        # Create crafting job at workstation location
        # Determine job category based on workstation type
        workstation_type = ws.get("type", "")
        
        # For plant_bed, check if crop already exists (don't create job until harvested)
        if workstation_type == "plant_bed":
            from crops import get_crop_at
            existing_crop = get_crop_at(x, y, z)
            if existing_crop:
                # Crop still growing/mature - wait for harvest
                continue
        
        if workstation_type == "stove":
            job_category = "cooking"
        else:
            job_category = "crafting"
        
        # Calculate dynamic pressure for cooking jobs
        from job_pressure import get_job_pressure
        pressure = get_job_pressure(job_category)
        
        work_time = recipe.get("work_time", 60)
        jobs_module.add_job(
            "crafting",
            x, y,
            required=work_time,
            category=job_category,
            z=z,
            pressure=pressure,
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
    doors_data = {}
    for coord, door in _DOOR_STATES.items():
        key = f"{coord[0]},{coord[1]},{coord[2]}"
        doors_data[key] = {
            "open": bool(door.get("open", False)),
            "close_timer": int(door.get("close_timer", 0)),
        }

    windows_data = {}
    for coord, window in _WINDOW_STATES.items():
        key = f"{coord[0]},{coord[1]},{coord[2]}"
        windows_data[key] = {
            "open": bool(window.get("open", False)),
            "close_timer": int(window.get("close_timer", 0)),
        }
    
    # Fire escapes
    fire_escapes_data = {}
    for coord, escape in _FIRE_ESCAPES.items():
        key = f"{coord[0]},{coord[1]},{coord[2]}"
        fire_escapes_data[key] = {
            "platform_dir": escape.get("platform_dir"),
            "platform_pos": escape.get("platform_pos"),
            "z": escape.get("z", coord[2]),
            "complete": escape.get("complete", False),
        }
    
    return {
        "construction_sites": sites_data,
        "workstations": workstations_data,
        "doors": doors_data,
        "windows": windows_data,
        "fire_escapes": fire_escapes_data,
    }


def load_save_state(state: dict):
    """Restore buildings state from save."""
    global _CONSTRUCTION_SITES, _WORKSTATIONS, _DOOR_STATES, _WINDOW_STATES, _FIRE_ESCAPES
    global _PENDING_SUPPLY_JOBS, _PENDING_CRAFTING_JOBS
    
    _CONSTRUCTION_SITES.clear()
    _WORKSTATIONS.clear()
    _DOOR_STATES.clear()
    _WINDOW_STATES.clear()
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
        _DOOR_STATES[coord] = {
            "open": bool(door_data.get("open", False)),
            "close_timer": int(door_data.get("close_timer", door_data.get("timer", 0))),
        }
    
    # Restore windows
    for key, window_data in state.get("windows", {}).items():
        parts = key.split(",")
        coord = (int(parts[0]), int(parts[1]), int(parts[2]))
        _WINDOW_STATES[coord] = {
            "open": bool(window_data.get("open", False)),
            "close_timer": int(window_data.get("close_timer", window_data.get("timer", 0))),
        }
    
    # Restore fire escapes
    for key, escape_data in state.get("fire_escapes", {}).items():
        parts = key.split(",")
        coord = (int(parts[0]), int(parts[1]), int(parts[2]))
        _FIRE_ESCAPES[coord] = {
            "platform_dir": escape_data.get("platform_dir"),
            "platform_pos": escape_data.get("platform_pos"),
            "z": escape_data.get("z", coord[2]),
            "complete": escape_data.get("complete", False),
        }
