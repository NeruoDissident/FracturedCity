# Tagging System Implementation - Complete
## Dec 31, 2025

## ✅ All Phases Implemented

### **Phase 1: Enhanced Item Tags** ✅
Updated all hunting-related items with detailed tag hierarchy:

**Rat Meat:**
```python
tags=["food", "meat", "raw", "rodent", "rat", "low_quality", "common"]
```

**Bird Meat:**
```python
tags=["food", "meat", "raw", "poultry", "bird", "medium_quality", "common"]
```

**Rat Pelt:**
```python
tags=["material", "leather", "pelt", "rodent", "rat", "low_quality"]
```

**Feathers:**
```python
tags=["material", "soft", "feather", "poultry", "bird", "medium_quality"]
```

---

### **Phase 2: Tag-Priority Hauling** ✅
Updated `process_equipment_haul_jobs()` in `items.py` to categorize items by tag priority:

**Priority Order:**
1. **Corpses** → `corpses` filter
2. **Food** → `raw_food` or `cooked_meal` filter
3. **Materials** → `materials` filter
4. **Components** → `components` filter
5. **Instruments** → `instruments` filter
6. **Furniture** → `furniture` filter
7. **Consumables** → `consumables` filter
8. **Default** → `equipment` filter

**Result:**
- Rat meat → hauled to stockpiles with `allow_raw_food = True`
- Rat pelt → hauled to stockpiles with `allow_materials = True`
- Corpses → hauled to stockpiles with `allow_corpses = True`

---

### **Phase 3: Tag-Based Recipe Matching** ✅
Added two new functions to `items.py`:

#### `find_items_by_tag(tag_requirement, count, zones_module)`
- Finds items matching single tag ("meat") or multi-tag ("meat+poultry")
- Searches all equipment storage in stockpiles
- Returns list of (coord, item) tuples

#### `find_items_for_recipe(recipe, zones_module)`
- Matches recipe `input_items` requirements
- Supports exact item IDs OR tag matching
- Returns dict of found items or None if insufficient

**Example Usage:**
```python
# Recipe requires 6x any meat
recipe = {"input_items": {"meat": 6}}
found = find_items_for_recipe(recipe, zones_module)
# Returns: {"meat": [(coord1, rat_meat), (coord2, rat_meat), (coord3, bird_meat), ...]}
```

---

### **Phase 4: Stove Recipes with Tag Matching** ✅
Updated stove recipes to use `input_items` with flexible tag matching:

**Generic Recipe (Any Meat):**
```python
{"id": "simple_meal", "input_items": {"meat": 1}, "input": {"power": 1}, ...}
```
- Accepts: rat_meat, bird_meat, any future meat

**Flexible Recipe (Lots of Meat):**
```python
{"id": "meat_stew", "input_items": {"meat": 6}, ...}
```
- Grabs any 6 meat items from stockpile
- Could be: 2x rat + 4x bird, or 6x rat, etc.

**Family-Specific Recipes:**
```python
{"id": "poultry_roast", "input_items": {"meat+poultry": 4}, ...}
{"id": "rodent_skewers", "input_items": {"meat+rodent": 3}, ...}
```
- Multi-tag matching: item must have ALL tags
- Poultry roast only accepts bird_meat (has "meat" AND "poultry")
- Rodent skewers only accepts rat_meat (has "meat" AND "rodent")

---

### **Stockpile Filters Enhanced** ✅
Added new filters to `zones.py`:

```python
"allow_raw_food": True,      # Raw meat, produce
"allow_cooked_meal": True,   # Prepared meals
"allow_materials": True,     # NEW - Pelts, feathers, leather
"allow_corpses": True,       # NEW - Animal corpses
"allow_equipment": True,     # Armor, tools, weapons
"allow_components": True,    # NEW - Electronics, parts
"allow_instruments": True,   # NEW - Musical instruments
"allow_furniture": True,     # NEW - Placeable items
"allow_consumables": True,   # NEW - Consumable items
```

**All filters default to `True`** (accept everything) for backwards compatibility.

---

### **Bio-Matter Salvage Station** ✅
Added to workstations menu in `ui_arcade.py`:
```python
{"label": "Bio-Matter Salvage", "tool": "bio_matter_salvage_station", "cost": "3 metal, 2 scrap"}
```

**Recipes:**
- Butcher Rat Corpse → 2x rat_meat + 1x rat_pelt
- Butcher Bird Corpse → 3x bird_meat + 2x feathers

---

## How It Works

### **Full Hunting Loop:**

