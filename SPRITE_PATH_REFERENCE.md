# COMPLETE SPRITE PATH REFERENCE

**Every crafting station, placeable object, and sprite path the game looks for.**

---

## 🏗️ BUILDINGS & STRUCTURES

### Single-Tile Buildings:

| Building | Tile Type | Construction Sprite | Finished Sprite |
|----------|-----------|---------------------|-----------------|
| Wall | `wall` | `assets/tiles/wall.png` | `assets/tiles/finished_wall.png` |
| Reinforced Wall | `wall_advanced` | `assets/tiles/wall_advanced.png` | `assets/tiles/finished_wall_advanced.png` |
| Door | `door` | `assets/tiles/door.png` | `assets/tiles/finished_door.png` |
| Bar Door | `bar_door` | `assets/tiles/bar_door.png` | `assets/tiles/finished_bar_door.png` |
| Floor | `floor` | `assets/tiles/floor.png` | `assets/tiles/finished_floor.png` |
| Window | `window` | `assets/tiles/window.png` | `assets/tiles/finished_window.png` |
| Bridge | `bridge` | `assets/tiles/bridge.png` | `assets/tiles/finished_bridge.png` |
| Fire Escape | `fire_escape` | `assets/tiles/fire_escape.png` | `assets/tiles/finished_fire_escape.png` |
| Stage | `stage` | `assets/tiles/stage.png` | `assets/tiles/finished_stage.png` |
| Stage Stairs | `stage_stairs` | `assets/tiles/stage_stairs.png` | `assets/tiles/finished_stage_stairs.png` |
| Bar Counter | `scrap_bar_counter` | `assets/tiles/scrap_bar_counter.png` | `assets/tiles/finished_scrap_bar_counter.png` |

---

## 🔧 WORKSTATIONS (1x1 Single-Tile)

| Workstation | Tile Type | Construction Sprite | Finished Sprite |
|-------------|-----------|---------------------|-----------------|
| Salvager's Bench | `salvagers_bench` | `assets/workstations/salvagers_bench.png` | `assets/workstations/finished_salvagers_bench.png` |
| Spark Bench | `spark_bench` | `assets/workstations/spark_bench.png` | `assets/workstations/finished_spark_bench.png` |
| Tinker Station | `tinker_station` | `assets/workstations/tinker_station.png` | `assets/workstations/finished_tinker_station.png` |
| Skinshop Loom | `skinshop_loom` | `assets/workstations/skinshop_loom.png` | `assets/workstations/finished_skinshop_loom.png` |
| Cortex Spindle | `cortex_spindle` | `assets/workstations/cortex_spindle.png` | `assets/workstations/finished_cortex_spindle.png` |
| Barracks | `barracks` | `assets/workstations/barracks.png` | `assets/workstations/finished_barracks.png` |

---

## 🏭 MULTI-TILE WORKSTATIONS

### 2x1 Stove (Horizontal)

**Tile Type:** `stove`  
**Size:** 2 tiles wide, 1 tile tall

| Position | Suffix | Construction Sprite | Finished Sprite |
|----------|--------|---------------------|-----------------|
| Left (origin) | _(none)_ | `assets/workstations/stove.png` | `assets/workstations/finished_stove.png` |
| Right | `_e` | `assets/workstations/stove_e.png` | `assets/workstations/finished_stove_e.png` |

---

### 2x2 Generator

**Tile Type:** `generator`  
**Size:** 2 tiles wide, 2 tiles tall

| Position | Suffix | Construction Sprite | Finished Sprite |
|----------|--------|---------------------|-----------------|
| Bottom-Left (origin) | `_sw` | `assets/workstations/generator_sw.png` | `assets/workstations/finished_generator_sw.png` |
| Bottom-Right | `_se` | `assets/workstations/generator_se.png` | `assets/workstations/finished_generator_se.png` |
| Top-Left | `_nw` | `assets/workstations/generator_nw.png` | `assets/workstations/finished_generator_nw.png` |
| Top-Right | `_ne` | `assets/workstations/generator_ne.png` | `assets/workstations/finished_generator_ne.png` |

---

### 3x3 Gutter Forge

**Tile Type:** `gutter_forge`  
**Size:** 3 tiles wide, 3 tiles tall

