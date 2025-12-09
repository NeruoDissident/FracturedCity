"""Colonist simulation and rendering.

Colonists can now take simple construction jobs from the global job queue and
either wander idly or move/ work on assigned tasks.

State Machine
-------------
- IDLE: No job, may wander
- MOVING_TO_TARGET: Has a job and walking towards target
- PERFORMING_JOB: At job location, working on it
- RECOVERY: Interrupted or stuck, brief pause before returning to IDLE
- (eating state handled separately for hunger system)
"""

import random
from typing import Iterable
from enum import Enum

import pygame

from config import (
    TILE_SIZE,
    GRID_W,
    GRID_H,
    COLOR_COLONIST_DEFAULT,
    COLOR_COLONIST_ETHER,
)
from grid import Grid
from jobs import Job, request_job, remove_job, get_next_available_job, get_all_available_jobs, remove_designation, should_take_job, get_job_priority
from resources import complete_gathering_job, set_node_state, NodeState, harvest_tick, pickup_resource_item, add_to_stockpile, spend_from_stockpile
import buildings
from buildings import deliver_material, mark_supply_job_completed, has_required_materials, is_door, is_door_open, open_door, is_window, is_window_open, open_window, register_window
import zones
from rooms import mark_rooms_dirty


# Colonist states
class ColonistState(Enum):
    IDLE = "idle"
    MOVING_TO_TARGET = "moving_to_job"  # Keep old name for compatibility
    PERFORMING_JOB = "working"  # Keep old name for compatibility
    RECOVERY = "recovery"
    # Additional states for specific behaviors (kept as strings for now)
    HAULING = "hauling"
    CRAFTING_FETCH = "crafting_fetch"
    CRAFTING_WORK = "crafting_work"
    EATING = "eating"


# Default capabilities - all job categories a colonist can potentially do
# Legacy categories (kept for compatibility)
DEFAULT_CAPABILITIES = {
    "wall": True,
    "harvest": True,
    "construction": True,
    "haul": True,
    "crafting": True,
    "salvage": True,
}

# Job tags - user-facing toggles for job assignment
# These map to multiple job categories for easier management
DEFAULT_JOB_TAGS = {
    "can_build": True,      # Construction, walls, floors, doors, etc.
    "can_cook": True,       # Cooking at stove
    "can_craft": True,      # Crafting at workbenches (salvager's bench, etc.)
    "can_haul": True,       # Hauling resources to stockpiles and construction sites
    "can_scavenge": True,   # Salvaging and harvesting resources
}


# =============================================================================
# Identity Generation System (Display-only flavor text)
# =============================================================================

# Name pools - cyberpunk / dystopian / light eldritch tone
FIRST_NAMES = [
    "Kira", "Latch", "Soren", "Vex", "Mara", "Rime", "Ion", "Nessa", "Drax", "Vanta",
    "Kestrel", "Hallow", "Jax", "Nyx", "Solin", "Vire", "Orin", "Luma", "Cade", "Zephyr",
    "Rook", "Vesper", "Ash", "Cipher", "Dusk", "Echo", "Flint", "Glyph", "Hex", "Iris",
    "Jinx", "Kade", "Lynx", "Moth", "Nova", "Onyx", "Pike", "Quill", "Rust", "Shade",
    "Tarn", "Ulric", "Vale", "Wren", "Xen", "Yara", "Zara", "Blitz", "Crow", "Drift",
]

LAST_NAMES = [
    "Coil", "Needle", "Bramble", "Dross", "Verge", "Thorn", "Vector", "Halogen", "Lockstep",
    "Varn", "Umbra", "Flux", "Carbine", "Glass", "Ravel", "Shard", "Ember", "Hollow",
    "Cipher", "Weld", "Rust", "Static", "Void", "Glitch", "Splice", "Fracture", "Conduit",
    "Drift", "Null", "Surge", "Decay", "Wraith", "Synth", "Blight", "Crux", "Fray",
    "Grim", "Haze", "Jolt", "Krypt", "Lumen", "Murk", "Nether", "Oxide", "Pulse", "Quake",
]

# Flavor likes - atmospheric, cosmetic only
FLAVOR_LIKES = [
    "The hum of old generators",
    "Warm kitchens at night",
    "Rain hitting metal rooftops",
    "Dim neon signage",
    "Flickering consoles",
    "The smell of ozone",
    "Wide, empty streets at dawn",
    "The static glow of interference storms",
    "Elevated walkways and fire escapes",
    "Rooms with two doors — never one",
    "The click of cooling pipes",
    "Dust motes in shaft light",
    "Echoes that come back wrong",
    "The weight of concrete overhead",
    "Machines that talk to themselves",
    "Windows facing nowhere",
    "The taste of recycled air",
    "Shadows that stay put",
    "Old graffiti no one can read",
    "The silence between power cycles",
    "Rooftops at midnight",
    "The distant thrum of the grid",
    "Corners where the light bends",
    "Stairwells that go too deep",
    "The crackle before a broadcast",
]

# Flavor dislikes - atmospheric, cosmetic only
FLAVOR_DISLIKES = [
    "Crowded salvage floors",
    "Cold wind tunnels",
    "Silence with no echo",
    "Bright synthetic lighting",
    "Loose wiring underfoot",
    "Long hallways with no intersections",
    "Being watched by dead cameras",
    "Rooms that feel 'too clean'",
    "Pressure spikes",
    "Places where the static goes quiet",
    "Walls that hum at the wrong frequency",
    "Doors that open too slowly",
    "The smell of burnt insulation",
    "Floors that flex underfoot",
    "Spaces with no corners",
    "Lights that don't flicker",
    "Air that tastes like nothing",
    "Rooms with only one exit",
    "The feeling of being counted",
    "Ceilings too high to see",
    "Surfaces too smooth to grip",
    "The pause before alarms",
    "Reflections that lag behind",
    "Corridors that curve too gently",
    "The quiet after a collapse",
]

# Bio templates - keyed by preference tendencies
# {placeholder} will be filled based on colonist's affinities
BIO_TEMPLATES = [
    # Outside preference
    ("outside_high", [
        "Calm outdoors, uneasy indoors. Says sunlight 'keeps the signal clean.' No one knows what signal they mean.",
        "Spent years running courier routes across open rooftops. Still flinches at low ceilings.",
        "Prefers the sky overhead. Claims walls 'listen too closely.'",
        "Former perimeter scout. Trusts open ground more than any shelter.",
    ]),
    ("outside_low", [
        "Prefers sealed rooms with stable pressure. Avoids open streets. Once worked as a sublevel tech.",
        "Uncomfortable under open sky. Says the stars 'look back.'",
        "Grew up in the deep stacks. Finds comfort in enclosed spaces.",
        "Distrusts anything without a roof. The sky feels 'unfinished.'",
    ]),
    # Integrity preference
    ("integrity_high", [
        "Feels safest in solid structures. Tests walls by tapping. Knows the sound of stable concrete.",
        "Former structural surveyor. Can tell a building's age by its creaks.",
        "Only sleeps in rooms with load-bearing walls. Calls it 'practical paranoia.'",
    ]),
    ("integrity_low", [
        "Comforted by decayed structures and low integrity zones. Claims they can 'hear the building breathe.'",
        "Prefers ruins to new construction. Says fresh walls 'haven't learned anything yet.'",
        "Drawn to crumbling edges. Finds stability 'suspicious.'",
    ]),
    # Interference preference
    ("interference_high", [
        "Thrives in high-interference zones. Says the static 'drowns out the other noise.'",
        "Former signal tech who spent too long near broadcast arrays. Finds silence unsettling.",
        "Comfortable around electromagnetic chaos. Claims it 'feels like home.'",
    ]),
    ("interference_low", [
        "Gets anxious under high interference. Former salvage diver who spent too long beneath collapsed grids.",
        "Avoids areas with heavy static. Says it 'scrambles their thoughts.'",
        "Sensitive to electromagnetic fields. Prefers clean signal zones.",
    ]),
    # Echo preference
    ("echo_high", [
        "Feels at home in echoing hallways. Distrusts quiet spaces. Known for whispering to themselves during long shifts.",
        "Navigates by sound. Prefers spaces where footsteps carry.",
        "Finds comfort in reverberant chambers. Says silence 'hides things.'",
    ]),
    ("echo_low", [
        "Prefers acoustically dead spaces. Echoes make them 'hear things that aren't there.'",
        "Works best in muffled environments. Loud reverb triggers old memories.",
        "Seeks out quiet corners. Says echoes 'tell lies.'",
    ]),
    # Crowding preference
    ("crowding_high", [
        "Works better with others nearby. Finds isolation 'too loud.'",
        "Former collective worker. Uncomfortable when alone for too long.",
        "Prefers busy spaces. Says empty rooms 'watch too closely.'",
    ]),
    ("crowding_low", [
        "Prefers solitude. Gets twitchy in crowds. Once spent a year alone in a signal tower.",
        "Works best alone. Other people's breathing 'disrupts the pattern.'",
        "Avoids groups when possible. Claims they can 'feel everyone thinking.'",
    ]),
    # Pressure preference
    ("pressure_high", [
        "Comfortable in pressurized environments. Former deep-level maintenance crew.",
        "Finds low-pressure zones unsettling. Says their ears 'expect more.'",
        "Prefers the weight of atmosphere. Open air feels 'too thin.'",
    ]),
    ("pressure_low", [
        "Sensitive to pressure changes. Gets headaches in sealed environments.",
        "Prefers ventilated spaces. Pressurized rooms feel 'too heavy.'",
        "Former surface worker. Never adjusted to sublevel atmospherics.",
    ]),
    # Generic fallbacks
    ("neutral", [
        "Keeps to themselves. Watches more than they speak. Reliable in a crisis.",
        "No strong preferences. Adapts to whatever the city throws at them.",
        "Quiet worker. Does the job without complaint. Remembers everything.",
        "Arrived from somewhere else. Doesn't talk about before. Fits in anyway.",
        "Survived something once. Doesn't say what. Works harder than most.",
    ]),
]


def generate_colonist_name() -> str:
    """Generate a random colonist name in cyberpunk/dystopian style."""
    first = random.choice(FIRST_NAMES)
    last = random.choice(LAST_NAMES)
    return f"{first} {last}"


def generate_colonist_bio(preferences: dict[str, float]) -> str:
    """Generate a bio based on colonist's preference profile.
    
    Args:
        preferences: Dict of preference values (likes_outside, likes_integrity, etc.)
    
    Returns:
        A 1-3 sentence atmospheric bio string.
    """
    # Find the strongest preference (positive or negative)
    strongest_pref = None
    strongest_value = 0.0
    
    pref_to_template_key = {
        "likes_outside": ("outside_high", "outside_low"),
        "likes_integrity": ("integrity_high", "integrity_low"),
        "likes_interference": ("interference_high", "interference_low"),
        "likes_echo": ("echo_high", "echo_low"),
        "likes_crowding": ("crowding_high", "crowding_low"),
        "likes_pressure": ("pressure_high", "pressure_low"),
    }
    
    for pref_key, value in preferences.items():
        if abs(value) > abs(strongest_value):
            strongest_value = value
            strongest_pref = pref_key
    
    # Select template based on strongest preference
    template_key = "neutral"
    if strongest_pref and abs(strongest_value) > 0.5:
        high_key, low_key = pref_to_template_key.get(strongest_pref, ("neutral", "neutral"))
        template_key = high_key if strongest_value > 0 else low_key
    
    # Find matching templates
    templates = []
    for key, template_list in BIO_TEMPLATES:
        if key == template_key:
            templates = template_list
            break
    
    if not templates:
        # Fallback to neutral
        for key, template_list in BIO_TEMPLATES:
            if key == "neutral":
                templates = template_list
                break
    
    return random.choice(templates) if templates else "A survivor. Nothing more to say."


def generate_flavor_likes(count: int = 2) -> list[str]:
    """Generate random flavor likes for a colonist.
    
    Args:
        count: Number of likes to generate (1-3)
    
    Returns:
        List of flavor like strings.
    """
    count = max(1, min(3, count))
    return random.sample(FLAVOR_LIKES, min(count, len(FLAVOR_LIKES)))


def generate_flavor_dislikes(count: int = 2) -> list[str]:
    """Generate random flavor dislikes for a colonist.
    
    Args:
        count: Number of dislikes to generate (1-3)
    
    Returns:
        List of flavor dislike strings.
    """
    count = max(1, min(3, count))
    return random.sample(FLAVOR_DISLIKES, min(count, len(FLAVOR_DISLIKES)))


# =============================================================================
# Thought System - Internal monologue and observations
# =============================================================================

# Thought types for categorization and UI coloring
THOUGHT_TYPES = {
    "environment": (150, 200, 255),   # Blue - environmental observations
    "social": (255, 200, 150),        # Orange - social interactions
    "work": (150, 255, 150),          # Green - work-related
    "need": (255, 150, 150),          # Red - needs/wants
    "mood": (200, 150, 255),          # Purple - mood changes
    "idle": (180, 180, 180),          # Gray - idle musings
    "combat": (255, 80, 80),          # Bright red - combat/violence
}

# Environment thought templates - keyed by preference direction
# {preference_key: {positive: [...], negative: [...], neutral: [...]}}
ENVIRONMENT_THOUGHTS = {
    "likes_echo": {
        "positive": [
            "The acoustics here are perfect.",
            "I can hear my own footsteps. Comforting.",
            "Good reverb in this space.",
            "The echoes feel right.",
        ],
        "negative": [
            "Too quiet in here. Unsettling.",
            "Where did all the sound go?",
            "This silence is... wrong.",
            "I miss the echoes.",
        ],
    },
    "likes_interference": {
        "positive": [
            "The static feels like home.",
            "Good interference here. Drowns out the noise.",
            "This electromagnetic hum is soothing.",
            "Finally, some proper signal chaos.",
        ],
        "negative": [
            "Too clean. Too quiet. Where's the static?",
            "The signal here is too pure. Feels sterile.",
            "I can hear myself think. That's the problem.",
        ],
    },
    "likes_pressure": {
        "positive": [
            "Good pressure in here. Feels solid.",
            "The atmosphere has weight. I like it.",
            "Proper pressurization. Finally.",
        ],
        "negative": [
            "Air feels thin here.",
            "Not enough pressure. My ears are complaining.",
            "This atmosphere feels... incomplete.",
        ],
    },
    "likes_integrity": {
        "positive": [
            "Solid walls. Good construction.",
            "This structure feels stable. Safe.",
            "I can trust these walls.",
        ],
        "negative": [
            "These walls are too new. Haven't proven themselves.",
            "Fresh construction. Doesn't feel lived-in yet.",
            "Too pristine. Where's the character?",
        ],
    },
    "likes_outside": {
        "positive": [
            "Open air. Room to breathe.",
            "Good to see the sky.",
            "No ceiling pressing down. Nice.",
        ],
        "negative": [
            "Too exposed out here.",
            "The sky is... watching.",
            "I'd rather be inside.",
            "Need a roof over my head.",
        ],
    },
    "likes_crowding": {
        "positive": [
            "Good to have company nearby.",
            "Not alone. That's something.",
            "People around. Feels safer.",
        ],
        "negative": [
            "Too many people here.",
            "Need some space to think.",
            "Crowded. Can feel everyone's presence.",
            "Wish I had this corner to myself.",
        ],
    },
}

# Social thought templates
SOCIAL_THOUGHTS = {
    "charisma_received": [
        "{name}'s presence is calming.",
        "Nice to be near {name}.",
        "{name} has a way of making things feel okay.",
        "Something about {name} puts me at ease.",
    ],
    "intimidation_received": [
        "{name} seems... intense today.",
        "Why is {name} looking at me like that?",
        "{name}'s presence is unsettling.",
        "I should probably give {name} some space.",
    ],
}

# Work thought templates
WORK_THOUGHTS = {
    "job_complete": [
        "Done. That's satisfying.",
        "Another one finished.",
        "Good work. Moving on.",
        "That's done. What's next?",
    ],
    "job_interrupted": [
        "Interrupted again...",
        "Can't finish anything around here.",
        "Fine. I'll do something else.",
        "Switching tasks. Again.",
    ],
    "job_stuck": [
        "Can't get there from here.",
        "Path's blocked. Frustrating.",
        "Something's in the way.",
    ],
    "crafting_complete": [
        "Made something useful.",
        "Crafting done. Feels productive.",
        "Another item finished.",
    ],
    "building_complete": [
        "Wall's up. Solid work.",
        "Construction complete.",
        "Built something that'll last.",
    ],
    "harvesting_complete": [
        "Got what we needed.",
        "Resources secured.",
        "Good haul.",
    ],
}

# Need thought templates
NEED_THOUGHTS = {
    "hungry": [
        "Getting hungry.",
        "Could use some food.",
        "Stomach's starting to complain.",
    ],
    "very_hungry": [
        "Really need to eat soon.",
        "Can't focus. Too hungry.",
        "Food. Where's the food?",
    ],
    "starving": [
        "Starving. This is bad.",
        "Need food. Now.",
        "Can barely think straight.",
    ],
    "stressed": [
        "Feeling on edge.",
        "Need a break.",
        "Everything's getting to me.",
    ],
    "overwhelmed": [
        "Too much. It's all too much.",
        "Can't handle this right now.",
        "Need to get away.",
    ],
    "relaxed": [
        "Feeling better.",
        "Stress is fading.",
        "This is more manageable.",
    ],
}

