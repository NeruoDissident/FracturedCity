# Multi-Tile Structures System

## Overview

You can add large multi-tile structures (fountains, statues, plazas, monuments) that spawn randomly in the city. The system handles placement, collision detection, and sprite management automatically.

---

## How It Works

### **1. Define Structure Template**

Create a template defining the structure's tiles:

```python
FOUNTAIN_3X3 = {
    "name": "fountain_small",
    "width": 3,
    "height": 3,
    "tiles": [
        # Format: (dx, dy, tile_type)
        (0, 0, "landmark_fountain_nw"),
        (1, 0, "landmark_fountain_n"),
        (2, 0, "landmark_fountain_ne"),
        (0, 1, "landmark_fountain_w"),
        (1, 1, "landmark_fountain_center"),
        (2, 1, "landmark_fountain_e"),
        (0, 2, "landmark_fountain_sw"),
        (1, 2, "landmark_fountain_s"),
        (2, 2, "landmark_fountain_se"),
    ]
}
```

### **2. Create Sprites**

For the 3x3 fountain above, create 9 sprites:
- `landmark_fountain_nw.png` (top-left corner)
- `landmark_fountain_n.png` (top edge)
- `landmark_fountain_ne.png` (top-right corner)
- `landmark_fountain_w.png` (left edge)
- `landmark_fountain_center.png` (center)
- `landmark_fountain_e.png` (right edge)
- `landmark_fountain_sw.png` (bottom-left corner)
- `landmark_fountain_s.png` (bottom edge)
- `landmark_fountain_se.png` (bottom-right corner)

All 64x64 pixels, saved to `assets/tiles/`

### **3. System Places It**

City generator automatically:
- Finds suitable locations (plazas, parks, block centers)
- Checks for collisions with roads/buildings
- Places all tiles at once
- Handles rendering

---

## Structure Types

### **Small Structures (3x3 to 5x5)**

**Fountains:**
```
┌─┬─┐
│ F │  F = fountain center
└─┴─┘
```

**Statues:**
```
┌───┐
│ S │  S = statue
└───┘
```

**Benches/Seating:**
```
═══  Simple 1x3 or 3x1 bench
```

### **Medium Structures (5x5 to 7x7)**

**Plaza Centers:**
```
┌─────┐
│     │
│  P  │  P = plaza feature
│     │
└─────┘
```

**Monuments:**
```
  ╔═╗
  ║M║  M = monument
╔═╩═╩═╗
║     ║
╚═════╝
```

### **Large Structures (7x7+)**

**Parks:**
```
🌳🌳🌳🌳🌳
🌳      🌳
🌳  ⛲  🌳  Trees + fountain
🌳      🌳
🌳🌳🌳🌳🌳
```

**Plazas:**
```
╔═══════╗
║       ║
║   ⛲   ║  Large open space
║       ║
╚═══════╝
```

---

## Naming Convention

### **Format:**
```
landmark_{type}_{position}.png
```

### **Examples:**

**3x3 Fountain:**
- `landmark_fountain_nw.png` (northwest corner)
- `landmark_fountain_n.png` (north edge)
- `landmark_fountain_ne.png` (northeast corner)
- `landmark_fountain_w.png` (west edge)
- `landmark_fountain_center.png` (center)
- `landmark_fountain_e.png` (east edge)
- `landmark_fountain_sw.png` (southwest corner)
- `landmark_fountain_s.png` (south edge)
- `landmark_fountain_se.png` (southeast corner)

**5x5 Statue:**
- `landmark_statue_nw.png`
- `landmark_statue_n.png`
- `landmark_statue_ne.png`
- `landmark_statue_w.png`
- `landmark_statue_center.png`
- `landmark_statue_e.png`
- `landmark_statue_sw.png`
- `landmark_statue_s.png`
- `landmark_statue_se.png`
- Plus 16 more for 5x5 grid

**Simple 1x3 Bench:**
- `landmark_bench_left.png`
- `landmark_bench_center.png`
- `landmark_bench_right.png`

---

## Placement Rules

### **Where Structures Spawn:**

