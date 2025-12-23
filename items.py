"""Item definitions and registry.

This module owns:
- Item type definitions (weapons, tools, clothing, implants, charms, etc.)
- Item registry for looking up item data by ID
- World item spawning and pickup
- Helper functions for equipping/unequipping items

Items can exist in three states:
1. Equipped on a colonist (in equipment slots)
2. In colonist inventory (inventory_slots)
3. As world items on the ground (similar to resource items)

Item stats are placeholder for now - will be wired up in a later milestone.
"""

from __future__ import annotations

from typing import Dict, Tuple, Optional, List
from dataclasses import dataclass, field


# ============================================================================
# Item Definition
# ============================================================================

@dataclass
class ItemDef:
    """Definition for an item type."""
    id: str                          # Unique identifier, e.g. "hard_hat"
    name: str                        # Display name, e.g. "Hard Hat"
    slot: str | None                 # Equipment slot: head, body, hands, feet, implant, charm, or None
    tags: List[str] = field(default_factory=list)  # Tags for filtering: weapon, tool, clothing, etc.
    
    # Placeholder stat fields - will be wired up later
    comfort: float = 0.0             # Bonus to colonist comfort
    speed_bonus: float = 0.0         # Movement speed modifier (0.1 = +10%)
    hazard_resist: float = 0.0       # Resistance to environmental hazards
    work_bonus: float = 0.0          # Work speed modifier
    
    # Visual
    icon_color: Tuple[int, int, int] = (150, 150, 150)  # Color for UI icon
    description: str = ""            # Flavor text


# ============================================================================
# Item Registry - Central definition of all item types
# ============================================================================

ITEM_REGISTRY: Dict[str, ItemDef] = {}


def register_item(item_def: ItemDef) -> None:
    """Register an item definition."""
    ITEM_REGISTRY[item_def.id] = item_def


def get_item_def(item_id: str) -> Optional[ItemDef]:
    """Get item definition by ID."""
    return ITEM_REGISTRY.get(item_id)


def get_items_for_slot(slot: str) -> List[ItemDef]:
    """Get all item definitions that can go in a specific slot."""
    return [item for item in ITEM_REGISTRY.values() if item.slot == slot]


def get_items_with_tag(tag: str) -> List[ItemDef]:
    """Get all item definitions with a specific tag."""
    return [item for item in ITEM_REGISTRY.values() if tag in item.tags]


# ============================================================================
# Default Item Definitions
# ============================================================================

# --- Head Slot ---
register_item(ItemDef(
    id="hard_hat",
    name="Hard Hat",
    slot="head",
    tags=["clothing", "protective"],
    hazard_resist=0.1,
    icon_color=(200, 180, 50),
    description="Basic head protection for construction work."
))

register_item(ItemDef(
    id="scavenger_hood",
    name="Scavenger Hood",
    slot="head",
    tags=["clothing"],
    comfort=0.05,
    icon_color=(100, 90, 80),
    description="A worn hood that keeps the dust out."
))

register_item(ItemDef(
    id="signal_visor",
    name="Signal Visor",
    slot="head",
    tags=["tech", "implant_adjacent"],
    work_bonus=0.05,
    icon_color=(80, 180, 200),
    description="Displays environmental data on a heads-up display."
))

# --- Body Slot ---
register_item(ItemDef(
    id="work_vest",
    name="Work Vest",
    slot="body",
    tags=["clothing", "work"],
    work_bonus=0.05,
    icon_color=(180, 120, 60),
    description="Sturdy vest with many pockets."
))

register_item(ItemDef(
    id="padded_jacket",
    name="Padded Jacket",
    slot="body",
    tags=["clothing", "protective"],
    comfort=0.1,
    hazard_resist=0.05,
    icon_color=(80, 100, 120),
    description="Insulated jacket for harsh conditions."
))

register_item(ItemDef(
    id="scrap_armor",
    name="Scrap Armor",
    slot="body",
    tags=["armor", "protective"],
    hazard_resist=0.2,
    speed_bonus=-0.1,
    icon_color=(100, 100, 110),
    description="Makeshift armor cobbled from salvage."
))

