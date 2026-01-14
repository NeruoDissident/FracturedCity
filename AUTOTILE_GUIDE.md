# Autotiling Guide - Fractured City

**Last Updated:** January 10, 2026

## Overview

Fractured City uses two autotiling systems for seamless tile connections:
1. **13-Tile System** - Roads, sidewalks, bridges
2. **47-Tile Blob System** - Dirt overlays, organic transitions

---

## 13-Tile Road Autotiling

### Concept
Roads connect to adjacent road tiles. Each sprite represents a specific connection pattern.

### Tile Size
**64x64 pixels** per sprite

### File Naming
```
{type}_autotile_{variant}.png
```

**Examples:**
- `street_autotile_0.png` through `street_autotile_12.png`
- `sidewalk_autotile_0.png` through `sidewalk_autotile_12.png`

---

### Variant Specifications

#### Variant 0: Isolated
**Connections:** None  
**Visual:** Single tile, no connections
```
    [empty]
[empty] [ROAD] [empty]
    [empty]
```

#### Variant 1: Horizontal
**Connections:** East + West  
**Visual:** Road running left-right
```
    [empty]
[ROAD]━━━━━[ROAD]
    [empty]
```

#### Variant 2: Vertical
**Connections:** North + South  
**Visual:** Road running up-down
```
  [ROAD]
    ┃
  [ROAD]
```

#### Variant 3: Corner NW
**Connections:** South + East  
**Visual:** Bottom-right corner
```
[empty] [empty]
[empty]    ┐
         [ROAD]
```

#### Variant 4: Corner NE
**Connections:** South + West  
**Visual:** Bottom-left corner
```
[empty] [empty]
   ┌    [empty]
[ROAD]
```

#### Variant 5: Corner SW
**Connections:** North + East  
**Visual:** Top-right corner
```
         [ROAD]
[empty]    └
[empty] [ROAD]
```

#### Variant 6: Corner SE
**Connections:** North + West  
**Visual:** Top-left corner
```
[ROAD]
   ┘    [empty]
[empty] [empty]
```

#### Variant 7: T-Junction North
**Connections:** South + East + West  
**Visual:** T pointing up
```
    [empty]
[ROAD]━┴━[ROAD]
    [ROAD]
```

#### Variant 8: T-Junction South
**Connections:** North + East + West  
**Visual:** T pointing down
```
    [ROAD]
[ROAD]━┬━[ROAD]
    [empty]
```

#### Variant 9: T-Junction East
**Connections:** North + South + West  
**Visual:** T pointing right
```
  [ROAD]
    ├━[ROAD]
  [ROAD]
```

#### Variant 10: T-Junction West
**Connections:** North + South + East  
**Visual:** T pointing left
```
  [ROAD]
[ROAD]━┤
  [ROAD]
```

#### Variant 11: 4-Way Intersection
**Connections:** All directions  
**Visual:** Cross intersection
```
    [ROAD]
[ROAD]━┼━[ROAD]
    [ROAD]
```

#### Variant 12: End Cap
**Connections:** One direction only  
**Visual:** Dead end (4 rotations needed)

---

## 47-Tile Blob Autotiling

### Concept
Organic transitions using bitmask-based tile selection. Each tile represents a unique neighbor configuration.

### Use Cases
- Dirt overlay on concrete
- Grass on pavement
- Organic terrain transitions

### Bitmask System

Each adjacent tile contributes to a bitmask:
```
  1   2   4
  8  [X]  16
 32  64  128
```

**Total combinations:** 256 (2^8)  
**Reduced to 47 unique visual patterns** (rotations/mirrors handled)

### Key Variants

#### Core Patterns
- **0:** Isolated blob
- **1-4:** Single edges (N, E, S, W)
- **5-12:** Corners (convex)
- **13-16:** Inner corners (concave) - **CRITICAL FOR SMOOTH EDGES**
- **17-44:** Complex combinations
- **45-46:** Special cases

### Inner Corners (13-16)

**Most important for smooth organic edges:**

- **Variant 13:** Inner corner NE (bitmask 80)
- **Variant 14:** Inner corner NW (bitmask 68)
- **Variant 15:** Inner corner SE (bitmask 20)
- **Variant 16:** Inner corner SW (bitmask 5)

These create smooth concave curves where dirt "wraps around" concrete.

### File Naming
```
ground_dirt_overlay_autotile_{variant}.png
```

**Examples:**
- `ground_dirt_overlay_autotile_0.png` (isolated)
- `ground_dirt_overlay_autotile_13.png` (inner corner NE)
- `ground_dirt_overlay_autotile_46.png` (complex pattern)

---

## Implementation

### Road Autotiling (`autotiling.py`)

```python
def get_road_autotile_variant(grid, x, y, z):
    """
    Returns 0-12 based on adjacent road connections.
    Checks N, S, E, W neighbors.
    """
    # Check connections
    n = is_road(x, y+1, z)
    s = is_road(x, y-1, z)
    e = is_road(x+1, y, z)
    w = is_road(x-1, y, z)
    
    # Return variant based on pattern
    # (see autotiling.py for full logic)
```

### Blob Autotiling

```python
def get_blob_autotile_variant(grid, x, y, z):
    """
    Returns 0-46 based on 8-neighbor bitmask.
    Checks all 8 surrounding tiles.
    """
    # Build bitmask from neighbors
    bitmask = 0
    if has_dirt(x, y+1, z): bitmask |= 2    # N
    if has_dirt(x+1, y, z): bitmask |= 16   # E
    # ... (all 8 neighbors)
    
    # Map bitmask to variant (0-46)
    return BITMASK_TO_VARIANT[bitmask]
```

---

## Creating Autotile Sprites

### For 13-Tile Roads

1. Create base road texture (64x64)
2. For each variant (0-12):
   - Draw road connections to specified edges
   - Leave other edges empty/clean
   - Ensure seamless tiling when connected

### For 47-Tile Blobs

1. Create base dirt texture
2. For each variant:
   - Draw dirt where bitmask indicates neighbors
   - Create smooth edges where no neighbors
   - Handle inner corners (13-16) carefully for smooth curves

**Tip:** Use a template generator or reference existing blob tilesets (Godot, RPG Maker)

---

## Testing Autotiles

### Visual Verification
```python
# In-game debug overlay
python main.py
# Press F6 to toggle autotile debug view
```

### Common Issues

**Roads not connecting:**
- Check variant 1 (horizontal) connects left-right edges
- Check variant 2 (vertical) connects top-bottom edges

**Dirt edges look jagged:**
- Missing inner corner variants (13-16)
- Bitmask mapping incorrect

**Tiles appear random:**
- Autotile logic not running
- Sprite files named incorrectly

---

## Performance

- **Autotile calculation:** Once per tile placement/removal
- **Sprite lookup:** Cached after first load
- **Rendering:** GPU batched, no performance impact

---

## See Also

- `autotiling.py` - Autotiling logic implementation
- `grid_arcade.py` - Rendering with autotiles
- `SPRITE_SYSTEM.md` - Overall sprite organization
