"""Procedural Item Generation System.

This module creates items with random stat combinations, names, and effects.
Items are generated from component pools that can be infinitely expanded.

Design Philosophy:
- Items are combinations of prefixes, bases, and suffixes
- Each component contributes stats and name fragments
- Conditional bonuses (e.g., "+1 warmth near acorns") are supported
- The system is extensible - add new components without code changes
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum


# ============================================================================
# Stat Definitions - All possible stats an item can affect
# ============================================================================

class StatType(Enum):
    """All stat types that items can modify."""
    # Movement
    WALK_SPEED = "walk_speed"           # Movement speed modifier
    WALK_STEADY = "walk_steady"         # Reduces stumbling/knockback
    
    # Work
    BUILD_SPEED = "build_speed"         # Construction speed
    HARVEST_SPEED = "harvest_speed"     # Gathering speed
    CRAFT_SPEED = "craft_speed"         # Crafting speed
    HAUL_CAPACITY = "haul_capacity"     # Carry amount
    
    # Senses
    VISION = "vision"                   # Sight range
    HEARING = "hearing"                 # Sound detection
    ECHO_SENSE = "echo_sense"           # Echo sensitivity
    
    # Survival
    WARMTH = "warmth"                   # Cold resistance
    COOLING = "cooling"                 # Heat resistance
    HAZARD_RESIST = "hazard_resist"     # Environmental damage reduction
    
    # Mental
    COMFORT = "comfort"                 # Mood bonus
    FOCUS = "focus"                     # Work quality
    STRESS_RESIST = "stress_resist"     # Stress reduction
    
    # Social
    CHARISMA = "charisma"               # Social interactions
    INTIMIDATION = "intimidation"       # Threat presence


# ============================================================================
# Conditional Triggers - When bonuses apply
# ============================================================================

class TriggerType(Enum):
    """Conditions that can trigger bonus effects."""
    ALWAYS = "always"                   # Always active
    
    # Environmental
    NEAR_FIRE = "near_fire"
    NEAR_WATER = "near_water"
    NEAR_TREES = "near_trees"
    IN_COLD = "in_cold"
    IN_HEAT = "in_heat"
    OUTDOORS = "outdoors"
    INDOORS = "indoors"
    IN_DARKNESS = "in_darkness"
    IN_LIGHT = "in_light"
    
    # Situational
    WHILE_WORKING = "while_working"
    WHILE_IDLE = "while_idle"
    WHILE_MOVING = "while_moving"
    WHEN_HUNGRY = "when_hungry"
    WHEN_STRESSED = "when_stressed"
    WHEN_CALM = "when_calm"
    
    # Proximity
    NEAR_COLONISTS = "near_colonists"
    ALONE = "alone"
    NEAR_ANIMALS = "near_animals"
    
    # Whimsical (for flavor)
    NEAR_ACORNS = "near_acorns"
    NEAR_RUST = "near_rust"
    NEAR_ECHOES = "near_echoes"
    DURING_RAIN = "during_rain"
    AT_DAWN = "at_dawn"
    AT_DUSK = "at_dusk"


# ============================================================================
# Stat Modifier - A single stat change with optional condition
# ============================================================================

@dataclass
class StatModifier:
    """A single stat modification, possibly conditional."""
    stat: StatType
    value: float                        # Positive = bonus, negative = penalty
    trigger: TriggerType = TriggerType.ALWAYS
    
    def describe(self) -> str:
        """Human-readable description of this modifier."""
        sign = "+" if self.value >= 0 else ""
        stat_name = self.stat.value.replace("_", " ").title()
        
        if self.trigger == TriggerType.ALWAYS:
            return f"{sign}{self.value:.1f} {stat_name}"
        else:
            trigger_name = self.trigger.value.replace("_", " ")
            return f"{sign}{self.value:.1f} {stat_name} ({trigger_name})"


# ============================================================================
# Item Components - Building blocks for procedural items
# ============================================================================

@dataclass
class ItemComponent:
    """A component that contributes to an item's name and stats."""
    id: str
    name_fragment: str                  # e.g., "Wind's", "of the Fallen", "Scarf"
    position: str                       # "prefix", "base", "suffix"
    slot: Optional[str] = None          # Required slot (only for base components)
    tags: List[str] = field(default_factory=list)
    modifiers: List[StatModifier] = field(default_factory=list)
    flavor: str = ""                    # Flavor text contribution
    rarity_weight: float = 1.0          # Higher = more common


