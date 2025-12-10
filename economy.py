"""
Economy and Barter System for Fractured City.

Fixers are wandering traders with personality-driven pricing.
- Each item has a base trade value
- Fixers have origins that affect what they have/want
- Barter is item-for-item, no currency

Fixer Origins:
- Timberland: Forest dwellers, plenty of wood, crave tech
- Spire: Tower folk, have tech/power, need food/comfort
- Rustfield: Scavengers from ruins, have scrap, need everything
- Driftway: Nomads from wastes, desperate, will trade anything
- Enclave: Settled folk, balanced, want luxury items
"""

import random
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field


# =============================================================================
# BASE TRADE VALUES
# =============================================================================

# Base value for resources (used in barter calculations)
RESOURCE_VALUES: Dict[str, int] = {
    # Raw resources
    "wood": 5,
    "mineral": 8,
    "scrap": 3,
    "metal": 12,
    "power": 15,
    "raw_food": 4,
    "cooked_meal": 10,
    
    # Crafted furniture
    "crash_bed": 25,
    
    # Crafted equipment (from buildings.py recipes)
    "shiv": 15,
    "pipe_wrench": 20,
    "knuckle_rig": 25,
    "padded_jacket": 30,
    "work_boots": 20,
    "scrap_armor": 45,
    
    # Implants/medical (cortex_spindle)
    "cortex_chip": 50,
    "trauma_patch": 35,
    "lucky_charm": 40,
    
    # Processed resources
    "power_cell": 18,
}

# Category mappings for modifier application
ITEM_CATEGORIES: Dict[str, str] = {
    # Resources
    "wood": "organic",
    "mineral": "mineral",
    "scrap": "scrap",
    "metal": "metal",
    "power": "tech",
    "raw_food": "food",
    "cooked_meal": "food",
    
    # Equipment
    "shiv": "weapon",
    "pipe_wrench": "tool",
    "knuckle_rig": "weapon",
    "padded_jacket": "armor",
    "work_boots": "armor",
    "scrap_armor": "armor",
    
    # Tech/Medical
    "cortex_chip": "tech",
    "trauma_patch": "medical",
    "lucky_charm": "charm",
    "power_cell": "tech",
    
    # Furniture
    "crash_bed": "comfort",
}


def get_base_value(item_id: str) -> int:
    """Get base trade value for an item."""
    return RESOURCE_VALUES.get(item_id, 10)  # Default 10 for unknown items


def get_item_category(item_id: str) -> str:
    """Get trade category for an item."""
    return ITEM_CATEGORIES.get(item_id, "misc")


# =============================================================================
# FIXER ORIGINS
# =============================================================================

@dataclass
class FixerOrigin:
    """Defines a fixer's background and trade preferences."""
    id: str
    name: str                    # Display name
    description: str             # Flavor text
    
    # Category modifiers: <1.0 = has plenty, >1.0 = wants badly
    modifiers: Dict[str, float] = field(default_factory=dict)
    
    # What they typically carry (for inventory generation)
    common_stock: List[str] = field(default_factory=list)
    rare_stock: List[str] = field(default_factory=list)


# Origin definitions
FIXER_ORIGINS: Dict[str, FixerOrigin] = {}


