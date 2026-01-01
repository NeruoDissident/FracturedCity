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
        self.bounce_offset_x = 0
        self.bounce_offset_y = 0
        self.bounce_timer = 0
        
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
        base_x = self.colonist.x * TILE_SIZE + TILE_SIZE // 2
        base_y = self.colonist.y * TILE_SIZE + TILE_SIZE // 2
        
        # Apply bounce animation if active
        self.center_x = base_x + self.bounce_offset_x
        self.center_y = base_y + self.bounce_offset_y
        
        # Decay bounce animation
        if self.bounce_timer > 0:
            self.bounce_timer -= 1
            decay = self.bounce_timer / 10.0  # 10 frame animation
            self.bounce_offset_x *= decay
            self.bounce_offset_y *= decay
        else:
            self.bounce_offset_x = 0
            self.bounce_offset_y = 0
        
        # Update visibility based on z-level (will implement z-level filtering later)
        self.visible = True
    
    def trigger_attack_bounce(self, target_x: int, target_y: int):
        """Trigger bounce animation towards target."""
        # Calculate direction to target
        dx = target_x - self.colonist.x
        dy = target_y - self.colonist.y
        
        # Normalize and scale
        dist = max(abs(dx), abs(dy), 1)
        bounce_strength = TILE_SIZE * 0.3
        
        self.bounce_offset_x = (dx / dist) * bounce_strength
        self.bounce_offset_y = (dy / dist) * bounce_strength
        self.bounce_timer = 10  # 10 frame animation


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
            # Store reference in colonist for combat animations
            colonist._arcade_sprite = sprite
    
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
        
        # Draw combat halos BEHIND colonists
        self._draw_combat_halos(current_z)
        
        # Draw all sprites (Arcade will skip invisible ones)
        self.sprite_list.draw()
        
        # Draw NPC icons above colonists (visitors, merchants, raiders)
        self._draw_npc_icons(current_z)
        
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
    
    def _draw_combat_halos(self, current_z: int = 0):
        """Draw red halos around colonists in combat."""
        for sprite in self.colonist_sprites.values():
            colonist = sprite.colonist
            
            # Only draw for colonists on current Z-level
            if colonist.z != current_z:
                continue
            
            # Check if colonist is in combat
            if not colonist.in_combat:
                continue
            
            # Draw pulsing red halo
            import time
            pulse = abs((time.time() * 3) % 2 - 1)  # 0->1->0 pulse
            alpha = int(100 + pulse * 80)  # 100-180 alpha
            
            # Red glow circle
            arcade.draw_circle_filled(
                sprite.center_x,
                sprite.center_y,
                TILE_SIZE * 0.6,
                (255, 50, 50, alpha)
            )
            
            # Outer red ring
            arcade.draw_circle_outline(
                sprite.center_x,
                sprite.center_y,
                TILE_SIZE * 0.6,
                (255, 100, 100),
                2
            )
    
    def _draw_npc_icons(self, current_z: int = 0):
        """Draw identifying icons above NPCs (visitors, merchants, raiders)."""
        from wanderers import _wanderers, _fixers
        
        # Draw visitor icons (?) - cyan question marks
        for wanderer in _wanderers:
            if wanderer.get("z", 0) != current_z:
                continue
            
            x = wanderer["x"]
            y = wanderer["y"]
            center_x = x * TILE_SIZE + TILE_SIZE // 2
            center_y = y * TILE_SIZE + TILE_SIZE // 2 + TILE_SIZE * 0.7
            
            # Draw background circle
            arcade.draw_circle_filled(
                center_x, center_y, 10,
                (0, 0, 0, 180)
            )
            
            # Draw cyan question mark
            arcade.draw_text(
                "?",
                center_x, center_y - 4,
                (0, 255, 255),
                font_size=16,
                bold=True,
                anchor_x="center",
                anchor_y="center"
            )
        
        # Draw merchant icons ($) - yellow/gold dollar signs
        for fixer in _fixers:
            if fixer.get("z", 0) != current_z:
                continue
            
            x = fixer["x"]
            y = fixer["y"]
            center_x = x * TILE_SIZE + TILE_SIZE // 2
            center_y = y * TILE_SIZE + TILE_SIZE // 2 + TILE_SIZE * 0.7
            
            # Draw background circle
            arcade.draw_circle_filled(
                center_x, center_y, 10,
                (0, 0, 0, 180)
            )
            
            # Draw gold dollar sign
            arcade.draw_text(
                "$",
                center_x, center_y - 4,
                (255, 215, 0),
                font_size=16,
                bold=True,
                anchor_x="center",
                anchor_y="center"
            )
        
        # Draw raider icons (!) - red exclamation marks
        # Check for raiders in colonist list (they have is_hostile=True and not in colony)
        for sprite in self.colonist_sprites.values():
            colonist = sprite.colonist
            
            if colonist.z != current_z:
                continue
            
            # Raiders are hostile and not part of colony
            if colonist.is_hostile and getattr(colonist, 'is_raider', False):
                center_x = sprite.center_x
                center_y = sprite.center_y + TILE_SIZE * 0.7
                
                # Draw background circle
                arcade.draw_circle_filled(
                    center_x, center_y, 10,
                    (0, 0, 0, 180)
                )
                
                # Draw red exclamation mark
                arcade.draw_text(
                    "!",
                    center_x, center_y - 4,
                    (255, 50, 50),
                    font_size=16,
                    bold=True,
                    anchor_x="center",
                    anchor_y="center"
                )