# ============================================================================
# Component Pools - Collections of components by type
# ============================================================================

# Prefix components (adjectives, origins)
PREFIX_POOL: List[ItemComponent] = []

# Base components (the actual item type)
BASE_POOL: List[ItemComponent] = []

# Suffix components (of the X, enchantments)
SUFFIX_POOL: List[ItemComponent] = []


def register_prefix(component: ItemComponent) -> None:
    """Register a prefix component."""
    component.position = "prefix"
    PREFIX_POOL.append(component)


def register_base(component: ItemComponent) -> None:
    """Register a base item component."""
    component.position = "base"
    BASE_POOL.append(component)


def register_suffix(component: ItemComponent) -> None:
    """Register a suffix component."""
    component.position = "suffix"
    SUFFIX_POOL.append(component)


# ============================================================================
# Default Component Definitions
# ============================================================================

# --- Prefixes (adjectives, materials, origins) ---

register_prefix(ItemComponent(
    id="worn",
    name_fragment="Worn",
    position="prefix",
    tags=["common", "old"],
    modifiers=[],
    rarity_weight=3.0,
))

register_prefix(ItemComponent(
    id="sturdy",
    name_fragment="Sturdy",
    position="prefix",
    tags=["quality"],
    modifiers=[StatModifier(StatType.HAZARD_RESIST, 0.1)],
    rarity_weight=2.0,
))

register_prefix(ItemComponent(
    id="swift",
    name_fragment="Swift",
    position="prefix",
    tags=["speed"],
    modifiers=[StatModifier(StatType.WALK_SPEED, 0.1)],
    rarity_weight=1.5,
))

register_prefix(ItemComponent(
    id="winds",
    name_fragment="Wind's",
    position="prefix",
    tags=["elemental", "air"],
    modifiers=[
        StatModifier(StatType.WALK_SPEED, 0.05),
        StatModifier(StatType.COOLING, 0.1, TriggerType.IN_HEAT),
    ],
    rarity_weight=0.8,
))

register_prefix(ItemComponent(
    id="ember",
    name_fragment="Ember",
    position="prefix",
    tags=["elemental", "fire"],
    modifiers=[
        StatModifier(StatType.WARMTH, 0.15),
        StatModifier(StatType.COMFORT, 0.05, TriggerType.IN_COLD),
    ],
    rarity_weight=0.8,
))

register_prefix(ItemComponent(
    id="silent",
    name_fragment="Silent",
    position="prefix",
    tags=["stealth"],
    modifiers=[StatModifier(StatType.HEARING, 0.1)],
    rarity_weight=1.2,
))

register_prefix(ItemComponent(
    id="heavy",
    name_fragment="Heavy",
    position="prefix",
    tags=["weight"],
    modifiers=[
        StatModifier(StatType.WALK_SPEED, -0.1),
        StatModifier(StatType.WALK_STEADY, 0.2),
        StatModifier(StatType.HAZARD_RESIST, 0.15),
    ],
    rarity_weight=1.5,
))

register_prefix(ItemComponent(
    id="lucky",
    name_fragment="Lucky",
    position="prefix",
    tags=["fortune"],
    modifiers=[StatModifier(StatType.COMFORT, 0.1)],
    rarity_weight=1.0,
))

register_prefix(ItemComponent(
    id="focused",
    name_fragment="Focused",
    position="prefix",
    tags=["mental"],
    modifiers=[
        StatModifier(StatType.FOCUS, 0.15),
        StatModifier(StatType.BUILD_SPEED, 0.05),
    ],
    rarity_weight=1.0,
))

register_prefix(ItemComponent(
    id="rusted",
    name_fragment="Rusted",
    position="prefix",
    tags=["decay", "old"],
    modifiers=[
        StatModifier(StatType.HAZARD_RESIST, -0.05),
        StatModifier(StatType.COMFORT, 0.1, TriggerType.NEAR_RUST),
    ],
    rarity_weight=2.5,
))

# --- Base Items (the actual equipment) ---

register_base(ItemComponent(
    id="scarf",
    name_fragment="Scarf",
    position="base",
    slot="head",
    tags=["clothing", "neck"],
    modifiers=[StatModifier(StatType.WARMTH, 0.05)],
    rarity_weight=2.0,
))

