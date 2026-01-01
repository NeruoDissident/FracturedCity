# Item Tagging System - Flexible & Modular Design
## Dec 31, 2025

## Design Goals

1. **Scalable**: Support 30+ animal types, each with unique meat
2. **Flexible Recipes**: "6x meat" can be ANY combination (2 rat + 4 pigeon)
3. **Specific Recipes**: "Pigeon Wing Stew" requires pigeon specifically
4. **Transparent**: UI shows WHICH items are being used ("2x Rat Meat, 4x Pigeon Meat")
5. **Consistent**: Same system for all items (food, materials, equipment)

---

## Tag Hierarchy System

### Multi-Level Tags (Most Specific → Most General)

**Example: Rat Meat**
```python
tags = [
    "food",           # Top level: edible
    "meat",           # Category: protein source
    "raw",            # State: needs cooking
    "rodent",         # Animal family
    "rat",            # Specific animal
    "low_quality",    # Quality tier
    "common"          # Rarity
]
```

**Example: Pigeon Meat**
```python
tags = [
    "food",
    "meat",
    "raw",
    "poultry",        # Animal family
    "pigeon",         # Specific animal
    "medium_quality",
    "common"
]
```

**Example: Rat Pelt**
```python
tags = [
    "material",       # Top level: crafting material
    "leather",        # Category: material type
    "pelt",           # Subcategory: animal skin
    "rodent",
    "rat",
    "low_quality",
    "common"
]
```

---

## Recipe Input Matching

### Three Types of Recipe Inputs:

#### 1. **Specific Item** (Exact Match)
```python
"input_items": {
    "rat_meat": 2  # Must be rat meat specifically
}
```
- Used for: Specialty recipes ("Rat Skewers")
- Matches: Only `rat_meat` item

#### 2. **Tag Match** (Any Item With Tag)
```python
"input_items": {
    "meat": 6  # Any meat works
}
```
- Used for: Generic recipes ("Meat Stew")
- Matches: rat_meat, pigeon_meat, bird_meat, etc.
- System finds 6 meat items from stockpile (any combination)

#### 3. **Multi-Tag Match** (All Tags Required)
```python
"input_items": {
    "meat+poultry": 4  # Must be poultry meat
}
```
- Used for: Semi-specific recipes ("Poultry Stew")
- Matches: pigeon_meat, bird_meat (both have "meat" AND "poultry")
- Excludes: rat_meat (has "meat" but not "poultry")

---

## Implementation Details

### Item Definition Format
```python
register_item(ItemDef(
    id="rat_meat",
    name="Rat Meat",
    slot=None,
    tags=["food", "meat", "raw", "rodent", "rat", "low_quality", "common"],
    icon_color=(140, 90, 80),
    description="Raw rat meat. Low quality but edible. Cook before eating.",
    # New fields:
    nutrition=10,      # Food value
    quality=1,         # 1-5 scale
    spoilage_time=300  # Ticks before spoiling (optional)
))
```

### Recipe Format
```python
{
    "id": "meat_stew",
    "name": "Meat Stew",
    "input_items": {
        "meat": 6,           # Any 6 meat items
        "vegetable": 2       # Any 2 vegetables (future)
    },
    "output_item": "meat_stew",
    "work_time": 120,
    "quality_bonus": True    # Higher quality inputs = better output
}
```

### Crafting Logic (Pseudocode)
```python
def find_items_for_recipe(recipe, stockpiles):
    """Find items matching recipe requirements."""
    required = recipe["input_items"]
    found_items = {}
    
    for requirement, count in required.items():
        # Check if it's a specific item or tag match
        if requirement in ITEM_REGISTRY:
            # Specific item - find exact matches
            items = find_items_by_id(requirement, count, stockpiles)
        else:
            # Tag match - find any items with this tag
            items = find_items_by_tag(requirement, count, stockpiles)
        
        if len(items) < count:
            return None  # Not enough items
        
        found_items[requirement] = items[:count]
    
    return found_items

def find_items_by_tag(tag, count, stockpiles):
    """Find items that have the specified tag."""
    matches = []
    
    # Handle multi-tag requirements (e.g., "meat+poultry")
    required_tags = tag.split("+")
    
    for coord, items in stockpiles.items():
        for item in items:
            item_def = get_item_def(item["id"])
            if item_def and all(t in item_def.tags for t in required_tags):
                matches.append((coord, item))
                if len(matches) >= count:
                    return matches
    
    return matches
```

---

## Stockpile Filter System

