# Dirt Autotile Overlay Sprites - Complete Specification

## Naming Convention

```
ground_dirt_overlay_autotile_{variant}.png
```

**13 variants (0-12)** matching the 13-tile blob autotiling system.

---

## Sprite Specifications (64x64 pixels, Transparent PNG)

### **Variant 0: Isolated Patch**
**File:** `ground_dirt_overlay_autotile_0.png`

**Edges:** All 4 sides transparent (top, bottom, left, right)

**Description:**
- Dirt patch surrounded by concrete on all sides
- Transparent border: 8-10 pixels from each edge
- Center: Brown/tan dirt texture (44x44 pixel area)
- Edges: Rough, irregular transition (not circular)
- Small rocks/pebbles scattered in dirt
- Feather edges 2-3 pixels for smooth blend

**Visual:**
```
░░░░░░░░░░░░░░░░  ░ = Transparent (concrete shows)
░░░░░░░░░░░░░░░░  ▓ = Dirt texture
░░░░▓▓▓▓▓▓░░░░░░  
░░░▓▓▓▓▓▓▓▓░░░░░  Center dirt patch
░░▓▓▓▓▓▓▓▓▓▓░░░░  Irregular rough edges
░░▓▓▓▓▓▓▓▓▓▓░░░░
░░░▓▓▓▓▓▓▓▓░░░░░
░░░░▓▓▓▓▓▓░░░░░░
░░░░░░░░░░░░░░░░
```

---

### **Variant 1: Horizontal Straight**
**File:** `ground_dirt_overlay_autotile_1.png`

**Edges:** Top and bottom transparent, left and right have dirt

**Description:**
- Horizontal dirt strip connecting left-right
- Transparent border: 8-10 pixels from top and bottom
- Left and right edges: Dirt extends to edge (0px transparent)
- Center: Brown/tan dirt texture (64x44 pixel area)
- Rough horizontal edges (not straight lines)

**Visual:**
```
░░░░░░░░░░░░░░░░  ░ = Transparent
▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  ▓ = Dirt (extends to edges)
▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  
▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  Horizontal strip
▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
░░░░░░░░░░░░░░░░
```

---

### **Variant 2: Vertical Straight**
**File:** `ground_dirt_overlay_autotile_2.png`

**Edges:** Left and right transparent, top and bottom have dirt

**Description:**
- Vertical dirt strip connecting top-bottom
- Transparent border: 8-10 pixels from left and right
- Top and bottom edges: Dirt extends to edge (0px transparent)
- Center: Brown/tan dirt texture (44x64 pixel area)
- Rough vertical edges (not straight lines)

**Visual:**
```
░░░░▓▓▓▓▓▓▓▓░░░░  ░ = Transparent
░░░░▓▓▓▓▓▓▓▓░░░░  ▓ = Dirt (extends to top/bottom)
░░░░▓▓▓▓▓▓▓▓░░░░  
░░░░▓▓▓▓▓▓▓▓░░░░  Vertical strip
░░░░▓▓▓▓▓▓▓▓░░░░
░░░░▓▓▓▓▓▓▓▓░░░░
░░░░▓▓▓▓▓▓▓▓░░░░
```

---

### **Variant 3: Outer Corner - Top-Left**
**File:** `ground_dirt_overlay_autotile_3.png`

**Edges:** Top and left transparent, bottom and right have dirt

**Description:**
- Dirt curves from bottom edge to right edge
- Transparent border: 8-10 pixels from top and left
- Bottom and right edges: Dirt extends to edge
- Curve: Smooth arc from bottom-right area
- Rough organic curve (not perfect circle)

**Visual:**
```
░░░░░░░░░░░░░░░░  ░ = Transparent (top-left)
░░░░░░░░░░░░░░░░  ▓ = Dirt
░░░░░░░░░░▓▓▓▓▓▓  
░░░░░░░░▓▓▓▓▓▓▓▓  Curves from bottom to right
░░░░░░▓▓▓▓▓▓▓▓▓▓
░░░░▓▓▓▓▓▓▓▓▓▓▓▓
▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
```

---

### **Variant 4: Outer Corner - Top-Right**
**File:** `ground_dirt_overlay_autotile_4.png`

**Edges:** Top and right transparent, bottom and left have dirt

**Description:**
- Dirt curves from bottom edge to left edge
- Transparent border: 8-10 pixels from top and right
- Bottom and left edges: Dirt extends to edge
- Curve: Smooth arc from bottom-left area
- Rough organic curve

