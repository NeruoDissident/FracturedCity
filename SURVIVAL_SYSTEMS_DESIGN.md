# FRACTURED CITY - SURVIVAL SYSTEMS DESIGN
## Hunting, Animal Husbandry & Rooftop Farming

**Design Philosophy:** Urban survival in a collapsed megacity
**Progression:** Foraging → Hunting → Taming → Farming → Self-Sustaining

---

## 🎯 HUNTING SYSTEM

### Urban Critters (Wildlife)

**Design Constraint:** This is a CITY, not wilderness. Hunt urban animals that thrive in ruins.

#### Huntable Animals:

**1. Rats** (Common, Easy)
- **Spawn:** Ground level (Z=0), in ruins, near trash, sewers
- **Behavior:** Flee when approached, hide in walls
- **Hunting Difficulty:** Easy (slow, predictable)
- **Yield:** 
  - Rat meat (1-2 units) - low quality food
  - Rat pelt (1 unit) - crafting material
- **Respawn:** Fast (every 2-3 days)
- **Mood Impact:** Neutral (expected in ruins)

**2. Pigeons** (Common, Medium)
- **Spawn:** Rooftops (Z=1+), ledges, open air
- **Behavior:** Fly away when threatened, roost at night
- **Hunting Difficulty:** Medium (fast, airborne)
- **Yield:**
  - Pigeon meat (2-3 units) - decent food
  - Feathers (1-2 units) - crafting/comfort items
- **Respawn:** Medium (every 3-4 days)
- **Mood Impact:** Positive (fresh meat, not rats)

**3. Raccoons** (Uncommon, Hard)
- **Spawn:** Ground/rooftop, near food sources, dumpsters
- **Behavior:** Aggressive if cornered, smart, nocturnal
- **Hunting Difficulty:** Hard (fights back, can injure)
- **Yield:**
  - Raccoon meat (4-5 units) - good quality food
  - Raccoon pelt (2 units) - quality crafting material
  - Chance of infection if injured during hunt
- **Respawn:** Slow (every 5-7 days)
- **Mood Impact:** Very positive (quality meat, trophy)

**4. Feral Cats** (Rare, Hard)
- **Spawn:** Anywhere, independent, territorial
- **Behavior:** Extremely fast, aggressive, can escape easily
- **Hunting Difficulty:** Very Hard (fast, fights back)
- **Yield:**
  - Cat meat (3-4 units) - controversial food
  - Cat pelt (2 units) - soft material
