# Workstations and Items Reference

Complete list of all crafting stations, what they produce, and item stats.

---

## SALVAGER'S BENCH
**Purpose:** Basic material processing

### Recipes
- **Refine Metal**: 2 Scrap → 1 Metal
- **Metal Components**: 1 Metal → 3 Scrap

---

## SPARK BENCH
**Purpose:** Electronics components

### Recipes
- **Salvage Wire**: 1 Scrap → Wire (component)
- **Craft Resistor**: 1 Scrap + 1 Mineral → Resistor (component)
- **Craft Capacitor**: 1 Scrap + 1 Metal → Capacitor (component)
- **Craft Circuit Chip**: 2 Metal + 1 Mineral + 2 Wire → Chip (component)
- **Craft LED**: 1 Mineral + 1 Wire → LED (component)

---

## TINKER STATION
**Purpose:** Musical instruments and devices

### Recipes
- **Scrap Guitar**: 2 Wood + 1 Metal + 2 Wire → Scrap Guitar (instrument, comfort +0.1)
- **Drum Kit**: 3 Scrap + 2 Wood → Drum Kit (instrument, comfort +0.1)
- **Synth Keyboard**: 2 Chip + 3 Wire + 2 Scrap → Synth (instrument, comfort +0.15)
- **Harmonica**: 1 Metal + 1 Scrap → Harmonica (instrument, comfort +0.05)
- **Amplifier**: 1 Chip + 2 Wire + 2 Metal → Amp (instrument)
- **Vending Machine**: 3 Metal + 2 Chip + 1 LED → Vending Machine (furniture)

---

## GUTTER FORGE
**Purpose:** Metalworking - tools, wearable armor/clothing, weapons

### Recipes

#### Tools & Gloves
- **Salvage Tool**: 2 Metal + 1 Scrap → Salvage Tool (hands slot, work +0.1)
- **Work Gloves**: 2 Scrap → Work Gloves (hands slot, work +0.05, comfort +0.02)
- **Signal Gauntlet**: 2 Metal + 1 Power → Signal Gauntlet (hands slot, work +0.15) *[PLACEHOLDER]*

#### Wearable Armor & Clothing
- **Hard Hat**: 2 Scrap → Hard Hat (head slot, hazard resist +0.1)
- **Work Vest**: 2 Scrap + 1 Wood → Work Vest (body slot, work +0.05, comfort +0.05)
- **Padded Jacket**: 3 Scrap → Padded Jacket (body slot, comfort +0.1, warmth +0.15)
- **Work Boots**: 2 Scrap → Work Boots (feet slot, speed +0.05, walk steady +0.1)
- **Scrap Armor**: 3 Metal + 2 Scrap → Scrap Armor (body slot, hazard resist +0.15, speed -0.1)
- **Armor Plate**: 3 Metal → Armor Plate (body slot, hazard resist +0.25, speed -0.15)

#### Weapons
- **Pipe Weapon**: 3 Metal + 1 Scrap → Pipe Weapon (weapon slot, work -0.05)
- **Scrap Blade**: 2 Metal + 2 Scrap → Scrap Blade (weapon slot, work -0.1)

---

## SKINSHOP LOOM
**Purpose:** Furniture crafting

### Recipes
- **Crash Bed**: 2 Scrap + 2 Wood → Crash Bed (furniture, 1x2 vertical)
- **Comfort Chair**: 2 Wood + 1 Scrap → Comfort Chair (furniture, comfort +0.15)
- **Bar Stool**: 1 Scrap + 1 Wood → Bar Stool (furniture)
- **Storage Locker**: 3 Wood + 1 Metal → Storage Locker (furniture)
- **Dining Table**: 4 Wood → Dining Table (furniture)
- **Wall Lamp**: 1 Metal + 1 Power → Wall Lamp (furniture, lighting)

---

## CORTEX SPINDLE
**Purpose:** Cybernetics, implants, charms (MIXED IDENTITY)

