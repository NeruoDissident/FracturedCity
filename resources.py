"""Resource nodes and ground resource piles.

This module owns:
- definitions and storage for resource nodes in the world
- resource piles dropped on the ground
- helper functions for spawning nodes and harvesting them
- node types: trees, scrap piles, mineral nodes
- depletion and regrowth timer scaffolding
- node states for visual feedback (IDLE, RESERVED, IN_PROGRESS, DEPLETED)

Tiles themselves are still represented in the grid as simple string markers
("resource_node", "resource_pile"). All richer data lives here and is
accessed by other systems (jobs, colonists, etc.).
"""

from __future__ import annotations

import random
from enum import Enum
from typing import Dict, Tuple, Optional

from config import GRID_W, GRID_H


# Node states for visual feedback
class NodeState(Enum):
    IDLE = "idle"           # No colonist assigned
    RESERVED = "reserved"   # Colonist assigned, en route
    IN_PROGRESS = "in_progress"  # Colonist actively harvesting
    YIELDED = "yielded"     # Harvesting done, resource item spawned on tile
    DEPLETED = "depleted"   # Fully harvested, waiting to respawn

Coord = Tuple[int, int]
Coord3D = Tuple[int, int, int]  # (x, y, z)

# Simple in-memory registries keyed by (x, y) for nodes (ground level only).
_RESOURCE_NODES: Dict[Coord, dict] = {}
_RESOURCE_PILES: Dict[Coord, dict] = {}

# Resource items use 3D coordinates - can exist on any Z-level
_RESOURCE_ITEMS: Dict[Coord3D, dict] = {}  # Dropped resource items awaiting pickup

# Global stockpile - total resources collected by the colony
_STOCKPILE: Dict[str, int] = {
    "wood": 0,
    "scrap": 0,
    "mineral": 0,
    "metal": 0,  # Refined from scrap at Salvager's Bench
    "power": 0,  # Generated at Generator station
    "raw_food": 0,  # Harvested from food nodes
    "cooked_meal": 0,  # Cooked at Stove
}

# Reserved resources - resources allocated to pending construction jobs
_RESERVED: Dict[str, int] = {
    "wood": 0,
    "scrap": 0,
    "mineral": 0,
    "metal": 0,
    "power": 0,
    "raw_food": 0,
    "cooked_meal": 0,
}


def get_stockpile() -> Dict[str, int]:
    """Return the current global stockpile counts."""
    return _STOCKPILE.copy()


def add_to_stockpile(resource_type: str, amount: int = 1) -> None:
    """Add resources to the global stockpile."""
    if resource_type in _STOCKPILE:
        _STOCKPILE[resource_type] += amount
    else:
        _STOCKPILE[resource_type] = amount


def spend_from_stockpile(resource_type: str, amount: int = 1) -> bool:
    """Spend resources from stockpile. Returns True if successful.
    
    Will spend even if stockpile goes negative (for deficit tracking).
    """
    if resource_type not in _STOCKPILE:
        _STOCKPILE[resource_type] = 0
    _STOCKPILE[resource_type] -= amount
    return True


def get_stockpile_amount(resource_type: str) -> int:
    """Get the current amount of a specific resource."""
    return _STOCKPILE.get(resource_type, 0)


def reserve_resources(costs: Dict[str, int]) -> None:
    """Reserve resources for a pending construction job.
    
    This tracks what resources are needed but not yet available.
    """
    for resource, amount in costs.items():
        if resource not in _RESERVED:
            _RESERVED[resource] = 0
        _RESERVED[resource] += amount


def unreserve_resources(costs: Dict[str, int]) -> None:
    """Remove resource reservation (e.g., when construction completes or is cancelled)."""
    for resource, amount in costs.items():
        if resource in _RESERVED:
            _RESERVED[resource] = max(0, _RESERVED[resource] - amount)


def consume_reserved_resources(costs: Dict[str, int]) -> bool:
    """Consume resources from stockpile for a construction job.
    
    Only succeeds if stockpile has enough. Also removes from reserved.
    Returns True if successful.
    """
    # Check if we have enough
    for resource, amount in costs.items():
        if _STOCKPILE.get(resource, 0) < amount:
            return False
    
    # Consume from stockpile and remove reservation
    for resource, amount in costs.items():
        _STOCKPILE[resource] -= amount
        if resource in _RESERVED:
            _RESERVED[resource] = max(0, _RESERVED[resource] - amount)
    
    return True


def can_afford_costs(costs: Dict[str, int]) -> bool:
    """Check if stockpile has enough resources for the given costs."""
    for resource, amount in costs.items():
        if _STOCKPILE.get(resource, 0) < amount:
            return False
    return True


def get_available_resources() -> Dict[str, int]:
    """Return available resources (stockpile)."""
    return _STOCKPILE.copy()


def get_reserved_resources() -> Dict[str, int]:
    """Return reserved resources (pending construction)."""
    return _RESERVED.copy()


def get_resource_balance() -> Dict[str, int]:
    """Return effective balance (stockpile - reserved).
    
    Negative values indicate deficit - more reserved than available.
    """
    balance = {}
    all_resources = set(_STOCKPILE.keys()) | set(_RESERVED.keys())
    for resource in all_resources:
        balance[resource] = _STOCKPILE.get(resource, 0) - _RESERVED.get(resource, 0)
    return balance


def has_resource_deficit() -> bool:
    """Return True if reserved resources exceed stockpile (deficit)."""
    balance = get_resource_balance()
    for amount in balance.values():
        if amount < 0:
            return True
    return False


def can_afford_construction() -> bool:
    """Return True if stockpile has enough for at least one wall.
    
    Used to determine if colonists should take construction jobs.
    Checks actual stockpile, not balance, since each job consumes independently.
    """
    # Check if we have at least 1 wood and 1 mineral (cost of one wall)
    return _STOCKPILE.get("wood", 0) >= 1 and _STOCKPILE.get("mineral", 0) >= 1


# --- Resource items (dropped items on tiles) ----------------------------------


def spawn_resource_item(x: int, y: int, z: int, resource_type: str, amount: int = 1, 
                        auto_haul: bool = False) -> None:
    """Spawn a resource item on the tile at (x, y, z).
    
    If an item already exists at this location, add to its amount.
    
    Args:
        x, y, z: Tile coordinates
        resource_type: Type of resource
        amount: Amount to spawn
        auto_haul: If True, item will be automatically queued for hauling
                   (used for harvested resources like wood, mineral)
    """
    coord = (x, y, z)
    if coord in _RESOURCE_ITEMS:
        _RESOURCE_ITEMS[coord]["amount"] += amount
        # If new spawn requests auto_haul, enable it
        if auto_haul:
            _RESOURCE_ITEMS[coord]["haul_requested"] = True
    else:
        _RESOURCE_ITEMS[coord] = {
            "type": resource_type,
            "amount": amount,
            "haul_requested": auto_haul,  # Whether this needs to be hauled
        }


def get_resource_item_at(x: int, y: int, z: int = 0) -> Optional[dict]:
    """Return the resource item at (x, y, z), if any."""
    return _RESOURCE_ITEMS.get((x, y, z))


def create_resource_item(x: int, y: int, z: int, resource_type: str, amount: int = 1) -> None:
    """Create a resource item that will be auto-hauled to stockpile.
    
    Convenience wrapper for spawn_resource_item with auto_haul=True.
    Used for crafting outputs and salvage drops.
    """
    spawn_resource_item(x, y, z, resource_type, amount, auto_haul=True)


def get_all_resource_items() -> Dict[Coord3D, dict]:
    """Return all resource items for rendering."""
    return _RESOURCE_ITEMS.copy()


def pickup_resource_item(x: int, y: int, z: int = 0) -> Optional[dict]:
    """Pick up and remove the resource item at (x, y, z).
    
    Returns the item dict if found, None otherwise.
    """
    return _RESOURCE_ITEMS.pop((x, y, z), None)


def collect_resource_item(x: int, y: int, z: int = 0) -> bool:
    """Collect a resource item and add it to the stockpile.
    
    Returns True if item was collected, False if no item exists.
    """
    item = pickup_resource_item(x, y, z)
    if item is None:
        return False
    
    add_to_stockpile(item["type"], item["amount"])
    return True


