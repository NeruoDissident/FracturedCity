# Hunting & Animal System Design
**Fractured City - Urban Survival Edition**

Based on existing design doc + new brainstorming session

---

## 🎯 Asset Analysis

**Current Animal Sprites:**
- `bird_0_flight.png` - Flying bird sprite
- `bird_0_perched.png` - Perched bird sprite
- `dog_dobermann_0.png` - Doberman dog sprite
- `dog_mutt_0.png` - Mutt dog sprite

**Naming Convention:** `{species}_{variant}_{state}.png`

**Implications:**
- Birds have multiple states (flight/perched) - need state machine
- Dogs have breed variants - can have different stats per breed
- Numbered variants (_0) suggest more variants coming

---

## 🏗️ System Architecture Options

### Option A: Hunting Station as Multi-Purpose Workstation
**Concept:** One station handles both hunting job creation AND butchering

**Pros:**
- Simple, one building to manage
- Natural workflow: hunt → butcher at same place
- Fits existing workstation pattern

**Cons:**
- Conflates two different activities
- Can't have dedicated hunters vs butchers
- Station placement affects both activities

**Implementation:**
```python
BUILDING_TYPES = {
    "hunting_lodge": {
        "workstation": True,
        "size": (2, 2),
        "recipes": [
            # Butchering recipes
            {"id": "butcher_rat", "input": {"rat_corpse": 1}, "output": {"rat_meat": 2, "rat_pelt": 1}},
            {"id": "butcher_pigeon", "input": {"pigeon_corpse": 1}, "output": {"pigeon_meat": 3, "feathers": 2}},
            # ... etc
        ],
        "special": {
            "creates_hunt_jobs": True,  # Special flag
            "hunt_range": 50,  # Tiles from station
        }
    }
}
```

### Option B: Separate Hunting & Butchering
**Concept:** Hunting Lodge creates hunt jobs, Butcher Table processes corpses

**Pros:**
- Clear separation of concerns
- Can specialize colonists (hunters vs butchers)
- Butcher table can be in kitchen, hunting lodge near exit
- More realistic workflow

**Cons:**
- Two buildings to manage
- More complex for player

**Implementation:**
```python
# Hunting Lodge - creates hunt jobs for nearby animals
"hunting_lodge": {
    "workstation": False,  # Not a crafting station
    "size": (2, 2),
    "special": {
        "type": "hunting_post",
        "hunt_range": 50,
        "auto_designate": False,  # Player manually designates animals
    }
}

# Butcher Table - processes corpses into materials
"butcher_table": {
    "workstation": True,
    "size": (2, 1),
    "recipes": [
        {"id": "butcher_rat", ...},
        {"id": "butcher_pigeon", ...},
    ]
}
```

### Option C: No Station Required for Hunting
**Concept:** Player designates animals directly, butchering needs station

**Pros:**
- Most flexible - hunt anywhere
- Butcher table is clear purpose
- Simplest for player

**Cons:**
- No progression gate for hunting
- Can't limit hunting to specific colonists

**Implementation:**
```python
# Just butcher table, hunting is direct designation
"butcher_table": {
    "workstation": True,
    "size": (2, 1),
    "recipes": [...],
}

# Hunting is like mining/chopping - direct designation
# Click animal → "Hunt" button → creates hunt job
```

---

## 🎮 Workstation Assignment Discussion

### Current System: No Assignment
- Any colonist can take any job from any workstation
- Works via job queue priority system
- Simple, emergent behavior

### Assignment Systems in Other Games:

**Dwarf Fortress:**
- No direct assignment
- Uses labor toggles per colonist (mining, crafting, etc.)
- Workshops don't have owners

**RimWorld:**
- Work priorities per colonist (1-4 scale)
- Workbenches have "bills" (orders) but no owners
- Colonists pick jobs based on priority + skill

**Prison Architect:**
- No assignment, workers auto-pick tasks
- Room assignments (cells, offices) but not workstations

**Oxygen Not Included:**
- Job priorities per duplicant
- No workstation assignment

### Recommendation: **Hybrid Approach**

**Keep current system BUT add optional specialization:**

```python
# Workstation data structure
workstation = {
    "type": "spark_bench",
    "x": 10, "y": 15, "z": 0,
    "recipe": "salvage_wire",
    "orders": [...],
    "reserved": False,
    # NEW: Optional assignment
    "assigned_colonists": [],  # Empty = anyone can use
    "assignment_mode": "anyone",  # "anyone", "assigned_only", "preferred"
}

# Assignment modes:
# - "anyone": Current behavior, anyone can use (DEFAULT)
# - "preferred": Assigned colonists get priority, others can use if idle
# - "assigned_only": Only assigned colonists can use (strict)
```

