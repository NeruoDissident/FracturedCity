"""
Shared UI configuration and data.

Contains all menu definitions, tooltips, and flavor text in one place.
Used by both ui_layout.py and any other UI components.
"""

from typing import Dict, Tuple, List

# ============================================================================
# TOOLTIPS / FLAVOR DESCRIPTIONS
# ============================================================================

# Format: {id: (title, description, extra_info)}
TOOLTIPS: Dict[str, Tuple[str, str, str]] = {
    # Walls
    "wall": (
        "Wooden Wall",
        "A basic wall made of wood. Blocks movement and line of sight.",
        "Cost: 2 wood"
    ),
    "wall_advanced": (
        "Reinforced Wall", 
        "A stronger wall made of minerals. More durable and provides better insulation.",
        "Cost: 2 mineral"
    ),
    
    # Floors
    "floor": (
        "Wood Floor",
        "Wooden flooring that makes rooms feel complete. Colonists prefer walking on floors.",
        "Cost: 1 wood"
    ),
    "stage": (
        "Stage Tiles",
        "Performance platform for musicians and entertainers. Drag to place multiple tiles.",
        "Cost: 1 wood, 1 scrap"
    ),
    "stage_stairs": (
        "Stage Stairs",
        "Access stairs for stage platforms. Click to place.",
        "Cost: 1 wood"
    ),
    
    # Access
    "door": (
        "Door",
        "Allows colonists to pass through walls. Opens and closes automatically.",
        "Cost: 1 wood, 1 metal"
    ),
    "bar_door": (
        "Bar Door",
        "Saloon-style swinging door. Perfect for bars and clubs.",
        "Cost: 1 wood, 1 scrap"
    ),
    "window": (
        "Window",
        "Colonists can pass through like a door. Lets light into rooms and can be opened for ventilation.",
        "Cost: 1 wood, 1 mineral"
    ),
    "fire_escape": (
        "Fire Escape",
        "Vertical ladder that provides access between floors. Must be placed on the edge of a building.",
        "Cost: 1 wood, 1 metal"
    ),
    "bridge": (
        "Bridge",
        "A horizontal walkway that spans gaps between buildings or over open areas.",
        "Cost: 2 wood, 1 metal"
    ),
    
    # Bar/Club
    "scrap_bar_counter": (
        "Scrap Bar Counter",
        "Rusty metal counter for serving drinks. The heart of any gutter bar.",
        "Cost: 2 scrap, 1 wood"
    ),
    "gutter_still": (
        "Gutter Still",
        "Makeshift distillery for brewing cheap booze. Turns raw food into liquid courage.",
        "Crafts: Swill, Guttershine"
    ),
    
    # Crafting Stations
    "spark_bench": (
        "Spark Bench",
        "Electronics workstation for salvaging and assembling components. Sparks fly when the tech gets real.",
        "Crafts: Wire, Resistors, Chips, LEDs"
    ),
    "tinker_station": (
        "Tinker Station",
        "General crafts bench for building instruments and improvised gear. Where junk becomes art.",
        "Crafts: Guitars, Drums, Synths, Amps"
    ),
    "salvagers_bench": (
        "Salvager's Bench",
        "Strip down scrap into usable metal. Essential for turning junk into the chrome that keeps your crew alive.",
        "Processes: Scrap → Metal"
    ),
    "generator": (
        "Generator",
        "Cranks out power cells to juice your machines. No cells, no craft - keep this thing humming.",
        "Produces: Power Cells"
    ),
    "stove": (
        "Stove",
        "Turns raw ingredients into actual food. Hot meals keep morale up and bellies full.",
        "Produces: Cooked Meals"
    ),
    "gutter_forge": (
        "Gutter Forge",
        "Where street iron gets hammered into blades and knuckle rigs. Crude but deadly.",
        "Crafts: Weapons, Armor, Furniture"
    ),
    "skinshop_loom": (
        "Skinshop Loom",
        "Stitches together armor from scavenged hides and synth-weave. Protection for the meat underneath.",
        "Crafts: Armor, Protective Gear"
    ),
    "cortex_spindle": (
        "Cortex Spindle",
        "Delicate work - neural implants, lucky charms, and trauma patches. Handles the stuff between your ears.",
        "Crafts: Implants, Charms, Medical"
    ),
    
    # Zones
    "stockpile": (
        "Stockpile Zone",
        "Designate an area for storing resources. Colonists will haul items here. Click and drag to create.",
        "Right-click stockpile to set filters"
    ),
    "allow": (
        "Allowed Area",
        "Mark tiles where colonists are allowed to walk. Use to restrict movement or create paths.",
        "Drag to paint allowed tiles"
    ),
    "roof_zone": (
        "Roof Zone",
        "Designate an area to be automatically roofed. Roofs provide shelter from weather.",
        "Requires enclosed walls"
    ),
    "demolish": (
        "Demolish",
        "Remove buildings, walls, floors, and other constructions. Resources are lost.",
        "Click or drag to demolish"
    ),
    
    # Tools
    "harvest": (
        "Harvest",
        "Gather resources from plants, trees, and resource nodes. Colonists will collect the materials.",
        "Click or drag to mark for harvest"
    ),
    "salvage": (
        "Salvage",
        "Carefully deconstruct buildings to recover some materials. Better than demolish for reclaiming resources.",
        "Click buildings to salvage"
    ),
}


