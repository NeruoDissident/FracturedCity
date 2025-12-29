# 47-Tile Blob Autotiling System - Complete Specification

## Overview

This is the industry-standard blob autotiling system used in Terraria, RPG Maker, Stardew Valley, etc.

**All sprites:** 64x64 pixels, transparent PNG, dirt texture with concrete showing through where specified.

**Naming:** `ground_dirt_overlay_autotile_0.png` through `ground_dirt_overlay_autotile_46.png`

---

## Tile Categories

### **Category 1: Full Tile (1 sprite)**

**Variant 0: Full/Center**
- All 8 neighbors are dirt
- Entire 64x64 tile is dirt
- No transparent areas
```
▓▓▓
▓▓▓
▓▓▓
```

---

### **Category 2: Edges (4 sprites)**

**Variant 1: North Edge**
- Dirt to South, concrete to North
- Top edge fades to transparent
- Bottom extends to edge
```
░░░
▓▓▓
▓▓▓
```

**Variant 2: South Edge**
- Dirt to North, concrete to South
- Bottom edge fades to transparent
- Top extends to edge
```
▓▓▓
▓▓▓
░░░
```

**Variant 3: East Edge**
- Dirt to West, concrete to East
- Right edge fades to transparent
- Left extends to edge
```
▓▓░
▓▓░
▓▓░
```

**Variant 4: West Edge**
- Dirt to East, concrete to West
- Left edge fades to transparent
- Right extends to edge
```
░▓▓
░▓▓
░▓▓
```

---

### **Category 3: Outer Corners (4 sprites)**

**Variant 5: Outer Corner NW**
- Dirt to SE, concrete to NW
- Small dirt in bottom-right corner
- Smooth curve in top-left
```
░░░
░▓▓
░▓▓
```

**Variant 6: Outer Corner NE**
- Dirt to SW, concrete to NE
- Small dirt in bottom-left corner
- Smooth curve in top-right
```
░░░
▓▓░
▓▓░
```

**Variant 7: Outer Corner SW**
- Dirt to NE, concrete to SW
- Small dirt in top-right corner
- Smooth curve in bottom-left
```
░▓▓
░▓▓
░░░
```

**Variant 8: Outer Corner SE**
- Dirt to NW, concrete to SE
- Small dirt in top-left corner
- Smooth curve in bottom-right
```
▓▓░
▓▓░
░░░
```

---

### **Category 4: Inner Corners (4 sprites)**

**Variant 9: Inner Corner NW**
- Dirt fills most of tile
- Small concave cut from top-left (~20x20 pixels)
- Concrete cuts into dirt from NW
```
░░▓▓▓
░▓▓▓▓
▓▓▓▓▓
▓▓▓▓▓
▓▓▓▓▓
```

**Variant 10: Inner Corner NE**
- Dirt fills most of tile
- Small concave cut from top-right
- Concrete cuts into dirt from NE
```
▓▓▓░░
▓▓▓▓░
▓▓▓▓▓
▓▓▓▓▓
▓▓▓▓▓
```

**Variant 11: Inner Corner SW**
- Dirt fills most of tile
- Small concave cut from bottom-left
- Concrete cuts into dirt from SW
```
▓▓▓▓▓
▓▓▓▓▓
▓▓▓▓▓
░▓▓▓▓
░░▓▓▓
```

**Variant 12: Inner Corner SE**
- Dirt fills most of tile
- Small concave cut from bottom-right
- Concrete cuts into dirt from SE
```
▓▓▓▓▓
▓▓▓▓▓
▓▓▓▓▓
▓▓▓▓░
▓▓▓░░
```

---

### **Category 5: T-Junctions (4 sprites)**

**Variant 13: T-Junction North**
- Dirt to S, E, W
- Concrete to N
- Top edge transparent, sides extend
```
░░░
▓▓▓
▓▓▓
```

**Variant 14: T-Junction South**
- Dirt to N, E, W
- Concrete to S
- Bottom edge transparent, sides extend
```
▓▓▓
▓▓▓
░░░
```

**Variant 15: T-Junction East**
- Dirt to N, S, W
- Concrete to E
- Right edge transparent, top/bottom extend
```
▓▓░
▓▓░
▓▓░
```

**Variant 16: T-Junction West**
- Dirt to N, S, E
- Concrete to W
- Left edge transparent, top/bottom extend
```
░▓▓
░▓▓
░▓▓
```

---

### **Category 6: Edge + Single Inner Corner (8 sprites)**

**Variant 17: North Edge + NW Inner**
- North edge transparent
- Small concave cut from NW corner
- Dirt extends S, E, W except NW cut
```
░░▓▓▓
░▓▓▓▓
▓▓▓▓▓
▓▓▓▓▓
```

**Variant 18: North Edge + NE Inner**
- North edge transparent
- Small concave cut from NE corner
```
▓▓▓░░
▓▓▓▓░
▓▓▓▓▓
▓▓▓▓▓
```

**Variant 19: South Edge + SW Inner**
- South edge transparent
- Small concave cut from SW corner
```
▓▓▓▓▓
▓▓▓▓▓
░▓▓▓▓
░░▓▓▓
```

**Variant 20: South Edge + SE Inner**
- South edge transparent
- Small concave cut from SE corner
```
▓▓▓▓▓
▓▓▓▓▓
▓▓▓▓░
▓▓▓░░
```

**Variant 21: East Edge + NE Inner**
- East edge transparent
- Small concave cut from NE corner
```
▓▓▓░░
▓▓▓▓░
▓▓▓▓░
▓▓▓▓░
```

