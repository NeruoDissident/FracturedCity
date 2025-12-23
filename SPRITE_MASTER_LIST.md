# SPRITE MASTER LIST - Complete Guide

## ✅ COMPLETED (You Already Have These)
- `default_north.png` - Colonist facing away
- `default_east.png` - Colonist facing right  
- `default_west.png` - Colonist facing left
- `finished_floor_0.png` through `finished_floor_5.png` - Floor variations (6 total)
- `finished_wall_0.png` through `finished_wall_3.png` - Wall variations (4 total)

---

## 🎯 PRIORITY SPRITES (Most Visible)

### Ground/Terrain Tiles
**Naming:** `tilename_#.png` (# = variation 0-7)

- `empty_0.png` to `empty_7.png` - Dark earth/void (8 variations)
- `dirt_0.png` to `dirt_3.png` - Brown dirt (4 variations)
- `grass_0.png` to `grass_3.png` - Dark grass (4 variations)
- `rock_0.png` to `rock_3.png` - Stone/rock (4 variations)
- `scorched_0.png` to `scorched_3.png` - Burnt ground (4 variations)

### Streets & Sidewalks
- `street_0.png` to `street_3.png` - Intact pavement (4 variations)
- `street_cracked_0.png` to `street_3.png` - Cracked pavement (4 variations)
- `street_scar_0.png` to `street_3.png` - Heavily damaged road (4 variations)
- `street_ripped_0.png` to `street_3.png` - Destroyed pavement (4 variations)
- `sidewalk_0.png` to `sidewalk_3.png` - Sidewalk tiles (4 variations)

### Decorative/Ruins
- `debris_0.png` to `debris_7.png` - Rubble piles (8 variations)
- `weeds_0.png` to `weeds_3.png` - Overgrown vegetation (4 variations)
- `prop_barrel_0.png` to `prop_3.png` - Barrel props (4 variations)
- `prop_sign_0.png` to `prop_3.png` - Sign props (4 variations)
- `prop_scrap_0.png` to `prop_3.png` - Scrap piles (4 variations)

---

## 🏗️ BUILDINGS & CONSTRUCTION

### Walls
- `wall_0.png` to `wall_1.png` - Wall under construction (2 variations)
- `finished_wall_advanced_0.png` to `finished_wall_advanced_3.png` - Advanced walls (4 variations)

### Floors (Additional)
- `floor_0.png` to `floor_3.png` - Floor under construction (4 variations)
- `roof_floor.png` - Rooftop floor
- `roof_access.png` - Accessible roof tile

### Doors & Windows
- `door.png` - Door under construction
- `finished_door.png` - Completed door
- `bar_door.png` - Saloon-style door
- `window.png` - Window under construction
- `finished_window.png` - Completed window

### Special Building Tiles
- `building.png` - Generic building under construction
- `finished_building.png` - Generic completed building
- `bridge.png` - Bridge under construction
- `finished_bridge.png` - Completed bridge
- `fire_escape.png` - Fire escape under construction
- `finished_fire_escape.png` - Completed fire escape

---

## ⚙️ WORKSTATIONS (Finished)

**Naming:** `finished_stationname.png` (single sprite, no variations)

- `finished_spark_bench.png` - Electronics workbench
- `finished_tinker_station.png` - General crafting bench
- `finished_generator.png` - Power generator
- `finished_gutter_forge.png` - Metal forge
- `finished_salvagers_bench.png` - Salvage workstation
- `finished_stove.png` - Kitchen stove
- `finished_gutter_still.png` - Distillery/brewery
- `finished_skinshop_loom.png` - Textile loom
- `finished_cortex_spindle.png` - Neural/tech workstation
- `finished_barracks.png` - Military/training station

---

## 🎸 FURNITURE & ITEMS (Placed)

**Naming:** `itemname_placed.png` or just `itemname.png`

### Instruments
- `scrap_guitar_placed.png` - Guitar on floor/stand
- `drum_kit_placed.png` - Drum set
- `synth_placed.png` - Synthesizer
- `harmonica_placed.png` - Harmonica
- `amp_placed.png` - Amplifier

### Furniture
- `crash_bed.png` - Bed
- `comfort_chair.png` - Chair
- `bar_stool.png` - Bar stool
- `scrap_bar_counter.png` - Bar counter

### Recreation
- `finished_stage.png` - Performance stage
- `finished_stage_stairs.png` - Stage stairs

---

## 📦 RESOURCE NODES (Optional - Currently Procedural)

**Naming:** `nodetype_node.png` or `nodetype_node_depleted.png`

- `wood_node.png` - Tree/lumber pile
- `wood_node_depleted.png` - Harvested wood
- `scrap_node.png` - Scrap metal pile
- `scrap_node_depleted.png` - Picked-over scrap
- `mineral_node.png` - Rock/ore deposit
- `mineral_node_depleted.png` - Mined out deposit

---

## 🎨 SPRITE SPECIFICATIONS

### Size Requirements
- **Any resolution works!** System auto-scales
- Recommended: 512x512, 1024x1024, or 2048x2048 for crisp detail
- Can be non-square - system preserves aspect ratio

### File Format
- **PNG with transparency** (for layering)
- Transparent backgrounds allow items to sit on floors
- Opaque backgrounds for ground tiles

### Variations
- Numbered 0-7 (or 0-3 depending on tile type)
- System picks variation based on tile position
- Creates organic, non-repetitive look

### Naming Convention
```
tiletype_#.png        → Tiles with variations (empty_0.png, empty_1.png, etc.)
finished_name.png     → Completed buildings/workstations (finished_wall.png)
itemname_placed.png   → Placed furniture/items (scrap_guitar_placed.png)
```
a
---

## 📊 PRIORITY ORDER (Recommended)

1. **Ground tiles** (empty, dirt, grass) - Most common, biggest visual impact
2. **Streets** (street, sidewalk) - Define city layout
3. **Workstations** (spark_bench, tinker_station, etc.) - Gameplay critical
4. **Decorative** (debris, weeds, props) - Atmosphere
5. **Furniture** (instruments, beds, chairs) - Gameplay features
6. **Resource nodes** (wood, scrap, mineral) - Optional, procedural works fine

---

## 🚀 QUICK START

1. Create sprite at any resolution (square or not)
2. Save as PNG with transparency if needed
3. Name according to convention above
4. Drop in `assets/` folder (or `assets/tiles/`, `assets/buildings/`, etc.)
5. Run game - sprite loads automatically!
6. Missing sprites fall back to procedural drawing

---

## 💡 TIPS

- **Start with 1-2 variations** per tile type, add more later
- **Transparent PNGs** let items layer on floors
- **Non-square sprites** work fine - aspect ratio preserved
- **Canvas size doesn't matter** - system scales everything
- **Test as you go** - drop sprites in and see them immediately
- **Mix sprite + procedural** - only sprite what you want, rest uses fallback

---

**Total Sprites Possible:** ~200+
**Already Complete:** 13 (colonists + floors + walls)
**High Priority Remaining:** ~50-60 (ground, streets, workstations)

You can create as many or as few as you want - the system handles both gracefully!
