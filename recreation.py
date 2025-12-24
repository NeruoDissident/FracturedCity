"""
Recreation system for Fractured City.

Spawns recreation jobs during recreation hours so colonists can socialize and relax.
Recreation prevents burnout and provides mood bonuses.
"""

from jobs import add_job, JOB_QUEUE
from typing import List, Tuple


# Global tracking for recreation job spawning
_last_spawn_tick: int = 0
_spawn_interval: int = 300  # Spawn recreation jobs every 5 seconds


def spawn_recreation_jobs(colonists: List, grid, game_tick: int) -> None:
    """Spawn recreation jobs for colonists during recreation hours.
    
    Creates social and solo recreation activities at various locations.
    
    Args:
        colonists: List of all colonists
        grid: Game grid
        game_tick: Current game tick
    """
    global _last_spawn_tick
    
    # Only spawn periodically
    if game_tick - _last_spawn_tick < _spawn_interval:
        return
    
    _last_spawn_tick = game_tick
    
    # Check if any colonist is in recreation time
    from time_system import get_game_time
    hour = get_game_time().hour
    
    # Recreation hours are typically 18-22 (6pm-10pm)
    # Check if we're in recreation time for default schedule
    is_recreation_time = 18 <= hour < 22
    
    if not is_recreation_time:
        return
    
    # Count existing recreation jobs
    existing_recreation = sum(1 for j in JOB_QUEUE if j.category == "recreation" and not j.assigned)
    
    # Target: 1 recreation job per 2 colonists (so they can pair up or do solo activities)
    target_jobs = max(1, len(colonists) // 2)
    
    if existing_recreation >= target_jobs:
        return  # Already have enough
    
    # Spawn recreation jobs in recreation rooms if available
    import random
    from room_system import get_all_rooms
    
    jobs_to_spawn = target_jobs - existing_recreation
    
    # Find all recreation venues (Social Venues and Dining Halls)
    rec_room_tiles = []
    all_rooms = get_all_rooms()
    for room_id, room_data in all_rooms.items():
        room_type = room_data.get("type")
        # Social Venues (bars, clubs, etc.) and Dining Halls count as recreation spaces
        if room_type in ("Social Venue", "Dining Hall"):
            rec_room_tiles.extend(room_data.get("tiles", []))
    
    for _ in range(jobs_to_spawn):
        if not colonists:
            break
        
        # Try to spawn in recreation room first
        if rec_room_tiles:
            # Pick random tile from recreation rooms
            tile = random.choice(rec_room_tiles)
            x, y = tile
            z = 0  # Assume ground level for now
        else:
            # Fallback: spawn near colonists if no rec rooms
            anchor = random.choice(colonists)
            x = anchor.x + random.randint(-5, 5)
            y = anchor.y + random.randint(-5, 5)
            z = anchor.z
        
        # Clamp to grid bounds
        x = max(0, min(grid.width - 1, x))
        y = max(0, min(grid.height - 1, y))
        
        # Check if tile is walkable
        if not grid.is_walkable(x, y, z):
            continue
        
        # Randomly choose social or solo recreation
        job_type = random.choice(["recreation_social", "recreation_solo"])
        
        # Create recreation job
        # Low work requirement (quick activity)
        # Pressure=2 (personal time, but can be interrupted by urgent colony needs)
        # Colonists with low needs_of_the_many (1-4) won't be interrupted
        # Colonists with high needs_of_the_many (7-10) will drop recreation for urgent work
        add_job(
            job_type=job_type,
            x=x,
            y=y,
            z=z,
            required=50,  # Quick activity (~1 second)
            category="recreation",
            pressure=2,  # Personal time - only urgent work (5+) can interrupt collectivists
        )


def complete_recreation_job(colonist, job, game_tick: int) -> None:
    """Handle completion of a recreation job.
    
    Gives mood bonus and generates recreation thoughts.
    
    Args:
        colonist: The colonist who completed the job
        job: The recreation job
        game_tick: Current game tick
    """
    # Give mood bonus
    mood_bonus = 0.5
    
    if job.type == "recreation_social":
        # Social recreation - bigger mood bonus
        colonist.add_thought(
            "recreation",
            "Nice to take a break and chat.",
            mood_bonus,
            game_tick=game_tick
        )
    else:  # recreation_solo
        # Solo recreation - smaller but still positive
        colonist.add_thought(
            "recreation",
            "Some quiet time to myself.",
            mood_bonus * 0.7,
            game_tick=game_tick
        )
