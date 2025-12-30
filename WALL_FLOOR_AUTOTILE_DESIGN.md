# Wall & Floor Autotiling Design Discussion

## Critical Design Decisions

We need to decide on the autotiling approach for walls and floors before creating sprites. This affects how many sprites you need to create and how buildings will look.

---

## Wall Autotiling Options

### **Option 1: 13-Tile Path System** (Like Roads)

**How it works:**
- Checks 4 cardinal neighbors (N, S, E, W)
- 13 variants for different connection patterns
- Simpler, cleaner look

**Variants needed:**
```
0  = Isolated (no connections)
1  = Horizontal (E-W)
2  = Vertical (N-S)
3  = Corner NW (S-E)
4  = Corner NE (S-W)
5  = Corner SW (N-E)
6  = Corner SE (N-W)
7  = T-junction North (S-E-W)
8  = T-junction South (N-E-W)
9  = T-junction East (N-S-W)
10 = T-junction West (N-S-E)
11 = 4-way cross (N-S-E-W)
12 = End cap (one direction)
```

**Visual Example:**
```
    ║
    ║
════╬════
    ║
    ║
```

**Pros:**
- Only 13 sprites to create
- Clean, geometric look
- Perfect for straight walls
- Works well for rectangular buildings

**Cons:**
- No diagonal corner smoothing
- Sharp 90° corners
- Less organic feel

**Best for:**
- Industrial/cyberpunk aesthetic
- Clean, modern buildings
- Grid-based construction

---

### **Option 2: 47-Tile Blob System** (Like Dirt)

**How it works:**
- Checks all 8 neighbors (N, S, E, W, NE, NW, SE, SW)
- 47 variants for all possible patterns
- Handles inner corners and complex shapes

**Variants include:**
- Edges (4)
- Outer corners (4)
- Inner corners (4) - **KEY DIFFERENCE**
- T-junctions (4)
- Edge + inner corner combos (8)
- Double inner corners (4)
- Triple inner corners (4)
- Complex combinations (15)

**Visual Example:**
```
▓▓▓▓▓
▓░░░▓  ← Inner corners create
▓░░░▓     hollow spaces
▓▓▓▓▓
```

**Pros:**
- Smooth corners and transitions
- Handles complex building shapes
- Inner corners for room interiors
- More organic, natural look

**Cons:**
- 47 sprites to create (much more work)
- More complex to design
- Can look "blobby" if not careful

**Best for:**
- Organic/ruined buildings
- Complex room shapes
- Interior wall rendering
- Smooth, rounded aesthetic

---

## Floor Autotiling Options

### **Option 1: Simple Edge Detection**

**How it works:**
- Floors check for adjacent walls
- Different sprites for floor edges vs interior
- 13-16 variants

**Variants:**
```
0  = Interior (no walls nearby)
1  = Edge North (wall to north)
2  = Edge South (wall to south)
3  = Edge East (wall to east)
4  = Edge West (wall to west)
5  = Corner NW (walls N and W)
6  = Corner NE (walls N and E)
7  = Corner SW (walls S and W)
8  = Corner SE (walls S and E)
... + T-junctions and crosses
```

**Visual:**
```
▓▓▓▓▓▓▓
▓═════▓  ← Floor edges meet walls
▓═════▓     Interior is plain
▓▓▓▓▓▓▓
```

**Pros:**
- Clean transition from floor to wall
- Clear room boundaries
- 13-16 sprites (manageable)

**Cons:**
- Requires wall detection logic
- Floors must know about walls

---

### **Option 2: No Autotiling (Simple Variations)**

**How it works:**
- Keep current system (5-8 variations)
- Random variation per tile
- No edge detection

**Pros:**
- Simplest option
- Already implemented
- Only need 5-8 sprites

**Cons:**
- No visual distinction between edges and interior
- Less polished look
- Floors don't "connect" to walls

---

### **Option 3: 47-Tile Blob System**

**How it works:**
- Same as dirt/walls blob system
- Full edge and corner detection
- Smooth transitions

