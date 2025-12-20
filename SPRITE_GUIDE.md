# Fractured City - Sprite System Guide

## Overview

The sprite system allows you to replace procedural drawing with actual image sprites. It supports:
- **Tile variations** - Multiple sprites per tile type for visual variety
- **Directional colonist sprites** - North, East, West facing (South uses East/West alternation)
- **Zoom support** - Sprites scale cleanly at any zoom level
- **Fallback rendering** - If sprite not found, uses procedural drawing

## Folder Structure

```
Fractured City/
  assets/
    tiles/
      # Ground tiles
      empty_0.png, empty_1.png, empty_2.png, ...
      dirt_0.png, dirt_1.png, ...
      grass_0.png, grass_1.png, ...
      
      # Floors
      finished_floor_0.png, finished_floor_1.png, ...
      
      # Walls
      finished_wall_0.png, finished_wall_1.png, ...
      wall_0.png (under construction)
      
      # Doors/Windows
      finished_door.png
      door.png (under construction)
      finished_window.png
      bar_door.png
      
      # Workstations (finished)
      finished_spark_bench.png
      finished_tinker_station.png
      finished_generator.png
      finished_gutter_forge.png
      finished_salvagers_bench.png
      finished_stove.png
      finished_skinshop_loom.png
      finished_cortex_spindle.png
      finished_gutter_still.png
      
      # Furniture/Instruments
      crash_bed.png
      comfort_chair.png
      bar_stool.png
      scrap_guitar_placed.png
      drum_kit_placed.png
      synth_placed.png
      harmonica_placed.png
      amp_placed.png
      
      # Stage
      stage_0.png, stage_1.png, ...
      stage_stairs.png
      
      # Bar
      scrap_bar_counter.png
      
    colonists/
      # Default colonist
      default_north.png    # Facing away/up
      default_east.png     # Facing right
      default_west.png     # Facing left (mirror of east works too)
      
      # Additional variations (optional)
      worker_north.png
      worker_east.png
      worker_west.png
      
      scavenger_north.png
      scavenger_east.png
      scavenger_west.png
      
    buildings/
      # Under construction versions
      spark_bench.png
      tinker_station.png
      generator.png
      salvagers_bench.png
      ...
      
    items/
      # Components
      wire.png
      resistor.png
      capacitor.png
      chip.png
      led.png
      
      # Instruments (as items before placement)
      scrap_guitar.png
      drum_kit.png
      synth.png
      harmonica.png
      amp.png
      
      # Consumables
      swill.png
      guttershine.png
      
      # Equipment
      hard_hat.png
      work_gloves.png
      ...
```

## Sprite Specifications

### Tile Sprites
- **Size:** 64x64 pixels (recommended)
- **Format:** PNG with transparency
- **Variations:** Up to 8 per tile type (0-7)
- **Naming:** `{tile_type}_{variation}.png` or just `{tile_type}.png`

### Colonist Sprites
- **Size:** 64x64 pixels (or larger for detail)
- **Format:** PNG with transparency
- **Directions:** north, east, west (south uses east/west alternation)
- **Naming:** `{colonist_id}_{direction}.png`
- **Animation:** For walking south, system alternates between east and west sprites

### Item/Building Sprites
- **Size:** 64x64 pixels
- **Format:** PNG with transparency
- **Naming:** `{item_id}.png` or `{building_type}.png`

## How It Works

### Tile Rendering
1. System checks for sprite: `tiles/{tile_type}_{variation}.png`
2. If not found, tries: `tiles/{tile_type}.png`
3. If still not found, falls back to procedural drawing
4. Variation is deterministic based on tile position (x, y, z)

### Colonist Rendering
1. Determines direction from movement (dx, dy)
2. For south movement: alternates between east/west sprites every 0.2 seconds
3. Loads sprite: `colonists/{colonist_id}_{direction}.png`
4. Falls back to procedural "sprite person" if not found

### Zoom Support
- Sprites are cached at each zoom level
- When zoom changes, scaled cache is cleared
- Sprites scale smoothly using pygame.transform.scale()

## Integration Points

### In grid.py
```python
# Try to draw tile with sprite first
sprite = sprites.get_tile_sprite(tile, x, y, z, TILE_SIZE)
if sprite:
    surface.blit(sprite, rect.topleft)
else:
    # Fall back to procedural drawing
    draw_tile_procedural(surface, tile, rect, x, y, z)
```

### In colonist rendering
```python
# Get colonist sprite based on direction and movement
colonist_sprite = colonist.sprite_manager.get_sprite(
    direction=colonist.facing_direction,
    is_moving=colonist.is_moving,
    tile_size=TILE_SIZE
)

if colonist_sprite:
    surface.blit(colonist_sprite, (screen_x, screen_y))
else:
    # Fall back to sprite person
    draw_sprite_person(surface, colonist, screen_x, screen_y)
```

## Quick Start

### 1. Create Assets Folder
```bash
mkdir assets
mkdir assets/tiles
mkdir assets/colonists
mkdir assets/buildings
mkdir assets/items
```

### 2. Add Your First Sprites
Start with the most visible elements:
- `colonists/default_north.png`
- `colonists/default_east.png`
- `colonists/default_west.png`
- `tiles/finished_floor_0.png`
- `tiles/finished_wall_0.png`

### 3. Test
Run the game - sprites will load automatically. If a sprite is missing, the game falls back to procedural drawing.

### 4. Add More Sprites
Add sprites gradually. The system supports:
- 100+ sprites easily
- Multiple variations per tile
- Different colonist types
- All items and buildings

## Performance Notes

- Sprites are cached after first load (fast)
- Scaled sprites are cached per zoom level (fast)
- Cache clears when zoom changes (necessary)
- No performance impact from missing sprites (graceful fallback)

## Tips for Creating Sprites

### Tile Variations
Create 4-8 variations per tile type for organic look:
- Slight color differences
- Different wear patterns
- Rotated details
- Cracks, stains, weathering

### Colonist Sprites
- North: Back view, facing away
- East: Side view, facing right
- West: Side view, facing left (can mirror east)
- South: Not needed (uses east/west alternation)

### Transparency
- Use alpha channel for irregular shapes
- Tiles can have transparent edges for blending
- Colonists should have transparent backgrounds

### Style Consistency
- Keep lighting direction consistent
- Match color palette across all sprites
- Use same level of detail/resolution
- Maintain cyberpunk aesthetic!

## Current Status

✅ Sprite system implemented
✅ Tile sprite support with variations
✅ Colonist directional sprites
✅ Zoom support
✅ Fallback to procedural rendering
⏳ Waiting for sprite assets to be created

**Ready to receive your sprites!** Drop them in the assets folder and they'll load automatically.