# Mood change thought templates
MOOD_THOUGHTS = {
    "Euphoric": [
        "Everything feels possible today!",
        "In a great mood. Let's get things done.",
        "Feeling fantastic.",
    ],
    "Calm": [
        "Feeling centered. Good.",
        "Calm and ready.",
        "At peace with things.",
    ],
    "Focused": [
        "Clear head. Time to work.",
        "Focused. Let's do this.",
    ],
    "Uneasy": [
        "Something feels off.",
        "Can't quite settle.",
        "A bit on edge.",
    ],
    "Stressed": [
        "Tension building.",
        "Hard to concentrate.",
        "Stress is getting to me.",
    ],
    "Overwhelmed": [
        "It's all too much.",
        "Can't cope right now.",
        "Need this to stop.",
    ],
}

# Idle thought templates - random musings when not doing anything
IDLE_THOUGHTS = [
    "Wonder what's for dinner.",
    "Could use some better equipment.",
    "This place has potential.",
    "What was that noise?",
    "Should check on the others.",
    "Need to stay busy.",
    "Quiet moment. Rare.",
    "Wonder what's beyond the walls.",
    "Miss the old days. Sometimes.",
    "One day at a time.",
    "Keep moving forward.",
    "The city never sleeps. Neither do I.",
    "Something's different today. Can't place it.",
    "Hope the supplies hold out.",
    "Weather's changing. Can feel it.",
]


