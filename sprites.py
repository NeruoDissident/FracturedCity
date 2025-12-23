"""
Sprite loading and rendering system for Fractured City.

Handles loading sprite sheets, individual sprites, and rendering them with
support for zoom levels, variations, and directional animations.
"""

import pygame
import os
from typing import Dict, Optional, Tuple, List
from pathlib import Path


# ============================================================================
# SPRITE CACHE
# ============================================================================

_SPRITE_CACHE: Dict[str, pygame.Surface] = {}
_SCALED_CACHE: Dict[Tuple[str, int], pygame.Surface] = {}

# Base sprite size (your art will be this size)
BASE_SPRITE_SIZE = 64  # Adjust based on your actual sprite size

# Current zoom level (1.0 = 100%, 2.0 = 200%, etc.)
_current_zoom = 1.0


# ============================================================================
# SPRITE LOADING
# ============================================================================

def load_sprite(sprite_path: str) -> Optional[pygame.Surface]:
    """Load a sprite from the assets folder.
    
    Args:
        sprite_path: Relative path from assets folder (e.g., "tiles/floor.png")
        
    Returns:
        Loaded sprite or None if not found
    """
    if sprite_path in _SPRITE_CACHE:
        return _SPRITE_CACHE[sprite_path]
    
    # Try to load from assets folder with subfolder
    full_path = Path("assets") / sprite_path
    
    # If not found in subfolder, try directly in assets folder
    if not full_path.exists():
        # Extract just the filename and try in assets root
        filename = Path(sprite_path).name
        full_path = Path("assets") / filename
    
    if not full_path.exists():
        return None
    
    try:
        sprite = pygame.image.load(str(full_path)).convert_alpha()
        _SPRITE_CACHE[sprite_path] = sprite
        print(f"[DEBUG Sprite] Successfully loaded: {sprite_path} from {full_path}")
        return sprite
    except Exception as e:
        print(f"[Sprites] Failed to load {sprite_path}: {e}")
        return None


def get_scaled_sprite(sprite_path: str, target_size: int, apply_construction_tint: bool = False) -> Optional[pygame.Surface]:
    """Get a sprite scaled to target size (with caching).
    
    Args:
        sprite_path: Path to sprite file
        target_size: Target width/height in pixels
        apply_construction_tint: If True, apply desaturated/darker tint for under-construction appearance
        
    Returns:
        Scaled sprite or None
    """
    cache_key = (sprite_path, target_size, apply_construction_tint)
    
    if cache_key in _SCALED_CACHE:
        return _SCALED_CACHE[cache_key]
    
    sprite = load_sprite(sprite_path)
    if sprite is None:
        return None
    
    # Scale sprite to target size (preserve aspect ratio by fitting to target)
    width, height = sprite.get_size()
    if width != height:
        # Non-square sprite - scale to fit within target size, preserving aspect ratio
        aspect = width / height
        if aspect > 1:  # Wider than tall
            new_width = target_size
            new_height = int(target_size / aspect)
        else:  # Taller than wide
            new_width = int(target_size * aspect)
            new_height = target_size
        scaled = pygame.transform.scale(sprite, (new_width, new_height))
    else:
        scaled = pygame.transform.scale(sprite, (target_size, target_size))
    
    # Apply construction tint if requested
    if apply_construction_tint:
        scaled = apply_construction_tint_to_surface(scaled)
    
    _SCALED_CACHE[cache_key] = scaled
    return scaled


