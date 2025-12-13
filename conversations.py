"""
Conversation system for Fractured City colonists.

Colonists have conversations when idle and nearby each other.
Conversations are based on:
- Shared traits (common ground)
- Mood states (checking in)
- Recent events (work, environment)
- Personality differences (clashes or curiosity)

Conversations appear in:
- Colony-wide chat log
- Individual colonist thought logs
"""

import random
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from colonist import Colonist

# =============================================================================
# CONVERSATION TEMPLATES
# =============================================================================

# Greetings - how conversations start
GREETINGS = [
    "{speaker} nods at {listener}.",
    "{speaker} glances over at {listener}.",
    "{speaker} catches {listener}'s eye.",
    "{speaker} walks up to {listener}.",
]

# Shared origin conversations
SHARED_ORIGIN_CONVERSATIONS = {
    "rust_warrens": [
        ('"{listener_first}, you ever miss the Warrens?"', '"Every damn day."'),
        ('"Remember the sound of the pipes at night?"', '"Hard to forget."'),
        ('"Warrens folk stick together."', '"Always have."'),
    ],
    "deep_shelters": [
        ('"The echoes here are different, right?"', '"Shallower. Less... alive."'),
        ('"Miss the shelter sometimes."', '"Miss the quiet, at least."'),
        ('"You feel that pressure shift?"', '"Yeah. Old habits."'),
    ],
    "topside_sprawl": [
        ('"Sky feels smaller down here."', '"Everything does."'),
        ('"Remember the bridges?"', '"Try not to."'),
        ('"Topside was something else."', '"Something else entirely."'),
    ],
    "signal_frontier": [
        ('"The static here is all wrong."', '"Too quiet."'),
        ('"You hear the old frequencies sometimes?"', '"When I listen hard enough."'),
        ('"Signal folk know things."', '"Things others don\'t want to."'),
    ],
    "fringe_settlements": [
        ('"This place has walls. Actual walls."', '"Luxury, right?"'),
        ('"Fringe taught us to survive."', '"Taught us everything."'),
        ('"Never thought I\'d miss the nothing."', '"The nothing was honest, at least."'),
    ],
    "wreck_yards": [
        ('"Good salvage around here."', '"If you know where to look."'),
        ('"Machines make more sense than people."', '"Always have."'),
        ('"Yards folk see potential in everything."', '"Even the broken stuff."'),
    ],
}

# Shared experience conversations
SHARED_EXPERIENCE_CONVERSATIONS = {
    "cortex_bloom_survivor": [
        ('"You survived a bloom too?"', '"Still seeing the ghost-light sometimes."'),
        ('"The bloom changed us."', '"Changed everything."'),
    ],
    "former_mercenary": [
        ('"You did contract work?"', '"Don\'t like to talk about it."'),
        ('"Old soldiers recognize each other."', '"Yeah. We do."'),
    ],
    "signal_diver": [
        ('"You dove the signals?"', '"Until they started diving back."'),
        ('"The interference speaks to you too?"', '"In its own way."'),
    ],
    "collapsed_block_escapee": [
        ('"You got out of a collapse?"', '"Barely. Still hear it sometimes."'),
        ('"We know what buildings sound like before they go."', '"A useful skill to have."'),
    ],
}

# Mood-based conversations
MOOD_CONVERSATIONS = {
    "Euphoric": [
        ('"You seem happy."', '"Things are good right now."'),
        ('"What\'s got you smiling?"', '"Just... feeling it today."'),
    ],
    "Calm": [
        ('"Peaceful day."', '"Could be worse."'),
        ('"How are you holding up?"', '"Can\'t complain."'),
    ],
    "Stressed": [
        ('"You okay?"', '"Just... a lot going on."'),
        ('"Take a breath."', '"Trying to."'),
        ('"Need to talk?"', '"Maybe later."'),
    ],
    "Overwhelmed": [
        ('"Hey. Hey. Look at me."', '"...yeah?"'),
        ('"One thing at a time."', '"Right. Right."'),
        ('"We\'re gonna get through this."', '"...okay."'),
    ],
}

