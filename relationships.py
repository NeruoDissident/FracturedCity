"""
Relationship system for Fractured City colonists.

Tracks:
- Relationship scores between colonists (-100 to +100)
- Relationship types (stranger, acquaintance, friend, close friend, rival, enemy, romantic, family)
- Family connections (parent, child, sibling, partner)
- Shared history (same origin, worked together, etc.)

Relationships affect:
- Conversation topics and frequency
- Mood when near certain colonists
- Work efficiency when paired
- Willingness to help/rescue
"""

import random
from typing import Optional, Dict, List, TYPE_CHECKING
from enum import Enum

if TYPE_CHECKING:
    from colonist import Colonist


class RelationType(Enum):
    """Types of relationships between colonists."""
    STRANGER = "stranger"           # Never interacted
    ACQUAINTANCE = "acquaintance"   # Talked a few times
    FRIEND = "friend"               # Positive relationship
    CLOSE_FRIEND = "close_friend"   # Strong positive bond
    RIVAL = "rival"                 # Competitive tension
    ENEMY = "enemy"                 # Strong negative relationship
    ROMANTIC = "romantic"           # Romantic interest/partner
    FAMILY = "family"               # Blood or adopted family


class FamilyBond(Enum):
    """Types of family connections."""
    PARENT = "parent"       # This colonist is the parent
    CHILD = "child"         # This colonist is the child
    SIBLING = "sibling"     # Siblings
    PARTNER = "partner"     # Romantic partner / spouse


# =============================================================================
# RELATIONSHIP DATA STORAGE
# =============================================================================

# Global relationship storage: {(colonist_id_a, colonist_id_b): RelationshipData}
# IDs are sorted so (A,B) and (B,A) map to same entry
_relationships: Dict[tuple, dict] = {}

# Family bonds: {colonist_id: [(other_id, FamilyBond), ...]}
_family_bonds: Dict[int, List[tuple]] = {}


def _get_pair_key(colonist_a: "Colonist", colonist_b: "Colonist") -> tuple:
    """Get a consistent key for a pair of colonists."""
    id_a = id(colonist_a)
    id_b = id(colonist_b)
    return (min(id_a, id_b), max(id_a, id_b))


def get_relationship(colonist_a: "Colonist", colonist_b: "Colonist") -> dict:
    """Get relationship data between two colonists.
    
    Returns dict with:
        - score: int (-100 to +100)
        - type: RelationType
        - interactions: int (number of conversations)
        - last_interaction: int (game tick)
        - shared_origin: bool
        - shared_experience: bool
        - history: list of notable events
    """
    key = _get_pair_key(colonist_a, colonist_b)
    
    if key not in _relationships:
        # Initialize new relationship
        _relationships[key] = {
            "score": 0,
            "type": RelationType.STRANGER,
            "interactions": 0,
            "last_interaction": 0,
            "shared_origin": False,
            "shared_experience": False,
            "history": [],
        }
        
        # Check for shared traits
        _check_shared_background(colonist_a, colonist_b, _relationships[key])
    
    return _relationships[key]


def _check_shared_background(colonist_a: "Colonist", colonist_b: "Colonist", rel_data: dict) -> None:
    """Check if colonists share background traits and update relationship."""
    traits_a = getattr(colonist_a, 'traits', {})
    traits_b = getattr(colonist_b, 'traits', {})
    
    # Shared origin gives starting bonus
    if traits_a.get("origin") and traits_a.get("origin") == traits_b.get("origin"):
        rel_data["shared_origin"] = True
        rel_data["score"] += 15  # Starting affinity
        rel_data["history"].append("Recognized each other from the same origin")
    
    # Shared experience gives smaller bonus
    if traits_a.get("experience") and traits_a.get("experience") == traits_b.get("experience"):
        rel_data["shared_experience"] = True
        rel_data["score"] += 10
        rel_data["history"].append("Bonded over shared experience")