**Benefits:**
- Backward compatible (default = current behavior)
- Optional optimization for players who want it
- Can specialize colonists without forcing it
- UI: Right-click workstation → "Assign Colonists" panel

**Use Cases:**
- Assign best crafter to important workstations
- Keep dangerous jobs (butchering) to specific colonists
- Prevent unskilled colonists from wasting materials

---

## 🐾 Animal System Design

### Animal Entity Structure

```python
class Animal:
    """Wild or tamed animal entity."""
    
    def __init__(self):
        self.uid = generate_uid()
        self.species = "rat"  # rat, pigeon, dog, cat, raccoon
        self.variant = 0  # Sprite variant
        self.x, self.y, self.z = 0, 0, 0
        
        # State
        self.state = "idle"  # idle, fleeing, hunting, sleeping, eating
        self.health = 100
        self.hunger = 0  # 0-100
        self.age = 0  # Days old
        
        # Behavior
        self.is_wild = True
        self.is_hostile = False
        self.flee_distance = 5  # Tiles to flee from threats
        self.aggression = 0.0  # 0.0-1.0, chance to fight back
        
        # Taming
        self.tame_progress = 0  # 0-100
        self.tame_difficulty = 50  # Species-dependent
        self.owner = None  # Colonist UID if tamed
        
        # Products
        self.can_be_milked = False
        self.can_lay_eggs = False
        self.last_product_tick = 0
        
        # Corpse data (when killed)
        self.corpse_item = None  # Item ID for corpse
        self.meat_yield = (1, 3)  # Min, max
        self.material_yield = {"pelt": (1, 2)}
```

### Animal Behavior States

```python
# State machine for animals
ANIMAL_STATES = {
    "idle": {
        "wander": 0.3,  # 30% chance to wander each tick
        "sleep": 0.1,   # 10% chance to sleep if tired
        "eat": 0.2,     # 20% chance to eat if hungry
    },
    "fleeing": {
        "duration": 100,  # Flee for 100 ticks
        "speed": 1.5,     # Move faster when fleeing
    },
    "tamed_idle": {
        "stay_near_pen": True,
        "wander_radius": 10,
    },
    "hunting": {  # For predators (cats hunting rats)
        "target": None,
        "chase_range": 15,
    }
}
```

### Hunting Flow

```
1. SPAWN ANIMALS
   └─> Random spawn in valid zones (ruins, rooftops)
   └─> Species based on Z-level and biome

2. PLAYER DESIGNATES
   └─> Click animal → "Hunt" button
   └─> Creates hunt job at animal location

3. COLONIST TAKES JOB
   └─> Moves toward animal
   └─> Animal detects threat, flees or fights

4. CHASE/COMBAT
   └─> If animal flees: colonist pursues
   └─> If animal fights: combat system
   └─> Success: animal dies, becomes corpse item

5. HAUL CORPSE
   └─> Colonist hauls corpse to butcher table or stockpile
   └─> Corpse is world item (like resources)

6. BUTCHER
   └─> At butcher table, corpse → meat + materials
   └─> Uses butchery skill for yield
```

### Taming Flow

```
1. CAPTURE/APPROACH
   └─> Click animal → "Tame" button (instead of Hunt)
   └─> Creates tame job

2. FEEDING PHASE
   └─> Colonist brings food to animal daily
   └─> Tame progress increases (3-14 days)
   └─> Animal stays in area, doesn't flee from feeder

3. TAMED
   └─> Progress reaches 100%
   └─> Animal becomes owned by colony
   └─> Moves to assigned pen/coop

4. MAINTENANCE
   └─> Daily feeding jobs auto-created
   └─> Health checks, breeding, product collection
```

### Animal Pens & Coops

```python
# Similar to room system but for animals
ANIMAL_HOUSING = {
    "pigeon_coop": {
        "size": (2, 2),
        "capacity": 6,  # Max 6 pigeons
        "z_level": 1,   # Rooftop only
        "species": ["pigeon"],
        "products": ["eggs", "feathers"],
    },
    "rat_cage": {
        "size": (1, 1),
        "capacity": 4,
        "z_level": 0,
        "species": ["rat"],
        "products": ["rat_meat"],  # Breeding for meat
    },
    "dog_kennel": {
        "size": (2, 2),
        "capacity": 2,
        "z_level": 0,
        "species": ["dog"],
        "products": [],  # Companionship only
    },
    "animal_pen": {
        "size": (3, 3),
        "capacity": 3,
        "z_level": 0,
        "species": ["raccoon", "cat"],  # Multi-species
        "products": ["pelts", "companionship"],
    }
}
```

---

## 🐕 Companion System

### Companion Mechanics

**Concept:** Tamed animals can bond with specific colonists

**Benefits:**
- **Mood Bonus:** +5-10 mood when near companion
- **Stress Relief:** Petting/playing reduces stress
- **Loyalty:** Companion defends owner in combat
- **Skills:** Some companions can be trained for tasks

