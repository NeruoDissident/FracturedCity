# Current Construction Sprite System - Analysis

## Overview

This document maps out how construction elements (walls, floors, workstations, furniture) are currently being rendered in the game.

---

## Sprite Locations

### **Walls**
**Location:** `assets/tiles/`
- `finished_wall_0.png` (3 variations: _0, _1, _2)
- `wall_0.png` (under construction version)

### **Floors**
**Location:** `assets/tiles/`
- `finished_floor_0.png` through `finished_floor_4.png` (5 variations)
- `floor_0.png` (under construction version)
- `Xfinished_floor_0.png` (backup/old version)

### **Doors & Windows**
**Location:** `assets/tiles/`
- `finished_door.png` (single sprite)
- `door.png` (under construction)
- `bar_door.png` (special door type)
- `window.png` (single sprite)

### **Bridges**
**Location:** `assets/tiles/`
- `finished_bridge_0.png` through `finished_bridge_3.png` (4 variations)
- `finished_bridge4.png` (5th variation - note different naming)

### **Stage/Platform**
**Location:** `assets/tiles/`
- `finished_stage_0.png` through `finished_stage_2.png` (3 variations)

### **Bar Counter**
**Location:** `assets/tiles/`
- `finished_scrap_bar_counter_0.png` through `finished_scrap_bar_counter_2.png` (3 variations)

### **Workstations**
**Location:** `assets/workstations/`
- `finished_cortex_spindle.png`
- `finished_generator.png`
- `finished_gutter_forge.png`
- `finished_gutter_still.png`
- `finished_salvagers_bench.png`
- `finished_skinshop_loom.png`
- `finished_spark_bench.png`
- `finished_stove.png`
- `finished_tinker_station.png`

**Note:** Workstations have NO variations - single sprite each

### **Furniture**
**Location:** `assets/furniture/`
- `crash_bed.png`
- `comfort_chair.png`
- `bar_stool.png`
- `amp_placed.png`
- `drum_kit_placed.png`
- `harmonica_placed.png`
- `scrap_guitar_placed.png`
- `synth_placed.png`

**Note:** Furniture has NO variations - single sprite each

---

## Current Rendering Logic

### **Construction State Mapping** (`grid_arcade.py` lines 115-151)

The system maps construction tiles to their finished versions:

```python
construction_to_finished = {
    # Structures
    "wall": "finished_wall",
    "floor": "finished_floor",
    "door": "finished_door",
    "window": "finished_window",
    "bridge": "finished_bridge",
    
    # Workstations
    "gutter_still": "finished_gutter_still",
    "stove": "finished_stove",
    # ... etc
    
    # Furniture
    "crash_bed": "finished_crash_bed",
    "bar_stool": "finished_bar_stool",
    # ... etc
}
```

**How it works:**
1. During construction: tile_type is `"wall"` → maps to `"finished_wall"` sprite (rendered darker)
2. After construction: tile_type is `"finished_wall"` → uses `"finished_wall"` sprite (normal brightness)

### **Variation System** (`grid_arcade.py` lines 159-203)

**Position-based variation:**
```python
variation_index = (x * 7 + y * 13 + z * 3) % 8  # 0-7 range
```

**Variation counts by type:**
- **Walls:** 3 variations (0-2)
- **Floors:** 5 variations (0-4)
- **Bridges:** 5 variations (0-4, special case)
- **Stage:** 3 variations (0-2)
- **Bar Counter:** 3 variations (0-2)
- **Workstations:** NO variations (single sprite)
- **Furniture:** NO variations (single sprite)

**Fallback system:**
Tries variations in descending order: 8, 6, 4, 3, 2, 1, then base sprite
- If `finished_wall_7.png` doesn't exist, tries `_5`, then `_3`, then `_2`, then `_1`, then `finished_wall.png`

### **Sprite Path Logic** (`grid_arcade.py` lines 167-203)

**1. Workstations** (checked first):
```python
if tile_type in workstation_types:
    sprite_path = f"assets/workstations/{tile_type}.png"
```

**2. Variations** (for walls, floors, bridges):
```python
sprite_path = f"assets/tiles/{tile_type}_{variation}.png"
```

