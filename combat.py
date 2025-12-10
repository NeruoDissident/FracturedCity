"""
Combat system for Fractured City.

Minimal stub for now - fistfighting only.
Combat decisions are influenced by:
- Relationships (will they help a friend?)
- Traits (brave vs cowardly, aggressive vs passive)
- Mood/stress (overwhelmed colonists may flee)
- Affinities (future: echo-touched may have special abilities)

Future expansion:
- Weapons and armor
- Echo abilities (corrupted AI/data magic)
- Ranged combat
- Group tactics
"""

import random
from typing import Optional, List, TYPE_CHECKING
from enum import Enum

if TYPE_CHECKING:
    from colonist import Colonist


class CombatStance(Enum):
    """How a colonist responds to combat."""
    AGGRESSIVE = "aggressive"   # Seeks fights, joins readily
    DEFENSIVE = "defensive"     # Fights when attacked or to protect others
    PASSIVE = "passive"         # Avoids combat, flees
    BERSERK = "berserk"         # Attacks anyone when triggered


# =============================================================================
# COMBAT STATS
# =============================================================================

def get_combat_power(colonist: "Colonist") -> float:
    """Calculate a colonist's combat effectiveness.
    
    Base power modified by:
    - Health (wounded = weaker)
    - Mood (stressed = weaker)
    - Traits (mercenary = stronger)
    - Equipment (future: weapons)
    
    Returns value typically 0.5 to 2.0
    """
    base_power = 1.0
    
    # Health modifier (50% health = 75% power)
    health_pct = colonist.health / 100.0
    health_mod = 0.5 + (health_pct * 0.5)
    
    # Mood modifier
    mood_mods = {
        "Euphoric": 1.1,
        "Calm": 1.05,
        "Focused": 1.0,
        "Uneasy": 0.95,
        "Stressed": 0.85,
        "Overwhelmed": 0.7,
    }
    mood_mod = mood_mods.get(colonist.mood_state, 1.0)
    
    # Trait modifiers
    trait_mod = 1.0
    traits = getattr(colonist, 'traits', {})
    
    # Experience bonuses
    exp = traits.get("experience", "")
    if exp == "former_mercenary":
        trait_mod += 0.3  # Combat training
    elif exp == "heatline_runner":
        trait_mod += 0.1  # Tough
    
    # Major trait bonuses
    major = traits.get("major_trait", "")
    if major == "rustborn":
        trait_mod += 0.15  # Hardy
    elif major == "pressure_blind":
        trait_mod += 0.1  # Fearless
    
    # Quirk penalties
    quirks = traits.get("quirks", [])
    if "mild_paranoia" in quirks:
        trait_mod += 0.05  # Always alert
    if "afraid_of_sky" in quirks or "afraid_of_tight_spaces" in quirks:
        trait_mod -= 0.05  # Anxious
    
    # Equipment bonus (future: actual weapons)
    equip_mod = 1.0
    equipment = getattr(colonist, 'equipment', {})
    # For now, any equipment gives tiny bonus
    equipped_count = sum(1 for v in equipment.values() if v is not None)
    equip_mod += equipped_count * 0.02
    
    return base_power * health_mod * mood_mod * trait_mod * equip_mod


def get_combat_stance(colonist: "Colonist") -> CombatStance:
    """Determine a colonist's combat stance based on personality.
    
    Influenced by traits, mood, and stress.
    """
    # Debug berserk mode (F12 toggle)
    if getattr(colonist, '_debug_berserk', False):
        return CombatStance.BERSERK
    
    traits = getattr(colonist, 'traits', {})
    stress = getattr(colonist, 'stress', 0.0)
    mood = colonist.mood_state
    
    # Check for berserk (very high stress + certain traits)
    if stress > 8:
        major = traits.get("major_trait", "")
        if major in ("rustborn", "static_soul"):
            return CombatStance.BERSERK
    
    # Check traits for stance
    exp = traits.get("experience", "")
    quirks = traits.get("quirks", [])
    
    # Aggressive types
    if exp == "former_mercenary":
        return CombatStance.AGGRESSIVE
    
    # Passive types
    if "mild_paranoia" in quirks:
        # Paranoid people avoid direct confrontation
        if stress > 5:
            return CombatStance.PASSIVE
    
    if "afraid_of_sky" in quirks or "afraid_of_tight_spaces" in quirks:
        return CombatStance.PASSIVE
    
    # Mood-based
    if mood == "Overwhelmed":
        return CombatStance.PASSIVE  # Too stressed to fight
    elif mood == "Euphoric":
        return CombatStance.AGGRESSIVE  # Feeling invincible
    
    # Default: defensive
    return CombatStance.DEFENSIVE