def modify_relationship(colonist_a: "Colonist", colonist_b: "Colonist", 
                        delta: int, reason: str = "") -> None:
    """Modify relationship score between two colonists.
    
    Args:
        colonist_a: First colonist
        colonist_b: Second colonist
        delta: Amount to change score (-100 to +100)
        reason: Optional reason for the change (for history)
    """
    rel = get_relationship(colonist_a, colonist_b)
    
    old_score = rel["score"]
    rel["score"] = max(-100, min(100, rel["score"] + delta))
    
    # Update relationship type based on score
    rel["type"] = _score_to_type(rel["score"], rel)
    
    # Add to history if significant
    if reason and abs(delta) >= 5:
        rel["history"].append(reason)
        # Keep history manageable
        if len(rel["history"]) > 10:
            rel["history"] = rel["history"][-10:]


def record_interaction(colonist_a: "Colonist", colonist_b: "Colonist", 
                       game_tick: int, positive: bool = True) -> None:
    """Record that two colonists interacted.
    
    Args:
        colonist_a: First colonist
        colonist_b: Second colonist
        game_tick: Current game tick
        positive: Whether the interaction was positive
    """
    rel = get_relationship(colonist_a, colonist_b)
    
    rel["interactions"] += 1
    rel["last_interaction"] = game_tick
    
    # Small relationship change from interaction
    if positive:
        delta = random.randint(1, 3)
    else:
        delta = random.randint(-3, -1)
    
    rel["score"] = max(-100, min(100, rel["score"] + delta))
    rel["type"] = _score_to_type(rel["score"], rel)


def _score_to_type(score: int, rel_data: dict) -> RelationType:
    """Convert relationship score to relationship type."""
    # Check for family first
    # (Family bonds are tracked separately)
    
    if score >= 60:
        return RelationType.CLOSE_FRIEND
    elif score >= 30:
        return RelationType.FRIEND
    elif score >= 5:
        return RelationType.ACQUAINTANCE
    elif score > -30:
        return RelationType.STRANGER
    elif score > -60:
        return RelationType.RIVAL
    else:
        return RelationType.ENEMY


# =============================================================================
# FAMILY SYSTEM
# =============================================================================

def add_family_bond(colonist_a: "Colonist", colonist_b: "Colonist", 
                    bond_type: FamilyBond) -> None:
    """Add a family bond between two colonists.
    
    Args:
        colonist_a: First colonist
        colonist_b: Second colonist
        bond_type: Type of bond FROM colonist_a's perspective
    """
    id_a = id(colonist_a)
    id_b = id(colonist_b)
    
    if id_a not in _family_bonds:
        _family_bonds[id_a] = []
    if id_b not in _family_bonds:
        _family_bonds[id_b] = []
    
    # Add bond from A's perspective
    _family_bonds[id_a].append((id_b, bond_type))
    
    # Add reciprocal bond from B's perspective
    reciprocal = _get_reciprocal_bond(bond_type)
    _family_bonds[id_b].append((id_a, reciprocal))
    
    # Family members start with high relationship
    rel = get_relationship(colonist_a, colonist_b)
    rel["score"] = max(rel["score"], 50)
    rel["type"] = RelationType.FAMILY
    rel["history"].append(f"Family: {bond_type.value}")


def _get_reciprocal_bond(bond_type: FamilyBond) -> FamilyBond:
    """Get the reciprocal family bond type."""
    if bond_type == FamilyBond.PARENT:
        return FamilyBond.CHILD
    elif bond_type == FamilyBond.CHILD:
        return FamilyBond.PARENT
    elif bond_type == FamilyBond.SIBLING:
        return FamilyBond.SIBLING
    elif bond_type == FamilyBond.PARTNER:
        return FamilyBond.PARTNER
    return bond_type


def get_family_bonds(colonist: "Colonist") -> List[tuple]:
    """Get all family bonds for a colonist.
    
    Returns list of (colonist_id, FamilyBond) tuples.
    """
    return _family_bonds.get(id(colonist), [])


def find_colonist_by_id(colonist_id: int, all_colonists: list) -> Optional["Colonist"]:
    """Find a colonist by their id()."""
    for c in all_colonists:
        if id(c) == colonist_id:
            return c
    return None


# =============================================================================
# RELATIONSHIP QUERIES
# =============================================================================

