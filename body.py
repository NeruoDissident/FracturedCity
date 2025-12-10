"""Body System for Fractured City.

Detailed body part tracking for colonists, inspired by Dwarf Fortress.
Each colonist has a full body with parts that can be damaged, healed,
or replaced with cybernetics.

Body parts affect stats and capabilities when damaged.
"""

from enum import Enum
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
import random


class PartStatus(Enum):
    """Status of a body part."""
    HEALTHY = "healthy"
    BRUISED = "bruised"      # Minor damage, heals quickly
    CUT = "cut"              # Bleeding, needs treatment
    FRACTURED = "fractured"  # Bone damage, slow heal
    BROKEN = "broken"        # Severe, very slow heal
    MANGLED = "mangled"      # Permanent damage without surgery
    MISSING = "missing"      # Gone entirely
    CYBERNETIC = "cybernetic"  # Replaced with tech


class PartCategory(Enum):
    """Category of body part for grouping."""
    HEAD = "head"
    TORSO = "torso"
    ARM_LEFT = "arm_left"
    ARM_RIGHT = "arm_right"
    LEG_LEFT = "leg_left"
    LEG_RIGHT = "leg_right"


@dataclass
class BodyPart:
    """A single body part with health and status."""
    name: str
    category: PartCategory
    health: float = 100.0  # 0-100
    status: PartStatus = PartStatus.HEALTHY
    is_vital: bool = False  # If destroyed, colonist dies
    is_internal: bool = False  # Inside another part
    parent: Optional[str] = None  # Parent part (e.g., "hand" parent is "lower_arm_left")
    
    # Stat modifiers when damaged (stat_name -> modifier_per_damage_percent)
    stat_effects: Dict[str, float] = field(default_factory=dict)
    
    # Combat log entries for this part
    damage_log: List[str] = field(default_factory=list)
    
    def get_condition_text(self) -> str:
        """Get human-readable condition."""
        if self.status == PartStatus.MISSING:
            return "Missing"
        if self.status == PartStatus.CYBERNETIC:
            return f"Cybernetic ({self.health:.0f}%)"
        if self.health >= 90:
            return "Healthy"
        elif self.health >= 70:
            return f"Minor damage ({self.health:.0f}%)"
        elif self.health >= 50:
            return f"Damaged ({self.health:.0f}%)"
        elif self.health >= 25:
            return f"Badly damaged ({self.health:.0f}%)"
        else:
            return f"Critical ({self.health:.0f}%)"
    
    def get_color(self) -> Tuple[int, int, int]:
        """Get display color based on condition."""
        if self.status == PartStatus.MISSING:
            return (80, 80, 80)
        if self.status == PartStatus.CYBERNETIC:
            return (0, 200, 255)  # Cyan for cyber
        if self.health >= 90:
            return (100, 200, 100)  # Green
        elif self.health >= 70:
            return (180, 200, 100)  # Yellow-green
        elif self.health >= 50:
            return (220, 180, 60)   # Yellow
        elif self.health >= 25:
            return (220, 120, 60)   # Orange
        else:
            return (220, 60, 60)    # Red


