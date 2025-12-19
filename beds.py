"""
Bed and sleep system for Fractured City.

Beds are furniture that colonists can be assigned to.
- Up to 2 colonists per bed (sharing)
- Romantic partners sharing = comfort bonus
- Enemies sharing = stress penalty
- No bed = stress from sleeping on ground

Sleep restores health and reduces tiredness.
"""

from typing import Optional, List, Tuple, Dict, TYPE_CHECKING
import random

if TYPE_CHECKING:
    from colonist import Colonist

# =============================================================================
# BED REGISTRY
# =============================================================================

# {(x, y, z): {"assigned": [colonist_id, ...], "quality": int}}
_beds: Dict[Tuple[int, int, int], dict] = {}


def register_bed(x: int, y: int, z: int, quality: int = 1) -> None:
    """Register a new bed at position."""
    _beds[(x, y, z)] = {
        "assigned": [],
        "quality": quality,  # 1=basic, 2=good, 3=excellent
    }
    # print(f"[Beds] Registered bed at ({x}, {y}, {z})")


def unregister_bed(x: int, y: int, z: int) -> None:
    """Remove a bed from registry."""
    if (x, y, z) in _beds:
        del _beds[(x, y, z)]
        # print(f"[Beds] Unregistered bed at ({x}, {y}, {z})")


def get_bed_at(x: int, y: int, z: int) -> Optional[dict]:
    """Get bed data at position, or None."""
    return _beds.get((x, y, z))


def get_all_beds() -> List[Tuple[Tuple[int, int, int], dict]]:
    """Get all beds as list of ((x,y,z), data) tuples."""
    return list(_beds.items())


def get_bed_count() -> int:
    """Get total number of beds."""
    return len(_beds)


def get_available_bed_slots() -> int:
    """Get number of unassigned bed slots (2 per bed)."""
    total = 0
    for pos, data in _beds.items():
        total += 2 - len(data["assigned"])
    return total


# =============================================================================
# BED ASSIGNMENT
# =============================================================================

def assign_colonist_to_bed(colonist_id: int, x: int, y: int, z: int) -> bool:
    """Assign a colonist to a bed. Returns True if successful."""
    bed = _beds.get((x, y, z))
    if not bed:
        return False
    
    # Already assigned here?
    if colonist_id in bed["assigned"]:
        return True
    
    # Bed full?
    if len(bed["assigned"]) >= 2:
        return False
    
    # Remove from any other bed first
    unassign_colonist(colonist_id)
    
    # Assign
    bed["assigned"].append(colonist_id)
    # print(f"[Beds] Colonist {colonist_id} assigned to bed at ({x}, {y}, {z})")
    return True


def unassign_colonist(colonist_id: int) -> None:
    """Remove colonist from any bed they're assigned to."""
    for pos, data in _beds.items():
        if colonist_id in data["assigned"]:
            data["assigned"].remove(colonist_id)
            # print(f"[Beds] Colonist {colonist_id} unassigned from bed at {pos}")
            return


def get_colonist_bed(colonist_id: int) -> Optional[Tuple[int, int, int]]:
    """Get the bed position a colonist is assigned to, or None."""
    for pos, data in _beds.items():
        if colonist_id in data["assigned"]:
            return pos
    return None


def get_bed_occupants(x: int, y: int, z: int) -> List[int]:
    """Get list of colonist IDs assigned to a bed."""
    bed = _beds.get((x, y, z))
    if bed:
        return list(bed["assigned"])
    return []


def get_bedmate(colonist_id: int) -> Optional[int]:
    """Get the other colonist sharing a bed, if any."""
    for pos, data in _beds.items():
        if colonist_id in data["assigned"]:
            for other_id in data["assigned"]:
                if other_id != colonist_id:
                    return other_id
    return None


# =============================================================================
# SLEEP QUALITY
# =============================================================================

def calculate_sleep_quality(colonist: "Colonist", all_colonists: list) -> float:
    """Calculate sleep quality for a colonist (0.0 to 2.0).
    
    Factors:
    - Has bed vs sleeping on ground
    - Bed quality
    - Bedmate relationship
    - Room quality (Bedroom bonus)
    """
    from relationships import get_relationship, get_romantic_partner
    
    colonist_id = id(colonist)
    bed_pos = get_colonist_bed(colonist_id)
    
    if not bed_pos:
        # Sleeping on ground
        return 0.5
    
    bed = _beds.get(bed_pos)
    if not bed:
        return 0.5
    
    # Base quality from bed
    quality = bed["quality"] * 0.5  # 0.5, 1.0, or 1.5
    
    # Room quality bonus (Bedroom)
    from room_effects import get_room_sleep_bonus
    bx, by, bz = bed_pos
    sleep_mult, mood = get_room_sleep_bonus(bx, by, bz)
    quality *= (1.0 + sleep_mult)  # Apply room sleep quality multiplier
    
    # Bedmate modifier
    bedmate_id = get_bedmate(colonist_id)
    if bedmate_id:
        # Find the bedmate colonist
        bedmate = None
        for c in all_colonists:
            if id(c) == bedmate_id:
                bedmate = c
                break
        
        if bedmate:
            rel = get_relationship(colonist, bedmate)
            
            # Romantic partner = bonus
            partner = get_romantic_partner(colonist, all_colonists)
            if partner and id(partner) == bedmate_id:
                quality += 0.3  # Cozy bonus
            elif rel["score"] >= 30:
                quality += 0.1  # Friend bonus
            elif rel["score"] <= -30:
                quality -= 0.3  # Enemy penalty
    
    return max(0.3, min(2.0, quality))


