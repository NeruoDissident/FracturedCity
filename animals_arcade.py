"""Animal sprite rendering for Arcade.

Handles GPU-accelerated rendering of all animals using sprite batching.
Similar to colonist_arcade.py but for animals.
"""

import arcade
from typing import Dict, List, Optional
from animals import get_all_animals, Animal
from config import TILE_SIZE


class AnimalSprite(arcade.Sprite):
    """Sprite for an individual animal."""
    
    def __init__(self, animal: Animal):
        super().__init__()
        self.animal = animal
        self.uid = animal.uid
        
        # Smooth movement interpolation
        self.display_x = float(animal.x)
        self.display_y = float(animal.y)
        self.lerp_speed = 0.3  # How fast to interpolate (0.3 = 30% per frame)
        
        # Load texture
        try:
            self.texture = arcade.load_texture(animal.get_sprite_path())
        except Exception as e:
            print(f"[Animals] Failed to load sprite for {animal.species}_{animal.variant}: {e}")
            # Create placeholder colored square
            self.texture = arcade.make_soft_square_texture(TILE_SIZE, arcade.color.MAGENTA, outer_alpha=255)
        
        # Set position
        self.center_x = animal.x * TILE_SIZE + TILE_SIZE / 2
        self.center_y = animal.y * TILE_SIZE + TILE_SIZE / 2
        
        # Scale to tile size
        self.width = TILE_SIZE
        self.height = TILE_SIZE
    
    def update_position(self):
        """Update sprite position from animal entity with smooth interpolation."""
        # Smoothly interpolate display position towards actual position
        target_x = float(self.animal.x)
        target_y = float(self.animal.y)
        
        # Lerp towards target (Rimworld-style smooth movement)
        self.display_x += (target_x - self.display_x) * self.lerp_speed
        self.display_y += (target_y - self.display_y) * self.lerp_speed
        
        # Snap if very close (avoid infinite tiny movements)
        if abs(target_x - self.display_x) < 0.01:
            self.display_x = target_x
        if abs(target_y - self.display_y) < 0.01:
            self.display_y = target_y
        
        # Convert to pixel coordinates
        self.center_x = self.display_x * TILE_SIZE + TILE_SIZE / 2
        self.center_y = self.display_y * TILE_SIZE + TILE_SIZE / 2


class AnimalRenderer:
    """Manages all animal sprites with GPU batching."""
    
    def __init__(self):
        self.sprites: Dict[int, AnimalSprite] = {}  # uid -> sprite
        self.sprite_list = arcade.SpriteList()
        print("[AnimalRenderer] Initialized")
    
    def update_sprites(self):
        """Sync sprites with animal entities."""
        animals = get_all_animals()
        current_uids = {a.uid for a in animals}
        
        # Remove sprites for dead/removed animals
        for uid in list(self.sprites.keys()):
            if uid not in current_uids:
                sprite = self.sprites[uid]
                self.sprite_list.remove(sprite)
                del self.sprites[uid]
        
        # Add/update sprites
        for animal in animals:
            if not animal.is_alive():
                continue
            
            if animal.uid not in self.sprites:
                # Create new sprite
                sprite = AnimalSprite(animal)
                self.sprites[animal.uid] = sprite
                self.sprite_list.append(sprite)
            else:
                # Update existing sprite position
                self.sprites[animal.uid].update_position()
    
    def draw(self, current_z: int):
        """Draw all animals on the current Z-level.
        
        Args:
            current_z: Current Z-level being viewed
        """
        # Draw shadows first
        for sprite in self.sprite_list:
            if sprite.animal.z == current_z:
                # Draw ellipse shadow slightly below sprite
                shadow_offset_y = -6  # Pixels below sprite (smaller than colonist)
                shadow_width = TILE_SIZE * 0.5
                shadow_height = TILE_SIZE * 0.2
                
                arcade.draw_ellipse_filled(
                    sprite.center_x,
                    sprite.center_y + shadow_offset_y,
                    shadow_width,
                    shadow_height,
                    (0, 0, 0, 70)  # Semi-transparent black (lighter than colonist)
                )
        
        # Draw all sprites on current Z-level
        for sprite in self.sprite_list:
            if sprite.animal.z == current_z:
                # Use arcade's draw method for sprites
                arcade.draw_sprite(sprite)


# Singleton instance
_animal_renderer: Optional[AnimalRenderer] = None


def get_animal_renderer() -> AnimalRenderer:
    """Get or create the animal renderer singleton."""
    global _animal_renderer
    if _animal_renderer is None:
        _animal_renderer = AnimalRenderer()
    return _animal_renderer
