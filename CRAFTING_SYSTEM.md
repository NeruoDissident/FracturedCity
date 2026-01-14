# Crafting System Reference

This document explains how the crafting system works in Fractured City and where to find/add recipes.

---

## Overview

The game has **two types of crafting systems**:

1. **Type 1: Static Recipes** - Explicit inputs/outputs defined in `buildings.py`
2. **Type 2: Dynamic Recipes** - Outputs generated based on input metadata

Both systems use the same workstation infrastructure and job system, but differ in how outputs are determined.

---

## Type 1: Static Recipes (Most Workstations)

### How It Works
- Recipes are explicitly defined in `buildings.py::BUILDING_TYPES[station]["recipes"]`
- Inputs and outputs are hardcoded
- No metadata tracking (yet)
- Execution: `colonist.py::_crafting_work_at_bench()` lines 4016-4075

### Recipe Format
```python
{
    "id": "work_gloves",           # Unique recipe ID
    "name": "Work Gloves",         # Display name
    "input": {"scrap": 2},         # Fungible resources (wood, metal, power, raw_food)
    "input_items": {},             # Items with metadata (optional)
    "output_item": "work_gloves",  # Single item output
    "output": {},                  # OR resource outputs (power, cooked_meal)
    "work_time": 60                # Ticks to complete
}
```

### Input Types
- **`"input": {}`** - Fungible resources (any wood is the same)
  - `wood`, `metal`, `scrap`, `mineral`, `power`, `raw_food`
- **`"input_items": {}`** - Items with metadata (each item is unique)
  - `corpse`, `scrap_meat`, `poultry_meat`, components

### Output Types
- **`"output_item": "item_id"`** - Single item (equipment, furniture)
- **`"output": {"resource": amount}`** - Resources (power, cooked_meal)

### Workstations Using Type 1
- **Salvager's Bench** - Basic salvaging/refining
- **Spark Bench** - Electronics crafting
- **Tinker Station** - Instruments, devices
- **Gutter Forge** - Metalworking, weapons, armor
- **Skinshop Loom** - Clothing, furniture
- **Cortex Spindle** - Implants, charms
- **Gutter Still** - Brewing, distilling
- **Generator** - Power production
- **Stove** - Cooking (see hybrid section below)

---

## Type 2: Dynamic Recipes (Butchering)

### How It Works
- Recipe has **empty `"output": {}`** in `buildings.py`
- Actual outputs determined by input metadata (corpse species)
- Species data in `animals.py::AnimalSpecies`
- Execution: `colonist.py::_crafting_work_at_bench()` lines 4080-4130
- Metadata preserved: `source_species`, `harvested_by`

### Recipe Format
```python
{
    "id": "butcher",
    "name": "Butcher Corpse",
    "input_items": {"corpse": 1},
    "output": {},  # EMPTY - dynamic generation!
    "work_time": 60
}
```

### How Outputs Are Generated
1. Corpse item has `source_species` metadata (set when animal dies)
2. Workstation stores `corpse_metadata` when colonist delivers corpse
3. Butchering looks up species in `animals.py::AnimalSpecies`
4. Generates outputs based on:
   - `species.meat_yield` (min, max) → scrap_meat or poultry_meat
   - `species.materials` → pelts, feathers, etc.
5. Spawns items with metadata preserved

### Example Outputs (from animals.py)
```python
# Rat corpse
AnimalSpecies.RAT = {
    "meat_yield": (1, 2),           # 1-2 scrap_meat
    "materials": {"rat_pelt": (1, 1)}  # 1 rat_pelt
}

# Bird corpse
AnimalSpecies.BIRD = {
    "meat_yield": (2, 3),              # 2-3 poultry_meat
    "materials": {"feathers": (1, 2)}  # 1-2 feathers
}

# Cat corpse
AnimalSpecies.CAT = {
    "meat_yield": (2, 3),           # 2-3 scrap_meat
    "materials": {"cat_pelt": (1, 1)}  # 1 cat_pelt
}
```

### Workstations Using Type 2
- **Bio-Matter Salvage Station** - Butchering corpses

---

## Hybrid: Stove (Both Types)

The stove has **multiple recipes** using both systems:

### Resource-Based Recipe (Type 1)
```python
{"id": "simple_meal", "name": "Simple Meal", 
 "input": {"raw_food": 2, "power": 1},  # Fungible resources
 "output": {"cooked_meal": 1},          # Generic output
 "work_time": 60}
```
- Uses `raw_food` resource (harvested from plants/foraging)
- Produces generic `cooked_meal`

### Item-Based Recipes (Type 1)
```python
{"id": "grilled_scraps", "name": "Grilled Scraps",
 "input_items": {"scrap_meat": 1},  # Item with metadata
 "input": {"power": 1},
 "output": {"cooked_meal": 1},      # Metadata NOT preserved (yet)
 "work_time": 50}
```
- Uses `scrap_meat` or `poultry_meat` items (from butchering)
- Items have `source_species` metadata
- **Currently:** Metadata is lost when cooking (future feature)

---

## Adding New Recipes

### For Type 1 (Static) Workstations

1. Open `buildings.py`
2. Find your workstation in `BUILDING_TYPES`
3. Add recipe to `"recipes"` list:

```python
"gutter_forge": {
    "recipes": [
        # ... existing recipes ...
        {"id": "new_item", "name": "New Item",
         "input": {"metal": 3, "scrap": 1},
         "output_item": "new_item",
         "work_time": 80},
    ]
}
```

4. Define the item in `items.py` if it's equipment/furniture

### For Type 2 (Dynamic) Workstations

1. Open `animals.py`
2. Add/modify species data:

```python
NEW_ANIMAL = {
    "id": "new_animal",
    "meat_yield": (2, 4),  # Min, max meat
    "materials": {
        "new_pelt": (1, 1),
        "new_material": (0, 2)
    }
}
```

3. Add species lookup in `colonist.py::_crafting_work_at_bench()` (lines 4093-4106)

---

## File Locations

- **`buildings.py`** - All workstation definitions and Type 1 recipes
- **`animals.py`** - Species data for Type 2 butchering outputs
- **`colonist.py`** - Crafting execution logic (lines 3966-4200)
- **`items.py`** - Item definitions (equipment, furniture, materials)
- **`zones.py`** - Stockpile system for storing inputs/outputs

---

## Future Features (Not Yet Implemented)

- **Metadata propagation in cooking** - Track what meat was used in meals
- **Crafted by tracking** - Show which colonist crafted an item
- **Material lineage** - Track full crafting chain (rat pelt → leather → armor)
- **Processing recipes** - Tanning hides, refining materials
- **Multi-material recipes** - Hunting cap from cat pelt + crow feathers

---

## Quick Reference: All Recipes

### Salvager's Bench
- Refine Metal: 2 Scrap → 1 Metal
- Metal Components: 1 Metal → 3 Scrap

### Spark Bench
- Salvage Wire: 1 Scrap → Wire
- Craft Resistor: 1 Scrap + 1 Mineral → Resistor
- Craft Capacitor: 1 Scrap + 1 Metal → Capacitor
- Craft Circuit Chip: 2 Metal + 1 Mineral + 2 Wire → Chip
- Craft LED: 1 Mineral + 1 Wire → LED

### Tinker Station
- Scrap Guitar: 2 Wood + 1 Metal + 2 Wire → Scrap Guitar
- Drum Kit: 3 Scrap + 2 Wood → Drum Kit
- Synth Keyboard: 2 Chip + 3 Wire + 2 Scrap → Synth
- Harmonica: 1 Metal + 1 Scrap → Harmonica
- Amplifier: 1 Chip + 2 Wire + 2 Metal → Amp
- Vending Machine: 3 Metal + 2 Chip + 1 LED → Vending Machine

### Gutter Forge
- Salvage Tool: 2 Metal + 1 Scrap → Salvage Tool
- Work Gloves: 2 Scrap → Work Gloves
- Signal Gauntlet: 2 Metal + 1 Power → Signal Gauntlet
- Gutter Slab: 4 Wood + 2 Mineral → Gutter Slab
- Pipe Weapon: 3 Metal + 1 Scrap → Pipe Weapon
- Scrap Blade: 2 Metal + 2 Scrap → Scrap Blade
- Reinforced Door: 4 Metal + 2 Wood → Reinforced Door
- Weapon Rack: 2 Metal + 3 Wood → Weapon Rack
- Armor Plate: 3 Metal → Armor Plate

### Skinshop Loom
- Hard Hat: 2 Scrap → Hard Hat
- Work Vest: 2 Scrap + 1 Wood → Work Vest
- Padded Jacket: 3 Scrap → Padded Jacket
- Work Boots: 2 Scrap → Work Boots
- Scrap Armor: 3 Metal + 2 Scrap → Scrap Armor
- Crash Bed: 2 Scrap + 2 Wood → Crash Bed
- Comfort Chair: 2 Wood + 1 Scrap → Comfort Chair
- Bar Stool: 1 Scrap + 1 Wood → Bar Stool
- Storage Locker: 3 Wood + 1 Metal → Storage Locker
- Dining Table: 4 Wood → Dining Table
- Wall Lamp: 1 Metal + 1 Power → Wall Lamp

### Cortex Spindle
- Focus Chip: 2 Metal + 1 Mineral → Focus Chip
- Echo Dampener: 1 Metal + 2 Mineral → Echo Dampener
- Lucky Coin: 1 Metal → Lucky Coin
- Memory Locket: 1 Metal + 1 Mineral → Memory Locket
- Signal Stone: 2 Mineral + 1 Power → Signal Stone
- Medical Scanner: 2 Metal + 2 Mineral + 1 Power → Medical Scanner
- Stim Injector: 1 Metal + 2 Mineral → Stim Injector
- Neural Interface: 3 Metal + 3 Mineral + 2 Power → Neural Interface
- Data Slate: 1 Metal + 1 Mineral → Data Slate

### Gutter Still
- Brew Swill: 2 Raw Food + 1 Scrap → Swill
- Distill Guttershine: 3 Raw Food + 2 Scrap → Guttershine

### Generator
- Burn Wood for Power: 3 Wood → 1 Power
- Burn Scrap for Power: 4 Scrap → 1 Power

### Stove
- Simple Meal: 2 Raw Food + 1 Power → 1 Cooked Meal
- Grilled Scraps: 1 Scrap Meat + 1 Power → 1 Cooked Meal
- Meat Stew: 2 Scrap Meat + 1 Power → 1 Cooked Meal
- Hearty Roast: 3 Scrap Meat + 2 Power → 1 Cooked Meal
- Poultry Roast: 2 Poultry Meat + 1 Power → 1 Cooked Meal

### Bio-Matter Salvage Station (Dynamic)
- Butcher Corpse: 1 Corpse → Meat + Materials (based on species)
  - Rat: 1-2 Scrap Meat, 1 Rat Pelt
  - Bird: 2-3 Poultry Meat, 1-2 Feathers
  - Cat: 2-3 Scrap Meat, 1 Cat Pelt
  - Dog: 3-5 Scrap Meat, 1-2 Dog Pelt
  - Raccoon: 3-4 Scrap Meat, 1 Raccoon Pelt
  - Opossum: 2-3 Scrap Meat, 1 Opossum Pelt
