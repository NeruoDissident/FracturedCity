# Item & Tagging System - Fractured City

**Last Updated:** January 10, 2026  
**Status:** Fully Implemented

## Overview

Items in Fractured City use a flexible tagging system for categorization, storage, and crafting. Tags determine where items can be stored, what recipes they're used in, and how colonists interact with them.

---

## Item Structure

```python
{
    "id": "work_gloves",
    "name": "Work Gloves",
    "slot": "hands",  # Equipment slot (if equippable)
    "tags": ["equipment", "protective", "work"],
    "stats": {
        "build_speed": 1.1,
        "hazard_resist": 5
    }
}
```

---

## Tag Categories

### Storage Tags
Determine which stockpile type accepts the item:

- **`equipment`** - Tools, weapons, armor, clothing
- **`furniture`** - Beds, tables, chairs, decorations
- **`instruments`** - Musical instruments, entertainment
- **`components`** - Crafting materials, parts
- **`consumables`** - Food, medicine, temporary items

### Material Tags
Define what the item is made of:

- **`metal`** - Metal items (weapons, tools)
- **`wood`** - Wooden items (furniture, tools)
- **`fabric`** - Cloth items (clothing, bedding)
- **`tech`** - Electronic/technological items

### Function Tags
Describe what the item does:

- **`protective`** - Provides protection (armor, helmets)
- **`work`** - Improves work efficiency
- **`comfort`** - Provides comfort bonus
- **`medical`** - Healing/medical items

---

## Equipment System

### Equipment Slots
Colonists have 6 equipment slots:

1. **Head** - Helmets, hoods, visors
2. **Body** - Vests, jackets, armor
3. **Hands** - Gloves, tools, gauntlets
4. **Feet** - Boots, shoes
5. **Implant** - Cybernetic implants
6. **Charm** - Lucky items, trinkets

### Auto-Equip System

Colonists automatically claim equipment from stockpiles based on preference scoring:

```python
def score_item(item, colonist):
    score = 0.0
    
    # Map item stats to colonist preferences
    if "hazard_resist" in item.stats:
        score += colonist.likes_outside * 0.3
    if "work_bonus" in item.stats:
        score += colonist.likes_pressure * 0.3
    if "comfort" in item.stats:
        score += colonist.likes_integrity * 0.3
    
    # Tag bonuses
    if "tech" in item.tags:
        score += colonist.likes_interference * 0.2
    if "protective" in item.tags:
        score += colonist.likes_outside * 0.2
    
    return score
```

**Threshold:** Colonist claims item if `score > 0.5`

### Equipment Flow

1. **Craft** - Item created at workstation
2. **Spawn** - Item appears as world item near workstation
3. **Haul** - Colonist moves item to equipment stockpile
4. **Scan** - Idle colonist scans stockpiles for equipment
5. **Score** - Colonist scores each item based on preferences
6. **Claim** - If score > 0.5, create "equip" job
7. **Equip** - Colonist walks to stockpile, picks up item, equips it

---

## Stockpile Filtering

### Filter System
Each stockpile zone has resource filters:

```python
zone = {
    "allow_wood": True,
    "allow_mineral": True,
    "allow_scrap": True,
    "allow_metal": True,
    "allow_power": True,
    "allow_raw_food": True,
    "allow_cooked_meal": True,
    "allow_equipment": False  # This stockpile doesn't accept equipment
}
```

### Auto-Relocation
When filters change, items are automatically relocated:

```python
# Called every 10 ticks
process_filter_mismatch_relocation(jobs_module)
```

If an item is in a stockpile that no longer allows it:
1. Find another stockpile that allows the item
2. Create haul job to move it
3. If no valid stockpile exists, item stays (warning logged)

---

## Crafting Integration

### Recipe Inputs
Recipes use item IDs or tags:

```python
{
    "name": "Work Gloves",
    "inputs": {
        "fabric": 2,      # Generic fabric (by tag)
        "scrap": 1        # Generic scrap
    },
    "outputs": {
        "work_gloves": 1  # Specific item ID
    }
}
```