# ============================================================================
# MENU DEFINITIONS
# ============================================================================

# Shared submenu definitions used by both LeftSidebar and BottomBuildBar
SUBMENUS: Dict[str, List[dict]] = {
    "build": [
        {"id": "wall", "name": "Wall", "cost": "2 wood"},
        {"id": "wall_advanced", "name": "Reinforced Wall", "cost": "2 mineral"},
        {"id": "scrap_bar_counter", "name": "Bar Counter", "cost": "2 scrap, 1 wood"},
    ],
    "floors": [
        {"id": "floor", "name": "Wood Floor", "cost": "1 wood"},
        {"id": "stage", "name": "Stage Tiles", "cost": "1 wood, 1 scrap"},
        {"id": "stage_stairs", "name": "Stage Stairs", "cost": "1 wood"},
    ],
    "access": [
        {"id": "door", "name": "Door", "cost": "1 wood, 1 metal"},
        {"id": "bar_door", "name": "Bar Door", "cost": "1 wood, 1 scrap"},
        {"id": "window", "name": "Window", "cost": "1 wood, 1 mineral"},
        {"id": "fire_escape", "name": "Fire Escape", "cost": "1 wood, 1 metal"},
        {"id": "bridge", "name": "Bridge", "cost": "2 wood, 1 metal"},
    ],
    "zone": [
        {"id": "stockpile", "name": "Stockpile"},
        {"id": "allow", "name": "Allow"},
        {"id": "roof", "name": "Roof"},
    ],
    "rooms": [
        {"id": "room_bedroom", "name": "Bedroom"},
        {"id": "room_kitchen", "name": "Kitchen"},
        {"id": "room_workshop", "name": "Workshop"},
        {"id": "room_barracks", "name": "Barracks"},
        {"id": "room_prison", "name": "Prison"},
        {"id": "room_hospital", "name": "Hospital"},
        {"id": "room_rec_room", "name": "Rec Room"},
        {"id": "room_dining_hall", "name": "Dining Hall"},
    ],
    "demolish": [
        {"id": "demolish", "name": "Demolish"},
    ],
    "salvage": [
        {"id": "salvage", "name": "Salvage"},
    ],
    "harvest": [
        {"id": "harvest", "name": "Harvest"},
    ],
    # stations and furniture are populated dynamically at runtime
}


def get_tooltip(item_id: str) -> Tuple[str, str, str]:
    """Get tooltip data for an item.
    
    Returns:
        (title, description, extra_info) tuple
        If not found, returns generic tooltip
    """
    if item_id in TOOLTIPS:
        return TOOLTIPS[item_id]
    
    # Generic fallback
    title = item_id.replace("_", " ").title()
    return (title, "No description available.", "")


def add_tooltip(item_id: str, title: str, description: str, extra: str = "") -> None:
    """Add or update a tooltip dynamically (for runtime-generated items)."""
    TOOLTIPS[item_id] = (title, description, extra)


def get_submenu(category: str) -> List[dict]:
    """Get submenu items for a category.
    
    Returns empty list if category doesn't exist.
    """
    return SUBMENUS.get(category, [])