# Work-related small talk
WORK_CONVERSATIONS = [
    ('"Busy day?"', '"Always is."'),
    ('"How\'s the work going?"', '"Getting there."'),
    ('"Need a hand?"', '"I got it. Thanks though."'),
    ('"Taking a break?"', '"Just for a minute."'),
    ('"Good work on that wall."', '"Thanks. Took forever."'),
    ('"You see what they built?"', '"Not bad, right?"'),
]

# General idle chatter
IDLE_CONVERSATIONS = [
    ('"Quiet today."', '"Too quiet, maybe."'),
    ('"You ever think about before?"', '"Try not to."'),
    ('"What do you think happens next?"', '"Same as always. We keep going."'),
    ('"Nice weather."', '"If you can call it that."'),
    ('"Hungry?"', '"Always."'),
    ('"Sleep well?"', '"Well enough."'),
    ('"Heard anything interesting?"', '"Just the usual."'),
    ('"You believe in luck?"', '"Believe in being prepared."'),
    ('"Miss anything from before?"', '"Everything. Nothing. Depends on the day."'),
    ('"Think we\'re safe here?"', '"Safe as anywhere."'),
]

# Injury check-in conversations
INJURY_CONVERSATIONS = [
    ('"Your eye... what happened?"', '"Fight got ugly."'),
    ('"You\'re limping."', '"I\'ll be fine."'),
    ('"That looks bad."', '"Seen worse."'),
    ('"You okay?"', '"Been better."'),
    ('"Need help?"', '"I can manage."'),
    ('"Should get that looked at."', '"When I have time."'),
    ('"You\'re hurt."', '"I noticed."'),
    ('"Can you even see out of that?"', '"Enough to get by."'),
    ('"Your hand..."', '"Still works. Mostly."'),
    ('"You need to rest."', '"Can\'t afford to."'),
]

# Fight aftermath conversations
FIGHT_AFTERMATH_CONVERSATIONS = [
    ('"Saw you and {other} going at it."', '"Don\'t want to talk about it."'),
    ('"That fight was brutal."', '"Yeah."'),
    ('"You two done?"', '"For now."'),
    ('"What was that about?"', '"Old tensions."'),
    ('"Heard the commotion."', '"It\'s handled."'),
    ('"You won, at least."', '"Doesn\'t feel like it."'),
    ('"They had it coming."', '"Maybe."'),
    ('"Glad you\'re okay."', '"Thanks."'),
]

# Quirk-triggered conversations (speaker has the quirk)
QUIRK_CONVERSATIONS = {
    "hums_when_thinking": [
        ('"What\'s that tune?"', '"Hmm? Oh. Didn\'t realize I was humming."'),
    ],
    "talks_to_machines": [
        ('"Were you... talking to that?"', '"It listens better than most people."'),
    ],
    "scavenges_trinkets": [
        ('"What\'d you find?"', '"Just a little something. Might be useful."'),
    ],
    "mild_paranoia": [
        ('"You keep looking around."', '"Just... being careful."'),
    ],
    "collects_stories": [
        ('"Tell me something."', '"What do you want to know?"'),
        ('"Got any good stories?"', '"Always."'),
    ],
    "gives_nicknames": [
        ('"Why do you call it that?"', '"Names make things real."'),
    ],
    "afraid_of_sky": [
        ('"You don\'t like being outside?"', '"Too much nothing up there."'),
    ],
    "afraid_of_tight_spaces": [
        ('"You okay in here?"', '"Just need some air."'),
    ],
}

