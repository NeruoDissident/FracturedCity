# Inner Corner Sprites (Variants 13-16) - For Dirt Patches

## Overview

These 4 new variants are **INNER corners** (concave) for dirt patches/blobs.
Your existing variants 3-6 (outer corners) are preserved for future use.

**All sprites:** 64x64 pixels, transparent PNG, 10 pixels from edge

---

## Variant 13: Inner Corner NW (Top-Left Cut)

**File:** `ground_dirt_overlay_autotile_13.png`

**Edges:** 
- Bottom: Dirt extends to edge (0px transparent)
- Right: Dirt extends to edge (0px transparent)
- Top-Left: Small concave cut (transparent)

**Description:**
- Dirt fills MOST of the tile (~80%)
- Small concave curve cut from **top-left corner**
- Transparent area: ~20x20 pixels in top-left
- Feather edges 2-3 pixels for smooth blend

**Visual:**
```
░░░░░░░░▓▓▓▓▓▓▓▓  ░ = Transparent (concave cut)
░░░░░░▓▓▓▓▓▓▓▓▓▓  ▓ = Dirt
░░░░▓▓▓▓▓▓▓▓▓▓▓▓  
░░▓▓▓▓▓▓▓▓▓▓▓▓▓▓  Concave curve in top-left
▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  Dirt extends to bottom/right
▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
```

**When used:** Dirt to the South and East (this tile is top-left of blob)

**Photoshop steps:**
1. Fill 64x64 with dirt texture
2. Select top-left corner (~20x20 area)
3. Use soft round brush to erase concave curve
4. Feather selection 2-3 pixels
5. Save as PNG with transparency

---

## Variant 14: Inner Corner NE (Top-Right Cut)

**File:** `ground_dirt_overlay_autotile_14.png`

**Edges:**
- Bottom: Dirt extends to edge
- Left: Dirt extends to edge
- Top-Right: Small concave cut (transparent)

**Visual:**
```
▓▓▓▓▓▓▓▓░░░░░░░░  Concave cut in top-right
▓▓▓▓▓▓▓▓▓▓░░░░░░  Dirt fills most of tile
▓▓▓▓▓▓▓▓▓▓▓▓░░░░  
▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░  
▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  Dirt extends to bottom/left
▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
```

**When used:** Dirt to the South and West (this tile is top-right of blob)

---

## Variant 15: Inner Corner SW (Bottom-Left Cut)

**File:** `ground_dirt_overlay_autotile_15.png`

**Edges:**
- Top: Dirt extends to edge
- Right: Dirt extends to edge
- Bottom-Left: Small concave cut (transparent)

**Visual:**
```
▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  Dirt extends to top/right
▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░  
▓▓▓▓▓▓▓▓▓▓▓▓░░░░  Concave cut in bottom-left
▓▓▓▓▓▓▓▓▓▓░░░░░░
▓▓▓▓▓▓▓▓░░░░░░░░
```

**When used:** Dirt to the North and East (this tile is bottom-left of blob)

---

## Variant 16: Inner Corner SE (Bottom-Right Cut)

**File:** `ground_dirt_overlay_autotile_16.png`

**Edges:**
- Top: Dirt extends to edge
- Left: Dirt extends to edge
- Bottom-Right: Small concave cut (transparent)

**Visual:**
```
▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  Dirt extends to top/left
▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
░░▓▓▓▓▓▓▓▓▓▓▓▓▓▓  
░░░░▓▓▓▓▓▓▓▓▓▓▓▓  Concave cut in bottom-right
░░░░░░▓▓▓▓▓▓▓▓▓▓
░░░░░░░░▓▓▓▓▓▓▓▓
```

**When used:** Dirt to the North and West (this tile is bottom-right of blob)

---

## Quick Reference

**All 4 inner corners:**
- Start with full 64x64 dirt
- Cut small concave curve (~20x20) from specified corner
- Leave other edges with dirt extending to edge (0px transparent)
- Feather 2-3 pixels
- Save as transparent PNG

**Corner positions:**
- **Variant 13:** Cut from **top-left**
- **Variant 14:** Cut from **top-right**
- **Variant 15:** Cut from **bottom-left**
- **Variant 16:** Cut from **bottom-right**

---

## Test Pattern

A 2x2 dirt blob will use:
```
[Variant 13] [Variant 14]
[Variant 15] [Variant 16]
```

With concrete cutting small curves into each corner, forming a rounded blob.

---

## Complete Variant List

**You'll have 17 total variants (0-16):**

- **0:** Isolated
- **1:** Horizontal straight
- **2:** Vertical straight
- **3-6:** Outer corners (for roads/walls - already created ✓)
- **7-10:** T-junctions (already created ✓)
- **11:** 4-way cross (already created ✓)
- **12:** End cap (already created ✓)
- **13-16:** Inner corners (for patches - create these 4 new ones)

---

**Save all 4 new sprites to `assets/tiles/` and test!**
