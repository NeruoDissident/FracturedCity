# Fractured City - Development Session Notes

**Last Updated:** Jan 1, 2026

---

## ✅ COMPLETED: Material System Foundation

**Status:** IMPLEMENTED (Jan 1, 2026)

### What Was Implemented:

**1. Extended ItemDef Structure (`items.py`)**
Added 8 new fields for material categorization:
- `size_class` - "tiny", "small", "medium", "large", "huge"
- `material_type` - "meat", "hide", "bone", "feather", "fat", "organ", etc.
- `processing_state` - "raw", "cleaned", "tanned", "cooked", "preserved"
- `quality` - 0-5 scale (terrible → excellent)
- `spoilage_rate` - How fast items rot (0=never, 1.0=1 day)
- `stack_size` - Inventory stacking
- `weight` / `volume` - For future hauling/storage

**2. Updated All Organic Items**
Categorized existing items with proper metadata:
- **Corpses:** `rat_corpse`, `bird_corpse` (spoil in 1 day)
- **Meat:** `rat_meat` (quality=1), `bird_meat` (quality=2) - spoil in 2 days
- **Materials:** `rat_pelt` (hide, quality=1), `feathers` (quality=2, never spoil)

**3. Flavor Text System**
Created `get_item_display_name()` that generates:
- `"Poor Rat Meat (Rat) - 12h old"`
- `"Bird Meat (Bird) - just harvested"`
- `"Excellent Bird Meat (Bird) - 2d old"`

**4. Butchery Metadata (`colonist.py`)**
When items are crafted from corpses, they now get:
- `source_species` - "rat" or "bird"
- `harvest_tick` - When butchered
- `harvested_by` - Colonist UID

**5. UI Integration (`ui_arcade_tile_info.py`, `main_arcade.py`)**
Tile info tooltips now show full item metadata:
- Source species in parentheses
- Age ("just harvested", "12h old", "2d old")
- Quality descriptor for notable items

**6. Fixed Stove Recipes (`buildings.py`)**
Corrected power requirements (were all 1, now scale with complexity):
- Simple Meal: 1 power
- Fine Meal: 2 power
- Meat Stew: 3 power
- Poultry Roast: 2 power
- Rodent Skewers: 2 power

### Files Modified:
- `items.py`: Extended ItemDef, updated organic items, added flavor text helpers
- `colonist.py`: Added metadata when spawning butchered items
- `buildings.py`: Fixed stove recipe power costs
- `ui_arcade_tile_info.py`: Display item metadata in tooltips
- `main_arcade.py`: Pass game_tick to tile info panel

### Test Files Created:
- `test_item_metadata.py`: Validates code structure (all tests passed ✓)
- `ITEM_AUDIT.md`: Full breakdown of all 60+ items and their purposes

---

## ✅ COMPLETED: Hunting System Implementation

**Status:** IMPLEMENTED & WORKING

### Features Added:
- Hunt job type for colonists to track and kill urban animals
- Animal entities with health, movement, and AI
- Corpse spawning system when animals are killed
- Butchering at Bio-Matter Salvage Station

### Urban Animals Available:
- **Rats**: Common, easy to hunt, low quality meat
- **Pigeons**: Common, medium difficulty, decent meat + feathers
- **Raccoons**: Uncommon, hard, quality meat (fights back)
- **Feral Cats**: Rare, hard, fast moving
- **Mutant Squirrels**: Uncommon, Echo-tainted

### How It Works:
1. Colonist creates hunt job targeting animal
2. Colonist chases animal (animals flee/move around)
3. When in range (1 tile), colonist attacks
4. Animal takes damage, dies when health <= 0
5. Corpse spawns as world item at death location
6. Corpse hauled to stockpile by auto-haul system
7. Butchered at Bio-Matter Salvage Station for meat/materials

### Files Involved:
- `animals.py`: Animal entities, movement, spawning
- `colonist.py`: Hunt job execution, chase/attack logic
- `items.py`: Corpse items, butchering recipes
- `buildings.py`: Bio-Matter Salvage Station with butchering recipes

---

## 📋 NEXT STEPS: Material Processing Expansion

**Priority:** Fix dead-end items (pelts/feathers need uses)

### Existing Workstations:
- **Salvagers Bench**: Basic salvaging/crafting
- **Tinker Station**: Advanced crafting
- **Spark Bench**: Electronics/tech
- **Generator**: Power production (2x2) ✓ Working
- **Stove**: Cooking (2x1) ⚠️ NEEDS FIX
- **Gutter Forge**: Metalworking (3x3) ✓ Working
- **Gutter Still**: Brewing/distilling (3x3) ✓ Working
- **Skinshop Loom**: Textiles/clothing
- **Cortex Spindle**: Implants/charms
- **Bio-Matter Salvage Station**: Butchering (2x1) ⚠️ NEEDS FIX
- **Barracks**: Military equipment

### Development Priorities:
1. **Fix multi-tile rendering** for stove and bio-matter station
2. **Expand recipes** for existing workstations
3. **Add progression** - early/mid/late game recipes
4. **Balance materials** - ensure resource flow makes sense
5. **Add specialized stations** as needed for new systems

### Recipe Categories to Expand:
- **Food preparation**: Cooking, preserving, meal combinations
- **Equipment crafting**: Tools, weapons, armor
- **Building materials**: Refined metals, composites, advanced materials
- **Medical/chemical**: Medicine, drugs, chemicals, stimulants
- **Electronics**: Components, devices, implants, tech
- **Textiles**: Clothing, bags, bedding, protective gear

### Design Philosophy:
- **Urban survival theme** - scavenged/improvised materials
- **Multi-step crafting chains** for advanced items
- **Workstation specialization** - not everything at one bench
- **Resource scarcity** drives player decisions
- **Progression gating** - unlock better recipes with better stations

---

## 🔧 Technical Notes

### Multi-Tile Rendering System:
- 2x1 horizontal structures use suffixes: `""` (left/origin), `"_right"` (right)
- 2x2 structures use: `_sw`, `_se`, `_nw`, `_ne`
- 3x3 structures use: `_sw`, `_s`, `_se`, `_w`, `_center`, `_e`, `_nw`, `_n`, `_ne`
- Construction tiles are darkened (RGB 153,153,153)
- All tiles in footprint must be updated when construction completes

### Sprite File Naming Convention:
- Construction: `{station_name}.png`, `{station_name}_right.png`
- Finished: `finished_{station_name}.png`, `finished_{station_name}_right.png`
- Use underscores in file names, not hyphens

### Key Functions:
- `_render_multi_tile_structure()`: Renders all tiles of a multi-tile structure
- `_get_multi_tile_suffix()`: Returns correct suffix based on position
- `_get_multi_tile_texture()`: Loads texture with suffix
- `add_to_cache()`: Should skip multi-tile structures (they're handled separately)

---

## 📝 Session History

### Dec 31, 2025:
- Implemented hunting system with urban animals
- Added Bio-Matter Salvage Station for butchering
- Fixed multi-tile rendering duplicate sprite bug
- Renamed sprite files to match code expectations
- Updated construction completion logic
- **Issue remains**: Right tile not rendering for 2x1 stations

---

*This file is for tracking development progress across sessions. Update as needed.*