def apply_construction_tint_to_surface(surface: pygame.Surface) -> pygame.Surface:
    """Apply a desaturated, darker tint to a surface for under-construction appearance.
    
    Args:
        surface: Original surface
        
    Returns:
        New surface with construction tint applied
    """
    # Create a copy to avoid modifying the original
    tinted = surface.copy()
    
    # Create a semi-transparent dark overlay with slight blue tint (blueprint-like)
    overlay = pygame.Surface(tinted.get_size(), pygame.SRCALPHA)
    # Dark blue-gray overlay at ~40% opacity
    overlay.fill((60, 70, 85, 100))
    
    # Blend the overlay onto the sprite
    tinted.blit(overlay, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    
    return tinted


def clear_scaled_cache():
    """Clear the scaled sprite cache (call when zoom changes)."""
    _SCALED_CACHE.clear()


def set_zoom(zoom: float):
    """Set the current zoom level and clear scaled cache."""
    global _current_zoom
    if zoom != _current_zoom:
        _current_zoom = zoom
        clear_scaled_cache()


def get_zoom() -> float:
    """Get current zoom level."""
    return _current_zoom


# ============================================================================
# TILE SPRITES
# ============================================================================

def get_tile_sprite(tile_type: str, x: int, y: int, z: int, tile_size: int, apply_construction_tint: bool = False) -> Optional[pygame.Surface]:
    """Get a sprite for a tile type with variation support.
    
    Args:
        tile_type: Type of tile (e.g., "finished_floor", "finished_wall")
        x, y, z: Tile coordinates (for variation selection)
        tile_size: Target size in pixels
        apply_construction_tint: If True, apply construction tint to sprite
        
    Returns:
        Scaled sprite or None if not found
    """
    # For workstations and single-sprite items, try base sprite first
    # (workstations don't need variations)
    # Exclude resource nodes which DO use variations
    # Check for furniture sprites first (crash_bed, instruments, etc.)
    furniture_types = ["crash_bed", "comfort_chair", "bar_stool", "storage_locker",
                      "drum_kit_placed", "scrap_guitar_placed", "synth_placed", 
                      "harmonica_placed", "amp_placed"]
    if tile_type in furniture_types:
        sprite_path = f"furniture/{tile_type}.png"
        sprite = get_scaled_sprite(sprite_path, tile_size, apply_construction_tint)
        if sprite is not None:
            return sprite
    
    if tile_type.startswith("finished_") and not tile_type in ("finished_floor", "finished_wall", "finished_wall_advanced", "finished_stage", "finished_stage_stairs", "finished_bridge"):
        if not tile_type.endswith("_node") and not tile_type.endswith("_node_depleted"):
            # Try workstations folder first for workstation sprites
            workstation_types = ["finished_stove", "finished_generator", "finished_gutter_forge", 
                                "finished_salvagers_bench", "finished_spark_bench", "finished_tinker_station",
                                "finished_gutter_still", "finished_skinshop_loom", "finished_cortex_spindle", "finished_barracks"]
            if tile_type in workstation_types:
                sprite_path = f"workstations/{tile_type}.png"
                sprite = get_scaled_sprite(sprite_path, tile_size, apply_construction_tint)
                if sprite is not None:
                    return sprite
            
            # Fall back to tiles folder
            sprite_path = f"tiles/{tile_type}.png"
            sprite = get_scaled_sprite(sprite_path, tile_size, apply_construction_tint)
            if sprite is not None:
                return sprite
    
    # Try variations 0-8 for bridges, 0-7 for others
    max_variation_counts = [9, 8, 6, 4, 3, 2, 1] if tile_type == "finished_bridge" else [8, 6, 4, 3, 2, 1]
    for max_variations in max_variation_counts:
        variation_index = (x * 7 + y * 13 + z * 3) % max_variations
        sprite_path = f"tiles/{tile_type}_{variation_index}.png"
        sprite = get_scaled_sprite(sprite_path, tile_size, apply_construction_tint)
        
        if sprite is not None:
            return sprite
    
    # Fall back to base sprite (no variation)
    sprite_path = f"tiles/{tile_type}.png"
    return get_scaled_sprite(sprite_path, tile_size, apply_construction_tint)


# ============================================================================
# COLONIST SPRITES
# ============================================================================

class ColonistSprite:
    """Manages colonist sprite rendering with directional animations."""
    
    # Direction mappings
    NORTH = "north"
    SOUTH = "south"
    EAST = "east"
    WEST = "west"
    
    def __init__(self, colonist_id: str = "default"):
        """Initialize colonist sprite manager.
        
        Args:
            colonist_id: Identifier for colonist type/variation
        """
        self.colonist_id = colonist_id
        self.current_direction = self.SOUTH
        self.animation_frame = 0
        self.animation_timer = 0
        
    def get_sprite(self, direction: str, is_moving: bool, tile_size: int) -> Optional[pygame.Surface]:
        """Get the appropriate colonist sprite.
        
        Args:
            direction: Direction facing (north, south, east, west)
            is_moving: Whether colonist is currently moving
            tile_size: Target size in pixels
            
        Returns:
            Scaled sprite or None
        """
        # Build sprite path based on direction
        # For south: alternate between east and west sprites
        if direction == self.SOUTH and is_moving:
            # Alternate between east and west for south movement
            sprite_dir = self.EAST if self.animation_frame % 2 == 0 else self.WEST
        else:
            sprite_dir = direction
        
        sprite_path = f"colonists/{self.colonist_id}_{sprite_dir}.png"
        return get_scaled_sprite(sprite_path, tile_size)
    
    def update_animation(self, dt: float, is_moving: bool):
        """Update animation state.
        
        Args:
            dt: Delta time in seconds
            is_moving: Whether colonist is moving
        """
        if is_moving:
            self.animation_timer += dt
            # Switch frame every 0.2 seconds
            if self.animation_timer >= 0.2:
                self.animation_timer = 0
                self.animation_frame += 1
        else:
            self.animation_frame = 0
            self.animation_timer = 0


def get_colonist_direction(dx: float, dy: float) -> str:
    """Determine colonist facing direction from movement delta.
    
    Args:
        dx: X movement delta
        dy: Y movement delta
        
    Returns:
        Direction string (north, south, east, west)
    """
    if abs(dx) > abs(dy):
        return ColonistSprite.EAST if dx > 0 else ColonistSprite.WEST
    else:
        return ColonistSprite.SOUTH if dy > 0 else ColonistSprite.NORTH


def get_colonist_sprite(direction: str, is_moving: bool, tile_size: int, colonist_id: str = "default") -> Optional[pygame.Surface]:
    """Get colonist sprite for rendering.
    
    Supports two naming patterns:
    1. Single sprite: colonists/colonist_X.png (where X is a number)
    2. Directional: colonists/{colonist_id}_{direction}.png (legacy)
    
    Args:
        direction: Direction facing (north, south, east, west)
        is_moving: Whether colonist is moving
        tile_size: Target size in pixels
        colonist_id: Colonist type/variation ID (e.g., "default", "1", "2", "corpo_m_1")
        
    Returns:
        Scaled sprite or None if not found
    """
    # Try single-sprite pattern first: colonist_X.png
    # This allows simple naming like colonist_1.png, colonist_2.png, etc.
    if colonist_id.isdigit() or colonist_id == "default":
        sprite_path = f"colonists/colonist_{colonist_id}.png"
        sprite = get_scaled_sprite(sprite_path, tile_size)
        if sprite is not None:
            return sprite
        # Debug: print if sprite not found
        print(f"[DEBUG Sprite] Failed to load: {sprite_path}")
    
    # Fall back to directional sprites for backward compatibility
    # For south, just use east sprite
    if direction == "south":
        sprite_dir = "east"
    else:
        sprite_dir = direction
    
    sprite_path = f"colonists/{colonist_id}_{sprite_dir}.png"
    sprite = get_scaled_sprite(sprite_path, tile_size)
    
    # If not found in subfolder, try root assets folder
    if sprite is None:
        sprite_path = f"{colonist_id}_{sprite_dir}.png"
        sprite = get_scaled_sprite(sprite_path, tile_size)
    
    return sprite


# ============================================================================
# ITEM/OBJECT SPRITES
# ============================================================================

def get_item_sprite(item_id: str, tile_size: int) -> Optional[pygame.Surface]:
    """Get sprite for an item/object.
    
    Args:
        item_id: Item identifier (e.g., "scrap_guitar", "wire")
        tile_size: Target size in pixels
        
    Returns:
        Scaled sprite or None
    """
    sprite_path = f"items/{item_id}.png"
    return get_scaled_sprite(sprite_path, tile_size)


def get_building_sprite(building_type: str, tile_size: int) -> Optional[pygame.Surface]:
    """Get sprite for a building/workstation.
    
    Args:
        building_type: Building type (e.g., "spark_bench", "generator")
        tile_size: Target size in pixels
        
    Returns:
        Scaled sprite or None
    """
    sprite_path = f"buildings/{building_type}.png"
    return get_scaled_sprite(sprite_path, tile_size)


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def preload_sprites(sprite_list: List[str]):
    """Preload a list of sprites into cache.
    
    Args:
        sprite_list: List of sprite paths to preload
    """
    for sprite_path in sprite_list:
        load_sprite(sprite_path)


def get_sprite_info() -> Dict[str, int]:
    """Get info about loaded sprites.
    
    Returns:
        Dict with cache statistics
    """
    return {
        "loaded_sprites": len(_SPRITE_CACHE),
        "scaled_sprites": len(_SCALED_CACHE),
        "zoom_level": _current_zoom,
    }


# ============================================================================
# SPRITE NAMING CONVENTIONS
# ============================================================================

"""
Expected folder structure:

assets/
  tiles/
    finished_floor_0.png, finished_floor_1.png, ... (variations)
    finished_wall_0.png, finished_wall_1.png, ...
    finished_door.png
    scrap_guitar_placed.png
    drum_kit_placed.png
    synth_placed.png
    ...
  
  colonists/
    default_north.png    (facing away/up)
    default_east.png     (facing right)
    default_west.png     (facing left)
    default_south.png    (facing toward camera - optional, uses east/west)
    
    # Additional colonist variations
    worker_north.png
    worker_east.png
    worker_west.png
    ...
  
  buildings/
    spark_bench.png
    tinker_station.png
    generator.png
    gutter_forge.png
    ...
  
  items/
    wire.png
    chip.png
    scrap_guitar.png
    drum_kit.png
    ...
  
  ui/
    icons/
      ...

Naming conventions:
- Tiles: {tile_type}_{variation}.png or {tile_type}.png
- Colonists: {colonist_id}_{direction}.png
- Buildings: {building_type}.png
- Items: {item_id}.png
"""
