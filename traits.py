"""
Trait system for Fractured City colonists.

Each colonist gets: 1 Origin + 1 Experience + 1-2 Quirks + (rare) 1 Major Trait

Traits modify:
- Starting affinities (interference, echo, pressure, integrity, outside, crowding)
- Job speed modifiers (build, haul, craft, cook, scavenge)
- Thought flavor text
- Backstory generation
"""

import random
from typing import Optional

# =============================================================================
# TRAIT COLORS - For UI highlighting (RGB tuples)
# =============================================================================

TRAIT_COLORS = {
    "origin": (150, 200, 255),      # Light blue - where you're from
    "experience": (255, 200, 150),  # Warm orange - what shaped you
    "quirk": (180, 180, 180),       # Gray - behavioral flavor
    "major": (255, 215, 100),       # Gold - rare powerful traits
}

# =============================================================================
# ORIGINS - Where they came from (pick 1)
# =============================================================================

ORIGINS = {
    "rust_warrens": {
        "label": "Rust Warrens",
        "bio": "Grew up in the Rust Warrens, where metal groans louder than people.",
        "affinities": {"interference": 0.3, "integrity": -0.2},
        "job_mods": {"scavenge": 0.1},
        "thoughts": {
            "idle": [
                "The rust here smells like home.",
                "Metal always tells you when it's about to give.",
                "Quieter than the Warrens. Almost unsettling.",
            ],
            "environment": [
                "This interference feels familiar.",
                "Solid ground. Didn't have much of that growing up.",
            ],
        },
    },
    "deep_shelters": {
        "label": "Deep Shelters",
        "bio": "Emerged from the deep shelters beneath the old metro lines.",
        "affinities": {"echo": 0.3, "pressure": 0.2, "outside": -0.3},
        "job_mods": {"craft": 0.1},
        "thoughts": {
            "idle": [
                "The echoes down here are different. Shallower.",
                "Miss the hum of the deep vents.",
                "Too much sky. Too much nothing above.",
            ],
            "environment": [
                "Can feel the pressure shifting.",
                "The echoes here have stories.",
            ],
        },
    },
    "topside_sprawl": {
        "label": "Topside Sprawl",
        "bio": "Born topside under fractured sky bridges and broken light.",
        "affinities": {"outside": 0.4, "crowding": -0.2},
        "job_mods": {"haul": 0.1},
        "thoughts": {
            "idle": [
                "Used to watch the bridges sway in the wind.",
                "Light's different down here. Heavier.",
                "Need to see the sky sometimes.",
            ],
            "environment": [
                "Open air. That's more like it.",
                "Walls closing in. Don't like it.",
            ],
        },
    },
    "signal_frontier": {
        "label": "Signal Frontier",
        "bio": "Raised near the old signal towers where the static sang.",
        "affinities": {"interference": 0.4, "echo": 0.2},
        "job_mods": {"craft": 0.15},
        "thoughts": {
            "idle": [
                "The static here is too quiet.",
                "Used to fall asleep to the signal hum.",
                "Towers taught me to listen between the noise.",
            ],
            "environment": [
                "Good interference. Feels alive.",
                "Can almost hear the old frequencies.",
            ],
        },
    },
    "fringe_settlements": {
        "label": "The Fringe",
        "bio": "Lived in the Fringe, far from water, food, and safety.",
        "affinities": {"pressure": 0.3, "integrity": 0.1},
        "job_mods": {"scavenge": 0.15, "haul": 0.1},
        "thoughts": {
            "idle": [
                "This is luxury compared to the Fringe.",
                "Always watching the horizon out there.",
                "Learned to make do with nothing.",
            ],
            "environment": [
                "Pressure's building. Stay sharp.",
                "Feels exposed. Old habits.",
            ],
        },
    },
    "wreck_yards": {
        "label": "Wreck Yards",
        "bio": "Grew up stripping parts from dead machines.",
        "affinities": {"integrity": 0.3, "interference": 0.1},
        "job_mods": {"craft": 0.2, "build": 0.1},
        "thoughts": {
            "idle": [
                "Everything here could be useful.",
                "Machines have a logic. People don't.",
                "Good salvage nearby. Can feel it.",
            ],
            "environment": [
                "Solid construction. Respect that.",
                "This place is falling apart. Could fix it.",
            ],
        },
    },
}