# Body part templates - defines the full body structure
BODY_TEMPLATE: Dict[str, dict] = {
    # === HEAD ===
    "skull": {
        "name": "Skull",
        "category": PartCategory.HEAD,
        "is_vital": False,
        "is_internal": False,
        "parent": None,
        "stat_effects": {},
    },
    "brain": {
        "name": "Brain",
        "category": PartCategory.HEAD,
        "is_vital": True,
        "is_internal": True,
        "parent": "skull",
        "stat_effects": {"focus": -0.5, "mood": -0.3},
    },
    "eye_left": {
        "name": "Left Eye",
        "category": PartCategory.HEAD,
        "is_vital": False,
        "is_internal": False,
        "parent": "skull",
        "stat_effects": {"vision": -0.25},
    },
    "eye_right": {
        "name": "Right Eye",
        "category": PartCategory.HEAD,
        "is_vital": False,
        "is_internal": False,
        "parent": "skull",
        "stat_effects": {"vision": -0.25},
    },
    "ear_left": {
        "name": "Left Ear",
        "category": PartCategory.HEAD,
        "is_vital": False,
        "is_internal": False,
        "parent": "skull",
        "stat_effects": {"hearing": -0.25},
    },
    "ear_right": {
        "name": "Right Ear",
        "category": PartCategory.HEAD,
        "is_vital": False,
        "is_internal": False,
        "parent": "skull",
        "stat_effects": {"hearing": -0.25},
    },
    "nose": {
        "name": "Nose",
        "category": PartCategory.HEAD,
        "is_vital": False,
        "is_internal": False,
        "parent": "skull",
        "stat_effects": {},
    },
    "jaw": {
        "name": "Jaw",
        "category": PartCategory.HEAD,
        "is_vital": False,
        "is_internal": False,
        "parent": "skull",
        "stat_effects": {},
    },
    "teeth": {
        "name": "Teeth",
        "category": PartCategory.HEAD,
        "is_vital": False,
        "is_internal": False,
        "parent": "jaw",
        "stat_effects": {},
    },
    
    # === TORSO ===
    "chest": {
        "name": "Chest",
        "category": PartCategory.TORSO,
        "is_vital": False,
        "is_internal": False,
        "parent": None,
        "stat_effects": {},
    },
    "heart": {
        "name": "Heart",
        "category": PartCategory.TORSO,
        "is_vital": True,
        "is_internal": True,
        "parent": "chest",
        "stat_effects": {"walk_speed": -0.3, "stamina": -0.5},
    },
    "lungs": {
        "name": "Lungs",
        "category": PartCategory.TORSO,
        "is_vital": True,
        "is_internal": True,
        "parent": "chest",
        "stat_effects": {"walk_speed": -0.2, "stamina": -0.4},
    },
    "spine": {
        "name": "Spine",
        "category": PartCategory.TORSO,
        "is_vital": False,
        "is_internal": True,
        "parent": "chest",
        "stat_effects": {"walk_speed": -0.5, "haul_capacity": -0.5},
    },
    "ribs": {
        "name": "Ribs",
        "category": PartCategory.TORSO,
        "is_vital": False,
        "is_internal": False,
        "parent": "chest",
        "stat_effects": {},
    },
    "stomach": {
        "name": "Stomach",
        "category": PartCategory.TORSO,
        "is_vital": False,
        "is_internal": True,
        "parent": "chest",
        "stat_effects": {},
    },
    "liver": {
        "name": "Liver",
        "category": PartCategory.TORSO,
        "is_vital": False,
        "is_internal": True,
        "parent": "chest",
        "stat_effects": {"hazard_resist": -0.3},
    },
    "kidney_left": {
        "name": "Left Kidney",
        "category": PartCategory.TORSO,
        "is_vital": False,
        "is_internal": True,
        "parent": "chest",
        "stat_effects": {},
    },
    "kidney_right": {
        "name": "Right Kidney",
        "category": PartCategory.TORSO,
        "is_vital": False,
        "is_internal": True,
        "parent": "chest",
        "stat_effects": {},
    },
    
    # === LEFT ARM ===
    "shoulder_left": {
        "name": "Left Shoulder",
        "category": PartCategory.ARM_LEFT,
        "is_vital": False,
        "is_internal": False,
        "parent": "chest",
        "stat_effects": {"build_speed": -0.1, "haul_capacity": -0.15},
    },
    "upper_arm_left": {
        "name": "Left Upper Arm",
        "category": PartCategory.ARM_LEFT,
        "is_vital": False,
        "is_internal": False,
        "parent": "shoulder_left",
        "stat_effects": {"build_speed": -0.1, "haul_capacity": -0.1},
    },
    "elbow_left": {
        "name": "Left Elbow",
        "category": PartCategory.ARM_LEFT,
        "is_vital": False,
        "is_internal": False,
        "parent": "upper_arm_left",
        "stat_effects": {"build_speed": -0.05},
    },
    "lower_arm_left": {
        "name": "Left Lower Arm",
        "category": PartCategory.ARM_LEFT,
        "is_vital": False,
        "is_internal": False,
        "parent": "elbow_left",
        "stat_effects": {"build_speed": -0.1, "craft_speed": -0.1},
    },
    "hand_left": {
        "name": "Left Hand",
        "category": PartCategory.ARM_LEFT,
        "is_vital": False,
        "is_internal": False,
        "parent": "lower_arm_left",
        "stat_effects": {"build_speed": -0.15, "craft_speed": -0.2},
    },
    "fingers_left": {
        "name": "Left Fingers",
        "category": PartCategory.ARM_LEFT,
        "is_vital": False,
        "is_internal": False,
        "parent": "hand_left",
        "stat_effects": {"craft_speed": -0.15},
    },
    
    # === RIGHT ARM ===
    "shoulder_right": {
        "name": "Right Shoulder",
        "category": PartCategory.ARM_RIGHT,
        "is_vital": False,
        "is_internal": False,
        "parent": "chest",
        "stat_effects": {"build_speed": -0.1, "haul_capacity": -0.15},
    },
    "upper_arm_right": {
        "name": "Right Upper Arm",
        "category": PartCategory.ARM_RIGHT,
        "is_vital": False,
        "is_internal": False,
        "parent": "shoulder_right",
        "stat_effects": {"build_speed": -0.1, "haul_capacity": -0.1},
    },
    "elbow_right": {
        "name": "Right Elbow",
        "category": PartCategory.ARM_RIGHT,
        "is_vital": False,
        "is_internal": False,
        "parent": "upper_arm_right",
        "stat_effects": {"build_speed": -0.05},
    },
    "lower_arm_right": {
        "name": "Right Lower Arm",
        "category": PartCategory.ARM_RIGHT,
        "is_vital": False,
        "is_internal": False,
        "parent": "elbow_right",
        "stat_effects": {"build_speed": -0.1, "craft_speed": -0.1},
    },
    "hand_right": {
        "name": "Right Hand",
        "category": PartCategory.ARM_RIGHT,
        "is_vital": False,
        "is_internal": False,
        "parent": "lower_arm_right",
        "stat_effects": {"build_speed": -0.15, "craft_speed": -0.2},
    },
    "fingers_right": {
        "name": "Right Fingers",
        "category": PartCategory.ARM_RIGHT,
        "is_vital": False,
        "is_internal": False,
        "parent": "hand_right",
        "stat_effects": {"craft_speed": -0.15},
    },
    
    # === LEFT LEG ===
    "hip_left": {
        "name": "Left Hip",
        "category": PartCategory.LEG_LEFT,
        "is_vital": False,
        "is_internal": False,
        "parent": "chest",
        "stat_effects": {"walk_speed": -0.15},
    },
    "upper_leg_left": {
        "name": "Left Upper Leg",
        "category": PartCategory.LEG_LEFT,
        "is_vital": False,
        "is_internal": False,
        "parent": "hip_left",
        "stat_effects": {"walk_speed": -0.15},
    },
    "knee_left": {
        "name": "Left Knee",
        "category": PartCategory.LEG_LEFT,
        "is_vital": False,
        "is_internal": False,
        "parent": "upper_leg_left",
        "stat_effects": {"walk_speed": -0.1, "walk_steady": -0.2},
    },
    "lower_leg_left": {
        "name": "Left Lower Leg",
        "category": PartCategory.LEG_LEFT,
        "is_vital": False,
        "is_internal": False,
        "parent": "knee_left",
        "stat_effects": {"walk_speed": -0.1},
    },
    "foot_left": {
        "name": "Left Foot",
        "category": PartCategory.LEG_LEFT,
        "is_vital": False,
        "is_internal": False,
        "parent": "lower_leg_left",
        "stat_effects": {"walk_speed": -0.1, "walk_steady": -0.15},
    },
    "toes_left": {
        "name": "Left Toes",
        "category": PartCategory.LEG_LEFT,
        "is_vital": False,
        "is_internal": False,
        "parent": "foot_left",
        "stat_effects": {"walk_steady": -0.1},
    },
    
    # === RIGHT LEG ===
    "hip_right": {
        "name": "Right Hip",
        "category": PartCategory.LEG_RIGHT,
        "is_vital": False,
        "is_internal": False,
        "parent": "chest",
        "stat_effects": {"walk_speed": -0.15},
    },
    "upper_leg_right": {
        "name": "Right Upper Leg",
        "category": PartCategory.LEG_RIGHT,
        "is_vital": False,
        "is_internal": False,
        "parent": "hip_right",
        "stat_effects": {"walk_speed": -0.15},
    },
    "knee_right": {
        "name": "Right Knee",
        "category": PartCategory.LEG_RIGHT,
        "is_vital": False,
        "is_internal": False,
        "parent": "upper_leg_right",
        "stat_effects": {"walk_speed": -0.1, "walk_steady": -0.2},
    },
    "lower_leg_right": {
        "name": "Right Lower Leg",
        "category": PartCategory.LEG_RIGHT,
        "is_vital": False,
        "is_internal": False,
        "parent": "knee_right",
        "stat_effects": {"walk_speed": -0.1},
    },
    "foot_right": {
        "name": "Right Foot",
        "category": PartCategory.LEG_RIGHT,
        "is_vital": False,
        "is_internal": False,
        "parent": "lower_leg_right",
        "stat_effects": {"walk_speed": -0.1, "walk_steady": -0.15},
    },
    "toes_right": {
        "name": "Right Toes",
        "category": PartCategory.LEG_RIGHT,
        "is_vital": False,
        "is_internal": False,
        "parent": "foot_right",
        "stat_effects": {"walk_steady": -0.1},
    },
}


