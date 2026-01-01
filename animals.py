"""
Animal system for Fractured City.

Handles wild and tamed animals including:
- Spawning and behavior
- Hunting mechanics
- Taming and husbandry
- Animal products and breeding
"""

import random
from typing import Dict, List, Tuple, Optional
from enum import Enum


class AnimalState(Enum):
    """Animal behavior states."""
    IDLE = "idle"
    WANDERING = "wandering"
    FLEEING = "fleeing"
    EATING = "eating"
    SLEEPING = "sleeping"
    TAMED_IDLE = "tamed_idle"
    HUNTING = "hunting"
    # Bird-specific states
    FLYING = "flying"  # Birds in flight (default for birds)
    SEEKING_PERCH = "seeking_perch"  # Flying toward rooftop
    PERCHED = "perched"  # Stationary on rooftop  # For predators


class AnimalSpecies:
    """Animal species definitions."""
    
    # Rats - ground level scavengers
    RAT = {
        "id": "rat",
        "name": "Rat",
        "variants": 4,  # rat_0 through rat_3
        "z_levels": [0],  # Ground only
        "size": 1,  # Tiles
        "speed": 1.0,
        "health": 20,
        "aggression": 0.1,  # 10% chance to fight back
        "flee_distance": 8,
        "tame_difficulty": 30,  # Easy to tame
        "corpse_item": "rat_corpse",
        "meat_yield": (1, 2),
        "materials": {"rat_pelt": (1, 1)},
        "spawn_weight": 0.4,  # 40% of spawns
        "spawn_locations": ["ruins", "ground", "trash"],
    }
    
    # Birds - rooftop and airborne
    BIRD = {
        "id": "bird",
        "name": "Bird",
        "variants": 1,  # bird_0 for now
        "z_levels": [1, 2],  # Rooftops
        "size": 1,
        "speed": 1.5,  # Faster than rats
        "health": 15,
        "aggression": 0.0,  # Never fights back
        "flee_distance": 12,
        "tame_difficulty": 40,  # Medium difficulty
        "corpse_item": "bird_corpse",
        "meat_yield": (2, 3),
        "materials": {"feathers": (1, 2)},
        "spawn_weight": 0.6,  # 60% of spawns
        "spawn_locations": ["rooftop", "ledge", "open"],
    }