def _register_origins():
    """Register all fixer origin types."""
    
    # Timberland - Forest folk
    FIXER_ORIGINS["timberland"] = FixerOrigin(
        id="timberland",
        name="Timberland",
        description="From the overgrown sectors where nature reclaimed the concrete.",
        modifiers={
            "organic": 0.5,    # Has plenty of wood
            "food": 0.7,       # Decent food supply
            "tech": 2.0,       # Craves technology
            "metal": 1.5,      # Needs metal
            "scrap": 1.0,      # Neutral
            "mineral": 1.2,    # Slightly wants
            "weapon": 1.3,     # Could use weapons
            "armor": 1.0,      # Neutral
            "medical": 1.4,    # Wants medical
            "charm": 1.8,      # Superstitious, loves charms
            "comfort": 0.8,    # Has comfort items
        },
        common_stock=["wood", "raw_food", "lucky_charm"],
        rare_stock=["cooked_meal", "padded_jacket"],
    )
    
    # Spire - Tower dwellers
    FIXER_ORIGINS["spire"] = FixerOrigin(
        id="spire",
        name="Spire",
        description="Descended from the signal towers. Still hears the ghost frequencies.",
        modifiers={
            "organic": 1.8,    # Desperately needs wood
            "food": 2.0,       # Very hungry
            "tech": 0.4,       # Has tons of tech
            "metal": 0.7,      # Has metal
            "scrap": 1.2,      # Could use scrap
            "mineral": 1.0,    # Neutral
            "weapon": 0.8,     # Has some weapons
            "armor": 1.3,      # Wants armor
            "medical": 0.6,    # Has medical
            "charm": 0.5,      # Has charms (tower trinkets)
            "comfort": 1.5,    # Wants comfort
        },
        common_stock=["power", "cortex_chip", "power_cell"],
        rare_stock=["trauma_patch", "metal"],
    )
    
    # Rustfield - Ruin scavengers
    FIXER_ORIGINS["rustfield"] = FixerOrigin(
        id="rustfield",
        name="Rustfield",
        description="Crawled out of the collapsed sectors. Knows every bolt and beam.",
        modifiers={
            "organic": 1.6,    # Needs wood
            "food": 1.8,       # Hungry
            "tech": 1.4,       # Wants tech
            "metal": 0.6,      # Has metal
            "scrap": 0.4,      # Drowning in scrap
            "mineral": 0.5,    # Has minerals
            "weapon": 0.7,     # Has crude weapons
            "armor": 0.8,      # Has scrap armor
            "medical": 1.5,    # Needs medical
            "charm": 1.2,      # Mildly superstitious
            "comfort": 1.7,    # Wants comfort badly
        },
        common_stock=["scrap", "mineral", "metal", "shiv"],
        rare_stock=["scrap_armor", "knuckle_rig"],
    )
    
    # Driftway - Wasteland nomads
    FIXER_ORIGINS["driftway"] = FixerOrigin(
        id="driftway",
        name="Driftway",
        description="Wanderer from the dead zones. Trades anything to survive another day.",
        modifiers={
            "organic": 1.3,
            "food": 1.5,
            "tech": 1.2,
            "metal": 1.1,
            "scrap": 0.9,
            "mineral": 1.0,
            "weapon": 1.4,
            "armor": 1.3,
            "medical": 1.6,
            "charm": 1.1,
            "comfort": 1.4,
        },
        common_stock=["scrap", "raw_food"],
        rare_stock=["work_boots", "pipe_wrench"],
    )
    
    # Enclave - Settled community
    FIXER_ORIGINS["enclave"] = FixerOrigin(
        id="enclave",
        name="Enclave",
        description="From a stable settlement. Trades for profit, not survival.",
        modifiers={
            "organic": 1.0,
            "food": 0.9,
            "tech": 1.1,
            "metal": 1.0,
            "scrap": 1.1,
            "mineral": 1.0,
            "weapon": 1.2,
            "armor": 1.1,
            "medical": 1.0,
            "charm": 1.5,      # Loves luxury/charm items
            "comfort": 1.3,    # Wants comfort
        },
        common_stock=["cooked_meal", "metal", "power_cell"],
        rare_stock=["cortex_chip", "padded_jacket", "crash_bed"],
    )


_register_origins()


def get_origin(origin_id: str) -> Optional[FixerOrigin]:
    """Get origin definition by ID."""
    return FIXER_ORIGINS.get(origin_id)


def get_random_origin() -> FixerOrigin:
    """Get a random fixer origin."""
    return random.choice(list(FIXER_ORIGINS.values()))


# =============================================================================
# FIXER NAMES
# =============================================================================

FIXER_FIRST_NAMES = [
    "Slink", "Raze", "Volt", "Crank", "Sever", "Glitch", "Torque", "Rivet",
    "Scorch", "Flicker", "Grind", "Splice", "Jolt", "Rust", "Chrome", "Neon",
    "Haze", "Drift", "Shard", "Vex", "Kink", "Wrench", "Spark", "Fuse",
    "Coil", "Blade", "Patch", "Wire", "Bolt", "Gear", "Piston", "Axle",
]

FIXER_LAST_NAMES = [
    "Hexbolt", "Ironside", "Coldwire", "Blackhand", "Rustborn", "Voidwalker",
    "Steelgrave", "Ashfall", "Driftwood", "Shadowjack", "Burnside", "Hollowpoint",
    "Deadlock", "Razorback", "Nightcoil", "Grimweld", "Dustrunner", "Scrapheap",
    "Flickerjack", "Boneyard", "Ghostwire", "Ironlung", "Shatterproof", "Lowvolt",
]

