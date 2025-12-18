"""Dynamic job pressure system - adjusts job urgency based on colony state.

This module provides lightweight functions to calculate job pressure dynamically
based on real-time colony conditions like food shortage, enemy proximity, etc.
"""

def calculate_cooking_pressure() -> int:
    """Calculate pressure for cooking jobs based on food availability.
    
    Returns:
        int: 1-10 pressure (1=plenty of food, 10=critical shortage)
    """
    from zones import get_total_stored
    
    # Count total food in stockpiles
    total_food = get_total_stored("food")
    
    # Debug output (can be removed later)
    # print(f"[Job Pressure] Food in stockpiles: {total_food}")
    
    # Pressure thresholds
    if total_food >= 50:
        return 2  # Plenty of food, low priority
    elif total_food >= 30:
        return 4  # Getting low, moderate priority
    elif total_food >= 15:
        return 6  # Low food, elevated priority
    elif total_food >= 5:
        return 8  # Critical shortage, high priority
    else:
        return 10  # Starvation imminent, maximum priority


def calculate_combat_pressure(colonists: list, x: int, y: int, z: int) -> int:
    """Calculate pressure for combat jobs based on enemy proximity.
    
    Args:
        colonists: List of all colonists (to check for nearby hostiles)
        x, y, z: Location of the combat job
    
    Returns:
        int: 1-10 pressure (1=distant threat, 10=immediate danger)
    """
    # Find nearest hostile
    min_distance = float('inf')
    
    for colonist in colonists:
        if not colonist.is_hostile or colonist.is_dead:
            continue
        if colonist.z != z:
            continue
        
        dx = abs(colonist.x - x)
        dy = abs(colonist.y - y)
        distance = max(dx, dy)  # Chebyshev distance
        
        if distance < min_distance:
            min_distance = distance
    
    # No hostiles found
    if min_distance == float('inf'):
        return 1
    
    # Pressure based on distance
    if min_distance <= 3:
        return 10  # Immediate danger
    elif min_distance <= 6:
        return 8   # Very close
    elif min_distance <= 10:
        return 6   # Close
    elif min_distance <= 15:
        return 4   # Nearby
    else:
        return 2   # Distant


def calculate_hauling_pressure(resource_type: str) -> int:
    """Calculate pressure for hauling jobs based on resource need.
    
    Args:
        resource_type: Type of resource being hauled
    
    Returns:
        int: 1-10 pressure (1=not urgent, 10=critically needed)
    """
    # For now, keep hauling at baseline
    # Future: Could check if construction jobs are waiting for this resource
    return 1


def get_job_pressure(job_type: str, **kwargs) -> int:
    """Get dynamic pressure for a job based on its type and colony state.
    
    Args:
        job_type: Type of job (cooking, combat, haul, etc.)
        **kwargs: Additional context (colonists, x, y, z, resource_type, etc.)
    
    Returns:
        int: 1-10 pressure value
    """
    if job_type == "cooking":
        return calculate_cooking_pressure()
    
    elif job_type == "combat":
        colonists = kwargs.get("colonists", [])
        x = kwargs.get("x", 0)
        y = kwargs.get("y", 0)
        z = kwargs.get("z", 0)
        return calculate_combat_pressure(colonists, x, y, z)
    
    elif job_type == "haul" or job_type == "supply":
        resource_type = kwargs.get("resource_type", "")
        return calculate_hauling_pressure(resource_type)
    
    # Default pressure for other job types
    return 1
