# Animal System Integration Guide
**Fractured City - Systems-First Implementation**

This document outlines the complete animal UI system implementation and integration steps.

---

## ✅ COMPLETED COMPONENTS

### 1. Core Animal System (`animals.py`)
**Status:** Complete with comprehensive needs system

**Key Features:**
- Animal entity class with full state machine
- Species definitions (Rat, Bird with 4 and 1 variants respectively)
- Progressive reveal data structure:
  - `food_preferences` - Dict of food types and preference values
  - `sleep_pattern` - Nocturnal/diurnal patterns, sleep hours
  - `pen_preferences` - Min/max space, preferred items, dislikes
- Needs tracking: hunger, thirst, sleep, mood (0-100)
- Taming system with progress tracking (0-100%)
- Feed mechanics with preference-based taming gains
- Global registry functions for animal management

**Progressive Reveal Tiers:**
- **Tier 0 (0-24%):** Species, state, location, tame bar only
- **Tier 1 (25-49%):** + Health, hunger, age
- **Tier 2 (50-74%):** + Behavior patterns, aggression, flee distance
- **Tier 3 (75-99%):** + Products, pen preferences
- **Tier 4 (100%):** + Full ownership, all stats unlocked

### 2. Animal Detail Panel (`ui_arcade_animal_panel.py`)
**Status:** Complete with 6 tabs

**Tabs:**
1. **Status** - Tame progress bar, state, location, health, hunger, age, behavior
2. **Bio** - Species info, habitat, yields (meat/materials)
3. **Stats** - Detailed statistics (health, speed, aggression, etc.)
4. **Products** - Eggs, milk, other products (future)
5. **Pen** - Housing requirements and preferences
6. **Help** - Taming guide and tier unlock info

**Visual Design:**
- Magenta accent color (vs cyan for colonists)
- Vertical tabs on left side
- Progressive stat locking with 🔒 icons
- Tame progress bar with color gradient (red→orange→yellow→green)
- Prev/Next/Close buttons
- Matches colonist panel structure for consistency

### 3. Animal Items (`items.py`)
**Status:** Complete

**Added Items:**
- `rat_corpse` - Dead rat for butchering
- `bird_corpse` - Dead bird for butchering
- `rat_meat` - Raw meat (low quality)
- `bird_meat` - Raw meat (decent quality)
- `rat_pelt` - Crafting material
- `feathers` - Crafting material

### 4. Butcher Shop Workstation (`buildings.py`)
**Status:** Complete

**Specs:**
- Size: 2x1 horizontal
- Materials: 3 wood + 2 metal
- Construction work: 100
- Multi-recipe workstation
- Recipes:
  - Butcher Rat: 1 corpse → 2 meat + 1 pelt (60 work)
  - Butcher Bird: 1 corpse → 3 meat + 2 feathers (70 work)

### 5. Left Sidebar ANIMALS Tab (`ui_arcade_panels.py` + `ui_arcade_panels_animals.py`)
**Status:** Complete

**Features:**
- New ANIMALS tab (index 1) in left sidebar
- Tab order: COLONISTS, ANIMALS, JOBS, ITEMS, ROOMS
- Animal list with species name, variant, state
- Mini tame progress bar per animal
- Click left half to locate, right half to open detail panel
- Hover highlighting
- Scroll support for long lists

---

## 🔧 INTEGRATION STEPS

### Step 1: Wire Animal Panel to Main Game
**File:** `main_arcade.py`

```python
# In setup() method, after colonist_detail_panel initialization:
from ui_arcade_animal_panel import get_animal_panel
self.animal_detail_panel = get_animal_panel(self.current_width, self.current_height)

# Wire sidebar callbacks for animals
self.left_sidebar.on_animal_locate = self.snap_camera_to_tile
self.left_sidebar.on_animal_click = self.open_animal_detail

# Add method:
def open_animal_detail(self, animal):
    """Open animal detail panel for a specific animal."""
    from animals import get_all_animals
    animals = get_all_animals()
    if animal in animals:
        index = animals.index(animal)
        self.animal_detail_panel.open(animals, index)
        print(f"[UI] Opened animal panel for {animal.species} #{animal.variant}")

# In on_draw(), after colonist_detail_panel.draw():
self.animal_detail_panel.draw()

# In on_mouse_press(), after colonist_detail_panel.handle_click():
if self.animal_detail_panel.handle_click(x, y):
    return

# In on_resize(), after colonist_detail_panel.on_resize():
if hasattr(self, 'animal_detail_panel'):
    self.animal_detail_panel.on_resize(width, height)
```

### Step 2: Add Animal Update Loop
**File:** `main_arcade.py`