def get_all_relationships(colonist: "Colonist", all_colonists: list) -> List[tuple]:
    """Get all relationships for a colonist.
    
    Returns list of (other_colonist, relationship_data) tuples, sorted by score.
    """
    relationships = []
    
    for other in all_colonists:
        if other is colonist:
            continue
        rel = get_relationship(colonist, other)
        relationships.append((other, rel))
    
    # Sort by score (highest first)
    relationships.sort(key=lambda x: x[1]["score"], reverse=True)
    return relationships


def get_friends(colonist: "Colonist", all_colonists: list) -> List["Colonist"]:
    """Get all friends (score >= 30) of a colonist."""
    friends = []
    for other in all_colonists:
        if other is colonist:
            continue
        rel = get_relationship(colonist, other)
        if rel["score"] >= 30:
            friends.append(other)
    return friends


def get_rivals(colonist: "Colonist", all_colonists: list) -> List["Colonist"]:
    """Get all rivals/enemies (score <= -30) of a colonist."""
    rivals = []
    for other in all_colonists:
        if other is colonist:
            continue
        rel = get_relationship(colonist, other)
        if rel["score"] <= -30:
            rivals.append(other)
    return rivals


def get_romantic_partner(colonist: "Colonist", all_colonists: list) -> Optional["Colonist"]:
    """Get the romantic partner of a colonist, if any."""
    for other in all_colonists:
        if other is colonist:
            continue
        rel = get_relationship(colonist, other)
        if rel["type"] == RelationType.ROMANTIC:
            return other
    return None


# =============================================================================
# TRAIT COMPATIBILITY
# =============================================================================

# Trait pairs that create natural affinity
COMPATIBLE_TRAITS = {
    # Origins that understand each other
    ("rust_warrens", "wreck_yards"),  # Both scavenger types
    ("deep_shelters", "silent_commune_raised"),  # Both underground
    ("topside_sprawl", "signal_frontier"),  # Both exposed to signals
    
    # Experiences that bond
    ("cortex_bloom_survivor", "echo_touched"),  # Both affected by echoes
    ("former_mercenary", "heatline_runner"),  # Both dangerous work
    ("collapsed_block_escapee", "floodlight_displaced"),  # Both lost homes
}

# Trait pairs that create tension
CONFLICTING_TRAITS = {
    # Personality clashes
    ("mild_paranoia", "overexplains"),  # Paranoid hates talkers
    ("afraid_of_sky", "topside_sprawl"),  # Fears vs loves outside
    ("afraid_of_tight_spaces", "deep_shelters"),  # Claustrophobic vs underground
    
    # Philosophical differences
    ("last_light_disciple", "gravemind_listener"),  # Different beliefs
}


def calculate_trait_compatibility(colonist_a: "Colonist", colonist_b: "Colonist") -> int:
    """Calculate compatibility bonus/penalty based on traits.
    
    Returns value from -20 to +20.
    """
    traits_a = getattr(colonist_a, 'traits', {})
    traits_b = getattr(colonist_b, 'traits', {})
    
    compatibility = 0
    
    # Collect all trait keys
    all_traits_a = set()
    all_traits_a.add(traits_a.get("origin", ""))
    all_traits_a.add(traits_a.get("experience", ""))
    all_traits_a.update(traits_a.get("quirks", []))
    if traits_a.get("major_trait"):
        all_traits_a.add(traits_a["major_trait"])
    all_traits_a.discard("")
    
    all_traits_b = set()
    all_traits_b.add(traits_b.get("origin", ""))
    all_traits_b.add(traits_b.get("experience", ""))
    all_traits_b.update(traits_b.get("quirks", []))
    if traits_b.get("major_trait"):
        all_traits_b.add(traits_b["major_trait"])
    all_traits_b.discard("")
    
    # Check compatible pairs
    for trait_a in all_traits_a:
        for trait_b in all_traits_b:
            if (trait_a, trait_b) in COMPATIBLE_TRAITS or (trait_b, trait_a) in COMPATIBLE_TRAITS:
                compatibility += 10
    
    # Check conflicting pairs
    for trait_a in all_traits_a:
        for trait_b in all_traits_b:
            if (trait_a, trait_b) in CONFLICTING_TRAITS or (trait_b, trait_a) in CONFLICTING_TRAITS:
                compatibility -= 10
    
    return max(-20, min(20, compatibility))


