"""Room effects helper functions.

Provides utility functions to get room bonuses for colonists based on their location.
"""

from typing import Optional, Tuple
import room_system


def get_room_work_bonus(x: int, y: int, z: int, job_type: str) -> float:
    """Get work speed bonus from room at location.
    
    Args:
        x, y, z: Colonist location
        job_type: Type of job ("crafting", "cook", "build", etc.)
    
    Returns:
        Multiplier bonus (e.g., 0.15 for +15% speed)
    """
    room_id = room_system.get_room_at(x, y, z)
    if room_id is None:
        return 0.0
    
    room_data = room_system.get_room_data(room_id)
    if not room_data:
        return 0.0
    
    effects = room_data.get("effects", {})
    
    # Map job types to room effect keys
    if job_type == "crafting":
        return effects.get("craft_speed_mult", 0.0)
    elif job_type == "cook":
        return effects.get("cooking_speed_mult", 0.0)
    
    return 0.0


def get_room_healing_bonus(x: int, y: int, z: int) -> float:
    """Get healing rate bonus from room at location.
    
    Returns:
        Multiplier bonus (e.g., 0.5 for +50% healing)
    """
    room_id = room_system.get_room_at(x, y, z)
    if room_id is None:
        return 0.0
    
    room_data = room_system.get_room_data(room_id)
    if not room_data:
        return 0.0
    
    effects = room_data.get("effects", {})
    return effects.get("healing_rate_mult", 0.0)


def get_room_sleep_bonus(x: int, y: int, z: int) -> Tuple[float, float]:
    """Get sleep quality and mood bonus from room at location.
    
    Returns:
        (sleep_quality_mult, mood_bonus) tuple
    """
    room_id = room_system.get_room_at(x, y, z)
    if room_id is None:
        return (0.0, 0.0)
    
    room_data = room_system.get_room_data(room_id)
    if not room_data:
        return (0.0, 0.0)
    
    effects = room_data.get("effects", {})
    sleep_mult = effects.get("sleep_quality_mult", 0.0)
    mood = effects.get("mood_bonus", 0.0)
    
    return (sleep_mult, mood)


def get_room_mood_bonus(x: int, y: int, z: int) -> float:
    """Get mood bonus from room at location.
    
    Returns:
        Mood bonus value (e.g., 5.0 for +5 mood)
    """
    room_id = room_system.get_room_at(x, y, z)
    if room_id is None:
        return 0.0
    
    room_data = room_system.get_room_data(room_id)
    if not room_data:
        return 0.0
    
    effects = room_data.get("effects", {})
    return effects.get("mood_bonus", 0.0)


def get_room_info(x: int, y: int, z: int) -> Optional[dict]:
    """Get full room info at location for debugging/UI.
    
    Returns dict with:
        - room_id
        - room_type
        - quality
        - effects
        - owner (if assigned)
    """
    room_id = room_system.get_room_at(x, y, z)
    if room_id is None:
        return None
    
    room_data = room_system.get_room_data(room_id)
    if not room_data:
        return None
    
    return {
        "room_id": room_id,
        "room_type": room_data.get("type", "Unknown"),
        "quality": room_data.get("quality", 0),
        "effects": room_data.get("effects", {}),
        "owner": room_data.get("owner"),
    }