# Major trait conversations (about the person with the trait)
MAJOR_TRAIT_CONVERSATIONS = {
    "echo_touched": [
        ('"You feel things others don\'t, huh?"', '"The echoes speak. I just listen."'),
        ('"What do the echoes say?"', '"Things that were. Things that might be."'),
    ],
    "rustborn": [
        ('"The interference doesn\'t bother you?"', '"Feels like home."'),
        ('"How do you stand the static?"', '"How do you stand the silence?"'),
    ],
    "pressure_blind": [
        ('"Doesn\'t this place feel dangerous to you?"', '"Feels fine to me."'),
        ('"You\'re not worried?"', '"Should I be?"'),
    ],
    "static_soul": [
        ('"You need the noise, don\'t you?"', '"Silence is deafening."'),
    ],
    "last_light_disciple": [
        ('"What do you believe in?"', '"The Last Light. It guides."'),
        ('"I see you praying sometimes."', '"Someone has to remember."'),
    ],
    "gravemind_listener": [
        ('"Who are you talking to?"', '"The deep ones. They remember."'),
        ('"You hear voices?"', '"Not voices. Memories."'),
    ],
    "ghost_memory_carrier": [
        ('"You okay? You looked far away."', '"Someone else\'s memory. It happens."'),
    ],
}

# Conflict conversations - triggered by trait clashes before fights
# Format: {(trait_a, trait_b): [(speaker_line, listener_line), ...]}
CONFLICT_CONVERSATIONS = {
    # Paranoia vs Talkers
    ("mild_paranoia", "overexplains"): [
        ('"Can you just... stop talking?"', '"I\'m just trying to help!"'),
        ('"Do you ever shut up?"', '"I\'m explaining things!"'),
        ('"Too many words."', '"You need to understand—"'),
        ('"Give me some space."', '"I\'m just standing here!"'),
    ],
    ("mild_paranoia", "gives_nicknames"): [
        ('"Don\'t call me that."', '"It\'s just a nickname!"'),
        ('"Stop acting so familiar."', '"We\'re friends, aren\'t we?"'),
        ('"I don\'t like nicknames."', '"Lighten up a little."'),
    ],
    
    # Sky fear vs Outside lovers
    ("afraid_of_sky", "topside_sprawl"): [
        ('"How can you stand it out there?"', '"Better than hiding like a coward."'),
        ('"All that... nothing above us."', '"It\'s called freedom."'),
        ('"The sky is wrong."', '"You\'re wrong."'),
    ],
    
    # Claustrophobia vs Underground
    ("afraid_of_tight_spaces", "deep_shelters"): [
        ('"These walls are closing in."', '"This is nothing. You should see the shelters."'),
        ('"I need air."', '"We\'re fine."'),
        ('"Too cramped in here."', '"You\'re being dramatic."'),
    ],
    
    # Light sleeper vs Noisy
    ("sleeps_lightly", "hums_when_thinking"): [
        ('"That humming. Please stop."', '"Didn\'t realize I was doing it."'),
        ('"Can\'t sleep with all that noise."', '"I\'m barely making a sound!"'),
        ('"You\'re too loud."', '"You\'re too sensitive."'),
    ],
    
    # Organizer vs Hoarder
    ("keeps_inventory", "scavenges_trinkets"): [
        ('"Why do you keep all this junk?"', '"It\'s not junk!"'),
        ('"This place is a mess."', '"I know where everything is."'),
        ('"Throw it out."', '"You don\'t understand."'),
    ],
    
    # Slow vs Efficient
    ("takes_long_path", "former_mercenary"): [
        ('"Why do you always rush?"', '"Why do you always waste time?"'),
        ('"There\'s value in being careful."', '"There\'s value in getting things done."'),
        ('"Not everything is a mission."', '"Everything is."'),
    ],
    
    # Belief conflicts
    ("last_light_disciple", "gravemind_listener"): [
        ('"Your voices are lies."', '"Your light is dead."'),
        ('"The Last Light guides."', '"The deep ones remember."'),
        ('"You worship nothing."', '"You worship a corpse."'),
    ],
    
    # Connection conflicts
    ("echo_touched", "unlinked"): [
        ('"You feel nothing."', '"I feel plenty. Just not your echoes."'),
        ('"You\'re cut off."', '"I\'m free."'),
        ('"The echoes connect us all."', '"I don\'t want to be connected."'),
    ],
    
    # Noise conflicts
    ("static_soul", "silent_commune_raised"): [
        ('"The silence is suffocating."', '"The noise is maddening."'),
        ('"I need the static."', '"I need the quiet."'),
        ('"How can you stand it so quiet?"', '"How can you stand all that noise?"'),
    ],
    
    # Origin tensions
    ("rust_warrens", "deep_shelters"): [
        ('"Surface scavenger."', '"At least I saw the sky."'),
        ('"You don\'t know real darkness."', '"You don\'t know real danger."'),
        ('"Warrens folk are tougher."', '"Shelter folk are smarter."'),
    ],
    ("topside_sprawl", "fringe_settlements"): [
        ('"City folk don\'t know survival."', '"Fringe folk don\'t know civilization."'),
        ('"The sprawl made us weak."', '"The fringe made you animals."'),
        ('"You wouldn\'t last a day topside."', '"You wouldn\'t last an hour on the fringe."'),
    ],
}