register_base(ItemComponent(
    id="hood",
    name_fragment="Hood",
    position="base",
    slot="head",
    tags=["clothing", "head"],
    modifiers=[StatModifier(StatType.VISION, -0.05)],
    rarity_weight=2.0,
))

register_base(ItemComponent(
    id="goggles",
    name_fragment="Goggles",
    position="base",
    slot="head",
    tags=["eyewear", "tech"],
    modifiers=[StatModifier(StatType.VISION, 0.1)],
    rarity_weight=1.5,
))

register_base(ItemComponent(
    id="jacket",
    name_fragment="Jacket",
    position="base",
    slot="body",
    tags=["clothing", "torso"],
    modifiers=[
        StatModifier(StatType.WARMTH, 0.1),
        StatModifier(StatType.HAZARD_RESIST, 0.05),
    ],
    rarity_weight=2.0,
))

register_base(ItemComponent(
    id="vest",
    name_fragment="Vest",
    position="base",
    slot="body",
    tags=["clothing", "torso"],
    modifiers=[StatModifier(StatType.HAUL_CAPACITY, 0.1)],
    rarity_weight=2.0,
))

register_base(ItemComponent(
    id="gloves",
    name_fragment="Gloves",
    position="base",
    slot="hands",
    tags=["clothing", "hands"],
    modifiers=[StatModifier(StatType.BUILD_SPEED, 0.05)],
    rarity_weight=2.0,
))

register_base(ItemComponent(
    id="gauntlets",
    name_fragment="Gauntlets",
    position="base",
    slot="hands",
    tags=["armor", "hands"],
    modifiers=[
        StatModifier(StatType.HAZARD_RESIST, 0.1),
        StatModifier(StatType.CRAFT_SPEED, -0.05),
    ],
    rarity_weight=1.0,
))

register_base(ItemComponent(
    id="boots",
    name_fragment="Boots",
    position="base",
    slot="feet",
    tags=["footwear"],
    modifiers=[StatModifier(StatType.WALK_STEADY, 0.1)],
    rarity_weight=2.0,
))

register_base(ItemComponent(
    id="sandals",
    name_fragment="Sandals",
    position="base",
    slot="feet",
    tags=["footwear", "light"],
    modifiers=[
        StatModifier(StatType.WALK_SPEED, 0.1),
        StatModifier(StatType.WALK_STEADY, -0.1),
    ],
    rarity_weight=1.5,
))

register_base(ItemComponent(
    id="chip",
    name_fragment="Chip",
    position="base",
    slot="implant",
    tags=["tech", "implant"],
    modifiers=[StatModifier(StatType.FOCUS, 0.1)],
    rarity_weight=1.0,
))

register_base(ItemComponent(
    id="pendant",
    name_fragment="Pendant",
    position="base",
    slot="charm",
    tags=["jewelry", "charm"],
    modifiers=[StatModifier(StatType.COMFORT, 0.05)],
    rarity_weight=1.5,
))

register_base(ItemComponent(
    id="coin",
    name_fragment="Coin",
    position="base",
    slot="charm",
    tags=["trinket", "charm"],
    modifiers=[],
    rarity_weight=2.0,
))

register_base(ItemComponent(
    id="stone",
    name_fragment="Stone",
    position="base",
    slot="charm",
    tags=["natural", "charm"],
    modifiers=[StatModifier(StatType.ECHO_SENSE, 0.05)],
    rarity_weight=1.5,
))

# --- Suffixes (of the X, enchantments) ---

register_suffix(ItemComponent(
    id="fallen_squirrel",
    name_fragment="of the Fallen Squirrel",
    position="suffix",
    tags=["whimsy", "nature"],
    modifiers=[
        StatModifier(StatType.WALK_SPEED, 0.05, TriggerType.IN_COLD),
        StatModifier(StatType.WARMTH, 0.1, TriggerType.NEAR_ACORNS),
    ],
    flavor="A strange warmth emanates when acorns are near.",
    rarity_weight=0.3,
))

register_suffix(ItemComponent(
    id="wanderer",
    name_fragment="of the Wanderer",
    position="suffix",
    tags=["travel"],
    modifiers=[
        StatModifier(StatType.WALK_SPEED, 0.1),
        StatModifier(StatType.COMFORT, 0.05, TriggerType.OUTDOORS),
    ],
    rarity_weight=0.8,
))