# =============================================================================
# EXPERIENCES - Formative life events (pick 1)
# =============================================================================

EXPERIENCES = {
    "cortex_bloom_survivor": {
        "label": "Cortex Bloom Survivor",
        "bio": "Survived a cortex bloom when the sky lit up with ghost-light.",
        "affinities": {"echo": 0.4},
        "job_mods": {"craft": 0.1},
        "stat_mods": {"focus": 0.1},
        "thoughts": {
            "idle": [
                "Sometimes still see the ghost-light when I close my eyes.",
                "The bloom changed something. Can't explain what.",
                "Others who survived... we know things.",
            ],
            "mood": [
                "Head's clear today. Bloom's quiet.",
                "The echoes are louder. Bloom days.",
            ],
        },
    },
    "former_mercenary": {
        "label": "Former Mercenary",
        "bio": "Did contract work in the border riots.",
        "affinities": {"pressure": 0.3, "crowding": -0.3},
        "job_mods": {"haul": 0.1},
        "stat_mods": {"intimidation": 0.2},
        "thoughts": {
            "idle": [
                "Seen worse. Done worse.",
                "Old instincts never really leave.",
                "Peace is just the space between contracts.",
            ],
            "social": [
                "Don't crowd me.",
                "Watching everyone. Can't help it.",
            ],
        },
    },
    "signal_diver": {
        "label": "Signal Diver",
        "bio": "Worked the comm relays until the interference changed them.",
        "affinities": {"interference": 0.5, "echo": 0.2},
        "job_mods": {"craft": 0.15},
        "stat_mods": {"hearing": 0.15},
        "thoughts": {
            "idle": [
                "The signals are different now. Alive, almost.",
                "Spent years listening. Hard to stop.",
                "Interference has patterns if you know how to look.",
            ],
            "environment": [
                "Strong signal here. Interesting.",
                "Dead zone. Hate the silence.",
            ],
        },
    },
    "collapsed_block_escapee": {
        "label": "Collapsed Block Escapee",
        "bio": "Escaped a collapsing high-rise with seconds to spare.",
        "affinities": {"integrity": 0.5, "pressure": 0.2},
        "job_mods": {"build": 0.15},
        "stat_mods": {"walk_steady": 0.1},
        "thoughts": {
            "idle": [
                "Always checking the walls now.",
                "Know the sounds a building makes before it goes.",
                "Got out. Others didn't.",
            ],
            "environment": [
                "Structure's solid. Good.",
                "This place feels unstable. Don't like it.",
            ],
        },
    },
    "floodlight_displaced": {
        "label": "Floodlight Displaced",
        "bio": "Was displaced when the Floodlights swept the district clean.",
        "affinities": {"outside": 0.3},
        "job_mods": {"scavenge": 0.15, "haul": 0.1},
        "thoughts": {
            "idle": [
                "Lost everything to the lights.",
                "Keep moving. That's how you survive.",
                "Home is wherever you stop running.",
            ],
            "work": [
                "Scavenging's second nature now.",
                "Carry what matters. Leave the rest.",
            ],
        },
    },
    "machine_gravekeeper": {
        "label": "Machine Gravekeeper",
        "bio": "Used to maintain abandoned server vaults no one else would touch.",
        "affinities": {"echo": 0.3, "crowding": -0.2},
        "job_mods": {"craft": 0.2},
        "thoughts": {
            "idle": [
                "Machines remember things. Even dead ones.",
                "Prefer the company of servers, honestly.",
                "The vaults were peaceful. Miss that.",
            ],
            "work": [
                "Good craftsmanship. Machines deserve care.",
                "Sloppy work. Wouldn't last a week in the vaults.",
            ],
        },
    },
    "heatline_runner": {
        "label": "Heatline Runner",
        "bio": "Ran supplies across thermal ruptures before the towers fell.",
        "affinities": {"pressure": 0.4},
        "job_mods": {"haul": 0.2},
        "stat_mods": {"walk_speed": 0.1, "cooling": 0.1},
        "thoughts": {
            "idle": [
                "Used to run the heatlines. This is nothing.",
                "Speed kept me alive. Still does.",
                "Miss the rush, honestly.",
            ],
            "work": [
                "Light load. Easy run.",
                "Heavy haul. Good workout.",
            ],
        },
    },
    "silent_commune_raised": {
        "label": "Silent Commune Raised",
        "bio": "Spent years in a quiet commune beneath the vents.",
        "affinities": {"crowding": -0.4, "pressure": -0.2},
        "job_mods": {},
        "stat_mods": {"stress_resist": 0.2},
        "thoughts": {
            "idle": [
                "Too loud here. Too many voices.",
                "The commune taught stillness. Hard to unlearn.",
                "Silence has its own language.",
            ],
            "social": [
                "Words feel wasteful sometimes.",
                "Prefer to listen.",
            ],
        },
    },
}

