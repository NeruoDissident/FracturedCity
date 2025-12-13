"""
Wanderer/Refugee system for Fractured City.

Wanderers are potential colonists who appear at map edges and can be recruited.
- Spawn randomly (chance per day)
- Guaranteed spawn after X days without visitors
- 1-6 wanderers can arrive at once
- Walk toward colony center
- Can be recruited via right-click
- Leave if ignored for too long
"""

import random
from typing import Optional, List, Tuple
from config import GRID_W, GRID_H

# Wanderer state
_wanderers: List[dict] = []
_last_spawn_day: int = -1
_days_since_visitor: int = 0
_guarantee_threshold: int = 0  # Days until guaranteed spawn (set randomly)

# Tuning
SPAWN_CHANCE_PER_DAY = 0.20  # 20% chance each day
MAX_WANDERERS = 8  # Max wanderers waiting at once
PATIENCE_TICKS = 3600  # ~1 minute at 60fps before they leave

# Guarantee thresholds based on location type
GUARANTEE_RANGE_URBAN = (2, 3)   # City zones: 2-3 days
GUARANTEE_RANGE_SUBURBAN = (3, 4)  # Default: 3-4 days
GUARANTEE_RANGE_RURAL = (4, 6)   # Remote areas: 4-6 days

# How many wanderers can arrive at once
MIN_GROUP_SIZE = 1
MAX_GROUP_SIZE = 6


def get_wanderers() -> List[dict]:
    """Get list of active wanderers."""
    return _wanderers.copy()


def _get_location_type(colony_center: Tuple[int, int]) -> str:
    """Determine if colony is urban, suburban, or rural based on position.
    
    Center of map = urban, edges = rural.
    """
    cx, cy = colony_center
    map_center_x, map_center_y = GRID_W // 2, GRID_H // 2
    
    dist_from_center = abs(cx - map_center_x) + abs(cy - map_center_y)
    max_dist = GRID_W // 2 + GRID_H // 2
    
    ratio = dist_from_center / max_dist
    
    if ratio < 0.25:
        return "urban"
    elif ratio < 0.5:
        return "suburban"
    else:
        return "rural"


def _roll_guarantee_threshold(colony_center: Tuple[int, int]) -> int:
    """Roll a new guarantee threshold based on location."""
    location = _get_location_type(colony_center)
    
    if location == "urban":
        return random.randint(*GUARANTEE_RANGE_URBAN)
    elif location == "suburban":
        return random.randint(*GUARANTEE_RANGE_SUBURBAN)
    else:
        return random.randint(*GUARANTEE_RANGE_RURAL)