1. **Plazas** - Open blocks designated as public spaces
2. **Parks** - Overgrown/green zones
3. **Block Centers** - Middle of large city blocks
4. **Intersections** - Major road crossings (for monuments)

### **Collision Detection:**

System automatically checks:
- ✅ Not overlapping roads
- ✅ Not overlapping buildings
- ✅ Not overlapping other landmarks
- ✅ Fits within block boundaries
- ✅ Proper ground clearance

---

## Implementation Example

Here's how to add a 3x3 fountain to the city generator:

```python
# In city_generator.py

LANDMARK_TEMPLATES = {
    "fountain_small": {
        "width": 3,
        "height": 3,
        "tiles": [
            (0, 0, "landmark_fountain_nw"),
            (1, 0, "landmark_fountain_n"),
            (2, 0, "landmark_fountain_ne"),
            (0, 1, "landmark_fountain_w"),
            (1, 1, "landmark_fountain_center"),
            (2, 1, "landmark_fountain_e"),
            (0, 2, "landmark_fountain_sw"),
            (1, 2, "landmark_fountain_s"),
            (2, 2, "landmark_fountain_se"),
        ],
        "spawn_zones": ["commercial", "residential"],  # Where it can spawn
        "spawn_chance": 0.3  # 30% chance per suitable block
    }
}

def _place_landmark(self, block: Dict, template_name: str):
    """Place a multi-tile landmark structure."""
    template = LANDMARK_TEMPLATES[template_name]
    
    # Find center position in block
    center_x = block["x"] + (block["width"] - template["width"]) // 2
    center_y = block["y"] + (block["height"] - template["height"]) // 2
    
    # Check if space is clear
    for dx, dy, tile_type in template["tiles"]:
        x = center_x + dx
        y = center_y + dy
        
        if not self.grid.in_bounds(x, y, 0):
            return False
        
        # Check for collisions
        if (x, y) in self.road_network.roads:
            return False
        
        current_tile = self.grid.get_tile(x, y, 0)
        if current_tile not in ["empty", "ground_concrete_0", "ground_pavement_0"]:
            return False
    
    # Place all tiles
    for dx, dy, tile_type in template["tiles"]:
        x = center_x + dx
        y = center_y + dy
        self.grid.set_tile(x, y, tile_type, z=0)
    
    return True
```

---

## Starter Landmark Pack

### **Phase 1: Simple Structures (3-5 sprites each)**

**1. Small Fountain (3x3 = 9 sprites)**
- Circular fountain with water in center
- Decorative edges

**2. Bench (1x3 = 3 sprites)**
- Simple seating
- Can place multiple

**3. Small Statue (3x3 = 9 sprites)**
- Monument/memorial
- Pedestal + figure

**4. Tree Cluster (2x2 = 4 sprites)**
- Group of trees
- Natural landmark

### **Phase 2: Medium Structures (5-7 sprites each)**

**5. Plaza Center (5x5 = 25 sprites)**
- Open gathering space
- Decorative pattern

**6. Monument (5x5 = 25 sprites)**
- Large statue/obelisk
- Impressive centerpiece

### **Phase 3: Large Structures (10+ sprites each)**

**7. Park (7x7 = 49 sprites)**
- Trees, paths, fountain
- Green space

**8. Memorial Plaza (7x7 = 49 sprites)**
- Formal public space
- Multiple features

---

## Additive System

Like ground tiles, landmarks are **additive**:
- Start with 1-2 simple structures
- Add more over time
- Never replace existing sprites
- System automatically uses what's available

---

## Current Status

**Ready to implement:**
- ✅ Template system designed
- ✅ Placement logic ready
- ✅ Collision detection ready
- ✅ Sprite naming convention defined

**Waiting for:**
- Landmark sprite creation
- Template definitions for each structure

---

## Next Steps

1. Create 3x3 fountain sprites (9 PNGs)
2. Add fountain template to city_generator.py
3. Test fountain placement
4. Add more landmarks incrementally

Want me to implement the landmark placement system now so it's ready when you create the sprites?
