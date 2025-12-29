"""
Arcade-based grid rendering for Fractured City.

This module handles converting the Grid's tile data into Arcade sprites
for GPU-accelerated rendering.
"""

import arcade
from config import TILE_SIZE
from grid import Grid
from autotiling import get_autotile_variant, get_connection_set, should_autotile
from tileset_loader import get_tile_texture as get_tileset_texture


class GridRenderer:
    """Handles rendering Grid tiles using Arcade sprites."""
    
    def __init__(self, grid: Grid):
        self.grid = grid
        
        # Sprite list for all tiles (GPU batching)
        self.tile_sprite_list = arcade.SpriteList(use_spatial_hash=True)
        
        # Texture cache to avoid reloading same sprites
        self.texture_cache = {}
        
        # Track which tiles have been rendered
        self.rendered_tiles = set()
        
    def get_tile_texture(self, tile_type: str, x: int, y: int, z: int):
        """Get or load texture for a tile type.
        
        For construction tiles (wall, floor, door, etc.), uses finished_ sprite.
        For autotiled tiles (roads, walls), calculates variant based on neighbors.
        Tries variations in order: 0-8, 0-7, 0-6, 0-4, 0-3, 0-2, 0-1, then base sprite.
        """
        # Debug: Log first street tile
        if tile_type == "street" and not hasattr(self, '_street_logged'):
            self._street_logged = True
            print(f"[GridRenderer] Processing street tile at ({x}, {y}), should_autotile={should_autotile(tile_type)}")
        
        # Check if this tile type should use autotiling
        if should_autotile(tile_type):
            variant = get_autotile_variant(
                self.grid, x, y, z, tile_type, 
                connect_to=get_connection_set(tile_type)
            )
            
            # Try to get autotiled texture from tileset
            autotile_name = f"{tile_type}_autotile_{variant}"
            tileset_texture = get_tileset_texture("city_roads", autotile_name)
            if tileset_texture:
                return tileset_texture
            
            # Fallback: try numbered variation with autotile variant
            # If tile_type already ends with _autotile, don't add it again
            if tile_type.endswith("_autotile"):
                # Check if this is a dirt overlay (uses subfolder)
                if "dirt_overlay" in tile_type:
                    sprite_path = f"assets/tiles/dirt/{tile_type}_{variant}.png"
                else:
                    sprite_path = f"assets/tiles/{tile_type}_{variant}.png"
            else:
                sprite_path = f"assets/tiles/{tile_type}_autotile_{variant}.png"
            try:
                texture = arcade.load_texture(sprite_path)
                cache_key = (tile_type, x, y, z, "autotile", variant)
                self.texture_cache[cache_key] = texture
                
                # Debug: Log first dirt overlay autotile load
                if "dirt_overlay" in tile_type and not hasattr(self, '_dirt_variant_logged'):
                    self._dirt_variant_logged = True
                    print(f"[GridRenderer] Loading dirt overlay variant {variant}: {sprite_path}")
                
                return texture
            except Exception as e:
                # Debug: print first few failures to see what's wrong
                if not hasattr(self, '_autotile_error_logged'):
                    self._autotile_error_logged = True
                    print(f"[GridRenderer] Autotile sprite not found: {sprite_path}, error: {e}")
                pass  # Fall through to regular variation system
        # Special handling for resource nodes - need to look up resource type
        if tile_type == "resource_node":
            import resources
            node = resources.get_node_at(x, y)
            if node:
                resource_type = node.get("resource", "")
                # Map resource type to sprite name
                if resource_type == "wood":
                    tile_type = "wood_node"
                elif resource_type == "scrap":
                    tile_type = "scrap_node"
                elif resource_type == "mineral":
                    tile_type = "mineral_node"
                elif resource_type == "raw_food":
                    tile_type = "raw_food_node"
                elif resource_type == "metal":
                    tile_type = "scrap_node"  # Use scrap sprite as fallback
                else:
                    return None  # Unknown resource type
            else:
                return None  # No node data
        
        # Special handling for salvage objects
        if tile_type == "salvage_object":
            tile_type = "scrap_node"  # Use scrap_node sprites
        
        # Map construction tiles to finished_ versions
        # During construction: tile_type is "wall" -> maps to "finished_wall" (darkened)
        # After construction: tile_type is "finished_wall" -> stays "finished_wall" (normal)
        construction_to_finished = {
            # Structures
            "wall": "finished_wall",
            "wall_advanced": "finished_wall",
            "floor": "finished_floor",
            "door": "finished_door",
            "bar_door": "finished_bar_door",
            "window": "finished_window",
            "bridge": "finished_bridge",
            "fire_escape": "finished_fire_escape",
            "stage": "finished_stage",
            "stage_stairs": "finished_stage_stairs",
            "building": "finished_building",
            # Workstations - ALL use finished_ sprites
            "gutter_still": "finished_gutter_still",
            "spark_bench": "finished_spark_bench",
            "tinker_station": "finished_tinker_station",
            "salvagers_bench": "finished_salvagers_bench",
            "generator": "finished_generator",
            "stove": "finished_stove",
            "gutter_forge": "finished_gutter_forge",
            "skinshop_loom": "finished_skinshop_loom",
            "cortex_spindle": "finished_cortex_spindle",
            "barracks": "finished_barracks",
            # Furniture
            "scrap_bar_counter": "finished_scrap_bar_counter",
            "crash_bed": "finished_crash_bed",
            "comfort_chair": "finished_comfort_chair",
            "bar_stool": "finished_bar_stool",
            "storage_locker": "finished_storage_locker",
            "dining_table": "finished_dining_table",
            "wall_lamp": "finished_wall_lamp",
            "workshop_table": "finished_workshop_table",
            "tool_rack": "finished_tool_rack",
            "weapon_rack": "finished_weapon_rack",
            "gutter_slab": "finished_gutter_slab",
        }
        
        # Map construction tiles to finished versions (for darkening during construction)
        if tile_type in construction_to_finished:
            tile_type = construction_to_finished[tile_type]
        
        # Finished tiles stay as-is (already have finished_ prefix from grid.set_tile)
        
        # Calculate variation index for ground tiles (deterministic but varied)
        # Ground tiles use position-based variation to break up grid look
        variation_index = (x * 7 + y * 13 + z * 3) % 8  # 0-7 range
        
        cache_key = (tile_type, variation_index)
        if cache_key in self.texture_cache:
            return self.texture_cache[cache_key]
        
        # For workstations, try workstations folder first (no variations)
        workstation_types = [
            "finished_stove", "finished_generator", "finished_gutter_forge",
            "finished_salvagers_bench", "finished_spark_bench", "finished_tinker_station",
            "finished_gutter_still", "finished_skinshop_loom", "finished_cortex_spindle",
            "finished_barracks"
        ]
        
        if tile_type in workstation_types:
            sprite_path = f"assets/workstations/{tile_type}.png"
            try:
                texture = arcade.load_texture(sprite_path)
                self.texture_cache[cache_key] = texture
                return texture
            except:
                pass  # Fall through to tiles folder
        
        # Try variations in descending order (matches Pygame sprites.py logic)
        max_variation_counts = [9, 8, 6, 4, 3, 2, 1] if tile_type == "finished_bridge" else [8, 6, 4, 3, 2, 1]
        
        for max_variations in max_variation_counts:
            variation = variation_index % max_variations
            sprite_path = f"assets/tiles/{tile_type}_{variation}.png"
            
            try:
                texture = arcade.load_texture(sprite_path)
                self.texture_cache[cache_key] = texture
                return texture
            except:
                continue
        
        # Fall back to base sprite (no variation number)
        sprite_path = f"assets/tiles/{tile_type}.png"
        try:
            texture = arcade.load_texture(sprite_path)
            self.texture_cache[cache_key] = texture
            return texture
        except:
            pass
        
        # No sprite available
        return None
    
    def _get_furniture_texture(self, furniture_type: str):
        """Get texture for furniture from assets/furniture/ folder."""
        cache_key = (furniture_type, 0)  # No variations for furniture
        if cache_key in self.texture_cache:
            return self.texture_cache[cache_key]
        
        sprite_path = f"assets/furniture/{furniture_type}.png"
        try:
            texture = arcade.load_texture(sprite_path)
            self.texture_cache[cache_key] = texture
            return texture
        except:
            return None
    
    def build_tile_sprites(self, z_level: int = 0):
        """Build sprite list for current Z-level and Z-1 (for depth effect).
        
        Only renders non-empty tiles for performance.
        Z-1 level is rendered with reduced opacity for depth illusion.
        """
        self.tile_sprite_list.clear()
        self.rendered_tiles.clear()
        
        print(f"[GridRenderer] Building sprites for z={z_level}...")
        
        tiles_processed = 0
        
        # First, render Z-1 level at reduced opacity (if not on ground level)
        if z_level > 0:
            for y in range(self.grid.height):
                for x in range(self.grid.width):
                    tile_type = self.grid.get_tile(x, y, z_level - 1)
                    
                    # Only render non-empty tiles
                    if tile_type and tile_type != "empty":
                        self._add_tile_sprite(x, y, z_level - 1, tile_type, opacity=128)
                        tiles_processed += 1
        
        # Then render current Z-level at full opacity
        # LAYERED SYSTEM: Render ALL tiles (concrete base everywhere)
        for y in range(self.grid.height):
            for x in range(self.grid.width):
                tile_type = self.grid.get_tile(x, y, z_level)
                
                # Render all tiles (concrete base + overlay if not empty)
                if tile_type:
                    self._add_tile_sprite(x, y, z_level, tile_type, opacity=255)
                    tiles_processed += 1
                
                # Render overlay tiles on top (dirt, grass, rubble)
                overlay_type = self.grid.get_overlay_tile(x, y, z_level)
                if overlay_type:
                    self._add_overlay_sprite(x, y, z_level, overlay_type, opacity=255)
                    tiles_processed += 1
        
        print(f"[GridRenderer] Built {len(self.tile_sprite_list)} tile sprites ({tiles_processed} non-empty tiles)")
    
    def _add_tile_sprite(self, x: int, y: int, z: int, tile_type: str, opacity: int = 255):
        """Add tile sprite(s) with layered rendering system.
        
        LAYER 1: Base concrete (always rendered)
        LAYER 2: Material overlay (transparent PNG on top)
        
        Args:
            x, y, z: Tile coordinates
            tile_type: Type of tile to render
            opacity: Alpha value (0-255), used for Z-1 depth effect
        """
        screen_x = x * TILE_SIZE
        screen_y = y * TILE_SIZE
        
        # Special handling for furniture tiles (floor + furniture)
        furniture_tiles = [
            "crash_bed", "comfort_chair", "bar_stool",
            "scrap_guitar_placed", "drum_kit_placed", "synth_placed",
            "harmonica_placed", "amp_placed"
        ]
        
        if tile_type in furniture_tiles:
            # Draw floor first
            floor_texture = self.get_tile_texture("finished_floor", x, y, z)
            if floor_texture:
                floor_sprite = arcade.Sprite()
                floor_sprite.texture = floor_texture
                floor_sprite.center_x = screen_x + TILE_SIZE // 2
                floor_sprite.center_y = screen_y + TILE_SIZE // 2
                floor_sprite.alpha = opacity
                self.tile_sprite_list.append(floor_sprite)
            
            # Draw furniture on top
            furniture_texture = self._get_furniture_texture(tile_type)
            if furniture_texture:
                furniture_sprite = arcade.Sprite()
                furniture_sprite.texture = furniture_texture
                furniture_sprite.center_x = screen_x + TILE_SIZE // 2
                furniture_sprite.center_y = screen_y + TILE_SIZE // 2
                furniture_sprite.alpha = opacity
                self.tile_sprite_list.append(furniture_sprite)
            
            self.rendered_tiles.add((x, y, z))
            return
        
        # LAYERED RENDERING SYSTEM
        # LAYER 1: Base concrete (ALWAYS render for ALL tiles)
        base_texture = self.get_tile_texture("ground_concrete_0", x, y, z)
        if base_texture:
            base_sprite = arcade.Sprite()
            base_sprite.texture = base_texture
            base_sprite.center_x = screen_x + TILE_SIZE // 2
            base_sprite.center_y = screen_y + TILE_SIZE // 2
            base_sprite.alpha = opacity
            self.tile_sprite_list.append(base_sprite)
        
        # LAYER 2: Material overlay system
        # Only approved materials render as overlays on concrete base
        allowed_overlays = [
            "street", "road",  # Roads (autotiled)
            "ground_dirt_overlay",  # Dirt (autotiled transparent overlay)
            "finished_wall", "finished_floor", "finished_door", "finished_window",  # Buildings
            "finished_bridge", "finished_fire_escape",  # Structures
        ]
        
        # Check if this tile type should render as overlay
        should_render_overlay = False
        for allowed in allowed_overlays:
            if tile_type.startswith(allowed):
                should_render_overlay = True
                break
        
        if should_render_overlay:
            overlay_texture = self.get_tile_texture(tile_type, x, y, z)
            if overlay_texture:
                overlay_sprite = arcade.Sprite()
                overlay_sprite.texture = overlay_texture
                overlay_sprite.center_x = screen_x + TILE_SIZE // 2
                overlay_sprite.center_y = screen_y + TILE_SIZE // 2
                overlay_sprite.alpha = opacity
                self.tile_sprite_list.append(overlay_sprite)
        
        self.rendered_tiles.add((x, y, z))
    
    def _is_construction_tile(self, tile_type: str) -> bool:
        """Check if tile type is under construction (not finished)."""
        construction_types = {
            "wall", "wall_advanced", "floor", "door", "window", "bridge",
            "fire_escape", "building", "salvagers_bench", "generator",
            "stove", "gutter_forge", "skinshop_loom", "cortex_spindle",
            "barracks", "scrap_bar_counter", "crash_bed", "gutter_slab"
        }
        return tile_type in construction_types
    
    def _add_overlay_sprite(self, x: int, y: int, z: int, overlay_type: str, opacity: int = 255):
        """Add overlay sprite (dirt, grass, rubble) on top of base tile.
        
        Overlays are transparent PNGs that render on top of concrete/street base.
        Uses autotiling to create smooth blob shapes.
        """
        screen_x = x * TILE_SIZE
        screen_y = y * TILE_SIZE
        
        # Get autotiled texture for overlay
        texture = self.get_tile_texture(overlay_type, x, y, z)
        if texture:
            sprite = arcade.Sprite()
            sprite.texture = texture
            sprite.center_x = screen_x + TILE_SIZE // 2
            sprite.center_y = screen_y + TILE_SIZE // 2
            sprite.alpha = opacity
            self.tile_sprite_list.append(sprite)
    
    def update_tile(self, x: int, y: int, z: int):
        """Update a single tile when it changes.
        
        Removes old sprite for this tile and adds new one.
        Much faster than rebuilding entire sprite list.
        """
        # Remove old sprite for this tile if it exists
        if (x, y, z) in self.rendered_tiles:
            # Find and remove the sprite at this position
            for sprite in self.tile_sprite_list:
                if (sprite.center_x == x * TILE_SIZE + TILE_SIZE // 2 and 
                    sprite.center_y == y * TILE_SIZE + TILE_SIZE // 2):
                    sprite.remove_from_sprite_lists()
                    break
            self.rendered_tiles.discard((x, y, z))
        
        # Add new sprite for current tile type
        tile_type = self.grid.get_tile(x, y, z)
        if tile_type:
            self._add_tile_sprite(x, y, z, tile_type)
    
    def draw(self):
        """Draw all tile sprites."""
        self.tile_sprite_list.draw()