# =============================================================================
# CONVERSATION LOG - Per-colonist perspective
# =============================================================================

# Store conversations per colonist: {colonist_id: [conversation_entries]}
_colonist_conversation_logs: dict[int, list[dict]] = {}
_max_log_entries = 100


def add_conversation(speaker_name: str, listener_name: str, 
                     speaker_line: str, listener_line: str,
                     game_tick: int, conversation_type: str = "chat",
                     speaker_id: int = None, listener_id: int = None) -> None:
    """Add a conversation to both participants' logs from their perspective.
    
    Args:
        speaker_name: Name of colonist who initiated
        listener_name: Name of colonist who responded
        speaker_line: What the speaker said
        listener_line: What the listener replied
        game_tick: Current game tick
        conversation_type: "chat", "shared_origin", "shared_experience", "mood", "work", "quirk", "major", "conflict", "injury_checkin", "fight_aftermath"
        speaker_id: ID of speaker colonist (for per-colonist log)
        listener_id: ID of listener colonist (for per-colonist log)
    """
    global _colonist_conversation_logs
    
    # Add to speaker's log (they spoke first)
    if speaker_id is not None:
        if speaker_id not in _colonist_conversation_logs:
            _colonist_conversation_logs[speaker_id] = []
        
        speaker_entry = {
            "tick": game_tick,
            "is_speaker": True,
            "other_name": listener_name,
            "my_line": speaker_line,
            "their_line": listener_line,
            "type": conversation_type,
        }
        _colonist_conversation_logs[speaker_id].append(speaker_entry)
        
        # Trim if too long
        if len(_colonist_conversation_logs[speaker_id]) > _max_log_entries:
            _colonist_conversation_logs[speaker_id] = _colonist_conversation_logs[speaker_id][-_max_log_entries:]
    
    # Add to listener's log (they responded)
    if listener_id is not None:
        if listener_id not in _colonist_conversation_logs:
            _colonist_conversation_logs[listener_id] = []
        
        listener_entry = {
            "tick": game_tick,
            "is_speaker": False,
            "other_name": speaker_name,
            "my_line": listener_line,
            "their_line": speaker_line,
            "type": conversation_type,
        }
        _colonist_conversation_logs[listener_id].append(listener_entry)
        
        # Trim if too long
        if len(_colonist_conversation_logs[listener_id]) > _max_log_entries:
            _colonist_conversation_logs[listener_id] = _colonist_conversation_logs[listener_id][-_max_log_entries:]


def get_conversation_log(colonist_id: int, limit: int = 20) -> list[dict]:
    """Get recent conversations from a specific colonist's perspective.
    
    Args:
        colonist_id: ID of the colonist whose log to retrieve
        limit: Maximum number of conversations to return
        
    Returns:
        List of conversation entries from this colonist's perspective, most recent first
    """
    if colonist_id not in _colonist_conversation_logs:
        return []
    
    return list(reversed(_colonist_conversation_logs[colonist_id][-limit:]))


def clear_conversation_log() -> None:
    """Clear the conversation log."""
    global _conversation_log
    _conversation_log = []


# =============================================================================
# CONVERSATION GENERATION
# =============================================================================

