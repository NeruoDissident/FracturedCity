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
        """Update sprite position from animal entity."""
        self.center_x = self.animal.x * TILE_SIZE + TILE_SIZE / 2
        self.center_y = self.animal.y * TILE_SIZE + TILE_SIZE / 2


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
        # Draw all sprites on current Z-level
        # Note: We draw the whole sprite list, but only sprites on current_z are visible
        # because we filter during update_sprites or we can filter here
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
