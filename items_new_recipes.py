"""
New item definitions for expanded recipe system.

Add these to items.py by importing and calling register_item() for each.
"""

from items import ItemDef, register_item

# ============================================================================
# FURNITURE - Room-specific items
# ============================================================================

# Workshop furniture
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

# Comfort furniture
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

# Dining furniture
register_item(ItemDef(
    id="dining_table",
    name="Dining Table",
    slot=None,
    tags=["furniture", "dining"],
    icon_color=(130, 100, 70),
    description="Large table for communal meals."
))

# Lighting
register_item(ItemDef(
    id="wall_lamp",
    name="Wall Lamp",
    slot=None,
    tags=["furniture", "lighting"],
    icon_color=(220, 200, 100),
    description="Electric lamp that illuminates a room."
))

# Military furniture
register_item(ItemDef(
    id="weapon_rack",
    name="Weapon Rack",
    slot=None,
    tags=["furniture", "military", "storage"],
    icon_color=(100, 100, 110),
    description="Rack for storing weapons and combat gear."
))

# ============================================================================
# WEAPONS - Hands slot, combat-focused
# ============================================================================

register_item(ItemDef(
    id="pipe_weapon",
    name="Pipe Weapon",
    slot="hands",
    tags=["weapon", "melee"],
    work_bonus=-0.05,  # Not great for work
    icon_color=(120, 110, 100),
    description="Heavy metal pipe, effective as a club."
))

register_item(ItemDef(
    id="scrap_blade",
    name="Scrap Blade",
    slot="hands",
    tags=["weapon", "melee"],
    work_bonus=-0.1,  # Worse for work
    icon_color=(140, 130, 120),
    description="Sharpened metal blade fashioned from salvage."
))

# ============================================================================
# ARMOR & PROTECTIVE GEAR - Body/Hands slots
# ============================================================================

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

# ============================================================================
# TECH & MEDICAL - Implant/Charm slots
# ============================================================================

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
    hazard_resist=-0.05,  # Trade-off
    icon_color=(200, 100, 100),
    description="Auto-injector for performance enhancement."
))

register_item(ItemDef(
    id="neural_interface",
    name="Neural Interface",
    slot="implant",
    tags=["tech", "advanced"],
    work_bonus=0.2,
    comfort=-0.05,  # Invasive
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

# ============================================================================
# BUILDING COMPONENTS - Non-equippable
# ============================================================================

register_item(ItemDef(
    id="reinforced_door",
    name="Reinforced Door",
    slot=None,
    tags=["building", "security"],
    icon_color=(100, 100, 110),
    description="Heavy-duty door for secure areas."
))
