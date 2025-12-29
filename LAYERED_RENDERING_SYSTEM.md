# Layered Rendering System - Transparent Overlays

## Overview

The entire grid is filled with **base concrete tiles**, then all other materials are rendered as **transparent PNG overlays** on top. This creates seamless blending and eliminates hard edges.

---

## How It Works

### **Rendering Order**

1. **Base Layer (Z=0):** `ground_concrete_0.png` fills entire grid
2. **Overlay Layer (Z=1):** Transparent material sprites render on top
   - Roads
   - Dirt
   - Grass
   - Rubble
   - Walls
   - Buildings
   - Everything else

### **Result**

- Base concrete shows through transparent areas
- Materials blend naturally at edges
- No hard tile boundaries
- Smooth, painterly look

---

## Sprite Requirements

### **Base Concrete (Opaque)**

**Files:**
- `ground_concrete_0.png` - Full opaque concrete tile
- `ground_concrete_1.png` - Variation (optional)
- `ground_concrete_2.png` - Variation (optional)

**Properties:**
- 64x64 pixels
- **Fully opaque** (no transparency)
- Fills entire tile
- Gray concrete texture

---

### **Material Overlays (Transparent)**

All overlay sprites are **64x64 PNG with transparency** showing base concrete at edges.

#### **Roads (13 sprites)**

**Files:**
```
street_autotile_0.png   # Isolated road patch (transparent edges)
street_autotile_1.png   # Horizontal (transparent top/bottom)
street_autotile_2.png   # Vertical (transparent left/right)
street_autotile_3.png   # Corner NW (transparent top-left)
street_autotile_4.png   # Corner NE (transparent top-right)
street_autotile_5.png   # Corner SW (transparent bottom-left)
street_autotile_6.png   # Corner SE (transparent bottom-right)
street_autotile_7.png   # T-junction N (transparent top)
street_autotile_8.png   # T-junction S (transparent bottom)
street_autotile_9.png   # T-junction E (transparent right)
street_autotile_10.png  # T-junction W (transparent left)
street_autotile_11.png  # 4-way cross (no transparency)
street_autotile_12.png  # End cap (transparent one side)
```

**Properties:**
- Dark asphalt with dashed center line
- **Transparent edges** where concrete should show
- Smooth fade/blend at boundaries

#### **Dirt (13 sprites)**

**Files:**
```
ground_dirt_autotile_0.png through ground_dirt_autotile_12.png
```

**Properties:**
- Brown/tan dirt texture
- **Transparent edges** blending to concrete
- Rough, natural look

#### **Grass/Overgrown (13 sprites)**

**Files:**
```
ground_overgrown_autotile_0.png through ground_overgrown_autotile_12.png
```

**Properties:**
- Green vegetation
- **Transparent edges** showing concrete underneath
- Organic, irregular edges

#### **Rubble (13 sprites)**

**Files:**
```
ground_rubble_autotile_0.png through ground_rubble_autotile_12.png
```

**Properties:**
- Broken concrete chunks, debris
- **Transparent edges** revealing base concrete
- Scattered, chaotic look

#### **Walls (13 sprites)**

**Files:**
```
wall_exterior_autotile_0.png through wall_exterior_autotile_12.png
```

**Properties:**
- Building walls
- **Transparent background** (only wall visible)
- Connects seamlessly with other walls

---

## Creating Transparent Overlays

### **Photoshop Workflow**

#### **Step 1: Trim Your Road Sprites**

1. Open existing `street_autotile_1.png` (horizontal road)
2. Select road portion (center ~30 pixels)
3. Delete everything else (make transparent)
4. **Feather edges** by 2-3 pixels for smooth blend
5. Save as transparent PNG

**Before (Opaque):**
```
████████████████  Full tile, opaque edges
████▓▓▓▓▓▓██████  Road in center
████████████████
```

