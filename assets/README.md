# Assets Folder

Drop your sprite files here!

## Quick Start

### Folder Structure
```
assets/
  tiles/          # All tile sprites (floors, walls, furniture, etc.)
  colonists/      # Colonist directional sprites
  buildings/      # Building/workstation sprites
  items/          # Item sprites (components, instruments, etc.)
```

### Priority Sprites (Start Here)

**Colonists (3 sprites):**
- `colonists/default_north.png` - Back view
- `colonists/default_east.png` - Side view (right)
- `colonists/default_west.png` - Side view (left)

**Common Tiles (2-8 sprites each for variety):**
- `tiles/finished_floor_0.png`, `tiles/finished_floor_1.png`, etc.
- `tiles/finished_wall_0.png`, `tiles/finished_wall_1.png`, etc.

**Instruments (5 sprites):**
- `tiles/scrap_guitar_placed.png`
- `tiles/drum_kit_placed.png`
- `tiles/synth_placed.png`
- `tiles/harmonica_placed.png`
- `tiles/amp_placed.png`

### Sprite Specs
- **Size:** 64x64 pixels recommended
- **Format:** PNG with transparency
- **Style:** Cyberpunk wasteland aesthetic (like your example!)

### How It Works
1. Drop sprites in the appropriate folder
2. Run the game
3. Sprites load automatically
4. Missing sprites fall back to procedural drawing

**No code changes needed - just add sprites and they'll appear!**

See `SPRITE_GUIDE.md` in the root folder for complete documentation.