# --- Hands Slot ---
register_item(ItemDef(
    id="work_gloves",
    name="Work Gloves",
    slot="hands",
    tags=["clothing", "work"],
    work_bonus=0.1,
    icon_color=(140, 100, 60),
    description="Thick gloves for manual labor."
))

register_item(ItemDef(
    id="salvage_tool",
    name="Salvage Tool",
    slot="hands",
    tags=["tool", "work"],
    work_bonus=0.15,
    icon_color=(120, 130, 140),
    description="Multi-purpose tool for breaking down scrap."
))

register_item(ItemDef(
    id="signal_gauntlet",
    name="Signal Gauntlet",
    slot="hands",
    tags=["tech", "tool"],
    work_bonus=0.05,
    icon_color=(60, 140, 180),
    description="Wrist-mounted interface for tech work."
))

# --- Feet Slot ---
register_item(ItemDef(
    id="work_boots",
    name="Work Boots",
    slot="feet",
    tags=["clothing", "work"],
    speed_bonus=0.05,
    icon_color=(90, 70, 50),
    description="Sturdy boots for rough terrain."
))

register_item(ItemDef(
    id="runner_shoes",
    name="Runner Shoes",
    slot="feet",
    tags=["clothing"],
    speed_bonus=0.15,
    comfort=0.05,
    icon_color=(180, 60, 60),
    description="Lightweight shoes for quick movement."
))

# --- Implant Slot ---
register_item(ItemDef(
    id="focus_chip",
    name="Focus Chip",
    slot="implant",
    tags=["implant", "tech"],
    work_bonus=0.1,
    icon_color=(200, 100, 200),
    description="Neural implant that enhances concentration."
))

register_item(ItemDef(
    id="endurance_mod",
    name="Endurance Mod",
    slot="implant",
    tags=["implant", "tech"],
    speed_bonus=0.1,
    hazard_resist=0.1,
    icon_color=(100, 200, 100),
    description="Metabolic regulator for sustained activity."
))

register_item(ItemDef(
    id="echo_dampener",
    name="Echo Dampener",
    slot="implant",
    tags=["implant", "tech"],
    comfort=0.15,
    icon_color=(100, 150, 200),
    description="Filters out disorienting environmental signals."
))

# --- Charm Slot ---
register_item(ItemDef(
    id="lucky_coin",
    name="Lucky Coin",
    slot="charm",
    tags=["charm", "trinket"],
    comfort=0.05,
    icon_color=(220, 180, 50),
    description="A worn coin that brings comfort."
))

register_item(ItemDef(
    id="memory_locket",
    name="Memory Locket",
    slot="charm",
    tags=["charm", "trinket"],
    comfort=0.1,
    icon_color=(180, 150, 200),
    description="Contains a faded photograph."
))

register_item(ItemDef(
    id="signal_stone",
    name="Signal Stone",
    slot="charm",
    tags=["charm", "tech"],
    hazard_resist=0.05,
    icon_color=(80, 200, 180),
    description="A crystal that hums with strange energy."
))

# --- Non-equippable items (for inventory) ---
register_item(ItemDef(
    id="rusty_key",
    name="Rusty Key",
    slot=None,
    tags=["key", "trinket"],
    icon_color=(160, 100, 60),
    description="Opens something, somewhere."
))

register_item(ItemDef(
    id="data_chip",
    name="Data Chip",
    slot=None,
    tags=["tech", "valuable"],
    icon_color=(60, 180, 220),
    description="Contains encrypted information."
))

register_item(ItemDef(
    id="acorn",
    name="Acorn",
    slot=None,
    tags=["organic", "seed"],
    icon_color=(140, 100, 50),
    description="A small seed. Could be planted."
))

# --- Furniture / World Objects ---
register_item(ItemDef(
    id="gutter_slab",
    name="Gutter Slab",
    slot=None,
    tags=["furniture", "work_surface"],
    icon_color=(110, 80, 90),
    description=(
        "\"You don’t need a lot of space to butcher rats.\"\n"
        "Type: Universal Furniture / Work Surface\n"
        "Room Tags: Kitchen, Workshop, Salvage Bay, Stitchery, Bio-Still\n"
        "Rarity: Common / Found Everywhere in Ruins\n"
        "Crafted At: Gutter Forge\n"
        "Recipe: 4 Wood + 2 Mineral\n"
        "Placement: Walkable tile, does not block movement, counts as furniture."
    ),
))