def spawn_wanderer_check(current_day: int, colony_center: Tuple[int, int], grid) -> List[dict]:
    """Check if wanderers should spawn. Call once per tick.
    
    Returns list of new wanderer dicts spawned (may be empty).
    """
    global _last_spawn_day, _days_since_visitor, _guarantee_threshold
    
    # Only check once per day
    if current_day == _last_spawn_day:
        return []
    
    _last_spawn_day = current_day
    _days_since_visitor += 1
    
    # Initialize guarantee threshold if not set
    if _guarantee_threshold == 0:
        _guarantee_threshold = _roll_guarantee_threshold(colony_center)
        print(f"[Wanderer] Guarantee threshold set to {_guarantee_threshold} days ({_get_location_type(colony_center)} area)")
    
    # Too many wanderers already?
    if len(_wanderers) >= MAX_WANDERERS:
        return []
    
    # Check if we should spawn
    should_spawn = False
    guaranteed = False
    
    # Guaranteed spawn if threshold reached
    if _days_since_visitor >= _guarantee_threshold:
        should_spawn = True
        guaranteed = True
    # Random chance
    elif random.random() < SPAWN_CHANCE_PER_DAY:
        should_spawn = True
    
    if not should_spawn:
        return []
    
    # Spawn wanderers!
    # Determine group size (1-6, but don't exceed max capacity)
    available_slots = MAX_WANDERERS - len(_wanderers)
    group_size = random.randint(MIN_GROUP_SIZE, min(MAX_GROUP_SIZE, available_slots))
    
    # Guaranteed spawns get at least 1
    if guaranteed and group_size < 1:
        group_size = 1
    
    # Pick ONE spawn location for the whole group (they travel together)
    group_spawn = _pick_group_spawn_location(grid)
    if not group_spawn:
        return []
    
    spawned = []
    for i in range(group_size):
        # Spread around the group spawn point
        offset_x = (i % 3) - 1  # -1, 0, 1
        offset_y = (i // 3) - 1  # -1, 0, 1
        spawn_x = group_spawn[0] + offset_x
        spawn_y = group_spawn[1] + offset_y
        
        # Make sure it's walkable, otherwise use base point
        if not grid.is_walkable(spawn_x, spawn_y, 0):
            spawn_x, spawn_y = group_spawn
        
        wanderer = _create_wanderer_at(spawn_x, spawn_y, colony_center, grid)
        if wanderer:
            _wanderers.append(wanderer)
            spawned.append(wanderer)
    
    if spawned:
        # Reset counter and roll new threshold
        _days_since_visitor = 0
        _guarantee_threshold = _roll_guarantee_threshold(colony_center)
        
        names = ", ".join(w["name"] for w in spawned)
        spawn_type = "guaranteed" if guaranteed else "random"
        print(f"[Wanderer] {len(spawned)} visitor(s) arrived ({spawn_type}): {names}")
        
        # Store group spawn location for camera jump
        spawned[0]["group_spawn"] = group_spawn
    
    return spawned


def _pick_group_spawn_location(grid) -> Optional[Tuple[int, int]]:
    """Pick a single spawn location for a group of wanderers."""
    # Pick a random edge
    edge = random.choice(["north", "south", "east", "west"])
    
    # Find a walkable spawn point on that edge
    attempts = 50
    
    for _ in range(attempts):
        if edge == "north":
            x = random.randint(10, GRID_W - 10)
            y = 5
        elif edge == "south":
            x = random.randint(10, GRID_W - 10)
            y = GRID_H - 5
        elif edge == "west":
            x = 5
            y = random.randint(10, GRID_H - 10)
        else:  # east
            x = GRID_W - 5
            y = random.randint(10, GRID_H - 10)
        
        if grid.is_walkable(x, y, 0):
            return (x, y)
    
    return None


def _create_wanderer_at(x: int, y: int, colony_center: Tuple[int, int], grid) -> Optional[dict]:
    """Create a new wanderer at a specific position."""
    from colonist import Colonist
    
    # Create a colonist object (but not added to main list yet)
    colonist = Colonist(x=x, y=y)
    
    # Wanderer metadata
    wanderer = {
        "colonist": colonist,
        "name": colonist.name,
        "x": x,
        "y": y,
        "spawn_tick": 0,  # Will be set by caller
        "patience": PATIENCE_TICKS,
        "target": colony_center,
        "state": "approaching",  # approaching, waiting, leaving
    }
    
    return wanderer


def _create_wanderer(colony_center: Tuple[int, int], grid) -> Optional[dict]:
    """Create a new wanderer at a random map edge. (Legacy, used by debug)"""
    spawn = _pick_group_spawn_location(grid)
    if not spawn:
        return None
    return _create_wanderer_at(spawn[0], spawn[1], colony_center, grid)


def update_wanderers(grid, colony_center: Tuple[int, int], game_tick: int) -> None:
    """Update all wanderers. Call once per tick."""
    to_remove = []
    
    for wanderer in _wanderers:
        colonist = wanderer["colonist"]
        
        # Set spawn tick if not set
        if wanderer["spawn_tick"] == 0:
            wanderer["spawn_tick"] = game_tick
        
        # Update position tracking
        wanderer["x"] = colonist.x
        wanderer["y"] = colonist.y
        
        if wanderer["state"] == "approaching":
            # Move toward colony center
            _move_toward_target(colonist, wanderer["target"], grid)
            
            # Check if close enough to wait
            dist = abs(colonist.x - colony_center[0]) + abs(colonist.y - colony_center[1])
            if dist < 15:
                wanderer["state"] = "waiting"
                print(f"[Wanderer] {wanderer['name']} is waiting near the colony")
        
        elif wanderer["state"] == "waiting":
            # Decrease patience
            wanderer["patience"] -= 1
            
            # Wander a bit while waiting
            if random.random() < 0.01:
                _wander_nearby(colonist, colony_center, grid)
            
            # Out of patience?
            if wanderer["patience"] <= 0:
                wanderer["state"] = "leaving"
                print(f"[Wanderer] {wanderer['name']} is leaving (not recruited)")
        
        elif wanderer["state"] == "leaving":
            # Move toward map edge
            edge_target = _get_nearest_edge(colonist.x, colonist.y)
            _move_toward_target(colonist, edge_target, grid)
            
            # Check if off map
            if colonist.x <= 2 or colonist.x >= GRID_W - 2 or colonist.y <= 2 or colonist.y >= GRID_H - 2:
                to_remove.append(wanderer)
                print(f"[Wanderer] {wanderer['name']} left the area")
    
    # Remove departed wanderers
    for w in to_remove:
        _wanderers.remove(w)


def _move_toward_target(colonist, target: Tuple[int, int], grid) -> None:
    """Simple movement toward target."""
    if colonist.move_cooldown > 0:
        colonist.move_cooldown -= 1
        return
    
    tx, ty = target
    dx = 0 if colonist.x == tx else (1 if tx > colonist.x else -1)
    dy = 0 if colonist.y == ty else (1 if ty > colonist.y else -1)
    
    # Try to move
    new_x = colonist.x + dx
    new_y = colonist.y + dy
    
    if grid.is_walkable(new_x, new_y, 0):
        colonist.x = new_x
        colonist.y = new_y
        colonist.move_cooldown = colonist.move_speed
    elif dx != 0 and grid.is_walkable(colonist.x + dx, colonist.y, 0):
        colonist.x += dx
        colonist.move_cooldown = colonist.move_speed
    elif dy != 0 and grid.is_walkable(colonist.x, colonist.y + dy, 0):
        colonist.y += dy
        colonist.move_cooldown = colonist.move_speed


def _wander_nearby(colonist, center: Tuple[int, int], grid) -> None:
    """Random wander near the colony."""
    dx = random.randint(-1, 1)
    dy = random.randint(-1, 1)
    new_x = colonist.x + dx
    new_y = colonist.y + dy
    
    # Stay near center
    if abs(new_x - center[0]) < 20 and abs(new_y - center[1]) < 20:
        if grid.is_walkable(new_x, new_y, 0):
            colonist.x = new_x
            colonist.y = new_y


def _get_nearest_edge(x: int, y: int) -> Tuple[int, int]:
    """Get the nearest map edge point."""
    distances = [
        (y, (x, 0)),           # North
        (GRID_H - y, (x, GRID_H)),  # South
        (x, (0, y)),           # West
        (GRID_W - x, (GRID_W, y)),  # East
    ]
    distances.sort(key=lambda d: d[0])
    return distances[0][1]


def recruit_wanderer(wanderer: dict) -> Optional["Colonist"]:
    """Recruit a wanderer, returning the Colonist object to add to main list."""
    if wanderer not in _wanderers:
        return None
    
    colonist = wanderer["colonist"]
    _wanderers.remove(wanderer)
    
    # Reset colonist state for proper integration
    colonist.state = "idle"
    colonist.current_job = None
    colonist.current_path = []
    
    print(f"[Wanderer] {wanderer['name']} has joined the colony!")
    colonist.add_thought("social", "Found a new home.", 0.3, game_tick=0)
    
    return colonist


def get_wanderer_at(x: int, y: int, z: int = 0) -> Optional[dict]:
    """Get wanderer at position, if any."""
    for wanderer in _wanderers:
        if wanderer["x"] == x and wanderer["y"] == y:
            return wanderer
    return None


def reject_wanderer(wanderer: dict) -> None:
    """Reject a wanderer, making them leave immediately."""
    if wanderer not in _wanderers:
        return
    
    wanderer["state"] = "leaving"
    wanderer["patience"] = 0
    print(f"[Wanderer] {wanderer['name']} was rejected and is leaving")


# =============================================================================
# FIXERS (Trading Wanderers)
# =============================================================================

_fixers: List[dict] = []
_last_fixer_day: int = -1
_days_since_fixer: int = 0

FIXER_SPAWN_CHANCE = 0.10  # 10% per day
FIXER_GUARANTEE_DAYS = 7   # Guaranteed fixer every 7 days
FIXER_PATIENCE_TICKS = 5400  # ~1.5 minutes before leaving


def get_fixers() -> List[dict]:
    """Get list of active fixers."""
    return _fixers.copy()


def spawn_fixer_check(current_day: int, colony_center: Tuple[int, int], grid) -> Optional[dict]:
    """Check if a fixer should spawn. Call once per tick."""
    global _last_fixer_day, _days_since_fixer
    
    if current_day == _last_fixer_day:
        return None
    
    _last_fixer_day = current_day
    _days_since_fixer += 1
    
    # Max 1 fixer at a time
    if len(_fixers) >= 1:
        return None
    
    # Check spawn
    should_spawn = False
    if _days_since_fixer >= FIXER_GUARANTEE_DAYS:
        should_spawn = True
    elif random.random() < FIXER_SPAWN_CHANCE:
        should_spawn = True
    
    if not should_spawn:
        return None
    
    fixer = _create_fixer(colony_center, grid)
    if fixer:
        _fixers.append(fixer)
        _days_since_fixer = 0
        print(f"[Fixer] {fixer['name']} arrived from {fixer['origin'].name}!")
    
    return fixer


def _create_fixer(colony_center: Tuple[int, int], grid) -> Optional[dict]:
    """Create a new fixer at map edge."""
    from colonist import Colonist
    from economy import get_random_origin, generate_fixer_name, generate_fixer_inventory
    
    # Pick a random edge
    edge = random.choice(["north", "south", "east", "west"])
    
    attempts = 50
    x, y = 0, 0
    
    for _ in range(attempts):
        if edge == "north":
            x = random.randint(10, GRID_W - 10)
            y = 5
        elif edge == "south":
            x = random.randint(10, GRID_W - 10)
            y = GRID_H - 5
        elif edge == "west":
            x = 5
            y = random.randint(10, GRID_H - 10)
        else:
            x = GRID_W - 5
            y = random.randint(10, GRID_H - 10)
        
        if grid.is_walkable(x, y, 0):
            break
    else:
        return None
    
    # Create colonist visual (not recruitable)
    colonist = Colonist(x=x, y=y)
    
    # Fixer-specific data
    origin = get_random_origin()
    
    fixer = {
        "colonist": colonist,
        "name": generate_fixer_name(),
        "x": x,
        "y": y,
        "origin": origin,
        "inventory": generate_fixer_inventory(origin),
        "patience": FIXER_PATIENCE_TICKS,
        "target": colony_center,
        "state": "approaching",
        "is_fixer": True,
    }
    
    return fixer


def update_fixers(grid, colony_center: Tuple[int, int], game_tick: int) -> None:
    """Update all fixers."""
    to_remove = []
    
    for fixer in _fixers:
        colonist = fixer["colonist"]
        fixer["x"] = colonist.x
        fixer["y"] = colonist.y
        
        if fixer["state"] == "approaching":
            _move_toward_target(colonist, fixer["target"], grid)
            
            dist = abs(colonist.x - colony_center[0]) + abs(colonist.y - colony_center[1])
            if dist < 15:
                fixer["state"] = "waiting"
                print(f"[Fixer] {fixer['name']} is ready to trade")
        
        elif fixer["state"] == "waiting":
            fixer["patience"] -= 1
            
            if random.random() < 0.01:
                _wander_nearby(colonist, colony_center, grid)
            
            if fixer["patience"] <= 0:
                fixer["state"] = "leaving"
                print(f"[Fixer] {fixer['name']} is leaving (no trades made)")
        
        elif fixer["state"] == "trading":
            # Stay put while trade is being executed by colonists
            # Don't decrease patience - trade is in progress
            pass
        
        elif fixer["state"] == "leaving":
            edge_target = _get_nearest_edge(colonist.x, colonist.y)
            _move_toward_target(colonist, edge_target, grid)
            
            if colonist.x <= 2 or colonist.x >= GRID_W - 2 or colonist.y <= 2 or colonist.y >= GRID_H - 2:
                to_remove.append(fixer)
                print(f"[Fixer] {fixer['name']} left the area")
    
    for f in to_remove:
        _fixers.remove(f)


def get_fixer_at(x: int, y: int, z: int = 0) -> Optional[dict]:
    """Get fixer at position, if any."""
    for fixer in _fixers:
        if fixer["x"] == x and fixer["y"] == y:
            return fixer
    return None


def dismiss_fixer(fixer: dict) -> None:
    """Make a fixer leave after trading."""
    if fixer in _fixers:
        fixer["state"] = "leaving"
        print(f"[Fixer] {fixer['name']} is heading out")


# =============================================================================
# Trade Job System
# =============================================================================
# When a trade is confirmed, we store the pending trade on the fixer and create
# jobs for colonists to physically exchange goods.

def queue_trade(fixer: dict, player_offer: dict, fixer_offer: dict) -> bool:
    """Queue a trade for colonist execution.
    
    Args:
        fixer: The fixer dict
        player_offer: {item_id: qty} items player is giving
        fixer_offer: {item_id: qty} items fixer is giving
    
    Returns True if trade was queued.
    """
    if not fixer:
        return False
    
    # Store pending trade on fixer
    fixer["pending_trade"] = {
        "player_offer": {k: v for k, v in player_offer.items() if v > 0},
        "fixer_offer": {k: v for k, v in fixer_offer.items() if v > 0},
        "state": "pending",  # pending -> delivering -> collecting -> complete
        "delivered": {},  # Track what's been delivered to fixer
        "collected": {},  # Track what's been collected from fixer
    }
    
    # Change fixer state to trading (won't leave while trade pending)
    fixer["state"] = "trading"
    print(f"[Trade] Trade queued with {fixer['name']}")
    
    return True


def get_pending_trade(fixer: dict) -> Optional[dict]:
    """Get pending trade data from fixer, if any."""
    return fixer.get("pending_trade") if fixer else None


def complete_trade_delivery(fixer: dict, item_id: str, amount: int) -> None:
    """Called when colonist delivers items TO the fixer."""
    trade = fixer.get("pending_trade")
    if not trade:
        return
    
    trade["delivered"][item_id] = trade["delivered"].get(item_id, 0) + amount
    print(f"[Trade] Delivered {amount} {item_id} to fixer. Total delivered: {trade['delivered']}")
    
    # Check if all player items delivered
    all_delivered = True
    for iid, needed in trade["player_offer"].items():
        delivered_amt = trade["delivered"].get(iid, 0)
        if delivered_amt < needed:
            print(f"[Trade] Still need {needed - delivered_amt} more {iid}")
            all_delivered = False
            break
    
    if all_delivered:
        trade["state"] = "collecting"
        print(f"[Trade] All items delivered to {fixer['name']}, ready for pickup")


def complete_trade_collection(fixer: dict, item_id: str, amount: int) -> None:
    """Called when colonist collects items FROM the fixer."""
    trade = fixer.get("pending_trade")
    if not trade:
        return
    
    trade["collected"][item_id] = trade["collected"].get(item_id, 0) + amount
    
    # Remove from fixer inventory
    if item_id in fixer["inventory"]:
        fixer["inventory"][item_id] -= amount
        if fixer["inventory"][item_id] <= 0:
            del fixer["inventory"][item_id]
    
    # Check if all fixer items collected
    all_collected = True
    for item_id, needed in trade["fixer_offer"].items():
        if trade["collected"].get(item_id, 0) < needed:
            all_collected = False
            break
    
    if all_collected:
        trade["state"] = "complete"
        fixer["pending_trade"] = None
        fixer["state"] = "leaving"  # Trade done, fixer leaves
        print(f"[Trade] Trade complete with {fixer['name']}, fixer departing")


BASE_CARRY_AMOUNT = 10  # Base amount a colonist can carry per trip

def create_trade_jobs(fixer: dict, jobs_module, zones_module) -> int:
    """Create jobs to execute a pending trade.
    
    Returns number of jobs created.
    Creates all needed jobs upfront, split by carry capacity.
    """
    trade = fixer.get("pending_trade")
    if not trade:
        return 0
    
    fixer_x, fixer_y = fixer["x"], fixer["y"]
    
    # Get all existing trade jobs for this fixer
    existing_jobs = jobs_module.get_jobs_by_type("trade_deliver") + jobs_module.get_jobs_by_type("trade_collect")
    active_deliver = [j for j in existing_jobs if j.type == "trade_deliver" and j.dest_x == fixer_x and j.dest_y == fixer_y]
    active_collect = [j for j in existing_jobs if j.type == "trade_collect" and j.x == fixer_x and j.y == fixer_y]
    
    jobs_created = 0
    
    # Create delivery jobs (player items -> fixer)
    if trade["state"] == "pending" and len(active_deliver) == 0:
        for item_id, qty in trade["player_offer"].items():
            already_delivered = trade["delivered"].get(item_id, 0)
            remaining = qty - already_delivered
            if remaining <= 0:
                continue
            
            # Create jobs for this resource type, split by carry capacity
            while remaining > 0:
                carry_amount = min(remaining, BASE_CARRY_AMOUNT)
                
                # Find stockpile with this item
                source = zones_module.find_tile_with_resource(item_id, min_amount=1)
                if not source:
                    break  # No more of this resource available
                
                src_x, src_y, src_z = source
                job = jobs_module.add_job(
                    "trade_deliver",
                    src_x, src_y,
                    required=10,
                    resource_type=item_id,
                    dest_x=fixer_x,
                    dest_y=fixer_y,
                    dest_z=0,
                    z=src_z,
                    category="haul",
                )
                job.pickup_amount = carry_amount
                jobs_created += 1
                remaining -= carry_amount
                
                # Limit jobs per resource to avoid spam
                if jobs_created >= 5:
                    break
    
    # Create collection jobs (fixer items -> stockpile)
    if trade["state"] == "collecting" and len(active_collect) == 0:
        for item_id, qty in trade["fixer_offer"].items():
            already_collected = trade["collected"].get(item_id, 0)
            remaining = qty - already_collected
            if remaining <= 0:
                continue
            
            # Create jobs for this resource type, split by carry capacity
            while remaining > 0:
                carry_amount = min(remaining, BASE_CARRY_AMOUNT)
                
                # Find stockpile destination
                dest = zones_module.find_stockpile_tile_for_resource(item_id, z=0, from_x=fixer_x, from_y=fixer_y)
                if not dest:
                    break  # No stockpile available
                
                dest_x, dest_y, dest_z = dest
                job = jobs_module.add_job(
                    "trade_collect",
                    fixer_x, fixer_y,
                    required=10,
                    resource_type=item_id,
                    dest_x=dest_x,
                    dest_y=dest_y,
                    dest_z=dest_z,
                    z=0,
                    category="haul",
                )
                job.pickup_amount = carry_amount
                jobs_created += 1
                remaining -= carry_amount
                
                # Limit jobs per resource to avoid spam
                if jobs_created >= 5:
                    break
    
    return jobs_created


_trade_job_cooldown = 0

def process_trade_jobs(jobs_module, zones_module) -> int:
    """Process pending trades and create jobs as needed.
    
    Called from main loop. Only checks every 30 ticks to reduce overhead.
    """
    global _trade_job_cooldown
    
    # Only process every 30 ticks to reduce CPU load
    _trade_job_cooldown -= 1
    if _trade_job_cooldown > 0:
        return 0
    _trade_job_cooldown = 30
    
    jobs_created = 0
    
    for fixer in _fixers:
        trade = fixer.get("pending_trade")
        if not trade:
            continue
        
        # Create jobs for this trade
        jobs_created += create_trade_jobs(fixer, jobs_module, zones_module)
    
    return jobs_created


def get_fixer_for_trade_job(x: int, y: int) -> Optional[dict]:
    """Find fixer at or near position (for trade job completion)."""
    for fixer in _fixers:
        if abs(fixer["x"] - x) <= 1 and abs(fixer["y"] - y) <= 1:
            return fixer
    return None


def draw_wanderers(surface, current_z: int = 0, camera_x: int = 0, camera_y: int = 0) -> None:
    """Draw all wanderers and fixers."""
    import pygame
    from config import TILE_SIZE
    
    # Draw regular wanderers
    for wanderer in _wanderers:
        colonist = wanderer["colonist"]
        if colonist.z != current_z:
            continue
        
        colonist.draw(surface, ether_mode=False, camera_x=camera_x, camera_y=camera_y)
        
        # Draw "?" indicator (recruit)
        screen_x = colonist.x * TILE_SIZE + TILE_SIZE // 2 - camera_x
        screen_y = colonist.y * TILE_SIZE - 8 - camera_y
        
        font = pygame.font.Font(None, 20)
        
        pygame.draw.circle(surface, (60, 80, 60), (screen_x, screen_y), 8)
        pygame.draw.circle(surface, (100, 200, 100), (screen_x, screen_y), 8, 1)
        
        text = font.render("?", True, (200, 255, 200))
        text_rect = text.get_rect(center=(screen_x, screen_y))
        surface.blit(text, text_rect)
    
    # Draw fixers with different indicator
    for fixer in _fixers:
        colonist = fixer["colonist"]
        if colonist.z != current_z:
            continue
        
        colonist.draw(surface, ether_mode=False, camera_x=camera_x, camera_y=camera_y)
        
        # Draw "$" indicator (trade)
        screen_x = colonist.x * TILE_SIZE + TILE_SIZE // 2 - camera_x
        screen_y = colonist.y * TILE_SIZE - 8 - camera_y
        
        font = pygame.font.Font(None, 20)
        
        # Gold/yellow for traders
        pygame.draw.circle(surface, (80, 70, 40), (screen_x, screen_y), 8)
        pygame.draw.circle(surface, (255, 200, 80), (screen_x, screen_y), 8, 1)
        
        text = font.render("$", True, (255, 220, 100))
        text_rect = text.get_rect(center=(screen_x, screen_y))
        surface.blit(text, text_rect)


# =============================================================================
# RAIDERS - Hostile NPCs
# =============================================================================

def spawn_raider(grid) -> Optional["Colonist"]:
    """Spawn a single hostile raider at map edge.
    
    Returns the Colonist object (caller adds to colonists list).
    """
    from colonist import Colonist, generate_colonist_name
    
    spawn = _pick_group_spawn_location(grid)
    if not spawn:
        return None
    
    x, y = spawn
    raider = Colonist(x, y, color=(180, 50, 50))  # Dark red
    raider.name = generate_colonist_name()
    raider.faction = "raiders"
    raider.is_hostile = True
    
    return raider
