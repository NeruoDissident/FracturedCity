# Rendering System - Fractured City

**Last Updated:** January 10, 2026  
**Renderer:** Python Arcade (GPU-accelerated)

## Overview

Fractured City uses **Python Arcade** for all rendering. The system is GPU-accelerated, achieving 60 FPS at all zoom levels with 1000+ sprites on screen.

---

## Architecture

### Entry Point
**`main.py`** (formerly `main_arcade.py`)
- Initializes Arcade window
- Sets up camera and viewport
- Manages game loop and rendering

### Core Rendering Components

**`grid_arcade.py`** - Tile Renderer
- GPU batch rendering for tiles
- Sprite caching system
- Layer-based rendering
- Autotiling integration

**`colonist_arcade.py`** - Colonist Renderer
- Character sprite rendering
- Animation states (idle, walking)
- Combat effects (shake, halo)
- Equipment visualization

**`animals_arcade.py`** - Animal Renderer
- Animal sprite rendering
- Movement animations
- Health indicators

---

## Rendering Pipeline

### Frame Rendering Order

1. **Camera Setup** - Position viewport
2. **Ground Layer** - Base terrain tiles
3. **Dirt Overlays** - Additive dirt autotiles
4. **Structures** - Walls, floors, doors
5. **Resources** - Trees, minerals, scrap piles
6. **Furniture** - Beds, tables, workstations
7. **Items** - Dropped world items
8. **Colonists** - Character sprites
9. **Animals** - Wildlife sprites
10. **Effects** - Combat halos, particles
11. **UI Overlays** - Selection boxes, highlights
12. **UI Panels** - Action bar, sidebars, popups

---

## Layer System

### Z-Levels
- **Z=0:** Ground level (streets, buildings)
- **Z=1:** Rooftops (accessible via ladders/fire escapes)

### Rendering Layers (per Z-level)
```python
LAYER_GROUND = 0
LAYER_DIRT_OVERLAY = 1
LAYER_STRUCTURES = 2
LAYER_RESOURCES = 3
LAYER_FURNITURE = 4
LAYER_ITEMS = 5
LAYER_COLONISTS = 6
LAYER_ANIMALS = 7
LAYER_EFFECTS = 8
LAYER_UI = 9
```

---

## Sprite Caching

### Cache Structure
```python
sprite_cache = {
    "wall_0": arcade.Texture,
    "finished_wall_0": arcade.Texture,
    "tree_3": arcade.Texture,
    # ... thousands of cached sprites
}
```

### Cache Strategy
- **First Load:** Sprite loaded from disk, cached
- **Subsequent Draws:** Retrieved from cache (instant)
- **Memory:** ~100-200MB for full sprite set
- **Performance:** 60 FPS with 2000+ cached sprites

---

## GPU Batch Rendering

### Sprite Lists
Arcade uses `SpriteList` for batch rendering:

```python
ground_sprites = arcade.SpriteList()
structure_sprites = arcade.SpriteList()
colonist_sprites = arcade.SpriteList()

# Add sprites
ground_sprites.append(sprite)

# Batch draw (single GPU call)
ground_sprites.draw()
```

### Performance Benefits
- **1 draw call** per sprite list (vs 1000+ individual calls)
- **GPU instancing** for identical sprites
- **Automatic culling** of off-screen sprites

---

## Camera System

### Arcade Camera2D
```python
self.camera = arcade.Camera2D()
self.camera.position = (world_x, world_y)
self.camera.zoom = zoom_level
```

### Viewport Calculation
```python
# Convert screen coords to world coords
viewport_width = screen_width / zoom_level
viewport_height = screen_height / zoom_level
view_left = camera_x - viewport_width / 2
view_bottom = camera_y - viewport_height / 2
```

### Zoom Levels
- **Min:** 0.5x (zoomed out, see more)
- **Max:** 2.0x (zoomed in, detail view)
- **Default:** 1.0x (1:1 pixel ratio)