register_item(ItemDef(
    id="crash_bed",
    name="Crash Bed",
    slot=None,
    tags=["furniture", "bed"],
    icon_color=(160, 90, 160),
    description=(
        "A narrow synthfoam slab with a bolted-in pillow and graffiti on the side.\n"
        "Type: Sleeping Furniture / Bed\n"
        "Room Tags: Crash Pad (shared), Coffin Nook (private)\n"
        "Rarity: Scavenged from capsule hotels and end-of-line hab blocks.\n"
        "Crafted At: Skinshop Loom\n"
        "Recipe: 2 Scrap + 2 Wood\n"
        "Placement: Walkable tile, does not block movement, counts as furniture."
    ),
))

# ============================================================================
# NEW ITEMS - Room-focused recipes
# ============================================================================

# --- Workshop Furniture ---
register_item(ItemDef(
    id="workshop_table",
    name="Workshop Table",
    slot=None,
    tags=["furniture", "workshop"],
    icon_color=(120, 100, 80),
    description="Sturdy work surface for crafting and assembly."
))

register_item(ItemDef(
    id="tool_rack",
    name="Tool Rack",
    slot=None,
    tags=["furniture", "workshop", "storage"],
    icon_color=(140, 110, 90),
    description="Wall-mounted rack for organizing tools."
))

# --- Comfort Furniture ---
register_item(ItemDef(
    id="comfort_chair",
    name="Comfort Chair",
    slot=None,
    tags=["furniture", "comfort"],
    icon_color=(100, 80, 120),
    description="Padded chair for relaxation."
))

register_item(ItemDef(
    id="storage_locker",
    name="Storage Locker",
    slot=None,
    tags=["furniture", "storage"],
    icon_color=(90, 90, 100),
    description="Metal locker for personal belongings."
))

# --- Dining Furniture ---
register_item(ItemDef(
    id="dining_table",
    name="Dining Table",
    slot=None,
    tags=["furniture", "dining"],
    icon_color=(130, 100, 70),
    description="Large table for communal meals."
))

# --- Lighting ---
register_item(ItemDef(
    id="wall_lamp",
    name="Wall Lamp",
    slot=None,
    tags=["furniture", "lighting"],
    icon_color=(220, 200, 100),
    description="Electric lamp that illuminates a room."
))

# --- Military Furniture ---
register_item(ItemDef(
    id="weapon_rack",
    name="Weapon Rack",
    slot=None,
    tags=["furniture", "military", "storage"],
    icon_color=(100, 100, 110),
    description="Rack for storing weapons and combat gear."
))

register_item(ItemDef(
    id="bar_stool",
    name="Bar Stool",
    slot=None,
    tags=["furniture", "bar"],
    icon_color=(90, 70, 50),
    description="Rusty metal stool for sitting at the bar."
))

# --- Consumables / Booze ---
register_item(ItemDef(
    id="swill",
    name="Swill",
    slot=None,
    tags=["consumable", "booze", "low_quality"],
    comfort=0.05,
    icon_color=(120, 100, 60),
    description="Cheap fermented drink. Tastes like rust and regret, but it's alcohol."
))

register_item(ItemDef(
    id="guttershine",
    name="Guttershine",
    slot=None,
    tags=["consumable", "booze", "high_quality"],
    comfort=0.15,
    icon_color=(180, 160, 100),
    description="Distilled spirits with a kick. Burns going down, but worth it."
))

# --- Electronic Components ---
register_item(ItemDef(
    id="wire",
    name="Wire",
    slot=None,
    tags=["component", "electronics"],
    icon_color=(180, 160, 140),
    description="Salvaged copper wire. Basic electrical component."
))

register_item(ItemDef(
    id="resistor",
    name="Resistor",
    slot=None,
    tags=["component", "electronics"],
    icon_color=(160, 140, 120),
    description="Scavenged resistor. Controls electrical current."
))

register_item(ItemDef(
    id="capacitor",
    name="Capacitor",
    slot=None,
    tags=["component", "electronics"],
    icon_color=(140, 150, 160),
    description="Salvaged capacitor. Stores electrical charge."
))

