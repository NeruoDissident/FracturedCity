"""Colonist simulation and rendering.

Colonists can now take simple construction jobs from the global job queue and
either wander idly or move/ work on assigned tasks.

State Machine
-------------
- IDLE: No job, may wander
- MOVING_TO_TARGET: Has a job and walking towards target
- PERFORMING_JOB: At job location, working on it
- RECOVERY: Interrupted or stuck, brief pause before returning to IDLE
- (eating state handled separately for hunger system)
"""

import random
from typing import Iterable
from enum import Enum

import pygame

from config import (
    TILE_SIZE,
    GRID_W,
    GRID_H,
    COLOR_COLONIST_DEFAULT,
    COLOR_COLONIST_ETHER,
)
from grid import Grid
from jobs import Job, request_job, remove_job, get_next_available_job
from resources import complete_gathering_job, set_node_state, NodeState, harvest_tick, pickup_resource_item, add_to_stockpile, spend_from_stockpile
import buildings
from buildings import deliver_material, mark_supply_job_completed, has_required_materials, is_door, is_door_open, open_door, is_window, is_window_open, open_window, register_window
import zones
from rooms import mark_rooms_dirty


# Colonist states
class ColonistState(Enum):
    IDLE = "idle"
    MOVING_TO_TARGET = "moving_to_job"  # Keep old name for compatibility
    PERFORMING_JOB = "working"  # Keep old name for compatibility
    RECOVERY = "recovery"
    # Additional states for specific behaviors (kept as strings for now)
    HAULING = "hauling"
    CRAFTING_FETCH = "crafting_fetch"
    CRAFTING_WORK = "crafting_work"
    EATING = "eating"


# Default capabilities - all job categories a colonist can potentially do
DEFAULT_CAPABILITIES = {
    "wall": True,
    "harvest": True,
    "construction": True,
    "haul": True,
    "crafting": True,
    "salvage": True,
}