def generate_conversation(speaker: "Colonist", listener: "Colonist", 
                          game_tick: int) -> Optional[tuple[str, str, str]]:
    """Generate a conversation between two colonists.
    
    Returns tuple of (speaker_line, listener_line, conversation_type) or None.
    """
    # Check for recent events first (most contextual)
    
    # Check if listener has visible injuries (health < 75%)
    listener_body = getattr(listener, 'body', None)
    if listener_body and random.random() < 0.4:  # 40% chance to comment on injuries
        # Find worst injury
        worst_health = 100.0
        for part in listener_body.parts.values():
            if part.health < worst_health:
                worst_health = part.health
        
        if worst_health < 75:
            speaker_line, listener_line = random.choice(INJURY_CONVERSATIONS)
            return (speaker_line, listener_line, "injury_checkin")
    
    # Check if listener was recently in combat (last 3000 ticks = ~50 seconds)
    listener_last_combat = getattr(listener, 'last_combat_tick', 0)
    if game_tick - listener_last_combat < 3000 and random.random() < 0.3:
        # Find who they fought
        recent_target = getattr(listener, 'combat_target', None)
        if recent_target:
            other_name = recent_target.name.split()[0]
            speaker_line, listener_line = random.choice(FIGHT_AFTERMATH_CONVERSATIONS)
            speaker_line = speaker_line.format(other=other_name)
            return (speaker_line, listener_line, "fight_aftermath")
    
    # Check for shared traits (more interesting)
    
    # Shared origin?
    speaker_origin = speaker.traits.get("origin", "")
    listener_origin = listener.traits.get("origin", "")
    if speaker_origin and speaker_origin == listener_origin:
        if speaker_origin in SHARED_ORIGIN_CONVERSATIONS:
            templates = SHARED_ORIGIN_CONVERSATIONS[speaker_origin]
            if templates and random.random() < 0.3:  # 30% chance to use shared origin
                speaker_line, listener_line = random.choice(templates)
                speaker_line = speaker_line.format(
                    listener_first=listener.name.split()[0]
                )
                return (speaker_line, listener_line, "shared_origin")
    
    # Shared experience?
    speaker_exp = speaker.traits.get("experience", "")
    listener_exp = listener.traits.get("experience", "")
    if speaker_exp and speaker_exp == listener_exp:
        if speaker_exp in SHARED_EXPERIENCE_CONVERSATIONS:
            templates = SHARED_EXPERIENCE_CONVERSATIONS[speaker_exp]
            if templates and random.random() < 0.25:
                speaker_line, listener_line = random.choice(templates)
                return (speaker_line, listener_line, "shared_experience")
    
    # Speaker has a major trait?
    speaker_major = speaker.traits.get("major_trait", "")
    if speaker_major and speaker_major in MAJOR_TRAIT_CONVERSATIONS:
        if random.random() < 0.2:  # 20% chance
            templates = MAJOR_TRAIT_CONVERSATIONS[speaker_major]
            speaker_line, listener_line = random.choice(templates)
            return (speaker_line, listener_line, "major")
    
    # Listener has a major trait? (speaker asks about it)
    listener_major = listener.traits.get("major_trait", "")
    if listener_major and listener_major in MAJOR_TRAIT_CONVERSATIONS:
        if random.random() < 0.15:
            templates = MAJOR_TRAIT_CONVERSATIONS[listener_major]
            # Swap - speaker asks, listener answers
            listener_line, speaker_line = random.choice(templates)
            return (speaker_line, listener_line, "major")
    
    # Speaker has a quirk that triggers conversation?
    for quirk in speaker.traits.get("quirks", []):
        if quirk in QUIRK_CONVERSATIONS and random.random() < 0.15:
            templates = QUIRK_CONVERSATIONS[quirk]
            # Listener notices speaker's quirk
            listener_line, speaker_line = random.choice(templates)
            return (speaker_line, listener_line, "quirk")
    
    # Mood-based conversation?
    listener_mood = listener.mood_state
    if listener_mood in MOOD_CONVERSATIONS:
        if listener_mood in ("Stressed", "Overwhelmed") and random.random() < 0.3:
            # More likely to check in on stressed colonists
            templates = MOOD_CONVERSATIONS[listener_mood]
            speaker_line, listener_line = random.choice(templates)
            return (speaker_line, listener_line, "mood")
        elif random.random() < 0.1:
            templates = MOOD_CONVERSATIONS[listener_mood]
            speaker_line, listener_line = random.choice(templates)
            return (speaker_line, listener_line, "mood")
    
    # Work conversation?
    if random.random() < 0.2:
        speaker_line, listener_line = random.choice(WORK_CONVERSATIONS)
        return (speaker_line, listener_line, "work")
    
    # Default: idle chatter
    speaker_line, listener_line = random.choice(IDLE_CONVERSATIONS)
    return (speaker_line, listener_line, "chat")