register_item(ItemDef(
    id="chip",
    name="Circuit Chip",
    slot=None,
    tags=["component", "electronics", "advanced"],
    icon_color=(100, 180, 140),
    description="Hand-assembled circuit chip. Complex electronics component."
))

register_item(ItemDef(
    id="led",
    name="LED",
    slot=None,
    tags=["component", "electronics", "lighting"],
    icon_color=(200, 220, 100),
    description="Light-emitting diode. Glows when powered."
))

# --- Instruments ---
register_item(ItemDef(
    id="scrap_guitar",
    name="Scrap Guitar",
    slot=None,
    tags=["instrument", "recreation", "music"],
    comfort=0.1,
    icon_color=(140, 100, 60),
    description="Guitar cobbled together from scrap and wire. Sounds rough but playable."
))

register_item(ItemDef(
    id="drum_kit",
    name="Drum Kit",
    slot=None,
    tags=["instrument", "recreation", "music"],
    comfort=0.1,
    icon_color=(120, 110, 100),
    description="Improvised drums from barrels and scrap metal. Loud and cathartic."
))

register_item(ItemDef(
    id="synth",
    name="Synth Keyboard",
    slot=None,
    tags=["instrument", "recreation", "music", "electronic"],
    comfort=0.15,
    icon_color=(100, 180, 200),
    description="Synthesizer built from salvaged chips. Makes strange electronic sounds."
))

register_item(ItemDef(
    id="harmonica",
    name="Harmonica",
    slot=None,
    tags=["instrument", "recreation", "music", "portable"],
    comfort=0.05,
    icon_color=(150, 140, 130),
    description="Simple metal harmonica. Easy to carry, easy to play."
))

register_item(ItemDef(
    id="amp",
    name="Amplifier",
    slot=None,
    tags=["instrument", "recreation", "music", "electronic"],
    icon_color=(80, 90, 100),
    description="Amplifier for instruments. Makes everything louder."
))

# --- Weapons (Hands slot) ---
register_item(ItemDef(
    id="pipe_weapon",
    name="Pipe Weapon",
    slot="hands",
    tags=["weapon", "melee"],
    work_bonus=-0.05,
    icon_color=(120, 110, 100),
    description="Heavy metal pipe, effective as a club."
))

register_item(ItemDef(
    id="scrap_blade",
    name="Scrap Blade",
    slot="hands",
    tags=["weapon", "melee"],
    work_bonus=-0.1,
    icon_color=(140, 130, 120),
    description="Sharpened metal blade fashioned from salvage."
))

# --- Armor (Body slot) ---
register_item(ItemDef(
    id="armor_plate",
    name="Armor Plate",
    slot="body",
    tags=["armor", "protective", "military"],
    hazard_resist=0.25,
    speed_bonus=-0.15,
    icon_color=(110, 110, 120),
    description="Heavy metal plating for maximum protection."
))

# --- Tech & Medical (Implant/Charm slots) ---
register_item(ItemDef(
    id="medical_scanner",
    name="Medical Scanner",
    slot="implant",
    tags=["tech", "medical"],
    work_bonus=0.05,
    icon_color=(100, 200, 150),
    description="Diagnostic implant for medical work."
))

register_item(ItemDef(
    id="stim_injector",
    name="Stim Injector",
    slot="implant",
    tags=["tech", "medical"],
    speed_bonus=0.15,
    hazard_resist=-0.05,
    icon_color=(200, 100, 100),
    description="Auto-injector for performance enhancement."
))

register_item(ItemDef(
    id="neural_interface",
    name="Neural Interface",
    slot="implant",
    tags=["tech", "advanced"],
    work_bonus=0.2,
    comfort=-0.05,
    icon_color=(150, 100, 200),
    description="Advanced neural augmentation for enhanced cognition."
))

register_item(ItemDef(
    id="data_slate",
    name="Data Slate",
    slot="charm",
    tags=["tech", "tool"],
    work_bonus=0.05,
    icon_color=(80, 150, 180),
    description="Portable data terminal for information access."
))

# --- Building Components (Non-equippable) ---
register_item(ItemDef(
    id="reinforced_door",
    name="Reinforced Door",
    slot=None,
    tags=["building", "security"],
    icon_color=(100, 100, 110),
    description="Heavy-duty door for secure areas."
))


