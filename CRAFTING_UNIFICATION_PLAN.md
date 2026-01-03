# Crafting System Unification Plan

**Goal:** Unify all workstation crafting to use the same pattern. Clean, simple, single source of truth.

---

## Current Problem

Workstations have **inconsistent input/output patterns**:

### Pattern 1: Resource Inputs Only
```python
# Generator, Salvagers Bench
"input": {"wood": 3},
"output": {"power": 1}
```

### Pattern 2: Item Inputs Only
```python
# Bio-Matter Salvage Station (butchery)
"input": {"rat_corpse": 1},
"output": {"rat_meat": 2, "rat_pelt": 1}
```

### Pattern 3: Mixed Inputs (BROKEN)
```python
# Stove - has BOTH but only resources are fetched/consumed
"input_items": {"meat": 1},  # ← NOT being fetched
"input": {"power": 1},        # ← Only this works
"output": {"cooked_meal": 1}
```

### Pattern 4: Item Outputs
```python
# Gutter Forge, Skinshop Loom
"input": {"metal": 2, "scrap": 1},
"output_item": "salvage_tool"  # Spawns as world item
```

---

## Unified Pattern (Target)

**All recipes should use this structure:**

```python
{
    "id": "recipe_id",
    "name": "Recipe Name",
    
    # INPUTS (what gets consumed)
    "input": {
        # Resources (wood, metal, scrap, power, etc.)
        "power": 1,
        "wood": 2,
    },
    "input_items": {
        # Items by tag (meat, corpse, hide, etc.)
        "meat": 2,
        "hide": 1,
    },
    
    # OUTPUTS (what gets produced)
    "output": {
        # Resources (if producing resources)
        "cooked_meal": 1,
    },
    "output_items": [
        # Items (if producing items)
        {"id": "rat_meat", "count": 2},
        {"id": "rat_pelt", "count": 1},
    ],
    
    "work_time": 60,
}
```

---

## Implementation Steps

### 1. Update Recipe Definitions (`buildings.py`)
- Convert all recipes to unified format
- Use `input` for resources, `input_items` for items
- Use `output` for resources, `output_items` for items

### 2. Fix Fetching Logic (`colonist.py`)
Currently only fetches resources. Need to:
- Fetch resources from resource stockpiles
- Fetch items from equipment stockpiles (by tag)
- Deliver both to workstation

### 3. Fix Consumption Logic (`buildings.py`)
Already partially fixed, but needs:
- Consume from `ws["input_items"]` (resources)
- Consume from `ws["equipment_items"]` (items)

### 4. Fix Output Logic (`colonist.py`)
- Spawn resources using `create_resource_item()`
- Spawn items using `spawn_world_item()` with metadata

---

## Workstations to Update

### Resource → Resource
- **Generator**: wood/scrap → power ✓ (already works)
- **Salvagers Bench**: scrap → metal ✓ (already works)

### Item → Items
- **Bio-Matter Salvage Station**: corpse → meat + materials
  - Currently uses `"output": {"rat_meat": 2}` (resource pattern)
  - Should use `"output_items": [{"id": "rat_meat", "count": 2}]`

### Mixed → Resource
- **Stove**: meat + power → cooked_meal
  - Currently broken (only consumes power)
  - Need to fetch meat from equipment stockpiles

### Resource → Item
- **Gutter Forge**: metal + scrap → tools/weapons ✓ (already works)
- **Skinshop Loom**: scrap + wood → furniture ✓ (already works)
- **Spark Bench**: metal + mineral → components ✓ (already works)

---

## Testing Checklist

After unification, test each workstation:

1. **Generator**: Wood → Power ✓
2. **Salvagers Bench**: Scrap → Metal ✓
3. **Bio-Matter Station**: Rat corpse → Rat meat + Rat pelt
4. **Stove**: Meat + Power → Cooked meal
5. **Gutter Forge**: Metal + Scrap → Salvage tool
6. **Skinshop Loom**: Scrap + Wood → Crash bed
7. **Spark Bench**: Scrap + Mineral → Wire

---

## Code Cleanup Targets

### Remove Old Pygame Code
- Search for `pygame` imports (except audio)
- Remove unused UI code
- Consolidate to Arcade-only

### Consolidate Item Systems
- `items.py` - Item definitions ✓
- `resources.py` - Resource items (wood, scrap)
- **Merge?** Consider if resources should just be items with `material_type="resource"`

### Single Source of Truth
- All recipes in `buildings.py` ✓
- All item defs in `items.py` ✓
- All animal data in `animals.py` ✓
- No duplicate definitions

---

## Benefits After Unification

1. **Predictable**: All workstations work the same way
2. **Extensible**: Easy to add new recipes
3. **Debuggable**: One place to look for issues
4. **Godot-ready**: Clean patterns for porting
5. **Maintainable**: No special cases or edge cases

---

**Next Session:** After testing material system, do full crafting unification pass.