### Material Matching
Crafting system checks:
1. **Exact ID match** - If input specifies "work_gloves", need that exact item
2. **Tag match** - If input specifies "fabric", any item with "fabric" tag works

---

## World Items

### Dropped Items
Items on the ground (not in stockpiles):

```python
WORLD_ITEMS = [
    {
        "type": "work_gloves",
        "x": 45,
        "y": 78,
        "z": 0,
        "age": 1200  # Ticks since spawned
    }
]
```

### Auto-Haul System
Every 10 ticks, system creates haul jobs for world items:

```python
# In items.py
process_equipment_haul_jobs(jobs_module, zones_module)
```

1. Find all world items
2. Determine storage type by tags
3. Find valid stockpile
4. Create haul job

---

## Item Definitions

### Current Equipment (17 items)

**Head (3):**
- `hard_hat` - Construction safety (+hazard_resist)
- `scavenger_hood` - Scavenging gear (+vision)
- `signal_visor` - Tech visor (+echo_sense)

**Body (3):**
- `work_vest` - Work clothing (+build_speed)
- `padded_jacket` - Comfort clothing (+comfort)
- `scrap_armor` - Makeshift armor (+hazard_resist)

**Hands (3):**
- `work_gloves` - Work gloves (+build_speed)
- `salvage_tool` - Salvaging tool (+harvest_speed)
- `signal_gauntlet` - Tech gauntlet (+craft_speed)

**Feet (2):**
- `work_boots` - Sturdy boots (+walk_steady)
- `runner_shoes` - Fast shoes (+walk_speed)

**Implant (3):**
- `focus_chip` - Neural implant (+focus)
- `endurance_mod` - Stamina implant (+stress_resist)
- `echo_dampener` - Echo resistance (+echo_resist)

**Charm (3):**
- `lucky_coin` - Lucky charm (+comfort)
- `memory_locket` - Sentimental item (+comfort)
- `signal_stone` - Tech trinket (+interference_resist)

---

## Procedural Item Generation

### Item Generator (`item_generator.py`)
Generates random items with stats and names:

```python
from item_generator import generate_item

item = generate_item(
    slot="hands",
    min_components=2,
    max_components=3
)
# Result: "Swift Gloves of the Fallen Squirrel"
# Stats: +walk_speed, +build_speed, trigger: near_acorns
```

### Components
- **Prefixes:** "Wind's", "Ember", "Swift", "Heavy"
- **Bases:** Scarf, Hood, Jacket, Gloves, Boots, Chip
- **Suffixes:** "of Echoes", "of Dawn", "of the Fallen Squirrel"

### Stats
- Movement: walk_speed, walk_steady
- Work: build_speed, harvest_speed, craft_speed
- Senses: vision, hearing, echo_sense
- Survival: warmth, cooling, hazard_resist
- Mental: comfort, focus, stress_resist

---

## Performance

### Current Load
- **17 equipment items** defined
- **~50 total items** (equipment + furniture + consumables)
- **Auto-equip:** Scans every tick (negligible CPU)
- **Auto-haul:** Scans every 10 ticks (negligible CPU)

### Optimization
- Equipment scanning early-exits if all slots full
- Stockpile filtering cached (not recalculated every frame)
- World items stored in simple list (fast iteration)

---

## Future Enhancements

### Planned Features
- **Item Durability** - Equipment degrades over time
- **Repair System** - Fix damaged equipment at workstations
- **Item Quality** - Poor/Normal/Excellent tiers
- **Enchantments** - Rare items with special effects
- **Sets** - Equipment sets with bonuses

### Recipe Expansion
- More equipment types (weapons, advanced armor)
- Consumables (medicine, drugs, food)
- Building materials (refined metals, composites)

---

## See Also

- `items.py` - Item definitions and systems
- `zones.py` - Stockpile filtering
- `EQUIPMENT_SYSTEM_NOTES.md` - Detailed equipment notes