# ============================================================================
# World Items - Items dropped on the ground
# ============================================================================

Coord3D = Tuple[int, int, int]

# World items registry - items on the ground awaiting pickup
_WORLD_ITEMS: Dict[Coord3D, List[dict]] = {}


def spawn_world_item(x: int, y: int, z: int, item_id: str, count: int = 1) -> bool:
    """Spawn an item on the ground at the given position.
    
    Returns True if successful, False if item_id is invalid.
    """
    item_def = get_item_def(item_id)
    if item_def is None:
        return False
    
    coord = (x, y, z)
    if coord not in _WORLD_ITEMS:
        _WORLD_ITEMS[coord] = []
    
    # Add item instances
    for _ in range(count):
        _WORLD_ITEMS[coord].append({
            "id": item_id,
            "name": item_def.name,
            "slot": item_def.slot,
            "haul_requested": True,  # Auto-mark for hauling
        })
    
    return True


def get_world_items_at(x: int, y: int, z: int) -> List[dict]:
    """Get all items at a world position."""
    return _WORLD_ITEMS.get((x, y, z), [])


def pickup_world_item(x: int, y: int, z: int) -> Optional[dict]:
    """Pick up one item from the ground. Returns the item dict or None."""
    coord = (x, y, z)
    items = _WORLD_ITEMS.get(coord, [])
    if items:
        item = items.pop(0)
        if not items:
            del _WORLD_ITEMS[coord]
        return item
    return None


def get_all_world_items() -> Dict[Coord3D, List[dict]]:
    """Get all world items for rendering/saving."""
    return _WORLD_ITEMS.copy()


def clear_world_items() -> None:
    """Clear all world items (for testing/reset)."""
    _WORLD_ITEMS.clear()


def process_equipment_haul_jobs(jobs_module, zones_module) -> int:
    """Create haul jobs for all items on the ground.
    
    Called each tick from main loop. Finds items needing haul and creates
    jobs to move them to stockpile zones. Handles equipment, components, 
    instruments, and other crafted items.
    
    Returns number of jobs created.
    """
    jobs_created = 0
    
    for (x, y, z), items in list(_WORLD_ITEMS.items()):
        if not items:
            continue
        
        # Check first item (we haul one at a time)
        item = items[0]
        if not item.get("haul_requested", False):
            continue
        
        # Already has a job at this location
        if jobs_module.get_job_at(x, y, z) is not None:
            continue
        
        # Determine storage type based on item tags
        item_id = item.get("id", "")
        item_def = get_item_def(item_id)
        
        # Default to equipment stockpile
        storage_type = "equipment"
        
        # Check item tags to determine proper storage
        if item_def:
            tags = getattr(item_def, "tags", [])
            if "component" in tags or "electronics" in tags:
                storage_type = "components"
            elif "instrument" in tags or "music" in tags:
                storage_type = "instruments"
            elif "furniture" in tags:
                storage_type = "furniture"
            elif "consumable" in tags:
                storage_type = "consumables"
        
        # Find appropriate stockpile
        dest = zones_module.find_stockpile_tile_for_resource(
            storage_type, z=z, from_x=x, from_y=y
        )
        
        # Fall back to general equipment stockpile if no specialized stockpile exists
        if dest is None and storage_type != "equipment":
            dest = zones_module.find_stockpile_tile_for_resource(
                "equipment", z=z, from_x=x, from_y=y
            )
        
        if dest is None:
            # No valid stockpile zone exists - skip
            continue
        
        dest_x, dest_y, dest_z = dest
        
        # Create haul job
        print(f"[DEBUG Haul] Creating haul job: item at ({x},{y},{z}), dest ({dest_x},{dest_y},{dest_z}), storage_type={storage_type}")
        jobs_module.add_job(
            "haul",
            x, y,
            required=10,  # Quick job
            resource_type=storage_type,
            dest_x=dest_x,
            dest_y=dest_y,
            dest_z=dest_z,
            z=z,
        )
        jobs_created += 1
    
    return jobs_created


# ============================================================================
# Item Instance Creation
# ============================================================================

