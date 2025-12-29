# Sprite Naming System - Fractured City

## Overview

This document defines the complete sprite naming convention for all tile types in Fractured City. Names are structured for easy replacement and organization.

---

## Naming Convention Format

```
{category}_{type}_{variant}_{state}.png
```

**Examples:**
- `ground_concrete_0_clean.png`
- `ground_concrete_0_cracked.png`
- `ground_pavement_autotile_3.png`
- `building_residential_small_intact.png`

---

## Category 1: GROUND TILES (Base Layer)

These fill empty spaces and create the foundation.

### **Concrete Ground**
```
ground_concrete_0.png          # Basic concrete
ground_concrete_1.png          # Variation 1
ground_concrete_2.png          # Variation 2
ground_concrete_cracked_0.png  # Cracked concrete
ground_concrete_cracked_1.png  # Cracked variation
ground_concrete_stained_0.png  # Oil stains, dirt
```

### **Pavement**
```
ground_pavement_0.png          # Basic pavement
ground_pavement_1.png          # Variation
ground_pavement_cracked_0.png  # Damaged pavement
ground_pavement_worn_0.png     # Worn/faded
```

### **Industrial Flooring**
```
ground_metal_grating_0.png     # Metal grating
ground_metal_grating_1.png     # Rusted grating
ground_industrial_0.png        # Industrial concrete
ground_industrial_1.png        # Variation
```

### **Dirt/Broken Ground**
```
ground_dirt_0.png              # Exposed dirt
ground_dirt_1.png              # Variation
ground_rubble_0.png            # Rubble-strewn
ground_rubble_1.png            # Variation
```

### **Overgrown**
```
ground_overgrown_0.png         # Grass breaking through
ground_overgrown_1.png         # More vegetation
ground_overgrown_dense_0.png   # Heavy overgrowth
```

---

## Category 2: GROUND AUTOTILING (Blending)

For smooth transitions between ground types. Uses same 13-tile system as roads.

### **Concrete to Dirt Transition**
```
ground_concrete_to_dirt_autotile_0.png   # Isolated
ground_concrete_to_dirt_autotile_1.png   # Horizontal
ground_concrete_to_dirt_autotile_2.png   # Vertical
ground_concrete_to_dirt_autotile_3.png   # Corner NW
ground_concrete_to_dirt_autotile_4.png   # Corner NE
ground_concrete_to_dirt_autotile_5.png   # Corner SW
ground_concrete_to_dirt_autotile_6.png   # Corner SE
ground_concrete_to_dirt_autotile_7.png   # T-junction N
ground_concrete_to_dirt_autotile_8.png   # T-junction S
ground_concrete_to_dirt_autotile_9.png   # T-junction E
ground_concrete_to_dirt_autotile_10.png  # T-junction W
ground_concrete_to_dirt_autotile_11.png  # 4-way cross
ground_concrete_to_dirt_autotile_12.png  # End cap
```

### **Pavement to Overgrown Transition**
```
ground_pavement_to_overgrown_autotile_0.png
ground_pavement_to_overgrown_autotile_1.png
... (same 13 variants)
```

### **Industrial to Rubble Transition**
```
ground_industrial_to_rubble_autotile_0.png
ground_industrial_to_rubble_autotile_1.png
... (same 13 variants)
```

---

## Category 3: ROADS (Already Done)

```
street_autotile_0.png through street_autotile_12.png  ✅ COMPLETE
```

### **Road Overlays** (Future)
```
street_overlay_crosswalk_0.png    # Crosswalk markings
street_overlay_arrow_0.png        # Directional arrows
street_overlay_damage_0.png       # Cracks, potholes
```

---

## Category 4: BUILDINGS

### **Residential Buildings**
```
building_residential_small_intact.png      # 3x3 intact house
building_residential_small_damaged.png     # 3x3 damaged
building_residential_small_ruined.png      # 3x3 ruined
building_residential_medium_intact.png     # 5x5 intact
building_residential_medium_damaged.png    # 5x5 damaged
building_residential_large_intact.png      # 7x7 intact
building_residential_large_damaged.png     # 7x7 damaged
```

### **Commercial Buildings**
```
building_commercial_small_intact.png
building_commercial_small_damaged.png
building_commercial_medium_intact.png
building_commercial_medium_damaged.png
building_commercial_large_intact.png
building_commercial_large_damaged.png
```

### **Industrial Buildings**
```
building_industrial_small_intact.png
building_industrial_small_damaged.png
building_industrial_medium_intact.png
building_industrial_medium_damaged.png
building_industrial_large_intact.png
building_industrial_large_damaged.png
```

### **Building Components** (Multi-tile)
```
building_wall_exterior_0.png       # Exterior wall tile
building_wall_exterior_damaged.png # Damaged wall
building_wall_interior_0.png       # Interior wall
building_floor_0.png               # Building floor
building_floor_damaged.png         # Damaged floor
building_roof_0.png                # Roof tile (Z=1)
building_roof_damaged.png          # Damaged roof
```

---

## Category 5: RESOURCES & SALVAGE

