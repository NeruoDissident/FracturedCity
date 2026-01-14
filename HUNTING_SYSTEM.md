# Hunting & Animal System - Fractured City

**Last Updated:** January 10, 2026  
**Status:** Fully Implemented

## Overview

Colonists can hunt urban wildlife for food and materials. Animals roam the city, flee from threats, and drop corpses when killed. Corpses are butchered at the Bio-Matter Salvage Station.

---

## Urban Animals

### Rat
- **Rarity:** Common
- **Difficulty:** Easy
- **Health:** 20 HP
- **Speed:** Medium
- **Drops:** Rat corpse → Raw meat (low quality)
- **Behavior:** Flees from colonists

### Pigeon
- **Rarity:** Common
- **Difficulty:** Medium
- **Health:** 15 HP
- **Speed:** Fast
- **Drops:** Pigeon corpse → Raw meat, Feathers
- **Behavior:** Flees quickly, harder to catch

### Raccoon
- **Rarity:** Uncommon
- **Difficulty:** Hard
- **Health:** 40 HP
- **Speed:** Medium
- **Drops:** Raccoon corpse → Quality meat, Pelt
- **Behavior:** Fights back when cornered

### Feral Cat
- **Rarity:** Rare
- **Difficulty:** Hard
- **Health:** 30 HP
- **Speed:** Very fast
- **Drops:** Cat corpse → Meat (controversial), Pelt
- **Behavior:** Fast, aggressive when cornered

### Opossum
- **Rarity:** Uncommon
- **Difficulty:** Medium
- **Health:** 25 HP
- **Speed:** Slow
- **Drops:** Opossum corpse → Meat, Pelt
- **Behavior:** Plays dead when threatened (future)

---

## Hunting Mechanics

### 1. Hunt Job Creation
Colonist creates hunt job when idle:
```python
# In colonist.py
if animal_nearby and colonist.can_hunt:
    create_hunt_job(animal_id)
```

### 2. Chase Phase
- Colonist moves toward animal
- Animal flees (moves away from colonist)
- Chase continues until:
  - Colonist in range (1 tile)
  - Animal escapes (too far away)
  - Colonist gives up (timeout)

### 3. Attack Phase
When colonist is adjacent (1 tile):
```python
# Deal damage
animal.health -= colonist.combat_power
if animal.health <= 0:
    spawn_corpse(animal.x, animal.y)
    remove_animal(animal)
```

### 4. Corpse Spawning
Dead animals become world items:
```python
corpse_item = {
    "type": "rat_corpse",
    "x": animal.x,
    "y": animal.y,
    "z": animal.z
}
WORLD_ITEMS.append(corpse_item)
```

### 5. Hauling
Auto-haul system creates jobs to move corpses to stockpiles:
- Corpses stored in equipment/consumables stockpiles
- Colonists with `can_haul` tag transport corpses

### 6. Butchering
At Bio-Matter Salvage Station:
```python
# Recipe: Rat corpse → Raw meat
{
    "name": "Butcher Rat",
    "inputs": {"rat_corpse": 1},
    "outputs": {"raw_food": 2},
    "time": 120  # 2 seconds
}
```

---

## Animal AI

### Movement
Animals move randomly every 60-120 ticks:
```python
if random.random() < 0.3:  # 30% chance
    move_to_random_adjacent_tile()
```

### Flee Behavior
When colonist is nearby (within 5 tiles):
```python
# Calculate direction away from threat
dx = animal.x - colonist.x
dy = animal.y - colonist.y

# Move in that direction
target_x = animal.x + sign(dx)
target_y = animal.y + sign(dy)
```

### Pathfinding
Animals use simple pathfinding:
- Avoid walls and unwalkable tiles
- Prefer open spaces
- No A* (too expensive for many animals)

---

## Combat System

### Colonist Combat Power
```python
base_power = 10
power *= health_modifier  # 0.5 to 1.0 based on health
power *= mood_modifier    # 0.7 to 1.3 based on mood
power *= trait_modifier   # Former mercenary +30%, etc.
```

### Animal Health
- Rats: 20 HP (2 hits to kill)
- Pigeons: 15 HP (1-2 hits)
- Raccoons: 40 HP (4 hits, fights back)
- Cats: 30 HP (3 hits, very fast)

### Damage Calculation
```python
damage = colonist.combat_power
animal.health -= damage
```

---

## Integration Points

### Files
- `animals.py` - Animal entities, spawning, AI
- `hunting.py` - Hunt job logic
- `colonist.py` - Hunt job execution, chase/attack
- `items.py` - Corpse items, butchering recipes
- `buildings.py` - Bio-Matter Salvage Station recipes

### Job System
Hunt jobs added to global `JOB_QUEUE`:
```python
{
    "type": "hunt",
    "target_animal_id": animal_uid,
    "category": "hunt",
    "priority": 5
}
```

### Resource Flow
```
Animal → Hunt → Corpse → Haul → Stockpile → Butcher → Raw Meat → Cook → Meal
```

---

## Spawning

### World Generation
Animals spawn during worldgen:
```python
# In main.py
from animals import spawn_random_animals
spawn_random_animals(grid, count=20)
```

### Distribution
- Rats: 40% of spawns
- Pigeons: 30%
- Raccoons: 15%
- Cats: 10%
- Opossums: 5%

### Spawn Locations
- Ground level (Z=0) only
- Walkable tiles
- Not inside buildings (future: rats in buildings)

---

## Future Enhancements

### Planned Features
- **Animal Husbandry** - Tame and breed animals
- **Traps** - Passive hunting (snares, cages)
- **Pelts** - Leather crafting from animal hides
- **Eggs** - Pigeons lay eggs (renewable food)
- **Pack Behavior** - Rats travel in groups
- **Aggressive Animals** - Mutant creatures that attack colonists

### Recipe Expansion
- Pelt → Leather → Clothing
- Feathers → Arrows, Bedding
- Bones → Tools, Fertilizer

---

## Performance

### Current Load
- 20 animals spawned at worldgen
- Each animal updates every tick (movement check)
- Negligible performance impact (<1% CPU)

### Optimization
- Animals only pathfind when fleeing (not every tick)
- Simple flee logic (no A*)
- Sprite rendering batched with colonists

---

## See Also

- `animals.py` - Animal implementation
- `hunting.py` - Hunt job logic
- `SURVIVAL_SYSTEMS_DESIGN.md` - Overall food/survival design