**After (Transparent):**
```
░░░░░░░░░░░░░░░░  Transparent edges
░░░░▓▓▓▓▓▓░░░░░░  Road in center, feathered
░░░░░░░░░░░░░░░░  Base concrete shows through
```

#### **Step 2: Create Edge Variants**

For each of the 13 autotile variants:
1. Determine which edges should be transparent
2. Mask/erase those edges
3. Feather for smooth blend
4. Save as transparent PNG

**Example - Corner NW (variant 3):**
```
░░░░░░░░░░░░░░░░  Top edge: transparent
░░░░░░░░░░░░░░░░  
░░░░░░░░▓▓▓▓▓▓▓▓  Road curves from bottom to right
░░░░░░░░▓▓▓▓▓▓▓▓  Left edge: transparent
```

#### **Step 3: Test Layering**

1. Open `ground_concrete_0.png` as base layer
2. Place transparent overlay on top
3. Verify concrete shows through transparent areas
4. Adjust feathering/transparency as needed

---

## Material Priority (Rendering Order)

When multiple materials overlap, render in this order (bottom to top):

1. **Base Concrete** (always bottom)
2. **Dirt**
3. **Grass/Overgrown**
4. **Rubble**
5. **Roads** (streets on top of ground)
6. **Walls** (buildings on top of everything)
7. **Objects** (furniture, resources, etc.)

---

## Advantages of This System

✅ **Seamless Blending** - No hard edges between materials
✅ **Easy to Create** - Just trim existing sprites to transparent
✅ **Flexible** - Add new materials without recreating everything
✅ **Performance** - GPU handles transparency efficiently
✅ **Consistent Base** - Concrete always shows through gaps
✅ **Additive** - Add materials incrementally

---

## Implementation Status

✅ **Rendering System Updated**
- Base concrete layer renders first
- Material overlays render on top
- Transparency supported

🔄 **Next Steps:**
1. Trim road sprites to transparent PNGs
2. Test layered road rendering
3. Create dirt overlay sprites (13)
4. Create grass overlay sprites (13)
5. Create rubble overlay sprites (13)
6. Create wall overlay sprites (13)

---

## Sprite Checklist

### **Phase 1: Roads (Trim Existing)**
- [ ] Trim `street_autotile_0.png` to transparent overlay
- [ ] Trim `street_autotile_1.png` to transparent overlay
- [ ] Trim `street_autotile_2.png` to transparent overlay
- [ ] Trim `street_autotile_3.png` to transparent overlay
- [ ] Trim `street_autotile_4.png` to transparent overlay
- [ ] Trim `street_autotile_5.png` to transparent overlay
- [ ] Trim `street_autotile_6.png` to transparent overlay
- [ ] Trim `street_autotile_7.png` to transparent overlay
- [ ] Trim `street_autotile_8.png` to transparent overlay
- [ ] Trim `street_autotile_9.png` to transparent overlay
- [ ] Trim `street_autotile_10.png` to transparent overlay
- [ ] Trim `street_autotile_11.png` to transparent overlay
- [ ] Trim `street_autotile_12.png` to transparent overlay

### **Phase 2: Dirt Overlays (Create New)**
- [ ] `ground_dirt_autotile_0.png` through `_12.png` (13 sprites)

### **Phase 3: Grass Overlays (Create New)**
- [ ] `ground_overgrown_autotile_0.png` through `_12.png` (13 sprites)

### **Phase 4: Rubble Overlays (Create New)**
- [ ] `ground_rubble_autotile_0.png` through `_12.png` (13 sprites)

### **Phase 5: Wall Overlays (Create New)**
- [ ] `wall_exterior_autotile_0.png` through `_12.png` (13 sprites)

---

## Testing

After trimming road sprites:

```bash
python main_arcade.py
```

You should see:
- ✅ Concrete base visible everywhere
- ✅ Roads rendered as overlays on top
- ✅ Smooth blending at road edges
- ✅ No hard tile boundaries

---

**Start by trimming your existing road sprites to transparent PNGs. The rendering system is ready!**