# =============================================================================
# WILLINGNESS TO HELP
# =============================================================================

def will_join_fight(colonist: "Colonist", victim: "Colonist", 
                    attacker: "Colonist", all_colonists: list) -> bool:
    """Determine if a colonist will join a fight to help the victim.
    
    Considers:
    - Relationship with victim (friend = more likely)
    - Relationship with attacker (enemy = more likely to oppose)
    - Combat stance (passive = unlikely)
    - Distance (too far = won't notice)
    - Own health/stress (wounded/stressed = less likely)
    
    Returns True if colonist will join to help victim.
    """
    from relationships import get_relationship
    
    # Can't help if dead or same person
    if colonist.is_dead or colonist is victim or colonist is attacker:
        return False
    
    # Check distance (must be within awareness range)
    dx = abs(colonist.x - victim.x)
    dy = abs(colonist.y - victim.y)
    if colonist.z != victim.z or max(dx, dy) > 8:
        return False  # Too far to notice
    
    # Get combat stance
    stance = get_combat_stance(colonist)
    
    # Passive colonists rarely join
    if stance == CombatStance.PASSIVE:
        # Only join for very close friends/family
        rel_victim = get_relationship(colonist, victim)
        if rel_victim["score"] < 70:
            return False
    
    # Berserk colonists attack everyone, don't help
    if stance == CombatStance.BERSERK:
        return False
    
    # Get relationships
    rel_victim = get_relationship(colonist, victim)
    rel_attacker = get_relationship(colonist, attacker)
    
    # Base willingness from relationship with victim
    # Friends help friends, strangers less so
    base_chance = 0.3  # 30% base chance to help anyone
    
    # Relationship with victim
    if rel_victim["score"] >= 60:
        base_chance += 0.5  # Close friend: very likely
    elif rel_victim["score"] >= 30:
        base_chance += 0.3  # Friend: likely
    elif rel_victim["score"] >= 0:
        base_chance += 0.1  # Acquaintance: somewhat
    else:
        base_chance -= 0.2  # Dislike victim: less likely
    
    # Relationship with attacker
    if rel_attacker["score"] <= -50:
        base_chance += 0.3  # Hate attacker: want to fight them
    elif rel_attacker["score"] >= 50:
        base_chance -= 0.4  # Like attacker: conflicted
    
    # Family bonds massively increase chance
    from relationships import get_family_bonds
    family = get_family_bonds(colonist)
    for other_id, bond in family:
        if other_id == id(victim):
            base_chance += 0.5  # Family: almost certain
            break
    
    # Stance modifier
    if stance == CombatStance.AGGRESSIVE:
        base_chance += 0.2  # Aggressive: eager to fight
    elif stance == CombatStance.DEFENSIVE:
        base_chance += 0.0  # Defensive: normal
    
    # Health/stress modifier
    health_pct = colonist.health / 100.0
    if health_pct < 0.5:
        base_chance -= 0.3  # Wounded: self-preservation
    
    stress = getattr(colonist, 'stress', 0.0)
    if stress > 6:
        base_chance -= 0.2  # Stressed: less heroic
    
    # Clamp and roll
    base_chance = max(0.0, min(1.0, base_chance))
    return random.random() < base_chance


def get_potential_defenders(victim: "Colonist", attacker: "Colonist", 
                            all_colonists: list) -> List["Colonist"]:
    """Get list of colonists who will defend the victim."""
    defenders = []
    for colonist in all_colonists:
        if will_join_fight(colonist, victim, attacker, all_colonists):
            defenders.append(colonist)
    return defenders


# =============================================================================
# COMBAT ACTIONS
# =============================================================================

def calculate_damage(attacker: "Colonist", defender: "Colonist") -> float:
    """Calculate damage from an attack.
    
    Base damage modified by power difference.
    Returns damage amount (typically 5-20).
    """
    attacker_power = get_combat_power(attacker)
    defender_power = get_combat_power(defender)
    
    # Base damage
    base_damage = 8.0
    
    # Power ratio affects damage
    power_ratio = attacker_power / max(0.1, defender_power)
    damage = base_damage * power_ratio
    
    # Randomness
    damage *= random.uniform(0.7, 1.3)
    
    # Minimum damage
    damage = max(3.0, damage)
    
    return damage