def mark_item_for_hauling(x: int, y: int, z: int = 0) -> bool:
    """Mark a resource item as needing to be hauled.
    
    Returns True if item exists and was marked.
    """
    coord = (x, y, z)
    item = _RESOURCE_ITEMS.get(coord)
    if item is None:
        return False
    item["haul_requested"] = True
    return True


def get_items_needing_haul() -> list[Coord3D]:
    """Return list of coordinates (x, y, z) with items that need hauling."""
    return [
        coord for coord, item in _RESOURCE_ITEMS.items()
        if item.get("haul_requested", False)
    ]


def is_item_haul_requested(x: int, y: int, z: int = 0) -> bool:
    """Check if item at (x, y, z) is marked for hauling."""
    item = _RESOURCE_ITEMS.get((x, y, z))
    return item is not None and item.get("haul_requested", False)


def create_haul_job_for_item(jobs_module, x: int, y: int, z: int, 
                             dest_x: int, dest_y: int, dest_z: int) -> bool:
    """Create a haul job for the resource item at (x, y, z).
    
    Returns True if job was created.
    """
    coord = (x, y, z)
    item = _RESOURCE_ITEMS.get(coord)
    if item is None:
        return False
    
    # Don't create duplicate jobs
    if jobs_module.get_job_at(x, y, z) is not None:
        return False
    
    resource_type = item.get("type", "unknown")
    # Haul jobs are quick - just pickup and delivery
    jobs_module.add_job(
        "haul", 
        x, y, 
        required=10,  # Quick job
        resource_type=resource_type,
        dest_x=dest_x,
        dest_y=dest_y,
        dest_z=dest_z,
        z=z,
    )
    # Mark as no longer needing haul request (job created)
    item["haul_requested"] = False
    return True


def process_auto_haul_jobs(jobs_module, zones_module) -> int:
    """Create haul jobs for items marked for auto-hauling.
    
    Called each tick from main loop. Finds items needing haul and creates
    jobs to move them to stockpile zones.
    
    Returns number of jobs created.
    """
    jobs_created = 0
    
    for (x, y, z), item in list(_RESOURCE_ITEMS.items()):
        if not item.get("haul_requested", False):
            continue
        
        # Already has a job
        if jobs_module.get_job_at(x, y, z) is not None:
            continue
        
        # Find nearest valid stockpile zone (respects filters and Z-level)
        dest = zones_module.find_stockpile_tile_for_resource(
            item.get("type", ""), z=z, from_x=x, from_y=y
        )
        if dest is None:
            # No valid stockpile zone exists - skip this item
            continue
        
        dest_x, dest_y, dest_z = dest
        if create_haul_job_for_item(jobs_module, x, y, z, dest_x, dest_y, dest_z):
            jobs_created += 1
    
    return jobs_created


# Node type definitions with default properties
# regrow_time: 0 = non-replenishable (node removed after harvest)
# regrow_time: >0 = ticks until respawn after depletion
# loose: True = spawns as loose item (no harvesting needed, just haul)
NODE_TYPES = {
    "tree": {"resource": "wood", "amount": 50, "regrow_time": 600, "replenishable": True, "loose": False},
    "scrap_pile": {"resource": "scrap", "amount": 25, "regrow_time": 0, "replenishable": False, "loose": True},
    "mineral_node": {"resource": "mineral", "amount": 75, "regrow_time": 0, "replenishable": False, "loose": False},  # No respawn - finite resource
    "food_plant": {"resource": "raw_food", "amount": 20, "regrow_time": 800, "replenishable": True, "loose": False},
    "street": {"resource": "mineral", "amount": 40, "regrow_time": 0, "replenishable": False, "loose": False, "converts_to": "scorched"},  # Streets can be harvested
    "sidewalk": {"resource": "mineral", "amount": 25, "regrow_time": 0, "replenishable": False, "loose": False, "converts_to": "scorched"},  # Sidewalks can be harvested
}

# Salvage objects - can be designated for salvage to produce scrap
# Key: (x, y), Value: {"type": str, "designated": bool, "scrap_amount": int}
_SALVAGE_OBJECTS: Dict[Coord, dict] = {}

# Salvage object types
SALVAGE_TYPES = {
    "ruined_tech": {"name": "Ruined Tech", "scrap_min": 3, "scrap_max": 6, "work_time": 80},
    "salvage_pile": {"name": "Salvage Pile", "scrap_min": 2, "scrap_max": 4, "work_time": 50},
    "ruined_wall": {"name": "Ruined Wall", "scrap_min": 2, "scrap_max": 5, "work_time": 60},
}


def spawn_salvage_object(x: int, y: int, salvage_type: str = "ruined_tech") -> bool:
    """Spawn a salvage object at (x, y). Returns True if successful."""
    if (x, y) in _SALVAGE_OBJECTS:
        return False
    
    salvage_def = SALVAGE_TYPES.get(salvage_type)
    if salvage_def is None:
        return False
    
    import random
    scrap_amount = random.randint(salvage_def["scrap_min"], salvage_def["scrap_max"])
    
    _SALVAGE_OBJECTS[(x, y)] = {
        "type": salvage_type,
        "designated": False,
        "scrap_amount": scrap_amount,
    }
    return True


def get_salvage_object_at(x: int, y: int) -> Optional[dict]:
    """Get salvage object at (x, y), or None."""
    return _SALVAGE_OBJECTS.get((x, y))


def get_all_salvage_objects() -> Dict[Coord, dict]:
    """Get all salvage objects for rendering."""
    return _SALVAGE_OBJECTS.copy()


def designate_salvage(x: int, y: int) -> bool:
    """Designate a salvage object for dismantling. Returns True if successful."""
    obj = _SALVAGE_OBJECTS.get((x, y))
    if obj is None:
        return False
    if obj.get("designated", False):
        return False  # Already designated
    obj["designated"] = True
    return True


def is_salvage_designated(x: int, y: int) -> bool:
    """Check if salvage object at (x, y) is designated."""
    obj = _SALVAGE_OBJECTS.get((x, y))
    return obj is not None and obj.get("designated", False)


def complete_salvage(x: int, y: int) -> int:
    """Complete salvage of object at (x, y). Returns scrap amount and removes object."""
    obj = _SALVAGE_OBJECTS.pop((x, y), None)
    if obj is None:
        return 0
    return obj.get("scrap_amount", 0)


def get_salvage_work_time(x: int, y: int) -> int:
    """Get work time required to salvage object at (x, y)."""
    obj = _SALVAGE_OBJECTS.get((x, y))
    if obj is None:
        return 0
    salvage_def = SALVAGE_TYPES.get(obj.get("type", ""))
    if salvage_def is None:
        return 50
    return salvage_def.get("work_time", 50)


def is_node_replenishable(node_type: str) -> bool:
    """Check if a node type can respawn after depletion."""
    node_def = NODE_TYPES.get(node_type)
    if node_def is None:
        return False
    return node_def.get("replenishable", node_def.get("regrow_time", 0) > 0)


def is_node_loose(node_type: str) -> bool:
    """Check if a node type spawns as loose items (no harvesting needed)."""
    node_def = NODE_TYPES.get(node_type)
    if node_def is None:
        return False
    return node_def.get("loose", False)


def designate_street_for_harvest(grid, x: int, y: int, jobs_module=None) -> bool:
    """Designate a street tile for harvesting. Creates a resource node on the street.
    
    When harvested, the street yields mineral and converts to scorched earth.
    Returns True if successful.
    """
    tile = grid.get_tile(x, y)
    # Accept all street variants (normal, cracked, scar, ripped)
    if tile not in ("street", "street_cracked", "street_scar", "street_ripped"):
        return False
    
    # Check if already has a node
    if (x, y) in _RESOURCE_NODES:
        return False
    
    # Create a street node (harvestable)
    node_def = NODE_TYPES["street"]
    amount = random.randint(30, node_def["amount"])
    
    _RESOURCE_NODES[(x, y)] = {
        "type": "street",
        "resource": node_def["resource"],
        "amount": amount,
        "max_amount": amount,
        "regrow_time": node_def["regrow_time"],
        "converts_to": node_def["converts_to"],
        "state": NodeState.IDLE,
        "depleted": False,
    }
    
    # Change tile to show it's designated (but keep street appearance until harvested)
    grid.set_tile(x, y, "street_designated")
    
    # Create gathering job if jobs_module provided
    if jobs_module is not None:
        jobs_module.add_job("gathering", x, y, required=60, resource_type="mineral")
    
    return True


