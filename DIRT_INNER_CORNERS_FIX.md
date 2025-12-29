# CORRECTED: Inner Corner Sprites for Dirt Patches

## The Problem

Your current corner sprites (variants 3-6) are **OUTER corners** (for paths/roads).
For dirt **PATCHES/BLOBS**, you need **INNER corners** (concave, not convex).

---

## What You Have Now (OUTER CORNERS - Wrong for patches)

### Variant 3 (Current - OUTER corner):
```
░░░░░░░░░░░░░░░░  Top-left is empty
░░░░░░░░░░░░░░░░  Dirt curves OUTWARD
░░░░░░░░░░▓▓▓▓▓▓  from bottom-right
░░░░░░░░▓▓▓▓▓▓▓▓  
░░░░░░▓▓▓▓▓▓▓▓▓▓  This makes a PATH corner
░░░░▓▓▓▓▓▓▓▓▓▓▓▓  Not a PATCH corner
▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
```

This creates **outward curves** like roads. Wrong for dirt blobs.

---

## What You Need (INNER CORNERS - Correct for patches)

### Variant 3 (INNER Corner NW - Top-Left Cut):
**File:** `ground_dirt_overlay_autotile_3.png`

**Edges:** Bottom and right have dirt extending to edge, top-left has small concave cut

**Description:**
- Dirt fills MOST of the tile (80%+)
- Small concave curve cut from **top-left corner**
- Bottom edge: Dirt extends to edge (full width)
- Right edge: Dirt extends to edge (full height)
- Top-left: Transparent concave curve (concrete cuts in)

**Visual:**
```
░░░░░░░░▓▓▓▓▓▓▓▓  ░ = Transparent (small cut)
░░░░░░▓▓▓▓▓▓▓▓▓▓  ▓ = Dirt (fills most of tile)
░░░░▓▓▓▓▓▓▓▓▓▓▓▓  
░░▓▓▓▓▓▓▓▓▓▓▓▓▓▓  Concave curve in top-left
▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  Dirt extends to bottom/right edges
▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
```

**When to use:** Dirt to the South and East (this tile is top-left of blob)

---

### Variant 4 (INNER Corner NE - Top-Right Cut):
**File:** `ground_dirt_overlay_autotile_4.png`

**Visual:**
```
▓▓▓▓▓▓▓▓░░░░░░░░  Small concave cut in top-right
▓▓▓▓▓▓▓▓▓▓░░░░░░  Dirt fills most of tile
▓▓▓▓▓▓▓▓▓▓▓▓░░░░  
▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░  Concave curve in top-right
▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  Dirt extends to bottom/left edges
▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
```

**When to use:** Dirt to the South and West (this tile is top-right of blob)

---

### Variant 5 (INNER Corner SW - Bottom-Left Cut):
**File:** `ground_dirt_overlay_autotile_5.png`

**Visual:**
```
▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  Dirt extends to top/right edges
▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░  Concave curve in bottom-left
▓▓▓▓▓▓▓▓▓▓▓▓░░░░
▓▓▓▓▓▓▓▓▓▓░░░░░░  Small concave cut in bottom-left
▓▓▓▓▓▓▓▓░░░░░░░░
```

**When to use:** Dirt to the North and East (this tile is bottom-left of blob)

---

### Variant 6 (INNER Corner SE - Bottom-Right Cut):
**File:** `ground_dirt_overlay_autotile_6.png`

**Visual:**
```
▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  Dirt extends to top/left edges
▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
░░▓▓▓▓▓▓▓▓▓▓▓▓▓▓  Concave curve in bottom-right
░░░░▓▓▓▓▓▓▓▓▓▓▓▓
░░░░░░▓▓▓▓▓▓▓▓▓▓  Small concave cut in bottom-right
░░░░░░░░▓▓▓▓▓▓▓▓
```

**When to use:** Dirt to the North and West (this tile is bottom-right of blob)

---

## Key Difference

**OUTER corners (what you have):**
- Dirt in small area
- Transparent fills most of tile
- Curves extend OUTWARD
- Good for: Roads, paths, lines

**INNER corners (what you need):**
- Dirt fills most of tile
- Transparent is small concave cut
- Curves cut INWARD
- Good for: Patches, blobs, areas

---

## Quick Fix

You need to **recreate variants 3, 4, 5, and 6** with the corners inverted:

1. Open your dirt texture (full 64x64 dirt)
2. Cut a small **concave curve** from the appropriate corner
3. Leave dirt extending to the other edges
4. Save as the variant number

**Example for variant 3:**
- Start with full 64x64 dirt
- Cut concave curve from **top-left** (about 20x20 pixel area)
- Leave bottom and right edges full dirt
- Feather the curve 2-3 pixels

---

## Test Pattern

After fixing, a 2x2 dirt blob should look like:
```
[Variant 3] [Variant 4]
[Variant 5] [Variant 6]
```

With concrete cutting small curves into each corner, forming a natural rounded blob.

---

**The autotiling code is correct now - you just need to recreate the corner sprites as INNER corners instead of OUTER corners!**