register_suffix(ItemComponent(
    id="builder",
    name_fragment="of the Builder",
    position="suffix",
    tags=["work", "construction"],
    modifiers=[
        StatModifier(StatType.BUILD_SPEED, 0.15),
        StatModifier(StatType.FOCUS, 0.05, TriggerType.WHILE_WORKING),
    ],
    rarity_weight=0.8,
))

register_suffix(ItemComponent(
    id="echoes",
    name_fragment="of Echoes",
    position="suffix",
    tags=["mystical", "sound"],
    modifiers=[
        StatModifier(StatType.ECHO_SENSE, 0.2),
        StatModifier(StatType.HEARING, 0.1),
        StatModifier(StatType.COMFORT, 0.1, TriggerType.NEAR_ECHOES),
    ],
    flavor="Whispers of distant places linger within.",
    rarity_weight=0.5,
))

register_suffix(ItemComponent(
    id="dawn",
    name_fragment="of Dawn",
    position="suffix",
    tags=["time", "light"],
    modifiers=[
        StatModifier(StatType.VISION, 0.1, TriggerType.AT_DAWN),
        StatModifier(StatType.COMFORT, 0.15, TriggerType.AT_DAWN),
    ],
    rarity_weight=0.6,
))

register_suffix(ItemComponent(
    id="solitude",
    name_fragment="of Solitude",
    position="suffix",
    tags=["social", "isolation"],
    modifiers=[
        StatModifier(StatType.FOCUS, 0.2, TriggerType.ALONE),
        StatModifier(StatType.STRESS_RESIST, 0.1, TriggerType.ALONE),
        StatModifier(StatType.COMFORT, -0.1, TriggerType.NEAR_COLONISTS),
    ],
    rarity_weight=0.7,
))

register_suffix(ItemComponent(
    id="rust",
    name_fragment="of Rust",
    position="suffix",
    tags=["decay", "salvage"],
    modifiers=[
        StatModifier(StatType.HARVEST_SPEED, 0.1),
        StatModifier(StatType.COMFORT, 0.1, TriggerType.NEAR_RUST),
    ],
    flavor="Finds beauty in decay.",
    rarity_weight=1.0,
))

register_suffix(ItemComponent(
    id="flame",
    name_fragment="of Flame",
    position="suffix",
    tags=["elemental", "fire"],
    modifiers=[
        StatModifier(StatType.WARMTH, 0.2),
        StatModifier(StatType.COMFORT, 0.15, TriggerType.NEAR_FIRE),
    ],
    rarity_weight=0.6,
))


# ============================================================================
# Generated Item - The result of procedural generation
# ============================================================================

@dataclass
class GeneratedItem:
    """A procedurally generated item."""
    id: str                             # Unique ID for this instance
    name: str                           # Full generated name
    slot: str                           # Equipment slot
    components: List[ItemComponent]     # Components used
    modifiers: List[StatModifier]       # All stat modifiers
    flavor: str                         # Combined flavor text
    tags: List[str]                     # Combined tags
    rarity: str                         # "common", "uncommon", "rare", "legendary"
    
    def get_stat_summary(self) -> Dict[str, float]:
        """Get total stats (ALWAYS triggers only)."""
        totals: Dict[str, float] = {}
        for mod in self.modifiers:
            if mod.trigger == TriggerType.ALWAYS:
                key = mod.stat.value
                totals[key] = totals.get(key, 0.0) + mod.value
        return totals
    
    def get_conditional_modifiers(self) -> List[StatModifier]:
        """Get all conditional modifiers."""
        return [m for m in self.modifiers if m.trigger != TriggerType.ALWAYS]
    
    def describe_stats(self) -> List[str]:
        """Get human-readable stat descriptions."""
        lines = []
        for mod in self.modifiers:
            lines.append(mod.describe())
        return lines


# ============================================================================
# Item Generator - Creates random items from component pools
# ============================================================================

_next_item_id = 0


