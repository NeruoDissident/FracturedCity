# Crop Metadata Implementation Plan

## Goal
Implement a metadata system for harvested crops (similar to corpses/meat) that allows recipes to use generic categories like "any vegetable" or "any meat" instead of specific items.

---

## Existing System Analysis

### 1. Corpse → Meat Metadata Flow (REFERENCE PATTERN)

**Step 1: Animal dies with species data**
- Location: `animals.py` lines 35-51 (AnimalSpecies.RAT example)
- Each species has: `"id": "rat"`, `"corpse_item": "corpse"`, `"meat_yield": (1, 2)`, `"materials": {"rat_pelt": (1, 1)}`

**Step 2: Corpse spawned with metadata**
- Location: `items.py` lines 104-118 (corpse ItemDef)
- Generic item: `id="corpse"`, `tags=["corpse", "organic", "animal"]`
- Metadata added at spawn: `source_species="rat"` (set when animal dies)

**Step 3: Butchering reads metadata**
- Location: `colonist.py` lines 4181-4241 (TYPE 2 CRAFTING: DYNAMIC BUTCHERING)
- Recipe: `{"id": "butcher", "input_items": {"corpse": 1}, "output": {}}`
- System reads `corpse_metadata` from workstation
- Looks up `source_species` → finds AnimalSpecies.RAT
- Generates outputs: `scrap_meat` (1-2), `rat_pelt` (1)

**Step 4: Meat spawned with preserved metadata**
- Location: `colonist.py` lines 4260-4277
- Checks `material_type in ["meat", "hide", "feather", "bone", "organ", "fat"]`
- Calls `add_item_metadata(latest_item, source_species=source_species, harvest_tick=game_tick, harvested_by=self.uid)`
- Result: Meat item has `source_species="rat"` metadata

**Step 5: Display name shows metadata**
- Location: `items.py` lines 910-913
- Format: `"Scrap Meat (Rat)"` instead of just `"Scrap Meat"`

### 2. Recipe Input System (CURRENT)

**Type 1: Specific Item Match**
- Location: `buildings.py` line 216-219 (stove recipes)
- Example: `{"id": "grilled_scraps", "input_items": {"scrap_meat": 1}}`
- System looks for EXACT item ID `"scrap_meat"` in stockpile
- Location: `colonist.py` lines 3950-3955 (fetch item inputs)
- Uses `zones.find_stockpile_with_resource(item_type, z=job.z)`

**Type 2: Tag-Based Match (NOT IMPLEMENTED YET)**
- Would need: Recipe specifies tag like `"input_items": {"@meat": 2}`
- System searches stockpile for ANY item with `"meat"` tag
- Matches: `scrap_meat`, `poultry_meat`, etc.

---

## Implementation Plan

### STEP 1: Add Crop Category System to CROPS Definition
**File:** `crops.py` lines 18-31

**Current:**
```python
CROPS = {
    "tomato": {
        "name": "Tomato",
        "seed_item": "tomato_seed",
        "harvest_item": "tomato",
        "growth_stages": 3,
        "ticks_per_stage": 3000,
        "sprites": [...],
        "harvest_yield": 2,
    }
}
```

**Add:**
```python
CROPS = {
    "tomato": {
        "name": "Tomato",
        "seed_item": "tomato_seed",
        "harvest_item": "tomato",
        "category": "vegetable",  # NEW: vegetable, fruit, grain, herb
        "growth_stages": 3,
        "ticks_per_stage": 3000,
        "sprites": [...],
        "harvest_yield": 2,
    }
}
```

**Pattern:** Replicates `AnimalSpecies.RAT["id"]` pattern

---

### STEP 2: Update Tomato ItemDef with Category Tag
**File:** `items.py` lines 341-353

**Current:**
```python
register_item(ItemDef(
    id="tomato",
    name="Tomato",
    slot=None,
    tags=["organic", "food", "raw_food"],
    material_type="food",
    ...
))
```

**Change to:**
```python
register_item(ItemDef(
    id="tomato",
    name="Tomato",
    slot=None,
    tags=["organic", "food", "raw_food", "vegetable"],  # ADD "vegetable"
    material_type="food",
    ...
))
```

**Pattern:** Replicates `scrap_meat` tags `["food", "meat", "raw", "rodent"]` (items.py line 592)

---

### STEP 3: Add Metadata to Harvested Crops
**File:** `crops.py` lines 163-185 (harvest_crop function)