**Implementation:**

```python
# In colonist.py
class Colonist:
    def __init__(self):
        # ... existing attributes ...
        self.companion = None  # Animal UID
        self.companion_bond = 0  # 0-100 bond strength

# In animal entity
class Animal:
    def __init__(self):
        # ... existing attributes ...
        self.companion_of = None  # Colonist UID
        self.bond_strength = 0  # 0-100

# Bonding process
def update_companion_bond(colonist, animal, game_tick):
    """Increase bond over time when near each other."""
    if distance(colonist, animal) < 5:
        animal.bond_strength += 0.1  # Slow increase
        if animal.bond_strength >= 50:
            colonist.companion = animal.uid
            animal.companion_of = colonist.uid
```

**Companion Abilities by Species:**

- **Dogs:**
  - Follow owner everywhere
  - Bark to alert of threats
  - Can be trained to haul items
  - Strong combat support

- **Cats:**
  - Independent, comes/goes
  - Kills rats automatically
  - Mood bonus when nearby
  - Weak combat support

- **Raccoons:**
  - Can be trained to scavenge
  - Brings random items to owner
  - Medium combat support
  - Requires more attention

- **Pigeons:**
  - Can carry messages (future)
  - Scout/explore areas
  - No combat support
  - Low maintenance

---

## 📋 Implementation Phases

### Phase 1: Basic Hunting (MVP)
- [ ] Animal entity system
- [ ] Animal spawning (rats, pigeons on ground/rooftop)
- [ ] Hunt job designation (click animal → hunt)
- [ ] Chase mechanics (animal flees, colonist pursues)
- [ ] Kill → corpse item
- [ ] Butcher table workstation
- [ ] Butchering recipes (corpse → meat + materials)

### Phase 2: Animal Behavior
- [ ] Animal state machine (idle, fleeing, eating, sleeping)
- [ ] Animal needs (hunger, thirst)
- [ ] Predator/prey interactions (cats hunt rats)
- [ ] Day/night behavior (nocturnal animals)

### Phase 3: Taming System
- [ ] Tame job designation
- [ ] Feeding mechanics
- [ ] Tame progress tracking
- [ ] Animal pens/coops
- [ ] Tamed animal maintenance

### Phase 4: Breeding & Products
- [ ] Breeding mechanics (2 animals → offspring)
- [ ] Egg laying (pigeons)
- [ ] Product collection jobs
- [ ] Slaughter designation

### Phase 5: Companions
- [ ] Companion bonding system
- [ ] Companion following behavior
- [ ] Companion abilities (hauling, combat, scouting)
- [ ] Companion UI (assign, train, interact)

### Phase 6: Advanced Features
- [ ] Training system (teach tricks/tasks)
- [ ] Animal health/medical system
- [ ] Mutant animals (Echo-touched)
- [ ] Animal mood/happiness

---

## 🎨 UI Considerations

### Animal Designation
- Click animal → Context menu appears
  - "Hunt" (red icon)
  - "Tame" (green icon)
  - "Info" (view stats)

### Butcher Table UI
- Same as other workstations
- Recipes list corpse types
- Shows available corpses in stockpile

### Animal Pen UI
- Click pen → Shows housed animals
- Assign animals to pen
- View products, health, breeding status

### Companion UI
- In colonist detail panel, new "Companion" tab
- Shows bonded animal
- Buttons: "Call", "Release", "Train"

---

## 🤔 Design Questions for User

1. **Hunting Station:** Option A (multi-purpose), B (separate), or C (no station)?
   - My recommendation: **Option C** for simplicity, add hunting lodge later if needed

2. **Workstation Assignment:** Add optional assignment system?
   - My recommendation: **Yes, but optional** - default to current behavior

3. **Companion Priority:** Should companions be Phase 1 or later?
   - My recommendation: **Phase 5** - get basic hunting working first

4. **Animal Variety:** Start with 2-3 species or all at once?
   - My recommendation: **Start with rats + pigeons** (easiest), add dogs/cats later

5. **Pen Requirement:** Must animals be in pens, or can they roam?
   - My recommendation: **Pens required for tamed animals** - prevents chaos

---

## 🚀 Recommended Starting Point

**Minimal Viable Hunting System:**

1. Create `animals.py` module
2. Add rat and pigeon entities with basic AI
3. Spawn animals randomly on ground/rooftop
4. Add "Hunt" designation (like mining)
5. Hunt job → chase → kill → corpse item
6. Add butcher table workstation
7. Butcher recipes: rat_corpse → rat_meat + rat_pelt

**This gives you:**
- Functional hunting loop
- New food source
- Foundation for taming/breeding later
- ~2-3 hours of implementation

**Then iterate:**
- Add more species
- Add taming
- Add pens
- Add companions