### **Scrap & Salvage**
```
resource_scrap_pile_small.png      # Small scrap pile
resource_scrap_pile_medium.png     # Medium pile
resource_scrap_pile_large.png      # Large pile
resource_salvage_metal_0.png       # Metal salvage
resource_salvage_electronics_0.png # Electronics
resource_salvage_components_0.png  # Tech components
```

### **Natural Resources**
```
resource_tree_green_0.png          # Living tree
resource_tree_dead_0.png           # Dead tree
resource_tree_overgrown_0.png      # Overgrown tree
resource_bush_0.png                # Bush/shrub
resource_grass_patch_0.png         # Grass patch
```

### **Harvestable Nodes**
```
resource_node_wood_0.png           # Wood node
resource_node_metal_0.png          # Metal node
resource_node_mineral_0.png        # Mineral node
resource_node_food_0.png           # Food source
```

---

## Category 6: URBAN CLUTTER

### **Debris**
```
clutter_debris_small_0.png         # Small debris
clutter_debris_medium_0.png        # Medium debris
clutter_debris_large_0.png         # Large debris
clutter_rubble_pile_0.png          # Rubble pile
clutter_rubble_pile_1.png          # Variation
```

### **Abandoned Objects**
```
clutter_dumpster_0.png             # Dumpster
clutter_dumpster_damaged.png       # Damaged dumpster
clutter_barrel_0.png               # Barrel/drum
clutter_crate_0.png                # Crate/box
clutter_vehicle_wreck_0.png        # Wrecked vehicle
clutter_vehicle_wreck_1.png        # Variation
```

### **Infrastructure**
```
clutter_fence_chain_0.png          # Chain-link fence
clutter_fence_damaged_0.png        # Broken fence
clutter_barrier_0.png              # Concrete barrier
clutter_sign_0.png                 # Street sign
clutter_light_post_0.png           # Light post
clutter_light_post_broken.png      # Broken light
```

---

## Category 7: WALLS (Autotiling)

### **Exterior Walls**
```
wall_exterior_autotile_0.png through wall_exterior_autotile_12.png
wall_exterior_damaged_autotile_0.png through wall_exterior_damaged_autotile_12.png
wall_exterior_ruined_autotile_0.png through wall_exterior_ruined_autotile_12.png
```

### **Interior Walls**
```
wall_interior_autotile_0.png through wall_interior_autotile_12.png
```

### **Doors**
```
door_intact_closed.png             # Closed door
door_intact_open.png               # Open door
door_damaged_closed.png            # Damaged closed
door_damaged_open.png              # Damaged open
door_destroyed.png                 # Destroyed door
```

---

## Category 8: SPECIAL TILES

### **Landmarks**
```
landmark_plaza_center_0.png        # Plaza center tile
landmark_fountain_0.png            # Fountain
landmark_statue_0.png              # Statue/monument
landmark_park_bench_0.png          # Park bench
```

### **Hazards**
```
hazard_toxic_puddle_0.png          # Toxic spill
hazard_fire_0.png                  # Fire tile
hazard_sparks_0.png                # Electrical sparks
hazard_steam_vent_0.png            # Steam vent
```

---

## Tile Blending System

### **How Blending Works**

When two different ground types meet, use autotiling to create smooth transitions:

**Example: Concrete meets Dirt**
1. Concrete tile has dirt to the east
2. System checks: "concrete" tile, neighbor is "dirt"
3. Loads: `ground_concrete_to_dirt_autotile_9.png` (T-junction E)
4. Result: Smooth blend with concrete on left, dirt on right

### **Blending Priority**

When multiple ground types meet, blend in this order:
1. Roads (highest - always on top)
2. Concrete/Pavement
3. Industrial flooring
4. Dirt/Rubble
5. Overgrown (lowest - underneath everything)

---

## Implementation Phases

### **Phase 1: Base Ground** (NOW)
- Concrete variations (3-5 sprites)
- Dirt variations (2-3 sprites)
- Basic pavement (2-3 sprites)

### **Phase 2: Ground Blending**
- Concrete-to-dirt autotile set (13 sprites)
- Pavement-to-overgrown autotile set (13 sprites)

### **Phase 3: Buildings**
- Small buildings (3x3) - 3 states each
- Medium buildings (5x5) - 3 states each

### **Phase 4: Resources**
- Scrap piles (3 sizes)
- Trees (3 types)
- Salvage objects (3 types)

### **Phase 5: Clutter & Detail**
- Debris (3 sizes)
- Vehicles (2-3 wrecks)
- Fences and barriers

---

## Sprite Specifications

**All sprites:**
- Size: 64x64 pixels
- Format: PNG with transparency
- Location: `assets/tiles/`

**Naming rules:**
- All lowercase
- Underscores for spaces
- Descriptive and consistent
- Easy to search/replace

---

## Current Status

✅ **Complete:**
- Roads (street_autotile_0 through 12)

🔄 **Next to Create:**
- Ground concrete (3-5 variations)
- Ground dirt (2-3 variations)
- Ground pavement (2-3 variations)

⏳ **Future:**
- Ground blending autotiles
- Buildings
- Resources
- Clutter

---

This naming system allows you to:
1. Easily replace sprites later
2. Add variations without breaking anything
3. Organize by category
4. Implement blending systematically
5. Scale up as you create more assets
