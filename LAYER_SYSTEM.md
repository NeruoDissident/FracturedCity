# Layered Rendering System - Fractured City

## Overview

The game uses a multi-pass layered rendering system with alpha blending to create rich, detailed environments. All sprites are transparent PNGs that stack on top of each other.

---

## Rendering Order (Bottom to Top)

### **Layer 1: Concrete Base**
- **Always rendered** for every tile
- Sprite: `ground_concrete_0.png` (with variations)
- Provides consistent base texture across entire map
- Method: `_add_concrete_base()`

### **Layer 2: Dirt/Grass/Rubble Overlays**
- **Optional** - only where placed in `grid.overlay_tiles`
- Sprites: `ground_dirt_overlay_autotile_0.png` through `_46.png`
- Uses **47-tile blob autotiling** for organic shapes
- Transparent PNGs that show concrete through gaps
- Method: `_add_overlay_sprite()`
- Examples:
  - `ground_dirt_overlay_autotile` - brown dirt patches
  - `ground_rubble_overlay_autotile` - debris (future)
  - `ground_overgrown_overlay_autotile` - weeds/grass (future)

### **Layer 3: Roads/Streets**
- **Optional** - only where roads exist in `grid.tiles`
- Sprites: `street_autotile_0.png` through `_12.png` (in `assets/tiles/roads/`)
- Uses **13-tile path autotiling** for linear features
- Transparent PNGs that show concrete/dirt through gaps
- Method: `_add_road_sprite()`
- Examples:
  - `street` - main roads
  - `road` - alternate road type

### **Layer 4: Structures**
- **Optional** - walls, floors, buildings
- Various sprites with autotiling or variations
- Method: `_add_structure_sprite()`
- Examples:
  - `finished_wall` - building walls
  - `finished_floor` - interior floors
  - `finished_bridge` - elevated structures

---

## Autotiling Systems

### **47-Tile Blob System** (Organic Patches)
- Used for: Dirt, grass, rubble overlays
- Checks all 8 neighbors (N, S, E, W, NE, NW, SE, SW)
- Bitmask-based variant selection
- Handles all possible neighbor combinations
- Creates smooth, organic blob shapes
- Function: `_get_blob_variant()` in `autotiling.py`

### **13-Tile Path System** (Linear Features)
- Used for: Roads, streets
- Checks 4 cardinal neighbors (N, S, E, W)
- Simpler variant selection for paths
- Creates convincing road networks
- Function: `_get_path_variant()` in `autotiling.py`

### **How System Decides:**
```python
# Line 32 in autotiling.py
is_patch = "overlay_autotile" in tile_type
```
- If tile name contains `"overlay_autotile"` → uses 47-tile blob
- Otherwise → uses 13-tile path

---

## Sprite Organization

```
assets/tiles/
├── ground_concrete_0.png              # Base layer (always)
├── dirt/
│   ├── ground_dirt_overlay_autotile_0.png
│   ├── ground_dirt_overlay_autotile_1.png
│   └── ... (through _46.png)          # 47 variants
├── roads/
│   ├── street_autotile_0.png
│   ├── street_autotile_1.png
│   └── ... (through _12.png)          # 13 variants
└── [other tiles]
```

---

## Adding New Overlay Layers

To add a new overlay type (e.g., weeds, debris):

### 1. Create Sprites
- Create 47 PNG sprites (64x64 pixels)
- Name: `ground_[type]_overlay_autotile_0.png` through `_46.png`
- Make transparent PNGs (alpha channel)
- Place in `assets/tiles/[type]/` subfolder

### 2. Update Autotiling System
Add to `AUTOTILE_GROUPS` in `autotiling.py`:
```python
"ground_weeds_overlay_autotile": {"ground_weeds_overlay_autotile"},
```

### 3. Update Grid System
Add to `should_autotile()` in `autotiling.py` (already covered by `"overlay_autotile"` keyword)

### 4. Update Renderer
Add sprite path logic in `grid_arcade.py` `get_tile_texture()`:
```python
if "weeds_overlay" in tile_type:
    sprite_path = f"assets/tiles/weeds/{tile_type}_{variant}.png"
```

### 5. Place in World
Use `grid.overlay_tiles` to place:
```python
grid.overlay_tiles[(x, y, z)] = "ground_weeds_overlay_autotile"
```

---

## Current Overlay Types

| Type | Sprites | Autotiling | Status |
|------|---------|------------|--------|
| **Concrete Base** | 1 (variations) | No | ✅ Active |
| **Dirt** | 47 | Blob (47-tile) | ✅ Active |
| **Roads** | 13 | Path (13-tile) | ✅ Active |
| **Rubble** | 47 | Blob (47-tile) | 🔄 Planned |
| **Weeds/Overgrown** | 47 | Blob (47-tile) | 🔄 Planned |
| **Debris** | 47 | Blob (47-tile) | 🔄 Planned |

---

## Technical Details

### Rendering Performance
- Uses Arcade's GPU-accelerated sprite batching
- All sprites added to `tile_sprite_list` for batch rendering
- Spatial hashing enabled for efficient culling
- 4-pass system ensures correct layer order

### Alpha Blending
- All overlay sprites use alpha transparency
- Arcade handles blending automatically
- Sprites render in order added to sprite list
- Later sprites render on top of earlier sprites

### Z-Level Support
- Z-1 level rendered at 50% opacity for depth effect
- Current Z-level rendered at full opacity
- Each Z-level has independent overlay system

---

## Future Enhancements

1. **Multiple Overlay Layers per Tile**
   - Currently: 1 overlay per tile position
   - Future: Stack multiple overlays (dirt + weeds + debris)
   - Requires: Multi-layer overlay system in `grid.py`

2. **Animated Overlays**
   - Flickering lights, flowing water, etc.
   - Requires: Frame animation system

3. **Dynamic Overlays**
   - Overlays that change over time (rust spreading, plants growing)
   - Requires: Overlay update system

4. **Overlay Interactions**
   - Roads prevent grass growth
   - Rain creates puddles
   - Requires: Overlay rule system

---

## Troubleshooting

### Roads not rendering?
- Check sprite path: `assets/tiles/roads/street_autotile_X.png`
- Verify autotiling is enabled for "street" tiles
- Check if roads are in base tiles, not overlay tiles

### Dirt rendering on top of roads?
- This was fixed in the 4-pass rendering system
- Verify rendering order: concrete → dirt → roads → structures

### Autotiling looks wrong?
- Check neighbor detection in `_is_connected()`
- Verify bitmask mapping in `_get_blob_variant()`
- Test with simple patterns first (straight lines, corners)

### Sprites not loading?
- Check file paths and naming conventions
- Verify PNG format and transparency
- Check console for loading errors

---

**Last Updated:** Dec 29, 2025
**System Version:** Arcade-based rendering