```python
# In on_update() method, after colonist updates:
from animals import update_animals
update_animals(self.grid, self.game_tick)
```

### Step 3: Test with Mock Animals
**File:** `main_arcade.py` (temporary test code)

```python
# In setup() method, after grid initialization:
# TEMP: Spawn test animals
from animals import spawn_animal
spawn_animal(self.grid, "rat", 10, 10, 0, variant=0)  # Rat variant 0
spawn_animal(self.grid, "rat", 12, 10, 0, variant=1)  # Rat variant 1
spawn_animal(self.grid, "bird", 15, 15, 1, variant=0)  # Bird on rooftop
print("[DEBUG] Spawned 3 test animals")
```

### Step 4: Add Animal Rendering (After UI Testing)
**File:** Create `animals_arcade.py` (similar to `colonist_arcade.py`)

```python
"""Animal sprite rendering for Arcade."""

import arcade
from typing import Dict, List
from animals import get_all_animals

class AnimalSprite(arcade.Sprite):
    """Sprite for an individual animal."""
    
    def __init__(self, animal):
        super().__init__()
        self.animal = animal
        self.texture = arcade.load_texture(animal.get_sprite_path())
        self.center_x = animal.x * TILE_SIZE + TILE_SIZE / 2
        self.center_y = animal.y * TILE_SIZE + TILE_SIZE / 2

class AnimalRenderer:
    """Manages all animal sprites."""
    
    def __init__(self):
        self.sprites: Dict[int, AnimalSprite] = {}
    
    def update_sprites(self):
        """Sync sprites with animal entities."""
        animals = get_all_animals()
        
        # Remove sprites for dead animals
        for uid in list(self.sprites.keys()):
            if uid not in [a.uid for a in animals]:
                del self.sprites[uid]
        
        # Add/update sprites
        for animal in animals:
            if animal.uid not in self.sprites:
                self.sprites[animal.uid] = AnimalSprite(animal)
            else:
                sprite = self.sprites[animal.uid]
                sprite.center_x = animal.x * TILE_SIZE + TILE_SIZE / 2
                sprite.center_y = animal.y * TILE_SIZE + TILE_SIZE / 2
    
    def draw(self, camera, current_z):
        """Draw all animals on current Z-level."""
        for sprite in self.sprites.values():
            if sprite.animal.z == current_z:
                sprite.draw()
```

---

## 🎯 TESTING CHECKLIST

### UI Testing (No Rendering Required)
- [ ] Launch game, open left sidebar
- [ ] Click ANIMALS tab - should show test animals
- [ ] Click animal in list - detail panel opens
- [ ] Verify tame progress bar shows correctly
- [ ] Verify Status tab shows tier 0 info only (state, location, tame bar)
- [ ] Verify locked stats show 🔒 icons
- [ ] Test Prev/Next buttons to cycle animals
- [ ] Test Close button
- [ ] Switch between all 6 tabs
- [ ] Verify Bio tab shows species info
- [ ] Verify Help tab shows tier unlock guide

### Data Testing
- [ ] Modify test animal tame_progress to 30% - verify tier 1 stats unlock
- [ ] Modify to 60% - verify tier 2 stats unlock
- [ ] Modify to 80% - verify tier 3 stats unlock
- [ ] Modify to 100% - verify tier 4 stats unlock
- [ ] Test feed() method - verify taming progress increases
- [ ] Test update_needs() - verify hunger/thirst increase over time
- [ ] Test take_damage() - verify health and mood decrease

### Integration Testing (After Rendering)
- [ ] Animals spawn at correct locations
- [ ] Animals render with correct sprites
- [ ] Animals move when wandering
- [ ] Click animal in world - detail panel opens
- [ ] Locate button in sidebar snaps camera to animal
- [ ] Animals flee when colonist approaches
- [ ] Hunt job creates corpse item
- [ ] Butcher shop processes corpses correctly

---

## 📊 SYSTEM ARCHITECTURE

### Data Flow
```
Animal Entity (animals.py)
    ↓
Animal Registry (global dict)
    ↓
Left Sidebar ANIMALS Tab (ui_arcade_panels_animals.py)
    ↓
Animal Detail Panel (ui_arcade_animal_panel.py)
    ↓
Progressive Reveal Logic (based on tame_progress)
```

### Progressive Reveal Logic
```python
def _get_tame_tier(tame_progress: int) -> int:
    if tame_progress >= 100: return 4  # Full info
    elif tame_progress >= 75: return 3  # Products, pen
    elif tame_progress >= 50: return 2  # Behavior
    elif tame_progress >= 25: return 1  # Vitals
    else: return 0  # Minimal
```

