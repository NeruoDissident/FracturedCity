"""
Injury-aware thought generation for Fractured City.

Maps body part injuries to contextual thoughts that colonists have
about their symptoms. Makes injuries feel real and visible in the
colonist's internal monologue.
"""

import random
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from colonist import Colonist
    from body import Body

# Injury thoughts organized by body part category
# Format: {part_id: {severity_range: [thought_templates]}}

INJURY_THOUGHTS = {
    # === EYES ===
    "eye_left": {
        (0, 25): [  # Critical
            "I can barely see anything.",
            "Everything's just a blur.",
            "My vision is fading.",
            "Can't see out of my left eye at all.",
        ],
        (25, 50): [  # Severe
            "My left eye is killing me.",
            "Can barely keep my eye open.",
            "Everything's blurry on the left.",
            "Vision's getting worse.",
        ],
        (50, 75): [  # Moderate
            "My eye hurts.",
            "Vision's a bit blurry.",
            "Left eye is throbbing.",
            "Hard to focus with this eye.",
        ],
    },
    "eye_right": {
        (0, 25): [
            "I can barely see anything.",
            "Everything's just a blur.",
            "My vision is fading.",
            "Can't see out of my right eye at all.",
        ],
        (25, 50): [
            "My right eye is killing me.",
            "Can barely keep my eye open.",
            "Everything's blurry on the right.",
            "Vision's getting worse.",
        ],
        (50, 75): [
            "My eye hurts.",
            "Vision's a bit blurry.",
            "Right eye is throbbing.",
            "Hard to focus with this eye.",
        ],
    },
    
    # === EARS ===
    "ear_left": {
        (0, 25): [
            "Can't hear anything on the left.",
            "Everything sounds muffled.",
            "The ringing won't stop.",
            "Deaf on one side.",
        ],
        (25, 50): [
            "My ear is killing me.",
            "Can barely hear on the left.",
            "Everything sounds distant.",
            "Hearing's getting worse.",
        ],
        (50, 75): [
            "My ear hurts.",
            "Sounds are muffled.",
            "Left ear is throbbing.",
            "Can't hear properly.",
        ],
    },
    "ear_right": {
        (0, 25): [
            "Can't hear anything on the right.",
            "Everything sounds muffled.",
            "The ringing won't stop.",
            "Deaf on one side.",
        ],
        (25, 50): [
            "My ear is killing me.",
            "Can barely hear on the right.",
            "Everything sounds distant.",
            "Hearing's getting worse.",
        ],
        (50, 75): [
            "My ear hurts.",
            "Sounds are muffled.",
            "Right ear is throbbing.",
            "Can't hear properly.",
        ],
    },
    
    # === LEGS ===
    "upper_leg_left": {
        (0, 25): [
            "Can't put weight on my left leg.",
            "My leg is useless.",
            "Can barely stand.",
            "Left leg won't hold me.",
        ],
        (25, 50): [
            "My leg is killing me.",
            "Every step is agony.",
            "Can barely walk.",
            "Left leg is on fire.",
        ],
        (50, 75): [
            "My leg hurts.",
            "Limping badly.",
            "Left leg is throbbing.",
            "Hard to walk straight.",
        ],
    },
    "upper_leg_right": {
        (0, 25): [
            "Can't put weight on my right leg.",
            "My leg is useless.",
            "Can barely stand.",
            "Right leg won't hold me.",
        ],
        (25, 50): [
            "My leg is killing me.",
            "Every step is agony.",
            "Can barely walk.",
            "Right leg is on fire.",
        ],
        (50, 75): [
            "My leg hurts.",
            "Limping badly.",
            "Right leg is throbbing.",
            "Hard to walk straight.",
        ],
    },
    "knee_left": {
        (0, 25): [
            "My knee is destroyed.",
            "Can't bend my left leg.",
            "Knee won't support me.",
            "Left knee is gone.",
        ],
        (25, 50): [
            "My knee is killing me.",
            "Can barely bend my leg.",
            "Every step shoots pain through my knee.",
            "Left knee is wrecked.",
        ],
        (50, 75): [
            "My knee hurts.",
            "Left knee is stiff.",
            "Hard to bend my leg.",
            "Knee is throbbing.",
        ],
    },
    "knee_right": {
        (0, 25): [
            "My knee is destroyed.",
            "Can't bend my right leg.",
            "Knee won't support me.",
            "Right knee is gone.",
        ],
        (25, 50): [
            "My knee is killing me.",
            "Can barely bend my leg.",
            "Every step shoots pain through my knee.",
            "Right knee is wrecked.",
        ],
        (50, 75): [
            "My knee hurts.",
            "Right knee is stiff.",
            "Hard to bend my leg.",
            "Knee is throbbing.",
        ],
    },
    "foot_left": {
        (0, 25): [
            "Can't feel my left foot.",
            "My foot is destroyed.",
            "Can't walk at all.",
            "Left foot is gone.",
        ],
        (25, 50): [
            "My foot is killing me.",
            "Every step is torture.",
            "Can barely put weight on it.",
            "Left foot is mangled.",
        ],
        (50, 75): [
            "My foot hurts.",
            "Left foot is throbbing.",
            "Hard to walk.",
            "Foot is swollen.",
        ],
    },
    "foot_right": {
        (0, 25): [
            "Can't feel my right foot.",
            "My foot is destroyed.",
            "Can't walk at all.",
            "Right foot is gone.",
        ],
        (25, 50): [
            "My foot is killing me.",
            "Every step is torture.",
            "Can barely put weight on it.",
            "Right foot is mangled.",
        ],
        (50, 75): [
            "My foot hurts.",
            "Right foot is throbbing.",
            "Hard to walk.",
            "Foot is swollen.",
        ],
    },
    
    # === ARMS ===
    "upper_arm_left": {
        (0, 25): [
            "My left arm is useless.",
            "Can't move my arm.",
            "Arm is destroyed.",
            "Left arm won't respond.",
        ],
        (25, 50): [
            "My arm is killing me.",
            "Can barely lift my left arm.",
            "Arm is on fire.",
            "Left arm is wrecked.",
        ],
        (50, 75): [
            "My arm hurts.",
            "Left arm is throbbing.",
            "Hard to lift my arm.",
            "Arm is stiff.",
        ],
    },
    "upper_arm_right": {
        (0, 25): [
            "My right arm is useless.",
            "Can't move my arm.",
            "Arm is destroyed.",
            "Right arm won't respond.",
        ],
        (25, 50): [
            "My arm is killing me.",
            "Can barely lift my right arm.",
            "Arm is on fire.",
            "Right arm is wrecked.",
        ],
        (50, 75): [
            "My arm hurts.",
            "Right arm is throbbing.",
            "Hard to lift my arm.",
            "Arm is stiff.",
        ],
    },
    "hand_left": {
        (0, 25): [
            "Can't feel my left hand.",
            "My hand is destroyed.",
            "Can't grip anything.",
            "Left hand is gone.",
        ],
        (25, 50): [
            "My hand is killing me.",
            "Can barely move my fingers.",
            "Can't grip properly.",
            "Left hand is mangled.",
        ],
        (50, 75): [
            "My hand hurts.",
            "Left hand is throbbing.",
            "Hard to hold things.",
            "Hand is swollen.",
        ],
    },
    "hand_right": {
        (0, 25): [
            "Can't feel my right hand.",
            "My hand is destroyed.",
            "Can't grip anything.",
            "Right hand is gone.",
        ],
        (25, 50): [
            "My hand is killing me.",
            "Can barely move my fingers.",
            "Can't grip properly.",
            "Right hand is mangled.",
        ],
        (50, 75): [
            "My hand hurts.",
            "Right hand is throbbing.",
            "Hard to hold things.",
            "Hand is swollen.",
        ],
    },
    
    # === TORSO ===
    "chest": {
        (0, 25): [
            "Can't breathe.",
            "My chest is crushed.",
            "Every breath is agony.",
            "Chest is destroyed.",
        ],
        (25, 50): [
            "Can't breathe right.",
            "My chest is on fire.",
            "Every breath hurts.",
            "Chest is wrecked.",
        ],
        (50, 75): [
            "My chest hurts.",
            "Hard to breathe deep.",
            "Chest is throbbing.",
            "Ribs are bruised.",
        ],
    },
    "stomach": {
        (0, 25): [
            "My gut is destroyed.",
            "Can't stand straight.",
            "Stomach is torn open.",
            "Everything hurts.",
        ],
        (25, 50): [
            "My stomach is killing me.",
            "Can barely move.",
            "Gut is on fire.",
            "Stomach is wrecked.",
        ],
        (50, 75): [
            "My stomach hurts.",
            "Gut is throbbing.",
            "Hard to stand straight.",
            "Stomach is bruised.",
        ],
    },
    "ribs": {
        (0, 25): [
            "My ribs are broken.",
            "Can't breathe without pain.",
            "Ribs are shattered.",
            "Chest is destroyed.",
        ],
        (25, 50): [
            "My ribs are killing me.",
            "Every breath hurts.",
            "Ribs are cracked.",
            "Chest is on fire.",
        ],
        (50, 75): [
            "My ribs hurt.",
            "Hard to breathe deep.",
            "Ribs are bruised.",
            "Chest is sore.",
        ],
    },
    
    # === HEAD ===
    "jaw": {
        (0, 25): [
            "My jaw is broken.",
            "Can't open my mouth.",
            "Jaw is shattered.",
            "Can't speak right.",
        ],
        (25, 50): [
            "My jaw is killing me.",
            "Can barely open my mouth.",
            "Jaw is cracked.",
            "Hard to talk.",
        ],
        (50, 75): [
            "My jaw hurts.",
            "Hard to chew.",
            "Jaw is throbbing.",
            "Mouth is sore.",
        ],
    },
    "nose": {
        (0, 25): [
            "My nose is broken.",
            "Can't breathe through my nose.",
            "Nose is shattered.",
            "Face is destroyed.",
        ],
        (25, 50): [
            "My nose is killing me.",
            "Can barely breathe.",
            "Nose is cracked.",
            "Face is on fire.",
        ],
        (50, 75): [
            "My nose hurts.",
            "Hard to breathe.",
            "Nose is throbbing.",
            "Face is swollen.",
        ],
    },
}