def designate_sidewalk_for_harvest(grid, x: int, y: int, jobs_module=None) -> bool:
    """Designate a sidewalk tile for harvesting. Creates a resource node on the sidewalk.
    
    When harvested, the sidewalk yields mineral and converts to scorched earth.
    Returns True if successful.
    """
    tile = grid.get_tile(x, y)
    if tile != "sidewalk":
        return False
    
    # Check if already has a node
    if (x, y) in _RESOURCE_NODES:
        return False
    
    # Create a sidewalk node (harvestable)
    node_def = NODE_TYPES["sidewalk"]
    amount = random.randint(15, node_def["amount"])
    
    _RESOURCE_NODES[(x, y)] = {
        "type": "sidewalk",
        "resource": node_def["resource"],
        "amount": amount,
        "max_amount": amount,
        "regrow_time": node_def["regrow_time"],
        "converts_to": node_def["converts_to"],
        "state": NodeState.IDLE,
        "depleted": False,
    }
    
    # Change tile to show it's designated
    grid.set_tile(x, y, "sidewalk_designated")
    
    # Create gathering job if jobs_module provided
    if jobs_module is not None:
        jobs_module.add_job("gathering", x, y, required=45, resource_type="mineral")
    
    return True


# --- Node helpers -------------------------------------------------------------