def create_item_instance(item_id: str) -> Optional[dict]:
    """Create an item instance dict from an item definition.
    
    Returns a dict suitable for storing in equipment slots or inventory.
    """
    item_def = get_item_def(item_id)
    if item_def is None:
        return None
    
    return {
        "id": item_id,
        "name": item_def.name,
        "slot": item_def.slot,
        "icon_color": item_def.icon_color,
    }


# ============================================================================
# Colonist Equipment Helpers
# ============================================================================

def equip_item(colonist, item_id: str) -> bool:
    """Equip an item on a colonist. Returns True if successful.
    
    The item must have a valid slot. If something is already equipped
    in that slot, it will be replaced (and lost for now - inventory
    management comes later).
    """
    item_def = get_item_def(item_id)
    if item_def is None or item_def.slot is None:
        return False
    
    slot = item_def.slot
    if slot not in colonist.equipment:
        return False
    
    colonist.equipment[slot] = create_item_instance(item_id)
    return True


def unequip_item(colonist, slot: str) -> Optional[dict]:
    """Unequip an item from a colonist's slot. Returns the item or None."""
    if slot not in colonist.equipment:
        return None
    
    item = colonist.equipment[slot]
    colonist.equipment[slot] = None
    return item


def get_equipped_item(colonist, slot: str) -> Optional[dict]:
    """Get the item equipped in a slot, or None."""
    return colonist.equipment.get(slot)


# ============================================================================
# Debug / Testing Helpers
# ============================================================================

def equip_random_items(colonist, count: int = 3) -> None:
    """Equip random items on a colonist for testing."""
    import random
    
    slots = ["head", "body", "hands", "feet", "implant", "charm"]
    random.shuffle(slots)
    
    equipped = 0
    for slot in slots:
        if equipped >= count:
            break
        items = get_items_for_slot(slot)
        if items:
            item = random.choice(items)
            equip_item(colonist, item.id)
            equipped += 1


def spawn_test_items(x: int, y: int, z: int = 0) -> None:
    """Spawn a variety of test items at a location."""
    test_items = ["hard_hat", "work_gloves", "lucky_coin", "rusty_key"]
    for i, item_id in enumerate(test_items):
        spawn_world_item(x + i, y, z, item_id)


# ============================================================================
# Auto-Equip System - Colonists claim items matching their preferences
# ============================================================================

# Mapping from item stats/tags to colonist preferences
# Positive value = colonist with positive preference likes this stat
STAT_TO_PREFERENCE = {
    # Item stats → preference keys
    "hazard_resist": "likes_outside",      # Protection helps outdoors
    "comfort": "likes_integrity",          # Comfort items for those who like stability
    "work_bonus": "likes_pressure",        # Work bonus for those who like pressure/productivity
    "speed_bonus": "likes_outside",        # Speed for outdoor explorers
}

TAG_TO_PREFERENCE = {
    # Item tags → preference keys
    "protective": "likes_outside",         # Protection for outdoor lovers
    "tech": "likes_interference",          # Tech items for those who like interference
    "implant": "likes_echo",               # Implants for echo-sensitive
    "charm": "likes_integrity",            # Charms for stability seekers
    "work": "likes_pressure",              # Work gear for pressure lovers
    "stealth": "likes_crowding",           # Stealth for crowd avoiders (negative crowding)
}


def score_item_for_colonist(item_data: dict, colonist) -> float:
    """Score how well an item matches a colonist's preferences.
    
    Higher score = better match. Score can be negative if item conflicts
    with preferences.
    
    Args:
        item_data: Item dict (from stockpile or world)
        colonist: Colonist to score for
    
    Returns:
        Float score. 0 = neutral, positive = good match, negative = bad match.
    """
    score = 0.0
    preferences = getattr(colonist, 'preferences', {})
    
    # Get item definition
    item_id = item_data.get("id")
    if item_id is None:
        return 0.0
    
    item_def = get_item_def(item_id)
    if item_def is None:
        # Check if it's a generated item
        if item_data.get("generated"):
            return _score_generated_item(item_data, preferences)
        return 0.0
    
    # Score based on item stats
    if item_def.hazard_resist > 0:
        pref = preferences.get("likes_outside", 0.0)
        score += pref * item_def.hazard_resist * 2.0
    
    if item_def.comfort != 0:
        pref = preferences.get("likes_integrity", 0.0)
        score += pref * item_def.comfort * 2.0
    
    if item_def.work_bonus > 0:
        pref = preferences.get("likes_pressure", 0.0)
        score += pref * item_def.work_bonus * 2.0
    
    if item_def.speed_bonus > 0:
        pref = preferences.get("likes_outside", 0.0)
        score += pref * item_def.speed_bonus * 2.0
    
    # Score based on tags
    for tag in item_def.tags:
        pref_key = TAG_TO_PREFERENCE.get(tag)
        if pref_key:
            pref = preferences.get(pref_key, 0.0)
            score += pref * 0.5  # Tags contribute less than stats
    
    return score