# =============================================================================
# QUIRKS - Personality color (pick 1-2)
# =============================================================================

QUIRKS = {
    "hums_when_thinking": {
        "label": "Hums When Thinking",
        "bio": "Hums tunelessly when deep in thought.",
        "thoughts": ["Hmm hmm hmm...", "That melody again. Where's it from?"],
    },
    "talks_to_machines": {
        "label": "Talks to Machines",
        "bio": "Has conversations with machines and tools.",
        "thoughts": ["Come on, work with me here.", "Good machine. Reliable."],
    },
    "scavenges_trinkets": {
        "label": "Scavenges Trinkets",
        "bio": "Collects small objects others overlook.",
        "thoughts": ["Ooh, shiny.", "This could be useful. Probably.", "Adding to the collection."],
    },
    "mild_paranoia": {
        "label": "Mildly Paranoid",
        "bio": "Always watching, always listening.",
        "affinities": {"pressure": 0.1},
        "thoughts": ["Something's off.", "Who's watching?", "Trust no one completely."],
    },
    "collects_stories": {
        "label": "Collects Stories",
        "bio": "Remembers every story they've ever heard.",
        "thoughts": ["Reminds me of a story...", "Should write this down.", "Everyone has a story."],
    },
    "sleeps_lightly": {
        "label": "Sleeps Lightly",
        "bio": "Wakes at the slightest sound.",
        "thoughts": ["Never really sleep. Just rest.", "Heard something. Probably nothing."],
    },
    "stares_into_pipes": {
        "label": "Stares Into Pipes",
        "bio": "Gets lost staring into pipes and vents.",
        "affinities": {"echo": 0.1},
        "thoughts": ["Wonder where that goes...", "The pipes know things.", "Could listen to that flow forever."],
    },
    "whispers_to_echoes": {
        "label": "Whispers to Echoes",
        "bio": "Sometimes whispers back to strange sounds.",
        "affinities": {"echo": 0.15},
        "thoughts": ["Did you hear that?", "Just answering.", "The echoes talk if you listen."],
    },
    "keeps_inventory": {
        "label": "Keeps Inventory",
        "bio": "Mentally catalogs everything nearby.",
        "thoughts": ["Three of those, two of these...", "Need to reorganize.", "Everything in its place."],
    },
    "wont_eat_cold": {
        "label": "Won't Eat Cold Food",
        "bio": "Refuses to eat anything that isn't warm.",
        "thoughts": ["Cold food is barely food.", "Needs heat. Standards matter."],
    },
    "overexplains": {
        "label": "Overexplains Everything",
        "bio": "Uses ten words when one would do.",
        "thoughts": ["Let me elaborate...", "To be more specific...", "What I mean is..."],
    },
    "gives_nicknames": {
        "label": "Gives Nicknames",
        "bio": "Gives everything and everyone a nickname.",
        "thoughts": ["Gonna call this one Rusty.", "That's a good name for it.", "Names make things real."],
    },
    "takes_long_path": {
        "label": "Takes the Long Path",
        "bio": "Prefers scenic routes over shortcuts.",
        "thoughts": ["No rush.", "The long way has better views.", "Shortcuts miss the point."],
    },
    "afraid_of_sky": {
        "label": "Afraid of Open Sky",
        "bio": "Gets nervous under open sky.",
        "affinities": {"outside": -0.3},
        "thoughts": ["Too much nothing up there.", "Need a roof. Any roof.", "Sky feels like falling."],
    },
    "afraid_of_tight_spaces": {
        "label": "Claustrophobic",
        "bio": "Panics in tight enclosed spaces.",
        "affinities": {"outside": 0.3},
        "thoughts": ["Walls too close.", "Need air. Need out.", "Can't breathe in here."],
    },
}