**Current:**
```python
def harvest_crop(x: int, y: int, z: int) -> Optional[Tuple[str, int]]:
    crop = _ACTIVE_CROPS.get((x, y, z))
    if crop is None:
        return None
    
    crop_def = CROPS.get(crop["crop_type"])
    if crop_def is None:
        return None
    
    if crop["stage"] < crop_def["growth_stages"] - 1:
        return None
    
    harvest_item = crop_def["harvest_item"]
    harvest_yield = crop_def.get("harvest_yield", 1)
    
    remove_crop(x, y, z)
    
    return (harvest_item, harvest_yield)
```

**Change to:**
```python
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
        return None
    
    harvest_item = crop_def["harvest_item"]
    harvest_yield = crop_def.get("harvest_yield", 1)
    crop_type = crop["crop_type"]  # NEW: Get crop type for metadata
    
    remove_crop(x, y, z)
    
    return (harvest_item, harvest_yield, crop_type)  # NEW: Return crop_type
```

**Pattern:** Replicates butchering return pattern (colonist.py lines 4196-4197 stores `source_species`)

---

### STEP 4: Update Harvest Job to Add Metadata
**File:** `colonist.py` lines 3179-3203 (harvest_crop job completion)

**Current:**
```python
elif job.type == "harvest_crop":
    from crops import harvest_crop
    from items import spawn_world_item
    
    result = harvest_crop(job.x, job.y, job.z)
    if result:
        item_id, quantity = result
        # Spawn harvested items adjacent to plant bed
        for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
            drop_x, drop_y = job.x + dx, job.y + dy
            if grid.is_walkable(drop_x, drop_y, job.z):
                for _ in range(quantity):
                    spawn_world_item(drop_x, drop_y, job.z, item_id)
                print(f"[Farming] {self.name} harvested {quantity}x {item_id} at ({job.x}, {job.y}, {job.z})")
                break
```

**Change to:**
```python
elif job.type == "harvest_crop":
    from crops import harvest_crop
    from items import spawn_world_item, add_item_metadata, get_world_items_at
    
    result = harvest_crop(job.x, job.y, job.z)
    if result:
        item_id, quantity, crop_type = result  # NEW: Unpack crop_type
        # Spawn harvested items adjacent to plant bed
        for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
            drop_x, drop_y = job.x + dx, job.y + dy
            if grid.is_walkable(drop_x, drop_y, job.z):
                for _ in range(quantity):
                    spawn_world_item(drop_x, drop_y, job.z, item_id)
                    
                    # NEW: Add metadata to harvested crop
                    items_at_loc = get_world_items_at(drop_x, drop_y, job.z)
                    if items_at_loc:
                        latest_item = items_at_loc[-1]
                        add_item_metadata(
                            latest_item,
                            source_species=crop_type,  # "tomato" → shows as "Tomato (Tomato)"
                            harvest_tick=game_tick,
                            harvested_by=self.uid
                        )
                
                print(f"[Farming] {self.name} harvested {quantity}x {item_id} ({crop_type}) at ({job.x}, {job.y}, {job.z})")
                break
```

**Pattern:** EXACT replication of butchering metadata (colonist.py lines 4260-4277)

---

### STEP 5: Implement Tag-Based Recipe Matching
**File:** `zones.py` (find_stockpile_with_resource function)

**Current Behavior:**
- Searches for EXACT item ID match
- Example: `find_stockpile_with_resource("scrap_meat", z=0)` only finds `scrap_meat`

**New Behavior:**
- If resource_type starts with `@`, treat as tag search
- Example: `find_stockpile_with_resource("@meat", z=0)` finds ANY item with `"meat"` tag
- Example: `find_stockpile_with_resource("@vegetable", z=0)` finds ANY item with `"vegetable"` tag