class Colonist:
    """Single colonist agent that can perform construction jobs.

    States
    ------
    - "idle":           No job, may wander.
    - "moving_to_job":  Has a job and is walking towards its tile.
    - "working":        Standing on the job tile and increasing progress.
    - "hauling":        Carrying item to destination.
    - "crafting_fetch": Fetching materials for crafting job.
    - "crafting_work":  Working at workstation.
    - "eating":         Walking to food and eating.
    - "recovery":       Brief pause after interruption before returning to idle.
    
    Interruptibility
    ----------------
    Jobs can be interrupted when:
    - Path becomes blocked (wall built, etc.)
    - Job target becomes invalid (construction completed by another, node depleted)
    - Colonist gets stuck in a non-walkable tile (teleported to safety)
    
    When interrupted, colonist enters recovery state briefly, then returns to idle.
    """

    def __init__(self, x: int, y: int, color: tuple[int, int, int] | None = None):
        self.x = x
        self.y = y
        self.z = 0  # Z-level (0 = ground, 1 = rooftop)
        self.color = color or COLOR_COLONIST_DEFAULT

        self.state: str = "idle"
        self.current_job: Job | None = None
        
        # Movement speed control - move every N ticks
        self.move_cooldown = 0
        self.move_speed = 8  # ticks between moves (lower = faster)
        
        # Path commitment - calculate once, follow until blocked
        # Path now includes z-level: list of (x, y, z) tuples
        self.current_path: list[tuple[int, int, int]] = []
        self.stuck_timer = 0
        self.max_stuck_time = 30  # ticks before giving up on current path
        
        # Recovery state - brief pause after interruption before returning to idle
        self.recovery_timer = 0
        self.recovery_duration = 15  # ticks to wait in recovery state
        
        # Capability flags - which job categories this colonist can perform
        # All True by default; future systems can disable specific capabilities
        self.capabilities: dict[str, bool] = DEFAULT_CAPABILITIES.copy()
        
        # Carrying state for haul jobs
        self.carrying: dict | None = None  # {"type": "wood", "amount": 1}
        
        # Hunger system
        # At 60 FPS: 0.003 per tick = 0.18 per second = ~9 minutes to reach 100
        # Colonists get hungry (>70) at ~6.5 minutes, giving plenty of time to set up food
        self.hunger: float = 0.0  # 0 = full, 100 = starving
        self.hunger_rate: float = 0.003  # Hunger increase per tick (slow)
        self.health: float = 100.0  # 0 = dead
        self.starving_damage: float = 0.05  # Damage per tick when hunger >= 100 (slower death)
        self.is_dead: bool = False

    # --- Core behavior -----------------------------------------------------

    def _maybe_wander_when_idle(self, grid: Grid) -> None:
        """Preserve the original random wandering when idle.

        This keeps the world visually alive when there is no work.
        Now respects walkability to avoid walking through buildings.
        Colonists wander on their current Z-level.
        """

        if random.random() < 0.02:  # 2% chance each frame
            dx, dy = random.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
            new_x = max(0, min(GRID_W - 1, self.x + dx))
            new_y = max(0, min(GRID_H - 1, self.y + dy))
            
            # Only move if the target tile is walkable on current Z-level
            if grid.is_walkable(new_x, new_y, self.z):
                self.x = new_x
                self.y = new_y

    def _try_take_job(self) -> None:
        """Claim a job from the global queue if available."""
        # Skip construction jobs that don't have materials delivered yet
        job = get_next_available_job(skip_types=[], skip_unready_construction=True)
        if job is not None:
            job.assigned = True
            self.current_job = job
            self.current_path = []  # Will be calculated on first move
            self.stuck_timer = 0
            
            # Set resource node to RESERVED state if this is a gathering job
            if job.type == "gathering":
                set_node_state(job.x, job.y, NodeState.RESERVED)
                self.state = "moving_to_job"
            elif job.type == "crafting":
                # Reserve workstation and start fetching materials
                buildings.reserve_workstation(job.x, job.y, job.z)
                self.state = "crafting_fetch"
                self._crafting_inputs_needed = None  # Will be set when we start fetching
            else:
                self.state = "moving_to_job"

    def _calculate_path(self, grid: Grid, target_x: int, target_y: int, target_z: int = 0) -> list[tuple[int, int, int]]:
        """Calculate path to target using BFS with z-level support.
        
        Returns list of (x, y, z) positions to follow.
        
        Fire escape path: Floor → WindowTile → Platform (z=0) → RoofFloor (z=1)
        - WindowTile is at the wall position (passable)
        - Platform is adjacent to the window (external)
        - RoofFloor is above the platform at z=1
        """
        start = (self.x, self.y, self.z)
        goal = (target_x, target_y, target_z)
        
        if start == goal:
            return []
        
        # Get fire escape locations for z-level transitions
        from buildings import get_all_fire_escapes, is_fire_escape_complete
        fire_escapes = get_all_fire_escapes()
        
        # Build a map of (platform_x, platform_y, z) -> fire escape data
        # Fire escapes connect Z to Z+1 at the platform position
        platform_transitions = {}
        for (wx, wy, wz), escape_data in fire_escapes.items():
            if is_fire_escape_complete(wx, wy, wz):
                platform_pos = escape_data.get("platform_pos")
                if platform_pos:
                    px, py = platform_pos
                    # Platform at Z can go up to Z+1
                    # Platform at Z+1 can go down to Z
                    platform_transitions[(px, py, wz)] = wz + 1  # Go up
                    platform_transitions[(px, py, wz + 1)] = wz  # Go down
        
        # BFS to find shortest path across z-levels
        from collections import deque
        queue = deque([(start, [start])])
        visited = {start}
        
        while queue:
            (cx, cy, cz), path = queue.popleft()
            
            # Regular 2D movement on current z-level
            for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                nx, ny, nz = cx + dx, cy + dy, cz
                
                if (nx, ny, nz) in visited:
                    continue
                
                # Can move to target or any walkable tile on this z-level
                is_goal = (nx, ny, nz) == goal
                is_walkable = grid.is_walkable(nx, ny, nz)
                
                if is_goal or is_walkable:
                    new_path = path + [(nx, ny, nz)]
                    if is_goal:
                        # Return path without start position
                        return new_path[1:]
                    visited.add((nx, ny, nz))
                    queue.append(((nx, ny, nz), new_path))
            
            # Z-level transition via fire escape platforms
            # Fire escapes allow vertical movement between adjacent Z-levels
            if (cx, cy, cz) in platform_transitions:
                other_z = platform_transitions[(cx, cy, cz)]
                if (cx, cy, other_z) not in visited:
                    other_tile = grid.get_tile(cx, cy, other_z)
                    # Can transition to platform on other Z (or any walkable tile)
                    if other_tile == "fire_escape_platform" or grid.is_walkable(cx, cy, other_z):
                        is_goal = (cx, cy, other_z) == goal
                        new_path = path + [(cx, cy, other_z)]
                        if is_goal:
                            return new_path[1:]
                        visited.add((cx, cy, other_z))
                        queue.append(((cx, cy, other_z), new_path))
        
        # No path found
        return []

    def _move_towards_job(self, grid: Grid) -> None:
        """Move along committed path toward job location."""

        if self.current_job is None:
            self.state = "idle"
            return

        target_x = self.current_job.x
        target_y = self.current_job.y
        target_z = self.current_job.z  # Use job's z-level

        # Already at target (including z-level)
        if self.x == target_x and self.y == target_y and self.z == target_z:
            self.state = "working"
            self.current_path = []
            self.stuck_timer = 0
            
            # Set resource node to IN_PROGRESS state when starting work
            if self.current_job and self.current_job.type == "gathering":
                set_node_state(target_x, target_y, NodeState.IN_PROGRESS)
            return
        
        # Movement speed control - only move every N ticks
        if self.move_cooldown > 0:
            self.move_cooldown -= 1
            return
        
        # Calculate path if we don't have one
        if not self.current_path:
            self.current_path = self._calculate_path(grid, target_x, target_y, target_z)
            self.stuck_timer = 0
            
            if not self.current_path:
                # No path exists - increment stuck timer
                self.stuck_timer += 1
                if self.stuck_timer > self.max_stuck_time:
                    # Give up on this job - reset node state if gathering
                    job = self.current_job
                    print(f"[Stuck] Colonist at ({self.x},{self.y},z={self.z}) gave up on {job.type} job at ({job.x},{job.y},z={job.z})")
                    if job.type == "gathering":
                        set_node_state(job.x, job.y, NodeState.IDLE)
                    job.assigned = False
                    self.current_job = None
                    self.state = "idle"
                    self.stuck_timer = 0
                return
        
        # Get next step in path (now includes z)
        next_pos = self.current_path[0]
        next_x, next_y, next_z = next_pos
        
        # Check if next step is still valid
        is_target = (next_x == target_x and next_y == target_y and next_z == target_z)
        is_walkable = grid.is_walkable(next_x, next_y, next_z)
        
        # Check if next tile is a closed door - open it
        if is_door(next_x, next_y, next_z) and not is_door_open(next_x, next_y, next_z):
            open_door(next_x, next_y, next_z)
            is_walkable = True  # Door is now open
        
        # Check if next tile is a closed window - open it (slower than doors)
        if is_window(next_x, next_y, next_z) and not is_window_open(next_x, next_y, next_z):
            open_window(next_x, next_y, next_z)
            is_walkable = True  # Window is now open
        
        if is_target or is_walkable:
            # Move to next position (including z-level change)
            self.x = next_x
            self.y = next_y
            self.z = next_z
            self.current_path.pop(0)
            
            # Windows have a movement speed penalty (climbing through)
            if is_window(next_x, next_y, next_z):
                self.move_cooldown = self.move_speed * 2  # Double delay for windows
            else:
                self.move_cooldown = self.move_speed
            self.stuck_timer = 0
        else:
            # Path blocked (wall built, door placed, etc.) - recalculate immediately
            self.current_path = []
            self.stuck_timer += 1
            
            # Add a small delay before retrying to avoid spinning
            self.move_cooldown = self.move_speed * 2
            
            if self.stuck_timer > self.max_stuck_time:
                # Give up on this job - reset node state if gathering
                job = self.current_job
                print(f"[Stuck] Colonist at ({self.x},{self.y},z={self.z}) path blocked to {job.type} job at ({job.x},{job.y},z={job.z})")
                if job.type == "gathering":
                    set_node_state(job.x, job.y, NodeState.IDLE)
                job.assigned = False
                self.current_job = None
                self.state = "idle"
                self.stuck_timer = 0

    def _work_on_job(self, grid: Grid) -> None:
        """Advance progress on the current job and complete it if finished."""

        if self.current_job is None:
            self.state = "idle"
            return

        job = self.current_job
        
        # Double-check construction has materials (shouldn't happen but safety)
        if job.type == "construction":
            # Check if waiting for stockpile items to be relocated
            if buildings.is_awaiting_stockpile_clear(job.x, job.y, job.z):
                # Can't work yet - wait for items to be moved
                job.assigned = False
                job.wait_timer = 60  # Don't reassign immediately
                self.current_job = None
                self.state = "idle"
                return
            if not has_required_materials(job.x, job.y, job.z):
                # Materials not delivered - release job and wait
                job.assigned = False
                job.wait_timer = 60  # Don't reassign immediately - wait for supply
                self.current_job = None
                self.state = "idle"
                return
        
        job.progress += 1
        
        # For gathering jobs, harvest resources incrementally
        if job.type == "gathering":
            harvest_tick(job.x, job.y, job.progress, job.required)

        if job.progress >= job.required:
            # Dispatch completion based on job type.
            if job.type == "construction":
                # Check what type of construction this was
                current_tile = grid.get_tile(job.x, job.y, job.z)
                if current_tile == "wall":
                    grid.set_tile(job.x, job.y, "finished_wall", z=job.z)
                elif current_tile == "wall_advanced":
                    grid.set_tile(job.x, job.y, "finished_wall_advanced", z=job.z)
                elif current_tile == "door":
                    # Door stays as "door" tile - state managed separately
                    pass
                elif current_tile == "floor":
                    grid.set_tile(job.x, job.y, "finished_floor", z=job.z)
                elif current_tile == "window":
                    grid.set_tile(job.x, job.y, "finished_window", z=job.z)
                    register_window(job.x, job.y, job.z)  # Register for open/close state
                elif current_tile == "fire_escape":
                    # Fire escape completion creates:
                    # 1. WindowTile at wall position (x, y, z) - passable wall
                    # 2. Platform at adjacent position on BOTH Z and Z+1
                    #    - Z: fire_escape_platform (current level balcony)
                    #    - Z+1: fire_escape_platform (upper level balcony, walkable)
                    
                    # Get platform position from fire escape data
                    platform_pos = buildings.get_fire_escape_platform(job.x, job.y, job.z)
                    if platform_pos:
                        px, py = platform_pos
                        
                        # Set window tile at wall position (passable wall)
                        grid.set_tile(job.x, job.y, "window_tile", z=job.z)
                        
                        # Set platform at adjacent position on current Z
                        grid.set_tile(px, py, "fire_escape_platform", z=job.z)
                        
                        # Set platform on Z+1 as well (balcony extends to upper level)
                        # This creates a proper floor tile colonists can stand on
                        grid.set_tile(px, py, "fire_escape_platform", z=job.z + 1)
                        
                        # Mark fire escape as complete
                        buildings.mark_fire_escape_complete(job.x, job.y, job.z)
                    else:
                        # Fallback if no platform data (shouldn't happen)
                        grid.set_tile(job.x, job.y, "window_tile", z=job.z)
                elif current_tile == "bridge":
                    grid.set_tile(job.x, job.y, "finished_bridge", z=job.z)
                elif current_tile == "salvagers_bench":
                    grid.set_tile(job.x, job.y, "finished_salvagers_bench", z=job.z)
                    # Register as workstation
                    buildings.register_workstation(job.x, job.y, job.z, "salvagers_bench")
                elif current_tile == "generator":
                    grid.set_tile(job.x, job.y, "finished_generator", z=job.z)
                    # Register as workstation
                    buildings.register_workstation(job.x, job.y, job.z, "generator")
                elif current_tile == "stove":
                    grid.set_tile(job.x, job.y, "finished_stove", z=job.z)
                    # Register as workstation
                    buildings.register_workstation(job.x, job.y, job.z, "stove")
                else:
                    grid.set_tile(job.x, job.y, "finished_building", z=job.z)
                buildings.remove_construction_site(job.x, job.y, job.z)
                remove_job(job)
                self.current_job = None
                self.state = "idle"
                # Trigger room re-detection after construction
                mark_rooms_dirty()
            elif job.type == "gathering":
                complete_gathering_job(grid, job)
                remove_job(job)
                self.current_job = None
                self.state = "idle"
            elif job.type == "haul":
                # Pickup phase complete - pick up the item and start hauling
                item = pickup_resource_item(job.x, job.y, job.z)
                if item is not None:
                    self.carrying = item
                    self.state = "hauling"
                    self.current_path = []  # Will recalculate path to destination
                else:
                    # Item was already picked up by someone else
                    remove_job(job)
                    self.current_job = None
                    self.state = "idle"
            elif job.type == "supply":
                # Supply job - pickup from stockpile for construction
                item = zones.remove_from_tile_storage(job.x, job.y, job.z, 1)
                if item is None and job.resource_type:
                    # Original tile empty - try to find another tile with this resource
                    alt_source = zones.find_stockpile_with_resource(job.resource_type, z=job.z)
                    if alt_source is not None:
                        # Redirect to new source
                        job.x, job.y, job.z = alt_source
                        self.current_path = []  # Recalculate path
                        self.state = "moving_to_job"
                        return
                
                if item is not None:
                    # Also remove from global stockpile count
                    spend_from_stockpile(item["type"], item.get("amount", 1))
                    self.carrying = item
                    self.state = "hauling"  # Reuse hauling state
                    self.current_path = []
                else:
                    # No resource available anywhere - cancel job, will retry later
                    mark_supply_job_completed(job.dest_x, job.dest_y, job.dest_z, job.resource_type)
                    remove_job(job)
                    self.current_job = None
                    self.state = "idle"
            elif job.type == "relocate":
                # Relocate job - move items from pending removal stockpile to another
                item = zones.remove_from_tile_storage(job.x, job.y, job.z, 1)
                if item is not None:
                    # Also remove from global stockpile count (will be re-added at destination)
                    spend_from_stockpile(item["type"], item.get("amount", 1))
                    self.carrying = item
                    self.state = "hauling"
                    self.current_path = []
                else:
                    # Tile is now empty - job complete
                    remove_job(job)
                    self.current_job = None
                    self.state = "idle"
            elif job.type == "salvage":
                # Salvage job complete - drop scrap and remove object
                from resources import complete_salvage, create_resource_item
                scrap_amount = complete_salvage(job.x, job.y)
                if scrap_amount > 0:
                    # Drop scrap on the tile (object is removed)
                    grid.set_tile(job.x, job.y, "empty", z=0)
                    create_resource_item(job.x, job.y, 0, "scrap", scrap_amount)
                    print(f"[Salvage] Recovered {scrap_amount} scrap at ({job.x},{job.y})")
                remove_job(job)
                self.current_job = None
                self.state = "idle"
            else:
                # Generic job completion
                remove_job(job)
                self.current_job = None
                self.state = "idle"

    def _haul_to_destination(self, grid: Grid) -> None:
        """Move towards haul destination and deliver item."""
        if self.current_job is None or self.carrying is None:
            # Something went wrong - clean up
            if self.current_job and self.current_job.type == "supply":
                mark_supply_job_completed(
                    self.current_job.dest_x, 
                    self.current_job.dest_y,
                    self.current_job.dest_z,
                    self.current_job.resource_type
                )
                remove_job(self.current_job)
            self.current_job = None
            self.state = "idle"
            self.carrying = None
            return
        
        job = self.current_job
        dest_x, dest_y = job.dest_x, job.dest_y
        dest_z = job.dest_z if job.dest_z is not None else 0
        
        if dest_x is None or dest_y is None:
            # No destination - drop item and abort
            if job.type == "supply":
                mark_supply_job_completed(dest_x, dest_y, dest_z, job.resource_type)
            self.carrying = None
            remove_job(job)
            self.current_job = None
            self.state = "idle"
            return
        
        # Check if we've arrived at destination
        if self.x == dest_x and self.y == dest_y and self.z == dest_z:
            resource_type = self.carrying.get("type", "")
            amount = self.carrying.get("amount", 1)
            
            if job.type == "supply":
                # Deliver to construction site (use dest_z for Z-level)
                deliver_material(dest_x, dest_y, resource_type, amount, z=dest_z)
                mark_supply_job_completed(dest_x, dest_y, dest_z, job.resource_type)
            elif job.type == "haul":
                # Deliver to stockpile
                if zones.is_stockpile_zone(dest_x, dest_y, dest_z):
                    add_to_stockpile(resource_type, amount)
                    zones.add_to_zone_storage(dest_x, dest_y, dest_z, resource_type, amount)
                    print(f"[Haul] Delivered {amount} {resource_type} to stockpile at ({dest_x},{dest_y})")
                else:
                    # Destination is no longer a stockpile - just add to global stockpile
                    add_to_stockpile(resource_type, amount)
                    print(f"[Haul] Delivered {amount} {resource_type} (stockpile zone removed)")
            
            # Job complete
            self.carrying = None
            remove_job(job)
            self.current_job = None
            self.state = "idle"
            return
        
        # Move towards destination
        if self.move_cooldown > 0:
            self.move_cooldown -= 1
            return
        
        # Calculate path if needed
        if not self.current_path:
            self.current_path = self._calculate_path(grid, dest_x, dest_y, dest_z)
            self.stuck_timer = 0
            if not self.current_path:
                self.stuck_timer += 1
                if self.stuck_timer > self.max_stuck_time:
                    # Can't reach destination - drop item and abort
                    self.carrying = None
                    remove_job(job)
                    self.current_job = None
                    self.state = "idle"
                return
        
        # Follow path (now includes z)
        next_pos = self.current_path[0]
        next_x, next_y, next_z = next_pos
        
        is_target = (next_x == dest_x and next_y == dest_y and next_z == dest_z)
        is_walkable = grid.is_walkable(next_x, next_y, next_z)
        
        if is_target or is_walkable:
            self.x = next_x
            self.y = next_y
            self.z = next_z
            self.current_path.pop(0)
            self.move_cooldown = self.move_speed
            self.stuck_timer = 0
        else:
            # Path blocked - recalculate
            self.current_path = []
            self.stuck_timer += 1
            self.move_cooldown = self.move_speed * 2  # Delay before retry
            
            if self.stuck_timer > self.max_stuck_time:
                # Can't reach destination - drop item and abort
                print(f"[Stuck] Colonist hauling path blocked, dropping item")
                self.carrying = None
                remove_job(job)
                self.current_job = None
                self.state = "idle"
                self.stuck_timer = 0

    def _unstick_if_needed(self, grid: Grid) -> bool:
        """Check if colonist is stuck in a non-walkable tile and teleport to nearest walkable.
        
        Returns True if colonist was stuck and teleported (triggers recovery).
        """
        if grid.is_walkable(self.x, self.y, self.z):
            return False  # Not stuck
        
        # Colonist is on a non-walkable tile - find nearest walkable
        # Search in expanding rings around current position
        for radius in range(1, max(GRID_W, GRID_H)):
            candidates = []
            for dx in range(-radius, radius + 1):
                for dy in range(-radius, radius + 1):
                    # Only check tiles at this radius (ring, not filled circle)
                    if abs(dx) != radius and abs(dy) != radius:
                        continue
                    nx, ny = self.x + dx, self.y + dy
                    if grid.in_bounds(nx, ny, self.z) and grid.is_walkable(nx, ny, self.z):
                        candidates.append((nx, ny))
            
            if candidates:
                # Pick random from candidates at this radius
                new_x, new_y = random.choice(candidates)
                print(f"[Unstick] Colonist teleported from ({self.x},{self.y}) to ({new_x},{new_y}) on Z={self.z}")
                self.x, self.y = new_x, new_y
                self._enter_recovery("teleported out of wall")
                return True
        
        # No walkable tile found on this Z-level - try Z=0 as fallback
        if self.z != 0:
            for radius in range(0, max(GRID_W, GRID_H)):
                for dx in range(-radius, radius + 1):
                    for dy in range(-radius, radius + 1):
                        nx, ny = self.x + dx, self.y + dy
                        if grid.in_bounds(nx, ny, 0) and grid.is_walkable(nx, ny, 0):
                            print(f"[Unstick] Colonist teleported to ground level ({nx},{ny}) from Z={self.z}")
                            self.x, self.y, self.z = nx, ny, 0
                            self._enter_recovery("teleported to ground level")
                            return True
        
        return False

    # --- Interruption and Recovery -------------------------------------------

    def _interrupt_current_job(self, reason: str = "") -> None:
        """Cancel current job and enter recovery state.
        
        Called when:
        - Path becomes blocked and can't be recalculated
        - Job target becomes unreachable
        - Colonist gets stuck and teleported
        """
        job = self.current_job
        if job is not None:
            # Release any reserved resources
            if job.type == "gathering":
                set_node_state(job.x, job.y, NodeState.IDLE)
            elif job.type == "crafting":
                buildings.release_workstation(job.x, job.y, job.z)
            
            # Unassign job so others can take it
            job.assigned = False
            self.current_job = None
            
            reason_str = f" ({reason})" if reason else ""
            print(f"[Interrupt] Job {job.type} at ({job.x},{job.y}) interrupted{reason_str}")
        
        # Drop carried items
        if self.carrying is not None:
            print(f"[Interrupt] Dropped {self.carrying.get('type', 'item')}")
            self.carrying = None
        
        # Clear path and enter recovery
        self.current_path = []
        self._enter_recovery(reason)

    def _enter_recovery(self, reason: str = "") -> None:
        """Enter recovery state - brief pause before returning to idle."""
        if self.state != "recovery":
            reason_str = f" ({reason})" if reason else ""
            print(f"[Recovery] Colonist entering recovery{reason_str}")
        self.state = "recovery"
        self.recovery_timer = self.recovery_duration
        self.current_path = []
        self.stuck_timer = 0

    def _update_recovery(self) -> None:
        """Update recovery state - count down and return to idle."""
        if self.recovery_timer > 0:
            self.recovery_timer -= 1
        else:
            self.state = "idle"

    def _check_job_still_valid(self, grid: Grid) -> bool:
        """Check if current job is still reachable and valid.
        
        Returns False if job should be interrupted.
        Only checks job target validity, NOT path validity (that's separate).
        """
        job = self.current_job
        if job is None:
            return True  # No job to validate
        
        # For construction jobs, check if the construction site still exists
        if job.type == "construction":
            site = buildings.get_construction_site(job.x, job.y, job.z)
            if site is None:
                # Construction was completed or cancelled
                return False
        
        # For gathering jobs, check if node still exists
        if job.type == "gathering":
            from resources import get_node_at
            node = get_node_at(job.x, job.y)
            if node is None or node.get("amount", 0) <= 0:
                return False
        
        return True

    def _check_path_still_valid(self, grid: Grid) -> bool:
        """Check if current path is still walkable.
        
        Returns False if any tile in the path is now blocked.
        """
        if not self.current_path:
            return True  # No path to check
        
        for px, py, pz in self.current_path:
            # Skip the final destination (might be a workstation or resource node)
            if self.current_path.index((px, py, pz)) == len(self.current_path) - 1:
                continue
            
            if not grid.is_walkable(px, py, pz):
                # Check if it's a door/window we can open
                if is_door(px, py, pz) or is_window(px, py, pz):
                    continue
                return False
        
        return True

    # --- Crafting behavior ---------------------------------------------------

    def _crafting_fetch_materials(self, grid: Grid) -> None:
        """Fetch materials from stockpile for crafting job."""
        if self.current_job is None:
            self.state = "idle"
            return
        
        job = self.current_job
        
        # Get recipe for workstation
        recipe = buildings.get_workstation_recipe(job.x, job.y, job.z)
        if recipe is None:
            # Invalid workstation - cancel job
            buildings.release_workstation(job.x, job.y, job.z)
            buildings.mark_crafting_job_completed(job.x, job.y, job.z)
            remove_job(job)
            self.current_job = None
            self.state = "idle"
            return
        
        # If already carrying something, deliver it to workstation
        if self.carrying is not None:
            # Move towards workstation
            if self.move_cooldown > 0:
                self.move_cooldown -= 1
                return
            
            # Check if at workstation (adjacent is fine)
            at_bench = (abs(self.x - job.x) <= 1 and abs(self.y - job.y) <= 1 and self.z == job.z)
            if at_bench:
                # Deliver to workstation
                res_type = self.carrying.get("type", "")
                amount = self.carrying.get("amount", 1)
                buildings.add_input_to_workstation(job.x, job.y, job.z, res_type, amount)
                self.carrying = None
                
                # Check if workstation has all inputs
                if buildings.workstation_has_inputs(job.x, job.y, job.z):
                    # Start working
                    ws = buildings.get_workstation(job.x, job.y, job.z)
                    if ws:
                        ws["working"] = True
                        ws["progress"] = 0
                    self.state = "crafting_work"
                    self.current_path = []
                return
            
            # Move towards workstation
            if not self.current_path:
                self.current_path = self._calculate_path(grid, job.x, job.y, job.z)
                if not self.current_path:
                    # Can't reach - try adjacent tile
                    for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
                        adj_x, adj_y = job.x + dx, job.y + dy
                        if grid.is_walkable(adj_x, adj_y, job.z):
                            self.current_path = self._calculate_path(grid, adj_x, adj_y, job.z)
                            if self.current_path:
                                break
            
            if self.current_path:
                next_pos = self.current_path[0]
                if grid.is_walkable(next_pos[0], next_pos[1], next_pos[2]):
                    self.x, self.y, self.z = next_pos
                    self.current_path.pop(0)
                    self.move_cooldown = 3
            return
        
        # Need to fetch materials
        inputs_needed = recipe.get("input", {})
        ws = buildings.get_workstation(job.x, job.y, job.z)
        inputs_have = ws.get("input_items", {}) if ws else {}
        
        # Find what we still need
        for res_type, amount_needed in inputs_needed.items():
            have = inputs_have.get(res_type, 0)
            if have < amount_needed:
                # Find stockpile with this resource
                source = zones.find_stockpile_with_resource(res_type, z=job.z)
                if source is None:
                    # No resource available - wait
                    return
                
                source_x, source_y, source_z = source
                
                # Move to stockpile
                if self.move_cooldown > 0:
                    self.move_cooldown -= 1
                    return
                
                # Check if at stockpile
                if self.x == source_x and self.y == source_y and self.z == source_z:
                    # Pick up resource
                    item = zones.remove_from_tile_storage(source_x, source_y, source_z, 1)
                    if item:
                        self.carrying = {"type": item["type"], "amount": item["amount"]}
                        spend_from_stockpile(item["type"], item["amount"])
                        self.current_path = []
                    return
                
                # Move towards stockpile
                if not self.current_path or self.current_path[-1] != (source_x, source_y, source_z):
                    self.current_path = self._calculate_path(grid, source_x, source_y, source_z)
                
                if self.current_path:
                    next_pos = self.current_path[0]
                    if grid.is_walkable(next_pos[0], next_pos[1], next_pos[2]):
                        self.x, self.y, self.z = next_pos
                        self.current_path.pop(0)
                        self.move_cooldown = 3
                return
        
        # All inputs delivered - start working
        if ws:
            ws["working"] = True
            ws["progress"] = 0
        self.state = "crafting_work"

    def _crafting_work_at_bench(self, grid: Grid) -> None:
        """Work at workstation to produce output."""
        if self.current_job is None:
            self.state = "idle"
            return
        
        job = self.current_job
        ws = buildings.get_workstation(job.x, job.y, job.z)
        
        if ws is None:
            # Workstation gone - cancel
            buildings.mark_crafting_job_completed(job.x, job.y, job.z)
            remove_job(job)
            self.current_job = None
            self.state = "idle"
            return
        
        # Move adjacent to workstation if not already
        at_bench = (abs(self.x - job.x) <= 1 and abs(self.y - job.y) <= 1 and self.z == job.z)
        if not at_bench:
            if self.move_cooldown > 0:
                self.move_cooldown -= 1
                return
            
            if not self.current_path:
                # Find adjacent walkable tile
                for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
                    adj_x, adj_y = job.x + dx, job.y + dy
                    if grid.is_walkable(adj_x, adj_y, job.z):
                        self.current_path = self._calculate_path(grid, adj_x, adj_y, job.z)
                        if self.current_path:
                            break
            
            if self.current_path:
                next_pos = self.current_path[0]
                if grid.is_walkable(next_pos[0], next_pos[1], next_pos[2]):
                    self.x, self.y, self.z = next_pos
                    self.current_path.pop(0)
                    self.move_cooldown = 3
            return
        
        # Work on crafting
        ws["progress"] = ws.get("progress", 0) + 1
        
        recipe = buildings.get_workstation_recipe(job.x, job.y, job.z)
        if recipe is None:
            return
        
        work_time = recipe.get("work_time", 60)
        
        if ws["progress"] >= work_time:
            # Crafting complete - consume inputs and produce output
            buildings.consume_workstation_inputs(job.x, job.y, job.z)
            
            # Produce output as dropped item
            outputs = recipe.get("output", {})
            from resources import create_resource_item
            for res_type, amount in outputs.items():
                # Drop output adjacent to workstation
                for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
                    drop_x, drop_y = job.x + dx, job.y + dy
                    if grid.is_walkable(drop_x, drop_y, job.z):
                        create_resource_item(drop_x, drop_y, job.z, res_type, amount)
                        print(f"[Crafting] Produced {amount} {res_type} at ({drop_x},{drop_y})")
                        break
            
            # Complete job
            buildings.release_workstation(job.x, job.y, job.z)
            buildings.mark_crafting_job_completed(job.x, job.y, job.z)
            remove_job(job)
            self.current_job = None
            self.state = "idle"

    def _update_hunger(self, grid: Grid) -> None:
        """Update hunger and handle eating/starvation."""
        if self.is_dead:
            return
        
        # Increase hunger over time
        self.hunger = min(100.0, self.hunger + self.hunger_rate)
        
        # Starving - take damage
        if self.hunger >= 100.0:
            self.health -= self.starving_damage
            if self.health <= 0:
                self.health = 0
                self.is_dead = True
                print(f"[Death] Colonist at ({self.x},{self.y}) died of starvation!")
                return
        
        # Hungry (>70) and idle - try to find food
        if self.hunger > 70 and self.state == "idle" and self.current_job is None:
            self._try_eat_food(grid)
    
    def _try_eat_food(self, grid: Grid) -> None:
        """Try to find and eat a cooked meal."""
        import zones
        
        # Look for cooked_meal in stockpiles (check all Z levels)
        meal_tile = zones.find_stockpile_with_resource("cooked_meal", z=None)
        if meal_tile is None:
            # No food available anywhere
            return
        
        mx, my, mz = meal_tile
        
        # Check if we're adjacent or on the food tile
        dist = abs(self.x - mx) + abs(self.y - my)
        if dist <= 1 and self.z == mz:
            # Eat the food!
            removed = zones.remove_from_tile_storage(mx, my, mz, 1)
            if removed and removed.get("type") == "cooked_meal":
                self.hunger = max(0, self.hunger - 70)
                print(f"[Eat] Colonist ate a meal at ({mx},{my}), hunger now {self.hunger:.0f}")
        else:
            # Need to walk to food - enter eating state
            self.current_path = self._calculate_path(grid, mx, my, mz)
            if self.current_path:
                self.state = "eating"
                self._eating_target = (mx, my, mz)
                print(f"[Hunger] Colonist going to eat at ({mx},{my},{mz})")
    
    def _move_to_eat(self, grid: Grid) -> None:
        """Move towards food and eat when arrived."""
        import zones
        from buildings import is_door, is_door_open, open_door, is_window, is_window_open, open_window
        
        if not hasattr(self, '_eating_target') or self._eating_target is None:
            self.state = "idle"
            return
        
        mx, my, mz = self._eating_target
        
        # Check if we've arrived (adjacent or on tile)
        dist = abs(self.x - mx) + abs(self.y - my)
        if dist <= 1 and self.z == mz:
            # Try to eat
            removed = zones.remove_from_tile_storage(mx, my, mz, 1)
            if removed and removed.get("type") == "cooked_meal":
                self.hunger = max(0, self.hunger - 70)
                print(f"[Eat] Colonist ate a meal at ({mx},{my}), hunger now {self.hunger:.0f}")
            else:
                print(f"[Eat] Food was taken before colonist arrived")
            self._eating_target = None
            self.state = "idle"
            return
        
        # Movement cooldown
        if self.move_cooldown > 0:
            self.move_cooldown -= 1
            return
        
        # Need path?
        if not self.current_path:
            self.current_path = self._calculate_path(grid, mx, my, mz)
            if not self.current_path:
                # Can't reach food
                print(f"[Eat] Can't reach food at ({mx},{my},{mz})")
                self._eating_target = None
                self.state = "idle"
                return
        
        # Follow path
        next_x, next_y, next_z = self.current_path[0]
        is_walkable = grid.is_walkable(next_x, next_y, next_z)
        
        # Handle doors/windows
        if is_door(next_x, next_y, next_z) and not is_door_open(next_x, next_y, next_z):
            open_door(next_x, next_y, next_z)
            is_walkable = True
        if is_window(next_x, next_y, next_z) and not is_window_open(next_x, next_y, next_z):
            open_window(next_x, next_y, next_z)
            is_walkable = True
        
        if is_walkable or (next_x == mx and next_y == my and next_z == mz):
            self.x = next_x
            self.y = next_y
            self.z = next_z
            self.current_path.pop(0)
            self.move_cooldown = self.move_speed
        else:
            # Path blocked - recalculate
            self.current_path = []

    def update(self, grid: Grid) -> None:
        """Advance colonist behavior for one simulation tick."""
        
        # Skip dead colonists
        if self.is_dead:
            return
        
        # Update hunger system
        self._update_hunger(grid)
        
        # Failsafe: unstick colonist if they're in a wall
        # If teleported, we're now in recovery state
        if self._unstick_if_needed(grid):
            self._interrupt_current_job("stuck in wall")
            return
        
        # Recovery state - wait before returning to idle
        if self.state == "recovery":
            self._update_recovery()
            return
        
        # Check if current job is still valid (target gone, etc.)
        if self.state not in ("idle", "eating", "recovery"):
            if not self._check_job_still_valid(grid):
                self._interrupt_current_job("job no longer valid")
                return
            
            # Check if path is still walkable (only if we have a path)
            if self.current_path and not self._check_path_still_valid(grid):
                # Path blocked - try to recalculate
                if self.current_job:
                    new_path = self._calculate_path(grid, self.current_job.x, self.current_job.y, self.current_job.z)
                    if new_path:
                        self.current_path = new_path
                    else:
                        # Can't find new path - interrupt
                        self._interrupt_current_job("path blocked")
                        return

        if self.state == "idle":
            self._try_take_job()
            if self.state == "idle":
                self._maybe_wander_when_idle(grid)
        elif self.state == "moving_to_job":
            self._move_towards_job(grid)
        elif self.state == "working":
            self._work_on_job(grid)
        elif self.state == "hauling":
            self._haul_to_destination(grid)
        elif self.state == "crafting_fetch":
            self._crafting_fetch_materials(grid)
        elif self.state == "crafting_work":
            self._crafting_work_at_bench(grid)
        elif self.state == "eating":
            self._move_to_eat(grid)
        else:
            print(f"ERROR: Colonist in unknown state: {self.state}")

    def draw(self, surface: pygame.Surface, ether_mode: bool = False) -> None:
        """Render the colonist as a circle on the grid."""

        cx = self.x * TILE_SIZE + TILE_SIZE // 2
        cy = self.y * TILE_SIZE + TILE_SIZE // 2

        color = COLOR_COLONIST_ETHER if ether_mode else self.color
        pygame.draw.circle(surface, color, (cx, cy), TILE_SIZE // 3)
        
        # Draw carrying indicator if hauling
        if self.carrying is not None:
            # Small colored square above colonist
            carry_type = self.carrying.get("type", "")
            if carry_type == "wood":
                carry_color = (139, 90, 43)
            elif carry_type == "scrap":
                carry_color = (120, 120, 120)
            elif carry_type == "metal":
                carry_color = (180, 180, 200)
            elif carry_type == "mineral":
                carry_color = (80, 200, 200)
            else:
                carry_color = (200, 200, 200)
            
            carry_rect = pygame.Rect(cx - 4, cy - TILE_SIZE // 3 - 6, 8, 6)
            pygame.draw.rect(surface, carry_color, carry_rect)
            pygame.draw.rect(surface, (255, 255, 255), carry_rect, 1)


# --- Module-level helpers -----------------------------------------------------


def create_colonists(count: int) -> list[Colonist]:
    """Construct an initial list of colonists in random positions."""

    colonists: list[Colonist] = []
    for _ in range(count):
        colonists.append(
            Colonist(
                x=random.randint(0, GRID_W - 1),
                y=random.randint(0, GRID_H - 1),
            )
        )
    return colonists


def update_colonists(colonists: Iterable[Colonist], grid: Grid) -> None:
    """Advance all colonists one simulation step."""

    for c in colonists:
        c.update(grid)


def draw_colonists(
    surface: pygame.Surface, colonists: Iterable[Colonist], ether_mode: bool = False, current_z: int = 0
) -> None:
    """Draw all colonists to the given surface.
    
    Only draws colonists that are on the current z-level.
    """
    for c in colonists:
        if c.z == current_z:
            c.draw(surface, ether_mode=ether_mode)