def perform_attack(attacker: "Colonist", defender: "Colonist", 
                   game_tick: int) -> dict:
    """Perform a single attack.
    
    Returns dict with:
        - hit: bool
        - damage: float
        - killed: bool
        - message: str
    """
    # Hit chance based on power difference
    attacker_power = get_combat_power(attacker)
    defender_power = get_combat_power(defender)
    
    hit_chance = 0.7 + (attacker_power - defender_power) * 0.1
    hit_chance = max(0.3, min(0.95, hit_chance))
    
    result = {
        "hit": False,
        "damage": 0.0,
        "killed": False,
        "retreated": False,
        "message": "",
    }
    
    attacker_name = attacker.name.split()[0]
    defender_name = defender.name.split()[0]
    
    if random.random() < hit_chance:
        # Hit!
        damage = calculate_damage(attacker, defender)
        defender.health -= damage
        
        result["hit"] = True
        result["damage"] = damage
        
        # Apply body damage if defender has body system
        from body import Body
        body = getattr(defender, 'body', None)
        if body is None:
            body = Body()
            defender.body = body
        
        # Pick a random body part and damage it
        target_part = body.get_random_external_part()
        if target_part:
            body_damage = damage * 1.5  # Scale damage for body parts
            is_fatal, body_log = body.damage_part(
                target_part, body_damage, "blunt", attacker_name, game_tick
            )
            result["body_part"] = target_part
            result["body_log"] = body_log
            
            # If vital organ destroyed, colonist dies
            if is_fatal:
                defender.health = 0
                defender.is_dead = True
                result["killed"] = True
                result["message"] = f"{attacker_name} killed {defender_name}! ({body_log})"
                return result
        
        # Check for retreat (fistfights usually non-lethal)
        if defender.health <= 30 and defender.health > 0:
            # Retreat check - most colonists flee at low health
            from relationships import get_relationship
            rel = get_relationship(attacker, defender)
            
            # Only fight to death if: berserk, true hatred, or hostile faction
            will_kill = False
            if get_combat_stance(attacker) == CombatStance.BERSERK:
                will_kill = True
            elif rel["score"] <= -80:  # True hatred
                will_kill = True
            elif getattr(attacker, 'is_hostile', False):  # Hostile faction
                will_kill = True
            
            if not will_kill:
                # Defender retreats!
                result["retreated"] = True
                result["message"] = f"{defender_name} retreats from the fight!"
                
                # End combat for both
                defender.in_combat = False
                defender.combat_target = None
                attacker.in_combat = False
                attacker.combat_target = None
                
                # Thoughts
                defender.add_thought("combat", f"Had to back down from {attacker_name}.", -0.2, game_tick=game_tick)
                attacker.add_thought("combat", f"{defender_name} backed off. Good.", 0.05, game_tick=game_tick)
                
                return result
        
        if defender.health <= 0:
            defender.health = 0
            defender.is_dead = True
            result["killed"] = True
            result["message"] = f"{attacker_name} killed {defender_name}!"
        else:
            # Include body part in message if available
            body_log = result.get("body_log", "")
            if body_log:
                result["message"] = body_log
            else:
                result["message"] = f"{attacker_name} hit {defender_name} for {damage:.0f} damage"
        
        # Add thoughts
        attacker.add_thought("combat", f"Fighting {defender_name}.", -0.1, game_tick=game_tick)
        defender.add_thought("combat", f"Attacked by {attacker_name}!", -0.2, game_tick=game_tick)
        
        # Stress from combat
        attacker.stress = min(10.0, attacker.stress + 0.5)
        defender.stress = min(10.0, defender.stress + 1.0)
        
    else:
        # Miss
        result["message"] = f"{attacker_name} missed {defender_name}"
    
    return result


# =============================================================================
# HOSTILITY SYSTEM
# =============================================================================

def is_hostile_to(colonist_a: "Colonist", colonist_b: "Colonist") -> bool:
    """Check if colonist_a is hostile to colonist_b.
    
    Hostility can come from:
    - Faction differences (future)
    - Berserk state
    - Explicit hostile flag
    """
    # Check explicit hostile flag
    if getattr(colonist_a, 'is_hostile', False):
        # Hostile to everyone not also hostile
        if not getattr(colonist_b, 'is_hostile', False):
            return True
    
    # Check berserk state
    if get_combat_stance(colonist_a) == CombatStance.BERSERK:
        return True  # Attacks everyone
    
    # Check faction (future)
    faction_a = getattr(colonist_a, 'faction', 'colony')
    faction_b = getattr(colonist_b, 'faction', 'colony')
    if faction_a != faction_b:
        # Different factions may be hostile
        hostile_factions = getattr(colonist_a, 'hostile_to_factions', set())
        if faction_b in hostile_factions:
            return True
    
    return False