| Position | Suffix | Construction Sprite | Finished Sprite |
|----------|--------|---------------------|-----------------|
| Bottom-Left (origin) | `_sw` | `assets/workstations/gutter_forge_sw.png` | `assets/workstations/finished_gutter_forge_sw.png` |
| Bottom-Center | `_s` | `assets/workstations/gutter_forge_s.png` | `assets/workstations/finished_gutter_forge_s.png` |
| Bottom-Right | `_se` | `assets/workstations/gutter_forge_se.png` | `assets/workstations/finished_gutter_forge_se.png` |
| Middle-Left | `_w` | `assets/workstations/gutter_forge_w.png` | `assets/workstations/finished_gutter_forge_w.png` |
| Middle-Center | `_center` | `assets/workstations/gutter_forge_center.png` | `assets/workstations/finished_gutter_forge_center.png` |
| Middle-Right | `_e` | `assets/workstations/gutter_forge_e.png` | `assets/workstations/finished_gutter_forge_e.png` |
| Top-Left | `_nw` | `assets/workstations/gutter_forge_nw.png` | `assets/workstations/finished_gutter_forge_nw.png` |
| Top-Center | `_n` | `assets/workstations/gutter_forge_n.png` | `assets/workstations/finished_gutter_forge_n.png` |
| Top-Right | `_ne` | `assets/workstations/gutter_forge_ne.png` | `assets/workstations/finished_gutter_forge_ne.png` |

---

### 3x3 Gutter Still (Brewing Station)

**Tile Type:** `gutter_still`  
**Size:** 3 tiles wide, 3 tiles tall

| Position | Suffix | Construction Sprite | Finished Sprite |
|----------|--------|---------------------|-----------------|
| Bottom-Left (origin) | `_sw` | `assets/workstations/gutter_still_sw.png` | `assets/workstations/finished_gutter_still_sw.png` |
| Bottom-Center | `_s` | `assets/workstations/gutter_still_s.png` | `assets/workstations/finished_gutter_still_s.png` |
| Bottom-Right | `_se` | `assets/workstations/gutter_still_se.png` | `assets/workstations/finished_gutter_still_se.png` |
| Middle-Left | `_w` | `assets/workstations/gutter_still_w.png` | `assets/workstations/finished_gutter_still_w.png` |
| Middle-Center | `_center` | `assets/workstations/gutter_still_center.png` | `assets/workstations/finished_gutter_still_center.png` |
| Middle-Right | `_e` | `assets/workstations/gutter_still_e.png` | `assets/workstations/finished_gutter_still_e.png` |
| Top-Left | `_nw` | `assets/workstations/gutter_still_nw.png` | `assets/workstations/finished_gutter_still_nw.png` |
| Top-Center | `_n` | `assets/workstations/gutter_still_n.png` | `assets/workstations/finished_gutter_still_n.png` |
| Top-Right | `_ne` | `assets/workstations/gutter_still_ne.png` | `assets/workstations/finished_gutter_still_ne.png` |

---

## 🪑 FURNITURE (Placeable Objects)

### Single-Tile Furniture (1x1):

| Furniture | Item ID | Tile Type | Sprite Path |
|-----------|---------|-----------|-------------|
| Comfort Chair | `comfort_chair` | `comfort_chair` | `assets/furniture/comfort_chair.png` |
| Bar Stool | `bar_stool` | `bar_stool` | `assets/furniture/bar_stool.png` |
| Storage Locker | `storage_locker` | `storage_locker` | `assets/furniture/storage_locker.png` |
| Scrap Guitar (placed) | `scrap_guitar` | `scrap_guitar_placed` | `assets/furniture/scrap_guitar_placed.png` |
| Drum Kit (placed) | `drum_kit` | `drum_kit_placed` | `assets/furniture/drum_kit_placed.png` |
| Synth (placed) | `synth` | `synth_placed` | `assets/furniture/synth_placed.png` |
| Harmonica (placed) | `harmonica` | `harmonica_placed` | `assets/furniture/harmonica_placed.png` |
| Amp (placed) | `amp` | `amp_placed` | `assets/furniture/amp_placed.png` |

### Multi-Tile Furniture:

#### 1x2 Crash Bed (Vertical)

**Item ID:** `crash_bed`  
**Tile Type:** `crash_bed`  
**Size:** 1 tile wide, 2 tiles tall