### Recipes
- **Focus Chip**: 2 Metal + 1 Mineral → Focus Chip (implant slot, work +0.1, focus +0.15)
- **Echo Dampener**: 1 Metal + 2 Mineral → Echo Dampener (implant slot, hazard resist +0.2)
- **Lucky Coin**: 1 Metal → Lucky Coin (charm slot, comfort +0.05) *[PLACEHOLDER]*
- **Memory Locket**: 1 Metal + 1 Mineral → Memory Locket (charm slot, comfort +0.1) *[PLACEHOLDER]*
- **Signal Stone**: 2 Mineral + 1 Power → Signal Stone (charm slot, comfort +0.08) *[PLACEHOLDER]*
- **Medical Scanner**: 2 Metal + 2 Mineral + 1 Power → Medical Scanner (implant slot, work +0.05)
- **Stim Injector**: 1 Metal + 2 Mineral → Stim Injector (implant slot, speed +0.15, hazard resist -0.05)
- **Neural Interface**: 3 Metal + 3 Mineral + 2 Power → Neural Interface (implant slot, work +0.2, comfort -0.05)
- **Data Slate**: 1 Metal + 1 Mineral → Data Slate (charm slot, work +0.05)

---

## GUTTER STILL
**Purpose:** Brewing alcohol

### Recipes
- **Brew Swill**: 2 Raw Food + 1 Scrap → Swill (consumable)
- **Distill Guttershine**: 3 Raw Food + 2 Scrap → Guttershine (consumable)

---

## GENERATOR
**Purpose:** Power production

### Recipes
- **Burn Wood for Power**: 3 Wood → 1 Power
- **Burn Scrap for Power**: 4 Scrap → 1 Power

---

## STOVE
**Purpose:** Cooking food

### Recipes
**Note:** Recipes use tag-based ingredient matching. `@meat` accepts any meat (scrap_meat, poultry_meat, etc.), `@vegetable` accepts any vegetable (tomato, carrot, etc.)

- **Simple Meal**: 2 Raw Food + 1 Power → 1 Cooked Meal
- **Grilled Scraps**: 1 @meat + 1 Power → 1 Cooked Meal
- **Meat Stew**: 2 @meat + 1 Power → 1 Cooked Meal
- **Hearty Roast**: 2 @meat + 1 @vegetable + 2 Power → 1 Cooked Meal
- **Poultry Roast**: 2 @meat + 1 Power → 1 Cooked Meal
- **Vegetable Stew**: 2 @vegetable + 1 Power → 1 Cooked Meal

---

## BIO-MATTER SALVAGE STATION
**Purpose:** Butchering animal corpses (dynamic outputs)

### Recipe
- **Butcher Corpse**: 1 Corpse → Meat + Materials (based on species)

### Outputs by Species
- **Rat**: 1-2 Scrap Meat, 1 Rough Hide
- **Bird**: 2-3 Poultry Meat, 1-2 Feathers
- **Cat**: 2-3 Scrap Meat, 1 Cat Pelt
- **Dog**: 3-5 Scrap Meat, 1-2 Dog Pelt
- **Raccoon**: 3-4 Scrap Meat, 1 Raccoon Pelt
- **Opossum**: 2-3 Scrap Meat, 1 Opossum Pelt

---

## PLANT BED
**Purpose:** Rooftop farming (2x1 horizontal workstation)

### Placement
- **Rooftop Only** (Z=1+) - Ground is contaminated, rooftops have sun/rain/clean air

### Crops
- **Tomato**: 1 Tomato Seed → 2 Tomatoes (9 in-game hours growth time)
  - Category: Vegetable
  - Harvested crops carry metadata (crop type, harvest time, harvested by)
  - Display: "Tomato (Tomato)" (similar to "Scrap Meat (Rat)")

