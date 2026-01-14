"""
Arcade-based colonist rendering for Fractured City.

Handles converting Colonist objects into Arcade sprites for GPU rendering.
"""

import arcade
from config import TILE_SIZE
from colonist import Colonist


class ColonistSprite(arcade.Sprite):
    """Arcade sprite for a colonist with layered appearance parts."""
    
    def __init__(self, colonist: Colonist):
        super().__init__()
        self.colonist = colonist
        self.bounce_offset_x = 0
        self.bounce_offset_y = 0
        self.bounce_timer = 0
        
        # Smooth movement interpolation
        self.display_x = float(colonist.x)
        self.display_y = float(colonist.y)
        self.lerp_speed = 0.3  # How fast to interpolate (0.3 = 30% per frame)
        
        # Load layered sprite parts based on appearance
        appearance = colonist.appearance
        self.layer_textures = {}  # Store all layer textures
        
        # Load body layer
        body_path = f"assets/colonists/bodies/body_{appearance['body']}_0.png"
        try:
            self.layer_textures['body'] = arcade.load_texture(body_path)
            print(f"[ColonistSprite] Loaded body: {body_path}")
        except Exception as e:
            print(f"[ColonistSprite] Failed to load body: {body_path}, error: {e}")
            self.layer_textures['body'] = None
        
        # Load head layer
        head_path = f"assets/colonists/heads/head_{appearance['head']}.png"
        try:
            self.layer_textures['head'] = arcade.load_texture(head_path)
            print(f"[ColonistSprite] Loaded head: {head_path}")
        except Exception as e:
            print(f"[ColonistSprite] Failed to load head: {head_path}, error: {e}")
            self.layer_textures['head'] = None
        
        # Load hair layer
        hair_path = f"assets/colonists/hair/hair_{appearance['hair']}.png"
        try:
            self.layer_textures['hair'] = arcade.load_texture(hair_path)
            print(f"[ColonistSprite] Loaded hair: {hair_path}")
        except Exception as e:
            print(f"[ColonistSprite] Failed to load hair: {hair_path}, error: {e}")
            self.layer_textures['hair'] = None
        
        # Load equipment layers from colonist.equipment
        self._load_equipment_textures()
        
        # Use body texture as main texture for sprite list compatibility
        self.texture = self.layer_textures.get('body')
        
        # Set size - colonists are 1.5 tiles tall (64x96) for better depth
        self.width = TILE_SIZE
        self.height = TILE_SIZE * 1.5  # 96 pixels tall
        
        # Initial position
        self.update_position()
    
    def _load_equipment_textures(self):
        """Load equipment sprite textures from colonist.equipment."""
        equipment = getattr(self.colonist, 'equipment', {})
        
        # Equipment slots to check (in order they'll be drawn)
        equipment_slots = ['feet', 'body', 'hands', 'weapon', 'head', 'implant', 'charm']
        
        for slot in equipment_slots:
            item_data = equipment.get(slot)
            if item_data is None:
                self.layer_textures[f'equipment_{slot}'] = None
                continue
            
            # Get item ID from item data
            item_id = item_data.get('id', '')
            if not item_id:
                self.layer_textures[f'equipment_{slot}'] = None
                continue
            
            # Try to load equipment sprite
            equipment_path = f"assets/equipment/{slot}/{item_id}.png"
            try:
                self.layer_textures[f'equipment_{slot}'] = arcade.load_texture(equipment_path)
                print(f"[ColonistSprite] Loaded equipment: {equipment_path}")
            except Exception as e:
                # Equipment sprites are optional - print debug info
                print(f"[ColonistSprite] No sprite for {slot}/{item_id} (expected at: {equipment_path})")
                self.layer_textures[f'equipment_{slot}'] = None
    
    def update_equipment(self):
        """Reload equipment textures when equipment changes."""
        self._load_equipment_textures()
    
    def update_position(self):
        """Update sprite position from colonist data with smooth interpolation."""
        # Smoothly interpolate display position towards actual position
        target_x = float(self.colonist.x)
        target_y = float(self.colonist.y)
        
        # Lerp towards target (Rimworld-style smooth movement)
        self.display_x += (target_x - self.display_x) * self.lerp_speed
        self.display_y += (target_y - self.display_y) * self.lerp_speed
        
        # Snap if very close (avoid infinite tiny movements)
        if abs(target_x - self.display_x) < 0.01:
            self.display_x = target_x
        if abs(target_y - self.display_y) < 0.01:
            self.display_y = target_y
        
        # Convert to pixel coordinates
        # For 1.5 tile tall sprites (96px), add +16 offset so feet anchor to tile bottom
        base_x = self.display_x * TILE_SIZE + TILE_SIZE // 2
        base_y = self.display_y * TILE_SIZE + TILE_SIZE // 2 + 16
        
        # Apply sleep offset for shared beds (stacked/overlapping effect)
        sleep_offset_x = 0
        if self.colonist.is_sleeping:
            from beds import get_colonist_bed, get_bed_occupants
            bed_pos = get_colonist_bed(id(self.colonist))
            if bed_pos:
                occupants = get_bed_occupants(*bed_pos)
                if len(occupants) == 2:
                    # Two colonists sharing - apply offset
                    # First colonist (lower ID) offset left, second offset right
                    if occupants[0] == id(self.colonist):
                        sleep_offset_x = -3  # 3 pixels left
                    else:
                        sleep_offset_x = 3   # 3 pixels right
        
        # Apply bounce animation if active
        self.center_x = base_x + self.bounce_offset_x + sleep_offset_x
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
        """Draw all colonists on the current z-level with layered sprites."""
        # Draw shadows FIRST (behind everything)
        self._draw_shadows(current_z)
        
        # Draw combat halos BEHIND colonists
        self._draw_combat_halos(current_z)
        
        # Draw layered colonist sprites (body, head, hair)
        # Sort by Y coordinate for depth (higher Y = further back = draw first, lower Y = closer = draw last)
        sprites_on_z = [(sprite, sprite.colonist) for sprite in self.colonist_sprites.values() 
                        if sprite.colonist.z == current_z]
        sprites_on_z.sort(key=lambda x: x[1].y, reverse=True)
        
        debug_draw_count = 0
        for sprite, colonist in sprites_on_z:
            # Draw each layer in order (back to front)
            # Equipment layers are interleaved with body parts for proper depth
            layers = [
                'equipment_feet',    # Boots under body
                'body',              # Colonist body
                'equipment_body',    # Vest/armor over body
                'equipment_hands',   # Gloves on hands
                'head',              # Colonist head
                'hair',              # Colonist hair (only if no head equipment)
                'equipment_head',    # Hat/helmet (replaces hair)
                'equipment_weapon',  # Weapon held/holstered
                'equipment_implant', # Implants (optional visual)
                'equipment_charm',   # Charms (optional visual)
            ]
            
            # Check if head equipment exists to skip hair
            has_head_equipment = sprite.layer_textures.get('equipment_head') is not None
            
            for layer_name in layers:
                # Skip hair if wearing head equipment
                if layer_name == 'hair' and has_head_equipment:
                    continue
                
                texture = sprite.layer_textures.get(layer_name)
                if texture:
                    # Create temporary sprite for this layer
                    layer_sprite = arcade.Sprite()
                    layer_sprite.texture = texture
                    layer_sprite.center_x = sprite.center_x
                    layer_sprite.center_y = sprite.center_y
                    layer_sprite.width = TILE_SIZE
                    layer_sprite.height = TILE_SIZE * 1.5  # 96 pixels tall
                    arcade.draw_sprite(layer_sprite)
                    debug_draw_count += 1
        
        # Debug output (only print once)
        if not hasattr(self, '_debug_printed'):
            self._debug_printed = True
            print(f"[ColonistRenderer] Drew {debug_draw_count} layers for {len([s for s in self.colonist_sprites.values() if s.colonist.z == current_z])} colonists")
        
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
    
    def _draw_shadows(self, current_z: int = 0):
        """Draw blob shadows under colonists."""
        for sprite in self.colonist_sprites.values():
            colonist = sprite.colonist
            
            # Only draw for colonists on current Z-level
            if colonist.z != current_z:
                continue
            
            # Draw ellipse shadow slightly below and offset
            shadow_offset_y = -8  # Pixels below sprite
            shadow_width = TILE_SIZE * 0.7
            shadow_height = TILE_SIZE * 0.25
            
            arcade.draw_ellipse_filled(
                sprite.center_x,
                sprite.center_y + shadow_offset_y,
                shadow_width,
                shadow_height,
                (0, 0, 0, 80)  # Semi-transparent black
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