# =============================================================================
# MAJOR TRAITS - Rare, strong identity flags (2-5% chance, pick 0-1)
# =============================================================================

MAJOR_TRAITS = {
    "echo_touched": {
        "label": "Echo-Touched",
        "bio": "Seems to feel resonance others can't perceive.",
        "affinities": {"echo": 0.6},
        "job_mods": {"craft": 0.2},
        "stat_mods": {"echo_sense": 0.3},
        "rare": True,
        "thoughts": {
            "idle": [
                "The echoes are speaking again.",
                "Can feel the resonance in my teeth.",
                "Others don't hear it. That's fine.",
            ],
            "environment": [
                "Strong echo here. It's... beautiful.",
                "Dead zone. Like going deaf.",
            ],
        },
    },
    "rustborn": {
        "label": "Rustborn",
        "bio": "Practically immune to interference stress.",
        "affinities": {"interference": 0.7, "crowding": -0.2},
        "job_mods": {"scavenge": 0.2, "craft": 0.1},
        "stat_mods": {"stress_resist": 0.2},
        "rare": True,
        "thoughts": {
            "idle": [
                "Interference feels like home.",
                "Static's just another kind of quiet.",
                "Born in the rust. It's in my blood.",
            ],
            "environment": [
                "Good static. Comforting.",
                "Too clean here. Sterile.",
            ],
        },
    },
    "pressure_blind": {
        "label": "Pressure-Blind",
        "bio": "Doesn't perceive danger properly — calm or reckless.",
        "affinities": {"pressure": -0.5},
        "job_mods": {"haul": 0.15},
        "stat_mods": {"stress_resist": 0.3},
        "rare": True,
        "thoughts": {
            "idle": [
                "Everyone's so tense. Why?",
                "Danger? What danger?",
                "Calm is easy when you can't feel the pressure.",
            ],
            "environment": [
                "Seems fine to me.",
                "Others are worried. I'm not.",
            ],
        },
    },
    "static_soul": {
        "label": "Static-Soul",
        "bio": "Finds clarity in interference; hates silence.",
        "affinities": {"interference": 0.8},
        "job_mods": {"craft": 0.15},
        "rare": True,
        "thoughts": {
            "idle": [
                "The static helps me think.",
                "Silence is deafening.",
                "Need the noise. Need it.",
            ],
            "environment": [
                "Perfect interference. Crystal clear.",
                "Too quiet. Can't focus.",
            ],
        },
    },
    "last_light_disciple": {
        "label": "Last-Light Disciple",
        "bio": "Follows a strange ritualistic worldview; prays during idle time.",
        "affinities": {"echo": 0.3, "pressure": 0.2},
        "job_mods": {},
        "stat_mods": {"stress_resist": 0.15},
        "rare": True,
        "thoughts": {
            "idle": [
                "The Last Light guides.",
                "Prayers for the fallen towers.",
                "Everything has meaning. Everything.",
            ],
            "mood": [
                "The Light provides clarity.",
                "Dark times. Must have faith.",
            ],
        },
    },
    "gravemind_listener": {
        "label": "Gravemind Listener",
        "bio": "Claims to hear voices in deep infrastructure; unnerving but insightful.",
        "affinities": {"echo": 0.5, "crowding": -0.3},
        "job_mods": {"craft": 0.1},
        "stat_mods": {"echo_sense": 0.4},
        "rare": True,
        "thoughts": {
            "idle": [
                "The deep ones are whispering again.",
                "They remember things we've forgotten.",
                "Not crazy. Just... listening.",
            ],
            "environment": [
                "Voices here. Old ones.",
                "Silent. They've moved on.",
            ],
        },
    },
    "ghost_memory_carrier": {
        "label": "Ghost Memory Carrier",
        "bio": "Has fragments of someone else's memories (neural artifact).",
        "affinities": {"echo": 0.4},
        "job_mods": {},
        "rare": True,
        "thoughts": {
            "idle": [
                "That memory isn't mine. Whose is it?",
                "Sometimes I remember places I've never been.",
                "Two lives in one head.",
            ],
            "mood": [
                "The other memories are quiet today.",
                "Hard to tell which feelings are mine.",
            ],
        },
    },
    "unlinked": {
        "label": "Unlinked",
        "bio": "Nervous system doesn't sync with implants; resistant but stable.",
        "affinities": {"interference": -0.3},
        "job_mods": {},
        "stat_mods": {"stress_resist": 0.25},
        "rare": True,
        "thoughts": {
            "idle": [
                "Implants never took. Blessing or curse?",
                "My head's my own, at least.",
                "Unlinked and unbothered.",
            ],
            "environment": [
                "Interference doesn't touch me the same way.",
                "Others feel it more. I just watch.",
            ],
        },
    },
}


