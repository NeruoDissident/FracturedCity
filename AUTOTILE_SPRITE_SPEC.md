# 13-Tile Autotile Sprite Specification

## Overview

You need to create **13 PNG files** for road autotiling. Each sprite is **64x64 pixels** and represents a different connection pattern.

---

## File Names & Specifications

### **Variant 0: Isolated Tile**
**File:** `street_autotile_0.png`  
**Connections:** None  
**Description:** Single road tile with no connections  
**Visual:** 
```
    [empty]
[empty] [ROAD] [empty]
    [empty]
```
Draw a road tile that looks good standalone. Could be a manhole cover, a patch of asphalt, or just a square of road texture.

---

### **Variant 1: Horizontal Straight**
**File:** `street_autotile_1.png`  
**Connections:** East + West  
**Description:** Road running left-right  
**Visual:**
```
    [empty]
[ROAD]━━━━━[ROAD]
    [empty]
```
Road connects to left and right edges. Top and bottom edges should NOT have road.

---

### **Variant 2: Vertical Straight**
**File:** `street_autotile_2.png`  
**Connections:** North + South  
**Description:** Road running up-down  
**Visual:**
```
  [ROAD]
    ┃
  [ROAD]
    ┃
  [ROAD]
```
Road connects to top and bottom edges. Left and right edges should NOT have road.

---

### **Variant 3: Corner NW (Top-Right)**
**File:** `street_autotile_3.png`  
**Connections:** South + East  
**Description:** Road turns from bottom to right  
**Visual:**
```
    [empty]
[empty] ┐
      [ROAD]
        ┃
      [ROAD]
```
Road comes from bottom, curves, exits to the right. Top-left corner is empty.

---

### **Variant 4: Corner NE (Top-Left)**
**File:** `street_autotile_4.png`  
**Connections:** South + West  
**Description:** Road turns from bottom to left  
**Visual:**
```
    [empty]
      ┌ [empty]
    [ROAD]
      ┃
    [ROAD]
```
Road comes from bottom, curves, exits to the left. Top-right corner is empty.

---

### **Variant 5: Corner SW (Bottom-Right)**
**File:** `street_autotile_5.png`  
**Connections:** North + East  
**Description:** Road turns from top to right  
**Visual:**
```
    [ROAD]
      ┃
    [ROAD]
      └
[empty] [ROAD]
```
Road comes from top, curves, exits to the right. Bottom-left corner is empty.

---

### **Variant 6: Corner SE (Bottom-Left)**
**File:** `street_autotile_6.png`  
**Connections:** North + West  
**Description:** Road turns from top to left  
**Visual:**
```
  [ROAD]
    ┃
  [ROAD]
    ┘
  [ROAD] [empty]
```
Road comes from top, curves, exits to the left. Bottom-right corner is empty.

---

### **Variant 7: T-Junction North**
**File:** `street_autotile_7.png`  
**Connections:** South + East + West  
**Description:** T-junction with opening at top  
**Visual:**
```
    [empty]
[ROAD]━━┬━━[ROAD]
        ┃
      [ROAD]
```
Road connects left, right, and bottom. Top is open (no road).

---

### **Variant 8: T-Junction South**
**File:** `street_autotile_8.png`  
**Connections:** North + East + West  
**Description:** T-junction with opening at bottom  
**Visual:**
```
      [ROAD]
        ┃
[ROAD]━━┴━━[ROAD]
    [empty]
```
Road connects left, right, and top. Bottom is open (no road).

---

### **Variant 9: T-Junction East**
**File:** `street_autotile_9.png`  
**Connections:** North + South + West  
**Description:** T-junction with opening at right  
**Visual:**
```
    [ROAD]
      ┃
[ROAD]━━┤
      ┃
    [ROAD]
```
Road connects top, bottom, and left. Right is open (no road).

---

### **Variant 10: T-Junction West**
**File:** `street_autotile_10.png`  
**Connections:** North + South + East  
**Description:** T-junction with opening at left  
**Visual:**
```
  [ROAD]
    ┃
    ├━━[ROAD]
    ┃
  [ROAD]
```
Road connects top, bottom, and right. Left is open (no road).

---

### **Variant 11: 4-Way Cross**
**File:** `street_autotile_11.png`  
**Connections:** North + South + East + West  
**Description:** Full intersection  
**Visual:**
```
    [ROAD]
      ┃
[ROAD]━━╋━━[ROAD]
      ┃
    [ROAD]
```
Road connects in all four directions. This is your main intersection tile.

---

### **Variant 12: End Cap**
**File:** `street_autotile_12.png`  
**Connections:** One direction only  
**Description:** Dead end / cul-de-sac  
**Visual:**
```
    [ROAD]
      ┃
    [ROAD]
      ╵
    [empty]
```
Road comes from one direction and stops. Can be any direction - the system will rotate as needed.

---

## Design Guidelines

### **Edge Connections**
- Road MUST extend to the edge of the 64x64 canvas where connections exist
- Road should be **centered** on the tile (roughly 20-30 pixels wide)
- Edges without connections should show ground/background

### **Style Consistency**
- All 13 tiles should use the same road texture/color
- Same road width across all tiles
- Same background/ground texture
- Cyberpunk aesthetic: dark asphalt, maybe subtle grid lines, worn/cracked

### **Corner Smoothness**
- Corners (variants 3-6) should have **smooth curves**, not sharp 90° angles
- Curve radius should be consistent across all corner tiles

### **Intersection Detail**
- 4-way cross (variant 11) can have extra detail: crosswalk lines, center marking, etc.
- T-junctions (variants 7-10) should clearly show which direction is open

### **Cyberpunk Details** (Optional but Awesome)
- Subtle glow/neon lines along road edges
- Worn paint markings
- Cracks and weathering
- Embedded lights or tech elements
- Holographic road markers

---

## Testing Checklist

Once you create all 13 sprites:

1. ✅ All files named correctly (`street_autotile_0.png` through `street_autotile_12.png`)
2. ✅ All files are 64x64 pixels
3. ✅ All files are PNG format with transparency
4. ✅ Road width is consistent across all tiles
5. ✅ Corners are smooth curves (not sharp angles)
6. ✅ Edges connect properly (road extends to canvas edge where needed)
7. ✅ Style is consistent (same colors, textures, details)

---

## Placement

Save all 13 files to:
```
c:\Users\thoma\Fractured City\assets\tiles\
```

Replace the existing `street_autotile_*.png` files (the auto-extracted ones are wrong).

---

## After Creation

Once all 13 sprites are in place:

1. Re-enable autotiling in `autotiling.py` (I'll do this)
2. Restart `main_arcade.py`
3. Streets will have proper corners, intersections, and smooth connections
4. City will look gorgeous with proper urban structure

---

## Future Expansion

Once roads work, we can create autotile sets for:
- **Walls** (building corners and connections)
- **Bridges** (overpasses, multi-level roads)
- **Alleys** (narrow paths between buildings)
- **Sidewalks** (separate from roads)
- **Rails/Tracks** (transit systems)

---

## Visual Reference

Think of games like:
- **Cities: Skylines** - Smooth road connections
- **Factorio** - Clean autotiling system
- **RimWorld** - Simple but effective tile connections
- **Cyberpunk 2077** - Dark asphalt, neon accents, worn urban aesthetic

---

**Ready to create gorgeous cyberpunk roads. No half measures. Let's make this city beautiful.**