**3. Base sprite** (fallback):
```python
sprite_path = f"assets/tiles/{tile_type}.png"
```

### **Furniture Rendering** (`grid_arcade.py` lines 413-441)

Furniture uses special 2-layer rendering:

```python
furniture_tiles = [
    "crash_bed", "comfort_chair", "bar_stool",
    "scrap_guitar_placed", "drum_kit_placed", "synth_placed",
    "harmonica_placed", "amp_placed"
]

if tile_type in furniture_tiles:
    # Layer 1: Draw floor first
    floor_texture = get_tile_texture("finished_floor", x, y, z)
    
    # Layer 2: Draw furniture on top
    furniture_texture = _get_furniture_texture(tile_type)
```

**Furniture path:**
```python
sprite_path = f"assets/furniture/{furniture_type}.png"
```

---

## Current Issues & Limitations

### **1. No Autotiling for Walls**
- Walls use simple variations, not autotiling
- No corner detection or connection logic
- Walls don't connect smoothly to each other

### **2. No Autotiling for Floors**
- Floors use simple variations
- No edge detection where floors meet walls
- No transitions between floor and ground

### **3. Limited Variations**
- Walls: only 3 variations
- Floors: only 5 variations
- Can look repetitive in large buildings

### **4. Workstations Have No Variations**
- Single sprite per workstation type
- Multiple of same workstation look identical

### **5. Furniture Rendering**
- Hardcoded list in two places (lines 300 and 416)
- No variation system
- Floor always renders under furniture (correct)

### **6. Construction State**
- Uses same sprite for construction and finished
- Relies on darkening for "under construction" look
- No visual progress indication

---

## Sprite Naming Conventions

### **Current Patterns:**

**Variations:**
- `finished_wall_0.png`, `finished_wall_1.png`, `finished_wall_2.png`
- `finished_floor_0.png` through `finished_floor_4.png`

**Single sprites:**
- `finished_door.png` (no variation number)
- `finished_generator.png` (workstations)

**Inconsistencies:**
- `finished_bridge4.png` (no underscore before 4)
- `Xfinished_floor_0.png` (X prefix for disabled/backup)

---

## Rendering Order (Current)

From `grid_arcade.py` 4-pass system:

1. **Pass 1:** Concrete base
2. **Pass 2:** Dirt/grass overlays
3. **Pass 3:** Roads
4. **Pass 4:** Structures (walls, floors, workstations, furniture)

**Within Pass 4:**
- Furniture: floor layer → furniture layer
- Everything else: single sprite

---

## What Could Be Improved

### **Potential Enhancements:**

1. **Wall Autotiling**
   - 13-tile or 47-tile system for smooth corners
   - Walls connect to adjacent walls
   - Different sprites for corners, T-junctions, crosses

2. **Floor Autotiling**
   - Edge detection where floor meets walls
   - Transitions between floor and ground
   - Interior vs edge tiles

3. **More Variations**
   - Walls: 8+ variations
   - Floors: 8+ variations
   - Workstations: 2-3 variations each

4. **Construction Progress**
   - Separate sprites for 0%, 25%, 50%, 75%, 100%
   - Visual scaffolding or framework
   - Material piles during construction

5. **Modular Workstations**
   - Base + attachments system
   - Directional variants (facing different ways)
   - Upgrade tiers with visual changes

---

## Files to Modify for Changes

1. **`grid_arcade.py`** - Rendering logic
   - `get_tile_texture()` - sprite path logic
   - `construction_to_finished` - mapping dictionary
   - `workstation_types` - workstation list
   - `furniture_tiles` - furniture list (2 places)

2. **`autotiling.py`** - If adding autotiling
   - Add wall/floor autotiling functions
   - Update `should_autotile()` to include walls/floors
   - Add connection groups for walls

3. **Sprite files** - Create new sprites
   - Walls: autotile variants or more variations
   - Floors: autotile variants or more variations
   - Workstations: variation sprites
   - Construction: progress sprites

---

**Last Updated:** Dec 29, 2025
**Current System:** Simple variation-based rendering, no autotiling for structures