### Filter Categories (Granular)
```python
"allow_raw_food": True,      # Raw meat, produce
"allow_cooked_food": True,   # Prepared meals
"allow_materials": True,     # Pelts, feathers, leather
"allow_corpses": True,       # Unprocessed animal bodies
"allow_equipment": True,     # Armor, tools, weapons
"allow_components": True,    # Electronics, parts
"allow_furniture": True,     # Placeable items
```

### Hauling Logic (Tag Priority)
```python
def determine_storage_type(item_def):
    """Determine stockpile filter based on item tags."""
    tags = item_def.tags
    
    # Priority order (check most specific first)
    if "corpse" in tags:
        return "corpses"
    elif "food" in tags:
        if "raw" in tags:
            return "raw_food"
        elif "cooked" in tags or "meal" in tags:
            return "cooked_food"
    elif "material" in tags:
        return "materials"
    elif "component" in tags or "electronics" in tags:
        return "components"
    elif "furniture" in tags:
        return "furniture"
    else:
        return "equipment"  # Default catch-all
```

---

## UI Display

### Crafting Station UI
When colonist starts "Meat Stew" recipe:
```
┌─────────────────────────────────────┐
│ Crafting: Meat Stew                 │
├─────────────────────────────────────┤
│ Ingredients:                        │
│  • 2x Rat Meat (rodent, low)       │
│  • 4x Pigeon Meat (poultry, medium)│
│  • 2x Wild Carrot (vegetable)      │
├─────────────────────────────────────┤
│ Output: 1x Meat Stew (medium)      │
│ Quality: Medium (avg of inputs)    │
└─────────────────────────────────────┘
```

### Stockpile Filter UI (Future)
```
┌─────────────────────────────────────┐
│ Stockpile Filters                   │
├─────────────────────────────────────┤
│ ☑ Raw Food                          │
│ ☑ Cooked Food                       │
│ ☑ Materials (pelts, leather)       │
│ ☐ Corpses                           │
│ ☑ Equipment                         │
│ ☐ Components                        │
│ ☐ Furniture                         │
└─────────────────────────────────────┘
```

---

## Example: 30 Animal Types

### Rodents
- **Rat**: low quality, common, fast breeding
- **Mouse**: very low quality, tiny portions
- **Squirrel**: medium quality, seasonal

### Poultry
- **Pigeon**: medium quality, common
- **Crow**: low quality, tough meat
- **Seagull**: medium quality, fishy taste

### Feral
- **Cat**: high quality, controversial (mood penalty)
- **Dog**: high quality, controversial (mood penalty)
- **Raccoon**: medium quality, fights back

### Mutant (Echo-affected)
- **Mutant Rat**: medium quality, Echo materials
- **Mutant Pigeon**: high quality, glows
- **Echo Beast**: very high quality, dangerous

**Each has:**
- Unique meat item with specific tags
- Unique materials (pelts, feathers, scales)
- Different quality/nutrition values
- Specific recipes OR generic "meat" recipes

---

## Recipe Examples

### Generic Recipes (Any Meat)
```python
{
    "id": "meat_stew",
    "name": "Meat Stew",
    "input_items": {"meat": 6},  # Any combination
    "output_item": "meat_stew"
}
```

### Family-Specific Recipes
```python
{
    "id": "poultry_roast",
    "name": "Poultry Roast",
    "input_items": {"meat+poultry": 4},  # Only poultry
    "output_item": "poultry_roast"
}
```

### Exact Recipes
```python
{
    "id": "pigeon_wing_special",
    "name": "Pigeon Wing Special",
    "input_items": {"pigeon_meat": 2},  # Must be pigeon
    "output_item": "pigeon_wing_special"
}
```

### Mixed Recipes
```python
{
    "id": "surf_and_turf",
    "name": "Surf & Turf",
    "input_items": {
        "meat+rodent": 2,    # Rodent meat
        "meat+poultry": 2    # Poultry meat
    },
    "output_item": "surf_and_turf"
}
```

---

## Benefits

✅ **Scalable**: Add new animals by just adding items with tags
✅ **Flexible**: Recipes can be generic or specific
✅ **Transparent**: UI shows exact items used
✅ **Consistent**: Same system for all items
✅ **Modular**: Tags can combine in any way
✅ **Future-proof**: Easy to add new tags (organic, preserved, frozen, etc.)

---

## Migration Path

1. **Phase 1**: Add tags to existing items (rat_meat, bird_meat, pelts)
2. **Phase 2**: Update hauling logic to use tag priority
3. **Phase 3**: Add tag-based recipe matching
4. **Phase 4**: Update stove recipes to use input_items
5. **Phase 5**: Add stockpile filter UI
6. **Phase 6**: Add quality/nutrition system
7. **Phase 7**: Expand to 30+ animals

Each phase is independent and can be tested separately.