- **Respawn:** Very slow (every 7-10 days)
- **Mood Impact:** Mixed (some colonists refuse to eat, others don't care)

**5. Mutant Squirrels** (Uncommon, Medium)
- **Spawn:** Trees, rooftop gardens, parks
- **Behavior:** Erratic, Echo-touched, unpredictable
- **Hunting Difficulty:** Medium (fast but small)
- **Yield:**
  - Squirrel meat (2 units) - slightly Echo-tainted
  - Echo residue (1 unit) - crafting component
- **Respawn:** Medium (every 4-5 days)
- **Mood Impact:** Neutral to negative (Echo concerns)

---

### Hunting Mechanics

#### Job Type: "hunt"
```python
Job(
    type="hunt",
    category="hunt",
    x=animal_x,
    y=animal_y,
    z=animal_z,
    target_animal=animal_id,  # Reference to animal entity
    required=100,  # Time to track and kill
)
```

#### Hunting Flow:
1. **Spawn Animals:** Random spawn in valid zones (ruins, rooftops, etc.)
2. **Detection:** Colonists can see animals in vision range
3. **Designation:** Player clicks animal → "Hunt" button
4. **Job Creation:** Creates hunt job at animal's current location
5. **Tracking:** Colonist moves toward animal
6. **Chase:** Animal flees/fights based on behavior
7. **Kill:** Colonist catches and kills animal (combat roll)
8. **Butcher:** Animal corpse becomes world item
9. **Haul:** Colonist hauls corpse to butcher station or stockpile
10. **Process:** At butcher station, corpse → meat + materials

#### Skills Involved:
- **Hunting Skill:** Affects tracking speed, kill chance
- **Combat Skill:** Affects damage to animal, injury chance
- **Butchery Skill:** Affects meat yield, material quality

#### Equipment:
- **Weapons:** Melee (knife, club) or ranged (bow, slingshot) - future
- **Traps:** Placeable traps that auto-catch animals - future
- **Bait:** Lure animals to specific locations - future

---

## 🐾 ANIMAL HUSBANDRY SYSTEM

### Tameable Urban Animals

**Design Constraint:** Only animals that make sense in a city. No cows or chickens - this is urban survival.

#### Tameable Species:

**1. Pigeons** (Easiest)
- **Taming Difficulty:** Easy (food-motivated)
- **Taming Method:** Feed consistently for 3-5 days
- **Housing:** Pigeon coop (rooftop structure)
- **Breeding:** Fast (eggs every 2-3 days)
- **Products:**
  - Eggs (food, crafting)
  - Feathers (crafting, comfort)
  - Meat (if slaughtered)
- **Maintenance:** Low (scavenge own food if allowed outside)
- **Benefits:** Renewable food source, early-game accessible

**2. Rats** (Easy)
- **Taming Difficulty:** Easy (breed quickly)
- **Taming Method:** Capture and breed in cages
- **Housing:** Rat cages (small, stackable)
- **Breeding:** Very fast (litters every 1-2 days)
- **Products:**
  - Rat meat (food - mood penalty)
  - Test subjects (medical research)
  - Pelts (low-quality crafting)
- **Maintenance:** Very low (eat scraps)
- **Benefits:** Emergency food, research, fast breeding
- **Drawbacks:** Mood penalty, disease risk

**3. Raccoons** (Medium)
- **Taming Difficulty:** Medium (smart, stubborn)
- **Taming Method:** Consistent feeding + handling for 7-10 days
- **Housing:** Raccoon pen (ground level, secure)
- **Breeding:** Medium (kits every 5-7 days)
- **Products:**
  - Raccoon meat (good food)
  - Pelts (quality crafting)
  - Companionship (mood bonus)
- **Maintenance:** Medium (need varied diet, enrichment)
- **Benefits:** Quality products, can train for tasks
- **Special:** Can train raccoons to scavenge/haul items

**4. Feral Cats** (Hard)
- **Taming Difficulty:** Hard (independent, selective)
- **Taming Method:** Patience, respect, food for 10-14 days
- **Housing:** Cat shelter (indoor/outdoor access)
- **Breeding:** Slow (kittens every 7-10 days)
- **Products:**
  - Pest control (kills rats automatically)
  - Companionship (strong mood bonus)
  - Pelts (if slaughtered - mood penalty)
- **Maintenance:** Low (hunt own food, independent)
- **Benefits:** Pest control, morale boost, low maintenance
- **Special:** Cats reduce rat spawns in area

**5. Mutant Pigeons** (Hard, Late Game)
- **Taming Difficulty:** Hard (Echo-touched, unstable)
- **Taming Method:** Echo dampeners + specialized feed
- **Housing:** Reinforced coop (Echo-shielded)
- **Breeding:** Medium (eggs every 3-4 days)
- **Products:**
  - Echo-infused eggs (special crafting)
  - Mutant feathers (advanced materials)
  - Meat (Echo-tainted, mood penalty)
- **Maintenance:** High (Echo stabilization required)
- **Benefits:** Advanced crafting materials, Echo research

---

### Animal Husbandry Mechanics

#### Taming Process:
1. **Capture/Approach:** Hunt animal but use "Tame" instead of "Kill"
2. **Feeding:** Colonist feeds animal daily (creates "tame" job)
3. **Trust Building:** Progress bar fills over time (3-14 days)
4. **Tamed:** Animal becomes owned, moves to pen/coop
5. **Breeding:** Two tamed animals → offspring (auto-tamed)

#### Housing Requirements:
- **Pigeon Coop:** 2x2 rooftop structure, holds 6 pigeons
- **Rat Cage:** 1x1 stackable, holds 4 rats
- **Raccoon Pen:** 3x3 ground structure, holds 3 raccoons
- **Cat Shelter:** 2x2 indoor/outdoor, holds 2 cats

#### Animal Needs:
- **Food:** Daily feeding (type depends on species)
- **Water:** Access to water source
- **Space:** Minimum tiles per animal
- **Enrichment:** Toys, climbing, social (affects mood/breeding)
- **Health:** Can get sick, injured, need medical care

#### Products & Slaughter:
- **Eggs/Milk:** Auto-collected daily (if applicable)
- **Slaughter:** Player designates animal for slaughter
  - Creates "slaughter" job
  - Colonist kills animal humanely
  - Yields meat + materials
  - Mood impact (some colonists upset)

#### Training (Advanced):
- **Raccoons:** Can train to haul items, scavenge
- **Cats:** Can train to patrol, guard
- **Pigeons:** Can train to carry messages (future)

---

## 🌱 ROOFTOP FARMING SYSTEM

### Design Constraint: Farms ONLY on rooftops (Z=1+)

**Rationale:** Ground level is ruins, concrete, contaminated. Rooftops have sunlight, rain, clean air.

#### Farm Types:

**1. Dirt Plot** (Basic)
- **Size:** 1x1 tile
- **Placement:** Any rooftop tile
- **Construction:** 5 wood + 10 dirt/scrap
- **Crops:** Basic vegetables (potatoes, carrots, tomatoes)
- **Yield:** Low (1-3 food per harvest)
- **Growth Time:** 5-7 days
- **Maintenance:** Water every 2 days, weed every 3 days

**2. Planter Box** (Improved)
- **Size:** 2x1 tile
- **Placement:** Rooftop, needs adjacent wall for support
- **Construction:** 10 wood + 5 metal + 20 dirt
- **Crops:** Improved vegetables, herbs, small fruits
- **Yield:** Medium (3-5 food per harvest)
- **Growth Time:** 4-6 days
- **Maintenance:** Water every 3 days, fertilize weekly

**3. Hydroponic Bed** (Advanced)
- **Size:** 3x1 tile
- **Placement:** Rooftop, needs power connection
- **Construction:** 15 metal + 10 components + 5 water pipes
- **Crops:** Any crop, year-round
- **Yield:** High (5-8 food per harvest)
- **Growth Time:** 3-5 days
- **Maintenance:** Power required, nutrient solution weekly

**4. Greenhouse** (Late Game)
- **Size:** Room designation (min 12 tiles, rooftop only)
- **Placement:** Enclosed rooftop room with glass roof
- **Construction:** Glass panels, heating, ventilation
- **Crops:** Multiple plots inside, climate-controlled
- **Yield:** Very high (all plots +50% yield)
- **Growth Time:** Reduced by 30%
- **Maintenance:** Power, temperature control

---

### Crop Types:

#### Tier 1 (Dirt Plot):
- **Potatoes:** 5 days, 2 food, filling
- **Carrots:** 6 days, 2 food, nutritious
- **Radishes:** 4 days, 1 food, fast growing
- **Herbs:** 7 days, 1 food, mood bonus

#### Tier 2 (Planter Box):
- **Tomatoes:** 6 days, 3 food, versatile
- **Lettuce:** 5 days, 2 food, fresh
- **Peppers:** 7 days, 3 food, spicy (mood bonus)
- **Strawberries:** 8 days, 4 food, luxury

#### Tier 3 (Hydroponic):
- **Mushrooms:** 4 days, 3 food, grows in dark
- **Algae:** 3 days, 2 food, nutrient-rich
- **Synthetic Greens:** 5 days, 5 food, engineered
- **Echo Moss:** 6 days, 1 food + Echo components

#### Special Crops:
- **Medicinal Herbs:** Crafting ingredient for medicine
- **Fiber Plants:** Crafting material for clothing
- **Tobacco/Stimulants:** Mood/recreation items
- **Decorative Flowers:** Mood bonus, beauty

---

### Farming Mechanics

#### Job Types:
- **"plant_crop":** Colonist plants seeds in plot
- **"water_crop":** Colonist waters growing plants
- **"fertilize_crop":** Colonist adds nutrients
- **"weed_plot":** Colonist removes weeds
- **"harvest_crop":** Colonist collects mature crops

#### Growth Stages:
1. **Planted:** Seeds in soil (0-20% growth)
2. **Sprouting:** Small shoots visible (20-40%)
3. **Growing:** Plants developing (40-70%)
4. **Mature:** Ready to harvest (70-100%)
5. **Withered:** Unharvested too long (100%+, yield loss)

#### Environmental Factors:
- **Sunlight:** Rooftop = full sun (growth bonus)
- **Rain:** Natural watering (reduces water jobs)
- **Temperature:** Affects growth speed (cold = slower)
- **Season:** Some crops seasonal (future)
- **Echo Storms:** Can damage/mutate crops

#### Crop Failure:
- **Drought:** Not watered → withers and dies
- **Pests:** Rats/insects eat crops (cats help!)
- **Disease:** Spreads between adjacent plots
- **Echo Corruption:** Mutates crop (edible but weird)

---

## 🔄 PROGRESSION PATH

### Early Game (Days 1-10):
- **Foraging:** Scavenge food from ruins
- **Hunting:** Hunt rats and pigeons for fresh meat
- **Goal:** Survive, establish base

### Mid Game (Days 10-30):
- **Taming:** Start pigeon coop, maybe rats
- **Basic Farming:** Dirt plots on rooftops
- **Hunting:** Hunt raccoons for quality meat
- **Goal:** Reduce foraging dependency

### Late Game (Days 30+):
- **Advanced Husbandry:** Raccoons, cats, mutant animals
- **Advanced Farming:** Hydroponics, greenhouse
- **Self-Sustaining:** No foraging needed
- **Goal:** Surplus production, trade

---

## 🎨 SPRITE REQUIREMENTS

### Animals (Animated):
- **Rat:** 32x32, idle/walk/flee animations
- **Pigeon:** 32x32, idle/walk/fly animations
- **Raccoon:** 48x48, idle/walk/attack animations
- **Feral Cat:** 32x32, idle/walk/attack animations
- **Mutant Squirrel:** 32x32, idle/erratic animations

### Animal Structures:
- **Pigeon Coop:** 2x2 rooftop structure
- **Rat Cage:** 1x1 stackable cage
- **Raccoon Pen:** 3x3 fenced area
- **Cat Shelter:** 2x2 cozy structure

### Farming:
- **Dirt Plot:** 1x1 brown soil tile
- **Planter Box:** 2x1 wooden box with soil
- **Hydroponic Bed:** 3x1 metal frame with pipes
- **Crops:** Growth stage sprites (4 stages per crop)
- **Greenhouse:** Glass panels, roof tiles

### Items:
- **Raw Meat:** Rat, pigeon, raccoon, cat variants
- **Pelts:** Different quality levels
- **Eggs:** Pigeon eggs
- **Vegetables:** Each crop type
- **Seeds:** Seed packets for each crop

---

## 🔧 TECHNICAL IMPLEMENTATION

### Animal Entity System:
```python
@dataclass
class Animal:
    id: str
    species: str  # "rat", "pigeon", "raccoon", etc.
    x: int
    y: int
    z: int
    health: int
    tamed: bool
    owner_id: str | None  # Colonist who tamed
    hunger: int
    mood: int
    age: int  # Days old
    can_breed: bool
```

### Crop Entity System:
```python
@dataclass
class Crop:
    id: str
    crop_type: str  # "potato", "tomato", etc.
    x: int
    y: int
    z: int
    growth: float  # 0.0 to 1.0
    watered: bool
    fertilized: bool
    health: int
    days_since_water: int
    days_since_fertilize: int
```

### Room Types (New):
- **Animal Pen:** Room designation for animal housing
- **Greenhouse:** Room designation for farming

---

## 📊 BALANCE CONSIDERATIONS

### Food Production Rates:
- **Foraging:** 10-20 food/day (early game, unsustainable)
- **Hunting:** 5-15 food/day (mid game, skill-dependent)
- **Animal Husbandry:** 10-30 food/day (renewable, maintenance)
- **Farming:** 20-50 food/day (late game, scalable)

### Resource Investment:
- **Hunting:** Low (time + weapons)
- **Taming:** Medium (time + food + housing)
- **Farming:** High (construction + maintenance + water)

### Colonist Needs:
- **1 Colonist:** ~3 food/day
- **10 Colonists:** ~30 food/day
- **Goal:** Surplus for trade, emergencies

---

**Last Updated:** Dec 31, 2025
**Status:** Design phase - ready for implementation
**Next Steps:** Implement animal spawning, hunting jobs, basic farming plots