**Variant 22: East Edge + SE Inner**
- East edge transparent
- Small concave cut from SE corner
```
▓▓▓▓░
▓▓▓▓░
▓▓▓▓░
▓▓▓░░
```

**Variant 23: West Edge + NW Inner**
- West edge transparent
- Small concave cut from NW corner
```
░░▓▓▓
░▓▓▓▓
░▓▓▓▓
░▓▓▓▓
```

**Variant 24: West Edge + SW Inner**
- West edge transparent
- Small concave cut from SW corner
```
░▓▓▓▓
░▓▓▓▓
░▓▓▓▓
░░▓▓▓
```

---

### **Category 7: Double Inner Corners - Opposite (4 sprites)**

**Variant 25: NW + SE Inner**
- Concave cuts from NW and SE corners
- Dirt fills rest
```
░░▓▓▓
░▓▓▓▓
▓▓▓▓▓
▓▓▓▓░
▓▓▓░░
```

**Variant 26: NE + SW Inner**
- Concave cuts from NE and SW corners
```
▓▓▓░░
▓▓▓▓░
▓▓▓▓▓
░▓▓▓▓
░░▓▓▓
```

**Variant 27: NW + NE Inner**
- Concave cuts from both top corners
```
░░▓░░
░▓▓▓░
▓▓▓▓▓
▓▓▓▓▓
▓▓▓▓▓
```

**Variant 28: SW + SE Inner**
- Concave cuts from both bottom corners
```
▓▓▓▓▓
▓▓▓▓▓
▓▓▓▓▓
░▓▓▓░
░░▓░░
```

---

### **Category 8: Double Inner Corners - Adjacent (4 sprites)**

**Variant 29: NW + NE Inner (same as 27)**
Already covered above

**Variant 30: SW + SE Inner (same as 28)**
Already covered above

**Variant 31: NW + SW Inner**
- Concave cuts from both left corners
```
░░▓▓▓
░▓▓▓▓
▓▓▓▓▓
░▓▓▓▓
░░▓▓▓
```

**Variant 32: NE + SE Inner**
- Concave cuts from both right corners
```
▓▓▓░░
▓▓▓▓░
▓▓▓▓▓
▓▓▓▓░
▓▓▓░░
```

---

### **Category 9: Triple Inner Corners (4 sprites)**

**Variant 33: All except NE**
- Concave cuts from NW, SW, SE
- Only NE corner is full
```
░░▓▓▓
░▓▓▓▓
▓▓▓▓▓
░▓▓▓░
░░▓░░
```

**Variant 34: All except NW**
- Concave cuts from NE, SW, SE
```
▓▓▓░░
▓▓▓▓░
▓▓▓▓▓
░▓▓▓░
░░▓░░
```

**Variant 35: All except SE**
- Concave cuts from NW, NE, SW
```
░░▓░░
░▓▓▓░
▓▓▓▓▓
░▓▓▓▓
░░▓▓▓
```

**Variant 36: All except SW**
- Concave cuts from NW, NE, SE
```
░░▓░░
░▓▓▓░
▓▓▓▓▓
▓▓▓▓░
▓▓▓░░
```

---

### **Category 10: Quadruple Inner Corner (1 sprite)**

**Variant 37: All 4 Inner Corners**
- Concave cuts from all 4 corners
- Dirt only in center cross shape
```
░░▓░░
░▓▓▓░
▓▓▓▓▓
░▓▓▓░
░░▓░░
```

---

### **Category 11: Isolated/Single (1 sprite)**

**Variant 38: Isolated**
- No neighbors
- Small dirt blob in center
- Fades to transparent on all sides
```
░░░░░
░▓▓▓░
░▓▓▓░
░▓▓▓░
░░░░░
```

---

### **Category 12: Outer Corners + Inner Corner (8 sprites)**

**Variant 39: Outer NW + Inner SE**
```
░░░
░▓▓
░▓░
```

**Variant 40: Outer NE + Inner SW**
```
░░░
▓▓░
░▓░
```

**Variant 41: Outer SW + Inner NE**
```
░▓░
░▓▓
░░░
```

**Variant 42: Outer SE + Inner NW**
```
░▓░
▓▓░
░░░
```

**Variant 43: Outer NW + Inner NE**
```
░░░
░▓░
░▓▓
```

**Variant 44: Outer NE + Inner NW**
```
░░░
░▓░
▓▓░
```

**Variant 45: Outer SW + Inner SE**
```
░▓▓
░▓░
░░░
```

**Variant 46: Outer SE + Inner SW**
```
▓▓░
░▓░
░░░
```

---

## Creation Workflow (Photoshop)

1. **Start with full 64x64 dirt texture** (variant 0)
2. **For each variant:**
   - Duplicate the full tile
   - Use layer mask or eraser
   - Cut transparent areas as specified
   - Feather edges 2-3 pixels for smooth blend
   - Save as `ground_dirt_overlay_autotile_X.png`

3. **Test incrementally:**
   - Create variants 0-12 first (basic set)
   - Test in game
   - Create remaining variants 13-46
   - Final test

---

## Priority Order

**Phase 1 (Essential - 13 sprites):**
- 0: Full
- 1-4: Edges
- 5-8: Outer corners
- 9-12: Inner corners

**Phase 2 (Smooth edges - 8 sprites):**
- 17-24: Edge + inner corner combinations

**Phase 3 (Complex corners - 13 sprites):**
- 25-37: Double/triple/quad inner corners

**Phase 4 (Perfect blending - 9 sprites):**
- 38-46: Outer + inner combinations, isolated

---

**Start with Phase 1 (13 sprites) and test. Then add more phases as needed.**