| Position | Suffix | Sprite Path |
|----------|--------|-------------|
| Bottom (origin) | _(none)_ | `assets/furniture/crash_bed.png` |
| Top | `_top` | `assets/furniture/crash_bed_top.png` |

---

## 📁 DIRECTORY STRUCTURE SUMMARY

```
assets/
├── tiles/
│   ├── wall.png, finished_wall.png
│   ├── wall_advanced.png, finished_wall_advanced.png
│   ├── door.png, finished_door.png
│   ├── bar_door.png, finished_bar_door.png
│   ├── floor.png, finished_floor.png
│   ├── window.png, finished_window.png
│   ├── bridge.png, finished_bridge.png
│   ├── fire_escape.png, finished_fire_escape.png
│   ├── stage.png, finished_stage.png
│   ├── stage_stairs.png, finished_stage_stairs.png
│   ├── scrap_bar_counter.png, finished_scrap_bar_counter.png
│   ├── walls/
│   │   └── finished_wall_autotile_0.png through _46.png (autotiling)
│   ├── roads/
│   │   └── street_autotile_0.png through _46.png (autotiling)
│   └── dirt/
│       └── ground_dirt_overlay_autotile_0.png through _46.png
│
├── workstations/
│   ├── salvagers_bench.png, finished_salvagers_bench.png
│   ├── spark_bench.png, finished_spark_bench.png
│   ├── tinker_station.png, finished_tinker_station.png
│   ├── skinshop_loom.png, finished_skinshop_loom.png
│   ├── cortex_spindle.png, finished_cortex_spindle.png
│   ├── barracks.png, finished_barracks.png
│   ├── stove.png, stove_e.png (2x1)
│   ├── finished_stove.png, finished_stove_e.png
│   ├── generator_sw/se/nw/ne.png (2x2)
│   ├── finished_generator_sw/se/nw/ne.png
│   ├── gutter_forge_sw/s/se/w/center/e/nw/n/ne.png (3x3)
│   ├── finished_gutter_forge_sw/s/se/w/center/e/nw/n/ne.png
│   ├── gutter_still_sw/s/se/w/center/e/nw/n/ne.png (3x3)
│   └── finished_gutter_still_sw/s/se/w/center/e/nw/n/ne.png
│
└── furniture/
    ├── comfort_chair.png
    ├── bar_stool.png
    ├── storage_locker.png
    ├── crash_bed.png, crash_bed_top.png (1x2)
    ├── scrap_guitar_placed.png
    ├── drum_kit_placed.png
    ├── synth_placed.png
    ├── harmonica_placed.png
    └── amp_placed.png
```

---

## 🔍 SPRITE LOADING LOGIC

### Workstations:
- **Path:** `assets/workstations/{tile_type}.png`
- **Finished:** `assets/workstations/finished_{tile_type}.png`
- **Multi-tile:** `assets/workstations/{tile_type}_{suffix}.png`

### Furniture:
- **Path:** `assets/furniture/{tile_type}.png`
- **Multi-tile:** `assets/furniture/{tile_type}_{suffix}.png`

### Buildings:
- **Path:** `assets/tiles/{tile_type}.png`
- **Finished:** `assets/tiles/finished_{tile_type}.png`

### Autotiling (walls, roads, dirt):
- **Walls:** `assets/tiles/walls/{tile_type}_autotile_{variant}.png` (0-46)
- **Roads:** `assets/tiles/roads/{tile_type}_autotile_{variant}.png` (0-46)
- **Dirt:** `assets/tiles/dirt/{tile_type}_autotile_{variant}.png` (0-46)

---

## ⚠️ IMPORTANT NOTES

1. **Workstations vs Tiles:** Workstations go in `assets/workstations/`, not `assets/tiles/`
2. **Furniture suffix:** Placed instruments use `_placed` suffix (e.g., `scrap_guitar_placed.png`)
3. **Multi-tile origin:** Always bottom-left tile is the origin (0,0 of the structure)
4. **Construction vs Finished:** Every buildable structure needs BOTH sprites
5. **Autotiling:** Walls, roads, and dirt use 47 variants (0-46) for seamless connections

---

**Last Updated:** Dec 31, 2025  
**Total Sprites Needed:** ~150+ (including autotile variants)