### Mechanics
1. Queue planting job (requires seeds in stockpile)
2. Colonist plants seed (instant)
3. Crop grows through 3 stages (seedling → growing → mature)
4. Harvest job auto-created when mature
5. Colonist harvests, items spawn adjacent to plant bed
6. Items auto-hauled to stockpile
7. Next planting job starts (if queued)

### Future Crops
- Carrots, potatoes, herbs, mushrooms, medicinal plants
- Each crop will have category tag (vegetable, fruit, grain, herb)
- Tag system allows recipes to accept any crop in category

---

## BARRACKS
**Purpose:** Combat training (no crafting recipes)

---

## BUTCHER SHOP
**Purpose:** DUPLICATE OF BIO-MATTER SALVAGE - SHOULD BE DELETED

### Recipes
- **Butcher Rat**: 1 Rat Corpse → 2 Scrap Meat + 1 Rough Hide
- **Butcher Bird**: 1 Bird Corpse → 3 Poultry Meat + 2 Feathers

---

## EQUIPMENT STATS SUMMARY

### Head Slot
- **Hard Hat**: hazard resist +0.1

### Body Slot
- **Work Vest**: work +0.05, comfort +0.05
- **Padded Jacket**: comfort +0.1, warmth +0.15
- **Scrap Armor**: hazard resist +0.15, speed -0.1
- **Armor Plate**: hazard resist +0.25, speed -0.15

### Hands Slot
- **Salvage Tool**: work +0.1
- **Work Gloves**: work +0.05, comfort +0.02
- **Signal Gauntlet**: work +0.15 *[PLACEHOLDER]*

### Weapon Slot
- **Pipe Weapon**: work -0.05
- **Scrap Blade**: work -0.1

### Feet Slot
- **Work Boots**: speed +0.05, walk steady +0.1

### Implant Slot
- **Focus Chip**: work +0.1, focus +0.15
- **Echo Dampener**: hazard resist +0.2
- **Medical Scanner**: work +0.05
- **Stim Injector**: speed +0.15, hazard resist -0.05
- **Neural Interface**: work +0.2, comfort -0.05

### Charm Slot
- **Lucky Coin**: comfort +0.05 *[PLACEHOLDER]*
- **Memory Locket**: comfort +0.1 *[PLACEHOLDER]*
- **Signal Stone**: comfort +0.08 *[PLACEHOLDER]*
- **Data Slate**: work +0.05

---

## PROBLEMS IDENTIFIED

### Identity Issues
1. **Gutter Forge** - Makes weapons, tools, gloves, armor, doors, furniture (too many categories)
2. **Skinshop Loom** - Makes clothing AND furniture (should be separate)
3. **Cortex Spindle** - Makes implants AND charms (should be separate)

### Placeholder Items (Meaningless Names)
- Signal Gauntlet (what does "signal" mean?)
- Gutter Slab (what is this?)
- Lucky Coin, Memory Locket, Signal Stone (generic trinkets with no gameplay purpose)

### Redundant Stations
- **Butcher Shop** duplicates Bio-Matter Salvage Station

### Stats Without Gameplay Purpose (Yet)
- Work speed bonuses (build_speed, craft_speed, haul_capacity) - no challenges require optimization
- Comfort bonuses - no mood/stress system impact yet
- Walk steady - no stumbling/falling mechanics

### Stats With Potential Gameplay Purpose
- **Hazard resist** - Could protect from Echo blooms, environmental hazards
- **Echo Dampener** - Could be critical for Echo events
- **Speed bonuses** - Useful for combat/escape
- **Warmth/Cooling** - Could matter for weather/climate zones

---

## NOTES FOR REORGANIZATION

**Consider:**
- Consolidate to fewer stations with clear identities
- Remove placeholder items with no gameplay purpose
- Focus on situational/environmental gear (Echo protection, hazards)
- Save stat optimization gear for when challenges require it
- Rename stations for clarity over flavor (Weaponsmith vs Gutter Forge)