def generate_conflict_conversation(colonist_a: "Colonist", colonist_b: "Colonist") -> Optional[tuple[str, str]]:
    """Generate a conflict conversation based on trait clash.
    
    Returns tuple of (speaker_line, listener_line) or None if no conflict found.
    """
    traits_a = getattr(colonist_a, 'traits', {})
    traits_b = getattr(colonist_b, 'traits', {})
    
    # Collect all traits
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
    
    # Find matching conflict conversation
    for trait_a in all_traits_a:
        for trait_b in all_traits_b:
            # Check both orderings
            key = (trait_a, trait_b)
            if key in CONFLICT_CONVERSATIONS:
                templates = CONFLICT_CONVERSATIONS[key]
                return random.choice(templates)
            
            key_reversed = (trait_b, trait_a)
            if key_reversed in CONFLICT_CONVERSATIONS:
                templates = CONFLICT_CONVERSATIONS[key_reversed]
                # Swap speaker and listener
                listener_line, speaker_line = random.choice(templates)
                return (speaker_line, listener_line)
    
    return None


def try_start_conversation(speaker: "Colonist", listener: "Colonist",
                           game_tick: int) -> bool:
    """Try to start a conversation between two colonists.
    
    Returns True if conversation happened.
    """
    # Don't talk to yourself
    if speaker is listener:
        return False
    
    # Both must be alive
    if speaker.is_dead or listener.is_dead:
        return False
    
    # Both should be idle or nearly idle
    if speaker.state not in ("idle",) or listener.state not in ("idle",):
        return False
    
    # Must be on same Z level and within range
    if speaker.z != listener.z:
        return False
    
    dx = abs(speaker.x - listener.x)
    dy = abs(speaker.y - listener.y)
    if max(dx, dy) > 3:  # Conversation range
        return False
    
    # Check cooldown (stored on speaker)
    last_convo = getattr(speaker, '_last_conversation_tick', 0)
    if game_tick - last_convo < 600:  # ~10 seconds cooldown
        return False
    
    # Generate conversation
    result = generate_conversation(speaker, listener, game_tick)
    if result is None:
        return False
    
    speaker_line, listener_line, convo_type = result
    
    # Add to per-colonist logs
    add_conversation(
        speaker.name, listener.name,
        speaker_line, listener_line,
        game_tick, convo_type,
        speaker_id=id(speaker), listener_id=id(listener)
    )
    
    # Record interaction in relationship system
    from relationships import record_interaction, get_relationship
    is_positive = convo_type not in ("argument", "conflict")
    record_interaction(speaker, listener, game_tick, positive=is_positive)
    
    # Get relationship for mood effect scaling
    rel = get_relationship(speaker, listener)
    base_mood = 0.05
    if rel["score"] >= 50:
        base_mood = 0.1  # Friends enjoy talking more
    elif rel["score"] <= -30:
        base_mood = -0.05  # Rivals don't enjoy it
    
    # Add thoughts to both colonists
    speaker_first = speaker.name.split()[0]
    listener_first = listener.name.split()[0]
    
    # Speaker's thought
    speaker.add_thought(
        "social",
        f"Talked with {listener_first}.",
        mood_effect=base_mood,
        game_tick=game_tick
    )
    
    # Listener's thought
    listener.add_thought(
        "social",
        f"Chatted with {speaker_first}.",
        mood_effect=base_mood,
        game_tick=game_tick
    )
    
    # Set cooldown
    speaker._last_conversation_tick = game_tick
    listener._last_conversation_tick = game_tick
    
    return True
