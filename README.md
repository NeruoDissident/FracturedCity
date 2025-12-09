# Fractured City

A colony survival simulation set in a post-collapse urban environment. Manage colonists with unique personalities, build shelter, gather resources, and survive in a world shaped by interference, echoes, and pressure.

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Controls](#controls)
3. [Core Systems](#core-systems)
4. [Colonists](#colonists)
5. [Traits & Personality](#traits--personality)
6. [Relationships](#relationships)
7. [Buildings & Construction](#buildings--construction)
8. [Resources](#resources)
9. [Workstations](#workstations)
10. [Environment](#environment)
11. [Debug Commands](#debug-commands)

---

## Getting Started

### Requirements
- Python 3.10+
- Pygame 2.x

### Installation
```bash
pip install pygame
python main.py
```

### First Steps
1. Game starts paused - press **SPACE** to unpause
2. Your colonists spawn in the center of a procedurally generated city
3. Designate resource gathering with **G** (gather) or **H** (harvest)
4. Build walls and structures with **B** (build menu)
5. Open colonist management with **TAB**

---

## Controls

### Camera
| Key | Action |
|-----|--------|
| **WASD** / **Arrow Keys** | Pan camera |
| **Mouse Wheel** | Zoom in/out |
| **Middle Mouse** | Pan camera (drag) |

### Game
| Key | Action |
|-----|--------|
| **SPACE** | Pause/Unpause |
| **TAB** | Toggle colonist management panel |
| **ESC** | Cancel current action / Close menus |
| **1-5** | Speed controls |

### Building & Orders
| Key | Action |
|-----|--------|
| **B** | Open build menu |
| **G** | Designate gather (scrap, minerals) |
| **H** | Designate harvest (wood, food) |
| **X** | Designate demolish |
| **C** | Cancel designations |

### Selection
| Key | Action |
|-----|--------|
| **Left Click** | Select tile / colonist |
| **Right Click** | Context action / Cancel |
| **Click + Drag** | Area selection |

---

## Core Systems

### Tick System
- Game runs at 60 ticks per second
- Colonist actions, hunger, mood all update per-tick
- Environment sampling occurs periodically

### Job Priority
Colonists automatically take jobs based on:
1. **Urgency** - Eating when hungry takes priority
2. **Distance** - Closer jobs preferred
3. **Job Tags** - Player can toggle which job types each colonist performs

### Pathfinding
- A* pathfinding with 3D support (ground level + rooftops)
- Colonists avoid unwalkable tiles (walls, water, machinery)
- Ladders connect Z-levels

---

## Colonists

### Vital Stats

| Stat | Range | Effect |
|------|-------|--------|
| **Hunger** | 0-100 | At 100 = starving, takes damage |
| **Health** | 0-100 | At 0 = death |
| **Comfort** | -10 to +10 | Positive = good mood |
| **Stress** | -10 to +10 | High stress = work penalty |

### Mood States

| Mood | Score Range | Work Speed |
|------|-------------|------------|
| **Euphoric** | > 10 | +15% |
| **Calm** | 5 to 10 | +10% |
| **Focused** | 0 to 5 | +5% |
| **Uneasy** | -5 to 0 | -5% |
| **Stressed** | -10 to -5 | -15% |
| **Overwhelmed** | < -10 | -30% |

### Colonist States
- `idle` - No current task, may wander or chat
- `moving` - Walking to destination
- `working` - Performing a job
- `eating` - Consuming food
- `recovery` - Brief pause after interruption

### Age
- Starting colonists: 18-55 years old
- Age affects relationship potential (romance requires 18+)
- Future: aging, elderly, children

---

## Traits & Personality

Each colonist has a unique combination of traits that affect their abilities, preferences, and personality.

### Trait Categories

#### Origins (1 per colonist)
Where they grew up - affects starting affinities.

| Origin | Affinity Bonuses | Job Bonus |
|--------|------------------|-----------|
| **Rust Warrens** | +interference, -integrity | +10% scavenge |
| **Deep Shelters** | +echo, +pressure, -outside | +10% craft |
| **Topside Sprawl** | +outside, -pressure | +10% build |
| **Signal Frontier** | +interference, +echo | +10% craft |
| **Fringe Settlements** | -crowding, +outside | +10% scavenge |
| **Wreck Yards** | +integrity, +interference | +15% scavenge |

#### Experiences (1 per colonist)
Major life events that shaped them.

| Experience | Effects |
|------------|---------|
| **Cortex Bloom Survivor** | +echo affinity, +craft |
| **Former Mercenary** | +stress resist, +build |
| **Signal Diver** | +interference affinity |
| **Collapsed Block Escapee** | +integrity affinity |
| **Floodlight Displaced** | -outside affinity |
| **Machine Gravekeeper** | +echo, +craft |
| **Heatline Runner** | +pressure tolerance |
| **Silent Commune Raised** | -crowding, +focus |

#### Quirks (1-2 per colonist)
Behavioral traits and habits.

| Quirk | Description |
|-------|-------------|
| **Hums When Thinking** | Hums tunelessly when deep in thought |
| **Talks to Machines** | Treats machines like old friends |
| **Scavenges Trinkets** | Collects small objects others overlook |
| **Mild Paranoia** | Watches every shadow carefully |
| **Collects Stories** | Remembers every story they've heard |
| **Sleeps Lightly** | Wakes at the slightest sound |
| **Stares Into Pipes** | Gets lost staring into pipes and vents |
| **Whispers to Echoes** | Whispers back to strange sounds |
| **Keeps Inventory** | Mentally catalogs everything nearby |
| **Won't Eat Cold Food** | Refuses anything that isn't warm |
| **Overexplains** | Uses ten words when one would do |
| **Gives Nicknames** | Names everything and everyone |
| **Takes Long Path** | Prefers scenic routes over shortcuts |
| **Afraid of Open Sky** | Gets nervous under open sky |
| **Claustrophobic** | Panics in tight enclosed spaces |

#### Major Traits (~5% chance, 1 max)
Rare, powerful traits that significantly define a colonist.

| Major Trait | Effects |
|-------------|---------|
| **★ Echo-Touched** | +0.6 echo affinity, +20% craft, senses echoes |
| **★ Rustborn** | +0.5 interference affinity, immune to rust damage |
| **★ Pressure-Blind** | Cannot sense dangerous pressure, fearless |
| **★ Static-Soul** | Needs interference to feel normal |
| **★ Last-Light Disciple** | Religious, +comfort from rituals |
| **★ Gravemind Listener** | Hears "the deep ones", unsettling |
| **★ Ghost Memory Carrier** | Experiences others' memories |
| **★ Unlinked** | Immune to echo effects, isolated |

### Affinities
Colonists develop preferences based on their environment:

| Affinity | What It Measures |
|----------|------------------|
| **Interference** | Tolerance for signal noise/static |
| **Echo** | Comfort with resonance and vibrations |
| **Pressure** | Tolerance for atmospheric pressure |
| **Integrity** | Preference for structural stability |
| **Outside** | Comfort outdoors vs indoors |
| **Crowding** | Tolerance for nearby colonists |

---

## Relationships

### Relationship Scores
- Range: -100 to +100
- Increase through positive interactions (conversations)
- Decrease through conflicts

### Relationship Types

| Type | Score Range |
|------|-------------|
| **Stranger** | -30 to +5 |
| **Acquaintance** | +5 to +30 |
| **Friend** | +30 to +60 |
| **Close Friend** | +60 to +100 |
| **Rival** | -30 to -60 |
| **Enemy** | -60 to -100 |
| **Romantic** | Special (requires +50 and compatibility) |
| **Family** | Special (blood or adopted) |

### Family Bonds
- **Parent/Child** - Blood relation
- **Sibling** - Shared parents
- **Partner** - Romantic partners

### Compatibility
- Colonists from same origin start with +15 relationship
- Shared experiences give +10 bonus
- Some trait combinations create natural affinity or tension

---

## Buildings & Construction

### Tile Types

#### Terrain
| Tile | Walkable | Description |
|------|----------|-------------|
| **Ground** | ✓ | Basic walkable surface |
| **Road** | ✓ | Paved surface, faster movement |
| **Sidewalk** | ✓ | Pedestrian path |
| **Damaged Road** | ✓ | Cracked pavement, may have resources |
| **Rubble** | ✗ | Collapsed debris, blocks movement |
| **Water** | ✗ | Impassable liquid |

#### Structures
| Tile | Walkable | Description |
|------|----------|-------------|
| **Wall** | ✗ | Blocks movement, creates rooms |
| **Door** | ✓ | Allows passage through walls |
| **Window** | ✗ | Blocks movement, allows light |
| **Floor** | ✓ | Interior flooring |
| **Roof** | - | Covers rooms (auto-generated) |
| **Ladder** | ✓ | Connects Z-levels |

#### Furniture
| Tile | Walkable | Description |
|------|----------|-------------|
| **Stockpile** | ✓ | Resource storage zone |
| **Bed** | ✓ | Rest location (future) |
| **Table** | ✗ | Work surface |
| **Chair** | ✓ | Seating |

### Construction Process
1. Player designates construction via build menu
2. Blueprint placed (ghost image)
3. Colonist with `can_build` tag claims job
4. Colonist gathers required materials
5. Colonist works at site until complete
6. Structure becomes solid

### Room Detection
- Rooms form automatically when walls fully enclose an area
- Maximum room size: 50 tiles
- Rooms provide:
  - Shelter from outside
  - Environmental modifiers
  - Roof coverage

---

## Resources

### Resource Types

| Resource | Source | Uses |
|----------|--------|------|
| **Wood** | Trees, pallets, crates | Construction, fuel |
| **Scrap** | Debris, ruins, junk piles | Construction, crafting |
| **Minerals** | Rock outcrops, rubble | Construction, crafting |
| **Food** | Canned goods, gardens | Eating (prevents starvation) |
| **Components** | Machinery, electronics | Advanced crafting |

### Gathering
- **G key** - Designate scrap/mineral gathering
- **H key** - Designate wood/food harvesting
- Colonists with appropriate job tags will gather
- Resources deposited at nearest stockpile

### Stockpiles
- Designated storage areas
- Resources automatically hauled to stockpiles
- Multiple stockpiles can exist

---

## Workstations

### Placement Rules
All workstations require:
- Placement on walkable floor tile
- Must be inside an enclosed room
- Adjacent walkable tile for colonist to stand

### Workstation Types

| Station | Purpose | Requirements |
|---------|---------|--------------|
| **Crafting Bench** | Basic item crafting | Enclosed room |
| **Forge** | Metal working | Enclosed room |
| **Kitchen** | Food preparation | Enclosed room |
| **Research Table** | Technology (future) | Enclosed room |

### Crafting Process
1. Player queues crafting job at workstation
2. Colonist with `can_craft` tag claims job
3. Colonist gathers required materials
4. Colonist works at station
5. Item produced

---

## Environment

### Environmental Parameters

| Parameter | Range | Effect |
|-----------|-------|--------|
| **Interference** | 0.0-1.0 | Signal noise, affects some colonists |
| **Echo** | 0.0-1.0 | Sound resonance, affects mood |
| **Pressure** | 0.0-1.0 | Atmospheric pressure |
| **Integrity** | 0.0-1.0 | Structural stability |
| **Outside** | 0/1 | Whether tile is outdoors |
| **Crowding** | 0.0+ | Nearby colonist density |

### Comfort & Stress
- Colonists sample environment periodically
- Environment matching preferences = comfort
- Environment opposing preferences = stress
- Comfort/stress affects mood and work speed

### Preference Drift
- Over time, colonists adapt to their environment
- Preferences slowly shift toward experienced conditions
- Creates natural specialization

---

## Combat

### Combat Power
Base power (1.0) modified by:
- **Health** - Wounded colonists fight weaker
- **Mood** - Stressed = weaker, Euphoric = stronger
- **Traits** - Former mercenary = +30%, Rustborn = +15%
- **Equipment** - Future: weapons and armor

### Combat Stances
| Stance | Behavior |
|--------|----------|
| **Aggressive** | Seeks fights, joins readily |
| **Defensive** | Fights when attacked or to protect others |
| **Passive** | Avoids combat, flees |
| **Berserk** | Attacks everyone (high stress + certain traits) |

### Joining Fights
When a colonist is attacked, others may join to help. Decision based on:
- **Relationship with victim** - Friends more likely to help
- **Relationship with attacker** - Enemies of attacker join eagerly
- **Family bonds** - Almost certain to help family
- **Combat stance** - Passive colonists rarely join
- **Own health/stress** - Wounded/stressed less heroic

### Factions
- `colony` - Player's colonists
- Future: raiders, traders, refugees
- Colonists attack members of hostile factions

---

## Debug Commands

### Keyboard Shortcuts

| Key | Action |
|-----|--------|
| **F1** | Toggle debug overlay |
| **F2** | Toggle room visualization |
| **F3** | Toggle pathfinding debug |
| **F4** | Spawn test colonist |
| **F5** | Give resources |
| **F6** | Toggle environment overlay |
| **F7** | Equip random items on all colonists |
| **F8** | Force conversation |

### Debug Overlay (F1)
Shows:
- FPS counter
- Colonist count
- Current tick
- Mouse tile coordinates
- Tile information under cursor

---

## File Structure

```
Fractured City/
├── main.py              # Game entry point, main loop
├── grid.py              # Tile grid and world data
├── colonist.py          # Colonist class and behavior
├── buildings.py         # Construction and structures
├── rooms.py             # Room detection and management
├── jobs.py              # Job system and priorities
├── pathfinding.py       # A* pathfinding
├── resources.py         # Resource definitions
├── items.py             # Static item definitions
├── item_generator.py    # Procedural item generation
├── traits.py            # Trait definitions and generation
├── conversations.py     # Colonist dialogue system
├── relationships.py     # Relationship tracking
├── ui.py                # User interface rendering
├── debug_overlay.py     # Debug visualization
├── worldgen.py          # Procedural world generation
├── environment_stats.py # Environment tracking
└── README.md            # This file
```

---

## Future Plans

- [ ] Hazards (environmental dangers)
- [ ] Events (random occurrences)
- [ ] Factions (external groups)
- [ ] New arrivals (wanderers, refugees, births)
- [ ] Temperature system
- [ ] Combat
- [ ] Research tree
- [ ] Save/Load

---

## Credits

Developed with love for colony sims, Dwarf Fortress, and the beauty of emergent storytelling.
