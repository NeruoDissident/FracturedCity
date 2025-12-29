"""
Arcade-based colonist rendering for Fractured City.

Handles converting Colonist objects into Arcade sprites for GPU rendering.
"""

import arcade
from config import TILE_SIZE
from colonist import Colonist


class ColonistSprite(arcade.Sprite):
    """Arcade sprite for a colonist with reference to game logic."""
    
    def __init__(self, colonist: Colonist):
        super().__init__()
        self.colonist = colonist
        
        # Load colonist sprite based on their style
        sprite_path = f"assets/colonists/colonist_{colonist.sprite_style}.png"
        
        try:
            self.texture = arcade.load_texture(sprite_path)
        except:
            # Fallback: use colonist_1.png
            try:
                self.texture = arcade.load_texture("assets/colonists/colonist_1.png")
            except:
                # Last resort: create colored circle (shouldn't happen with your sprites)
                pass
        
        # Set size
        self.width = TILE_SIZE
        self.height = TILE_SIZE
        
        # Initial position
        self.update_position()
    
    def update_position(self):
        """Update sprite position from colonist data."""
        self.center_x = self.colonist.x * TILE_SIZE + TILE_SIZE // 2
        self.center_y = self.colonist.y * TILE_SIZE + TILE_SIZE // 2
        
        # Update visibility based on z-level (will implement z-level filtering later)
        self.visible = True


class ColonistRenderer:
    """Manages rendering all colonists using Arcade sprites."""
    
    def __init__(self):
        self.sprite_list = arcade.SpriteList()
        self.colonist_sprites = {}  # Map colonist.uid -> ColonistSprite
        
    def add_colonist(self, colonist: Colonist):
        """Add a colonist to the renderer."""
        if colonist.uid not in self.colonist_sprites:
            sprite = ColonistSprite(colonist)
            self.colonist_sprites[colonist.uid] = sprite
            self.sprite_list.append(sprite)
    
    def remove_colonist(self, colonist: Colonist):
        """Remove a colonist from the renderer."""
        if colonist.uid in self.colonist_sprites:
            sprite = self.colonist_sprites[colonist.uid]
            sprite.remove_from_sprite_lists()
            del self.colonist_sprites[colonist.uid]
    
    def update_positions(self):
        """Update all colonist sprite positions from game data."""
        for sprite in self.colonist_sprites.values():
            sprite.update_position()
    
    def draw(self, current_z: int = 0):
        """Draw all colonists on the current z-level."""
        # Filter sprite list to only show colonists on current Z-level
        for sprite in self.colonist_sprites.values():
            sprite.visible = (sprite.colonist.z == current_z)
        
        # Draw all sprites (Arcade will skip invisible ones)
        self.sprite_list.draw()
        
        # Draw hauling indicators above colonists (only for current Z-level)
        self._draw_hauling_indicators(current_z)
    
    def _draw_hauling_indicators(self, current_z: int = 0):
        """Draw small icons above colonists showing what they're carrying."""
        for sprite in self.colonist_sprites.values():
            colonist = sprite.colonist
            
            # Only draw for colonists on current Z-level
            if colonist.z != current_z:
                continue
            
            # Only draw if colonist is carrying something
            if colonist.carrying is None:
                continue
            
            # Get carry type and determine color
            carry_type = colonist.carrying.get("type", "")
            
            # Resource colors (matching stockpile visualization)
            if "wood" in carry_type:
                carry_color = (139, 90, 43)
            elif "scrap" in carry_type or "metal" in carry_type:
                carry_color = (120, 120, 140)
            elif "mineral" in carry_type:
                carry_color = (100, 100, 120)
            elif "food" in carry_type or "meal" in carry_type:
                carry_color = (100, 200, 100)
            elif "power" in carry_type or "cell" in carry_type:
                carry_color = (255, 220, 0)
            elif carry_type == "equipment":
                carry_color = (150, 150, 200)
            elif carry_type == "furniture":
                carry_color = (180, 140, 100)
            else:
                carry_color = (200, 200, 200)
            
            # Draw small rectangle above colonist
            center_x = sprite.center_x
            center_y = sprite.center_y + TILE_SIZE * 0.6  # Above colonist
            
            box_width = 12
            box_height = 8
            
            # Filled box
            arcade.draw_lrbt_rectangle_filled(
                center_x - box_width / 2,
                center_x + box_width / 2,
                center_y - box_height / 2,
                center_y + box_height / 2,
                carry_color
            )
            
            # White outline
            arcade.draw_lrbt_rectangle_outline(
                center_x - box_width / 2,
                center_x + box_width / 2,
                center_y - box_height / 2,
                center_y + box_height / 2,
                (255, 255, 255),
                1
            )