# =============================================================================
# TRAIT GENERATION FUNCTIONS
# =============================================================================

def generate_traits() -> dict:
    """Generate a random trait set for a new colonist.
    
    Returns dict with:
        origin: str (key from ORIGINS)
        experience: str (key from EXPERIENCES)
        quirks: list[str] (1-2 keys from QUIRKS)
        major_trait: str or None (key from MAJOR_TRAITS, ~5% chance)
    """
    # Pick 1 origin
    origin = random.choice(list(ORIGINS.keys()))
    
    # Pick 1 experience
    experience = random.choice(list(EXPERIENCES.keys()))
    
    # Pick 1-2 quirks
    num_quirks = random.choices([1, 2], weights=[0.6, 0.4])[0]
    quirks = random.sample(list(QUIRKS.keys()), num_quirks)
    
    # 5% chance of major trait
    major_trait = None
    if random.random() < 0.05:
        major_trait = random.choice(list(MAJOR_TRAITS.keys()))
    
    return {
        "origin": origin,
        "experience": experience,
        "quirks": quirks,
        "major_trait": major_trait,
    }


def get_trait_data(trait_key: str) -> Optional[dict]:
    """Get trait data by key, searching all categories."""
    if trait_key in ORIGINS:
        return ORIGINS[trait_key]
    if trait_key in EXPERIENCES:
        return EXPERIENCES[trait_key]
    if trait_key in QUIRKS:
        return QUIRKS[trait_key]
    if trait_key in MAJOR_TRAITS:
        return MAJOR_TRAITS[trait_key]
    return None


def generate_backstory(traits: dict) -> str:
    """Generate a backstory string from trait set.
    
    Format: "[Origin bio] [Experience bio] [Quirk bios] [Major trait bio]"
    """
    parts = []
    
    # Origin
    origin_data = ORIGINS.get(traits.get("origin", ""))
    if origin_data:
        parts.append(origin_data["bio"])
    
    # Experience
    exp_data = EXPERIENCES.get(traits.get("experience", ""))
    if exp_data:
        parts.append(exp_data["bio"])
    
    # Quirks
    for quirk_key in traits.get("quirks", []):
        quirk_data = QUIRKS.get(quirk_key)
        if quirk_data:
            parts.append(quirk_data["bio"])
    
    # Major trait
    major_key = traits.get("major_trait")
    if major_key:
        major_data = MAJOR_TRAITS.get(major_key)
        if major_data:
            parts.append(major_data["bio"])
    
    return " ".join(parts)


def get_combined_affinities(traits: dict) -> dict[str, float]:
    """Get combined affinity modifiers from all traits.
    
    Returns dict like: {"interference": 0.5, "echo": 0.3, ...}
    """
    combined = {
        "interference": 0.0,
        "echo": 0.0,
        "pressure": 0.0,
        "integrity": 0.0,
        "outside": 0.0,
        "crowding": 0.0,
    }
    
    # Collect from all trait sources
    sources = [
        ORIGINS.get(traits.get("origin", "")),
        EXPERIENCES.get(traits.get("experience", "")),
    ]
    for quirk_key in traits.get("quirks", []):
        sources.append(QUIRKS.get(quirk_key))
    if traits.get("major_trait"):
        sources.append(MAJOR_TRAITS.get(traits["major_trait"]))
    
    # Sum up affinities
    for source in sources:
        if source and "affinities" in source:
            for key, val in source["affinities"].items():
                if key in combined:
                    combined[key] += val
    
    # Clamp to [-1.0, 1.0]
    for key in combined:
        combined[key] = max(-1.0, min(1.0, combined[key]))
    
    return combined