def find_hostile_target(colonist: "Colonist", all_colonists: list) -> Optional["Colonist"]:
    """Find a target for a hostile colonist to attack.
    
    Prioritizes:
    1. Closest enemy
    2. Weakest enemy
    """
    if not is_hostile_to_anyone(colonist):
        return None
    
    targets = []
    for other in all_colonists:
        if other is colonist or other.is_dead:
            continue
        if is_hostile_to(colonist, other):
            dx = abs(colonist.x - other.x)
            dy = abs(colonist.y - other.y)
            if colonist.z == other.z and max(dx, dy) <= 10:
                distance = max(dx, dy)
                targets.append((other, distance))
    
    if not targets:
        return None
    
    # Sort by distance, then by health (prefer weak targets)
    targets.sort(key=lambda x: (x[1], x[0].health))
    return targets[0][0]


def is_hostile_to_anyone(colonist: "Colonist") -> bool:
    """Check if colonist is hostile to anyone."""
    if getattr(colonist, 'is_hostile', False):
        return True
    if get_combat_stance(colonist) == CombatStance.BERSERK:
        return True
    return False


# =============================================================================
# COMBAT LOG
# =============================================================================

_combat_log: List[dict] = []
_max_log_entries = 50


def log_combat_event(event: dict) -> None:
    """Add an event to the combat log."""
    global _combat_log
    _combat_log.append(event)
    if len(_combat_log) > _max_log_entries:
        _combat_log = _combat_log[-_max_log_entries:]


def get_combat_log(limit: int = 20) -> List[dict]:
    """Get recent combat events."""
    return list(reversed(_combat_log[-limit:]))


def clear_combat_log() -> None:
    """Clear the combat log."""
    global _combat_log
    _combat_log = []


# =============================================================================
# SOCIAL CONFLICTS - JEALOUSY, RIVALRY, BRAWLS
# =============================================================================

def check_jealousy(colonist: "Colonist", all_colonists: list, game_tick: int) -> Optional["Colonist"]:
    """Check if colonist is jealous and wants to fight a romantic rival.
    
    Triggers when:
    - Colonist has a romantic partner
    - Partner is talking to / near someone else
    - That someone has high relationship with partner
    - Colonist is stressed or has jealous tendencies
    
    Returns the rival to fight, or None.
    """
    from relationships import get_relationship, get_romantic_partner, RelationType
    
    partner = get_romantic_partner(colonist, all_colonists)
    if not partner:
        return None
    
    # Check stress level - more stressed = more jealous
    stress = getattr(colonist, 'stress', 0.0)
    jealousy_threshold = 0.02 if stress > 5 else 0.005  # Higher chance when stressed
    
    if random.random() > jealousy_threshold:
        return None
    
    # Look for potential rivals near partner
    for other in all_colonists:
        if other is colonist or other is partner or other.is_dead:
            continue
        
        # Is other near partner?
        dx = abs(other.x - partner.x)
        dy = abs(other.y - partner.y)
        if other.z != partner.z or max(dx, dy) > 2:
            continue
        
        # Does other have high relationship with partner?
        rel_other_partner = get_relationship(other, partner)
        if rel_other_partner["score"] < 40:
            continue  # Not a threat
        
        # Is other a romantic threat? (high score, recent interactions)
        if rel_other_partner["score"] >= 50 or rel_other_partner["interactions"] > 10:
            # Jealousy triggered!
            colonist.add_thought("combat", 
                f"Why is {other.name.split()[0]} always around {partner.name.split()[0]}?!", 
                -0.3, game_tick=game_tick)
            return other
    
    return None