def get_sleep_thoughts(colonist: "Colonist", all_colonists: list) -> List[Tuple[str, float]]:
    """Get thoughts from sleep situation.
    
    Returns list of (thought_text, mood_effect) tuples.
    """
    from relationships import get_relationship, get_romantic_partner
    
    thoughts = []
    colonist_id = id(colonist)
    bed_pos = get_colonist_bed(colonist_id)
    
    if not bed_pos:
        thoughts.append(("Sleeping on the cold ground...", -0.2))
        return thoughts
    
    bed = _beds.get(bed_pos)
    if bed:
        if bed["quality"] >= 3:
            thoughts.append(("This bed is so comfortable.", 0.15))
        elif bed["quality"] >= 2:
            thoughts.append(("Decent bed.", 0.05))
    
    # Bedmate thoughts
    bedmate_id = get_bedmate(colonist_id)
    if bedmate_id:
        bedmate = None
        for c in all_colonists:
            if id(c) == bedmate_id:
                bedmate = c
                break
        
        if bedmate:
            rel = get_relationship(colonist, bedmate)
            partner = get_romantic_partner(colonist, all_colonists)
            
            if partner and id(partner) == bedmate_id:
                thoughts.append((f"Sleeping next to {bedmate.name.split()[0]}. ❤", 0.25))
            elif rel["score"] >= 50:
                thoughts.append((f"Sharing with {bedmate.name.split()[0]}. Good company.", 0.1))
            elif rel["score"] <= -50:
                thoughts.append((f"Have to share with {bedmate.name.split()[0]}. Ugh.", -0.25))
            elif rel["score"] <= -30:
                thoughts.append((f"Stuck with {bedmate.name.split()[0]}...", -0.15))
    
    return thoughts


# =============================================================================
# AUTO-ASSIGNMENT SUGGESTIONS
# =============================================================================

def suggest_bed_assignments(colonists: list) -> List[Tuple[int, int, Tuple[int, int, int]]]:
    """Suggest optimal bed assignments based on relationships.
    
    Returns list of (colonist_id, colonist_id, bed_pos) for pairs,
    or (colonist_id, None, bed_pos) for singles.
    """
    from relationships import get_relationship, get_romantic_partner
    
    suggestions = []
    assigned = set()
    
    # First pass: pair up romantic partners
    for colonist in colonists:
        if id(colonist) in assigned:
            continue
        
        partner = get_romantic_partner(colonist, colonists)
        if partner and id(partner) not in assigned:
            # Find an empty bed for them
            for pos, data in _beds.items():
                if len(data["assigned"]) == 0:
                    suggestions.append((id(colonist), id(partner), pos))
                    assigned.add(id(colonist))
                    assigned.add(id(partner))
                    break
    
    # Second pass: pair up close friends
    for colonist in colonists:
        if id(colonist) in assigned:
            continue
        
        best_friend = None
        best_score = 30  # Minimum friend threshold
        
        for other in colonists:
            if other is colonist or id(other) in assigned:
                continue
            rel = get_relationship(colonist, other)
            if rel["score"] > best_score:
                best_score = rel["score"]
                best_friend = other
        
        if best_friend:
            for pos, data in _beds.items():
                if len(data["assigned"]) == 0:
                    suggestions.append((id(colonist), id(best_friend), pos))
                    assigned.add(id(colonist))
                    assigned.add(id(best_friend))
                    break
    
    # Third pass: assign remaining colonists to any available bed
    for colonist in colonists:
        if id(colonist) in assigned:
            continue
        
        for pos, data in _beds.items():
            if len(data["assigned"]) < 2:
                # Check if we'd be pairing with an enemy
                if len(data["assigned"]) == 1:
                    other_id = data["assigned"][0]
                    other = None
                    for c in colonists:
                        if id(c) == other_id:
                            other = c
                            break
                    if other:
                        rel = get_relationship(colonist, other)
                        if rel["score"] <= -30:
                            continue  # Skip enemy pairing
                
                suggestions.append((id(colonist), None, pos))
                assigned.add(id(colonist))
                break
    
    return suggestions


# =============================================================================
# UNASSIGNED COLONISTS
# =============================================================================

def get_unassigned_colonists(colonists: list) -> List["Colonist"]:
    """Get colonists without bed assignments."""
    unassigned = []
    for colonist in colonists:
        if get_colonist_bed(id(colonist)) is None:
            unassigned.append(colonist)
    return unassigned


def get_bed_shortage(colonist_count: int) -> int:
    """Get how many more beds are needed (negative = surplus)."""
    # Each bed holds 2, so we need ceil(colonists/2) beds
    needed = (colonist_count + 1) // 2
    return needed - len(_beds)