1. **Hunt & Kill** → Rat dies, corpse spawns
2. **Haul Corpse** → Tagged "corpse" → goes to stockpile with `allow_corpses = True`
3. **Butcher** → Bio-matter station uses `input_items: {"rat_corpse": 1}`
4. **Output** → 2x rat_meat (tagged "food", "meat", "raw") + 1x rat_pelt (tagged "material")
5. **Haul Meat** → Tagged "food" → goes to stockpile with `allow_raw_food = True`
6. **Haul Pelt** → Tagged "material" → goes to stockpile with `allow_materials = True`
7. **Cook** → Stove uses `input_items: {"meat": 6}` → grabs ANY 6 meat items
8. **Output** → Cooked meal (resource)

---

## Scalability

### **Adding New Animals:**

Just register items with appropriate tags:

```python
# Mutant Rat (Echo-affected)
register_item(ItemDef(
    id="mutant_rat_meat",
    name="Mutant Rat Meat",
    tags=["food", "meat", "raw", "rodent", "mutant_rat", "medium_quality", "echo_tainted"],
    ...
))

# Seagull
register_item(ItemDef(
    id="seagull_meat",
    name="Seagull Meat",
    tags=["food", "meat", "raw", "poultry", "seagull", "medium_quality", "fishy"],
    ...
))
```

**Automatically works with:**
- Generic "meat" recipes (any meat)
- Family recipes ("poultry" only, "rodent" only)
- Stockpile filters (raw_food)
- Hauling system (categorizes by tags)

---

## Recipe Examples

### **Generic (Any Meat):**
```python
{"id": "meat_stew", "input_items": {"meat": 6}}
```
- Uses: 2x rat + 4x bird, or 6x rat, or 3x rat + 3x mutant_rat, etc.

### **Family-Specific:**
```python
{"id": "poultry_roast", "input_items": {"meat+poultry": 4}}
```
- Uses: Only bird_meat, seagull_meat (has "meat" AND "poultry")
- Excludes: rat_meat (no "poultry" tag)

### **Exact:**
```python
{"id": "rat_brain_delicacy", "input_items": {"rat_meat": 3}}
```
- Uses: Only rat_meat specifically

---

## Future Enhancements (Not Yet Implemented)

### **Phase 5: Stockpile Filter UI**
- Click stockpile → open filter panel
- Checkboxes for each filter type
- Save changes → trigger relocation jobs

### **Phase 6: Quality System**
- Track quality from tags (low_quality, medium_quality, high_quality)
- Recipe output quality = average of input quality
- UI shows quality in item names

### **Phase 7: Recipe UI Transparency**
- Show which specific items are being used
- "Crafting Meat Stew: Using 2x Rat Meat, 4x Pigeon Meat"
- Display quality bonus/penalty

---

## Consistency Rules

### **Storage:**
- Resources (wood, scrap) → `_TILE_STORAGE`
- Items (meat, equipment) → `_EQUIPMENT_STORAGE`

### **Recipes:**
- Basic resources → `"input": {"wood": 2}`
- Items/food → `"input_items": {"rat_meat": 1}` or `{"meat": 6}`

### **Tags:**
- Most specific → Most general
- Example: ["food", "meat", "raw", "poultry", "pigeon", "medium_quality"]

### **Filters:**
- All default to `True` (accept everything)
- Per-zone, not per-tile
- Changing filters triggers relocation jobs

---

## Testing Checklist

- [x] Bio-matter station appears in build menu
- [ ] Hunt rat → corpse spawns
- [ ] Corpse hauls to stockpile (allow_corpses)
- [ ] Butcher corpse → produces meat + pelt
- [ ] Meat hauls to stockpile (allow_raw_food)
- [ ] Pelt hauls to stockpile (allow_materials)
- [ ] Stove shows meat recipes
- [ ] Stove can craft with meat items
- [ ] Recipe uses any combination of meat types

---

## Files Modified

1. **items.py**
   - Enhanced tags for rat_meat, bird_meat, rat_pelt, feathers
   - Updated `process_equipment_haul_jobs()` with tag priority
   - Added `find_items_by_tag()` function
   - Added `find_items_for_recipe()` function

2. **zones.py**
   - Added new stockpile filters (materials, corpses, components, etc.)
   - Updated `get_zone_filters()` to return all filters

3. **buildings.py**
   - Updated stove recipes to use `input_items` with tag matching
   - Added flexible recipes (any meat, poultry only, rodent only)

4. **ui_arcade.py**
   - Added bio-matter salvage station to workstations menu

---

## System is Ready! 🎉

The tagging system is fully implemented and ready for testing. You can now:
- Add 30+ animals with unique meat types
- Create flexible recipes (any meat) or specific recipes (poultry only)
- Scale infinitely with consistent rules
- See which items are used in recipes (future UI enhancement)