class Animal:
    """Individual animal entity."""
    
    _next_uid = 1
    
    def __init__(self, species_id: str, x: int, y: int, z: int, variant: int = 0):
        """Create a new animal.
        
        Args:
            species_id: Species identifier (rat, bird, etc.)
            x, y, z: Spawn coordinates
            variant: Sprite variant number
        """
        self.uid = Animal._next_uid
        Animal._next_uid += 1
        
        # Get species data
        if species_id == "rat":
            self.species_data = AnimalSpecies.RAT
        elif species_id == "bird":
            self.species_data = AnimalSpecies.BIRD
        else:
            raise ValueError(f"Unknown species: {species_id}")
        
        self.species = species_id
        self.variant = variant
        
        # Position
        self.x = x
        self.y = y
        self.z = z
        
        # State
        if species_id == "bird":
            self.state = AnimalState.FLYING  # Birds start flying
        else:
            self.state = AnimalState.IDLE
        self.state_timer = 0
        self.health = self.species_data["health"]
        self.hunger = 0  # 0-100
        self.thirst = 0  # 0-100
        self.sleep = 0  # 0-100 (0=well rested, 100=exhausted)
        self.age = 0  # Days
        self.mood = 50  # 0-100 (affects taming speed, product quality)
        
        # Behavior
        self.is_wild = True
        self.is_hostile = False
        self.target_x = None
        self.target_y = None
        self.wander_cooldown = 0
        
        # Taming
        self.tame_progress = 0  # 0-100
        self.owner = None  # Colonist UID
        self.pen_location = None  # (x, y, z) of assigned pen
        self.last_fed_tick = 0
        self.taming_colonist = None  # UID of colonist currently taming
        
        # Hunting/fleeing
        self.flee_target = None  # Entity to flee from
        self.hunt_target = None  # Entity to hunt (for predators)
        
        # Products (for tamed animals)
        self.can_lay_eggs = False
        self.last_product_tick = 0
        
        # Preferences (revealed progressively as tame increases)
        self.food_preferences = self._generate_food_preferences()
        self.sleep_pattern = self._generate_sleep_pattern()
        self.pen_preferences = self._generate_pen_preferences()
        
        # Sprite state
        if self.species == "bird":
            self.sprite_state = "flight"  # Birds start flying
        else:
            self.sprite_state = "idle"  # For simple animals
        
        # Bird-specific
        self.perch_timer = 0  # Ticks remaining while perched
        self.last_rooftop_check = 0  # Last tick we checked for rooftop
        
        # Hunting
        self.marked_for_hunt = False  # Designated for hunting
        self.hunter_uid = None  # UID of colonist hunting this animal
    
    def _generate_food_preferences(self) -> Dict[str, float]:
        """Generate food preferences for this animal.
        
        Returns:
            Dict of food_type -> preference (0.0-1.0)
        """
        # Base preferences by species
        if self.species == "rat":
            return {
                "raw_food": 0.8,
                "cooked_meal": 0.6,
                "scrap": 0.4,  # Rats eat anything
            }
        elif self.species == "bird":
            return {
                "raw_food": 0.9,
                "seeds": 1.0,  # Future item
                "insects": 0.7,  # Future item
            }
        return {}
    
    def _generate_sleep_pattern(self) -> Dict[str, any]:
        """Generate sleep pattern for this animal.
        
        Returns:
            Dict with sleep_start, sleep_end, sleep_duration
        """
        if self.species == "rat":
            return {
                "nocturnal": True,
                "sleep_start": 6,  # 6:00 AM
                "sleep_end": 18,   # 6:00 PM
                "sleep_duration": 12,  # Hours
            }
        elif self.species == "bird":
            return {
                "nocturnal": False,
                "sleep_start": 20,  # 8:00 PM
                "sleep_end": 6,     # 6:00 AM
                "sleep_duration": 10,
            }
        return {}
    
    def _generate_pen_preferences(self) -> Dict[str, any]:
        """Generate pen preferences for this animal.
        
        Returns:
            Dict with preferred_items, min_space, max_capacity
        """
        if self.species == "rat":
            return {
                "min_space": 1,  # 1x1 minimum
                "preferred_space": 2,  # 2x2 preferred
                "max_per_pen": 4,
                "preferred_items": ["bedding", "hiding_spot"],  # Future items
                "dislikes": ["bright_light", "loud_noise"],
            }
        elif self.species == "bird":
            return {
                "min_space": 2,  # 2x2 minimum
                "preferred_space": 3,  # 3x3 preferred
                "max_per_pen": 6,
                "preferred_items": ["perch", "nesting_box"],  # Future items
                "dislikes": ["enclosed_space", "predators"],
                "requires_rooftop": True,  # Birds need outdoor access
            }
        return {}
    
    def get_sprite_path(self) -> str:
        """Get sprite path for this animal."""
        # For birds with multiple states
        if self.species == "bird":
            # Use perched only when PERCHED state, otherwise flight
            state = "perched" if self.state == AnimalState.PERCHED else "flight"
            return f"assets/animals/{self.species}_{self.variant}_{state}.png"
        # For simple animals (rats, etc)
        return f"assets/animals/{self.species}_{self.variant}.png"
    
    def is_alive(self) -> bool:
        """Check if animal is alive."""
        return self.health > 0
    
    def take_damage(self, amount: int) -> bool:
        """Apply damage to animal.
        
        Returns:
            True if animal died from damage
        """
        self.health -= amount
        # Damage affects mood
        self.mood = max(0, self.mood - 10)
        if self.health <= 0:
            self.health = 0
            return True
        return False
    
    def feed(self, food_type: str, game_tick: int) -> float:
        """Feed the animal.
        
        Args:
            food_type: Type of food given
            game_tick: Current game tick
        
        Returns:
            Taming progress gained (0.0-10.0)
        """
        # Reduce hunger
        self.hunger = max(0, self.hunger - 30)
        self.last_fed_tick = game_tick
        
        # Check food preference
        preference = self.food_preferences.get(food_type, 0.5)
        
        # Mood bonus for preferred food
        mood_gain = int(preference * 10)
        self.mood = min(100, self.mood + mood_gain)
        
        # Taming progress based on preference and mood
        if self.is_wild:
            base_gain = 5.0
            preference_mult = preference
            mood_mult = self.mood / 100.0
            taming_gain = base_gain * preference_mult * mood_mult
            self.tame_progress = min(100, self.tame_progress + taming_gain)
            return taming_gain
        
        return 0.0
    
    def get_mood_description(self) -> str:
        """Get text description of current mood."""
        if self.mood >= 80:
            return "Happy"
        elif self.mood >= 60:
            return "Content"
        elif self.mood >= 40:
            return "Neutral"
        elif self.mood >= 20:
            return "Unhappy"
        else:
            return "Miserable"
    
    def update_needs(self, game_tick: int) -> None:
        """Update hunger, thirst, sleep over time."""
        # Hunger increases slowly
        if game_tick % 100 == 0:  # Every 100 ticks
            self.hunger = min(100, self.hunger + 1)
            self.thirst = min(100, self.thirst + 1)
        
        # Sleep increases based on time of day
        # TODO: Integrate with game time system
        
        # Mood decreases if needs are high
        if self.hunger > 75 or self.thirst > 75:
            self.mood = max(0, self.mood - 1)
        
        # Mood increases slowly if needs are met
        if self.hunger < 25 and self.thirst < 25:
            self.mood = min(100, self.mood + 1)
    
    def start_fleeing(self, threat_x: int, threat_y: int):
        """Start fleeing from a threat."""
        self.state = AnimalState.FLEEING
        self.state_timer = 100  # Flee for 100 ticks
        # Calculate flee direction (away from threat)
        dx = self.x - threat_x
        dy = self.y - threat_y
        # Normalize and extend
        dist = max(abs(dx), abs(dy), 1)
        flee_dist = self.species_data["flee_distance"]
        self.target_x = self.x + int((dx / dist) * flee_dist)
        self.target_y = self.y + int((dy / dist) * flee_dist)