def get_combined_job_mods(traits: dict) -> dict[str, float]:
    """Get combined job speed modifiers from all traits.
    
    Returns dict like: {"build": 0.1, "craft": 0.2, ...}
    """
    combined = {
        "build": 0.0,
        "haul": 0.0,
        "craft": 0.0,
        "cook": 0.0,
        "scavenge": 0.0,
    }
    
    # Collect from all trait sources
    sources = [
        ORIGINS.get(traits.get("origin", "")),
        EXPERIENCES.get(traits.get("experience", "")),
    ]
    for quirk_key in traits.get("quirks", []):
        sources.append(QUIRKS.get(quirk_key))
    if traits.get("major_trait"):
        sources.append(MAJOR_TRAITS.get(traits["major_trait"]))
    
    # Sum up job mods
    for source in sources:
        if source and "job_mods" in source:
            for key, val in source["job_mods"].items():
                if key in combined:
                    combined[key] += val
    
    return combined


def get_combined_stat_mods(traits: dict) -> dict[str, float]:
    """Get combined stat modifiers from all traits.
    
    Returns dict like: {"stress_resist": 0.2, "echo_sense": 0.3, ...}
    """
    combined = {}
    
    # Collect from all trait sources
    sources = [
        ORIGINS.get(traits.get("origin", "")),
        EXPERIENCES.get(traits.get("experience", "")),
    ]
    for quirk_key in traits.get("quirks", []):
        sources.append(QUIRKS.get(quirk_key))
    if traits.get("major_trait"):
        sources.append(MAJOR_TRAITS.get(traits["major_trait"]))
    
    # Sum up stat mods
    for source in sources:
        if source and "stat_mods" in source:
            for key, val in source["stat_mods"].items():
                combined[key] = combined.get(key, 0.0) + val
    
    return combined


def get_trait_thoughts(traits: dict, thought_type: str) -> list[str]:
    """Get all thought templates for a given type from colonist's traits.
    
    Args:
        traits: Colonist's trait dict
        thought_type: "idle", "environment", "social", "work", "mood", "need"
    
    Returns list of thought strings to choose from.
    """
    thoughts = []
    
    # Collect from all trait sources
    sources = [
        ORIGINS.get(traits.get("origin", "")),
        EXPERIENCES.get(traits.get("experience", "")),
    ]
    for quirk_key in traits.get("quirks", []):
        sources.append(QUIRKS.get(quirk_key))
    if traits.get("major_trait"):
        sources.append(MAJOR_TRAITS.get(traits["major_trait"]))
    
    # Collect thoughts
    for source in sources:
        if source:
            # Check for thoughts dict
            if "thoughts" in source:
                if thought_type in source["thoughts"]:
                    thoughts.extend(source["thoughts"][thought_type])
            # Quirks have flat thought lists
            elif "thoughts" not in source and thought_type == "idle":
                # Quirk thoughts default to idle
                pass
    
    # Also get quirk thoughts (they're flat lists, default to idle)
    if thought_type == "idle":
        for quirk_key in traits.get("quirks", []):
            quirk_data = QUIRKS.get(quirk_key)
            if quirk_data and "thoughts" in quirk_data and isinstance(quirk_data["thoughts"], list):
                thoughts.extend(quirk_data["thoughts"])
    
    return thoughts


def get_trait_labels(traits: dict) -> list[str]:
    """Get display labels for all traits."""
    labels = []
    
    origin_data = ORIGINS.get(traits.get("origin", ""))
    if origin_data:
        labels.append(origin_data["label"])
    
    exp_data = EXPERIENCES.get(traits.get("experience", ""))
    if exp_data:
        labels.append(exp_data["label"])
    
    for quirk_key in traits.get("quirks", []):
        quirk_data = QUIRKS.get(quirk_key)
        if quirk_data:
            labels.append(quirk_data["label"])
    
    major_key = traits.get("major_trait")
    if major_key:
        major_data = MAJOR_TRAITS.get(major_key)
        if major_data:
            labels.append(f"★ {major_data['label']}")  # Star for rare trait
    
    return labels


