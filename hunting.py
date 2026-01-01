"""Hunting system for animals.

Handles hunt job creation, colonist hunting behavior, and animal fleeing.
"""

from typing import Optional, List
import jobs as jobs_module
from animals import get_huntable_animals, get_animal, unmark_for_hunt, kill_animal


def spawn_hunt_jobs(colonists: List) -> int:
    """Check for huntable animals and create hunt jobs.
    
    Called periodically from main game loop.
    
    Args:
        colonists: List of colonists
    
    Returns:
        Number of hunt jobs created
    """
    huntable = get_huntable_animals()
    if not huntable:
        return 0
    
    print(f"[Hunting] Found {len(huntable)} huntable animals")
    
    jobs_created = 0
    
    for animal in huntable:
        # Create hunt job - any available colonist can take it
        job = jobs_module.add_job(
            "hunt",
            animal.x,
            animal.y,
            required=1,  # Instant job, just need to reach and attack
            z=animal.z,
            category="hunt",
            pressure=8.0,  # High priority - food is important
        )
        
        # Store animal UID in job metadata
        job.animal_uid = animal.uid
        
        jobs_created += 1
        print(f"[Hunting] Created hunt job for {animal.species}_{animal.variant} at ({animal.x}, {animal.y}, z={animal.z})")
    
    return jobs_created


def process_hunt_job(colonist, animal, grid, game_tick: int) -> bool:
    """Process colonist hunting an animal.
    
    Args:
        colonist: Colonist doing the hunting
        animal: Animal being hunted
        grid: Game grid
        game_tick: Current game tick
    
    Returns:
        True if hunt completed (animal killed), False if still hunting
    """
    # Check if animal is still alive
    if not animal.is_alive():
        return True
    
    # Calculate distance to animal
    dx = abs(colonist.x - animal.x)
    dy = abs(colonist.y - animal.y)
    dist = max(dx, dy)
    
    # If within attack range (1 tile), attack
    if dist <= 1:
        # Use combat system to attack animal
        from combat import perform_attack
        
        # Colonist attacks animal
        hit_success = perform_attack(colonist, None, grid, game_tick, target_animal=animal)
        
        if hit_success and not animal.is_alive():
            # Animal died - create corpse
            kill_animal(animal, grid, game_tick)
            print(f"[Hunting] {colonist.name} killed {animal.species}_{animal.variant}")
            return True
        
        return False
    
    # Not in range - update target position to animal's current location
    colonist.target_x = animal.x
    colonist.target_y = animal.y
    
    return False


def cancel_hunt_job(animal_uid: int) -> None:
    """Cancel hunt job for an animal.
    
    Args:
        animal_uid: UID of animal to cancel hunt for
    """
    animal = get_animal(animal_uid)
    if animal:
        unmark_for_hunt(animal)
        print(f"[Hunting] Cancelled hunt for {animal.species}_{animal.variant}")