# =============================================================================
# GLOBAL ANIMAL REGISTRY
# =============================================================================

_ANIMALS: Dict[int, Animal] = {}  # uid -> Animal


def register_animal(animal: Animal) -> None:
    """Add animal to global registry."""
    _ANIMALS[animal.uid] = animal


def unregister_animal(uid: int) -> None:
    """Remove animal from registry."""
    if uid in _ANIMALS:
        del _ANIMALS[uid]


def get_animal(uid: int) -> Optional[Animal]:
    """Get animal by UID."""
    return _ANIMALS.get(uid)


def get_all_animals() -> List[Animal]:
    """Get all registered animals."""
    return list(_ANIMALS.values())


def get_animals_at(x: int, y: int, z: int) -> List[Animal]:
    """Get all animals at a specific location."""
    return [a for a in _ANIMALS.values() if a.x == x and a.y == y and a.z == z]


def get_animals_in_range(x: int, y: int, z: int, radius: int) -> List[Animal]:
    """Get all animals within radius of a location."""
    animals = []
    for animal in _ANIMALS.values():
        if animal.z != z:
            continue
        dx = abs(animal.x - x)
        dy = abs(animal.y - y)
        if max(dx, dy) <= radius:
            animals.append(animal)
    return animals


# =============================================================================
# HUNTING DESIGNATIONS
# =============================================================================

def mark_for_hunt(animal: Animal) -> bool:
    """Mark an animal for hunting.
    
    Args:
        animal: Animal to mark
    
    Returns:
        True if marked, False if already marked or dead
    """
    if not animal.is_alive():
        return False
    if animal.marked_for_hunt:
        return False
    
    animal.marked_for_hunt = True
    print(f"[Animals] {animal.species}_{animal.variant} marked for hunting at ({animal.x}, {animal.y}, z={animal.z})")
    return True