# =============================================================================
# BACKSTORY SENTENCE TEMPLATES
# =============================================================================

# Origin sentence templates - {trait} will be replaced with highlighted trait name
ORIGIN_SENTENCES = [
    "Grew up in the [{trait}], learning to survive before learning to walk.",
    "Born and raised in the [{trait}], where every day was a lesson in endurance.",
    "The [{trait}] shaped them from childhood, leaving marks that never fade.",
    "Came up through the [{trait}], carrying its dust in their lungs and its lessons in their bones.",
    "A child of the [{trait}], they learned early that nothing comes easy.",
]

# Experience sentence templates
EXPERIENCE_SENTENCES = [
    "Later, they [{trait}], an experience that changed everything.",
    "Years ago, they [{trait}], and haven't been the same since.",
    "At some point, they [{trait}]. They don't talk about it much.",
    "The past includes [{trait}], a chapter they carry quietly.",
    "Life took a turn when they [{trait}]. Some things you don't forget.",
]

# Quirk sentence templates (for 1 quirk)
QUIRK_SENTENCES_SINGLE = [
    "These days, they [{trait}].",
    "Those who know them notice they [{trait}].",
    "A small thing: they [{trait}].",
    "People say they [{trait}]. It's true.",
]

# Quirk sentence templates (for 2 quirks)
QUIRK_SENTENCES_DOUBLE = [
    "These days, they [{trait1}] and [{trait2}].",
    "Those who know them notice they [{trait1}], and also [{trait2}].",
    "Small things: they [{trait1}] and [{trait2}].",
    "People say they [{trait1}]. Also that they [{trait2}].",
]

# Major trait sentence templates
MAJOR_TRAIT_SENTENCES = [
    "But there's something else. They're [{trait}].",
    "What sets them apart: they're [{trait}].",
    "The rare truth is they're [{trait}].",
    "Few know, but they're [{trait}].",
]

# Quirk verb phrases (lowercase, for embedding in sentences)
QUIRK_VERBS = {
    "hums_when_thinking": "hum tunelessly when deep in thought",
    "talks_to_machines": "talk to machines like old friends",
    "scavenges_trinkets": "collect small objects others overlook",
    "mild_paranoia": "watch every shadow with careful eyes",
    "collects_stories": "remember every story they've ever heard",
    "sleeps_lightly": "wake at the slightest sound",
    "stares_into_pipes": "get lost staring into pipes and vents",
    "whispers_to_echoes": "whisper back to strange sounds",
    "keeps_inventory": "mentally catalog everything nearby",
    "wont_eat_cold": "refuse to eat anything that isn't warm",
    "overexplains": "use ten words when one would do",
    "gives_nicknames": "give everything and everyone a nickname",
    "takes_long_path": "prefer the scenic route over shortcuts",
    "afraid_of_sky": "get nervous under open sky",
    "afraid_of_tight_spaces": "panic in tight enclosed spaces",
}

# Experience verb phrases (lowercase, for embedding)
EXPERIENCE_VERBS = {
    "cortex_bloom_survivor": "survived a cortex bloom",
    "former_mercenary": "did contract work in the border riots",
    "signal_diver": "worked the comm relays until the interference changed them",
    "collapsed_block_escapee": "escaped a collapsing high-rise with seconds to spare",
    "floodlight_displaced": "lost everything when the Floodlights swept the district",
    "machine_gravekeeper": "maintained abandoned server vaults no one else would touch",
    "heatline_runner": "ran supplies across thermal ruptures",
    "silent_commune_raised": "spent years in a quiet commune beneath the vents",
}