class Colonist:
    """Single colonist agent that can perform construction jobs.

    States
    ------
    - "idle":           No job, may wander.
    - "moving_to_job":  Has a job and is walking towards its tile.
    - "working":        Standing on the job tile and increasing progress.
    - "hauling":        Carrying item to destination.
    - "crafting_fetch": Fetching materials for crafting job.
    - "crafting_work":  Working at workstation.
    - "eating":         Walking to food and eating.
    - "recovery":       Brief pause after interruption before returning to idle.
    
    Interruptibility
    ----------------
    Jobs can be interrupted when:
    - Path becomes blocked (wall built, etc.)
    - Job target becomes invalid (construction completed by another, node depleted)
    - Colonist gets stuck in a non-walkable tile (teleported to safety)
    
    When interrupted, colonist enters recovery state briefly, then returns to idle.
    """

    def __init__(self, x: int, y: int, color: tuple[int, int, int] | None = None):
        self.x = x
        self.y = y
        self.z = 0  # Z-level (0 = ground, 1 = rooftop)
        self.color = color or COLOR_COLONIST_DEFAULT

        self.state: str = "idle"
        self.current_job: Job | None = None
        
        # Movement speed control - move every N ticks
        self.move_cooldown = 0
        self.move_speed = 8  # ticks between moves (lower = faster)
        
        # Path commitment - calculate once, follow until blocked
        # Path now includes z-level: list of (x, y, z) tuples
        self.current_path: list[tuple[int, int, int]] = []
        self.stuck_timer = 0
        self.max_stuck_time = 30  # ticks before giving up on current path
        
        # Recovery state - brief pause after interruption before returning to idle
        self.recovery_timer = 0
        self.recovery_duration = 15  # ticks to wait in recovery state
        
        # Capability flags - which job categories this colonist can perform
        # All True by default; future systems can disable specific capabilities
        self.capabilities: dict[str, bool] = DEFAULT_CAPABILITIES.copy()
        
        # Job tags - user-facing toggles for job assignment
        self.job_tags: dict[str, bool] = DEFAULT_JOB_TAGS.copy()
        
        # Pressure score - willingness to be interrupted (1-10)
        # Higher score = more interruptible (will drop work for urgent jobs)
        # Score must be >= job.pressure to be interrupted
        # 10 = always drops work for urgent jobs, 1 = rarely interrupted
        self.pressure_score: int = 5  # Default: moderate interruptibility
        
        # Carrying state for haul jobs
        self.carrying: dict | None = None  # {"type": "wood", "amount": 1}
        
        # Carried items tracking - aggregates what colonist is currently carrying
        # Keys are resource types, values are amounts. Updated via pick_up_item/drop_item methods.
        self.carried_items: dict[str, int] = {}
        
        # Hunger system
        # At 60 FPS: 0.003 per tick = 0.18 per second = ~9 minutes to reach 100
        # Colonists get hungry (>70) at ~6.5 minutes, giving plenty of time to set up food
        self.hunger: float = 0.0  # 0 = full, 100 = starving
        self.hunger_rate: float = 0.003  # Hunger increase per tick (slow)
        self.health: float = 100.0  # 0 = dead
        self.starving_damage: float = 0.05  # Damage per tick when hunger >= 100 (slower death)
        self.is_dead: bool = False
        
        # Visual properties for sprite-people rendering
        self.skin_tone = self._generate_random_skin_tone()
        self.clothing_color = self._generate_random_clothing_color()
        self.facing_direction = "south"  # north, south, east, west
        self.last_x = x
        self.last_y = y
        self.idle_fidget_timer = 0
        self.fidget_offset = 0  # Vertical bobbing offset
        
        # Environment sampling - stores recent environmental context
        self.recent_context: list[dict] = []  # Last 10 environment samples
        self.max_context_samples = 10
        
        # Affinity system - preferences that drift based on experienced environments
        # Values range from -1.0 (strong dislike) to +1.0 (strong preference)
        self.affinity_interference: float = 0.0
        self.affinity_echo: float = 0.0
        self.affinity_pressure: float = 0.0
        self.affinity_integrity: float = 0.0
        self.affinity_outside: float = 0.0
        self.affinity_crowding: float = 0.0
        
        # Preference profile - accumulated personality direction derived from affinities
        # Values range from -10.0 to +10.0, representing stable personality traits
        # Updated each environment sample: preference += affinity * (sample - global_avg)
        self.preferences: dict[str, float] = {
            "likes_interference": 0.0,
            "likes_echo": 0.0,
            "likes_pressure": 0.0,
            "likes_integrity": 0.0,
            "likes_outside": 0.0,
            "likes_crowding": 0.0,
        }
        
        # Comfort/stress emotional state - derived from preference alignment with environment
        # Values range from -10.0 to +10.0
        # Comfort rises when environment matches preferences, stress rises when it doesn't
        self.comfort: float = 0.0
        self.stress: float = 0.0
        
        # Track strongest comfort influence this tick for debug display
        self.comfort_influence: tuple[str, float] = ("none", 0.0)  # (parameter_name, contribution)
        
        # Preference drift system - slowly adjusts preferences based on comfort/stress
        # When comfortable, preferences drift toward current environment parameters
        # When stressed, preferences drift away from current environment parameters
        self.preference_drift_rate: float = 0.00005  # Very small drift per tick
        
        # Track drift for debug display
        self.last_total_drift: float = 0.0  # Total drift magnitude this tick
        self.last_drift_strongest: tuple[str, float] = ("none", 0.0)  # (parameter, change)
        
        # Mood state - derived from comfort and stress, purely descriptive
        # Updated each tick based on mood_score = comfort - stress
        self.mood_state: str = "Focused"  # Default neutral mood
        self.mood_score: float = 0.0  # Raw score for debug
        
        # Identity - display-only flavor text, does NOT affect any game systems
        self.name: str = generate_colonist_name()
        self.flavor_likes: list[str] = generate_flavor_likes(random.randint(1, 3))
        self.flavor_dislikes: list[str] = generate_flavor_dislikes(random.randint(1, 3))
        
        # Age system - affects relationships, work capacity, and life events
        self.age: int = random.randint(18, 55)  # Starting colonists are adults
        self.birth_tick: int = 0  # Set when born in colony (0 = arrived as adult)
        
        # Combat/faction system
        self.faction: str = "colony"  # Which group this colonist belongs to
        self.is_hostile: bool = False  # If True, attacks non-hostiles
        self.hostile_to_factions: set = set()  # Factions this colonist will attack
        self.in_combat: bool = False  # Currently fighting
        self.combat_target: "Colonist" = None  # Who they're fighting
        self.last_combat_tick: int = 0  # Cooldown between attacks
        
        # Trait system - generates backstory and modifies affinities/job speeds
        from traits import (generate_traits, generate_backstory, get_combined_affinities,
                           get_combined_job_mods, get_combined_stat_mods, get_rich_backstory)
        self.traits: dict = generate_traits()
        self.bio: str = generate_backstory(self.traits)
        
        # Cache rich backstory segments (generated once, not every frame)
        self.rich_backstory: list[dict] = get_rich_backstory(self.traits)
        
        # Apply trait affinity modifiers (starting biases)
        trait_affinities = get_combined_affinities(self.traits)
        self.affinity_interference = trait_affinities.get("interference", 0.0)
        self.affinity_echo = trait_affinities.get("echo", 0.0)
        self.affinity_pressure = trait_affinities.get("pressure", 0.0)
        self.affinity_integrity = trait_affinities.get("integrity", 0.0)
        self.affinity_outside = trait_affinities.get("outside", 0.0)
        self.affinity_crowding = trait_affinities.get("crowding", 0.0)
        
        # Store trait job modifiers for work speed calculations
        self.trait_job_mods: dict[str, float] = get_combined_job_mods(self.traits)
        
        # Store trait stat modifiers for other bonuses
        self.trait_stat_mods: dict[str, float] = get_combined_stat_mods(self.traits)
        
        # Equipment slots - UI/data only, no gameplay effects yet
        # Each slot holds None or an item dict like {"name": "Hard Hat", "type": "head_armor"}
        self.equipment: dict[str, dict | None] = {
            "head": None,
            "body": None,
            "hands": None,
            "feet": None,
            "implant": None,
            "charm": None,
        }
        
        # Inventory slots - general carried items (pockets/backpack)
        # Each slot holds None or an item dict like {"name": "Rusty Key", "type": "key"}
        self.inventory_slots: list[dict | None] = [None, None, None, None, None, None]
        
        # Thought log - rolling log of internal monologue and observations
        self.thought_log: list[dict] = []  # [{tick, type, text, mood_effect}, ...]
        self.max_thoughts: int = 50  # Keep last 50 thoughts
        self.thought_cooldown: int = 0  # Ticks until next thought allowed
        self.min_thought_interval: int = 120  # ~2 seconds at 60 FPS between thoughts
        self.last_environment_thought_tick: int = 0  # Track environment thoughts separately
        self.last_mood_state: str = "Focused"  # Track mood changes
        self.last_hunger_threshold: str = "none"  # Track hunger state changes
        
        # Sleep/tiredness system
        self.tiredness: float = random.uniform(0, 30)  # 0-100, starts low
        self.is_sleeping: bool = False
        self.sleep_target: tuple = None  # (x, y, z) of bed or sleep spot
        self.last_sleep_tick: int = 0
    
    # =========================================================================
    # Thought System - Internal monologue and observations
    # =========================================================================
    
    def add_thought(self, thought_type: str, text: str, mood_effect: float = 0.0, 
                    force: bool = False, game_tick: int = 0) -> bool:
        """Add a thought to the colonist's thought log.
        
        Args:
            thought_type: Category of thought (environment, social, work, need, mood, idle)
            text: The thought text
            mood_effect: Optional mood modifier (-1.0 to 1.0)
            force: If True, bypass cooldown check
            game_tick: Current game tick for timestamp
            
        Returns:
            True if thought was added, False if on cooldown or duplicate
        """
        # Check cooldown (unless forced)
        if not force and self.thought_cooldown > 0:
            return False
        
        # Avoid duplicate consecutive thoughts
        if self.thought_log and self.thought_log[-1]["text"] == text:
            return False
        
        # Create thought entry
        thought = {
            "tick": game_tick,
            "type": thought_type,
            "text": text,
            "mood_effect": mood_effect,
        }
        
        # Add to log
        self.thought_log.append(thought)
        
        # Trim old thoughts
        if len(self.thought_log) > self.max_thoughts:
            self.thought_log = self.thought_log[-self.max_thoughts:]
        
        # Apply mood effect
        if mood_effect != 0:
            self.comfort += mood_effect
            self.comfort = max(-10.0, min(10.0, self.comfort))
        
        # Set cooldown
        self.thought_cooldown = self.min_thought_interval
        
        return True
    
    def get_recent_thoughts(self, count: int = 10) -> list[dict]:
        """Get the most recent thoughts for UI display.
        
        Args:
            count: Number of thoughts to return
            
        Returns:
            List of thought dicts, most recent first
        """
        return list(reversed(self.thought_log[-count:]))
    
    def get_latest_thought(self) -> dict | None:
        """Get the most recent thought, or None if no thoughts."""
        return self.thought_log[-1] if self.thought_log else None
    
    def _tick_thought_cooldown(self) -> None:
        """Decrement thought cooldown. Call once per game tick."""
        if self.thought_cooldown > 0:
            self.thought_cooldown -= 1
    
    def _generate_environment_thought(self, sample: dict, game_tick: int) -> None:
        """Generate a thought based on current environment and preferences.
        
        Called periodically during environment sampling.
        """
        # Only generate environment thoughts every ~10 seconds
        if game_tick - self.last_environment_thought_tick < 600:
            return
        
        # Find the strongest preference-environment alignment
        strongest_pref = None
        strongest_alignment = 0.0
        
        pref_to_env = {
            "likes_echo": sample.get("echo", 0.0),
            "likes_interference": sample.get("interference", 0.0),
            "likes_pressure": sample.get("pressure", 0.0),
            "likes_integrity": sample.get("integrity", 1.0),
            "likes_outside": 1.0 if sample.get("is_outside", True) else 0.0,
            "likes_crowding": float(sample.get("nearby_colonists", 0)) / 3.0,  # Normalize
        }
        
        for pref_key, env_value in pref_to_env.items():
            pref_value = self.preferences.get(pref_key, 0.0)
            # Alignment = preference * environment (positive = matches, negative = mismatch)
            alignment = pref_value * env_value
            if abs(alignment) > abs(strongest_alignment):
                strongest_alignment = alignment
                strongest_pref = pref_key
        
        # Only generate thought if alignment is significant
        if abs(strongest_alignment) < 1.0:
            return
        
        # Get appropriate thought template
        templates = ENVIRONMENT_THOUGHTS.get(strongest_pref, {})
        if strongest_alignment > 0:
            thought_list = templates.get("positive", [])
            mood_effect = 0.1
        else:
            thought_list = templates.get("negative", [])
            mood_effect = -0.1
        
        # Try trait-flavored environment thoughts first
        from traits import get_trait_thoughts
        trait_thoughts = get_trait_thoughts(self.traits, "environment")
        
        # 60% chance to use trait thought if available
        if trait_thoughts and random.random() < 0.6:
            text = random.choice(trait_thoughts)
        elif thought_list:
            text = random.choice(thought_list)
        else:
            return
        
        if self.add_thought("environment", text, mood_effect, game_tick=game_tick):
            self.last_environment_thought_tick = game_tick
    
    def _generate_social_thought(self, other_name: str, effect_type: str, game_tick: int) -> None:
        """Generate a thought about a social interaction.
        
        Args:
            other_name: Name of the other colonist
            effect_type: "charisma" or "intimidation"
        """
        if effect_type == "charisma":
            templates = SOCIAL_THOUGHTS.get("charisma_received", [])
            mood_effect = 0.05
        else:
            templates = SOCIAL_THOUGHTS.get("intimidation_received", [])
            mood_effect = -0.05
        
        if templates:
            text = random.choice(templates).format(name=other_name.split()[0])  # First name only
            self.add_thought("social", text, mood_effect, game_tick=game_tick)
    
    def _generate_work_thought(self, work_event: str, game_tick: int) -> None:
        """Generate a thought about work.
        
        Args:
            work_event: Type of work event (job_complete, job_interrupted, etc.)
        """
        templates = WORK_THOUGHTS.get(work_event, [])
        
        mood_effects = {
            "job_complete": 0.1,
            "building_complete": 0.15,
            "crafting_complete": 0.15,
            "harvesting_complete": 0.1,
            "job_interrupted": -0.05,
            "job_stuck": -0.1,
        }
        
        if templates:
            text = random.choice(templates)
            mood_effect = mood_effects.get(work_event, 0.0)
            self.add_thought("work", text, mood_effect, game_tick=game_tick)
    
    def _generate_need_thought(self, need_type: str, game_tick: int) -> None:
        """Generate a thought about a need.
        
        Args:
            need_type: Type of need (hungry, very_hungry, starving, stressed, etc.)
        """
        templates = NEED_THOUGHTS.get(need_type, [])
        
        mood_effects = {
            "hungry": -0.05,
            "very_hungry": -0.1,
            "starving": -0.2,
            "stressed": -0.1,
            "overwhelmed": -0.2,
            "relaxed": 0.1,
        }
        
        if templates:
            text = random.choice(templates)
            mood_effect = mood_effects.get(need_type, 0.0)
            self.add_thought("need", text, mood_effect, force=True, game_tick=game_tick)
    
    def _generate_mood_thought(self, new_mood: str, game_tick: int) -> None:
        """Generate a thought when mood state changes.
        
        Args:
            new_mood: The new mood state
        """
        templates = MOOD_THOUGHTS.get(new_mood, [])
        
        if templates:
            text = random.choice(templates)
            self.add_thought("mood", text, 0.0, force=True, game_tick=game_tick)
    
    def _maybe_generate_idle_thought(self, game_tick: int) -> None:
        """Maybe generate a random idle thought when not busy.
        
        Only triggers occasionally when colonist is idle.
        Prefers trait-flavored thoughts when available.
        """
        # 1 in 1000 chance per tick when idle (~once per 15 seconds at 60 FPS)
        if random.random() < 0.001:
            # Try to get trait-flavored idle thoughts first
            from traits import get_trait_thoughts
            trait_thoughts = get_trait_thoughts(self.traits, "idle")
            
            # 70% chance to use trait thought if available
            if trait_thoughts and random.random() < 0.7:
                text = random.choice(trait_thoughts)
            else:
                text = random.choice(IDLE_THOUGHTS)
            
            self.add_thought("idle", text, 0.0, game_tick=game_tick)
    
    # =========================================================================
    # Equipment Effects - Calculate bonuses from equipped items
    # =========================================================================
    
    def get_equipment_stats(self) -> dict:
        """Calculate total stat bonuses from all equipped items.
        
        Handles both static items (from items.py) and procedurally generated items.
        
        Returns dict with keys:
            - comfort: float (bonus to comfort/mood)
            - speed_bonus: float (movement speed modifier, e.g., 0.1 = +10%)
            - walk_steady: float (stumble resistance)
            - hazard_resist: float (resistance to environmental hazards)
            - stress_resist: float (reduces stress gain)
            - build_speed: float (construction speed bonus)
            - harvest_speed: float (gathering speed bonus)
            - craft_speed: float (crafting speed bonus)
            - haul_capacity: float (carry amount multiplier)
            - focus: float (work quality/concentration)
            - warmth: float (cold resistance, also adds comfort)
            - cooling: float (heat resistance)
        """
        from items import get_item_def
        
        totals = {
            "comfort": 0.0,
            "speed_bonus": 0.0,
            "walk_steady": 0.0,
            "hazard_resist": 0.0,
            "stress_resist": 0.0,
            "build_speed": 0.0,
            "harvest_speed": 0.0,
            "craft_speed": 0.0,
            "haul_capacity": 0.0,
            "focus": 0.0,
            "warmth": 0.0,
            "cooling": 0.0,
            # Senses
            "vision": 0.0,
            "hearing": 0.0,
            "echo_sense": 0.0,
            # Social
            "charisma": 0.0,
            "intimidation": 0.0,
        }
        
        # Direct stat mapping from generated item stat names
        stat_mapping = {
            "walk_speed": "speed_bonus",
            "walk_steady": "walk_steady",
            "build_speed": "build_speed",
            "harvest_speed": "harvest_speed",
            "craft_speed": "craft_speed",
            "haul_capacity": "haul_capacity",
            "hazard_resist": "hazard_resist",
            "stress_resist": "stress_resist",
            "comfort": "comfort",
            "warmth": "warmth",
            "cooling": "cooling",
            "focus": "focus",
            # Senses
            "vision": "vision",
            "hearing": "hearing",
            "echo_sense": "echo_sense",
            # Social
            "charisma": "charisma",
            "intimidation": "intimidation",
        }
        
        for slot, item_data in self.equipment.items():
            if item_data is None:
                continue
            
            # Check if this is a generated item
            if item_data.get("generated"):
                # Sum modifiers from generated item (ALWAYS triggers only for base stats)
                for mod in item_data.get("modifiers", []):
                    if mod.get("trigger") == "always":
                        stat = mod.get("stat", "")
                        value = mod.get("value", 0.0)
                        
                        # Map to our stat keys
                        target_key = stat_mapping.get(stat)
                        if target_key:
                            totals[target_key] += value
            else:
                # Static item - get from item registry
                item_id = item_data.get("id")
                if item_id is None:
                    continue
                    
                item_def = get_item_def(item_id)
                if item_def is None:
                    continue
                
                # Sum up stats (static items use legacy fields)
                totals["comfort"] += item_def.comfort
                totals["speed_bonus"] += item_def.speed_bonus
                totals["hazard_resist"] += item_def.hazard_resist
                # Legacy work_bonus applies to build_speed
                totals["build_speed"] += item_def.work_bonus
        
        # Warmth also contributes to comfort
        totals["comfort"] += totals["warmth"] * 0.5
        
        return totals
    
    def get_equipment_speed_modifier(self) -> float:
        """Get movement speed modifier from equipment.
        
        Returns multiplier for move_speed (lower = faster):
        - Positive speed_bonus (e.g., 0.1) → 0.9 multiplier (10% faster)
        - Negative speed_bonus (e.g., -0.1) → 1.1 multiplier (10% slower)
        """
        stats = self.get_equipment_stats()
        # Convert bonus to multiplier (invert because lower move_speed = faster)
        return 1.0 - stats["speed_bonus"]
    
    def get_equipment_work_modifier(self, job_type: str = "construction") -> float:
        """Get work speed modifier from equipment and traits for a specific job type.
        
        Args:
            job_type: "construction", "gathering", "crafting", "haul", "cook", "scavenge"
        
        Returns multiplier for work progress:
        - Positive bonus (e.g., 0.15) → 1.15 multiplier (15% faster work)
        
        Focus stat adds a small bonus to all work types.
        Trait job_mods add bonuses based on colonist background.
        """
        stats = self.get_equipment_stats()
        focus_bonus = stats["focus"] * 0.5  # Focus gives half its value to all work
        
        # Get trait bonus for this job type
        trait_bonus = 0.0
        if job_type == "gathering":
            trait_bonus = self.trait_job_mods.get("scavenge", 0.0)
            return 1.0 + stats["harvest_speed"] + focus_bonus + trait_bonus
        elif job_type == "crafting":
            trait_bonus = self.trait_job_mods.get("craft", 0.0)
            return 1.0 + stats["craft_speed"] + focus_bonus + trait_bonus
        elif job_type == "haul":
            trait_bonus = self.trait_job_mods.get("haul", 0.0)
            return 1.0 + focus_bonus + trait_bonus
        elif job_type == "cook":
            trait_bonus = self.trait_job_mods.get("cook", 0.0)
            return 1.0 + focus_bonus + trait_bonus
        else:  # construction (default)
            trait_bonus = self.trait_job_mods.get("build", 0.0)
            return 1.0 + stats["build_speed"] + focus_bonus + trait_bonus
    
    def get_equipment_comfort_bonus(self) -> float:
        """Get comfort bonus from equipment (added to mood calculations)."""
        stats = self.get_equipment_stats()
        return stats["comfort"]
    
    def get_equipment_hazard_resist(self) -> float:
        """Get hazard resistance from equipment (reduces environmental damage)."""
        stats = self.get_equipment_stats()
        return stats["hazard_resist"]
    
    def get_equipment_stress_resist(self) -> float:
        """Get stress resistance from equipment (reduces stress gain)."""
        stats = self.get_equipment_stats()
        return stats["stress_resist"]
    
    def get_equipment_haul_capacity(self) -> float:
        """Get haul capacity multiplier from equipment.
        
        Returns multiplier for carry amount:
        - 0.0 = base capacity (1x)
        - 0.5 = 1.5x capacity
        - 1.0 = 2x capacity
        """
        stats = self.get_equipment_stats()
        return 1.0 + stats["haul_capacity"]
    
    def take_damage(self, base_damage: float, damage_type: str = "hazard") -> float:
        """Apply damage to colonist, reduced by appropriate resistances.
        
        Args:
            base_damage: Raw damage amount before resistances
            damage_type: Type of damage - "hazard", "combat", "fall", etc.
            
        Returns:
            Actual damage dealt after resistances
        """
        actual_damage = base_damage
        
        # Apply hazard resist for environmental damage
        if damage_type == "hazard":
            hazard_resist = self.get_equipment_hazard_resist()
            actual_damage = base_damage * (1.0 - min(0.9, hazard_resist))  # Cap at 90% reduction
        
        # Apply damage
        self.health -= actual_damage
        
        # Check for death
        if self.health <= 0:
            self.health = 0
            self.is_dead = True
            print(f"[Death] {self.name} has died from {damage_type} damage")
        
        return actual_damage
    
    def heal(self, amount: float) -> float:
        """Heal the colonist.
        
        Args:
            amount: Amount to heal
            
        Returns:
            Actual amount healed (may be less if already near max)
        """
        if self.is_dead:
            return 0.0
        
        old_health = self.health
        self.health = min(100.0, self.health + amount)
        return self.health - old_health
    
    # =========================================================================
    # Detection System - Vision, Hearing, Echo Sense
    # =========================================================================
    
    def get_vision_range(self) -> int:
        """Get vision detection range in tiles.
        
        Base range is 8 tiles, modified by equipment vision stat.
        """
        base_range = 8
        stats = self.get_equipment_stats()
        vision_bonus = stats.get("vision", 0.0)
        return int(base_range * (1.0 + vision_bonus))
    
    def get_hearing_range(self) -> int:
        """Get hearing detection range in tiles.
        
        Base range is 6 tiles, modified by equipment hearing stat.
        """
        base_range = 6
        stats = self.get_equipment_stats()
        hearing_bonus = stats.get("hearing", 0.0)
        return int(base_range * (1.0 + hearing_bonus))
    
    def get_echo_sense_range(self) -> int:
        """Get echo sense detection range in tiles.
        
        Base range is 4 tiles, modified by equipment echo_sense stat.
        Echo sense detects things through walls in high-echo environments.
        """
        base_range = 4
        stats = self.get_equipment_stats()
        echo_bonus = stats.get("echo_sense", 0.0)
        return int(base_range * (1.0 + echo_bonus))
    
    def can_see(self, target_x: int, target_y: int, target_z: int) -> bool:
        """Check if colonist can see a target position.
        
        Simple distance check - no line-of-sight yet.
        Must be on same Z-level.
        """
        if target_z != self.z:
            return False
        
        dx = abs(target_x - self.x)
        dy = abs(target_y - self.y)
        distance = max(dx, dy)  # Chebyshev distance
        
        return distance <= self.get_vision_range()
    
    def can_hear(self, target_x: int, target_y: int, target_z: int) -> bool:
        """Check if colonist can hear a target position.
        
        Hearing works through walls and across Z-levels (with penalty).
        """
        dx = abs(target_x - self.x)
        dy = abs(target_y - self.y)
        dz = abs(target_z - self.z)
        
        # Z-level difference reduces effective range
        distance = max(dx, dy) + (dz * 3)  # Each Z-level = 3 tiles of distance
        
        return distance <= self.get_hearing_range()
    
    def can_sense_echo(self, target_x: int, target_y: int, target_z: int, grid: Grid) -> bool:
        """Check if colonist can sense a target via echo.
        
        Echo sense is enhanced in high-echo environments.
        """
        dx = abs(target_x - self.x)
        dy = abs(target_y - self.y)
        dz = abs(target_z - self.z)
        
        base_distance = max(dx, dy) + (dz * 2)
        
        # Get echo level at colonist's position
        env_data = grid.get_env_data(self.x, self.y, self.z)
        echo_level = env_data.get("echo", 0.0)
        
        # High echo environments extend range
        effective_range = self.get_echo_sense_range() * (1.0 + echo_level)
        
        return base_distance <= effective_range
    
    def detect(self, target_x: int, target_y: int, target_z: int, grid: Grid) -> bool:
        """Check if colonist can detect a target position via any sense.
        
        Returns True if target is within vision, hearing, or echo sense range.
        """
        return (self.can_see(target_x, target_y, target_z) or 
                self.can_hear(target_x, target_y, target_z) or
                self.can_sense_echo(target_x, target_y, target_z, grid))
    
    # =========================================================================
    # Social System - Charisma, Intimidation
    # =========================================================================
    
    def get_charisma(self) -> float:
        """Get charisma stat from equipment."""
        stats = self.get_equipment_stats()
        return stats.get("charisma", 0.0)
    
    def get_intimidation(self) -> float:
        """Get intimidation stat from equipment."""
        stats = self.get_equipment_stats()
        return stats.get("intimidation", 0.0)
    
    def apply_social_effect(self, other: "Colonist", game_tick: int = 0) -> None:
        """Apply social effects to another colonist when nearby.
        
        Charisma: Boosts other's mood
        Intimidation: Increases other's stress
        
        Called when colonists are within social range (2 tiles).
        """
        # Get social stats
        charisma = self.get_charisma()
        intimidation = self.get_intimidation()
        
        # Charisma effect: small mood boost to others
        if charisma > 0:
            mood_boost = charisma * 0.01  # 1% of charisma per interaction
            other.comfort += mood_boost
            other.comfort = min(10.0, other.comfort)
            # Generate thought in the OTHER colonist about this colonist's charisma
            if charisma > 0.3 and random.random() < 0.01:  # Rare thought
                other._generate_social_thought(self.name, "charisma", game_tick)
        
        # Intimidation effect: small stress increase to others
        if intimidation > 0:
            stress_effect = intimidation * 0.01  # 1% of intimidation per interaction
            # Apply other's stress resist
            stress_resist = other.get_equipment_stress_resist()
            stress_effect *= (1.0 - min(0.8, stress_resist))
            other.stress += stress_effect
            other.stress = min(10.0, other.stress)
            # Generate thought in the OTHER colonist about this colonist's intimidation
            if intimidation > 0.3 and random.random() < 0.01:  # Rare thought
                other._generate_social_thought(self.name, "intimidation", game_tick)
    
    def process_social_interactions(self, nearby_colonists: list["Colonist"], game_tick: int = 0) -> None:
        """Process social interactions with nearby colonists.
        
        Called periodically to apply charisma/intimidation effects.
        """
        for other in nearby_colonists:
            if other is self or other.is_dead:
                continue
            
            # Check if within social range (2 tiles)
            dx = abs(other.x - self.x)
            dy = abs(other.y - self.y)
            if other.z == self.z and max(dx, dy) <= 2:
                self.apply_social_effect(other, game_tick)
    
    def regenerate_bio(self) -> None:
        """Regenerate bio based on current preferences. Call after preferences develop."""
        self.bio = generate_colonist_bio(self.preferences)
    
    def _generate_random_skin_tone(self) -> tuple[int, int, int]:
        """Generate a random skin tone for visual variety."""
        tones = [
            (255, 220, 177),  # Light
            (241, 194, 125),  # Medium-light
            (224, 172, 105),  # Medium
            (198, 134, 66),   # Medium-dark
            (141, 85, 36),    # Dark
        ]
        return random.choice(tones)
    
    def _generate_random_clothing_color(self) -> tuple[int, int, int]:
        """Generate a random clothing color for visual variety."""
        colors = [
            (70, 130, 180),   # Steel blue
            (139, 69, 19),    # Saddle brown
            (85, 107, 47),    # Dark olive green
            (128, 0, 0),      # Maroon
            (75, 75, 75),     # Dark gray
            (184, 134, 11),   # Dark goldenrod
            (47, 79, 79),     # Dark slate gray
        ]
        return random.choice(colors)

    # --- Carried Items Tracking ----------------------------------------------------------
    
    def pick_up_item(self, item: dict) -> None:
        """Track picking up an item. Updates carried_items dict."""
        if item is None:
            return
        res_type = item.get("type", "unknown")
        amount = item.get("amount", 1)
        self.carried_items[res_type] = self.carried_items.get(res_type, 0) + amount
    
    def drop_item(self, item: dict = None) -> None:
        """Track dropping an item. Updates carried_items dict.
        If item is None, clears all carried items (for interrupts/errors)."""
        if item is None:
            self.carried_items.clear()
            return
        res_type = item.get("type", "unknown")
        amount = item.get("amount", 1)
        current = self.carried_items.get(res_type, 0)
        new_amount = current - amount
        if new_amount <= 0:
            self.carried_items.pop(res_type, None)
        else:
            self.carried_items[res_type] = new_amount

    # --- Environment Sampling System -----------------------------------------------------
    
    def sample_environment(self, grid: Grid, all_colonists: list = None, game_tick: int = 0) -> None:
        """Sample the current environment and store it in recent_context.
        
        Captures:
        - Tile environmental parameters (interference, pressure, echo, integrity, is_outside, exit_count)
        - Room ID from tile data
        - Number of nearby colonists (radius 2)
        - Game tick (time-of-day proxy)
        
        Also updates colonist affinities based on experienced environment.
        """
        # Get environmental data from current tile
        env_data = grid.get_env_data(self.x, self.y, self.z).copy()
        
        # Count nearby colonists (radius 2)
        nearby_count = self._count_nearby_colonists(all_colonists or [])
        
        # Create sample
        sample = {
            "tick": game_tick,
            "x": self.x,
            "y": self.y,
            "z": self.z,
            "interference": env_data.get("interference", 0.0),
            "pressure": env_data.get("pressure", 0.0),
            "echo": env_data.get("echo", 0.0),
            "integrity": env_data.get("integrity", 1.0),
            "is_outside": env_data.get("is_outside", True),
            "room_id": env_data.get("room_id"),
            "exit_count": env_data.get("exit_count", 0),
            "nearby_colonists": nearby_count,
        }
        
        # Add to recent context (keep last 10)
        self.recent_context.append(sample)
        if len(self.recent_context) > self.max_context_samples:
            self.recent_context.pop(0)
        
        # Add to global statistics
        from environment_stats import add_environment_sample
        add_environment_sample(sample)
        
        # Update affinities based on this sample
        self._update_affinities(sample)
        
        # Update comfort/stress based on preference alignment with current environment
        self._update_comfort_stress(sample)
        
        # Maybe generate an environment thought
        self._generate_environment_thought(sample, game_tick)
    
    def _count_nearby_colonists(self, all_colonists: list) -> int:
        """Count colonists within radius 2 of this colonist."""
        count = 0
        for other in all_colonists:
            if other is self or other.is_dead:
                continue
            if other.z != self.z:
                continue
            
            dx = abs(other.x - self.x)
            dy = abs(other.y - self.y)
            distance = max(dx, dy)  # Chebyshev distance
            
            if distance <= 2:
                count += 1
        
        return count
    
    def _update_affinities(self, sample: dict) -> None:
        """Update colonist affinities based on environment sample.
        
        Compares sampled values to global averages and drifts affinities accordingly.
        If a value is above average, affinity drifts positive (preference).
        If below average, affinity drifts negative (dislike).
        
        Args:
            sample: Environment sample dictionary
        """
        from environment_stats import get_global_averages
        
        # Get global averages for comparison
        averages = get_global_averages()
        
        # Affinity drift rate (small increments)
        drift_rate = 0.01
        
        # Update each affinity based on comparison to global average
        # Interference
        if sample.get('interference', 0.0) > averages.get('interference', 0.0):
            self.affinity_interference = self._clamp_affinity(self.affinity_interference + drift_rate)
        else:
            self.affinity_interference = self._clamp_affinity(self.affinity_interference - drift_rate)
        
        # Echo
        if sample.get('echo', 0.0) > averages.get('echo', 0.0):
            self.affinity_echo = self._clamp_affinity(self.affinity_echo + drift_rate)
        else:
            self.affinity_echo = self._clamp_affinity(self.affinity_echo - drift_rate)
        
        # Pressure
        if sample.get('pressure', 0.0) > averages.get('pressure', 0.0):
            self.affinity_pressure = self._clamp_affinity(self.affinity_pressure + drift_rate)
        else:
            self.affinity_pressure = self._clamp_affinity(self.affinity_pressure - drift_rate)
        
        # Integrity
        if sample.get('integrity', 1.0) > averages.get('integrity', 1.0):
            self.affinity_integrity = self._clamp_affinity(self.affinity_integrity + drift_rate)
        else:
            self.affinity_integrity = self._clamp_affinity(self.affinity_integrity - drift_rate)
        
        # Outside (convert boolean to float for comparison)
        sample_outside = 1.0 if sample.get('is_outside', True) else 0.0
        if sample_outside > averages.get('outside', 0.5):
            self.affinity_outside = self._clamp_affinity(self.affinity_outside + drift_rate)
        else:
            self.affinity_outside = self._clamp_affinity(self.affinity_outside - drift_rate)
        
        # Crowding (based on nearby colonists)
        sample_crowding = float(sample.get('nearby_colonists', 0))
        if sample_crowding > averages.get('crowding', 0.0):
            self.affinity_crowding = self._clamp_affinity(self.affinity_crowding + drift_rate)
        else:
            self.affinity_crowding = self._clamp_affinity(self.affinity_crowding - drift_rate)
        
        # Update preference profile based on affinities and sample deviation from average
        # Formula: preference += affinity * (sample_value - global_average)
        self._update_preferences(sample, averages)
    
    def _update_preferences(self, sample: dict, averages: dict) -> None:
        """Update preference profile based on current affinities and environment sample.
        
        Each preference accumulates: affinity * (sample - global_average)
        This creates a stable personality direction over time.
        """
        # Calculate deviations from global averages
        interference_delta = sample.get('interference', 0.0) - averages.get('interference', 0.0)
        echo_delta = sample.get('echo', 0.0) - averages.get('echo', 0.0)
        pressure_delta = sample.get('pressure', 0.0) - averages.get('pressure', 0.0)
        integrity_delta = sample.get('integrity', 1.0) - averages.get('integrity', 1.0)
        
        # Outside: convert boolean to float
        sample_outside = 1.0 if sample.get('is_outside', True) else 0.0
        outside_delta = sample_outside - averages.get('outside', 0.5)
        
        # Crowding
        sample_crowding = float(sample.get('nearby_colonists', 0))
        crowding_delta = sample_crowding - averages.get('crowding', 0.0)
        
        # Update preferences: affinity * delta
        self.preferences["likes_interference"] = self._clamp_preference(
            self.preferences["likes_interference"] + self.affinity_interference * interference_delta
        )
        self.preferences["likes_echo"] = self._clamp_preference(
            self.preferences["likes_echo"] + self.affinity_echo * echo_delta
        )
        self.preferences["likes_pressure"] = self._clamp_preference(
            self.preferences["likes_pressure"] + self.affinity_pressure * pressure_delta
        )
        self.preferences["likes_integrity"] = self._clamp_preference(
            self.preferences["likes_integrity"] + self.affinity_integrity * integrity_delta
        )
        self.preferences["likes_outside"] = self._clamp_preference(
            self.preferences["likes_outside"] + self.affinity_outside * outside_delta
        )
        self.preferences["likes_crowding"] = self._clamp_preference(
            self.preferences["likes_crowding"] + self.affinity_crowding * crowding_delta
        )
    
    def _clamp_preference(self, value: float) -> float:
        """Clamp preference value to [-10.0, 10.0] range."""
        return max(-10.0, min(10.0, value))
    
    def get_top_preferences(self) -> tuple[list[tuple[str, float]], list[tuple[str, float]]]:
        """Get top 2 positive and top 1 negative preferences.
        
        Returns:
            (top_positive, top_negative) - lists of (name, value) tuples
        """
        # Sort preferences by value
        sorted_prefs = sorted(self.preferences.items(), key=lambda x: x[1], reverse=True)
        
        # Get top 2 positive (value > 0)
        top_positive = [(name, val) for name, val in sorted_prefs if val > 0][:2]
        
        # Get top 1 negative (value < 0, most negative first)
        top_negative = [(name, val) for name, val in reversed(sorted_prefs) if val < 0][:1]
        
        return top_positive, top_negative
    
    def _update_comfort_stress(self, sample: dict) -> None:
        """Update comfort and stress based on preference alignment with environment.
        
        Computes comfort_change by multiplying each preference by the corresponding
        tile parameter value. Positive result = environment matches preferences.
        
        Args:
            sample: Environment sample dictionary with tile parameters
        """
        # Get tile parameter values
        tile_interference = sample.get('interference', 0.0)
        tile_echo = sample.get('echo', 0.0)
        tile_pressure = sample.get('pressure', 0.0)
        tile_integrity = sample.get('integrity', 1.0)
        tile_outside = 1.0 if sample.get('is_outside', True) else 0.0
        tile_crowding = float(sample.get('nearby_colonists', 0))
        
        # Calculate individual contributions for tracking strongest influence
        contributions = {
            "interference": self.preferences["likes_interference"] * tile_interference,
            "echo": self.preferences["likes_echo"] * tile_echo,
            "pressure": self.preferences["likes_pressure"] * tile_pressure,
            "integrity": self.preferences["likes_integrity"] * tile_integrity,
            "outside": self.preferences["likes_outside"] * tile_outside,
            "crowding": self.preferences["likes_crowding"] * tile_crowding,
        }
        
        # Sum all contributions for total comfort change
        comfort_change = sum(contributions.values())
        
        # Find strongest influence (by absolute value)
        strongest_param = max(contributions.keys(), key=lambda k: abs(contributions[k]))
        self.comfort_influence = (strongest_param, contributions[strongest_param])
        
        # Clamp comfort_change to small range per tick
        comfort_change = max(-0.1, min(0.1, comfort_change))
        
        # Apply stress resist from equipment (reduces stress gain, not comfort loss)
        stress_resist = self.get_equipment_stress_resist()
        stress_change = -comfort_change  # Inverse of comfort
        if stress_change > 0:
            # Only reduce stress GAIN, not stress loss
            stress_change *= (1.0 - min(0.8, stress_resist))  # Cap at 80% reduction
        
        # Comfort-based stress recovery: high comfort accelerates stress reduction
        # Equipment comfort bonus (warmth, comfort items) helps recover stress faster
        if self.stress > 0 and self.comfort > 0:
            equip_comfort = self.get_equipment_comfort_bonus()
            # Base recovery rate + bonus from equipment comfort
            recovery_rate = 0.01 * (1.0 + equip_comfort + self.comfort * 0.05)
            stress_change -= recovery_rate  # Reduce stress
        
        # Update comfort and stress
        self.comfort = self._clamp_comfort_stress(self.comfort + comfort_change)
        self.stress = self._clamp_comfort_stress(self.stress + stress_change)
        
        # Apply preference drift based on current comfort/stress
        self._apply_preference_drift(sample)
        
        # Update mood state based on comfort and stress
        self._update_mood_state()
    
    def _apply_preference_drift(self, sample: dict) -> None:
        """Apply slow preference drift based on comfort/stress state.
        
        When comfortable (comfort > stress), preferences drift toward current environment.
        When stressed (stress > comfort), preferences drift away from current environment.
        
        Args:
            sample: Environment sample dictionary with tile parameters
        """
        # Calculate drift value based on comfort-stress difference
        drift = (self.comfort - self.stress) * self.preference_drift_rate
        
        # Clamp drift to very small range
        drift = max(-0.001, min(0.001, drift))
        
        # Get tile parameter values
        tile_interference = sample.get('interference', 0.0)
        tile_echo = sample.get('echo', 0.0)
        tile_pressure = sample.get('pressure', 0.0)
        tile_integrity = sample.get('integrity', 1.0)
        tile_outside = 1.0 if sample.get('is_outside', True) else 0.0
        tile_crowding = float(sample.get('nearby_colonists', 0))
        
        # Calculate individual preference changes
        pref_changes = {
            "likes_interference": drift * tile_interference,
            "likes_echo": drift * tile_echo,
            "likes_pressure": drift * tile_pressure,
            "likes_integrity": drift * tile_integrity,
            "likes_outside": drift * tile_outside,
            "likes_crowding": drift * tile_crowding,
        }
        
        # Apply changes and clamp preferences
        for pref_key, change in pref_changes.items():
            self.preferences[pref_key] = self._clamp_preference_drift(
                self.preferences[pref_key] + change
            )
        
        # Track total drift and strongest change for debug
        self.last_total_drift = sum(abs(c) for c in pref_changes.values())
        
        # Find strongest change
        strongest_key = max(pref_changes.keys(), key=lambda k: abs(pref_changes[k]))
        self.last_drift_strongest = (
            strongest_key.replace("likes_", ""),
            pref_changes[strongest_key]
        )
    
    def _clamp_preference_drift(self, value: float) -> float:
        """Clamp preference value to [-5.0, 5.0] range for drift system."""
        return max(-5.0, min(5.0, value))
    
    def _clamp_comfort_stress(self, value: float) -> float:
        """Clamp comfort/stress value to [-10.0, 10.0] range."""
        return max(-10.0, min(10.0, value))
    
    def _clamp_affinity(self, value: float) -> float:
        """Clamp affinity value to [-1.0, 1.0] range."""
        return max(-1.0, min(1.0, value))
    
    def _update_mood_state(self) -> None:
        """Update mood state based on comfort, stress, and equipment.
        
        Computes mood_score = comfort + equipment_comfort - stress and classifies into mood states.
        Equipment comfort bonus is added to base comfort for mood calculation.
        """
        equipment_comfort = self.get_equipment_comfort_bonus()
        self.mood_score = self.comfort + equipment_comfort - self.stress
        
        old_mood = self.mood_state
        
        if self.mood_score > 10:
            self.mood_state = "Euphoric"
        elif self.mood_score > 5:
            self.mood_state = "Calm"
        elif self.mood_score > 0:
            self.mood_state = "Focused"
        elif self.mood_score > -5:
            self.mood_state = "Uneasy"
        elif self.mood_score > -10:
            self.mood_state = "Stressed"
        else:
            self.mood_state = "Overwhelmed"
        
        # Generate thought when mood changes significantly
        if self.mood_state != old_mood and old_mood != self.last_mood_state:
            self._generate_mood_thought(self.mood_state, self._game_tick)
            self.last_mood_state = old_mood
    
    @staticmethod
    def get_mood_color(mood_state: str) -> tuple[int, int, int]:
        """Get the display color for a mood state."""
        mood_colors = {
            "Euphoric": (100, 255, 100),     # Bright green
            "Calm": (150, 200, 255),         # Soft blue
            "Focused": (100, 220, 220),      # Cyan
            "Uneasy": (255, 255, 100),       # Yellow
            "Stressed": (255, 180, 80),      # Orange
            "Overwhelmed": (255, 80, 80),    # Red
        }
        return mood_colors.get(mood_state, (200, 200, 200))
    
    def get_mood_speed_modifier(self) -> float:
        """Get movement speed modifier based on mood state.
        
        Returns:
            Multiplier for movement speed:
            - Comfortable moods (Euphoric, Calm): +10% speed (0.9 move_speed multiplier)
            - Neutral moods (Focused): no change (1.0)
            - Stressed moods (Uneasy, Stressed, Overwhelmed): -10% speed (1.1 move_speed multiplier)
        
        Note: Lower move_speed value = faster movement (fewer ticks between moves)
        """
        if self.mood_state in ("Euphoric", "Calm"):
            return 0.9  # 10% faster (lower cooldown)
        elif self.mood_state in ("Uneasy", "Stressed", "Overwhelmed"):
            return 1.1  # 10% slower (higher cooldown)
        else:
            return 1.0  # No change (Focused)
    
    def get_mood_speed_display(self) -> str:
        """Get human-readable speed modifier for UI display."""
        modifier = self.get_mood_speed_modifier()
        if modifier < 1.0:
            percent = int((1.0 - modifier) * 100)
            return f"+{percent}%"
        elif modifier > 1.0:
            percent = int((modifier - 1.0) * 100)
            return f"-{percent}%"
        else:
            return "0%"
    
    def check_stumble(self, grid: Grid) -> int:
        """Check if colonist stumbles on current tile based on environment and walk_steady.
        
        Stumbling occurs in high-interference/hazard tiles. Walk Steady stat reduces chance.
        
        Args:
            grid: The game grid to check environmental data
            
        Returns:
            Extra move delay ticks if stumbled, 0 otherwise
        """
        import random
        
        # Get environmental hazard level from current tile
        env_data = grid.get_env_data(self.x, self.y, self.z)
        interference = env_data.get("interference", 0.0)
        pressure = env_data.get("pressure", 0.0)
        integrity = env_data.get("integrity", 1.0)
        
        # Calculate hazard factor (0-1 scale)
        # High interference, high pressure, or low integrity = more hazardous
        hazard_factor = (interference * 0.5) + (pressure * 0.3) + ((1.0 - integrity) * 0.2)
        
        # No stumble chance if hazard is negligible
        if hazard_factor < 0.1:
            return 0
        
        # Get walk_steady from equipment (0 = no bonus, higher = more stable)
        stats = self.get_equipment_stats()
        walk_steady = stats.get("walk_steady", 0.0)
        
        # Calculate stumble chance: hazard_factor minus walk_steady bonus
        # walk_steady of 0.5 would halve the stumble chance
        stumble_chance = hazard_factor * (1.0 - min(0.9, walk_steady))  # Cap at 90% reduction
        
        # Roll for stumble
        if random.random() < stumble_chance:
            # Stumbled! Add extra move delay (2-4 ticks based on hazard severity)
            extra_delay = int(2 + hazard_factor * 2)
            return extra_delay
        
        return 0
    
    def _calculate_work_modifier(self, job_type: str) -> float:
        """Calculate total work speed modifier for a job.
        
        Combines:
        - Equipment bonuses (job-type specific)
        - Mood effects (focused = bonus, stressed = penalty)
        - Stress effects (high stress = penalty)
        
        Args:
            job_type: "construction", "gathering", or "crafting"
        
        Returns:
            Multiplier for work progress (1.0 = normal, >1 = faster, <1 = slower)
        """
        # Map job types to equipment categories
        job_type_map = {
            "construction": "construction",
            "gathering": "gathering",
            "crafting": "crafting",
            "cooking": "crafting",  # Cooking uses craft speed
            "salvage": "gathering",  # Salvage uses harvest speed
        }
        equip_job_type = job_type_map.get(job_type, "construction")
        
        # Base modifier from equipment
        modifier = self.get_equipment_work_modifier(equip_job_type)
        
        # Mood effects on work speed
        if self.mood_state == "Euphoric":
            modifier *= 1.15  # 15% faster when euphoric
        elif self.mood_state == "Calm":
            modifier *= 1.10  # 10% faster when calm
        elif self.mood_state == "Focused":
            modifier *= 1.05  # 5% bonus for focused (default good state)
        elif self.mood_state == "Uneasy":
            modifier *= 0.95  # 5% slower when uneasy
        elif self.mood_state == "Stressed":
            modifier *= 0.85  # 15% slower when stressed
        elif self.mood_state == "Overwhelmed":
            modifier *= 0.70  # 30% slower when overwhelmed
        
        # High stress penalty (stacks with mood)
        if self.stress > 8:
            modifier *= 0.75  # 25% penalty for very high stress
        elif self.stress > 6:
            modifier *= 0.90  # 10% penalty for high stress
        
        # Low stress bonus
        if self.stress < 2 and self.comfort > 3:
            modifier *= 1.05  # 5% bonus for calm and comfortable
        
        return modifier
    
    # --- Job Tag System -----------------------------------------------------
    
    def can_perform_job_category(self, category: str) -> bool:
        """Check if colonist can perform a job based on job tags.
        
        Maps job categories to job tags:
        - construction, wall, fire_escape → can_build
        - haul, supply → can_haul
        - crafting → can_craft
        - cooking → can_cook
        - salvage, harvest → can_scavenge
        """
        # Map job categories to job tags
        category_to_tag = {
            "construction": "can_build",
            "wall": "can_build",
            "fire_escape": "can_build",
            "haul": "can_haul",
            "supply": "can_haul",
            "crafting": "can_craft",
            "cooking": "can_cook",
            "salvage": "can_scavenge",
            "harvest": "can_scavenge",
            "equip": None,  # Anyone can equip items - no tag restriction
        }
        
        # Get the corresponding tag
        tag = category_to_tag.get(category)
        if tag is None:
            # Unknown category - allow by default for compatibility
            return True
        
        # Check if colonist has this tag enabled
        return self.job_tags.get(tag, True)
    
    # --- Job Desirability Scoring -------------------------------------------
    
    # Job type to typical environment mapping
    # Maps job categories to which environment parameters they typically involve
    JOB_ENVIRONMENT_AFFINITY = {
        "harvest": {"outside": 1.0, "integrity": 0.5},      # Outdoor work, some structure
        "haul": {"outside": 0.8, "crowding": 0.3},          # Mostly outdoor, some social
        "construction": {"integrity": 0.8, "outside": 0.5}, # Building = integrity focus
        "wall": {"integrity": 0.8, "outside": 0.5},
        "crafting": {"interference": 0.5, "echo": 0.3},     # Indoor workstation work
        "cooking": {"interference": 0.3, "pressure": 0.3},  # Indoor kitchen work
        "salvage": {"outside": 0.7, "integrity": -0.5},     # Outdoor, low integrity areas
        "supply": {"outside": 0.5, "crowding": 0.3},        # Similar to haul
    }
    
    def calculate_job_desirability(self, job_category: str, job_x: int = None, job_y: int = None, job_z: int = None, grid = None) -> float:
        """Calculate how desirable a job is for this colonist.
        
        Formula:
            desirability = base_value + mood_factor + affinity_bonus + environment_match_bonus
        
        Args:
            job_category: The job category (harvest, haul, construction, etc.)
            job_x, job_y, job_z: Optional job location for environment matching
            grid: Optional grid for environment data lookup
        
        Returns:
            Desirability score (higher = more desirable)
        """
        # Base value - all jobs start equal
        base_value = 1.0
        
        # Mood factor - happier colonists are slightly more motivated
        # mood_score ranges roughly -20 to +20, scale to ±1.0
        mood_factor = self.mood_score * 0.05
        
        # Affinity bonus - based on preference profile matching job's typical environment
        affinity_bonus = self._calculate_affinity_bonus(job_category)
        
        # Environment match bonus - if job location is provided, check tile environment
        environment_bonus = 0.0
        if job_x is not None and job_y is not None and grid is not None:
            environment_bonus = self._calculate_environment_bonus(job_x, job_y, job_z or 0, grid)
        
        return base_value + mood_factor + affinity_bonus + environment_bonus
    
    def _calculate_affinity_bonus(self, job_category: str) -> float:
        """Calculate bonus based on preference profile matching job's typical environment."""
        bonus = 0.0
        
        env_affinity = self.JOB_ENVIRONMENT_AFFINITY.get(job_category, {})
        
        for param, weight in env_affinity.items():
            pref_key = f"likes_{param}"
            pref_value = self.preferences.get(pref_key, 0.0)
            
            # If colonist likes this parameter and job involves it positively, bonus
            # If colonist dislikes and job involves it, penalty
            # Scale: preference (-5 to +5) * weight * 0.04 = max ±0.2 per param
            bonus += pref_value * weight * 0.04
        
        # Clamp to reasonable range
        return max(-0.3, min(0.3, bonus))
    
    def _calculate_environment_bonus(self, x: int, y: int, z: int, grid) -> float:
        """Calculate bonus based on job tile's environment matching preferences."""
        bonus = 0.0
        
        # Get environment data for the job tile
        env_data = grid.get_env_data(x, y, z)
        
        # Check each preference against the tile's environment
        # Interference
        tile_interference = env_data.get('interference', 0.0)
        if abs(tile_interference) > 0.1:
            pref = self.preferences.get("likes_interference", 0.0)
            bonus += pref * tile_interference * 0.02  # Small effect
        
        # Echo
        tile_echo = env_data.get('echo', 0.0)
        if abs(tile_echo) > 0.1:
            pref = self.preferences.get("likes_echo", 0.0)
            bonus += pref * tile_echo * 0.02
        
        # Pressure
        tile_pressure = env_data.get('pressure', 0.0)
        if abs(tile_pressure) > 0.1:
            pref = self.preferences.get("likes_pressure", 0.0)
            bonus += pref * tile_pressure * 0.02
        
        # Integrity
        tile_integrity = env_data.get('integrity', 1.0)
        pref = self.preferences.get("likes_integrity", 0.0)
        bonus += pref * (tile_integrity - 0.5) * 0.04  # Center around 0.5
        
        # Outside
        is_outside = 1.0 if env_data.get('is_outside', True) else 0.0
        pref = self.preferences.get("likes_outside", 0.0)
        bonus += pref * (is_outside - 0.5) * 0.04  # Center around 0.5
        
        # Clamp to reasonable range
        return max(-0.2, min(0.2, bonus))
    
    def get_job_desirability_summary(self, grid = None) -> dict[str, float]:
        """Get desirability scores for all job categories.
        
        Returns dict of category -> score for UI display.
        """
        categories = ["harvest", "haul", "construction", "crafting", "cooking", "salvage"]
        result = {}
        
        for cat in categories:
            # Calculate without specific location (general desirability)
            result[cat] = self.calculate_job_desirability(cat, grid=grid)
        
        return result
    
    # --- Core behavior -----------------------------------------------------

    def _maybe_wander_when_idle(self, grid: Grid) -> None:
        """Preserve the original random wandering when idle.

        This keeps the world visually alive when there is no work.
        Now respects walkability to avoid walking through buildings.
        Colonists wander on their current Z-level.
        """

        if random.random() < 0.02:  # 2% chance each frame
            dx, dy = random.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
            new_x = max(0, min(GRID_W - 1, self.x + dx))
            new_y = max(0, min(GRID_H - 1, self.y + dy))
            
            # Only move if the target tile is walkable on current Z-level
            if grid.is_walkable(new_x, new_y, self.z):
                self.x = new_x
                self.y = new_y

    def _try_take_job(self, grid: Grid = None) -> None:
        """Claim a job from the global queue if available.
        
        Uses pressure-based selection:
        1. First check for urgent jobs (pressure > colonist.pressure_score)
        2. If urgent job found and should_take_job() returns True, take it
        3. Otherwise use normal desirability scoring
        
        Args:
            grid: Optional grid for environment-based desirability scoring
        """
        # Get all available jobs
        available_jobs = get_all_available_jobs(skip_types=[], skip_unready_construction=True)
        
        if not available_jobs:
            return
        
        # Filter to jobs this colonist can perform
        valid_jobs = [j for j in available_jobs if self.can_perform_job_category(j.category)]
        
        if not valid_jobs:
            return
        
        # Step 1: Check for jobs that could interrupt current work
        # Only matters if colonist is already working
        if self.current_job is not None:
            # Find jobs with higher pressure than current that we're willing to switch to
            # Colonist score must be >= job pressure to be interruptible
            interruptible_jobs = [
                j for j in valid_jobs 
                if j.pressure > self.current_job.pressure  # More urgent than current
                and self.pressure_score >= j.pressure      # Colonist willing to switch
            ]
            
            if interruptible_jobs:
                # Sort by pressure (highest first) and take the most urgent
                interruptible_jobs.sort(key=lambda j: j.pressure, reverse=True)
                self._assign_job(interruptible_jobs[0], grid)
                return
        
        # Step 2: No urgent jobs or none passed the check - use priority scoring
        # Only take normal jobs if idle
        if self.current_job is not None:
            return
        
        # Score each job by priority (higher = more important)
        # Priority order: crafting > construction > haul > harvest
        # Within construction: workstation > door > wall > floor
        scored_jobs = []
        for job in valid_jobs:
            priority = get_job_priority(job)
            # Add small desirability bonus for tie-breaking (personality flavor)
            desirability = self.calculate_job_desirability(
                job.category, 
                job.x, job.y, job.z,
                grid=grid
            )
            # Priority dominates, desirability is tie-breaker (scaled down)
            score = priority + (desirability * 0.1)
            scored_jobs.append((score, job))
        
        # Sort by score descending
        scored_jobs.sort(key=lambda x: x[0], reverse=True)
        
        # Take the highest-priority job
        _, job = scored_jobs[0]
        self._assign_job(job, grid)
    
    def _assign_job(self, job: Job, grid: Grid = None) -> None:
        """Assign a job to this colonist, handling state transitions.
        
        Args:
            job: The job to assign
            grid: Optional grid reference
        """
        # If we have a current job, release it first
        if self.current_job is not None:
            self._release_current_job()
        
        job.assigned = True
        self.current_job = job
        self.current_path = []  # Will be calculated on first move
        self.stuck_timer = 0
        
        # Set resource node to RESERVED state if this is a gathering job
        if job.type == "gathering":
            set_node_state(job.x, job.y, NodeState.RESERVED)
            self.state = "moving_to_job"
        elif job.type == "crafting":
            # Reserve workstation and start fetching materials
            buildings.reserve_workstation(job.x, job.y, job.z)
            self.state = "crafting_fetch"
            self._crafting_inputs_needed = None  # Will be set when we start fetching
        else:
            self.state = "moving_to_job"
    
    def _release_current_job(self) -> None:
        """Release the current job back to the queue."""
        if self.current_job is None:
            return
        
        job = self.current_job
        job.assigned = False
        
        # Release any reserved resources
        if job.type == "gathering":
            set_node_state(job.x, job.y, NodeState.IDLE)
        elif job.type == "crafting":
            buildings.release_workstation(job.x, job.y, job.z)
        
        self.current_job = None
        self.current_path = []

    def _calculate_path(self, grid: Grid, target_x: int, target_y: int, target_z: int = 0) -> list[tuple[int, int, int]]:
        """Calculate path to target using BFS with z-level support.
        
        Returns list of (x, y, z) positions to follow.
        
        Fire escape path: Floor → WindowTile → Platform (z=0) → RoofFloor (z=1)
        - WindowTile is at the wall position (passable)
        - Platform is adjacent to the window (external)
        - RoofFloor is above the platform at z=1
        """
        start = (self.x, self.y, self.z)
        goal = (target_x, target_y, target_z)
        
        if start == goal:
            return []
        
        # Get fire escape locations for z-level transitions
        from buildings import get_all_fire_escapes, is_fire_escape_complete
        fire_escapes = get_all_fire_escapes()
        
        # Build a map of (platform_x, platform_y, z) -> fire escape data
        # Fire escapes connect Z to Z+1 at the platform position
        platform_transitions = {}
        for (wx, wy, wz), escape_data in fire_escapes.items():
            if is_fire_escape_complete(wx, wy, wz):
                platform_pos = escape_data.get("platform_pos")
                if platform_pos:
                    px, py = platform_pos
                    # Platform at Z can go up to Z+1
                    # Platform at Z+1 can go down to Z
                    platform_transitions[(px, py, wz)] = wz + 1  # Go up
                    platform_transitions[(px, py, wz + 1)] = wz  # Go down
        
        # BFS to find shortest path across z-levels
        from collections import deque
        queue = deque([(start, [start])])
        visited = {start}
        
        while queue:
            (cx, cy, cz), path = queue.popleft()
            
            # Regular 2D movement on current z-level
            for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                nx, ny, nz = cx + dx, cy + dy, cz
                
                if (nx, ny, nz) in visited:
                    continue
                
                # Can move to target or any walkable tile on this z-level
                is_goal = (nx, ny, nz) == goal
                is_walkable = grid.is_walkable(nx, ny, nz)
                
                if is_goal or is_walkable:
                    new_path = path + [(nx, ny, nz)]
                    if is_goal:
                        # Return path without start position
                        return new_path[1:]
                    visited.add((nx, ny, nz))
                    queue.append(((nx, ny, nz), new_path))
            
            # Z-level transition via fire escape platforms
            # Fire escapes allow vertical movement between adjacent Z-levels
            if (cx, cy, cz) in platform_transitions:
                other_z = platform_transitions[(cx, cy, cz)]
                if (cx, cy, other_z) not in visited:
                    other_tile = grid.get_tile(cx, cy, other_z)
                    # Can transition to platform on other Z (or any walkable tile)
                    if other_tile == "fire_escape_platform" or grid.is_walkable(cx, cy, other_z):
                        is_goal = (cx, cy, other_z) == goal
                        new_path = path + [(cx, cy, other_z)]
                        if is_goal:
                            return new_path[1:]
                        visited.add((cx, cy, other_z))
                        queue.append(((cx, cy, other_z), new_path))
        
        # No path found
        return []

    def _move_towards_job(self, grid: Grid) -> None:
        """Move along committed path toward job location."""

        if self.current_job is None:
            self.state = "idle"
            return

        target_x = self.current_job.x
        target_y = self.current_job.y
        target_z = self.current_job.z  # Use job's z-level

        # Already at target (including z-level)
        if self.x == target_x and self.y == target_y and self.z == target_z:
            self.state = "working"
            self.current_path = []
            self.stuck_timer = 0
            
            # Set resource node to IN_PROGRESS state when starting work
            if self.current_job and self.current_job.type == "gathering":
                set_node_state(target_x, target_y, NodeState.IN_PROGRESS)
            return
        
        # Movement speed control - only move every N ticks
        if self.move_cooldown > 0:
            self.move_cooldown -= 1
            return
        
        # Calculate path if we don't have one
        if not self.current_path:
            self.current_path = self._calculate_path(grid, target_x, target_y, target_z)
            self.stuck_timer = 0
            
            if not self.current_path:
                # No path exists - increment stuck timer
                self.stuck_timer += 1
                if self.stuck_timer > self.max_stuck_time:
                    # Give up on this job - reset node state if gathering
                    job = self.current_job
                    print(f"[Stuck] Colonist at ({self.x},{self.y},z={self.z}) gave up on {job.type} job at ({job.x},{job.y},z={job.z})")
                    if job.type == "gathering":
                        set_node_state(job.x, job.y, NodeState.IDLE)
                    job.assigned = False
                    self.current_job = None
                    self.state = "idle"
                    self.stuck_timer = 0
                return
        
        # Get next step in path (now includes z)
        next_pos = self.current_path[0]
        next_x, next_y, next_z = next_pos
        
        # Check if next step is still valid
        is_target = (next_x == target_x and next_y == target_y and next_z == target_z)
        is_walkable = grid.is_walkable(next_x, next_y, next_z)
        
        # Check if next tile is a closed door - open it
        if is_door(next_x, next_y, next_z) and not is_door_open(next_x, next_y, next_z):
            open_door(next_x, next_y, next_z)
            is_walkable = True  # Door is now open
        
        # Check if next tile is a closed window - open it (slower than doors)
        if is_window(next_x, next_y, next_z) and not is_window_open(next_x, next_y, next_z):
            open_window(next_x, next_y, next_z)
            is_walkable = True  # Window is now open
        
        if is_target or is_walkable:
            # Move to next position (including z-level change)
            self.x = next_x
            self.y = next_y
            self.z = next_z
            self.current_path.pop(0)
            
            # Apply mood and equipment speed modifiers
            # Both are multipliers on move_speed (lower = faster)
            combined_modifier = self.get_mood_speed_modifier() * self.get_equipment_speed_modifier()
            base_speed = int(self.move_speed * combined_modifier)
            
            # Windows have a movement speed penalty (climbing through)
            if is_window(next_x, next_y, next_z):
                self.move_cooldown = base_speed * 2  # Double delay for windows
            else:
                self.move_cooldown = base_speed
            
            # Check for stumble in hazardous tiles
            stumble_delay = self.check_stumble(grid)
            if stumble_delay > 0:
                self.move_cooldown += stumble_delay
            
            self.stuck_timer = 0
        else:
            # Path blocked (wall built, door placed, etc.) - recalculate immediately
            self.current_path = []
            self.stuck_timer += 1
            
            # Add a small delay before retrying to avoid spinning
            self.move_cooldown = self.move_speed * 2  # No mood modifier for stuck delay
            
            if self.stuck_timer > self.max_stuck_time:
                # Give up on this job - reset node state if gathering
                job = self.current_job
                print(f"[Stuck] Colonist at ({self.x},{self.y},z={self.z}) path blocked to {job.type} job at ({job.x},{job.y},z={job.z})")
                if job.type == "gathering":
                    set_node_state(job.x, job.y, NodeState.IDLE)
                job.assigned = False
                self.current_job = None
                self.state = "idle"
                self.stuck_timer = 0

    def _work_on_job(self, grid: Grid) -> None:
        """Advance progress on the current job and complete it if finished."""

        if self.current_job is None:
            self.state = "idle"
            return

        job = self.current_job
        
        # Double-check construction has materials (shouldn't happen but safety)
        if job.type == "construction":
            # Check if waiting for stockpile items to be relocated
            if buildings.is_awaiting_stockpile_clear(job.x, job.y, job.z):
                # Can't work yet - wait for items to be moved
                job.assigned = False
                job.wait_timer = 60  # Don't reassign immediately
                self.current_job = None
                self.state = "idle"
                return
            if not has_required_materials(job.x, job.y, job.z):
                # Materials not delivered - release job and wait
                job.assigned = False
                job.wait_timer = 60  # Don't reassign immediately - wait for supply
                self.current_job = None
                self.state = "idle"
                return
        
        # Apply work modifier based on job type, equipment, mood, and stress
        work_modifier = self._calculate_work_modifier(job.type)
        job.progress += work_modifier
        
        # Log work progress on first tick of job (to verify equipment effects)
        if job.progress <= work_modifier + 0.01:  # First tick
            if work_modifier != 1.0:
                print(f"[Work] {self.name} working on {job.type} at {work_modifier:.0%} speed")
        
        # Sample environment on every job tick
        self.sample_environment(grid, self._all_colonists, self._game_tick)
        
        # For gathering jobs, harvest resources incrementally
        if job.type == "gathering":
            harvest_tick(job.x, job.y, int(job.progress), job.required)

        if job.progress >= job.required:
            # Log job completion with timing info
            if work_modifier != 1.0:
                expected_ticks = job.required
                actual_ticks = int(job.required / work_modifier)
                saved = expected_ticks - actual_ticks
                print(f"[Work] {self.name} finished {job.type} in ~{actual_ticks} ticks (saved ~{saved} ticks from {work_modifier:.0%} speed)")
            
            # Sample environment on job completion
            self.sample_environment(grid, self._all_colonists, self._game_tick)
            # Dispatch completion based on job type.
            if job.type == "construction":
                # Check what type of construction this was
                current_tile = grid.get_tile(job.x, job.y, job.z)
                if current_tile == "wall":
                    grid.set_tile(job.x, job.y, "finished_wall", z=job.z)
                elif current_tile == "wall_advanced":
                    grid.set_tile(job.x, job.y, "finished_wall_advanced", z=job.z)
                elif current_tile == "door":
                    # Door stays as "door" tile - state managed separately
                    pass
                elif current_tile == "floor":
                    grid.set_tile(job.x, job.y, "finished_floor", z=job.z)
                elif current_tile == "window":
                    grid.set_tile(job.x, job.y, "finished_window", z=job.z)
                    register_window(job.x, job.y, job.z)  # Register for open/close state
                elif current_tile == "fire_escape":
                    # Fire escape completion creates:
                    # 1. WindowTile at wall position (x, y, z) - passable wall
                    # 2. Platform at adjacent position on BOTH Z and Z+1
                    #    - Z: fire_escape_platform (current level balcony)
                    #    - Z+1: fire_escape_platform (upper level balcony, walkable)
                    
                    # Get platform position from fire escape data
                    platform_pos = buildings.get_fire_escape_platform(job.x, job.y, job.z)
                    if platform_pos:
                        px, py = platform_pos
                        
                        # Set window tile at wall position (passable wall)
                        grid.set_tile(job.x, job.y, "window_tile", z=job.z)
                        
                        # Set platform at adjacent position on current Z
                        grid.set_tile(px, py, "fire_escape_platform", z=job.z)
                        
                        # Set platform on Z+1 as well (balcony extends to upper level)
                        # This creates a proper floor tile colonists can stand on
                        grid.set_tile(px, py, "fire_escape_platform", z=job.z + 1)
                        
                        # Mark fire escape as complete
                        buildings.mark_fire_escape_complete(job.x, job.y, job.z)
                    else:
                        # Fallback if no platform data (shouldn't happen)
                        grid.set_tile(job.x, job.y, "window_tile", z=job.z)
                elif current_tile == "bridge":
                    grid.set_tile(job.x, job.y, "finished_bridge", z=job.z)
                elif current_tile == "salvagers_bench":
                    grid.set_tile(job.x, job.y, "finished_salvagers_bench", z=job.z)
                    # Register as workstation
                    buildings.register_workstation(job.x, job.y, job.z, "salvagers_bench")
                elif current_tile == "generator":
                    grid.set_tile(job.x, job.y, "finished_generator", z=job.z)
                    # Register as workstation
                    buildings.register_workstation(job.x, job.y, job.z, "generator")
                elif current_tile == "stove":
                    grid.set_tile(job.x, job.y, "finished_stove", z=job.z)
                    # Register as workstation
                    buildings.register_workstation(job.x, job.y, job.z, "stove")
                elif current_tile == "gutter_forge":
                    grid.set_tile(job.x, job.y, "finished_gutter_forge", z=job.z)
                    buildings.register_workstation(job.x, job.y, job.z, "gutter_forge")
                elif current_tile == "skinshop_loom":
                    grid.set_tile(job.x, job.y, "finished_skinshop_loom", z=job.z)
                    buildings.register_workstation(job.x, job.y, job.z, "skinshop_loom")
                elif current_tile == "cortex_spindle":
                    grid.set_tile(job.x, job.y, "finished_cortex_spindle", z=job.z)
                    buildings.register_workstation(job.x, job.y, job.z, "cortex_spindle")
                else:
                    grid.set_tile(job.x, job.y, "finished_building", z=job.z)
                buildings.remove_construction_site(job.x, job.y, job.z)
                remove_job(job)
                self.current_job = None
                self.state = "idle"
                # Generate work thought
                self._generate_work_thought("building_complete", self._game_tick)
                # Mark tile dirty for room detection (batched at end of tick)
                from rooms import mark_tile_dirty
                mark_tile_dirty(job.x, job.y, job.z)
            elif job.type == "gathering":
                complete_gathering_job(grid, job)
                remove_job(job)
                # Remove designation when job completes
                remove_designation(job.x, job.y, job.z)
                self.current_job = None
                self.state = "idle"
                # Generate work thought
                self._generate_work_thought("harvesting_complete", self._game_tick)
            elif job.type == "haul":
                # Pickup phase complete - pick up the item and start hauling
                # Check if this is an equipment haul or resource haul
                if job.resource_type == "equipment":
                    # Equipment haul - pick up from world items
                    from items import pickup_world_item
                    item = pickup_world_item(job.x, job.y, job.z)
                    if item is not None:
                        # Convert to carrying format
                        self.carrying = {"type": "equipment", "amount": 1, "item": item}
                        self.pick_up_item(self.carrying)
                        self.state = "hauling"
                        self.current_path = []
                        remove_designation(job.x, job.y, job.z)
                    else:
                        remove_job(job)
                        remove_designation(job.x, job.y, job.z)
                        self.current_job = None
                        self.state = "idle"
                else:
                    # Resource haul
                    item = pickup_resource_item(job.x, job.y, job.z)
                    if item is not None:
                        self.carrying = item
                        self.pick_up_item(item)
                        self.state = "hauling"
                        self.current_path = []  # Will recalculate path to destination
                        # Remove designation when item is picked up
                        remove_designation(job.x, job.y, job.z)
                    else:
                        # Item was already picked up by someone else
                        remove_job(job)
                        # Remove designation anyway
                        remove_designation(job.x, job.y, job.z)
                        self.current_job = None
                        self.state = "idle"
            elif job.type == "equip":
                # Equip job - pick up item from stockpile and equip it
                item = zones.remove_equipment_from_tile(job.x, job.y, job.z)
                if item is not None:
                    # Equip the item directly
                    slot = item.get("slot")
                    if slot and slot in self.equipment:
                        self.equipment[slot] = item
                        print(f"[Equip] {self.name} equipped {item.get('name')} in {slot} slot")
                    else:
                        print(f"[Equip] {self.name} couldn't equip {item.get('name')} - invalid slot")
                    
                    remove_job(job)
                    self.current_job = None
                    self.state = "idle"
                else:
                    # Item was already taken
                    remove_job(job)
                    self.current_job = None
                    self.state = "idle"
            elif job.type == "supply":
                # Supply job - pickup from stockpile for construction
                # Use pickup_amount for batch jobs, modified by colonist's haul capacity
                base_pickup = getattr(job, 'pickup_amount', 1) or 1
                haul_capacity = self.get_equipment_haul_capacity()
                # Apply haul capacity multiplier (e.g., 1.5x capacity = can carry 50% more)
                pickup_amount = int(base_pickup * haul_capacity)
                pickup_amount = max(1, pickup_amount)  # Always pick up at least 1
                item = zones.remove_from_tile_storage(job.x, job.y, job.z, pickup_amount)
                if item is None and job.resource_type:
                    # Original tile empty - try to find another tile with this resource
                    alt_source = zones.find_stockpile_with_resource(job.resource_type, z=job.z)
                    if alt_source is not None:
                        # Redirect to new source
                        job.x, job.y, job.z = alt_source
                        self.current_path = []  # Recalculate path
                        self.state = "moving_to_job"
                        return
                
                if item is not None:
                    # Also remove from global stockpile count
                    spend_from_stockpile(item["type"], item.get("amount", 1))
                    self.carrying = item
                    self.pick_up_item(item)
                    self.state = "hauling"  # Reuse hauling state
                    self.current_path = []
                    if item.get("amount", 1) > 1:
                        print(f"[Supply] {self.name} picked up {item.get('amount')} {item.get('type')} for batch delivery")
                else:
                    # No resource available anywhere - cancel job and clear all pending flags
                    if job.delivery_queue:
                        for site_x, site_y, site_z, _ in job.delivery_queue:
                            mark_supply_job_completed(site_x, site_y, site_z, job.resource_type)
                    else:
                        mark_supply_job_completed(job.dest_x, job.dest_y, job.dest_z, job.resource_type)
                    remove_job(job)
                    self.current_job = None
                    self.state = "idle"
            elif job.type == "relocate":
                # Relocate job - move items from pending removal stockpile to another
                item = zones.remove_from_tile_storage(job.x, job.y, job.z, 1)
                if item is not None:
                    # Also remove from global stockpile count (will be re-added at destination)
                    spend_from_stockpile(item["type"], item.get("amount", 1))
                    self.carrying = item
                    self.pick_up_item(item)
                    self.state = "hauling"
                    self.current_path = []
                else:
                    # Tile is now empty - job complete
                    remove_job(job)
                    self.current_job = None
                    self.state = "idle"
            elif job.type == "install_furniture":
                # Install furniture: pick up furniture item from stockpile, then haul to destination
                from zones import remove_equipment_from_tile
                item = remove_equipment_from_tile(job.x, job.y, job.z)
                if item is not None:
                    # Carry as furniture item (consumed on install)
                    self.carrying = {"type": "furniture", "amount": 1, "item": item, "item_id": job.resource_type}
                    self.pick_up_item(self.carrying)
                    self.state = "hauling"
                    self.current_path = []
                else:
                    # Nothing to pick up here anymore - cancel job
                    remove_job(job)
                    self.current_job = None
                    self.state = "idle"
            elif job.type == "salvage":
                # Salvage job complete - drop scrap and remove object
                from resources import complete_salvage, create_resource_item
                scrap_amount = complete_salvage(job.x, job.y)
                if scrap_amount > 0:
                    # Drop scrap on the tile (object is removed)
                    grid.set_tile(job.x, job.y, "empty", z=0)
                    create_resource_item(job.x, job.y, 0, "scrap", scrap_amount)
                    print(f"[Salvage] Recovered {scrap_amount} scrap at ({job.x},{job.y})")
                remove_job(job)
                # Remove designation when salvage completes
                remove_designation(job.x, job.y, job.z)
                self.current_job = None
                self.state = "idle"
            else:
                # Generic job completion
                remove_job(job)
                self.current_job = None
                self.state = "idle"

    def _haul_to_destination(self, grid: Grid) -> None:
        """Move towards haul destination and deliver item."""
        if self.current_job is None or self.carrying is None:
            # Something went wrong - clean up
            if self.current_job and self.current_job.type == "supply":
                mark_supply_job_completed(
                    self.current_job.dest_x, 
                    self.current_job.dest_y,
                    self.current_job.dest_z,
                    self.current_job.resource_type
                )
                remove_job(self.current_job)
            self.current_job = None
            self.state = "idle"
            self.drop_item()  # Clear all carried items
            self.carrying = None
            return
        
        job = self.current_job
        dest_x, dest_y = job.dest_x, job.dest_y
        dest_z = job.dest_z if job.dest_z is not None else 0
        
        if dest_x is None or dest_y is None:
            # No destination - drop item and abort
            if job.type == "supply":
                mark_supply_job_completed(dest_x, dest_y, dest_z, job.resource_type)
            self.drop_item(self.carrying)
            self.carrying = None
            remove_job(job)
            self.current_job = None
            self.state = "idle"
            return
        
        # Check if we've arrived at destination
        if self.x == dest_x and self.y == dest_y and self.z == dest_z:
            resource_type = self.carrying.get("type", "")
            amount = self.carrying.get("amount", 1)
            
            if job.type == "supply":
                # Batch supply delivery - deliver to current site, then move to next
                if job.delivery_queue:
                    # Find current site in queue and deliver its amount
                    current_site = None
                    for i, (sx, sy, sz, site_amount) in enumerate(job.delivery_queue):
                        if sx == dest_x and sy == dest_y and sz == dest_z:
                            current_site = (i, sx, sy, sz, site_amount)
                            break
                    
                    if current_site:
                        idx, sx, sy, sz, site_amount = current_site
                        # Deliver only what this site needs
                        delivered = deliver_material(sx, sy, resource_type, site_amount, z=sz)
                        mark_supply_job_completed(sx, sy, sz, job.resource_type)
                        
                        # Reduce carried amount
                        remaining = amount - delivered
                        if remaining > 0:
                            self.carrying["amount"] = remaining
                        
                        # Remove this site from queue
                        job.delivery_queue.pop(idx)
                        
                        # If more sites to deliver to, update destination and continue
                        if job.delivery_queue and remaining > 0:
                            next_site = job.delivery_queue[0]
                            job.dest_x, job.dest_y, job.dest_z = next_site[0], next_site[1], next_site[2]
                            self.current_path = []  # Recalculate path to next site
                            print(f"[Supply] {self.name} delivered {delivered} {resource_type}, moving to next site ({remaining} remaining)")
                            return
                        else:
                            # All deliveries complete or out of resources
                            # Clear any remaining pending flags
                            for sx, sy, sz, _ in job.delivery_queue:
                                mark_supply_job_completed(sx, sy, sz, job.resource_type)
                    else:
                        # Current destination not in queue (legacy single-site job)
                        deliver_material(dest_x, dest_y, resource_type, amount, z=dest_z)
                        mark_supply_job_completed(dest_x, dest_y, dest_z, job.resource_type)
                else:
                    # Legacy single-site supply job
                    deliver_material(dest_x, dest_y, resource_type, amount, z=dest_z)
                    mark_supply_job_completed(dest_x, dest_y, dest_z, job.resource_type)
            elif job.type == "haul":
                # Deliver to stockpile
                if resource_type == "equipment":
                    # Equipment delivery - store the item data
                    item_data = self.carrying.get("item", {})
                    item_name = item_data.get("name", "equipment")
                    if zones.is_stockpile_zone(dest_x, dest_y, dest_z):
                        zones.store_equipment_at_tile(dest_x, dest_y, dest_z, item_data)
                        print(f"[Haul] Stored {item_name} in stockpile at ({dest_x},{dest_y})")
                    else:
                        print(f"[Haul] Dropped {item_name} (stockpile zone removed)")
                elif zones.is_stockpile_zone(dest_x, dest_y, dest_z):
                    add_to_stockpile(resource_type, amount)
                    zones.add_to_zone_storage(dest_x, dest_y, dest_z, resource_type, amount)
                    print(f"[Haul] Delivered {amount} {resource_type} to stockpile at ({dest_x},{dest_y})")
                else:
                    # Destination is no longer a stockpile - just add to global stockpile
                    add_to_stockpile(resource_type, amount)
                    print(f"[Haul] Delivered {amount} {resource_type} (stockpile zone removed)")
            elif job.type == "install_furniture":
                # Install furniture at destination: convert tile and consume item
                furniture_item_id = job.resource_type or self.carrying.get("item_id")
                tile_type = furniture_item_id or "gutter_slab"
                grid.set_tile(dest_x, dest_y, tile_type, z=dest_z)
                item_data = self.carrying.get("item", {})
                item_name = item_data.get("name", furniture_item_id or "furniture")
                print(f"[Furniture] Installed {item_name} at ({dest_x},{dest_y},z={dest_z})")
                # Register bed if this is a bed (crash_bed is the craftable bed item)
                if furniture_item_id == "crash_bed":
                    from beds import register_bed
                    register_bed(dest_x, dest_y, dest_z)
                # Furniture can change room classification (e.g., Kitchen)
                from rooms import mark_tile_dirty
                mark_tile_dirty(dest_x, dest_y, dest_z)
            
            # Job complete
            self.drop_item(self.carrying)
            self.carrying = None
            remove_job(job)
            self.current_job = None
            self.state = "idle"
            return
        
        # Move towards destination
        if self.move_cooldown > 0:
            self.move_cooldown -= 1
            return
        
        # Calculate path if needed
        if not self.current_path:
            self.current_path = self._calculate_path(grid, dest_x, dest_y, dest_z)
            self.stuck_timer = 0
            if not self.current_path:
                self.stuck_timer += 1
                if self.stuck_timer > self.max_stuck_time:
                    # Can't reach destination - drop item and abort
                    self.drop_item(self.carrying)
                    self.carrying = None
                    remove_job(job)
                    self.current_job = None
                    self.state = "idle"
                return
        
        # Follow path (now includes z)
        next_pos = self.current_path[0]
        next_x, next_y, next_z = next_pos
        
        is_target = (next_x == dest_x and next_y == dest_y and next_z == dest_z)
        is_walkable = grid.is_walkable(next_x, next_y, next_z)
        
        if is_target or is_walkable:
            self.x = next_x
            self.y = next_y
            self.z = next_z
            self.current_path.pop(0)
            # Apply mood speed modifier
            self.move_cooldown = int(self.move_speed * self.get_mood_speed_modifier())
            
            # Check for stumble in hazardous tiles
            stumble_delay = self.check_stumble(grid)
            if stumble_delay > 0:
                self.move_cooldown += stumble_delay
            
            self.stuck_timer = 0
        else:
            # Path blocked - recalculate
            self.current_path = []
            self.stuck_timer += 1
            self.move_cooldown = self.move_speed * 2  # No mood modifier for stuck delay
            
            if self.stuck_timer > self.max_stuck_time:
                # Can't reach destination - drop item and abort
                print(f"[Stuck] Colonist hauling path blocked, dropping item")
                self.drop_item(self.carrying)
                self.carrying = None
                remove_job(job)
                self.current_job = None
                self.state = "idle"
                self.stuck_timer = 0

    def _unstick_if_needed(self, grid: Grid) -> bool:
        """Check if colonist is stuck in a non-walkable tile and teleport to nearest walkable.
        
        Returns True if colonist was stuck and teleported (triggers recovery).
        """
        if grid.is_walkable(self.x, self.y, self.z):
            return False  # Not stuck
        
        # Colonist is on a non-walkable tile - find nearest walkable
        # Search in expanding rings around current position
        for radius in range(1, max(GRID_W, GRID_H)):
            candidates = []
            for dx in range(-radius, radius + 1):
                for dy in range(-radius, radius + 1):
                    # Only check tiles at this radius (ring, not filled circle)
                    if abs(dx) != radius and abs(dy) != radius:
                        continue
                    nx, ny = self.x + dx, self.y + dy
                    if grid.in_bounds(nx, ny, self.z) and grid.is_walkable(nx, ny, self.z):
                        candidates.append((nx, ny))
            
            if candidates:
                # Pick random from candidates at this radius
                new_x, new_y = random.choice(candidates)
                print(f"[Unstick] Colonist teleported from ({self.x},{self.y}) to ({new_x},{new_y}) on Z={self.z}")
                self.x, self.y = new_x, new_y
                self._enter_recovery("teleported out of wall")
                return True
        
        # No walkable tile found on this Z-level - try Z=0 as fallback
        if self.z != 0:
            for radius in range(0, max(GRID_W, GRID_H)):
                for dx in range(-radius, radius + 1):
                    for dy in range(-radius, radius + 1):
                        nx, ny = self.x + dx, self.y + dy
                        if grid.in_bounds(nx, ny, 0) and grid.is_walkable(nx, ny, 0):
                            print(f"[Unstick] Colonist teleported to ground level ({nx},{ny}) from Z={self.z}")
                            self.x, self.y, self.z = nx, ny, 0
                            self._enter_recovery("teleported to ground level")
                            return True
        
        return False

    # --- Interruption and Recovery -------------------------------------------

    def _interrupt_current_job(self, reason: str = "") -> None:
        """Cancel current job and enter recovery state.
        
        Called when:
        - Path becomes blocked and can't be recalculated
        - Job target becomes unreachable
        - Colonist gets stuck and teleported
        """
        job = self.current_job
        if job is not None:
            # Release any reserved resources
            if job.type == "gathering":
                set_node_state(job.x, job.y, NodeState.IDLE)
            elif job.type == "crafting":
                buildings.release_workstation(job.x, job.y, job.z)
            
            # Unassign job so others can take it
            job.assigned = False
            self.current_job = None
            
            reason_str = f" ({reason})" if reason else ""
            print(f"[Interrupt] Job {job.type} at ({job.x},{job.y}) interrupted{reason_str}")
        
        # Drop carried items
        if self.carrying is not None:
            print(f"[Interrupt] Dropped {self.carrying.get('type', 'item')}")
            self.drop_item()  # Clear all carried items
            self.carrying = None
        
        # Clear path and enter recovery
        self.current_path = []
        self._enter_recovery(reason)

    def _enter_recovery(self, reason: str = "") -> None:
        """Enter recovery state - brief pause before returning to idle."""
        if self.state != "recovery":
            reason_str = f" ({reason})" if reason else ""
            print(f"[Recovery] Colonist entering recovery{reason_str}")
        self.state = "recovery"
        self.recovery_timer = self.recovery_duration
        self.current_path = []
        self.stuck_timer = 0

    def _update_recovery(self) -> None:
        """Update recovery state - count down and return to idle."""
        if self.recovery_timer > 0:
            self.recovery_timer -= 1
        else:
            self.state = "idle"

    def _check_job_still_valid(self, grid: Grid) -> bool:
        """Check if current job is still reachable and valid.
        
        Returns False if job should be interrupted.
        Only checks job target validity, NOT path validity (that's separate).
        """
        job = self.current_job
        if job is None:
            return True  # No job to validate
        
        # For construction jobs, check if the construction site still exists
        if job.type == "construction":
            site = buildings.get_construction_site(job.x, job.y, job.z)
            if site is None:
                # Construction was completed or cancelled
                return False
        
        # For gathering jobs, check if node still exists
        if job.type == "gathering":
            from resources import get_node_at
            node = get_node_at(job.x, job.y)
            if node is None or node.get("amount", 0) <= 0:
                return False
        
        return True

    def _check_path_still_valid(self, grid: Grid) -> bool:
        """Check if current path is still walkable.
        
        Returns False if any tile in the path is now blocked.
        """
        if not self.current_path:
            return True  # No path to check
        
        for px, py, pz in self.current_path:
            # Skip the final destination (might be a workstation or resource node)
            if self.current_path.index((px, py, pz)) == len(self.current_path) - 1:
                continue
            
            if not grid.is_walkable(px, py, pz):
                # Check if it's a door/window we can open
                if is_door(px, py, pz) or is_window(px, py, pz):
                    continue
                return False
        
        return True

    # --- Crafting behavior ---------------------------------------------------

    def _crafting_fetch_materials(self, grid: Grid) -> None:
        """Fetch materials from stockpile for crafting job."""
        if self.current_job is None:
            self.state = "idle"
            return
        
        job = self.current_job
        
        # Get recipe for workstation
        recipe = buildings.get_workstation_recipe(job.x, job.y, job.z)
        if recipe is None:
            # Invalid workstation - cancel job
            buildings.release_workstation(job.x, job.y, job.z)
            buildings.mark_crafting_job_completed(job.x, job.y, job.z)
            remove_job(job)
            self.current_job = None
            self.state = "idle"
            return
        
        # If already carrying something, deliver it to workstation
        if self.carrying is not None:
            # Move towards workstation
            if self.move_cooldown > 0:
                self.move_cooldown -= 1
                return
            
            # Check if at workstation (adjacent is fine)
            at_bench = (abs(self.x - job.x) <= 1 and abs(self.y - job.y) <= 1 and self.z == job.z)
            if at_bench:
                # Deliver to workstation
                res_type = self.carrying.get("type", "")
                amount = self.carrying.get("amount", 1)
                buildings.add_input_to_workstation(job.x, job.y, job.z, res_type, amount)
                self.drop_item(self.carrying)
                self.carrying = None
                
                # Check if workstation has all inputs
                if buildings.workstation_has_inputs(job.x, job.y, job.z):
                    # Start working
                    ws = buildings.get_workstation(job.x, job.y, job.z)
                    if ws:
                        ws["working"] = True
                        ws["progress"] = 0
                    self.state = "crafting_work"
                    self.current_path = []
                return
            
            # Move towards workstation
            if not self.current_path:
                self.current_path = self._calculate_path(grid, job.x, job.y, job.z)
                if not self.current_path:
                    # Can't reach - try adjacent tile
                    for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
                        adj_x, adj_y = job.x + dx, job.y + dy
                        if grid.is_walkable(adj_x, adj_y, job.z):
                            self.current_path = self._calculate_path(grid, adj_x, adj_y, job.z)
                            if self.current_path:
                                break
            
            if self.current_path:
                next_pos = self.current_path[0]
                if grid.is_walkable(next_pos[0], next_pos[1], next_pos[2]):
                    self.x, self.y, self.z = next_pos
                    self.current_path.pop(0)
                    self.move_cooldown = 3
            return
        
        # Need to fetch materials
        inputs_needed = recipe.get("input", {})
        ws = buildings.get_workstation(job.x, job.y, job.z)
        inputs_have = ws.get("input_items", {}) if ws else {}
        
        # Find what we still need
        for res_type, amount_needed in inputs_needed.items():
            have = inputs_have.get(res_type, 0)
            if have < amount_needed:
                # Find stockpile with this resource
                source = zones.find_stockpile_with_resource(res_type, z=job.z)
                if source is None:
                    # No resource available - wait
                    return
                
                source_x, source_y, source_z = source
                
                # Move to stockpile
                if self.move_cooldown > 0:
                    self.move_cooldown -= 1
                    return
                
                # Check if at stockpile
                if self.x == source_x and self.y == source_y and self.z == source_z:
                    # Pick up resource
                    item = zones.remove_from_tile_storage(source_x, source_y, source_z, 1)
                    if item:
                        self.carrying = {"type": item["type"], "amount": item["amount"]}
                        self.pick_up_item(self.carrying)
                        spend_from_stockpile(item["type"], item["amount"])
                        self.current_path = []
                    return
                
                # Move towards stockpile
                if not self.current_path or self.current_path[-1] != (source_x, source_y, source_z):
                    self.current_path = self._calculate_path(grid, source_x, source_y, source_z)
                
                if self.current_path:
                    next_pos = self.current_path[0]
                    if grid.is_walkable(next_pos[0], next_pos[1], next_pos[2]):
                        self.x, self.y, self.z = next_pos
                        self.current_path.pop(0)
                        self.move_cooldown = 3
                return
        
        # All inputs delivered - start working
        if ws:
            ws["working"] = True
            ws["progress"] = 0
        self.state = "crafting_work"

    def _crafting_work_at_bench(self, grid: Grid) -> None:
        """Work at workstation to produce output."""
        if self.current_job is None:
            self.state = "idle"
            return
        
        job = self.current_job
        ws = buildings.get_workstation(job.x, job.y, job.z)
        
        if ws is None:
            # Workstation gone - cancel
            buildings.mark_crafting_job_completed(job.x, job.y, job.z)
            remove_job(job)
            self.current_job = None
            self.state = "idle"
            return
        
        # Move adjacent to workstation if not already
        at_bench = (abs(self.x - job.x) <= 1 and abs(self.y - job.y) <= 1 and self.z == job.z)
        if not at_bench:
            if self.move_cooldown > 0:
                self.move_cooldown -= 1
                return
            
            if not self.current_path:
                # Find adjacent walkable tile
                for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
                    adj_x, adj_y = job.x + dx, job.y + dy
                    if grid.is_walkable(adj_x, adj_y, job.z):
                        self.current_path = self._calculate_path(grid, adj_x, adj_y, job.z)
                        if self.current_path:
                            break
            
            if self.current_path:
                next_pos = self.current_path[0]
                if grid.is_walkable(next_pos[0], next_pos[1], next_pos[2]):
                    self.x, self.y, self.z = next_pos
                    self.current_path.pop(0)
                    self.move_cooldown = 3
            return
        
        # Work on crafting
        ws["progress"] = ws.get("progress", 0) + 1
        
        recipe = buildings.get_workstation_recipe(job.x, job.y, job.z)
        if recipe is None:
            return
        
        work_time = recipe.get("work_time", 60)
        
        if ws["progress"] >= work_time:
            # Check if this produces an item or a resource
            output_item_id = recipe.get("output_item")
            
            if output_item_id:
                # Determine if this output is equippable gear or non-equippable (e.g. furniture)
                from items import spawn_world_item, get_item_def
                item_def = get_item_def(output_item_id)
                is_equippable = item_def is not None and getattr(item_def, "slot", None) is not None

                if is_equippable:
                    # For equippable gear, ensure there is stockpile space for equipment
                    dest = zones.find_stockpile_tile_for_resource("equipment", z=job.z, from_x=job.x, from_y=job.y)
                    if dest is None:
                        # No stockpile space - pause crafting until space available
                        if not ws.get("waiting_for_storage"):
                            print(f"[Crafting] Waiting for stockpile space for equipment...")
                            ws["waiting_for_storage"] = True
                        return  # Don't complete - wait for space

                # Either non-equippable item (furniture) or we have confirmed storage for gear
                ws["waiting_for_storage"] = False
                
                # Crafting complete - consume inputs and produce output
                buildings.consume_workstation_inputs(job.x, job.y, job.z)
                
                # Produce an item from the item system
                item_name = item_def.name if item_def else output_item_id
                
                # Drop item adjacent to workstation
                for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
                    drop_x, drop_y = job.x + dx, job.y + dy
                    if grid.is_walkable(drop_x, drop_y, job.z):
                        spawn_world_item(drop_x, drop_y, job.z, output_item_id)
                        print(f"[Crafting] Produced {item_name} at ({drop_x},{drop_y})")
                        break
            else:
                # Produce resource output (legacy behavior)
                outputs = recipe.get("output", {})
                from resources import create_resource_item
                for res_type, amount in outputs.items():
                    # Drop output adjacent to workstation
                    for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
                        drop_x, drop_y = job.x + dx, job.y + dy
                        if grid.is_walkable(drop_x, drop_y, job.z):
                            create_resource_item(drop_x, drop_y, job.z, res_type, amount)
                            print(f"[Crafting] Produced {amount} {res_type} at ({drop_x},{drop_y})")
                            break
            
            # Decrement any finite craft queue for this workstation
            ws_final = buildings.get_workstation(job.x, job.y, job.z)
            if ws_final is not None and ws_final.get("craft_queue", 0) > 0:
                ws_final["craft_queue"] -= 1

            # Complete job
            buildings.release_workstation(job.x, job.y, job.z)
            buildings.mark_crafting_job_completed(job.x, job.y, job.z)
            remove_job(job)
            self.current_job = None
            self.state = "idle"
            # Generate work thought
            self._generate_work_thought("crafting_complete", self._game_tick)

    def _update_hunger(self, grid: Grid) -> None:
        """Update hunger and handle eating/starvation."""
        if self.is_dead:
            return
        
        # Increase hunger over time
        self.hunger = min(100.0, self.hunger + self.hunger_rate)
        
        # Track hunger threshold changes for thoughts
        new_threshold = "none"
        if self.hunger >= 100.0:
            new_threshold = "starving"
        elif self.hunger >= 85:
            new_threshold = "very_hungry"
        elif self.hunger >= 70:
            new_threshold = "hungry"
        
        # Generate thought when crossing threshold
        if new_threshold != self.last_hunger_threshold and new_threshold != "none":
            self._generate_need_thought(new_threshold, self._game_tick)
        self.last_hunger_threshold = new_threshold
        
        # Starving - take damage
        if self.hunger >= 100.0:
            self.health -= self.starving_damage
            if self.health <= 0:
                self.health = 0
                self.is_dead = True
                print(f"[Death] Colonist at ({self.x},{self.y}) died of starvation!")
                return
        
        # Hungry (>70) and idle - try to find food
        if self.hunger > 70 and self.state == "idle" and self.current_job is None:
            self._try_eat_food(grid)
    
    def _try_eat_food(self, grid: Grid) -> None:
        """Try to find and eat a cooked meal."""
        import zones
        
        # Look for cooked_meal in stockpiles (check all Z levels)
        meal_tile = zones.find_stockpile_with_resource("cooked_meal", z=None)
        if meal_tile is None:
            # No food available anywhere
            return
        
        mx, my, mz = meal_tile
        
        # Check if we're adjacent or on the food tile
        dist = abs(self.x - mx) + abs(self.y - my)
        if dist <= 1 and self.z == mz:
            # Eat the food!
            removed = zones.remove_from_tile_storage(mx, my, mz, 1)
            if removed and removed.get("type") == "cooked_meal":
                self.hunger = max(0, self.hunger - 70)
                print(f"[Eat] Colonist ate a meal at ({mx},{my}), hunger now {self.hunger:.0f}")
        else:
            # Need to walk to food - enter eating state
            self.current_path = self._calculate_path(grid, mx, my, mz)
            if self.current_path:
                self.state = "eating"
                self._eating_target = (mx, my, mz)
                print(f"[Hunger] Colonist going to eat at ({mx},{my},{mz})")
    
    def _move_to_eat(self, grid: Grid) -> None:
        """Move towards food and eat when arrived."""
        import zones
        from buildings import is_door, is_door_open, open_door, is_window, is_window_open, open_window
        
        if not hasattr(self, '_eating_target') or self._eating_target is None:
            self.state = "idle"
            return
        
        mx, my, mz = self._eating_target
        
        # Check if we've arrived (adjacent or on tile)
        dist = abs(self.x - mx) + abs(self.y - my)
        if dist <= 1 and self.z == mz:
            # Try to eat
            removed = zones.remove_from_tile_storage(mx, my, mz, 1)
            if removed and removed.get("type") == "cooked_meal":
                self.hunger = max(0, self.hunger - 70)
                print(f"[Eat] Colonist ate a meal at ({mx},{my}), hunger now {self.hunger:.0f}")
            else:
                print(f"[Eat] Food was taken before colonist arrived")
            self._eating_target = None
            self.state = "idle"
            return
        
        # Movement cooldown
        if self.move_cooldown > 0:
            self.move_cooldown -= 1
            return
        
        # Need path?
        if not self.current_path:
            self.current_path = self._calculate_path(grid, mx, my, mz)
            if not self.current_path:
                # Can't reach food
                print(f"[Eat] Can't reach food at ({mx},{my},{mz})")
                self._eating_target = None
                self.state = "idle"
                return
        
        # Follow path
        next_x, next_y, next_z = self.current_path[0]
        is_walkable = grid.is_walkable(next_x, next_y, next_z)
        
        # Handle doors/windows
        if is_door(next_x, next_y, next_z) and not is_door_open(next_x, next_y, next_z):
            open_door(next_x, next_y, next_z)
            is_walkable = True
        if is_window(next_x, next_y, next_z) and not is_window_open(next_x, next_y, next_z):
            open_window(next_x, next_y, next_z)
            is_walkable = True
        
        if is_walkable or (next_x == mx and next_y == my and next_z == mz):
            self.x = next_x
            self.y = next_y
            self.z = next_z
            self.current_path.pop(0)
            # Apply mood speed modifier
            self.move_cooldown = int(self.move_speed * self.get_mood_speed_modifier())
            
            # Check for stumble in hazardous tiles
            stumble_delay = self.check_stumble(grid)
            if stumble_delay > 0:
                self.move_cooldown += stumble_delay
        else:
            # Path blocked - recalculate
            self.current_path = []

    def _update_tiredness(self, grid: Grid, all_colonists: list, game_tick: int) -> None:
        """Update tiredness and handle sleeping."""
        from beds import get_colonist_bed, get_sleep_thoughts, calculate_sleep_quality
        
        if self.is_dead:
            return
        
        # Increase tiredness over time (slower than hunger)
        if not self.is_sleeping:
            self.tiredness = min(100.0, self.tiredness + 0.003)  # ~5 hours to get tired
        
        # Generate tiredness thoughts
        if self.tiredness >= 90 and game_tick - self.last_sleep_tick > 600:
            self.add_thought("need", "I can barely keep my eyes open...", -0.2, game_tick=game_tick)
        elif self.tiredness >= 70 and game_tick - self.last_sleep_tick > 600:
            self.add_thought("need", "Getting tired...", -0.1, game_tick=game_tick)
        
        # If sleeping, process sleep
        if self.is_sleeping:
            # Calculate sleep quality
            quality = calculate_sleep_quality(self, all_colonists)
            
            # Reduce tiredness based on quality
            self.tiredness = max(0, self.tiredness - (0.05 * quality))
            
            # Slowly restore health while sleeping
            if self.health < 100:
                self.health = min(100, self.health + 0.01 * quality)
            
            # Wake up when rested
            if self.tiredness <= 10:
                self.is_sleeping = False
                self.sleep_target = None
                self.state = "idle"
                self.last_sleep_tick = game_tick
                
                # Sleep thoughts
                for thought_text, mood_effect in get_sleep_thoughts(self, all_colonists):
                    self.add_thought("need", thought_text, mood_effect, game_tick=game_tick)
                
                print(f"[Sleep] {self.name} woke up feeling {'rested' if quality > 1 else 'okay' if quality > 0.5 else 'tired'}")
            return
        
        # Very tired and idle - try to sleep
        # Lower threshold at night (colonists want to sleep when it's dark)
        from time_system import is_sleep_time
        sleep_threshold = 50 if is_sleep_time() else 80
        
        if self.tiredness > sleep_threshold and self.state == "idle" and not self.in_combat:
            self._try_go_to_sleep(grid, all_colonists, game_tick)
    
    def _try_go_to_sleep(self, grid: Grid, all_colonists: list, game_tick: int) -> None:
        """Try to find a bed and go to sleep."""
        from beds import get_colonist_bed
        
        # Check if we have an assigned bed
        bed_pos = get_colonist_bed(id(self))
        
        if bed_pos:
            bx, by, bz = bed_pos
            # Check if we're at the bed
            dist = abs(self.x - bx) + abs(self.y - by)
            if dist <= 1 and self.z == bz:
                # Sleep!
                self.is_sleeping = True
                self.state = "sleeping"
                self.add_thought("need", "Time to rest.", 0.05, game_tick=game_tick)
                print(f"[Sleep] {self.name} went to sleep in their bed")
                return
            else:
                # Walk to bed
                self.current_path = self._calculate_path(grid, bx, by, bz)
                if self.current_path:
                    self.sleep_target = bed_pos
                    self.state = "moving_to_sleep"
                    return
        
        # No bed - sleep on ground (with penalty)
        if self.tiredness > 95:
            self.is_sleeping = True
            self.state = "sleeping"
            self.add_thought("need", "Sleeping on the ground...", -0.15, game_tick=game_tick)
            print(f"[Sleep] {self.name} collapsed to sleep on the ground (no bed)")

    def _update_combat(self, all_colonists: list, game_tick: int) -> None:
        """Process combat behavior for this colonist."""
        from combat import (is_hostile_to_anyone, find_hostile_target, perform_attack,
                           get_potential_defenders, log_combat_event, is_hostile_to,
                           try_start_social_conflict)
        
        # Check for social conflicts (jealousy, rivalry, trait clashes)
        if not self.in_combat and self.state == "idle":
            conflict_target = try_start_social_conflict(self, all_colonists, game_tick)
            if conflict_target:
                self.in_combat = True
                self.combat_target = conflict_target
                # The target fights back
                if not conflict_target.in_combat:
                    conflict_target.in_combat = True
                    conflict_target.combat_target = self
                print(f"[Combat] {self.name} started a fight with {conflict_target.name}!")
                
                # Notification with reason
                from notifications import notify_fight_start
                reason = getattr(self, '_conflict_reason', "")
                notify_fight_start(self.name.split()[0], conflict_target.name.split()[0], reason)
        
        # Attack cooldown (can only attack every ~1 second)
        if game_tick - self.last_combat_tick < 60:
            return
        
        # If hostile, look for targets
        if is_hostile_to_anyone(self):
            target = find_hostile_target(self, all_colonists)
            if target:
                # Check if in melee range
                dx = abs(self.x - target.x)
                dy = abs(self.y - target.y)
                if self.z == target.z and max(dx, dy) <= 1:
                    # Attack!
                    result = perform_attack(self, target, game_tick)
                    self.last_combat_tick = game_tick
                    self.in_combat = True
                    self.combat_target = target
                    
                    # Log the event
                    log_combat_event({
                        "tick": game_tick,
                        "attacker": self.name,
                        "defender": target.name,
                        "hit": result["hit"],
                        "damage": result["damage"],
                        "killed": result["killed"],
                        "message": result["message"],
                    })
                    
                    # If we killed them, check for defenders joining
                    if result["killed"]:
                        self.in_combat = False
                        self.combat_target = None
                        from notifications import notify_death
                        notify_death(target.name, f"Killed by {self.name.split()[0]}")
                    elif result.get("retreated"):
                        from notifications import notify_fight_end
                        notify_fight_end(target.name.split()[0], "retreated")
                    else:
                        # Defenders may join
                        defenders = get_potential_defenders(target, self, all_colonists)
                        for defender in defenders:
                            if not defender.in_combat:
                                defender.in_combat = True
                                defender.combat_target = self
                                defender.add_thought("combat", 
                                    f"Rushing to help {target.name.split()[0]}!", 
                                    -0.1, game_tick=game_tick)
                else:
                    # Not in range - move toward target (handled by normal pathfinding)
                    self.in_combat = True
                    self.combat_target = target
        
        # If we're defending someone (in_combat but not hostile)
        elif self.in_combat and self.combat_target:
            target = self.combat_target
            if target.is_dead:
                # Target died, stop fighting
                self.in_combat = False
                self.combat_target = None
                self.add_thought("combat", "The fight is over.", 0.0, game_tick=game_tick)
                return
            
            # Check if in melee range
            dx = abs(self.x - target.x)
            dy = abs(self.y - target.y)
            if self.z == target.z and max(dx, dy) <= 1:
                # Counter-attack!
                result = perform_attack(self, target, game_tick)
                self.last_combat_tick = game_tick
                
                log_combat_event({
                    "tick": game_tick,
                    "attacker": self.name,
                    "defender": target.name,
                    "hit": result["hit"],
                    "damage": result["damage"],
                    "killed": result["killed"],
                    "message": result["message"],
                })
                
                if result["killed"]:
                    self.in_combat = False
                    self.combat_target = None
                    self.add_thought("combat", 
                        f"I... I killed {target.name.split()[0]}.", 
                        -0.5, game_tick=game_tick)
                    # Death notification
                    from notifications import notify_death
                    notify_death(target.name, f"Killed by {self.name.split()[0]}")
                
                if result.get("retreated"):
                    from notifications import notify_fight_end
                    notify_fight_end(target.name.split()[0], "retreated")

    def update(self, grid: Grid, all_colonists: list = None, game_tick: int = 0) -> None:
        """Advance colonist behavior for one simulation tick."""
        
        # Skip dead colonists
        if self.is_dead:
            return
        
        # Store for environment sampling
        self._all_colonists = all_colonists or []
        self._game_tick = game_tick
        
        # Tick thought cooldown
        self._tick_thought_cooldown()
        
        # Update facing direction based on movement
        if self.x != self.last_x or self.y != self.last_y:
            if self.x > self.last_x:
                self.facing_direction = "east"
            elif self.x < self.last_x:
                self.facing_direction = "west"
            elif self.y > self.last_y:
                self.facing_direction = "south"
            elif self.y < self.last_y:
                self.facing_direction = "north"
            self.last_x = self.x
            self.last_y = self.y
        
        # Update idle fidget animation
        if self.state == "idle":
            self.idle_fidget_timer += 1
            if self.idle_fidget_timer > 120:  # Every ~2 seconds at 60 FPS
                self.idle_fidget_timer = 0
            # Small sine wave bobbing
            import math
            self.fidget_offset = int(math.sin(self.idle_fidget_timer / 20.0) * 2)
            
            # Maybe generate idle thought
            self._maybe_generate_idle_thought(game_tick)
            
            # Process social interactions when idle
            self.process_social_interactions(all_colonists or [], game_tick)
            
            # Try to start conversations with nearby colonists
            if random.random() < 0.002:  # ~0.2% chance per tick when idle
                from conversations import try_start_conversation
                for other in (all_colonists or []):
                    if other is not self and not other.is_dead:
                        if try_start_conversation(self, other, game_tick):
                            break  # Only one conversation per tick
        else:
            self.fidget_offset = 0
        
        # Process combat
        self._update_combat(all_colonists or [], game_tick)
        
        # Update hunger system
        self._update_hunger(grid)
        
        # Update tiredness/sleep system
        self._update_tiredness(grid, all_colonists or [], game_tick)
        
        # If sleeping, skip other updates
        if self.is_sleeping:
            return
        
        # Failsafe: unstick colonist if they're in a wall
        # If teleported, we're now in recovery state
        if self._unstick_if_needed(grid):
            self._interrupt_current_job("stuck in wall")
            return
        
        # Recovery state - wait before returning to idle
        if self.state == "recovery":
            self._update_recovery()
            return
        
        # Check if current job is still valid (target gone, etc.)
        if self.state not in ("idle", "eating", "recovery"):
            if not self._check_job_still_valid(grid):
                self._interrupt_current_job("job no longer valid")
                return
            
            # Check if path is still walkable (only if we have a path)
            if self.current_path and not self._check_path_still_valid(grid):
                # Path blocked - try to recalculate
                if self.current_job:
                    new_path = self._calculate_path(grid, self.current_job.x, self.current_job.y, self.current_job.z)
                    if new_path:
                        self.current_path = new_path
                    else:
                        # Can't find new path - interrupt
                        self._interrupt_current_job("path blocked")
                        return

        if self.state == "idle":
            self._try_take_job(grid)
            if self.state == "idle":
                self._maybe_wander_when_idle(grid)
        elif self.state == "moving_to_job":
            self._move_towards_job(grid)
        elif self.state == "working":
            self._work_on_job(grid)
        elif self.state == "hauling":
            self._haul_to_destination(grid)
        elif self.state == "crafting_fetch":
            self._crafting_fetch_materials(grid)
        elif self.state == "crafting_work":
            self._crafting_work_at_bench(grid)
        elif self.state == "eating":
            self._move_to_eat(grid)
        else:
            print(f"ERROR: Colonist in unknown state: {self.state}")

    def draw(self, surface: pygame.Surface, ether_mode: bool = False, camera_x: int = 0, camera_y: int = 0) -> None:
        """Render the colonist as a sprite-person with job state indicator.
        
        Args:
            surface: Pygame surface to draw on
            ether_mode: If True, use ether color
            camera_x, camera_y: Camera offset for viewport rendering
        """
        # World position in pixels
        world_cx = self.x * TILE_SIZE + TILE_SIZE // 2
        world_cy = self.y * TILE_SIZE + TILE_SIZE // 2 + self.fidget_offset
        
        # Screen position (apply camera offset)
        screen_cx = world_cx - camera_x
        screen_cy = world_cy - camera_y
        
        # Use ether mode colors if enabled
        if ether_mode:
            clothing = COLOR_COLONIST_ETHER
            skin = COLOR_COLONIST_ETHER
        else:
            clothing = self.clothing_color
            skin = self.skin_tone
        
        # Draw sprite-person (simple geometric shapes)
        # Legs (2 small rectangles)
        leg_width = 3
        leg_height = 5
        leg_spacing = 2
        legs_y = screen_cy + 3
        
        # Left leg
        pygame.draw.rect(surface, clothing, 
                        (screen_cx - leg_spacing - leg_width, legs_y, leg_width, leg_height))
        # Right leg
        pygame.draw.rect(surface, clothing,
                        (screen_cx + leg_spacing, legs_y, leg_width, leg_height))
        
        # Torso (rectangle)
        torso_width = 10
        torso_height = 8
        torso_rect = pygame.Rect(screen_cx - torso_width // 2, screen_cy - 2, torso_width, torso_height)
        pygame.draw.rect(surface, clothing, torso_rect)
        
        # Head (circle)
        head_radius = 4
        head_y = screen_cy - 6
        pygame.draw.circle(surface, skin, (screen_cx, head_y), head_radius)
        
        # Simple facing indicator (small dot for eyes/face direction)
        face_offset_x = 0
        face_offset_y = 0
        if self.facing_direction == "north":
            face_offset_y = -2
        elif self.facing_direction == "south":
            face_offset_y = 1
        elif self.facing_direction == "east":
            face_offset_x = 2
        elif self.facing_direction == "west":
            face_offset_x = -2
        
        # Draw tiny face dot
        pygame.draw.circle(surface, (50, 50, 50), 
                          (screen_cx + face_offset_x, head_y + face_offset_y), 1)
        
        # Job state ring around colonist
        ring_color = None
        if self.state == "idle":
            ring_color = (100, 150, 255)  # Blue
        elif self.state in ("hauling", "moving_to_haul"):
            ring_color = (255, 220, 100)  # Yellow
        elif self.state in ("building", "moving_to_build", "salvaging", "moving_to_salvage", "harvesting", "moving_to_harvest"):
            ring_color = (100, 255, 150)  # Green
        elif self.stuck_timer > 15:
            ring_color = (255, 100, 100)  # Red (stuck)
        
        if ring_color:
            # Draw thin ring around colonist
            pygame.draw.circle(surface, ring_color, (screen_cx, screen_cy), 12, 1)
        
        # Draw carrying indicator if hauling
        if self.carrying is not None:
            # Small colored square above colonist
            carry_type = self.carrying.get("type", "")
            if carry_type == "wood":
                carry_color = (139, 90, 43)
            elif carry_type == "scrap":
                carry_color = (120, 120, 120)
            elif carry_type == "metal":
                carry_color = (180, 180, 200)
            elif carry_type == "mineral":
                carry_color = (80, 200, 200)
            elif carry_type == "raw_food":
                carry_color = (180, 220, 100)
            else:
                carry_color = (200, 200, 200)
            
            carry_rect = pygame.Rect(screen_cx - 4, screen_cy - 14, 8, 6)
            pygame.draw.rect(surface, carry_color, carry_rect)
            pygame.draw.rect(surface, (255, 255, 255), carry_rect, 1)


# --- Module-level helpers -----------------------------------------------------


def create_colonists(count: int, spawn_x: int = None, spawn_y: int = None) -> list[Colonist]:
    """Construct an initial list of colonists clustered at spawn location.
    
    Args:
        count: Number of colonists to create
        spawn_x, spawn_y: Optional spawn location (defaults to map center)
    
    Colonists spawn in a small group for easier camera positioning.
    """
    colonists: list[Colonist] = []
    
    # Use provided spawn or default to center
    if spawn_x is None or spawn_y is None:
        spawn_x = GRID_W // 2
        spawn_y = GRID_H // 2
    
    cluster_radius = 3  # Spawn within 3 tiles of spawn point
    
    for _ in range(count):
        # Random offset from spawn
        dx = random.randint(-cluster_radius, cluster_radius)
        dy = random.randint(-cluster_radius, cluster_radius)
        colonists.append(
            Colonist(
                x=spawn_x + dx,
                y=spawn_y + dy,
            )
        )
    return colonists


def update_colonists(colonists: Iterable[Colonist], grid: Grid, game_tick: int = 0) -> None:
    """Advance all colonists one simulation step."""

    colonist_list = list(colonists)  # Convert to list for environment sampling
    for c in colonist_list:
        c.update(grid, colonist_list, game_tick)


def draw_colonists(
    surface: pygame.Surface, colonists: Iterable[Colonist], ether_mode: bool = False, current_z: int = 0, camera_x: int = 0, camera_y: int = 0
) -> None:
    """Draw all colonists to the given surface.
    
    Only draws colonists that are on the current z-level.
    
    Args:
        surface: Pygame surface to draw on
        colonists: Iterable of colonist objects
        ether_mode: If True, use ether color
        current_z: Current Z-level to render
        camera_x, camera_y: Camera offset for viewport rendering
    """
    for c in colonists:
        if c.z == current_z:
            c.draw(surface, ether_mode=ether_mode, camera_x=camera_x, camera_y=camera_y)