def unmark_for_hunt(animal: Animal) -> None:
    """Remove hunting designation from animal."""
    animal.marked_for_hunt = False
    animal.hunter_uid = None


def get_huntable_animals() -> List[Animal]:
    """Get all animals marked for hunting that are alive and not being hunted."""
    return [a for a in _ANIMALS.values() if a.marked_for_hunt and a.is_alive() and a.hunter_uid is None]


# =============================================================================
# ANIMAL SPAWNING
# =============================================================================

def can_spawn_animal_at(grid, x: int, y: int, z: int, species_id: str) -> bool:
    """Check if an animal can spawn at this location.
    
    Args:
        grid: Game grid
        x, y, z: Coordinates
        species_id: Species to spawn
    
    Returns:
        True if valid spawn location
    """
    if not grid.in_bounds(x, y, z):
        return False
    
    # Get species data
    if species_id == "rat":
        species_data = AnimalSpecies.RAT
    elif species_id == "bird":
        species_data = AnimalSpecies.BIRD
    else:
        return False
    
    # Check Z-level
    if z not in species_data["z_levels"]:
        return False
    
    # Check tile is passable
    tile = grid.get_tile(x, y, z)
    if tile in ["void", "wall", "window"]:
        return False
    
    # Check no other animal already here
    if get_animals_at(x, y, z):
        return False
    
    # Check no colonist here
    # TODO: Check colonist positions when integrated
    
    return True


def spawn_animal(grid, species_id: str, x: int, y: int, z: int, variant: int = None) -> Optional[Animal]:
    """Spawn a new animal at location.
    
    Args:
        grid: Game grid
        species_id: Species to spawn
        x, y, z: Coordinates
        variant: Sprite variant (random if None)
    
    Returns:
        Spawned animal or None if failed
    """
    if not can_spawn_animal_at(grid, x, y, z, species_id):
        return None
    
    # Get species data for variant count
    if species_id == "rat":
        species_data = AnimalSpecies.RAT
    elif species_id == "bird":
        species_data = AnimalSpecies.BIRD
    else:
        return None
    
    # Random variant if not specified
    if variant is None:
        variant = random.randint(0, species_data["variants"] - 1)
    
    # Create and register animal
    animal = Animal(species_id, x, y, z, variant)
    register_animal(animal)
    
    print(f"[Animals] Spawned {species_id}_{variant} at ({x}, {y}, z={z})")
    return animal


def spawn_random_animals(grid, count: int = 1, z_level: int = None) -> int:
    """Spawn random animals in valid locations.
    
    Args:
        grid: Game grid
        count: Number of animals to spawn
        z_level: Specific Z-level or None for any
    
    Returns:
        Number of animals successfully spawned
    """
    spawned = 0
    attempts = 0
    max_attempts = count * 10  # Prevent infinite loop
    
    while spawned < count and attempts < max_attempts:
        attempts += 1
        
        # Random species based on spawn weights
        roll = random.random()
        if roll < 0.4:
            species_id = "rat"
            valid_z = [0]
        else:
            species_id = "bird"
            valid_z = [1, 2]
        
        # Pick Z-level
        if z_level is not None:
            z = z_level
            if z not in valid_z:
                continue
        else:
            z = random.choice(valid_z)
        
        # Random location
        x = random.randint(0, grid.width - 1)
        y = random.randint(0, grid.height - 1)
        
        # Try to spawn
        if spawn_animal(grid, species_id, x, y, z):
            spawned += 1
    
    return spawned


# =============================================================================
# ANIMAL UPDATE
# =============================================================================

