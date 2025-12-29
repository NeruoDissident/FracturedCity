"""Sprite sheet loader for tilesets.

Loads tiles from sprite sheets and provides texture lookup by name.
Supports both individual tile extraction and efficient sprite sheet atlases.
"""

import arcade
from typing import Dict, Tuple, Optional
from pathlib import Path


class TilesetAtlas:
    """Manages a collection of tiles loaded from a sprite sheet."""
    
    def __init__(self, sheet_path: str, tile_size: int = 64):
        """Initialize tileset atlas.
        
        Args:
            sheet_path: Path to sprite sheet image
            tile_size: Size of each tile in pixels (assumes square tiles)
        """
        self.sheet_path = sheet_path
        self.tile_size = tile_size
        self.textures: Dict[str, arcade.Texture] = {}
        self._sheet_texture: Optional[arcade.Texture] = None
        
        # Load the sprite sheet
        if Path(sheet_path).exists():
            self._sheet_texture = arcade.load_texture(sheet_path)
        else:
            print(f"[TilesetLoader] WARNING: Sprite sheet not found: {sheet_path}")
    
    def add_tile(self, name: str, x: int, y: int, width: Optional[int] = None, height: Optional[int] = None):
        """Add a tile definition from the sprite sheet.
        
        Args:
            name: Unique name for this tile
            x: X coordinate in sprite sheet (pixels)
            y: Y coordinate in sprite sheet (pixels)
            width: Width of tile (defaults to tile_size)
            height: Height of tile (defaults to tile_size)
        """
        if self._sheet_texture is None:
            return
        
        w = width or self.tile_size
        h = height or self.tile_size
        
        try:
            texture = arcade.load_texture(
                self.sheet_path,
                x=x, y=y,
                width=w, height=h
            )
            self.textures[name] = texture
        except Exception as e:
            print(f"[TilesetLoader] ERROR loading tile '{name}' at ({x}, {y}): {e}")
    
    def add_tile_grid(self, base_name: str, start_x: int, start_y: int, 
                      cols: int, rows: int, spacing: int = 0):
        """Add a grid of tiles with automatic naming.
        
        Args:
            base_name: Base name for tiles (will append _0, _1, etc.)
            start_x: Starting X coordinate in sprite sheet
            start_y: Starting Y coordinate in sprite sheet
            cols: Number of columns
            rows: Number of rows
            spacing: Spacing between tiles in pixels
        """
        index = 0
        for row in range(rows):
            for col in range(cols):
                x = start_x + col * (self.tile_size + spacing)
                y = start_y + row * (self.tile_size + spacing)
                tile_name = f"{base_name}_{index}"
                self.add_tile(tile_name, x, y)
                index += 1
    
    def get_texture(self, name: str) -> Optional[arcade.Texture]:
        """Get a texture by name.
        
        Args:
            name: Tile name
        
        Returns:
            Texture if found, None otherwise
        """
        return self.textures.get(name)
    
    def has_texture(self, name: str) -> bool:
        """Check if a texture exists.
        
        Args:
            name: Tile name
        
        Returns:
            True if texture exists
        """
        return name in self.textures


# Global tileset registry
_TILESETS: Dict[str, TilesetAtlas] = {}


def register_tileset(name: str, atlas: TilesetAtlas):
    """Register a tileset atlas globally.
    
    Args:
        name: Unique name for this tileset
        atlas: TilesetAtlas instance
    """
    _TILESETS[name] = atlas


def get_tileset(name: str) -> Optional[TilesetAtlas]:
    """Get a registered tileset by name.
    
    Args:
        name: Tileset name
    
    Returns:
        TilesetAtlas if found, None otherwise
    """
    return _TILESETS.get(name)


def get_tile_texture(tileset_name: str, tile_name: str) -> Optional[arcade.Texture]:
    """Get a tile texture from a registered tileset.
    
    Args:
        tileset_name: Name of the tileset
        tile_name: Name of the tile within the tileset
    
    Returns:
        Texture if found, None otherwise
    """
    tileset = get_tileset(tileset_name)
    if tileset:
        return tileset.get_texture(tile_name)
    return None


def load_city_tileset_64x64() -> TilesetAtlas:
    """Load the 64x64 city tileset from topdown_itch.png.
    
    This is a helper function to load the road tileset with proper tile definitions.
    Call this during game initialization.
    
    Returns:
        TilesetAtlas with road tiles loaded
    """
    atlas = TilesetAtlas("assets/topdown_itch.png", tile_size=64)
    
    # TODO: Map actual tile coordinates from sprite sheet
    # For now, this is a placeholder structure
    # Once we analyze the sprite sheet layout, we'll add proper coordinates
    
    # Example structure (coordinates need to be measured from actual sheet):
    # atlas.add_tile("road_straight_h", x=0, y=0)
    # atlas.add_tile("road_straight_v", x=64, y=0)
    # atlas.add_tile("road_corner_ne", x=128, y=0)
    # ... etc
    
    return atlas


def initialize_tilesets():
    """Initialize and register all game tilesets.
    
    Call this once during game startup after Arcade window is created.
    """
    # Load city roads tileset
    city_tileset = load_city_tileset_64x64()
    register_tileset("city_roads", city_tileset)
    
    print(f"[TilesetLoader] Initialized {len(_TILESETS)} tilesets")
    for name, tileset in _TILESETS.items():
        print(f"[TilesetLoader]   - {name}: {len(tileset.textures)} tiles")