def _score_generated_item(item_data: dict, preferences: dict) -> float:
    """Score a procedurally generated item for colonist preferences."""
    score = 0.0
    
    for mod in item_data.get("modifiers", []):
        stat = mod.get("stat", "")
        value = mod.get("value", 0.0)
        trigger = mod.get("trigger", "always")
        
        # Map stat to preference
        pref_key = None
        if stat in ("walk_speed", "hazard_resist"):
            pref_key = "likes_outside"
        elif stat in ("comfort", "warmth"):
            pref_key = "likes_integrity"
        elif stat in ("build_speed", "harvest_speed", "craft_speed", "focus"):
            pref_key = "likes_pressure"
        elif stat in ("echo_sense", "hearing"):
            pref_key = "likes_echo"
        elif stat == "vision":
            pref_key = "likes_interference"
        
        if pref_key:
            pref = preferences.get(pref_key, 0.0)
            # Conditional triggers are worth less
            multiplier = 1.0 if trigger == "always" else 0.5
            score += pref * value * 2.0 * multiplier
    
    # Score based on tags
    for tag in item_data.get("tags", []):
        pref_key = TAG_TO_PREFERENCE.get(tag)
        if pref_key:
            pref = preferences.get(pref_key, 0.0)
            score += pref * 0.3
    
    return score


def find_best_equipment_for_colonist(colonist, zones_module) -> Optional[tuple]:
    """Find the best unequipped item in stockpiles for a colonist.
    
    Returns (x, y, z, item_data, score) or None if no good items found.
    """
    best_item = None
    best_score = 0.1  # Minimum threshold - must be at least slightly positive
    best_pos = None
    
    # Get all stored equipment
    all_equipment = zones_module.get_all_stored_equipment()
    
    for (x, y, z), items in all_equipment.items():
        for item in items:
            # Check if colonist already has something in this slot
            slot = item.get("slot")
            # Only consider equippable items (furniture and other slotless items are ignored)
            if not slot:
                continue
            if slot and colonist.equipment.get(slot) is not None:
                continue  # Already has something in this slot
            
            score = score_item_for_colonist(item, colonist)
            if score > best_score:
                best_score = score
                best_item = item
                best_pos = (x, y, z)
    
    if best_item and best_pos:
        return (*best_pos, best_item, best_score)
    return None


def process_auto_equip(colonists: list, zones_module, jobs_module) -> int:
    """Process auto-equip for all idle colonists.
    
    Colonists will claim items from stockpiles that match their preferences.
    Creates a haul job to pick up and equip the item.
    
    Returns number of equip jobs created.
    """
    jobs_created = 0
    
    for colonist in colonists:
        # Only idle colonists look for equipment
        if colonist.state != "idle":
            continue
        
        # Skip if colonist is dead
        if getattr(colonist, 'is_dead', False):
            continue
        
        # Find best available equipment
        result = find_best_equipment_for_colonist(colonist, zones_module)
        if result is None:
            continue
        
        x, y, z, item_data, score = result
        
        # Check if there's already a job at this location
        if jobs_module.get_job_at(x, y, z) is not None:
            continue
        
        # Create equip job (special haul job that equips instead of storing)
        # Note: Job metadata like which colonist will take it is handled by the
        # normal job assignment system; we just enqueue an "equip" job here.
        jobs_module.add_job(
            "equip",
            x, y,
            required=10,  # Quick job
            resource_type="equipment",
            z=z,
        )
        
        print(f"[AutoEquip] {colonist.name} wants to equip {item_data.get('name')} (score: {score:.2f})")
        jobs_created += 1
    
    return jobs_created