def update_animals(grid, game_tick: int) -> None:
    """Update all animals each tick."""
    for animal in list(_ANIMALS.values()):
        # Skip dead animals
        if not animal.is_alive():
            continue
        
        # Check if being hunted and hunter is nearby
        if animal.marked_for_hunt and animal.hunter_uid is not None:
            _check_hunter_proximity(animal)
        
        # Decrease state timer
        if animal.state_timer > 0:
            animal.state_timer -= 1
        
        # State machine
        if animal.state == AnimalState.IDLE:
            _update_idle(animal, grid, game_tick)
        elif animal.state == AnimalState.WANDERING:
            _update_wandering(animal, grid, game_tick)
        elif animal.state == AnimalState.FLEEING:
            _update_fleeing(animal, grid, game_tick)
        elif animal.state == AnimalState.TAMED_IDLE:
            _update_tamed_idle(animal, grid, game_tick)
        # Bird-specific states
        elif animal.state == AnimalState.FLYING:
            _update_flying(animal, grid, game_tick)
        elif animal.state == AnimalState.SEEKING_PERCH:
            _update_seeking_perch(animal, grid, game_tick)
        elif animal.state == AnimalState.PERCHED:
            _update_perched(animal, grid, game_tick)


def _update_idle(animal: Animal, grid, game_tick: int) -> None:
    """Update idle animal behavior."""
    # Decrease wander cooldown
    if animal.wander_cooldown > 0:
        animal.wander_cooldown -= 1
    
    # Species-specific wander rates
    if animal.species == "rat":
        wander_chance = 0.03  # 3% - reduced from 8%, rats move less often
        wander_distance = 3  # Reduced from 5, shorter jumps
        cooldown = 40  # Increased from 20, longer wait between moves
    elif animal.species == "bird":
        wander_chance = 0.03  # 3% - birds are calmer, perch more
        wander_distance = 8  # Longer flights when they do move
        cooldown = 60  # Longer cooldown between flights
    else:
        wander_chance = 0.05
        wander_distance = 5
        cooldown = 30
    
    # Random chance to start wandering
    if animal.wander_cooldown <= 0 and random.random() < wander_chance:
        # Pick random nearby destination
        dx = random.randint(-wander_distance, wander_distance)
        dy = random.randint(-wander_distance, wander_distance)
        target_x = animal.x + dx
        target_y = animal.y + dy
        
        if grid.in_bounds(target_x, target_y, animal.z):
            animal.target_x = target_x
            animal.target_y = target_y
            animal.state = AnimalState.WANDERING
            animal.wander_cooldown = cooldown


def _update_wandering(animal: Animal, grid, game_tick: int) -> None:
    """Update wandering animal movement."""
    if animal.target_x is None or animal.target_y is None:
        animal.state = AnimalState.IDLE
        return
    
    # Move towards target
    dx = animal.target_x - animal.x
    dy = animal.target_y - animal.y
    
    # Reached target
    if dx == 0 and dy == 0:
        animal.state = AnimalState.IDLE
        animal.target_x = None
        animal.target_y = None
        return
    
    # Species-specific movement speed (skip ticks for slower animals)
    if animal.species == "bird":
        # Birds move every other tick (smoother, slower flight)
        if game_tick % 2 != 0:
            return
    # Rats move every tick (fast and twitchy)
    
    # Move one step
    move_x = 0 if dx == 0 else (1 if dx > 0 else -1)
    move_y = 0 if dy == 0 else (1 if dy > 0 else -1)
    
    new_x = animal.x + move_x
    new_y = animal.y + move_y
    
    # Check if can move there
    if can_spawn_animal_at(grid, new_x, new_y, animal.z, animal.species):
        animal.x = new_x
        animal.y = new_y
    else:
        # Blocked, stop wandering
        animal.state = AnimalState.IDLE
        animal.target_x = None
        animal.target_y = None