def get_injury_thought(colonist: "Colonist", game_tick: int) -> Optional[tuple[str, float]]:
    """Generate a thought about the colonist's worst injury.
    
    Returns:
        Tuple of (thought_text, mood_effect) or None if no significant injuries
    """
    body = getattr(colonist, 'body', None)
    if body is None:
        return None
    
    # Find the most damaged part that has thought templates
    worst_part = None
    worst_health = 100.0
    
    for part_id, part in body.parts.items():
        if part_id in INJURY_THOUGHTS and part.health < worst_health:
            worst_health = part.health
            worst_part = part_id
    
    # Only generate thoughts for significant injuries (< 75% health)
    if worst_part is None or worst_health >= 75:
        return None
    
    # Find appropriate severity range
    templates = INJURY_THOUGHTS[worst_part]
    thought_list = None
    
    for (min_health, max_health), thoughts in templates.items():
        if min_health <= worst_health < max_health:
            thought_list = thoughts
            break
    
    if thought_list is None:
        return None
    
    # Pick random thought from list
    thought_text = random.choice(thought_list)
    
    # Mood effect based on severity
    if worst_health < 25:
        mood_effect = -0.3  # Critical injury
    elif worst_health < 50:
        mood_effect = -0.2  # Severe injury
    else:
        mood_effect = -0.1  # Moderate injury
    
    return (thought_text, mood_effect)