**Implementation:**
```python
def find_stockpile_with_resource(resource_type: str, z: int = 0) -> Optional[Tuple[int, int, int]]:
    """Find a stockpile that has the given resource or item.
    
    If resource_type starts with '@', search by tag instead of exact ID.
    Example: '@meat' finds any item with 'meat' tag.
    """
    search_by_tag = resource_type.startswith("@")
    if search_by_tag:
        tag_to_find = resource_type[1:]  # Remove '@' prefix
    
    for (x, y, zone_z), zone in _ZONES.items():
        if zone_z != z:
            continue
        if zone.get("type") != "stockpile":
            continue
        
        # Check tile storage (regular resources)
        tile_storage = zone.get("tile_storage", {})
        if not search_by_tag:
            if resource_type in tile_storage and tile_storage[resource_type] > 0:
                return (x, y, zone_z)
        
        # Check equipment storage (items with metadata)
        equipment_storage = zone.get("equipment_storage", [])
        for item in equipment_storage:
            if search_by_tag:
                # Tag-based search
                from items import get_item_def
                item_def = get_item_def(item.get("id", ""))
                if item_def and tag_to_find in item_def.tags:
                    return (x, y, zone_z)
            else:
                # Exact ID search
                if item.get("id") == resource_type:
                    return (x, y, zone_z)
    
    return None
```

**Pattern:** Extends existing function, similar to how butchering checks `material_type` (colonist.py line 4261)

---

### STEP 6: Update Stove Recipes
**File:** `buildings.py` lines 213-220

**Current:**
```python
"recipes": [
    {"id": "simple_meal", "name": "Simple Meal", "input": {"raw_food": 2, "power": 1}, "output": {"cooked_meal": 1}, "work_time": 40},
    {"id": "grilled_scraps", "name": "Grilled Scraps", "input_items": {"scrap_meat": 1}, "input": {"power": 1}, "output": {"cooked_meal": 1}, "work_time": 50},
    {"id": "meat_stew", "name": "Meat Stew", "input_items": {"scrap_meat": 2}, "input": {"power": 1}, "output": {"cooked_meal": 1}, "work_time": 80},
    {"id": "hearty_roast", "name": "Hearty Roast", "input_items": {"scrap_meat": 3}, "input": {"power": 2}, "output": {"cooked_meal": 1}, "work_time": 100},
    {"id": "poultry_roast", "name": "Poultry Roast", "input_items": {"poultry_meat": 2}, "input": {"power": 1}, "output": {"cooked_meal": 1}, "work_time": 70},
],
```

**Change to:**
```python
"recipes": [
    {"id": "simple_meal", "name": "Simple Meal", "input": {"raw_food": 2, "power": 1}, "output": {"cooked_meal": 1}, "work_time": 40},
    {"id": "grilled_scraps", "name": "Grilled Scraps", "input_items": {"@meat": 1}, "input": {"power": 1}, "output": {"cooked_meal": 1}, "work_time": 50},
    {"id": "meat_stew", "name": "Meat Stew", "input_items": {"@meat": 2}, "input": {"power": 1}, "output": {"cooked_meal": 1}, "work_time": 80},
    {"id": "hearty_roast", "name": "Hearty Roast", "input_items": {"@meat": 2, "@vegetable": 1}, "input": {"power": 2}, "output": {"cooked_meal": 1}, "work_time": 100},
    {"id": "poultry_roast", "name": "Poultry Roast", "input_items": {"@meat": 2}, "input": {"power": 1}, "output": {"cooked_meal": 1}, "work_time": 70},
    {"id": "vegetable_stew", "name": "Vegetable Stew", "input_items": {"@vegetable": 2}, "input": {"power": 1}, "output": {"cooked_meal": 1}, "work_time": 60},
],
```

**Pattern:** Uses `@` prefix for tag-based matching (new convention)

---

## Summary of Changes

### Files Modified:
1. `crops.py` - Add `"category"` field to CROPS definitions
2. `items.py` - Add category tags to crop ItemDefs (`"vegetable"`, `"fruit"`, etc.)
3. `crops.py` - Modify `harvest_crop()` to return crop_type
4. `colonist.py` - Add metadata to harvested crops (lines 3179-3203)
5. `zones.py` - Implement tag-based search in `find_stockpile_with_resource()`
6. `buildings.py` - Update stove recipes to use `@meat`, `@vegetable` tags

### No Hallucinations:
- Every pattern is copied from existing corpse/meat system
- Tag-based matching extends existing `find_stockpile_with_resource()` function
- Metadata flow is IDENTICAL to butchering flow
- Display names automatically work (already implemented in items.py lines 910-913)

### Result:
- Tomatoes harvested → Tagged as "vegetable" → Show as "Tomato (Tomato)"
- Recipes can use `"@vegetable"` to accept ANY vegetable (tomato, carrot, potato, etc.)
- Recipes can use `"@meat"` to accept ANY meat (scrap_meat, poultry_meat, etc.)
- System is extensible: Add new crops with categories, recipes automatically work