def _check_hunter_proximity(animal: Animal) -> None:
    """Check if hunter is nearby and flee if so."""
    # Get hunter colonist - we need to get it from the game's colonist list
    # This will be passed in via the main update loop
    # For now, skip the proximity check if we can't get colonists
    return
    
    hunter = None
    for c in colonists:
        if c.uid == animal.hunter_uid:
            hunter = c
            break
    
    if hunter is None:
        return
    
    # Calculate distance to hunter
    dx = abs(animal.x - hunter.x)
    dy = abs(animal.y - hunter.y)
    dist = max(dx, dy)
    
    # If hunter is within flee distance, start fleeing
    flee_distance = animal.species_data.get("flee_distance", 8)
    
    if dist <= flee_distance and animal.state != AnimalState.FLEEING:
        # Start fleeing - pick direction away from hunter
        flee_dx = animal.x - hunter.x
        flee_dy = animal.y - hunter.y
        
        # Normalize and multiply by flee distance
        if flee_dx != 0:
            flee_dx = (flee_dx // abs(flee_dx)) * flee_distance
        if flee_dy != 0:
            flee_dy = (flee_dy // abs(flee_dy)) * flee_distance
        
        animal.target_x = animal.x + flee_dx
        animal.target_y = animal.y + flee_dy
        animal.state = AnimalState.FLEEING
        animal.state_timer = 120  # Flee for 2 seconds


def _update_fleeing(animal: Animal, grid, game_tick: int) -> None:
    """Update fleeing animal behavior."""
    # Stop fleeing after timer expires
    if animal.state_timer <= 0:
        animal.state = AnimalState.IDLE
        animal.target_x = None
        animal.target_y = None
        return
    
    # Move away from threat - faster than normal wandering
    if animal.target_x is None or animal.target_y is None:
        animal.state = AnimalState.IDLE
        return
    
    # Move towards flee target (every tick for fast escape)
    dx = animal.target_x - animal.x
    dy = animal.target_y - animal.y
    
    # Reached target
    if dx == 0 and dy == 0:
        animal.state = AnimalState.IDLE
        animal.target_x = None
        animal.target_y = None
        return
    
    # Move one step
    move_x = 0 if dx == 0 else (1 if dx > 0 else -1)
    move_y = 0 if dy == 0 else (1 if dy > 0 else -1)
    
    new_x = animal.x + move_x
    new_y = animal.y + move_y
    
    # Check if new position is valid
    if grid.in_bounds(new_x, new_y, animal.z):
        # Animals can move through most tiles when fleeing
        animal.x = new_x
        animal.y = new_y


def _update_tamed_idle(animal: Animal, grid, game_tick: int) -> None:
    """Update tamed animal behavior."""
    # Tamed animals stay near their pen
    # TODO: Implement pen system and stay-near behavior
    pass


# =============================================================================
# BIRD-SPECIFIC BEHAVIOR
# =============================================================================

def _check_for_rooftop(animal: Animal, grid) -> Optional[Tuple[int, int]]:
    """Check nearby area for rooftop perch spot.
    
    Args:
        animal: Bird to check for
        grid: Game grid
    
    Returns:
        (x, y) of rooftop tile or None
    """
    # Only check if on rooftop level (z >= 1)
    if animal.z < 1:
        return None
    
    # Check 3x3 area around bird
    for dx in range(-1, 2):
        for dy in range(-1, 2):
            check_x = animal.x + dx
            check_y = animal.y + dy
            
            if not grid.in_bounds(check_x, check_y, animal.z):
                continue
            
            tile = grid.get_tile(check_x, check_y, animal.z)
            
            # Rooftop tiles are floor types on z >= 1
            if tile in ["floor", "concrete", "metal", "wood_floor"]:
                # Make sure it's not occupied by another animal
                if not get_animals_at(check_x, check_y, animal.z):
                    return (check_x, check_y)
    
    return None


def _update_flying(animal: Animal, grid, game_tick: int) -> None:
    """Update bird flying behavior."""
    # Birds fly continuously, occasionally looking for rooftops
    
    # 10% chance per tick to look for rooftop (throttled)
    if game_tick - animal.last_rooftop_check > 30:  # Don't check every tick
        if random.random() < 0.1:
            animal.last_rooftop_check = game_tick
            rooftop = _check_for_rooftop(animal, grid)
            
            if rooftop:
                animal.target_x, animal.target_y = rooftop
                animal.state = AnimalState.SEEKING_PERCH
                return
    
    # Continue flying - pick random destination if no target
    if animal.target_x is None or animal.target_y is None:
        # Pick random nearby destination
        dx = random.randint(-8, 8)
        dy = random.randint(-8, 8)
        target_x = animal.x + dx
        target_y = animal.y + dy
        
        if grid.in_bounds(target_x, target_y, animal.z):
            animal.target_x = target_x
            animal.target_y = target_y
    
    # Move towards target (birds move every other tick)
    if game_tick % 2 == 0 and animal.target_x is not None and animal.target_y is not None:
        dx = animal.target_x - animal.x
        dy = animal.target_y - animal.y
        
        # Reached target, pick new one
        if dx == 0 and dy == 0:
            animal.target_x = None
            animal.target_y = None
            return
        
        # Move one step
        move_x = 0 if dx == 0 else (1 if dx > 0 else -1)
        move_y = 0 if dy == 0 else (1 if dy > 0 else -1)
        
        new_x = animal.x + move_x
        new_y = animal.y + move_y
        
        # Birds can fly over anything, just check bounds
        if grid.in_bounds(new_x, new_y, animal.z):
            animal.x = new_x
            animal.y = new_y


def _update_seeking_perch(animal: Animal, grid, game_tick: int) -> None:
    """Update bird seeking perch behavior."""
    if animal.target_x is None or animal.target_y is None:
        # Lost target, go back to flying
        animal.state = AnimalState.FLYING
        return
    
    # Move towards perch spot (birds move every other tick)
    if game_tick % 2 == 0:
        dx = animal.target_x - animal.x
        dy = animal.target_y - animal.y
        
        # Reached perch spot
        if dx == 0 and dy == 0:
            animal.state = AnimalState.PERCHED
            animal.perch_timer = random.randint(60, 180)  # Perch for 1-3 seconds
            animal.target_x = None
            animal.target_y = None
            return
        
        # Move one step
        move_x = 0 if dx == 0 else (1 if dx > 0 else -1)
        move_y = 0 if dy == 0 else (1 if dy > 0 else -1)
        
        new_x = animal.x + move_x
        new_y = animal.y + move_y
        
        # Birds can fly over anything
        if grid.in_bounds(new_x, new_y, animal.z):
            animal.x = new_x
            animal.y = new_y


def _update_perched(animal: Animal, grid, game_tick: int) -> None:
    """Update perched bird behavior."""
    # Count down perch timer
    if animal.perch_timer > 0:
        animal.perch_timer -= 1
    else:
        # Take off and fly again
        animal.state = AnimalState.FLYING
        animal.target_x = None
        animal.target_y = None


# =============================================================================
# ANIMAL DEATH & CORPSES
# =============================================================================

def kill_animal(animal: Animal, grid, game_tick: int) -> Optional[dict]:
    """Kill an animal and create corpse item.
    
    Args:
        animal: Animal to kill (should already have health <= 0)
        grid: Game grid
        game_tick: Current game tick
    
    Returns:
        Corpse item dict or None
    """
    # Ensure health is 0 (caller should have already set this)
    animal.health = 0
    
    # Create corpse as a world item (uses items system, not resources system)
    from items import spawn_world_item
    
    # Use the corpse_item type from species data (e.g., "rat_corpse")
    corpse_type = animal.species_data.get("corpse_item", f"{animal.species}_corpse")
    
    # Spawn corpse at animal's location (auto-marked for hauling)
    success = spawn_world_item(animal.x, animal.y, animal.z, corpse_type, count=1)
    
    if success:
        print(f"[Animals] Created {corpse_type} at ({animal.x}, {animal.y}, z={animal.z})")
    else:
        print(f"[Animals] WARNING: Failed to create corpse {corpse_type} - item not registered?")
    
    # Remove from registry
    unregister_animal(animal.uid)
    
    print(f"[Animals] {animal.species} died at ({animal.x}, {animal.y}, z={animal.z})")
    
    # Return corpse info for logging
    return {
        "type": corpse_type,
        "x": animal.x,
        "y": animal.y,
        "z": animal.z,
    }