def get_rich_backstory(traits: dict) -> list[dict]:
    """Get backstory as flowing prose with inline trait highlighting.
    
    Returns list of dicts, each representing a text segment:
        - text: The text content
        - is_trait: True if this is a highlighted trait name
        - trait_type: "origin", "experience", "quirk", or "major" (if is_trait)
        - color: RGB tuple (if is_trait)
    """
    segments = []
    
    # Origin sentence
    origin_key = traits.get("origin", "")
    origin_data = ORIGINS.get(origin_key)
    if origin_data:
        template = random.choice(ORIGIN_SENTENCES)
        _add_sentence_with_trait(segments, template, origin_data["label"], "origin")
        segments.append({"text": " ", "is_trait": False})
    
    # Experience sentence
    exp_key = traits.get("experience", "")
    exp_data = EXPERIENCES.get(exp_key)
    if exp_data:
        template = random.choice(EXPERIENCE_SENTENCES)
        verb = EXPERIENCE_VERBS.get(exp_key, exp_data["label"].lower())
        _add_sentence_with_trait(segments, template, verb, "experience")
        segments.append({"text": " ", "is_trait": False})
    
    # Quirk sentence(s)
    quirks = traits.get("quirks", [])
    if len(quirks) == 1:
        quirk_data = QUIRKS.get(quirks[0])
        if quirk_data:
            template = random.choice(QUIRK_SENTENCES_SINGLE)
            verb = QUIRK_VERBS.get(quirks[0], quirk_data["label"].lower())
            _add_sentence_with_trait(segments, template, verb, "quirk")
            segments.append({"text": " ", "is_trait": False})
    elif len(quirks) >= 2:
        quirk1_data = QUIRKS.get(quirks[0])
        quirk2_data = QUIRKS.get(quirks[1])
        if quirk1_data and quirk2_data:
            template = random.choice(QUIRK_SENTENCES_DOUBLE)
            verb1 = QUIRK_VERBS.get(quirks[0], quirk1_data["label"].lower())
            verb2 = QUIRK_VERBS.get(quirks[1], quirk2_data["label"].lower())
            _add_double_trait_sentence(segments, template, verb1, verb2, "quirk")
            segments.append({"text": " ", "is_trait": False})
    
    # Major trait sentence
    major_key = traits.get("major_trait")
    if major_key:
        major_data = MAJOR_TRAITS.get(major_key)
        if major_data:
            template = random.choice(MAJOR_TRAIT_SENTENCES)
            _add_sentence_with_trait(segments, template, major_data["label"], "major")
    
    return segments


def _add_sentence_with_trait(segments: list, template: str, trait_text: str, trait_type: str) -> None:
    """Add a sentence with a single highlighted trait to segments list."""
    # Split template on [{trait}]
    parts = template.split("[{trait}]")
    if len(parts) == 2:
        # Before trait
        if parts[0]:
            segments.append({"text": parts[0], "is_trait": False})
        # The trait itself (highlighted)
        segments.append({
            "text": trait_text,
            "is_trait": True,
            "trait_type": trait_type,
            "color": TRAIT_COLORS[trait_type],
        })
        # After trait
        if parts[1]:
            segments.append({"text": parts[1], "is_trait": False})
    else:
        # No placeholder, just add as-is
        segments.append({"text": template, "is_trait": False})


def _add_double_trait_sentence(segments: list, template: str, trait1: str, trait2: str, trait_type: str) -> None:
    """Add a sentence with two highlighted traits to segments list."""
    # Replace {trait1} and {trait2}
    # First split on [{trait1}]
    parts1 = template.split("[{trait1}]")
    if len(parts1) == 2:
        # Before trait1
        if parts1[0]:
            segments.append({"text": parts1[0], "is_trait": False})
        # Trait1
        segments.append({
            "text": trait1,
            "is_trait": True,
            "trait_type": trait_type,
            "color": TRAIT_COLORS[trait_type],
        })
        # Now handle the rest which contains [{trait2}]
        rest = parts1[1]
        parts2 = rest.split("[{trait2}]")
        if len(parts2) == 2:
            if parts2[0]:
                segments.append({"text": parts2[0], "is_trait": False})
            segments.append({
                "text": trait2,
                "is_trait": True,
                "trait_type": trait_type,
                "color": TRAIT_COLORS[trait_type],
            })
            if parts2[1]:
                segments.append({"text": parts2[1], "is_trait": False})
        else:
            segments.append({"text": rest, "is_trait": False})
    else:
        segments.append({"text": template, "is_trait": False})