def check_rivalry_brawl(colonist: "Colonist", all_colonists: list, game_tick: int) -> Optional["Colonist"]:
    """Check if colonist wants to start a brawl with a rival.
    
    Triggers when:
    - Colonist has low relationship with someone nearby
    - Colonist is stressed
    - Random chance based on aggression
    
    Returns the rival to fight, or None.
    """
    from relationships import get_relationship
    
    # Must be somewhat stressed
    stress = getattr(colonist, 'stress', 0.0)
    if stress < 3:
        return None  # Too calm to start fights
    
    # Check combat stance
    stance = get_combat_stance(colonist)
    if stance == CombatStance.PASSIVE:
        return None  # Won't start fights
    
    # Base chance scales with stress
    base_chance = (stress - 3) * 0.002  # 0.2% per stress point above 3
    if stance == CombatStance.AGGRESSIVE:
        base_chance *= 2
    
    if random.random() > base_chance:
        return None
    
    # Find nearby rivals
    for other in all_colonists:
        if other is colonist or other.is_dead:
            continue
        
        # Must be nearby
        dx = abs(other.x - colonist.x)
        dy = abs(other.y - colonist.y)
        if other.z != colonist.z or max(dx, dy) > 3:
            continue
        
        # Check relationship
        rel = get_relationship(colonist, other)
        if rel["score"] <= -30:  # Rival or enemy
            # Start a brawl!
            colonist.add_thought("combat", 
                f"I've had enough of {other.name.split()[0]}!", 
                -0.2, game_tick=game_tick)
            return other
    
    return None


def check_trait_clash(colonist: "Colonist", other: "Colonist", game_tick: int) -> bool:
    """Check if two colonists' traits cause a spontaneous conflict.
    
    Some trait combinations just don't mix.
    Returns True if a fight should start.
    """
    from relationships import get_relationship, CONFLICTING_TRAITS
    
    # Must be near each other
    dx = abs(other.x - colonist.x)
    dy = abs(other.y - colonist.y)
    if other.z != colonist.z or max(dx, dy) > 2:
        return False
    
    # Both must be somewhat stressed
    stress_a = getattr(colonist, 'stress', 0.0)
    stress_b = getattr(other, 'stress', 0.0)
    if stress_a < 2 or stress_b < 2:
        return False
    
    # Check for conflicting traits
    traits_a = getattr(colonist, 'traits', {})
    traits_b = getattr(other, 'traits', {})
    
    all_traits_a = set()
    all_traits_a.add(traits_a.get("origin", ""))
    all_traits_a.add(traits_a.get("experience", ""))
    all_traits_a.update(traits_a.get("quirks", []))
    if traits_a.get("major_trait"):
        all_traits_a.add(traits_a["major_trait"])
    
    all_traits_b = set()
    all_traits_b.add(traits_b.get("origin", ""))
    all_traits_b.add(traits_b.get("experience", ""))
    all_traits_b.update(traits_b.get("quirks", []))
    if traits_b.get("major_trait"):
        all_traits_b.add(traits_b["major_trait"])
    
    # Check for conflicts
    has_conflict = False
    for trait_a in all_traits_a:
        for trait_b in all_traits_b:
            if (trait_a, trait_b) in CONFLICTING_TRAITS or (trait_b, trait_a) in CONFLICTING_TRAITS:
                has_conflict = True
                break
    
    if not has_conflict:
        return False
    
    # Conflict exists - small chance of fight
    combined_stress = (stress_a + stress_b) / 2
    fight_chance = combined_stress * 0.001  # 0.1% per average stress point
    
    if random.random() < fight_chance:
        colonist.add_thought("combat", 
            f"{other.name.split()[0]} just gets under my skin!", 
            -0.15, game_tick=game_tick)
        other.add_thought("combat", 
            f"What is {colonist.name.split()[0]}'s problem?!", 
            -0.15, game_tick=game_tick)
        return True
    
    return False


def try_start_social_conflict(colonist: "Colonist", all_colonists: list, 
                               game_tick: int) -> Optional["Colonist"]:
    """Check if colonist starts a social conflict (jealousy, rivalry, trait clash).
    
    Called periodically from colonist update.
    Returns target to fight, or None.
    """
    # Already in combat?
    if colonist.in_combat:
        return None
    
    # Dead?
    if colonist.is_dead:
        return None
    
    # Cooldown - can't start fights too often
    last_conflict = getattr(colonist, '_last_conflict_check', 0)
    if game_tick - last_conflict < 300:  # ~5 seconds
        return None
    colonist._last_conflict_check = game_tick
    
    # Check jealousy first (most dramatic)
    target = check_jealousy(colonist, all_colonists, game_tick)
    if target:
        colonist._conflict_reason = "Jealousy"
        return target
    
    # Check rivalry
    target = check_rivalry_brawl(colonist, all_colonists, game_tick)
    if target:
        colonist._conflict_reason = "Rivalry"
        return target
    
    # Check trait clashes with nearby colonists
    for other in all_colonists:
        if other is colonist or other.is_dead:
            continue
        if check_trait_clash(colonist, other, game_tick):
            colonist._conflict_reason = "Personality clash"
            return other
    
    return None