# =============================================================================
# ROMANCE SYSTEM
# =============================================================================

def check_romance_potential(colonist_a: "Colonist", colonist_b: "Colonist") -> bool:
    """Check if two colonists could develop romantic interest.
    
    Requirements:
    - Both adults (age >= 18)
    - Not family
    - Relationship score >= 50
    - Compatible traits (not enemies)
    """
    # Check ages
    age_a = getattr(colonist_a, 'age', 25)
    age_b = getattr(colonist_b, 'age', 25)
    if age_a < 18 or age_b < 18:
        return False
    
    # Check not family
    family_bonds = get_family_bonds(colonist_a)
    for other_id, bond in family_bonds:
        if other_id == id(colonist_b):
            if bond in (FamilyBond.PARENT, FamilyBond.CHILD, FamilyBond.SIBLING):
                return False
    
    # Check relationship score
    rel = get_relationship(colonist_a, colonist_b)
    if rel["score"] < 50:
        return False
    
    # Check not enemies
    if rel["type"] in (RelationType.RIVAL, RelationType.ENEMY):
        return False
    
    return True


def try_develop_romance(colonist_a: "Colonist", colonist_b: "Colonist", 
                        game_tick: int) -> bool:
    """Try to develop romantic relationship between two colonists.
    
    Returns True if romance developed.
    """
    if not check_romance_potential(colonist_a, colonist_b):
        return False
    
    rel = get_relationship(colonist_a, colonist_b)
    
    # Already romantic
    if rel["type"] == RelationType.ROMANTIC:
        return False
    
    # Chance based on relationship score and compatibility
    compatibility = calculate_trait_compatibility(colonist_a, colonist_b)
    chance = (rel["score"] - 40 + compatibility) / 200  # 0-30% chance
    
    if random.random() < chance:
        rel["type"] = RelationType.ROMANTIC
        rel["score"] = max(rel["score"], 70)
        rel["history"].append("Became romantic partners")
        
        # Add partner family bond
        add_family_bond(colonist_a, colonist_b, FamilyBond.PARTNER)
        
        return True
    
    return False


# =============================================================================
# RELATIONSHIP LABELS FOR UI
# =============================================================================

def get_relationship_label(colonist_a: "Colonist", colonist_b: "Colonist") -> str:
    """Get a human-readable label for the relationship."""
    rel = get_relationship(colonist_a, colonist_b)
    
    # Check family bonds first
    family_bonds = get_family_bonds(colonist_a)
    for other_id, bond in family_bonds:
        if other_id == id(colonist_b):
            if bond == FamilyBond.PARTNER:
                return "Partner"
            elif bond == FamilyBond.PARENT:
                return "Parent"
            elif bond == FamilyBond.CHILD:
                return "Child"
            elif bond == FamilyBond.SIBLING:
                return "Sibling"
    
    # Use relationship type
    type_labels = {
        RelationType.STRANGER: "Stranger",
        RelationType.ACQUAINTANCE: "Acquaintance",
        RelationType.FRIEND: "Friend",
        RelationType.CLOSE_FRIEND: "Close Friend",
        RelationType.RIVAL: "Rival",
        RelationType.ENEMY: "Enemy",
        RelationType.ROMANTIC: "Partner",
        RelationType.FAMILY: "Family",
    }
    
    return type_labels.get(rel["type"], "Unknown")


def get_relationship_color(colonist_a: "Colonist", colonist_b: "Colonist") -> tuple:
    """Get a color for the relationship (for UI)."""
    rel = get_relationship(colonist_a, colonist_b)
    score = rel["score"]
    
    if rel["type"] == RelationType.ROMANTIC:
        return (255, 150, 200)  # Pink
    elif rel["type"] == RelationType.FAMILY:
        return (200, 180, 255)  # Purple
    elif score >= 60:
        return (100, 255, 150)  # Bright green
    elif score >= 30:
        return (150, 220, 150)  # Green
    elif score >= 0:
        return (180, 180, 180)  # Gray
    elif score >= -30:
        return (220, 180, 100)  # Yellow
    elif score >= -60:
        return (220, 150, 100)  # Orange
    else:
        return (220, 100, 100)  # Red
