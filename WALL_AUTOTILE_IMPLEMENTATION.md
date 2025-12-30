# Wall Autotiling Implementation Guide

## Summary

Implementing 13-tile top-down wall autotiling system. Easy to upgrade to directional walls later.

---

## What I've Done (Code Changes)

### 1. **Updated `autotiling.py`**
- Added `finished_wall_autotile` to connection groups
- Walls now connect to other walls during autotiling
- Added `_autotile` keyword to `should_autotile()` function

### 2. **Updated `grid_arcade.py`**
- Added sprite path logic for walls: `assets/tiles/walls/finished_wall_autotile_X.png`
- Walls organized in subfolder like roads and dirt

---

## What You Need to Do (Sprites)

### **Create 13 Wall Sprites**

**Location:** `assets/tiles/walls/`

**Naming:**
```
finished_wall_autotile_0.png   - Isolated (no connections)
finished_wall_autotile_1.png   - Horizontal (E-W connection)
finished_wall_autotile_2.png   - Vertical (N-S connection)
finished_wall_autotile_3.png   - Corner NW (connects S and E)
finished_wall_autotile_4.png   - Corner NE (connects S and W)
finished_wall_autotile_5.png   - Corner SW (connects N and E)
finished_wall_autotile_6.png   - Corner SE (connects N and W)
finished_wall_autotile_7.png   - T-junction North (connects S, E, W)
finished_wall_autotile_8.png   - T-junction South (connects N, E, W)
finished_wall_autotile_9.png   - T-junction East (connects N, S, W)
finished_wall_autotile_10.png  - T-junction West (connects N, S, E)
finished_wall_autotile_11.png  - 4-way cross (connects all 4 directions)
finished_wall_autotile_12.png  - End cap (one connection)
```

**Size:** 64x64 pixels

**Style:** 
- Top-down view (flat square)
- Dark metal/concrete texture
- Industrial cyberpunk aesthetic
- Panels, rivets, seams
- Weathered, worn look

**Visual Guide:**
```
Variant 0 (Isolated):    Variant 1 (Horizontal):   Variant 2 (Vertical):
    ▓▓▓▓                     ════════                    ║║║║
    ▓▓▓▓                     ════════                    ║║║║
    ▓▓▓▓                     ════════                    ║║║║
    ▓▓▓▓                     ════════                    ║║║║

Variant 3 (Corner NW):   Variant 7 (T-junction N):  Variant 11 (Cross):
    ▓▓▓▓                         ║                          ║
    ▓▓══                     ════╬════                  ════╬════
    ▓▓║                          ║                          ║
    ▓▓║                          ║                          ║
```

---

## Migration Strategy

### **Option A: Replace Old Walls (Recommended)**

Change all wall placement to use autotile naming:

**Files to update:**
1. `city_generator.py` - lines 633, 647, 663
2. `colonist.py` - line 2890
3. `resources.py` - line 996

**Change:**
```python
# OLD:
grid.set_tile(x, y, "finished_wall", z=0)

# NEW:
grid.set_tile(x, y, "finished_wall_autotile", z=0)
```

**Benefits:**
- Clean, consistent system
- All walls use autotiling
- No legacy code

**Drawback:**
- Need to update existing saves (or they'll have old walls)

---

### **Option B: Support Both (Backward Compatible)**

Keep old wall system working, add new autotile system:

**In `grid_arcade.py` construction mapping:**
```python
construction_to_finished = {
    "wall": "finished_wall_autotile",  # New construction uses autotile
    # ... rest stays same
}
```

**Benefits:**
- Existing saves still work
- Old walls render with variations
- New walls use autotiling

**Drawback:**
- Two systems running
- More complex

---

## Recommended Approach: Option A (Replace)

Since you're early in development, cleanest to just switch to autotiling everywhere.

---

## Testing Plan

### **Step 1: Create Sprites**
1. Create folder: `assets/tiles/walls/`
2. Create 13 sprites (start with simple versions)
3. Test with basic shapes (straight lines, corners)

### **Step 2: Update Code**
1. Change wall placement to use `finished_wall_autotile`
2. Test in city generator
3. Test in construction system

### **Step 3: Verify**
1. Build a room - walls should connect smoothly
2. Check corners autotile correctly
3. Check T-junctions where walls meet
4. Check 4-way intersections

---

## Upgrade Path to Directional Walls (Future)

When you want to add posters/details on walls:

### **Step 1: Add Direction Property**
```python
# When placing wall, store direction
grid.set_tile(x, y, "finished_wall_autotile", z=0)
grid.wall_directions[(x, y, 0)] = "north"  # or south/east/west
```

### **Step 2: Create Directional Sprites**
```
assets/tiles/walls/
  finished_wall_north_autotile_0.png
  finished_wall_south_autotile_0.png
  finished_wall_east_autotile_0.png
  finished_wall_west_autotile_0.png
```

### **Step 3: Update Sprite Path Logic**
```python
if wall_direction:
    sprite_path = f"assets/tiles/walls/finished_wall_{direction}_autotile_{variant}.png"
else:
    sprite_path = f"assets/tiles/walls/finished_wall_autotile_{variant}.png"
```

**That's it!** Autotiling logic stays the same, just different sprite sets.

---

## Sprite Creation Tips

### **Start Simple**
1. Create variants 0, 1, 2 first (isolated, horizontal, vertical)
2. Test those work
3. Add corners (3-6)
4. Add junctions (7-11)
5. Add end cap (12)

### **Design Consistency**
- Keep panel lines consistent across variants
- Corners should look natural
- T-junctions should blend smoothly
- Use same color palette for all variants

### **Test Pattern**
Build this in-game to test all variants:
```
▓▓▓▓▓▓▓
▓     ▓
▓  ▓  ▓
▓     ▓
▓▓▓▓▓▓▓
```
Should use: edges, corners, T-junctions, and cross

---

## Current Status

✅ **Code ready** - autotiling system implemented
⏳ **Sprites needed** - 13 wall autotile sprites
⏳ **Migration needed** - update wall placement code

Once you create the sprites, I'll update the placement code and we can test!

---

## Next: Floors

After walls work, we'll decide on floors:
- Keep simple variations (current system)?
- Or add edge detection autotiling?

Then move to multi-tile workstations/furniture (bed=2x1, forge=3x3).