### Stat Visibility Matrix
| Stat | Tier 0 | Tier 1 | Tier 2 | Tier 3 | Tier 4 |
|------|--------|--------|--------|--------|--------|
| Species | ✅ | ✅ | ✅ | ✅ | ✅ |
| State | ✅ | ✅ | ✅ | ✅ | ✅ |
| Location | ✅ | ✅ | ✅ | ✅ | ✅ |
| Tame Bar | ✅ | ✅ | ✅ | ✅ | ✅ |
| Health | 🔒 | ✅ | ✅ | ✅ | ✅ |
| Hunger | 🔒 | ✅ | ✅ | ✅ | ✅ |
| Age | 🔒 | ✅ | ✅ | ✅ | ✅ |
| Aggression | 🔒 | 🔒 | ✅ | ✅ | ✅ |
| Flee Distance | 🔒 | 🔒 | ✅ | ✅ | ✅ |
| Food Prefs | 🔒 | 🔒 | ✅ | ✅ | ✅ |
| Sleep Pattern | 🔒 | 🔒 | ✅ | ✅ | ✅ |
| Products | 🔒 | 🔒 | 🔒 | ✅ | ✅ |
| Pen Prefs | 🔒 | 🔒 | 🔒 | ✅ | ✅ |
| Owner | 🔒 | 🔒 | 🔒 | 🔒 | ✅ |
| Mood | 🔒 | 🔒 | 🔒 | 🔒 | ✅ |

---

## 🚀 NEXT PHASES

### Phase 2: Hunting Mechanics
- Hunt job designation (click animal → "Hunt")
- Chase mechanics (colonist pursues fleeing animal)
- Combat resolution (animal dies → corpse)
- Corpse hauling to butcher shop

### Phase 3: Taming Mechanics
- Tame job designation (click animal → "Tame")
- Feeding jobs (daily feeding increases tame progress)
- Tamed animal behavior (stays near pen, doesn't flee)
- Pen assignment UI

### Phase 4: Animal Husbandry
- Animal pens (room type or furniture)
- Breeding mechanics (2 animals → offspring)
- Product collection (eggs, milk, etc.)
- Slaughter designation

### Phase 5: Companion System
- Bonding mechanics (colonist + animal)
- Companion following behavior
- Companion abilities (hauling, combat, scouting)
- Mood bonuses from companions

---

## 💡 DESIGN NOTES

### Why Progressive Reveal?
1. **Realism:** You don't know everything about a wild animal
2. **Progression:** Taming feels meaningful as you unlock info
3. **Engagement:** Players discover animal personalities over time
4. **Balance:** Prevents information overload on feral animals

### Why Separate from Colonist Panel?
1. **Different data structure:** Animals have different stats than colonists
2. **Visual distinction:** Magenta vs cyan helps differentiate
3. **Future expansion:** Animals may get unique features (breeding, products)
4. **Code organization:** Cleaner separation of concerns

### Why Mood System?
1. **Taming speed:** Happy animals tame faster
2. **Product quality:** Happy animals produce better yields
3. **Breeding:** Happy animals breed more successfully
4. **Emergent gameplay:** Players optimize for animal happiness

---

## 🎨 UI DESIGN PHILOSOPHY

**Consistency with Colonist UI:**
- Same panel structure (header, tabs, content)
- Same interaction patterns (prev/next, close)
- Same visual language (cyberpunk, neon accents)

**Differentiation:**
- Magenta accent (vs cyan for colonists)
- Progressive reveal (vs full info for colonists)
- Animal-specific tabs (Products, Pen vs colonist tabs)

**Information Density:**
- No information overload - progressive reveal prevents this
- Clear visual hierarchy - important stats prominent
- Locked stats clearly marked - player knows what to unlock

---

## 📝 SUMMARY

**What's Complete:**
- ✅ Full animal entity system with needs/preferences
- ✅ Progressive reveal data structure (4 tiers)
- ✅ Animal detail panel with 6 tabs
- ✅ ANIMALS tab in left sidebar
- ✅ Animal list rendering
- ✅ Butcher shop workstation
- ✅ Animal items (corpses, meat, materials)

**What's Next:**
- Integration with main_arcade.py (5 min)
- Test with mock animals (5 min)
- Verify UI works correctly (10 min)
- Add animal rendering (30 min)
- Implement hunting mechanics (Phase 2)

**Total Implementation Time So Far:** ~2 hours
**Estimated Time to Playable:** ~1 hour (integration + rendering)

The UI is **locked in** and ready for testing. All systems are meticulously designed with no fragile dependencies.