**Visual:**
```
░░░░░░░░░░░░░░░░  ░ = Transparent (top-right)
░░░░░░░░░░░░░░░░  ▓ = Dirt
▓▓▓▓▓▓░░░░░░░░░░  
▓▓▓▓▓▓▓▓░░░░░░░░  Curves from bottom to left
▓▓▓▓▓▓▓▓▓▓░░░░░░
▓▓▓▓▓▓▓▓▓▓▓▓░░░░
▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
```

---

### **Variant 5: Outer Corner - Bottom-Left**
**File:** `ground_dirt_overlay_autotile_5.png`

**Edges:** Bottom and left transparent, top and right have dirt

**Description:**
- Dirt curves from top edge to right edge
- Transparent border: 8-10 pixels from bottom and left
- Top and right edges: Dirt extends to edge
- Curve: Smooth arc from top-right area
- Rough organic curve

**Visual:**
```
▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  ▓ = Dirt
░░░░▓▓▓▓▓▓▓▓▓▓▓▓  
░░░░░░▓▓▓▓▓▓▓▓▓▓  Curves from top to right
░░░░░░░░▓▓▓▓▓▓▓▓
░░░░░░░░░░▓▓▓▓▓▓
░░░░░░░░░░░░░░░░  ░ = Transparent (bottom-left)
░░░░░░░░░░░░░░░░
```

---

### **Variant 6: Outer Corner - Bottom-Right**
**File:** `ground_dirt_overlay_autotile_6.png`

**Edges:** Bottom and right transparent, top and left have dirt

**Description:**
- Dirt curves from top edge to left edge
- Transparent border: 8-10 pixels from bottom and right
- Top and left edges: Dirt extends to edge
- Curve: Smooth arc from top-left area
- Rough organic curve

**Visual:**
```
▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  ▓ = Dirt
▓▓▓▓▓▓▓▓▓▓▓▓░░░░  
▓▓▓▓▓▓▓▓▓▓░░░░░░  Curves from top to left
▓▓▓▓▓▓▓▓░░░░░░░░
▓▓▓▓▓▓░░░░░░░░░░
░░░░░░░░░░░░░░░░  ░ = Transparent (bottom-right)
░░░░░░░░░░░░░░░░
```

---

### **Variant 7: T-Junction - Opens North**
**File:** `ground_dirt_overlay_autotile_7.png`

**Edges:** Top transparent, bottom/left/right have dirt

**Description:**
- Dirt connects from bottom, left, and right edges
- Transparent border: 8-10 pixels from top only
- Bottom, left, right edges: Dirt extends to edge
- Top edge: Rough irregular transition to transparent
- Forms T-shape opening upward

**Visual:**
```
░░░░░░░░░░░░░░░░  ░ = Transparent (top)
▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  ▓ = Dirt
▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  
▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  T-junction opening north
▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
```

---

### **Variant 8: T-Junction - Opens South**
**File:** `ground_dirt_overlay_autotile_8.png`

**Edges:** Bottom transparent, top/left/right have dirt

**Description:**
- Dirt connects from top, left, and right edges
- Transparent border: 8-10 pixels from bottom only
- Top, left, right edges: Dirt extends to edge
- Bottom edge: Rough irregular transition to transparent
- Forms T-shape opening downward

**Visual:**
```
▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  ▓ = Dirt
▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  
▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  T-junction opening south
▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
░░░░░░░░░░░░░░░░  ░ = Transparent (bottom)
```

---

### **Variant 9: T-Junction - Opens East**
**File:** `ground_dirt_overlay_autotile_9.png`

**Edges:** Right transparent, top/bottom/left have dirt

**Description:**
- Dirt connects from top, bottom, and left edges
- Transparent border: 8-10 pixels from right only
- Top, bottom, left edges: Dirt extends to edge
- Right edge: Rough irregular transition to transparent
- Forms T-shape opening rightward

**Visual:**
```
▓▓▓▓▓▓▓▓▓▓░░░░░░  ▓ = Dirt
▓▓▓▓▓▓▓▓▓▓░░░░░░  ░ = Transparent (right)
▓▓▓▓▓▓▓▓▓▓░░░░░░  
▓▓▓▓▓▓▓▓▓▓░░░░░░  T-junction opening east
▓▓▓▓▓▓▓▓▓▓░░░░░░
▓▓▓▓▓▓▓▓▓▓░░░░░░
▓▓▓▓▓▓▓▓▓▓░░░░░░
```

---

### **Variant 10: T-Junction - Opens West**
**File:** `ground_dirt_overlay_autotile_10.png`

**Edges:** Left transparent, top/bottom/right have dirt

**Description:**
- Dirt connects from top, bottom, and right edges
- Transparent border: 8-10 pixels from left only
- Top, bottom, right edges: Dirt extends to edge
- Left edge: Rough irregular transition to transparent
- Forms T-shape opening leftward

