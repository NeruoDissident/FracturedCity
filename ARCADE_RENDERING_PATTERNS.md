# Arcade Rendering Patterns & Best Practices

**Last Updated:** Dec 31, 2025

This document defines the standard patterns for rendering in Fractured City using Python Arcade. Follow these patterns for consistency and rapid iteration.

---

## Core Architecture

### Main Entry Point
- **File:** `main_arcade.py`
- **Purpose:** Primary game loop, event handling, rendering orchestration
- **Status:** ✅ Active - This is the production codebase

### Legacy Files (DO NOT USE)
- `main.py` - Old Pygame version, kept for reference only
- `ui.py`, `ui_layout.py`, `ui_workstation_new.py` - Old Pygame UI
- `sprites.py` - Old Pygame sprite loading
- `debug_overlay.py` - Old Pygame debug overlay

**Note:** These files still import pygame but are NOT used in the Arcade rendering path.

---

## Rendering System Components

### 1. Grid Rendering (`grid_arcade.py`)

**Purpose:** Renders all tiles, structures, furniture, and world objects.

**Key Classes:**
- `GridRenderer` - Main renderer with Z-level support

**Rendering Passes (in order):**
1. **Concrete base** - Always rendered first
2. **Overlays** - Transparent material overlays (Z0 only)
3. **Roads** - Street tiles (Z0 only)
4. **Floors** - All floor types
5. **Resources** - Resource nodes, salvage objects (Z0 only)
6. **Structures** - Walls, buildings, furniture, workstations

**Sprite Loading Pattern:**
```python
# Tiles: assets/tiles/{tile_type}_{variation}.png
texture = self.get_tile_texture(tile_type, x, y, z)

# Furniture: assets/furniture/{furniture_type}.png
texture = self._get_furniture_texture(furniture_type)

# Workstations: assets/workstations/{workstation_type}.png
sprite_path = f"assets/workstations/{tile_type}.png"
```

**Furniture Rendering (CRITICAL PATTERN):**
```python
# Furniture uses floor + furniture layering
furniture_tiles = [
    "crash_bed", "comfort_chair", "bar_stool", "storage_locker",
    "vending_machine", "dining_table", "wall_lamp", "weapon_rack",
    "scrap_guitar_placed", "drum_kit_placed", "synth_placed",
    "harmonica_placed", "amp_placed"
]

# Render floor first, then furniture sprite on top
if tile_type in furniture_tiles:
    # 1. Draw floor
    floor_texture = self.get_tile_texture("finished_floor", x, y, z)
    # 2. Draw furniture
    furniture_texture = self._get_furniture_texture(tile_type)
```

**Multi-Tile Structures:**
- Workstations, furniture can be multi-tile (e.g., crash_bed is 1x2)
- Origin tile (bottom-left) stores the tile type
- Renderer handles multi-tile sprite loading automatically
- See `FURNITURE_SIZES` in `furniture.py` for size definitions

**Construction Mapping:**
```python
construction_to_finished = {
    "crash_bed": "finished_crash_bed",
    "vending_machine": "finished_vending_machine",
    # etc.
}
```

---

### 2. Colonist Rendering (`colonist_arcade.py`)

**Purpose:** Renders colonists with animations and state indicators.

**Key Features:**
- Sprite-based colonist rendering
- Animation support (walking, working, etc.)
- Health bars, status indicators
- Combat visual feedback (red halos, bounce animations)

**Pattern:**
```python
# Colonist sprites loaded from assets/colonists/
colonist_renderer = ColonistRenderer(colonists)
colonist_renderer.draw()
```

---

### 3. UI System (`ui_arcade*.py`)

**Purpose:** All UI panels, menus, tooltips using native Arcade drawing.

**Key Files:**
- `ui_arcade.py` - Top bar, action bar, colonist list
- `ui_arcade_panels.py` - Left sidebar, colonist detail panel
- `ui_arcade_workstation.py` - Workstation panel with recipes/orders
- `ui_arcade_visitor.py` - Visitor acceptance panel
- `ui_arcade_trader.py` - Trader/fixer panel
- `ui_arcade_bed.py` - Bed assignment panel
- `ui_arcade_notifications.py` - Pop-up notifications

**UI Drawing Pattern:**
```python
# Use arcade.draw_* functions directly
arcade.draw_lrbt_rectangle_filled(x1, x2, y1, y2, color)
arcade.draw_lrbt_rectangle_outline(x1, x2, y1, y2, color, width)
arcade.draw_text(text, x, y, color, font_size, bold, font_name)
```

**Color Palette (from `ui_arcade.py`):**
```python
# Neon accents
COLOR_NEON_CYAN = (0, 255, 255)
COLOR_NEON_MAGENTA = (255, 0, 255)
COLOR_NEON_PINK = (255, 50, 150)

# Backgrounds
COLOR_BG_DARKEST = (8, 10, 15)
COLOR_BG_DARK = (15, 18, 25)
COLOR_BG_PANEL = (20, 25, 35)

# Text
COLOR_TEXT_BRIGHT = (240, 250, 255)
COLOR_TEXT_NORMAL = (200, 210, 230)
COLOR_TEXT_DIM = (150, 165, 190)

# Fonts
UI_FONT = ("Bahnschrift", "Segoe UI", "Arial")
UI_FONT_MONO = ("Cascadia Mono", "Consolas", "Courier New")
```

