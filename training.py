"""
Training system for Fractured City.

Spawns training jobs at barracks during morning drill hours.
Fighters prioritize training to improve combat skills.
"""

from jobs import add_job, JOB_QUEUE
from typing import List


# Global tracking for training job spawning
_last_spawn_tick: int = 0
_spawn_interval: int = 300  # Check every 5 seconds


def spawn_training_jobs(colonists: List, grid, game_tick: int) -> None:
    """Spawn training jobs at barracks during morning drill hours.
    
    Creates training jobs for fighters to improve combat skills.
    
    Args:
        colonists: List of all colonists
        grid: Game grid for walkability checks
        game_tick: Current game tick
    """
    global _last_spawn_tick
    
    # Only spawn periodically
    if game_tick - _last_spawn_tick < _spawn_interval:
        return
    
    _last_spawn_tick = game_tick
    
    # Check if we're in morning drill hours (6am-8am)
    from time_system import get_game_time
    hour = get_game_time().hour
    
    is_drill_time = 6 <= hour < 8
    
    if not is_drill_time:
        return
    
    # Get all barracks locations
    from buildings import get_all_workstations
    all_workstations = get_all_workstations()
    barracks_list = [(coord, ws) for coord, ws in all_workstations.items() if ws.get("type") == "barracks"]
    
    if not barracks_list:
        return  # No barracks built yet
    
    # Count existing training jobs
    existing_training = sum(1 for j in JOB_QUEUE if j.category == "training" and not j.assigned)
    
    # Count fighters (colonists with fighter role)
    fighter_count = sum(1 for c in colonists if getattr(c, 'role', 'generalist') == "fighter")
    
    # Target: 1 training job per fighter (so each fighter can train)
    # But cap at number of barracks (1 job per barracks)
    target_jobs = min(fighter_count, len(barracks_list))
    
    if existing_training >= target_jobs:
        return  # Already have enough
    
    # Spawn training jobs at barracks
    jobs_to_spawn = target_jobs - existing_training
    
    for i in range(jobs_to_spawn):
        if i >= len(barracks_list):
            break
        
        coord, barracks = barracks_list[i]
        bx, by, bz = coord
        
        # Find a walkable tile adjacent to barracks (not ON the barracks)
        # Barracks are non-walkable, so colonists need to train next to them
        adjacent_tiles = [
            (bx + 1, by, bz),
            (bx - 1, by, bz),
            (bx, by + 1, bz),
            (bx, by - 1, bz),
        ]
        
        training_location = None
        for tx, ty, tz in adjacent_tiles:
            if grid.is_walkable(tx, ty, tz):
                training_location = (tx, ty, tz)
                break
        
        # Skip if no valid location found
        if training_location is None:
            continue
        
        x, y, z = training_location
        
        # Create training job at walkable location adjacent to barracks
        # Moderate work requirement (training session takes ~2-3 seconds)
        # Low pressure (not urgent, but higher than recreation)
        add_job(
            job_type="training",
            x=x,
            y=y,
            z=z,
            required=100,  # ~2 seconds at normal speed
            category="training",
            pressure=3,  # Higher than recreation (2), but not urgent
        )


def update_training_schedule(colonists: List) -> None:
    """Update colonist schedules to include morning drills.
    
    Fighters get dedicated training time in the morning.
    
    Args:
        colonists: List of all colonists
    """
    # This function can be called on game start to set up schedules
    # For now, we'll use a simple schedule for all colonists:
    # 6am-8am: Training time (fighters train, others can do light work)
    # 8am-6pm: Work hours
    # 6pm-10pm: Recreation
    # 10pm-6am: Sleep
    
    for colonist in colonists:
        # Update schedule to include training window
        # Fighters will prioritize training jobs during 6-8am
        # Non-fighters will treat it as normal work time
        colonist.schedule = {
            "training": (6, 8),      # 6am-8am: morning drills
            "work": (8, 18),         # 8am-6pm: work hours
            "recreation": (18, 22),  # 6pm-10pm: recreation time
            "sleep": (22, 6),        # 10pm-6am: sleep hours (wraps midnight)
        }
