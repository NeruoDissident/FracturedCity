# Fractured City - Development Session Notes

**Last Updated:** Dec 31, 2025

---

## 🐛 CURRENT BUG: Multi-Tile Workstation Rendering

**Status:** IN PROGRESS

### Problem:
2x1 horizontal workstations (stove, bio-matter salvage station) are not rendering correctly:
- **Stove**: Only showing left tile
- **Bio-Matter Station**: Random/inconsistent rendering
- Should render exactly 2 tiles each

### Root Cause Found:
`add_to_cache()` in `grid_arcade.py` was creating sprites for every tile in multi-tile footprints, then `_add_structure_sprite()` was ALSO rendering the full structure. This caused duplicate sprites.

### Fixes Applied:
1. Modified `add_to_cache()` (line 327-332) to skip multi-tile structures
2. Renamed sprite files to match code expectations:
   - Changed `_e` suffix → `_right` suffix for 2x1 structures
   - Changed `bio-matter_salvage_station` (hyphens) → `bio_matter_salvage_station` (underscores)
3. Updated construction completion in `colonist.py` to set ALL footprint tiles to finished state

### Current Issue:
After applying fixes, stove only shows left tile, bio-matter station still renders randomly. Right tile not appearing.

### Files Modified:
- `grid_arcade.py`: Added multi-tile skip in add_to_cache, added debug logging
- `colonist.py`: Updated stove and bio-matter completion to set all footprint tiles
- Sprite files in `assets/workstations/`: Renamed to use `_right` suffix

### Next Steps for Debugging:
1. Verify sprite files exist and are named correctly:
   - `stove.png` and `stove_right.png`
   - `bio_matter_salvage_station.png` and `bio_matter_salvage_station_right.png`
   - `finished_stove.png` and `finished_stove_right.png`
   - `finished_bio_matter_salvage_station.png` and `finished_bio_matter_salvage_station_right.png`
2. Check `_get_multi_tile_texture()` is finding the files
3. Review debug logs to see what's happening during rendering
4. Test both stations render correctly (2 tiles each)
5. Remove debug logging once fixed

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

## 📋 NEXT STEPS: Workstation & Recipe Development

**Priority:** After fixing rendering bug, continue expanding crafting system

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