def _place_node(grid, x: int, y: int, node_type: str) -> bool:
    """Place a single resource node at (x, y). Returns True if successful.
    
    For loose node types (like scrap), spawns items directly on the ground
    instead of creating a harvestable node.
    """
    tile = grid.get_tile(x, y)
    # Allow placement on empty tiles, finished floors, and decorative tiles
    if tile not in ["empty", "finished_floor", "weeds", "sidewalk", "debris"]:
        return False
    
    node_def = NODE_TYPES[node_type]
    # Random amount between 1 and max
    base_amount = node_def["amount"]
    amount = random.randint(max(1, base_amount // 2), base_amount)
    
    # Loose items spawn directly on ground (no harvesting needed)
    if node_def.get("loose", False):
        resource_type = node_def["resource"]
        # Spawn each unit as a separate item (or stack them) - always on z=0
        spawn_resource_item(x, y, 0, resource_type, amount, auto_haul=False)
        return True
    
    # Regular harvestable node
    node = {
        "type": node_type,
        "resource": node_def["resource"],
        "amount": amount,
        "max_amount": amount,
        "regrow_time": node_def["regrow_time"],
        "regrow_timer": 0,
        "depleted": False,
        "state": NodeState.IDLE,
    }
    _RESOURCE_NODES[(x, y)] = node
    grid.set_tile(x, y, "resource_node")
    return True


def _spawn_cluster(grid, center_x: int, center_y: int, node_type: str, cluster_size: int) -> int:
    """Spawn a cluster of nodes around a center point.
    
    Returns number of nodes placed.
    """
    placed = 0
    attempts = 0
    max_attempts = cluster_size * 10
    
    # Try to place the center node first
    if _place_node(grid, center_x, center_y, node_type):
        placed += 1
    
    # Spread radius based on cluster size
    radius = max(2, cluster_size // 2)
    
    while placed < cluster_size and attempts < max_attempts:
        attempts += 1
        # Random offset from center (clustered distribution)
        dx = random.randint(-radius, radius)
        dy = random.randint(-radius, radius)
        x = center_x + dx
        y = center_y + dy
        
        # Skip if too far from center (circular-ish clusters)
        if abs(dx) + abs(dy) > radius + 1:
            continue
        
        if _place_node(grid, x, y, node_type):
            placed += 1
    
    return placed


def _generate_street_grid(grid) -> tuple[list[tuple[int, int]], list[dict]]:
    """Generate a grid of streets across the map.
    
    Creates horizontal and vertical streets (1 tile wide with autotiling) at regular intervals.
    Returns (street_tiles, street_segments) where street_segments contain metadata.
    """
    streets = []
    street_segments = []  # List of {type: 'horizontal'/'vertical', x, y, length}
    street_width = 1  # Streets are 1 tile wide (autotiled for corners/intersections)
    block_size = 15   # Blocks are ~15 tiles apart (tighter urban density)
    
    # Horizontal streets (running east-west)
    for y in range(20, GRID_H, block_size):
        for x in range(GRID_W):
            for dy in range(street_width):
                street_y = y + dy
                if 0 <= street_y < GRID_H:
                    grid.set_tile(x, street_y, "street", z=0)
                    streets.append((x, street_y))
        
        # Record this street segment
        street_segments.append({
            "type": "horizontal",
            "y": y,
            "x_start": 0,
            "x_end": GRID_W,
            "width": street_width
        })
    
    # Vertical streets (running north-south)
    for x in range(20, GRID_W, block_size):
        for y in range(GRID_H):
            for dx in range(street_width):
                street_x = x + dx
                if 0 <= street_x < GRID_W:
                    grid.set_tile(street_x, y, "street", z=0)
                    streets.append((street_x, y))
        
        # Record this street segment
        street_segments.append({
            "type": "vertical",
            "x": x,
            "y_start": 0,
            "y_end": GRID_H,
            "width": street_width
        })
    
    return streets, street_segments


def _identify_lots(grid, streets: list[tuple[int, int]]) -> list[dict]:
    """Identify rectangular lots between streets.
    
    Returns list of lot dictionaries with keys: x, y, width, height.
    """
    lots = []
    
    # Simple approach: calculate lots based on block_size
    street_width = 1
    block_size = 15
    
    # Generate lots between streets
    for y_start in range(20, GRID_H - block_size, block_size):
        for x_start in range(20, GRID_W - block_size, block_size):
            lot_x = x_start + street_width
            lot_y = y_start + street_width
            lot_width = block_size - street_width
            lot_height = block_size - street_width
            
            if lot_width > 10 and lot_height > 10:
                lots.append({
                    "x": lot_x,
                    "y": lot_y,
                    "width": lot_width,
                    "height": lot_height
                })
    
    return lots


def _find_colonist_spawn_location(streets: list[tuple[int, int]]) -> tuple[int, int]:
    """Find a good spawn location near a street intersection in the center.
    
    Returns (x, y) coordinates.
    """
    center_x = GRID_W // 2
    center_y = GRID_H // 2
    
    # Find nearest street intersection to center
    best_dist = float('inf')
    best_pos = (center_x, center_y)
    
    # Look for street tiles near center
    for x, y in streets:
        dx = x - center_x
        dy = y - center_y
        dist = dx * dx + dy * dy
        if dist < best_dist:
            best_dist = dist
            best_pos = (x, y)
    
    return best_pos


def _spawn_ruins_in_lots(grid, lots: list[dict], colonist_spawn: tuple[int, int]) -> tuple[int, int, int]:
    """Spawn 3-7 ruined buildings in available lots with food inside.
    
    Returns (ruins_count, salvage_count, food_count).
    """
    ruins_count = 0
    salvage_count = 0
    food_count = 0
    num_ruins = random.randint(3, 7)
    
    # Shuffle lots for random placement
    available_lots = lots.copy()
    random.shuffle(available_lots)
    
    for lot in available_lots:
        if ruins_count >= num_ruins:
            break
        
        # Check distance from colonist spawn
        lot_center_x = lot["x"] + lot["width"] // 2
        lot_center_y = lot["y"] + lot["height"] // 2
        dx = lot_center_x - colonist_spawn[0]
        dy = lot_center_y - colonist_spawn[1]
        dist = (dx * dx + dy * dy) ** 0.5
        
        if dist < 20:  # Too close to spawn
            continue
        
        # Random building size within lot (leave margins) - scaled down
        max_width = min(lot["width"] - 2, 8)
        max_height = min(lot["height"] - 2, 8)
        
        if max_width < 3 or max_height < 3:
            continue  # Lot too small
        
        width = random.randint(3, max_width)
        height = random.randint(3, max_height)
        
        # Center building in lot
        x = lot["x"] + (lot["width"] - width) // 2
        y = lot["y"] + (lot["height"] - height) // 2
        
        # Place floor tiles
        for dx in range(1, width - 1):
            for dy in range(1, height - 1):
                grid.set_tile(x + dx, y + dy, "finished_floor", z=0)
        
        # Place broken walls with entrance
        entrance_side = random.choice(["north", "south", "east", "west"])
        entrance_pos = random.randint(2, max(2, min(width, height) - 3))
        
        for dx in range(width):
            for dy in range(height):
                is_edge = (dx == 0 or dx == width - 1 or dy == 0 or dy == height - 1)
                if not is_edge:
                    continue
                
                # Create entrance
                if entrance_side == "north" and dy == 0 and dx == entrance_pos:
                    continue
                if entrance_side == "south" and dy == height - 1 and dx == entrance_pos:
                    continue
                if entrance_side == "east" and dx == width - 1 and dy == entrance_pos:
                    continue
                if entrance_side == "west" and dx == 0 and dy == entrance_pos:
                    continue
                
                # Random gaps for ruined look
                if random.random() < 0.25:
                    continue
                
                px, py = x + dx, y + dy
                salvage_type = random.choice(["ruined_wall", "ruined_wall", "salvage_pile"])
                if spawn_salvage_object(px, py, salvage_type):
                    grid.set_tile(px, py, "salvage_object", z=0)
                    salvage_count += 1
        
        # Place food nodes inside (2-5 per building)
        num_food = random.randint(2, 5)
        for _ in range(num_food):
            for attempt in range(30):
                fx = x + random.randint(1, width - 2)
                fy = y + random.randint(1, height - 2)
                
                tile = grid.get_tile(fx, fy, 0)
                if tile == "finished_floor" and (fx, fy) not in _RESOURCE_NODES:
                    if _place_node(grid, fx, fy, "food_plant"):
                        food_count += 1
                        break
        
        # Place scrap piles inside (2-5 per building) - increased density
        num_scrap = random.randint(2, 5)
        for _ in range(num_scrap):
            for attempt in range(20):
                sx = x + random.randint(1, width - 2)
                sy = y + random.randint(1, height - 2)
                
                tile = grid.get_tile(sx, sy, 0)
                if tile == "finished_floor" and (sx, sy) not in _RESOURCE_NODES:
                    if spawn_salvage_object(sx, sy, "salvage_pile"):
                        grid.set_tile(sx, sy, "salvage_object", z=0)
                        salvage_count += 1
                        break
        
        ruins_count += 1
    
    return ruins_count, salvage_count, food_count


def _generate_buildings_along_streets(grid, street_segments: list[dict], colonist_spawn: tuple[int, int]) -> tuple[int, int, int]:
    """Generate buildings along both sides of streets.
    
    Buildings can be intact, partially collapsed, or completely ruined.
    Returns (buildings_count, food_count, scrap_count).
    """
    buildings_count = 0
    food_count = 0
    scrap_count = 0
    
    for segment in street_segments:
        if segment["type"] == "horizontal":
            # Buildings on north and south sides
            y = segment["y"]
            street_width = segment["width"]
            
            # North side buildings (above street)
            if y > 10:
                bldg, food, scrap = _place_building_row(grid, segment["x_start"], y - 1, 
                                                         segment["x_end"] - segment["x_start"], 
                                                         "north", colonist_spawn)
                buildings_count += bldg
                food_count += food
                scrap_count += scrap
            
            # South side buildings (below street)
            if y + street_width < GRID_H - 10:
                bldg, food, scrap = _place_building_row(grid, segment["x_start"], y + street_width, 
                                                         segment["x_end"] - segment["x_start"], 
                                                         "south", colonist_spawn)
                buildings_count += bldg
                food_count += food
                scrap_count += scrap
        
        elif segment["type"] == "vertical":
            # Buildings on east and west sides
            x = segment["x"]
            street_width = segment["width"]
            
            # West side buildings (left of street)
            if x > 10:
                bldg, food, scrap = _place_building_row(grid, x - 1, segment["y_start"], 
                                                         segment["y_end"] - segment["y_start"], 
                                                         "west", colonist_spawn)
                buildings_count += bldg
                food_count += food
                scrap_count += scrap
            
            # East side buildings (right of street)
            if x + street_width < GRID_W - 10:
                bldg, food, scrap = _place_building_row(grid, x + street_width, segment["y_start"], 
                                                         segment["y_end"] - segment["y_start"], 
                                                         "east", colonist_spawn)
                buildings_count += bldg
                food_count += food
                scrap_count += scrap
    
    return buildings_count, food_count, scrap_count


def _place_building_row(grid, x: int, y: int, length: int, direction: str, colonist_spawn: tuple[int, int]) -> tuple[int, int, int]:
    """Place a row of buildings along a street edge.
    
    Returns (buildings_placed, food_placed, scrap_placed).
    """
    buildings = 0
    food = 0
    scrap = 0
    
    if direction in ["north", "south"]:
        # Horizontal row of buildings
        pos = 0
        while pos < length - 3:
            # Random building width (3-6 tiles) - scaled down for tighter streets
            width = random.randint(3, 6)
            depth = random.randint(3, 5)  # Building depth into lot
            
            # Check distance from colonist spawn
            bldg_center_x = x + pos + width // 2
            bldg_center_y = y if direction == "north" else y + depth // 2
            dx = bldg_center_x - colonist_spawn[0]
            dy = bldg_center_y - colonist_spawn[1]
            dist = (dx * dx + dy * dy) ** 0.5
            
            if dist > 15:  # Not too close to spawn
                # Place building
                bldg_x = x + pos
                bldg_y = y - depth if direction == "north" else y
                
                f, s = _place_single_building(grid, bldg_x, bldg_y, width, depth)
                if f > 0 or s > 0:  # Building was placed
                    buildings += 1
                    food += f
                    scrap += s
            
            pos += width + random.randint(1, 3)  # Gap between buildings
    
    else:  # "east" or "west"
        # Vertical row of buildings
        pos = 0
        while pos < length - 3:
            # Random building dimensions - scaled down for tighter streets
            height = random.randint(3, 6)
            depth = random.randint(3, 5)
            
            # Check distance from colonist spawn
            bldg_center_x = x if direction == "west" else x + depth // 2
            bldg_center_y = y + pos + height // 2
            dx = bldg_center_x - colonist_spawn[0]
            dy = bldg_center_y - colonist_spawn[1]
            dist = (dx * dx + dy * dy) ** 0.5
            
            if dist > 15:
                bldg_x = x - depth if direction == "west" else x
                bldg_y = y + pos
                
                f, s = _place_single_building(grid, bldg_x, bldg_y, depth, height)
                if f > 0 or s > 0:
                    buildings += 1
                    food += f
                    scrap += s
            
            pos += height + random.randint(1, 3)
    
    return buildings, food, scrap


def _place_single_building(grid, x: int, y: int, width: int, height: int) -> tuple[int, int]:
    """Place a single building (intact, partial, or ruined).
    
    Returns (food_placed, scrap_placed).
    """
    # Check if area is clear
    for dx in range(width):
        for dy in range(height):
            if not grid.in_bounds(x + dx, y + dy, 0):
                return 0, 0
            tile = grid.get_tile(x + dx, y + dy, 0)
            if tile not in ["empty", "weeds", "sidewalk"]:
                return 0, 0
    
    # Determine building condition
    condition = random.choices(
        ["intact", "partial", "ruined"],
        weights=[0.2, 0.4, 0.4]  # 20% intact, 40% partial, 40% ruined
    )[0]
    
    food_placed = 0
    scrap_placed = 0
    
    # Place floor
    for dx in range(1, width - 1):
        for dy in range(1, height - 1):
            grid.set_tile(x + dx, y + dy, "finished_floor", z=0)
    
    # Place walls based on condition
    if condition == "intact":
        # Full walls with one entrance
        entrance_side = random.choice(["north", "south", "east", "west"])
        entrance_pos = random.randint(2, max(2, min(width, height) - 3))
        
        for dx in range(width):
            for dy in range(height):
                is_edge = (dx == 0 or dx == width - 1 or dy == 0 or dy == height - 1)
                if not is_edge:
                    continue
                
                # Skip entrance
                if entrance_side == "north" and dy == 0 and dx == entrance_pos:
                    continue
                if entrance_side == "south" and dy == height - 1 and dx == entrance_pos:
                    continue
                if entrance_side == "east" and dx == width - 1 and dy == entrance_pos:
                    continue
                if entrance_side == "west" and dx == 0 and dy == entrance_pos:
                    continue
                
                grid.set_tile(x + dx, y + dy, "finished_wall", z=0)
    
    elif condition == "partial":
        # Partial walls (50% coverage, salvageable)
        for dx in range(width):
            for dy in range(height):
                is_edge = (dx == 0 or dx == width - 1 or dy == 0 or dy == height - 1)
                if is_edge and random.random() < 0.5:
                    if spawn_salvage_object(x + dx, y + dy, "ruined_wall"):
                        grid.set_tile(x + dx, y + dy, "salvage_object", z=0)
    
    else:  # ruined
        # Minimal walls (20% coverage, mostly debris)
        for dx in range(width):
            for dy in range(height):
                is_edge = (dx == 0 or dx == width - 1 or dy == 0 or dy == height - 1)
                if is_edge and random.random() < 0.2:
                    if spawn_salvage_object(x + dx, y + dy, "ruined_wall"):
                        grid.set_tile(x + dx, y + dy, "salvage_object", z=0)
    
    # Place food inside (2-6 nodes per building)
    num_food = random.randint(2, 6)
    for _ in range(num_food):
        for attempt in range(30):
            fx = x + random.randint(1, width - 2)
            fy = y + random.randint(1, height - 2)
            
            tile = grid.get_tile(fx, fy, 0)
            if tile == "finished_floor" and (fx, fy) not in _RESOURCE_NODES:
                if _place_node(grid, fx, fy, "food_plant"):
                    food_placed += 1
                    break
    
    # Place scrap inside (3-8 piles per building)
    num_scrap = random.randint(3, 8)
    for _ in range(num_scrap):
        for attempt in range(20):
            sx = x + random.randint(1, width - 2)
            sy = y + random.randint(1, height - 2)
            
            tile = grid.get_tile(sx, sy, 0)
            if tile == "finished_floor" and (sx, sy) not in _RESOURCE_NODES:
                if spawn_salvage_object(sx, sy, "salvage_pile"):
                    grid.set_tile(sx, sy, "salvage_object", z=0)
                    scrap_placed += 1
                    break
    
    return food_placed, scrap_placed


def _generate_back_lots(grid, street_segments: list[dict]) -> list[dict]:
    """Identify back lots behind buildings for resource spawning.
    
    Returns list of lot dictionaries.
    """
    lots = []
    block_size = 40
    
    # Generate lots in the spaces between streets
    for y_start in range(20, GRID_H - block_size, block_size):
        for x_start in range(20, GRID_W - block_size, block_size):
            # Create a lot in the center of each block
            lot_x = x_start + 12  # Offset for buildings
            lot_y = y_start + 12
            lot_width = block_size - 24
            lot_height = block_size - 24
            
            if lot_width > 5 and lot_height > 5:
                lots.append({
                    "x": lot_x,
                    "y": lot_y,
                    "width": lot_width,
                    "height": lot_height
                })
    
    return lots


def _generate_sidewalks(grid, streets: list[tuple[int, int]]) -> int:
    """Generate sidewalk tiles along the edges of streets.
    
    Returns count of sidewalk tiles placed.
    """
    sidewalk_count = 0
    street_set = set(streets)
    
    # For each street tile, check adjacent tiles
    for sx, sy in streets:
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = sx + dx, sy + dy
            
            # If adjacent tile is not a street and is empty, make it a sidewalk
            if (nx, ny) not in street_set and grid.in_bounds(nx, ny, 0):
                tile = grid.get_tile(nx, ny, 0)
                if tile == "empty":
                    grid.set_tile(nx, ny, "sidewalk", z=0)
                    sidewalk_count += 1
    
    return sidewalk_count


def _spawn_debris(grid, lots: list[dict]) -> int:
    """Spawn debris tiles randomly in ruins and near walls.
    
    Returns count of debris tiles placed.
    """
    debris_count = 0
    
    # Spawn debris on sidewalks and in lots
    for y in range(GRID_H):
        for x in range(GRID_W):
            tile = grid.get_tile(x, y, 0)
            
            # 3% chance on sidewalks
            if tile == "sidewalk" and random.random() < 0.03:
                grid.set_tile(x, y, "debris", z=0)
                debris_count += 1
            # 5% chance on finished floors (inside ruins)
            elif tile == "finished_floor" and random.random() < 0.05:
                # Check if not occupied by resource node
                if (x, y) not in _RESOURCE_NODES:
                    grid.set_tile(x, y, "debris", z=0)
                    debris_count += 1
    
    return debris_count


def _spawn_weeds(grid, lots: list[dict]) -> int:
    """Spawn weed tiles in empty lots and near edges.
    
    Returns count of weed tiles placed.
    """
    weeds_count = 0
    
    # Spawn weeds in empty spaces
    for lot in lots:
        # Sparse weeds in each lot (2-8 per lot)
        num_weeds = random.randint(2, 8)
        for _ in range(num_weeds):
            wx = lot["x"] + random.randint(0, lot["width"] - 1)
            wy = lot["y"] + random.randint(0, lot["height"] - 1)
            
            if grid.in_bounds(wx, wy, 0):
                tile = grid.get_tile(wx, wy, 0)
                if tile == "empty" and (wx, wy) not in _RESOURCE_NODES:
                    grid.set_tile(wx, wy, "weeds", z=0)
                    weeds_count += 1
    
    # Add weeds near map edges
    for x in range(GRID_W):
        for y in [0, 1, GRID_H - 2, GRID_H - 1]:
            if random.random() < 0.15:
                tile = grid.get_tile(x, y, 0)
                if tile == "empty":
                    grid.set_tile(x, y, "weeds", z=0)
                    weeds_count += 1
    
    for y in range(GRID_H):
        for x in [0, 1, GRID_W - 2, GRID_W - 1]:
            if random.random() < 0.15:
                tile = grid.get_tile(x, y, 0)
                if tile == "empty":
                    grid.set_tile(x, y, "weeds", z=0)
                    weeds_count += 1
    
    return weeds_count


def _spawn_props(grid, streets: list[tuple[int, int]], lots: list[dict]) -> int:
    """Spawn prop tiles (barrels, signs, scrap heaps) sparsely.
    
    Returns count of prop tiles placed.
    """
    props_count = 0
    prop_types = ["prop_barrel", "prop_sign", "prop_scrap"]
    
    # Sparse props along streets (1 per 50 street tiles)
    street_sample = random.sample(streets, min(len(streets) // 50, 20))
    for sx, sy in street_sample:
        prop_type = random.choice(prop_types)
        grid.set_tile(sx, sy, prop_type, z=0)
        props_count += 1
    
    # Props inside ruins (on floors)
    for y in range(GRID_H):
        for x in range(GRID_W):
            tile = grid.get_tile(x, y, 0)
            if tile == "finished_floor" and random.random() < 0.02:
                # Check not occupied
                if (x, y) not in _RESOURCE_NODES:
                    prop_type = random.choice(prop_types)
                    grid.set_tile(x, y, prop_type, z=0)
                    props_count += 1
    
    return props_count


def _spawn_road_damage(grid, streets: list[tuple[int, int]], street_segments: list[dict]) -> tuple[int, int]:
    """Spawn road damage (cracks, scars, rips) on streets, focused near buildings.
    
    More damage appears near dense building areas.
    Ripped streets may have mineral nodes scattered nearby.
    
    Returns (damage_count, mineral_count).
    """
    damage_count = 0
    mineral_count = 0
    street_set = set(streets)
    
    # Build a density map - count buildings near each street tile
    def count_nearby_buildings(x: int, y: int, radius: int = 8) -> int:
        """Count building-related tiles near a position."""
        count = 0
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                nx, ny = x + dx, y + dy
                if grid.in_bounds(nx, ny, 0):
                    tile = grid.get_tile(nx, ny, 0)
                    if tile in ("finished_wall", "finished_floor", "salvage_object"):
                        count += 1
        return count
    
    # Process each street tile
    for sx, sy in streets:
        tile = grid.get_tile(sx, sy, 0)
        if tile != "street":
            continue  # Already modified
        
        # Calculate damage probability based on nearby building density
        building_density = count_nearby_buildings(sx, sy, 6)
        
        # Base chance increases with building density
        # 0 buildings = 2% chance, 20+ buildings = 25% chance
        base_chance = 0.02 + min(0.23, building_density * 0.012)
        
        if random.random() > base_chance:
            continue
        
        # Choose damage type - more severe damage near more buildings
        if building_density > 15 and random.random() < 0.3:
            damage_type = "street_ripped"
        elif building_density > 8 and random.random() < 0.4:
            damage_type = "street_scar"
        else:
            damage_type = "street_cracked"
        
        grid.set_tile(sx, sy, damage_type, z=0)
        damage_count += 1
        
        # Ripped streets have a chance to spawn mineral nodes nearby
        if damage_type == "street_ripped" and random.random() < 0.4:
            # Try to place a mineral node on an adjacent empty tile
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, 1), (-1, 1), (1, -1)]:
                nx, ny = sx + dx, sy + dy
                if grid.in_bounds(nx, ny, 0):
                    adj_tile = grid.get_tile(nx, ny, 0)
                    if adj_tile in ("empty", "weeds", "debris") and (nx, ny) not in _RESOURCE_NODES:
                        if _place_node(grid, nx, ny, "mineral_node"):
                            mineral_count += 1
                            break
    
    return damage_count, mineral_count


def _spawn_wood_clusters(grid, lots: list[dict], colonist_spawn: tuple[int, int]) -> int:
    """Spawn wood clusters in back lots (2x density).
    
    Returns total wood nodes placed.
    """
    wood_count = 0
    num_clusters = random.randint(30, 40)  # 2x increase
    
    for _ in range(num_clusters):
        # Pick a random lot
        if not lots:
            break
        lot = random.choice(lots)
        
        # Random position in lot
        center_x = lot["x"] + random.randint(2, min(lot["width"] - 3, lot["width"] - 1))
        center_y = lot["y"] + random.randint(2, min(lot["height"] - 3, lot["height"] - 1))
        
        cluster_size = random.randint(8, 16)  # Larger clusters
        wood_count += _spawn_cluster(grid, center_x, center_y, "tree", cluster_size)
    
    return wood_count


def _spawn_mineral_clusters(grid, lots: list[dict], colonist_spawn: tuple[int, int]) -> int:
    """Spawn mineral clusters in back lots (2x density).
    
    Returns total mineral nodes placed.
    """
    mineral_count = 0
    num_clusters = random.randint(24, 32)  # 2x increase
    
    for _ in range(num_clusters):
        # Pick a random lot
        if not lots:
            break
        lot = random.choice(lots)
        
        # Random position in lot
        center_x = lot["x"] + random.randint(2, min(lot["width"] - 3, lot["width"] - 1))
        center_y = lot["y"] + random.randint(2, min(lot["height"] - 3, lot["height"] - 1))
        
        cluster_size = random.randint(8, 14)  # Larger clusters
        mineral_count += _spawn_cluster(grid, center_x, center_y, "mineral_node", cluster_size)
    
    return mineral_count


def _spawn_exterior_scrap(grid, lots: list[dict]) -> int:
    """Spawn loose scrap piles in back lots.
    
    Returns total scrap piles placed.
    """
    scrap_count = 0
    
    for lot in lots:
        # 2-4 scrap piles per lot
        num_scrap = random.randint(2, 4)
        for _ in range(num_scrap):
            for attempt in range(20):
                sx = lot["x"] + random.randint(0, lot["width"] - 1)
                sy = lot["y"] + random.randint(0, lot["height"] - 1)
                
                if grid.in_bounds(sx, sy, 0):
                    tile = grid.get_tile(sx, sy, 0)
                    if tile == "empty" and (sx, sy) not in _RESOURCE_NODES:
                        if spawn_salvage_object(sx, sy, "salvage_pile"):
                            grid.set_tile(sx, sy, "salvage_object", z=0)
                            scrap_count += 1
                            break
    
    return scrap_count


def _spawn_ruined_buildings(grid, colonist_center_x: int, colonist_center_y: int, safe_radius: int) -> tuple[int, int]:
    """Spawn 4-6 ruined buildings with floors, walls, scrap, and food.
    
    Each ruin is a complete building structure:
    - Floor tiles (finished_floor) inside
    - Partial/broken walls around the perimeter (salvage objects)
    - Scrap piles inside (salvage objects)
    - Food plants inside (resource nodes)
    
    Returns (total_salvage_tiles, num_ruins_placed).
    """
    total_salvage = 0
    ruins_placed = 0
    num_ruins = random.randint(4, 6)  # More ruins for larger map
    
    for _ in range(num_ruins):
        # Random building size (scaled down for tighter streets)
        width = random.randint(3, 7)
        height = random.randint(3, 7)
        
        # Find a valid location (needs enough empty space, away from colonists)
        for attempt in range(50):
            # Leave margin from edges
            x = random.randint(10, GRID_W - width - 10)
            y = random.randint(10, GRID_H - height - 10)
            
            # Check distance from colonist spawn
            center_dx = (x + width // 2) - colonist_center_x
            center_dy = (y + height // 2) - colonist_center_y
            dist = (center_dx * center_dx + center_dy * center_dy) ** 0.5
            
            if dist < safe_radius + 10:  # Extra buffer for ruins
                continue
            
            # Check if area is clear (including 2-tile buffer around building)
            area_clear = True
            for dx in range(-2, width + 2):
                for dy in range(-2, height + 2):
                    check_x = x + dx
                    check_y = y + dy
                    if not grid.in_bounds(check_x, check_y, 0):
                        area_clear = False
                        break
                    tile = grid.get_tile(check_x, check_y, 0)
                    if tile != "empty":
                        area_clear = False
                        break
                    if (check_x, check_y) in _RESOURCE_NODES:
                        area_clear = False
                        break
                if not area_clear:
                    break
            
            if not area_clear:
                continue
            
            # Place the ruined building
            salvage_count = 0
            
            # 1. Place floor tiles inside
            for dx in range(1, width - 1):
                for dy in range(1, height - 1):
                    px, py = x + dx, y + dy
                    grid.set_tile(px, py, "finished_floor", z=0)
            
            # 2. Place broken walls around perimeter (with gaps for ruined look)
            for dx in range(width):
                for dy in range(height):
                    # Only place on edges (walls)
                    is_wall = (dx == 0 or dx == width - 1 or dy == 0 or dy == height - 1)
                    if not is_wall:
                        continue
                    
                    # Random gaps (30% chance) for ruined appearance
                    if random.random() < 0.30:
                        continue
                    
                    px, py = x + dx, y + dy
                    salvage_type = random.choice(["ruined_wall", "ruined_wall", "salvage_pile"])
                    if spawn_salvage_object(px, py, salvage_type):
                        grid.set_tile(px, py, "salvage_object", z=0)
                        salvage_count += 1
            
            # 3. Place scrap piles inside (2-5 piles)
            num_scrap = random.randint(2, 5)
            for _ in range(num_scrap):
                for scrap_attempt in range(20):
                    sx = x + random.randint(1, width - 2)
                    sy = y + random.randint(1, height - 2)
                    
                    # Check if tile is floor and empty
                    if grid.get_tile(sx, sy, 0) == "finished_floor" and (sx, sy) not in _RESOURCE_NODES:
                        if spawn_salvage_object(sx, sy, "salvage_pile"):
                            grid.set_tile(sx, sy, "salvage_object", z=0)
                            salvage_count += 1
                            break
            
            # 4. Place food plants inside (1-3 plants)
            num_food = random.randint(1, 3)
            for _ in range(num_food):
                for food_attempt in range(20):
                    fx = x + random.randint(1, width - 2)
                    fy = y + random.randint(1, height - 2)
                    
                    # Check if tile is floor and empty
                    tile = grid.get_tile(fx, fy, 0)
                    if tile == "finished_floor" and (fx, fy) not in _RESOURCE_NODES:
                        # Don't place on salvage objects
                        if tile != "salvage_object":
                            _place_node(grid, fx, fy, "food_plant")
                            break
            
            total_salvage += salvage_count
            ruins_placed += 1
            break  # Successfully placed this ruin
    
    return total_salvage, ruins_placed


# Global variable to store colonist spawn location
_COLONIST_SPAWN_LOCATION: tuple[int, int] = (100, 100)  # Default center


def get_colonist_spawn_location() -> tuple[int, int]:
    """Get the colonist spawn location determined during world generation.
    
    Returns (x, y) coordinates.
    """
    return _COLONIST_SPAWN_LOCATION


def spawn_resource_nodes(grid, count: int = 40) -> tuple[int, int]:
    """Generate a procedural ruined cyberpunk city.
    
    NEW SYSTEM: Uses proper city generation with:
    - Road networks with real intersections
    - Varied city blocks
    - Realistic building placement
    - Organic urban structure
    
    Returns (spawn_x, spawn_y) for colonist placement.
    """
    global _COLONIST_SPAWN_LOCATION
    
    # Use new city generator
    from city_generator import CityGenerator
    
    city_gen = CityGenerator(grid)
    spawn_x, spawn_y = city_gen.generate_city()
    
    _COLONIST_SPAWN_LOCATION = (spawn_x, spawn_y)
    
    # Add resource nodes to buildings (integrate with existing resource system)
    _spawn_resources_in_city(grid, city_gen)
    
    # Generate organic terrain patches on remaining empty tiles
    # TODO: Re-enable when terrain_gen module is created
    # from terrain_gen import generate_terrain_patches
    # generate_terrain_patches(grid)
    
    # Create starter stockpile near spawn
    _create_starter_stockpile(grid, (spawn_x, spawn_y))
    
    return spawn_x, spawn_y


def _spawn_resources_in_city(grid, city_gen):
    """Add resource nodes throughout the generated city."""
    # Scan for buildings and add resources
    wood_count = 0
    scrap_count = 0
    mineral_count = 0
    food_count = 0
    
    # Add scattered resources in empty areas
    for _ in range(100):
        x = random.randint(10, GRID_W - 10)
        y = random.randint(10, GRID_H - 10)
        
        tile = grid.get_tile(x, y, 0)
        
        # Add resources to appropriate tiles
        if tile == "empty" and (x, y) not in _RESOURCE_NODES:
            resource_type = random.choice(["tree", "mineral_node", "scrap_pile"])
            if resource_type == "tree":
                if _place_node(grid, x, y, "tree"):
                    wood_count += 1
            elif resource_type == "mineral_node":
                if _place_node(grid, x, y, "mineral_node"):
                    mineral_count += 1
            elif resource_type == "scrap_pile":
                if spawn_salvage_object(x, y, "salvage_pile"):
                    grid.set_tile(x, y, "salvage_object", z=0)
                    scrap_count += 1
        
        # Add food inside buildings
        elif tile == "finished_floor" and (x, y) not in _RESOURCE_NODES:
            if random.random() < 0.05:  # 5% chance
                if _place_node(grid, x, y, "food_plant"):
                    food_count += 1
    
    print(f"[WorldGen] Resources: {wood_count} wood, {scrap_count} scrap, {mineral_count} mineral, {food_count} food")


def _create_starter_stockpile(grid, colonist_spawn: tuple[int, int]) -> None:
    """Create a 4x4 starter stockpile with resources near colonist spawn.
    
    This is for testing/dev purposes to skip early resource gathering.
    """
    import zones
    
    spawn_x, spawn_y = colonist_spawn
    
    # Place stockpile 3 tiles to the right of spawn
    stockpile_x = spawn_x + 3
    stockpile_y = spawn_y - 2  # Slightly above
    
    # Find a clear 4x4 area (check for walkable tiles)
    found = False
    for offset_x in range(0, 10):
        for offset_y in range(-5, 5):
            test_x = spawn_x + 3 + offset_x
            test_y = spawn_y + offset_y
            
            # Check if 4x4 area is clear
            all_clear = True
            for dx in range(4):
                for dy in range(4):
                    tx, ty = test_x + dx, test_y + dy
                    if not grid.is_walkable(tx, ty, 0):
                        all_clear = False
                        break
                if not all_clear:
                    break
            
            if all_clear:
                stockpile_x = test_x
                stockpile_y = test_y
                found = True
                break
        if found:
            break
    
    if not found:
        print("[WorldGen] WARNING: Could not find clear area for starter stockpile")
        return
    
    # Create stockpile zone
    tiles = []
    for dx in range(4):
        for dy in range(4):
            tiles.append((stockpile_x + dx, stockpile_y + dy, 0))
    
    zone_id = zones.create_stockpile_zone(tiles, grid, z=0)
    if zone_id < 0:
        print("[WorldGen] WARNING: Failed to create starter stockpile zone")
        return
    
    # Add starter resources - distribute across tiles
    starter_resources = [
        ("wood", 50),
        ("mineral", 50),
        ("metal", 30),
        ("scrap", 40),
        ("raw_food", 30),
        ("power", 20),
    ]
    
    tile_index = 0
    for resource_type, amount in starter_resources:
        # Spread resources across multiple tiles if needed
        remaining = amount
        while remaining > 0 and tile_index < len(tiles):
            tx, ty, tz = tiles[tile_index]
            stored = zones.add_to_tile_storage(tx, ty, tz, resource_type, remaining)
            remaining -= stored
            if stored > 0:
                tile_index += 1  # Move to next tile for variety
    
    print(f"[WorldGen] ★ Starter stockpile created at ({stockpile_x}, {stockpile_y}) with resources")


def is_resource_node(tile_value: Optional[str]) -> bool:
    """Return True if the tile string corresponds to a resource node."""

    return tile_value == "resource_node"


def update_resource_nodes(grid) -> None:
    """Tick respawn timers for depleted nodes and respawn when ready.
    
    Call this once per game tick from the main loop.
    Node cannot respawn while a dropped resource item is on the tile.
    Non-replenishable nodes (regrow_time=0) are removed once their dropped item is collected.
    """
    nodes_to_remove = []
    
    for (x, y), node in _RESOURCE_NODES.items():
        if not node.get("depleted", False):
            continue
        
        regrow_time = node.get("regrow_time", 0)
        if regrow_time <= 0:
            # Non-replenishable node (e.g., scrap piles)
            # Remove it once the dropped item has been collected
            if (x, y) not in _RESOURCE_ITEMS:
                nodes_to_remove.append((x, y))
            continue
        
        # Can't respawn if there's a dropped item on this tile
        if (x, y) in _RESOURCE_ITEMS:
            continue
        
        # Tick down the timer
        node["regrow_timer"] = node.get("regrow_timer", 0) - 1
        
        if node["regrow_timer"] <= 0:
            # Respawn the node
            node["amount"] = node.get("max_amount", 1)
            node["depleted"] = False
            node["state"] = NodeState.IDLE
            node["regrow_timer"] = 0
            # Make sure tile is still marked as resource_node
            grid.set_tile(x, y, "resource_node")
    
    # Remove depleted non-replenishable nodes
    for (x, y) in nodes_to_remove:
        _RESOURCE_NODES.pop((x, y), None)
        grid.set_tile(x, y, "empty")


def get_node_at(x: int, y: int) -> Optional[dict]:
    """Return the node dict at (x, y), if any."""

    return _RESOURCE_NODES.get((x, y))


def get_all_nodes() -> Dict[Coord, dict]:
    """Return all resource nodes for debug/rendering."""
    return _RESOURCE_NODES.copy()


def get_node_state(x: int, y: int) -> Optional[NodeState]:
    """Return the state of the node at (x, y), if any."""
    node = get_node_at(x, y)
    if node is None:
        return None
    return node.get("state", NodeState.IDLE)


def set_node_state(x: int, y: int, state: NodeState) -> None:
    """Set the state of the node at (x, y)."""
    node = get_node_at(x, y)
    if node is not None:
        node["state"] = state


def _remove_node_at(x: int, y: int) -> None:
    _RESOURCE_NODES.pop((x, y), None)


def clear_node_for_construction(x: int, y: int) -> bool:
    """Clear a resource node for construction, spawning its resources as items.
    
    Forces all remaining resources to drop as items (marked for hauling),
    then removes the node permanently (no respawn).
    
    Returns True if a node was cleared, False if no node existed.
    """
    node = _RESOURCE_NODES.get((x, y))
    if node is None:
        return False
    
    # Drop all remaining resources as items
    resource_type = node.get("resource", "wood")
    amount = node.get("amount", 0)
    
    if amount > 0:
        # Spawn items and mark for hauling - nodes are always on z=0
        spawn_resource_item(x, y, 0, resource_type, amount, auto_haul=True)
    
    # Remove the node permanently (no respawn)
    _RESOURCE_NODES.pop((x, y), None)
    return True


def has_resource_node(x: int, y: int) -> bool:
    """Check if there's a resource node at (x, y)."""
    return (x, y) in _RESOURCE_NODES


def harvest_tick(x: int, y: int, job_progress: int, job_required: int) -> bool:
    """Called each work tick during gathering. Harvests resources incrementally.
    
    Divides the node's resources evenly across the job duration.
    Spawns resource items on the tile instead of adding directly to stockpile.
    Returns True if a resource was harvested this tick.
    """
    node = get_node_at(x, y)
    if node is None or node.get("amount", 0) <= 0:
        return False
    
    max_amount = node.get("max_amount", 1)
    current_amount = node.get("amount", 0)
    
    # Calculate how many resources should have been harvested by this progress point
    # Spread harvests evenly across the job duration
    ticks_per_resource = job_required / max_amount if max_amount > 0 else job_required
    expected_harvested = int(job_progress / ticks_per_resource) if ticks_per_resource > 0 else 0
    actual_harvested = max_amount - current_amount
    
    # If we should have harvested more than we have, harvest one now
    if expected_harvested > actual_harvested and current_amount > 0:
        resource_type = node.get("resource", "wood")
        node["amount"] -= 1
        
        # All resources auto-haul to stockpile zones
        auto_haul = True
        
        # Spawn resource item on the tile instead of adding to stockpile - z=0 for nodes
        spawn_resource_item(x, y, 0, resource_type, 1, auto_haul=auto_haul)
        
        # Set state to YIELDED (resources available for pickup)
        node["state"] = NodeState.YIELDED
        
        # Mark as depleted when empty and start respawn timer
        if node["amount"] <= 0:
            node["depleted"] = True
            node["state"] = NodeState.DEPLETED
            # Start respawn timer if this node type can regrow
            regrow_time = node.get("regrow_time", 0)
            if regrow_time > 0:
                node["regrow_timer"] = regrow_time
        
        return True
    
    return False


def harvest_resource(node: dict) -> Optional[dict]:
    """Harvest a single unit from *node* and return a resource item.

    The caller is responsible for handling depletion side effects such as
    removing the node entry and updating the grid tile.
    """

    if node.get("amount", 0) <= 0:
        return None

    node["amount"] -= 1
    
    # Mark as depleted when empty
    if node["amount"] <= 0:
        node["depleted"] = True
        node["state"] = NodeState.DEPLETED
        # Start regrowth timer if applicable (scaffold for future)
        if node.get("regrow_time", 0) > 0:
            node["regrow_timer"] = node["regrow_time"]
    
    resource_type = node.get("resource", "wood")
    return {"type": resource_type, "quantity": 1}


# --- Resource piles -----------------------------------------------------------


def get_pile_at(x: int, y: int) -> Optional[dict]:
    return _RESOURCE_PILES.get((x, y))


def drop_resource_item(grid, x: int, y: int, item: dict) -> None:
    """Drop a resource item on the ground as/into a pile.

    For now we assume a single resource type per pile and just accumulate the
    quantity when multiple items are dropped on the same tile.
    """

    key = (x, y)
    pile = _RESOURCE_PILES.get(key)

    if pile is None:
        pile = {"type": item["type"], "quantity": item.get("quantity", 1)}
        _RESOURCE_PILES[key] = pile
    else:
        if pile["type"] == item["type"]:
            pile["quantity"] += item.get("quantity", 1)
        else:
            # If types differ, keep the original for simplicity in this stage.
            pile["quantity"] += item.get("quantity", 1)

    grid.set_tile(x, y, "resource_pile")


def remove_node_if_empty(grid, x: int, y: int) -> None:
    """Handle depleted nodes - keep them if they can respawn, remove if not.

    Nodes with regrow_time > 0 stay in depleted state for respawning.
    Nodes with regrow_time = 0 are removed permanently.
    Some nodes convert to a different tile type (e.g., street -> dirt).
    """

    node = get_node_at(x, y)
    if node is not None and node.get("amount", 0) <= 0:
        regrow_time = node.get("regrow_time", 0)
        converts_to = node.get("converts_to")
        
        if regrow_time > 0:
            # Keep the node for respawning - it stays as depleted resource_node
            # Tile remains "resource_node" so it renders in depleted color
            pass
        else:
            # No respawn - remove permanently
            _remove_node_at(x, y)
            # Only clear to empty if there is no pile here.
            if (x, y) not in _RESOURCE_PILES:
                # Convert to specified tile type, or empty
                new_tile = converts_to if converts_to else "dirt"
                grid.set_tile(x, y, new_tile)


# --- Job integration helpers --------------------------------------------------


def create_gathering_job_for_node(jobs_module, grid, x: int, y: int) -> bool:
    """Create a gathering job if a node exists at (x, y).

    This keeps job-creation logic for resources in one place while delegating
    actual queue management to jobs.py.
    
    Returns True if job was created, False otherwise.
    """

    node = get_node_at(x, y)
    if node is None or node.get("amount", 0) <= 0:
        return False
    
    # Don't create duplicate jobs at the same location
    if jobs_module.get_job_at(x, y) is not None:
        return False

    resource_type = node.get("resource", "wood")
    jobs_module.add_job("gathering", x, y, required=40, resource_type=resource_type)
    return True


def complete_gathering_job(grid, job) -> None:
    """Apply the effects of a completed gathering job on the world.

    Resources are now harvested incrementally via harvest_tick(), so this
    just handles cleanup when the job finishes.
    """

    node = get_node_at(job.x, job.y)
    if node is None:
        return

    # Handle node removal/respawn state
    remove_node_if_empty(grid, job.x, job.y)


# --- Save/Load ---

def get_save_state() -> dict:
    """Get resources state for saving."""
    # Resource nodes
    nodes_data = {}
    for coord, node in _RESOURCE_NODES.items():
        key = f"{coord[0]},{coord[1]}"
        nodes_data[key] = {
            "type": node.get("type"),
            "resource": node.get("resource"),
            "amount": node.get("amount", 0),
            "state": node.get("state", NodeState.IDLE).value if isinstance(node.get("state"), NodeState) else node.get("state", "idle"),
        }
    
    # Resource items on ground
    items_data = {}
    for coord, item in _RESOURCE_ITEMS.items():
        key = f"{coord[0]},{coord[1]},{coord[2]}"
        items_data[key] = {
            "type": item.get("type"),
            "amount": item.get("amount", 1),
            "reserved": item.get("reserved", False),
        }
    
    return {
        "nodes": nodes_data,
        "items": items_data,
        "stockpile": dict(_STOCKPILE),
        "reserved": dict(_RESERVED),
    }


def load_save_state(state: dict):
    """Restore resources state from save."""
    global _RESOURCE_NODES, _RESOURCE_ITEMS, _STOCKPILE, _RESERVED
    
    _RESOURCE_NODES.clear()
    _RESOURCE_ITEMS.clear()
    
    # Restore nodes
    for key, node_data in state.get("nodes", {}).items():
        parts = key.split(",")
        coord = (int(parts[0]), int(parts[1]))
        state_str = node_data.get("state", "idle")
        try:
            node_state = NodeState(state_str)
        except ValueError:
            node_state = NodeState.IDLE
        
        _RESOURCE_NODES[coord] = {
            "type": node_data.get("type"),
            "resource": node_data.get("resource"),
            "amount": node_data.get("amount", 0),
            "state": node_state,
        }
    
    # Restore items
    for key, item_data in state.get("items", {}).items():
        parts = key.split(",")
        coord = (int(parts[0]), int(parts[1]), int(parts[2]))
        _RESOURCE_ITEMS[coord] = {
            "type": item_data.get("type"),
            "amount": item_data.get("amount", 1),
            "reserved": False,  # Reset reservations on load
        }
    
    # Restore stockpile
    for res_type, amount in state.get("stockpile", {}).items():
        _STOCKPILE[res_type] = amount
    
    # Restore reserved (but probably should reset to 0)
    for res_type in _RESERVED:
        _RESERVED[res_type] = 0  # Reset reservations on load
