# Sprite System - Fractured City

**Last Updated:** January 10, 2026  
**Status:** Arcade rendering only

## Overview

Fractured City uses a sprite-based rendering system with Arcade. All sprites are loaded from `assets/` directory and cached for performance.

---

## Sprite Loading System

### Tileset Loader (`tileset_loader.py`)
- Loads sprite sheets and extracts individual tiles
- Supports texture atlases for efficient GPU batching
- Handles sprite variants and autotiling

### Grid Renderer (`grid_arcade.py`)
- GPU-accelerated batch rendering
- Sprite caching system
- Layer-based rendering (ground → structures → colonists → UI)

---

## Naming Convention

```
{category}_{type}_{variant}_{state}.png
```

**Examples:**
- `ground_concrete_0.png`
- `wall_finished_0.png`
- `stove_right.png` (multi-tile)
- `street_autotile_3.png` (autotiling)

---

## Sprite Categories

### 1. Ground Tiles
**Location:** `assets/tiles/ground/`

Basic ground surfaces:
- `ground_concrete_*.png` - Concrete surfaces
- `ground_pavement_*.png` - Paved surfaces
- `ground_dirt_*.png` - Exposed dirt
- `ground_rubble_*.png` - Debris-covered

### 2. Structures
**Location:** `assets/tiles/structures/`

Walls, floors, doors:
- `wall_*.png` - Wall construction
- `finished_wall_*.png` - Completed walls
- `floor_*.png` - Interior flooring
- `finished_floor_*.png` - Completed floors
- `door_*.png` / `finished_door_*.png`
- `window_*.png` / `finished_window_*.png`

### 3. Roads & Streets
**Location:** `assets/tiles/roads/`

Urban infrastructure:
- `street_*.png` - Road tiles
- `street_autotile_*.png` - Road connections (13-tile system)
- `sidewalk_*.png` - Pedestrian paths
- `bridge_*.png` - Elevated connections

### 4. Workstations
**Location:** `assets/workstations/`

Crafting stations (see Multi-Tile section):
- Single-tile: `salvagers_bench.png`, `spark_bench.png`, etc.
- Multi-tile: `stove_*.png`, `generator_*.png`, `gutter_forge_*.png`

### 5. Furniture
**Location:** `assets/furniture/`

Placeable objects:
- `crash_bed_*.png` - Beds (1x2 vertical)
- `table_*.png` - Tables
- `chair_*.png` - Seating

### 6. Resources
**Location:** `assets/resources/`

Harvestable nodes:
- `tree_*.png` - Wood sources
- `mineral_node_*.png` - Mineral deposits
- `scrap_pile_*.png` - Salvageable debris

### 7. Colonists
**Location:** `assets/colonists/`

Character sprites:
- `colonist_{direction}_{state}.png`
- Directions: `n`, `s`, `e`, `w`, `ne`, `nw`, `se`, `sw`
- States: `idle`, `walking`

---

## Multi-Tile Structures

Multi-tile workstations use directional suffixes for each tile.

### 2x1 Horizontal (Stove, Bio-Matter Station)
```
[origin] [_right]
```

**Files:**
- `stove.png` + `stove_right.png` (construction)
- `finished_stove.png` + `finished_stove_right.png` (complete)

### 2x2 (Generator)
```
[_nw] [_ne]
[_sw] [_se]  (origin)
```

**Files:**
- `generator_sw.png`, `generator_se.png`, `generator_nw.png`, `generator_ne.png`
- `finished_generator_*.png` (4 finished variants)

### 3x3 (Gutter Forge, Gutter Still)
```
[_nw] [_n]  [_ne]
[_w]  [_c]  [_e]
[_sw] [_s]  [_se]  (origin)
```

**Files:**
- 9 construction sprites: `gutter_forge_{sw,s,se,w,center,e,nw,n,ne}.png`
- 9 finished sprites: `finished_gutter_forge_*.png`

### 1x2 Vertical (Crash Bed)
```
[_top]
[origin]
```

**Files:**
- `crash_bed.png` + `crash_bed_top.png`
- `finished_crash_bed.png` + `finished_crash_bed_top.png`

---

## Additive Sprites

Some tiles support **additive overlays** for visual variety.

### Dirt Overlays
**Location:** `assets/tiles/dirt/`

Dirt patches blend onto ground tiles:
- `ground_dirt_overlay_autotile_*.png` (47-tile blob autotiling)
- Applied on top of concrete/pavement for organic look

### Trash Particles
**Location:** `assets/particles/`

Small debris scattered on ground:
- `trash_particle_*.png` (multiple variants)
- Randomly placed for urban decay aesthetic

---

## Autotiling Systems

### 13-Tile Road System
Used for: roads, sidewalks, bridges

**Variants:**
- `0` - Isolated
- `1` - Horizontal straight
- `2` - Vertical straight
- `3-6` - Corners (NW, NE, SW, SE)
- `7-10` - T-junctions (N, S, E, W)
- `11` - 4-way intersection
- `12` - End cap

### 47-Tile Blob System
Used for: dirt overlays, organic transitions

**Bitmask-based:** Each tile represents a unique neighbor configuration
- Supports inner/outer corners
- Smooth organic edges
- See `AUTOTILE_GUIDE.md` for full spec

---

## Sprite States

### Construction vs Finished
Most structures have two states:
- **Construction:** `{name}.png` - Blueprint/in-progress
- **Finished:** `finished_{name}.png` - Completed structure

### Variants
Multiple visual variants for variety:
- `tree_0.png`, `tree_1.png`, `tree_2.png`
- Selected deterministically based on tile position

---

## Asset Organization

```
assets/
├── tiles/
│   ├── ground/          # Ground surfaces
│   ├── structures/      # Walls, floors, doors
│   ├── roads/           # Streets, sidewalks
│   └── dirt/            # Dirt overlays
├── workstations/        # Crafting stations
├── furniture/           # Beds, tables, chairs
├── resources/           # Trees, minerals, scrap
├── colonists/           # Character sprites
└── particles/           # Debris, effects
```

---

## Performance Notes

- **Sprite Caching:** All sprites cached on first load
- **Batch Rendering:** GPU batching for 1000+ sprites per frame
- **Texture Atlases:** Planned for further optimization
- **60 FPS Target:** Achieved at all zoom levels with current system

---

## See Also

- `AUTOTILE_GUIDE.md` - Detailed autotiling specifications
- `grid_arcade.py` - Rendering implementation
- `tileset_loader.py` - Sprite loading system