def generate_item(
    slot: Optional[str] = None,
    min_components: int = 1,
    max_components: int = 3,
    force_suffix: bool = False,
) -> GeneratedItem:
    """Generate a random item.
    
    Args:
        slot: Force a specific slot, or None for random
        min_components: Minimum number of components (1-3)
        max_components: Maximum number of components (1-3)
        force_suffix: Always include a suffix (for rarer items)
    
    Returns:
        A newly generated item
    """
    global _next_item_id
    
    # Select base item (determines slot)
    if slot:
        valid_bases = [b for b in BASE_POOL if b.slot == slot]
    else:
        valid_bases = BASE_POOL
    
    if not valid_bases:
        valid_bases = BASE_POOL
    
    base = _weighted_choice(valid_bases)
    
    # Determine component count
    num_components = random.randint(min_components, max_components)
    has_prefix = num_components >= 2 or random.random() < 0.3
    has_suffix = num_components >= 3 or force_suffix or random.random() < 0.2
    
    # Select prefix
    prefix = None
    if has_prefix and PREFIX_POOL:
        prefix = _weighted_choice(PREFIX_POOL)
    
    # Select suffix
    suffix = None
    if has_suffix and SUFFIX_POOL:
        suffix = _weighted_choice(SUFFIX_POOL)
    
    # Build name
    name_parts = []
    if prefix:
        name_parts.append(prefix.name_fragment)
    name_parts.append(base.name_fragment)
    if suffix:
        name_parts.append(suffix.name_fragment)
    name = " ".join(name_parts)
    
    # Collect components
    components = [c for c in [prefix, base, suffix] if c is not None]
    
    # Collect modifiers
    modifiers = []
    for comp in components:
        modifiers.extend(comp.modifiers)
    
    # Collect tags
    tags = []
    for comp in components:
        tags.extend(comp.tags)
    tags = list(set(tags))  # Dedupe
    
    # Collect flavor
    flavor_parts = [c.flavor for c in components if c.flavor]
    flavor = " ".join(flavor_parts)
    
    # Determine rarity based on components
    rarity = _calculate_rarity(components)
    
    # Generate unique ID
    _next_item_id += 1
    item_id = f"gen_{_next_item_id}_{base.id}"
    
    return GeneratedItem(
        id=item_id,
        name=name,
        slot=base.slot,
        components=components,
        modifiers=modifiers,
        flavor=flavor,
        tags=tags,
        rarity=rarity,
    )


def _weighted_choice(pool: List[ItemComponent]) -> ItemComponent:
    """Select a random component weighted by rarity_weight."""
    total = sum(c.rarity_weight for c in pool)
    r = random.random() * total
    cumulative = 0.0
    for comp in pool:
        cumulative += comp.rarity_weight
        if r <= cumulative:
            return comp
    return pool[-1]


def _calculate_rarity(components: List[ItemComponent]) -> str:
    """Calculate item rarity based on component weights."""
    if not components:
        return "common"
    
    # Lower total weight = rarer
    avg_weight = sum(c.rarity_weight for c in components) / len(components)
    
    if avg_weight < 0.5:
        return "legendary"
    elif avg_weight < 0.8:
        return "rare"
    elif avg_weight < 1.2:
        return "uncommon"
    else:
        return "common"


# ============================================================================
# Integration with existing item system
# ============================================================================

def generated_item_to_dict(item: GeneratedItem) -> dict:
    """Convert a GeneratedItem to a dict for colonist equipment."""
    return {
        "id": item.id,
        "name": item.name,
        "slot": item.slot,
        "generated": True,
        "rarity": item.rarity,
        "modifiers": [
            {
                "stat": m.stat.value,
                "value": m.value,
                "trigger": m.trigger.value,
            }
            for m in item.modifiers
        ],
        "tags": item.tags,
        "flavor": item.flavor,
    }


def get_generated_item_stats(item_dict: dict) -> Dict[str, float]:
    """Get total stats from a generated item dict (ALWAYS triggers only)."""
    if not item_dict.get("generated"):
        return {}
    
    totals: Dict[str, float] = {}
    for mod in item_dict.get("modifiers", []):
        if mod.get("trigger") == "always":
            stat = mod.get("stat", "")
            value = mod.get("value", 0.0)
            totals[stat] = totals.get(stat, 0.0) + value
    return totals


# ============================================================================
# Debug / Testing
# ============================================================================

def generate_test_items(count: int = 5) -> List[GeneratedItem]:
    """Generate test items for debugging."""
    items = []
    for _ in range(count):
        items.append(generate_item())
    return items


if __name__ == "__main__":
    # Test generation
    print("=== Procedural Item Generation Test ===\n")
    
    for i in range(10):
        item = generate_item()
        print(f"[{item.rarity.upper()}] {item.name}")
        print(f"  Slot: {item.slot}")
        print(f"  Tags: {', '.join(item.tags)}")
        print("  Stats:")
        for line in item.describe_stats():
            print(f"    {line}")
        if item.flavor:
            print(f"  \"{item.flavor}\"")
        print()