---

## Autotiling Integration

### Road Autotiling
```python
variant = get_road_autotile_variant(grid, x, y, z)
sprite = load_sprite(f"street_autotile_{variant}.png")
```

### Blob Autotiling (Dirt Overlays)
```python
variant = get_blob_autotile_variant(grid, x, y, z)
sprite = load_sprite(f"ground_dirt_overlay_autotile_{variant}.png")
# Rendered as additive layer over ground
```

---

## Multi-Tile Structures

### Rendering Strategy
Each tile in a multi-tile structure renders its own sprite:

**Example: 2x1 Stove**
```python
# Tile (x, y) - origin
render_sprite("stove.png", x, y)

# Tile (x+1, y) - right
render_sprite("stove_right.png", x+1, y)
```

### Construction Tint
In-progress structures render with blue tint:
```python
if is_construction:
    sprite.color = (100, 150, 255)  # Blue tint
```

---

## Colonist Rendering

### Sprite Selection
```python
direction = colonist.facing_direction  # n, s, e, w, ne, nw, se, sw
state = "walking" if colonist.is_moving else "idle"
sprite = f"colonist_{direction}_{state}.png"
```

### Animation
- **Idle:** Static sprite
- **Walking:** Bob animation (vertical sine wave)
- **Combat:** Shake toward target

### Equipment Overlay
Future: Equipment sprites rendered on top of colonist base sprite

---

## UI Rendering

### Arcade UI System
**Native Arcade widgets** (no Pygame):
- `ui_arcade.py` - Action bar, resource display
- `ui_arcade_panels.py` - Left sidebar (colonists, jobs, items, rooms)
- `ui_arcade_colonist_popup.py` - Colonist detail panel
- `ui_arcade_bed.py` - Bed assignment
- `ui_arcade_workstation.py` - Workstation orders
- `ui_arcade_trader.py` - Trader interface
- `ui_arcade_visitor.py` - Visitor panel
- `ui_arcade_notifications.py` - Notification system
- `ui_arcade_tile_info.py` - Tile hover info
- `ui_arcade_stockpile.py` - Stockpile filters

### Drawing Order
UI drawn **after** world rendering, using screen coordinates (not world coordinates).

---

## Performance Optimization

### Current Performance
- **60 FPS** at 1920x1080
- **2000+ sprites** on screen
- **Zoom:** 0.5x to 2.0x (no FPS drop)

### Optimization Techniques
1. **Sprite Caching** - Load once, reuse forever
2. **Batch Rendering** - 1 draw call per layer
3. **Viewport Culling** - Only render visible tiles
4. **Texture Atlases** - Planned for further optimization

### Bottlenecks (None Currently)
- Rendering: GPU-bound, plenty of headroom
- Simulation: CPU-bound, runs at 60 ticks/sec
- Memory: ~200MB sprite cache (acceptable)

---

## Debugging

### Debug Overlays
- **F1:** FPS counter, tile info
- **F2:** Room visualization
- **F6:** Autotile debug view

### Performance Profiling
```python
import arcade.perf_info
arcade.perf_info.enable()
# Shows draw calls, sprite counts, FPS
```

---

## Migration Notes

### Pygame → Arcade Complete
- ✅ All Pygame rendering removed
- ✅ All UI rebuilt in Arcade
- ✅ Sprite loading migrated to Arcade
- ✅ Camera system using Arcade Camera2D
- ✅ 60 FPS achieved at all zoom levels

### Removed Files
- `sprites.py` (Pygame sprite loader)
- `ui.py` (Pygame UI panels)
- `debug_overlay.py` (Pygame debug)
- All Pygame rendering methods from `grid.py` and `colonist.py`

---

## See Also

- `grid_arcade.py` - Tile rendering implementation
- `colonist_arcade.py` - Colonist rendering
- `SPRITE_SYSTEM.md` - Sprite organization
- `AUTOTILE_GUIDE.md` - Autotiling specifications
