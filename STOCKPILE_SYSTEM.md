# Stockpile System Audit - Dec 31, 2025

## Current State

### ✅ Stockpile Filtering EXISTS
Located in `zones.py`, lines 118-127:
```python
"allow_wood": True,
"allow_mineral": True,
"allow_scrap": True,
"allow_metal": True,
"allow_power": True,
"allow_raw_food": True,
"allow_cooked_meal": True,
"allow_equipment": True,
```

### ✅ Filter Enforcement WORKS
- `_zone_allows_resource()` checks filters when finding stockpile tiles
- `process_filter_mismatch_relocation()` moves items when filters change
- Hauling respects filters via `find_stockpile_tile_for_resource()`

### ❌ NO ARCADE UI FOR FILTERS
- Pygame had stockpile filter UI (not ported to Arcade)
- Players cannot currently change stockpile filters in Arcade
- All filters default to `True` (accept everything)

---

## Item Categorization Issues

### Current System Has 3 Parallel Storage Systems:

#### 1. **Resource Storage** (`_TILE_STORAGE` in zones.py)
- For: wood, mineral, scrap, metal, power
- Uses: `add_to_tile_storage()`, `remove_from_tile_storage()`
- Filter keys: `allow_wood`, `allow_mineral`, etc.

#### 2. **Equipment Storage** (`_EQUIPMENT_STORAGE` in zones.py)
- For: crafted items, corpses, equipment
- Uses: `store_equipment_at_tile()`, `get_equipment_at_tile()`
- Filter key: `allow_equipment` (single catch-all)
- **Problem**: No granular filtering for food vs equipment vs corpses

#### 3. **World Items** (`_WORLD_ITEMS` in items.py)
- For: items on ground before hauling
- Determines storage type by tags: component, instrument, furniture, consumable
- **Problem**: Doesn't check for food tags!

---

## Specific Issues Found

### 🔴 Issue 1: Food Items Not Categorized Properly
**Current state:**
- `rat_meat` and `bird_meat` have tags `["food", "meat", "raw"]`
- But `process_equipment_haul_jobs()` doesn't check for "food" tag
- They get stored as generic "equipment" → uses `allow_equipment` filter
- **Should use**: `allow_raw_food` filter

### 🔴 Issue 2: No Cooked Meal Items
- Filter exists: `allow_cooked_meal`
- But no items are tagged as cooked meals
- Stove recipes output generic `"cooked_meal"` resource (not an item)

### 🔴 Issue 3: Material Items (pelts, feathers) Not Categorized
- `rat_pelt` has tags `["material", "leather"]`
- `feathers` has tags `["material", "soft"]`
- No "material" storage type in hauling logic
- They'll be stored as generic "equipment"

### 🔴 Issue 4: Stove Recipes Use Generic "raw_food" Resource
- Stove recipes: `"input": {"raw_food": 1}`
- This expects a resource in `_TILE_STORAGE`, not an item
- **Conflict**: Meat items are in `_EQUIPMENT_STORAGE`
- Stove can't use meat items as input!

---

## Proposed Solutions

### 1. **Add Food Storage Type to Hauling Logic**
```python
# In items.py process_equipment_haul_jobs()
if "food" in tags:
    if "raw" in tags:
        storage_type = "raw_food"
    elif "cooked" in tags or "meal" in tags:
        storage_type = "cooked_meal"
```

### 2. **Add Material Storage Type**
```python
elif "material" in tags:
    storage_type = "materials"
```

### 3. **Add Stockpile Filters for New Types**
```python
# In zones.py create_stockpile_zone()
"allow_materials": True,  # pelts, feathers, leather, etc.
"allow_corpses": True,    # animal corpses (separate from food)
```

### 4. **Fix Stove to Accept Item Inputs**
Two options:
- **A)** Add `input_items` support to stove (like bio-matter station)
- **B)** Convert meat items to generic "raw_food" resource when stored

**Recommendation: Option A** - Use `input_items` for consistency

### 5. **Create Stockpile Filter UI Panel**
- Click stockpile tile → open filter panel
- Checkboxes for each filter type
- Save changes to zone data
- Trigger relocation jobs for mismatched items

---

## Implementation Priority

1. **Fix food item hauling** - categorize as `raw_food` not `equipment`
2. **Add material storage type** - for pelts/feathers
3. **Update stove recipes** - use `input_items` instead of `input`
4. **Add corpse filter** - separate from food/equipment
5. **Create stockpile filter UI** - let players control filters
6. **Add cooked meal items** - actual item instances, not just resources

---

## Rules to Lock In

### Item Storage Rules:
1. **Resources** (wood, scrap, metal, mineral, power) → `_TILE_STORAGE`
2. **Raw Food Items** (meat, produce) → `_EQUIPMENT_STORAGE` with `raw_food` filter
3. **Cooked Meals** → `_EQUIPMENT_STORAGE` with `cooked_meal` filter
4. **Equipment** (armor, tools, implants) → `_EQUIPMENT_STORAGE` with `equipment` filter
5. **Materials** (pelts, feathers, leather) → `_EQUIPMENT_STORAGE` with `materials` filter
6. **Corpses** → `_EQUIPMENT_STORAGE` with `corpses` filter

### Recipe Input Rules:
1. **Basic resources** → use `"input": {"wood": 2}`
2. **Items/equipment** → use `"input_items": {"rat_corpse": 1}`
3. **Food items** → use `"input_items": {"rat_meat": 2}`

### Stockpile Filter Rules:
1. Each filter defaults to `True` (accept all)
2. Filters are per-zone, not per-tile
3. Changing filters triggers relocation jobs
4. Equipment storage needs granular filters (not just one catch-all)