**Visual:**
```
░░░░░░▓▓▓▓▓▓▓▓▓▓  ░ = Transparent (left)
░░░░░░▓▓▓▓▓▓▓▓▓▓  ▓ = Dirt
░░░░░░▓▓▓▓▓▓▓▓▓▓  
░░░░░░▓▓▓▓▓▓▓▓▓▓  T-junction opening west
░░░░░░▓▓▓▓▓▓▓▓▓▓
░░░░░░▓▓▓▓▓▓▓▓▓▓
░░░░░░▓▓▓▓▓▓▓▓▓▓
```

---

### **Variant 11: 4-Way Cross**
**File:** `ground_dirt_overlay_autotile_11.png`

**Edges:** All 4 sides have dirt (no transparency at edges)

**Description:**
- Dirt connects from all 4 directions
- No transparent borders (dirt extends to all edges)
- Full 64x64 dirt texture
- Rough texture throughout
- Small rocks/pebbles scattered

**Visual:**
```
▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  ▓ = Dirt (full tile)
▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  
▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  
▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  4-way cross
▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  No transparent areas
▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
```

---

### **Variant 12: End Cap / Dead End**
**File:** `ground_dirt_overlay_autotile_12.png`

**Edges:** 3 sides transparent, 1 side has dirt

**Description:**
- Dirt extends from one edge (e.g., bottom)
- Transparent border: 8-10 pixels from top, left, right
- Bottom edge: Dirt extends to edge
- Dirt tapers toward center
- Rough irregular shape

**Visual:**
```
░░░░░░░░░░░░░░░░  ░ = Transparent
░░░░░░░░░░░░░░░░  ▓ = Dirt
░░░░░▓▓▓▓▓░░░░░░  
░░░░▓▓▓▓▓▓▓░░░░░  Dirt extends from bottom
░░░▓▓▓▓▓▓▓▓▓░░░░
░░▓▓▓▓▓▓▓▓▓▓▓░░░
▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
```

---

## Dirt Texture Guidelines

### **Color Palette:**
- Base: Brown/tan (#8B7355, #A0826D, #6B5344)
- Highlights: Lighter tan (#C4A57B)
- Shadows: Dark brown (#4A3728)
- Accents: Small gray rocks (#7A7A7A)

### **Texture Details:**
- Rough, uneven surface
- Small pebbles scattered (2-4 pixels)
- Subtle noise/grain for organic look
- Darker patches for depth
- Lighter patches for highlights
- NO grass or vegetation (pure dirt)

### **Edge Treatment:**
- Feather transparent edges 2-3 pixels
- Irregular, rough transitions (not smooth curves)
- Small dirt specks extending into transparent area
- Natural, organic shapes (avoid geometric)

---

## Photoshop Workflow

1. **Create 64x64 canvas** with transparent background
2. **Draw dirt texture** in appropriate area (see variant specs)
3. **Add noise/grain** for organic texture
4. **Add small rocks** (2-4 pixel gray dots)
5. **Feather edges** 2-3 pixels where transparent
6. **Add roughness** to edges (erase small chunks irregularly)
7. **Save as PNG** with transparency preserved

---

## Testing

After creating all 13 sprites, test in-game:

```bash
python main_arcade.py
```

You should see:
- ✅ Dirt patches with autotiling
- ✅ Smooth transitions at edges
- ✅ Concrete visible through transparent areas
- ✅ Corners, T-junctions, crosses all working
- ✅ Rough, natural appearance

---

## File Checklist

- [ ] ground_dirt_overlay_autotile_0.png (Isolated)
- [ ] ground_dirt_overlay_autotile_1.png (Horizontal)
- [ ] ground_dirt_overlay_autotile_2.png (Vertical)
- [ ] ground_dirt_overlay_autotile_3.png (Corner TL)
- [ ] ground_dirt_overlay_autotile_4.png (Corner TR)
- [ ] ground_dirt_overlay_autotile_5.png (Corner BL)
- [ ] ground_dirt_overlay_autotile_6.png (Corner BR)
- [ ] ground_dirt_overlay_autotile_7.png (T-North)
- [ ] ground_dirt_overlay_autotile_8.png (T-South)
- [ ] ground_dirt_overlay_autotile_9.png (T-East)
- [ ] ground_dirt_overlay_autotile_10.png (T-West)
- [ ] ground_dirt_overlay_autotile_11.png (4-Way)
- [ ] ground_dirt_overlay_autotile_12.png (End Cap)

Save all files to: `assets/tiles/`
