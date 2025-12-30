# Testing Wall Autotiles - Quick Start Guide

## ✅ System is Ready to Test!

All code changes are complete. You just need to add the wall sprites.

---

## Step 1: Upscale Your 32x32 Sprites

You have a PowerShell script ready: `upscale_sprites.ps1`

**To run it:**

1. Open PowerShell in the FracturedCity root folder
2. Run: `.\upscale_sprites.ps1`
3. Choose option 1 (assets/tiles/walls/)
4. Confirm to upscale

**What it does:**
- Finds all PNG files in the folder
- Upscales 32x32 → 64x64 using nearest-neighbor (preserves pixel art)
- Overwrites original files
- Skips files already 64x64

**Alternative - Manual upscale:**
If you prefer to upscale manually, use any image editor with nearest-neighbor/point sampling.

---

## Step 2: Place Your Wall Sprites

**Create folder:** `assets/tiles/walls/`

**Place 13 sprites:**
```
finished_wall_autotile_0.png   (isolated - single wall tile)
finished_wall_autotile_1.png   (horizontal - E-W connection)
finished_wall_autotile_2.png   (vertical - N-S connection)
finished_wall_autotile_3.png   (corner NW)
finished_wall_autotile_4.png   (corner NE)
finished_wall_autotile_5.png   (corner SW)
finished_wall_autotile_6.png   (corner SE)
finished_wall_autotile_7.png   (T-junction North)
finished_wall_autotile_8.png   (T-junction South)
finished_wall_autotile_9.png   (T-junction East)
finished_wall_autotile_10.png  (T-junction West)
finished_wall_autotile_11.png  (4-way cross)
finished_wall_autotile_12.png  (end cap)
```

**Quick test:** Start with just 0, 1, 2 (isolated, horizontal, vertical) to verify the system works.

---

## Step 3: Test In-Game

**Run the game:**
```powershell
python main_arcade.py
```

**What to look for:**
- Buildings should have walls with autotiling
- Corners should use corner sprites
- T-junctions where walls meet
- Straight walls use horizontal/vertical sprites

**Debug output:**
The console will show if wall sprites are loading:
```
[GridRenderer] Processing finished_wall_autotile tile at (x, y)
```

---

## Code Changes Made

### ✅ Updated Files:

1. **`autotiling.py`**
   - Added `finished_wall_autotile` to connection groups
   - Walls now autotile using 13-tile path system

2. **`grid_arcade.py`**
   - Sprite paths look in `assets/tiles/walls/` folder
   - Supports `finished_wall_autotile_X.png` naming

3. **`city_generator.py`**
   - Buildings use `finished_wall_autotile` instead of `finished_wall`

4. **`colonist.py`**
   - Construction completion uses `finished_wall_autotile`

5. **`resources.py`**
   - Building generation uses `finished_wall_autotile`

---

## Troubleshooting

### Walls not rendering?
- Check console for sprite loading errors
- Verify sprites are in `assets/tiles/walls/` folder
- Verify naming: `finished_wall_autotile_0.png` (not `wall_autotile_0.png`)

### Walls not autotiling?
- Check if sprites are 64x64 (game expects this size)
- Verify all 13 variants exist
- Check console for autotile debug messages

### Sprites look pixelated/blurry?
- Make sure upscaling used nearest-neighbor (not bilinear/bicubic)
- PowerShell script uses correct method automatically

---

## Current System Status

**Working:**
- ✅ Concrete base layer
- ✅ Dirt overlays (47-tile blob autotiling)
- ✅ Roads (13-tile path autotiling)
- ✅ Wall autotiling system (ready for sprites)

**Using placeholders:**
- ⏳ Walls (need 13 autotile sprites)
- ⏳ Floors (using 5 simple variations - no autotiling)
- ⏳ Workstations (single sprites)
- ⏳ Furniture (single sprites)

---

## Next Steps After Walls Work

1. **Test wall autotiling** - verify all 13 variants work
2. **Keep floors simple** - 5 variations, no autotiling (for now)
3. **Multi-tile structures** - implement bed=2x1, forge=3x3 system
4. **Replace placeholders** - hand-draw final assets at your pace

---

## Placeholder Workflow

**Your approach is smart:**
1. Use 32x32 placeholders to test scale and layout
2. Build entire game with placeholders
3. Replace with hand-drawn 64x64 assets later
4. System handles both seamlessly

**Benefits:**
- See final vision of scale early
- Test gameplay before art is done
- Easy to swap sprites later
- Focus on mechanics first, art second

---

**Ready to test!** Just upscale and place your wall sprites, then run the game.