**Tooltip Pattern (STANDARD):**
```python
# Use simple word wrapping, font size 9-10
tooltip_width = 280
tooltip_padding = 10
line_height = 16

# Build lines with word wrapping
lines = [title]
words = description.split()
current_line = ""
for word in words:
    test_line = current_line + " " + word if current_line else word
    if len(test_line) * 7 > tooltip_width - tooltip_padding * 2:
        if current_line:
            lines.append(current_line)
        current_line = word
    else:
        current_line = test_line
if current_line:
    lines.append(current_line)

# Draw with consistent styling
arcade.draw_text(line, x, y, color, font_size=9, font_name=UI_FONT)
```

---

## Adding New Furniture

**1. Define in `items.py`:**
```python
ItemDef(
    id="my_furniture",
    name="My Furniture",
    tags=["furniture"],
    description="Cool description"
)
```

**2. Add to `furniture.py`:**
```python
FURNITURE_TILE_MAPPING = {
    "my_furniture": "my_furniture",  # item_id -> tile_type
}

# If multi-tile:
FURNITURE_SIZES = {
    "my_furniture": (2, 1),  # width, height
}
```

**3. Add to `grid_arcade.py` furniture_tiles list:**
```python
furniture_tiles = [
    # ... existing furniture ...
    "my_furniture",
]
```

**4. Add sprite:**
- Single-tile: `assets/furniture/my_furniture.png` (64x64)
- Multi-tile: `assets/furniture/my_furniture.png` (width*64 x height*64)

**5. Add to UI menu (`ui_arcade.py`):**
```python
furniture_submenu = [
    {"label": "My Furniture", "tool": "furn_my_furniture"},
]
```

---

## Adding New Workstations

**1. Define in `buildings.py`:**
```python
BUILDING_TYPES = {
    "my_station": {
        "workstation": True,
        "size": (2, 2),  # width, height
        "recipes": [
            {"id": "craft_thing", "name": "Craft Thing", ...}
        ]
    }
}
```

**2. Add sprite:**
- `assets/workstations/finished_my_station.png`
- Multi-tile: Use full width*height sprite

**3. Add to construction mapping (`grid_arcade.py`):**
```python
construction_to_finished = {
    "my_station": "finished_my_station",
}
```

---

## Performance Guidelines

### Sprite Caching
- All textures are cached in `GridRenderer.texture_cache`
- Cache key: `(tile_type, variation_index)`
- Never reload the same texture twice

### Z-Level Management
- Each Z-level has its own `SpriteList`
- Only current Z-level is drawn
- Switching Z-levels is instant (no rebuild needed)

### Dirty Tile System
- Only changed tiles are rebuilt
- Use `mark_tile_dirty(x, y, z)` when tiles change
- Batch updates when possible

### Debug Mode
- F4: Toggle free build mode
- F7: Spawn wanderers/fixers
- F8: Print construction sites
- F11: Spawn raider
- F12: Toggle berserk mode

---

## Common Pitfalls

### ❌ DON'T: Use Pygame rendering in Arcade code
```python
# WRONG - This is old Pygame code
surface.blit(sprite, (x, y))
pygame.draw.rect(surface, color, rect)
```

### ✅ DO: Use Arcade drawing functions
```python
# CORRECT - Native Arcade rendering
arcade.draw_lrbt_rectangle_filled(x1, x2, y1, y2, color)
sprite = arcade.Sprite()
sprite.texture = texture
sprite_list.append(sprite)
```

### ❌ DON'T: Forget to add furniture to furniture_tiles list
```python
# This will cause furniture to not render!
# Must be in BOTH _add_tile_sprite AND _add_structure_sprite
```

### ✅ DO: Add to both furniture_tiles lists in grid_arcade.py
```python
# In _add_tile_sprite (line ~677)
furniture_tiles = [..., "my_furniture"]

# In _add_structure_sprite (line ~805)
furniture_tiles = [..., "my_furniture"]
```

### ❌ DON'T: Use hardcoded tile type mappings
```python
# WRONG - Hardcoded instrument list
if furniture_item_id in ("drum_kit", "scrap_guitar", ...):
    tile_type = f"{furniture_item_id}_placed"
```

### ✅ DO: Use FURNITURE_TILE_MAPPING
```python
# CORRECT - Uses centralized mapping
from furniture import FURNITURE_TILE_MAPPING
tile_type = FURNITURE_TILE_MAPPING.get(furniture_item_id, furniture_item_id)
```

---

## Testing Checklist

When adding new visual elements:

- [ ] Sprite file exists in correct folder
- [ ] Sprite dimensions match tile size (64x64 or multiples)
- [ ] Added to appropriate mapping dictionary
- [ ] Added to furniture_tiles list (if furniture)
- [ ] Construction mapping added (if buildable)
- [ ] UI menu entry added
- [ ] Test placement in-game
- [ ] Test rendering at different zoom levels
- [ ] Test Z-level switching
- [ ] Verify no console errors

---

## Future Improvements

### Planned Features
- Combat visual feedback (red halos, bounce animations)
- Room type indicators
- Job visualization (colonists show what they're doing)
- Weather effects
- Day/night lighting

### Architecture Goals
- Keep all rendering in Arcade
- Maintain 60 FPS at all zoom levels
- Support 4K resolution
- Minimize texture reloads
- Clean separation: game logic vs rendering

---

## Questions?

If you're unsure about a rendering pattern:
1. Check existing working examples in `grid_arcade.py` or `ui_arcade*.py`
2. Follow the patterns in this document
3. Test thoroughly before committing

**Remember:** Consistency is key for rapid iteration!
