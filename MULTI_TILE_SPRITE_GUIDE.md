# Multi-Tile Workstation Sprite Naming Guide

## Overview
This document specifies the exact sprite file names required for each multi-tile workstation in Fractured City. All sprites should be placed in `assets/workstations/` directory.

---

## 2x1 Workstations (Horizontal)

### **Stove** (`stove`)
- **Size:** 2 tiles wide × 1 tile tall
- **Construction Sprites:**
  - `stove.png` - Left tile (origin)
  - `stove_right.png` - Right tile
- **Finished Sprites:**
  - `finished_stove.png` - Left tile (origin)
  - `finished_stove_right.png` - Right tile

---

## 2x2 Workstations

### **Generator** (`generator`)
- **Size:** 2 tiles wide × 2 tiles tall
- **Construction Sprites:**
  - `generator_sw.png` - Bottom-left (origin)
  - `generator_se.png` - Bottom-right
  - `generator_nw.png` - Top-left
  - `generator_ne.png` - Top-right
- **Finished Sprites:**
  - `finished_generator_sw.png` - Bottom-left (origin)
  - `finished_generator_se.png` - Bottom-right
  - `finished_generator_nw.png` - Top-left
  - `finished_generator_ne.png` - Top-right

---

## 3x3 Workstations

### **Gutter Forge** (`gutter_forge`)
- **Size:** 3 tiles wide × 3 tiles tall
- **Construction Sprites:**
  - `gutter_forge_sw.png` - Bottom-left (origin)
  - `gutter_forge_s.png` - Bottom-center
  - `gutter_forge_se.png` - Bottom-right
  - `gutter_forge_w.png` - Middle-left
  - `gutter_forge_center.png` - Middle-center
  - `gutter_forge_e.png` - Middle-right
  - `gutter_forge_nw.png` - Top-left
  - `gutter_forge_n.png` - Top-center
  - `gutter_forge_ne.png` - Top-right
- **Finished Sprites:**
  - `finished_gutter_forge_sw.png` - Bottom-left (origin)
  - `finished_gutter_forge_s.png` - Bottom-center
  - `finished_gutter_forge_se.png` - Bottom-right
  - `finished_gutter_forge_w.png` - Middle-left
  - `finished_gutter_forge_center.png` - Middle-center
  - `finished_gutter_forge_e.png` - Middle-right
  - `finished_gutter_forge_nw.png` - Top-left
  - `finished_gutter_forge_n.png` - Top-center
  - `finished_gutter_forge_ne.png` - Top-right

### **Gutter Still** (`gutter_still`)
- **Size:** 3 tiles wide × 3 tiles tall
- **Construction Sprites:**
  - `gutter_still_sw.png` - Bottom-left (origin)
  - `gutter_still_s.png` - Bottom-center
  - `gutter_still_se.png` - Bottom-right
  - `gutter_still_w.png` - Middle-left
  - `gutter_still_center.png` - Middle-center
  - `gutter_still_e.png` - Middle-right
  - `gutter_still_nw.png` - Top-left
  - `gutter_still_n.png` - Top-center
  - `gutter_still_ne.png` - Top-right
- **Finished Sprites:**
  - `finished_gutter_still_sw.png` - Bottom-left (origin)
  - `finished_gutter_still_s.png` - Bottom-center
  - `finished_gutter_still_se.png` - Bottom-right
  - `finished_gutter_still_w.png` - Middle-left
  - `finished_gutter_still_center.png` - Middle-center
  - `finished_gutter_still_e.png` - Middle-right
  - `finished_gutter_still_nw.png` - Top-left
  - `finished_gutter_still_n.png` - Top-center
  - `finished_gutter_still_ne.png` - Top-right

---

## 1x1 Workstations (Single Tile)

The following workstations are single-tile and only need one sprite each:

### **Salvager's Bench** (`salvagers_bench`)
- `salvagers_bench.png` - Construction sprite
- `finished_salvagers_bench.png` - Finished sprite

### **Spark Bench** (`spark_bench`)
- `spark_bench.png` - Construction sprite
- `finished_spark_bench.png` - Finished sprite

### **Tinker Station** (`tinker_station`)
- `tinker_station.png` - Construction sprite
- `finished_tinker_station.png` - Finished sprite

### **Skinshop Loom** (`skinshop_loom`)
- `skinshop_loom.png` - Construction sprite
- `finished_skinshop_loom.png` - Finished sprite

### **Cortex Spindle** (`cortex_spindle`)
- `cortex_spindle.png` - Construction sprite
- `finished_cortex_spindle.png` - Finished sprite

### **Barracks** (`barracks`)
- `barracks.png` - Construction sprite
- `finished_barracks.png` - Finished sprite

---

## Technical Details

### Coordinate System
- **Origin Tile:** Bottom-left tile of multi-tile structures
- **X-axis:** Increases to the right (west → east)
- **Y-axis:** Increases upward (south → north)

### Suffix Naming Convention
- **Compass Directions:**
  - `sw` = Southwest (bottom-left)
  - `s` = South (bottom-center)
  - `se` = Southeast (bottom-right)
  - `w` = West (middle-left)
  - `center` = Center (middle-center)
  - `e` = East (middle-right)
  - `nw` = Northwest (top-left)
  - `n` = North (top-center)
  - `ne` = Northeast (top-right)
- **Simple Directions:**
  - `right` = Right tile (for 2x1 horizontal)
  - `top` = Top tile (for 1x2 vertical)

### Rendering Behavior
- **Floor Preservation:** All workstations render as overlays on top of floor tiles
- **Construction Darkening:** Construction sprites are automatically darkened (60% brightness)
- **Fallback:** If multi-tile sprites are missing, the system falls back to single sprite for all tiles

### Sprite Requirements
- **Format:** PNG with transparency
- **Size:** 64×64 pixels per tile
- **Location:** `assets/workstations/` directory
- **Naming:** Exact match required (case-sensitive on some systems)

---

## Adding New Multi-Tile Workstations

To add a new multi-tile workstation:

1. **Define in `buildings.py`:**
   ```python
   "my_workstation": {
       "name": "My Workstation",
       "tile_type": "my_workstation",
       "size": (2, 2),  # width, height
       "workstation": True,
       # ... other properties
   }
   ```

2. **Create sprites following naming convention:**
   - For 2x2: `my_workstation_sw.png`, `_se.png`, `_nw.png`, `_ne.png`
   - For 3x3: All 9 compass direction suffixes
   - For 2x1: `my_workstation.png` and `my_workstation_right.png`

3. **Add finished variants:**
   - Prefix all sprite names with `finished_`
   - Example: `finished_my_workstation_sw.png`

4. **Update `colonist.py` completion logic:**
   ```python
   elif current_tile == "my_workstation":
       grid.set_tile(job.x, job.y, "finished_my_workstation", z=job.z)
       # Mark multi-tile footprint as unwalkable
       width, height = buildings.get_building_size("my_workstation")
       for dy in range(height):
           for dx in range(width):
               grid.walkable[job.z][job.y + dy][job.x + dx] = False
       # Register as workstation
       buildings.register_workstation(job.x, job.y, job.z, "my_workstation")
   ```

---

## System Implementation

The multi-tile rendering system is implemented in:
- **`grid_arcade.py`:** Renderer with `_render_multi_tile_structure()` method
- **`buildings.py`:** `get_building_size()` function strips "finished_" prefix
- **`colonist.py`:** Construction completion marks footprint unwalkable

All multi-tile workstations automatically use this system - no additional code required per workstation.