class Body:
    """Complete body system for a colonist."""
    
    def __init__(self):
        self.parts: Dict[str, BodyPart] = {}
        self.combat_log: List[Tuple[float, str]] = []  # (game_time, message)
        self.blood_loss: float = 0.0  # 0-100, death at 100
        self.cause_of_death: str = ""  # Set when fatal damage occurs
        self._init_body()
    
    def _init_body(self) -> None:
        """Initialize all body parts from template."""
        for part_id, template in BODY_TEMPLATE.items():
            self.parts[part_id] = BodyPart(
                name=template["name"],
                category=template["category"],
                is_vital=template["is_vital"],
                is_internal=template["is_internal"],
                parent=template["parent"],
                stat_effects=dict(template.get("stat_effects", {})),
            )
    
    def get_part(self, part_id: str) -> Optional[BodyPart]:
        """Get a body part by ID."""
        return self.parts.get(part_id)
    
    def get_parts_by_category(self, category: PartCategory) -> List[Tuple[str, BodyPart]]:
        """Get all parts in a category."""
        return [(pid, part) for pid, part in self.parts.items() 
                if part.category == category]
    
    def get_external_parts(self) -> List[Tuple[str, BodyPart]]:
        """Get all external (targetable) parts."""
        return [(pid, part) for pid, part in self.parts.items() 
                if not part.is_internal and part.status != PartStatus.MISSING]
    
    def damage_part(self, part_id: str, amount: float, damage_type: str = "blunt",
                    attacker_name: str = "", game_time: float = 0.0) -> Tuple[bool, str]:
        """
        Damage a body part.
        
        Returns (is_fatal, log_message)
        - Fatal from: vital organ destruction, or blood loss reaching 100
        """
        import random
        part = self.parts.get(part_id)
        if not part or part.status == PartStatus.MISSING:
            return False, ""
        
        # Apply damage
        old_health = part.health
        part.health = max(0, part.health - amount)
        
        # Blood loss from cuts and severe damage
        # More blood from: cuts, major arteries (neck, torso), severe wounds
        bleed_amount = 0.0
        if damage_type != "blunt":
            # Cuts always bleed
            bleed_amount = amount * 0.3
        if part.health < 25:
            # Severe wounds bleed more
            bleed_amount += amount * 0.2
        # Major blood vessels
        if part_id in ("chest", "stomach", "heart", "lungs", "liver"):
            bleed_amount *= 2.0
        
        self.blood_loss = min(100, self.blood_loss + bleed_amount)
        
        # Vicious attack verbs based on body part and damage type
        part_lower = part.name.lower()
        
        # Special attack descriptions for specific body parts
        special_attacks = {
            "eye_left": ["gouges", "claws at", "jabs", "rakes"],
            "eye_right": ["gouges", "claws at", "jabs", "rakes"],
            "nose": ["smashes", "breaks", "crushes", "headbutts"],
            "jaw": ["cracks", "dislocates", "uppercuts", "shatters"],
            "teeth": ["knocks out", "smashes", "breaks"],
            "ear_left": ["tears", "bites", "rips"],
            "ear_right": ["tears", "bites", "rips"],
            "fingers_left": ["breaks", "bends back", "stomps", "crushes"],
            "fingers_right": ["breaks", "bends back", "stomps", "crushes"],
            "toes_left": ["stomps", "crushes", "breaks"],
            "toes_right": ["stomps", "crushes", "breaks"],
            "stomach": ["gut-punches", "knees", "elbows"],
            "ribs": ["cracks", "breaks", "elbows"],
            "knee_left": ["kicks", "stomps", "hyperextends"],
            "knee_right": ["kicks", "stomps", "hyperextends"],
        }
        
        # Generic attack verbs
        blunt_attacks = ["punches", "strikes", "slams", "hammers", "bashes", "kicks", "elbows", "knees"]
        cut_attacks = ["slashes", "cuts", "slices", "gashes", "rakes"]
        
        # Pick attack verb
        if part_id in special_attacks:
            attack_verb = random.choice(special_attacks[part_id])
        elif damage_type == "blunt":
            attack_verb = random.choice(blunt_attacks)
        else:
            attack_verb = random.choice(cut_attacks)
        
        # Damage result descriptions
        is_fatal = False
        if part.health <= 0:
            if part.is_vital:
                part.status = PartStatus.MANGLED
                # Specific death causes for vital organs
                death_causes = {
                    "brain": ["brain destroyed", "skull crushed", "head caved in"],
                    "heart": ["heart ruptured", "heart destroyed", "cardiac rupture"],
                    "lungs": ["lungs collapsed", "chest cavity destroyed", "suffocated"],
                }
                if part_id in death_causes:
                    self.cause_of_death = random.choice(death_causes[part_id])
                else:
                    self.cause_of_death = f"{part.name} destroyed"
                log_msg = self.cause_of_death.capitalize() + "!"
                if attacker_name:
                    log_msg = f"{attacker_name} {attack_verb} {part_lower} - {log_msg}"
                self.combat_log.append((game_time, log_msg))
                return True, log_msg  # Fatal!
            else:
                part.status = PartStatus.MANGLED
                results = ["mangled", "destroyed", "ruined", "wrecked"]
                log_msg = f"{part.name} {random.choice(results)}"
        elif part.health < 25:
            if damage_type == "blunt":
                part.status = PartStatus.BROKEN
                results = ["breaks", "shatters", "snaps", "crunches"]
            else:
                part.status = PartStatus.MANGLED
                results = ["torn open", "gashed deeply", "split"]
            log_msg = f"{part.name} {random.choice(results)}"
        elif part.health < 50:
            if damage_type == "blunt":
                part.status = PartStatus.FRACTURED
                results = ["cracks", "fractures", "buckles"]
            else:
                part.status = PartStatus.CUT
                results = ["sliced", "cut deep", "gashed"]
            log_msg = f"{part.name} {random.choice(results)}"
        elif part.health < 75:
            if damage_type == "blunt":
                part.status = PartStatus.BRUISED
                results = ["bruises", "swells", "throbs"]
            else:
                part.status = PartStatus.CUT
                results = ["bleeds", "is cut", "is nicked"]
            log_msg = f"{part.name} {random.choice(results)}"
        else:
            results = ["stings", "aches", "is hit", "takes a hit"]
            log_msg = f"{part.name} {random.choice(results)}"
        
        # Build full log message
        if attacker_name:
            full_log = f"{attacker_name} {attack_verb} {part_lower} - {log_msg}"
        else:
            full_log = log_msg
        
        self.combat_log.append((game_time, full_log))
        part.damage_log.append(full_log)
        
        # Check for death by blood loss
        if self.blood_loss >= 100:
            self.cause_of_death = "bled out"
            self.combat_log.append((game_time, "Bled out from wounds"))
            return True, full_log
        
        return False, full_log
    
    def heal_part(self, part_id: str, amount: float) -> None:
        """Heal a body part."""
        part = self.parts.get(part_id)
        if not part or part.status in (PartStatus.MISSING, PartStatus.CYBERNETIC):
            return
        
        part.health = min(100, part.health + amount)
        
        # Update status based on new health
        if part.health >= 90:
            part.status = PartStatus.HEALTHY
        elif part.health >= 70:
            part.status = PartStatus.BRUISED
        elif part.health >= 50:
            part.status = PartStatus.FRACTURED if part.status in (PartStatus.FRACTURED, PartStatus.BROKEN) else PartStatus.CUT
    
    def heal_all(self, amount: float) -> None:
        """Heal all body parts by a small amount (natural healing)."""
        for part in self.parts.values():
            if part.status not in (PartStatus.MISSING, PartStatus.CYBERNETIC, PartStatus.MANGLED):
                self.heal_part(part.name, amount)
    
    def get_random_external_part(self) -> Optional[str]:
        """Get a random external part that can be hit in combat."""
        external = self.get_external_parts()
        if not external:
            return None
        
        # Weight by body region (torso/head more likely to be hit)
        weights = []
        for part_id, part in external:
            if part.category == PartCategory.TORSO:
                weights.append(3.0)
            elif part.category == PartCategory.HEAD:
                weights.append(2.0)
            else:
                weights.append(1.0)
        
        total = sum(weights)
        r = random.random() * total
        cumulative = 0
        for i, (part_id, _) in enumerate(external):
            cumulative += weights[i]
            if r <= cumulative:
                return part_id
        
        return external[0][0] if external else None
    
    def get_stat_modifiers(self) -> Dict[str, float]:
        """Calculate total stat modifiers from all damaged parts."""
        modifiers: Dict[str, float] = {}
        
        for part in self.parts.values():
            if part.status == PartStatus.MISSING:
                # Missing part = full penalty
                damage_percent = 100
            elif part.status == PartStatus.CYBERNETIC:
                # Cybernetic = no penalty (or bonus later)
                continue
            else:
                damage_percent = 100 - part.health
            
            for stat, modifier_per_percent in part.stat_effects.items():
                penalty = modifier_per_percent * damage_percent
                modifiers[stat] = modifiers.get(stat, 0) + penalty
        
        return modifiers
    
    def get_overall_health(self) -> float:
        """Get overall body health percentage."""
        total = 0
        count = 0
        for part in self.parts.values():
            if part.status == PartStatus.MISSING:
                total += 0
            elif part.status == PartStatus.CYBERNETIC:
                total += part.health
            else:
                total += part.health
            count += 1
        
        return total / count if count > 0 else 100
    
    def get_recent_combat_log(self, count: int = 10) -> List[str]:
        """Get the most recent combat log entries."""
        return [msg for _, msg in self.combat_log[-count:]]
    
    def to_dict(self) -> dict:
        """Serialize body state for saving."""
        return {
            "parts": {
                part_id: {
                    "health": part.health,
                    "status": part.status.value,
                }
                for part_id, part in self.parts.items()
            },
            "combat_log": self.combat_log[-50:],  # Keep last 50 entries
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Body":
        """Deserialize body state from save."""
        body = cls()
        
        if "parts" in data:
            for part_id, part_data in data["parts"].items():
                if part_id in body.parts:
                    body.parts[part_id].health = part_data.get("health", 100)
                    status_str = part_data.get("status", "healthy")
                    try:
                        body.parts[part_id].status = PartStatus(status_str)
                    except ValueError:
                        body.parts[part_id].status = PartStatus.HEALTHY
        
        if "combat_log" in data:
            body.combat_log = data["combat_log"]
        
        return body


# Combat helper functions
def simulate_punch(attacker_name: str, defender_body: Body, game_time: float = 0.0) -> Tuple[bool, str]:
    """Simulate a punch attack, returns (is_fatal, log_message)."""
    target_part = defender_body.get_random_external_part()
    if not target_part:
        return False, f"{attacker_name} swings at nothing"
    
    # Punch damage: 5-15
    damage = random.uniform(5, 15)
    
    return defender_body.damage_part(target_part, damage, "blunt", attacker_name, game_time)


def simulate_fight_round(attacker_name: str, attacker_body: Body,
                         defender_name: str, defender_body: Body,
                         game_time: float = 0.0) -> List[str]:
    """Simulate one round of a fight between two colonists."""
    logs = []
    
    # Attacker hits defender
    fatal, log = simulate_punch(attacker_name, defender_body, game_time)
    if log:
        logs.append(log)
    
    if fatal:
        logs.append(f"{defender_name} has been killed!")
        return logs
    
    # Defender counter-attacks (50% chance)
    if random.random() < 0.5:
        fatal, log = simulate_punch(defender_name, attacker_body, game_time)
        if log:
            logs.append(log)
        if fatal:
            logs.append(f"{attacker_name} has been killed!")
    
    return logs
