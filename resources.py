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
    "mineral_node": {"resource": "mineral", "amount": 75, "regrow_time": 900, "replenishable": True, "loose": False},
    "food_plant": {"resource": "raw_food", "amount": 20, "regrow_time": 800, "replenishable": True, "loose": False},
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


# --- Node helpers -------------------------------------------------------------


def _place_node(grid, x: int, y: int, node_type: str) -> bool:
    """Place a single resource node at (x, y). Returns True if successful.
    
    For loose node types (like scrap), spawns items directly on the ground
    instead of creating a harvestable node.
    """
    tile = grid.get_tile(x, y)
    if tile != "empty":
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


def _spawn_ruined_buildings(grid) -> int:
    """Spawn 1-2 ruined buildings made of salvage objects.
    
    Each ruin is a rectangular building outline (walls only, no floor)
    that players can dismantle for scrap.
    
    Returns total salvage tiles placed.
    """
    total_placed = 0
    num_ruins = random.randint(1, 2)
    
    for _ in range(num_ruins):
        # Random building size (small to medium)
        width = random.randint(4, 7)
        height = random.randint(4, 7)
        
        # Find a valid location (needs enough empty space)
        for attempt in range(30):
            # Leave margin from edges
            x = random.randint(2, GRID_W - width - 2)
            y = random.randint(2, GRID_H - height - 2)
            
            # Check if area is clear
            area_clear = True
            for dx in range(width):
                for dy in range(height):
                    tile = grid.get_tile(x + dx, y + dy, 0)
                    if tile != "empty":
                        area_clear = False
                        break
                    if (x + dx, y + dy) in _RESOURCE_NODES:
                        area_clear = False
                        break
                if not area_clear:
                    break
            
            if not area_clear:
                continue
            
            # Place the ruined building (walls only - rectangular outline)
            placed = 0
            for dx in range(width):
                for dy in range(height):
                    # Only place on edges (walls)
                    is_wall = (dx == 0 or dx == width - 1 or dy == 0 or dy == height - 1)
                    if not is_wall:
                        continue
                    
                    # Random chance to have gaps (ruined look)
                    if random.random() < 0.15:
                        continue
                    
                    px, py = x + dx, y + dy
                    salvage_type = random.choice(["ruined_wall", "salvage_pile"])
                    if spawn_salvage_object(px, py, salvage_type):
                        grid.set_tile(px, py, "salvage_object", z=0)
                        placed += 1
            
            total_placed += placed
            break  # Successfully placed this ruin
    
    return total_placed


def spawn_resource_nodes(grid, count: int = 40) -> None:
    """Spawn resource nodes in natural-looking clusters.
    
    Creates grouped formations:
    - Trees spawn in forest clusters (3-6 trees each)
    - Minerals spawn in rock formations (2-4 nodes each)
    - Scrap spawns in small piles (1-2 each)
    """
    placed = 0
    
    # Cluster configurations: (node_type, num_clusters, min_size, max_size)
    cluster_configs = [
        ("tree", 6, 4, 8),           # 6 forest clusters, 4-8 trees each
        ("mineral_node", 4, 3, 5),   # 4 rock formations, 3-5 nodes each
        ("scrap_pile", 3, 2, 3),     # 3 scrap areas, 2-3 piles each
        ("food_plant", 3, 2, 4),     # 3 food patches, 2-4 plants each
    ]
    
    for node_type, num_clusters, min_size, max_size in cluster_configs:
        for _ in range(num_clusters):
            # Random center point for this cluster
            center_x = random.randint(2, GRID_W - 3)
            center_y = random.randint(2, GRID_H - 3)
            
            cluster_size = random.randint(min_size, max_size)
            nodes_placed = _spawn_cluster(grid, center_x, center_y, node_type, cluster_size)
            placed += nodes_placed
    
    # Spawn salvage objects in building-shaped ruins
    salvage_placed = _spawn_ruined_buildings(grid)
    
    print(f"[Resources] Spawned {placed} resource nodes in clusters")
    print(f"[Resources] Spawned {salvage_placed} salvage tiles in ruined buildings")


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
    """

    node = get_node_at(x, y)
    if node is not None and node.get("amount", 0) <= 0:
        regrow_time = node.get("regrow_time", 0)
        
        if regrow_time > 0:
            # Keep the node for respawning - it stays as depleted resource_node
            # Tile remains "resource_node" so it renders in depleted color
            pass
        else:
            # No respawn - remove permanently
            _remove_node_at(x, y)
            # Only clear to empty if there is no pile here.
            if (x, y) not in _RESOURCE_PILES:
                grid.set_tile(x, y, "empty")


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
