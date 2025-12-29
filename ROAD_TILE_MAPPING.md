# Road Tile Mapping Guide for topdown_itch.png

## Sprite Sheet Analysis

Looking at the sprite sheet, the road tiles appear to be **64x64 pixels each**.

### Top Section - Road Patterns (What We Need)

The top rows contain various road intersection patterns. Here's what I can identify:

**Row 1 (y=0):**
- Curved roads with smooth corners
- Various intersection types
- These are the autotile patterns we need

**Row 2 (y=64):**
- More road variations
- Different road types (solid, dashed lines)

**Row 3 (y=128):**
- Additional road patterns
- Crosswalks and intersections

### Tile Size
- Each tile: **64x64 pixels**
- Grid layout in sprite sheet

---

## Quick Extraction Method

Since the sprite sheet has many road variations, here's the fastest approach:

### Option A: Use Python Script
Run the extraction tool I created:
```bash
python extract_tiles.py
```

Choose mode 1 (interactive) and the sprite sheet will open. Then enter coordinates for each variant.

### Option B: Manual Extraction (Fastest for Testing)
1. Open `topdown_itch.png` in an image editor (GIMP, Photoshop, Paint.NET)
2. Use selection tool to grab 64x64 tiles
3. Save each as `street_autotile_0.png` through `street_autotile_12.png`
4. Place in `assets/tiles/` folder

### Option C: Start with Just 4 Essential Tiles
To test quickly, extract just these 4 critical tiles:
- **Variant 1:** Straight horizontal (any horizontal road piece)
- **Variant 2:** Straight vertical (any vertical road piece)  
- **Variant 3:** Corner (any 90° corner)
- **Variant 11:** 4-way intersection (the + intersection)

The game will use these for basic functionality and fall back to variant 0 for missing tiles.

---

## Recommended Coordinates (Estimated)

Based on visual inspection of the sprite sheet, here are approximate coordinates:

**NOTE:** These are estimates. You'll need to verify by opening the image and measuring exact positions.

```python
# Format: (variant_index, x_pixels, y_pixels)
# Measuring from top-left corner of sprite sheet

# Basic patterns (priority)
(1, 192, 0),    # Straight horizontal (estimated)
(2, 256, 0),    # Straight vertical (estimated)
(3, 320, 0),    # Corner NW (estimated)
(11, 384, 0),   # 4-way cross (estimated)

# Full set (measure these)
(0, 0, 0),      # Isolated
(4, 64, 0),     # Corner NE
(5, 128, 0),    # Corner SW
(6, 192, 0),    # Corner SE
(7, 256, 0),    # T-junction N
(8, 320, 0),    # T-junction S
(9, 384, 0),    # T-junction E
(10, 448, 0),   # T-junction W
(12, 512, 0),   # End cap
```

---

## Testing

Once you have at least 4 tiles extracted:
1. Place them in `assets/tiles/`
2. Restart the game
3. Streets should now show proper corners and intersections!

If a variant is missing, the game falls back to the old `street_0.png` sprite.