FIXER_TITLES = [
    "the Fixer", "the Scrounger", "the Haggler", "the Dealer", "the Broker",
    "the Peddler", "the Hustler", "the Runner", "the Mover", "the Connect",
]


def generate_fixer_name() -> str:
    """Generate a cyberpunk fixer name."""
    first = random.choice(FIXER_FIRST_NAMES)
    last = random.choice(FIXER_LAST_NAMES)
    
    # 30% chance for a title
    if random.random() < 0.3:
        title = random.choice(FIXER_TITLES)
        return f"{first} {last}, {title}"
    
    return f"{first} {last}"


# =============================================================================
# TRADE CALCULATIONS
# =============================================================================

def calculate_fixer_price(item_id: str, origin: FixerOrigin, is_buying: bool) -> int:
    """Calculate what a fixer will pay/charge for an item.
    
    Args:
        item_id: The item being traded
        origin: The fixer's origin (affects modifiers)
        is_buying: True if fixer is buying from player, False if selling to player
    
    Returns:
        Trade value in barter points
    """
    base = get_base_value(item_id)
    category = get_item_category(item_id)
    
    # Get modifier for this category
    modifier = origin.modifiers.get(category, 1.0)
    
    if is_buying:
        # Fixer buying from player - they pay more for things they want
        # But still try to profit (0.9 multiplier)
        return int(base * modifier * 0.9)
    else:
        # Fixer selling to player - they charge more for things they want to keep
        # And add profit margin (1.1 multiplier)
        # Inverse modifier: if they have plenty, sell cheap
        sell_modifier = 2.0 - modifier  # Inverts: 0.5 becomes 1.5, 2.0 becomes 0.0
        sell_modifier = max(0.3, min(2.0, sell_modifier))  # Clamp
        return int(base * sell_modifier * 1.1)


def calculate_trade_value(items: List[Tuple[str, int]], origin: FixerOrigin, is_player_offering: bool) -> int:
    """Calculate total trade value for a list of items.
    
    Args:
        items: List of (item_id, quantity) tuples
        origin: Fixer's origin
        is_player_offering: True if these are player's items (fixer buying)
    
    Returns:
        Total barter value
    """
    total = 0
    for item_id, qty in items:
        price = calculate_fixer_price(item_id, origin, is_buying=is_player_offering)
        total += price * qty
    return total


def is_fair_trade(player_items: List[Tuple[str, int]], 
                  fixer_items: List[Tuple[str, int]], 
                  origin: FixerOrigin,
                  tolerance: float = 0.1) -> bool:
    """Check if a proposed trade is fair (within tolerance).
    
    Args:
        player_items: What player is offering
        fixer_items: What fixer is offering
        origin: Fixer's origin
        tolerance: How much imbalance is acceptable (0.1 = 10%)
    
    Returns:
        True if trade is acceptable to fixer
    """
    player_value = calculate_trade_value(player_items, origin, is_player_offering=True)
    fixer_value = calculate_trade_value(fixer_items, origin, is_player_offering=False)
    
    if fixer_value == 0:
        return player_value > 0  # Fixer always accepts free stuff
    
    ratio = player_value / fixer_value
    return ratio >= (1.0 - tolerance)


# =============================================================================
# FIXER INVENTORY GENERATION
# =============================================================================

def generate_fixer_inventory(origin: FixerOrigin) -> Dict[str, int]:
    """Generate random inventory for a fixer based on their origin.
    
    Returns dict of {item_id: quantity}
    """
    inventory: Dict[str, int] = {}
    
    # Add common stock (2-5 of each, 80% chance per item)
    for item_id in origin.common_stock:
        if random.random() < 0.8:
            inventory[item_id] = random.randint(2, 5)
    
    # Add rare stock (1-2 of each, 30% chance per item)
    for item_id in origin.rare_stock:
        if random.random() < 0.3:
            inventory[item_id] = random.randint(1, 2)
    
    # Always have at least something
    if not inventory and origin.common_stock:
        item_id = random.choice(origin.common_stock)
        inventory[item_id] = random.randint(1, 3)
    
    return inventory