**Pros:**
- Most flexible
- Smooth transitions
- Handles complex shapes

**Cons:**
- 47 sprites (lots of work)
- Overkill for floors?

---

## Recommended Approach

### **For Walls: 13-Tile Path System**

**Reasoning:**
- Walls are linear structures (like roads)
- Buildings are mostly rectangular
- 13 sprites is manageable
- Clean cyberpunk aesthetic
- Matches road system consistency

**Sprite naming:**
```
finished_wall_autotile_0.png
finished_wall_autotile_1.png
...
finished_wall_autotile_12.png
```

**Folder:** `assets/tiles/walls/` (organized like roads)

---

### **For Floors: Simple Edge Detection (13-16 tiles)**

**Reasoning:**
- Floors need to look good against walls
- Edge detection provides polish
- 13-16 sprites is reasonable
- Not as critical as walls

**Sprite naming:**
```
finished_floor_autotile_0.png
finished_floor_autotile_1.png
...
finished_floor_autotile_15.png
```

**Folder:** `assets/tiles/floors/`

**Alternative:** Keep simple variations (5-8) if edge detection is too complex

---

## Visual Style Considerations

### **Walls**

**Cyberpunk Industrial Style:**
- Dark metal/concrete texture
- Rivets, panels, seams
- Weathered, worn look
- Subtle glow/neon accents (optional)
- Rust, scratches, graffiti

**Texture Details:**
- Panel lines at edges
- Corner brackets/reinforcement
- Vertical/horizontal seams
- Damage/wear patterns

**Color Palette:**
- Base: Dark gray (#3A3A3A)
- Highlights: Light gray (#6A6A6A)
- Shadows: Near black (#1A1A1A)
- Accents: Rust orange (#8B4513), neon cyan (#00FFFF)

---

### **Floors**

**Interior Floor Style:**
- Concrete or metal grating
- Grid lines or tile patterns
- Worn, industrial look
- Different from ground concrete (more finished)

**Edge Treatment:**
- Darker edge where floor meets wall
- Shadow/depth effect
- Clear boundary

**Color Palette:**
- Slightly lighter than walls
- Base: Medium gray (#4A4A4A)
- Grid lines: Darker gray (#2A2A2A)
- Highlights: Light gray (#6A6A6A)

---

## Implementation Plan

### **Phase 1: Wall Autotiling**
1. Create 13 wall autotile sprites
2. Update `autotiling.py` to handle walls
3. Add wall connection groups
4. Update `grid_arcade.py` sprite paths
5. Test in-game

### **Phase 2: Floor Autotiling**
1. Decide: Edge detection or simple variations?
2. Create floor sprites (13-16 or 5-8)
3. Implement floor autotiling logic (if edge detection)
4. Update sprite paths
5. Test in-game

### **Phase 3: Multi-Tile Structures** (Next)
1. Design multi-tile system
2. Implement placement logic
3. Create large workstation/furniture sprites

---

## Questions to Answer

### **1. Wall Style**
- **13-tile path system** (recommended) or 47-tile blob?
- Sharp corners or smooth corners?
- How much detail/texture?

### **2. Floor Style**
- Edge detection (13-16 tiles) or simple variations (5-8)?
- Should floors visually connect to walls?
- Same texture as ground concrete or different?

### **3. Sprite Creation**
- Create all 13 wall sprites first?
- Or start with basic set (0, 1, 2, 3-6) and expand?
- Who's creating the sprites?

### **4. Naming Convention**
- `finished_wall_autotile_X.png` or `wall_autotile_X.png`?
- Keep "finished_" prefix for consistency?
- Separate folders for walls/floors?

---

## Next Steps

**Once we decide on the approach:**

1. I'll update `autotiling.py` to support walls/floors
2. I'll create sprite path logic in `grid_arcade.py`
3. You create the sprites based on the specs
4. We test and iterate

**Then we move to multi-tile structures.**

---

**What's your preference?**
- Walls: 13-tile path or 47-tile blob?
- Floors: Edge detection or simple variations?
- Style: Industrial cyberpunk with panels/rivets?
