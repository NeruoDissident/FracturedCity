# Documentation Audit - January 10, 2026

## OBSOLETE - DELETE (17 files)

### Completed Tasks / One-Time Operations
- `RESCALE_SUMMARY.md` - Completed sprite rescaling task
- `PRESSURE_REMOVAL_SUMMARY.md` - Completed feature removal
- `TESTING_WALL_AUTOTILES.md` - Testing notes, not needed
- `SPRITE_VISUAL_VERIFICATION.md` - One-time verification
- `SPRITE_RENAME_GUIDE.md` - One-time renaming task
- `DIRT_INNER_CORNERS_13-16.md` - Specific bug fix, resolved
- `DIRT_INNER_CORNERS_FIX.md` - Specific bug fix, resolved

### Session Notes (Outdated)
- `SESSION_NOTES.md` - Old session notes
- `SESSION_NOTES_DEC18.md` - Old session notes from Dec 18

### Outdated Plans
- `IMPLEMENTATION_PLAN.md` - Outdated implementation plan
- `PHASE1_SPRITES_NEEDED.md` - Completed sprite phase

### Extraction Scripts (One-Time)
- `ROAD_TILE_MAPPING.md` - Road extraction mapping (completed)
- `SPRITE_MAPPING_ANALYSIS.md` - Analysis doc for extraction

### Redundant/Superseded
- `SPRITES_NEEDED.md` - Superseded by other sprite docs
- `MISSING_SPRITES_LIST.md` - Outdated missing sprite list
- `CONSTRUCTION_SPRITES_CURRENT.md` - Current state doc (outdated)
- `STAT_AUDIT.md` - Old stat audit

## CONSOLIDATE - Sprite Documentation (16 files → 2 files)

### Target: SPRITE_SYSTEM.md
Merge these sprite reference docs:
- `SPRITE_GUIDE.md`
- `SPRITE_MASTER_LIST.md`
- `SPRITE_NAMING_SYSTEM.md`
- `SPRITE_PATH_REFERENCE.md`
- `COLONIST_SPRITE_GUIDE.md`
- `MULTI_TILE_SPRITE_GUIDE.md`
- `MULTI_TILE_STRUCTURES.md`
- `ADDITIVE_SPRITE_GUIDE.md`

### Target: AUTOTILE_GUIDE.md
Merge these autotiling docs:
- `AUTOTILE_SPRITE_SPEC.md`
- `BLOB_AUTOTILE_47_SPEC.md`
- `DIRT_AUTOTILE_SPEC.md`
- `WALL_AUTOTILE_IMPLEMENTATION.md`
- `WALL_FLOOR_AUTOTILE_DESIGN.md`

## CONSOLIDATE - System Documentation (11 files → 4 files)

### Target: RENDERING_SYSTEM.md
- `ARCADE_RENDERING_PATTERNS.md`
- `LAYERED_RENDERING_SYSTEM.md`
- `LAYER_SYSTEM.md`

### Target: HUNTING_SYSTEM.md
- `HUNTING_ANIMAL_SYSTEM_DESIGN.md`
- `HUNTING_IMPLEMENTATION.md`
- `ANIMAL_SYSTEM_INTEGRATION.md`

### Target: ITEM_SYSTEM.md
- `ITEM_AUDIT.md`
- `ITEM_TAGGING_SYSTEM_DESIGN.md`
- `TAGGING_SYSTEM_IMPLEMENTATION_SUMMARY.md`

### Target: STOCKPILE_SYSTEM.md
- `STOCKPILE_SYSTEM_AUDIT.md` (keep as-is, just rename)

## KEEP & UPDATE (7 files)

### Keep As-Is (Accurate)
- `EQUIPMENT_SYSTEM_NOTES.md` - Accurate system documentation
- `SURVIVAL_SYSTEMS_DESIGN.md` - Good design reference
- `ROOM_TYPES_GUIDE.md` - Useful reference
- `CRAFTING_UNIFICATION_PLAN.md` - Forward-looking plan
- `CITY_GENERATOR_GUIDE.md` - Current worldgen system
- `UI_COLONIST_AUDIT.md` - Current UI state

### Update for Arcade
- `README.md` - Remove Pygame references, update for Arcade

## CREATE NEW (4 files)

- `CURRENT_STATE.md` - What works RIGHT NOW (Jan 2026)
- `ROADMAP.md` - Next 6 months to Godot port
- `ARCHITECTURE.md` - Codebase organization (Arcade rendering, systems)
- `COMPLETION_CHECKLIST.md` - Status of architecture review items

## Summary

- **Delete**: 17 obsolete files
- **Consolidate**: 27 files → 6 consolidated docs
- **Keep**: 7 files (1 needs update)
- **Create**: 4 new master docs
- **Final Count**: ~17 clean, organized documentation files (down from 51)
