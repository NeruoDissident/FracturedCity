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
        
        # Cached sprite lists for each Z-level (for performance)
        # Key: z_level, Value: SpriteList
        self.z_level_cache = {}
        
        # Current Z-level being viewed
        self.current_z = 0
        
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
        # Map construction tiles to finished_ versions FIRST (before autotiling check)
        # During construction: tile_type is "wall" -> maps to "finished_wall_autotile" (will be darkened)
        # After construction: tile_type is "finished_wall_autotile" -> stays "finished_wall_autotile" (normal)
        construction_to_finished = {
            # Structures
            "wall": "finished_wall_autotile",
            "wall_advanced": "finished_wall_autotile",
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
            
            # Debug: Log wall autotiling
            if "wall" in tile_type and not hasattr(self, '_wall_autotile_logged'):
                self._wall_autotile_logged = True
                print(f"[GridRenderer] Wall autotiling: tile_type={tile_type}, variant={variant}")
                print(f"[GridRenderer] should_autotile={should_autotile(tile_type)}")
            
            # Try to get autotiled texture from tileset
            autotile_name = f"{tile_type}_autotile_{variant}"
            tileset_texture = get_tileset_texture("city_roads", autotile_name)
            if tileset_texture:
                return tileset_texture
            
            # Fallback: try numbered variation with autotile variant
            # If tile_type already ends with _autotile, don't add it again
            if tile_type.endswith("_autotile"):
                # Check subfolder based on tile type
                if "dirt_overlay" in tile_type:
                    sprite_path = f"assets/tiles/dirt/{tile_type}_{variant}.png"
                elif "wall" in tile_type:
                    sprite_path = f"assets/tiles/walls/{tile_type}_{variant}.png"
                else:
                    sprite_path = f"assets/tiles/{tile_type}_{variant}.png"
            else:
                # Check if this is a road/street tile (uses roads subfolder)
                if "street" in tile_type or "road" in tile_type:
                    sprite_path = f"assets/tiles/roads/{tile_type}_autotile_{variant}.png"
                elif "wall" in tile_type:
                    sprite_path = f"assets/tiles/walls/{tile_type}_autotile_{variant}.png"
                else:
                    sprite_path = f"assets/tiles/{tile_type}_autotile_{variant}.png"
            
            # Debug: Log wall sprite path
            if "wall" in tile_type and not hasattr(self, '_wall_sprite_path_logged'):
                self._wall_sprite_path_logged = True
                print(f"[GridRenderer] Wall sprite path: {sprite_path}")
            
            try:
                texture = arcade.load_texture(sprite_path)
                # Cache by variant only, not by position - allows recalculation
                cache_key = (tile_type, variant)
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
        
        # Determine subfolder based on tile type
        if "wall" in tile_type:
            subfolder = "walls/"
        else:
            subfolder = ""
        
        for max_variations in max_variation_counts:
            variation = variation_index % max_variations
            sprite_path = f"assets/tiles/{subfolder}{tile_type}_{variation}.png"
            
            try:
                texture = arcade.load_texture(sprite_path)
                self.texture_cache[cache_key] = texture
                return texture
            except:
                continue
        
        # Fall back to base sprite (no variation number)
        sprite_path = f"assets/tiles/{subfolder}{tile_type}.png"
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
    
    def build_tile_sprites(self, z_level: int = 0, force_rebuild: bool = False):
        """Build sprite list for current Z-level with cached lower level.
        
        Z0: Renders all tiles normally
        Z1+: Only renders walkable/buildable tiles (roof_access, roof_floor, fire_escape, etc.)
        Z-1 level is cached and reused for performance.
        
        Args:
            z_level: Z-level to render
            force_rebuild: If True, rebuild cache even if it exists
        """
        self.tile_sprite_list.clear()
        self.rendered_tiles.clear()
        self.current_z = z_level
        
        print(f"[GridRenderer] Building sprites for z={z_level}...")
        
        tiles_processed = 0
        
        # First, render Z-1 level at reduced opacity (if not on ground level)
        # Use cached sprite list if available for performance
        if z_level > 0:
            lower_z = z_level - 1
            
            # Build or retrieve cached sprite list for lower Z-level
            if lower_z not in self.z_level_cache or force_rebuild:
                print(f"[GridRenderer] Building cache for Z={lower_z}...")
                self._build_z_level_cache(lower_z)
            
            # Add cached lower level sprites with reduced opacity
            cached_sprites = self.z_level_cache.get(lower_z)
            if cached_sprites:
                for sprite in cached_sprites:
                    # Create a copy with reduced opacity for depth effect
                    depth_sprite = arcade.Sprite()
                    depth_sprite.texture = sprite.texture
                    depth_sprite.center_x = sprite.center_x
                    depth_sprite.center_y = sprite.center_y
                    depth_sprite.alpha = 128  # 50% opacity for depth
                    depth_sprite.color = (180, 180, 180)  # Slight gray tint
                    self.tile_sprite_list.append(depth_sprite)
                    tiles_processed += 1
        
        # Then render current Z-level at full opacity
        # Z1+: Only render walkable/buildable rooftop tiles
        walkable_roof_tiles = {
            "roof_access", "roof_floor", "fire_escape", "finished_fire_escape",
            "fire_escape_platform", "window_tile", "roof", "bridge", "finished_bridge"
        }
        
        # LAYERED SYSTEM: Render in proper order for alpha blending
        # Pass 1: Concrete base layer (only for Z0 or walkable tiles on Z1+)
        for y in range(self.grid.height):
            for x in range(self.grid.width):
                tile_type = self.grid.get_tile(x, y, z_level)
                if tile_type:
                    # Z1+: Only render walkable tiles
                    if z_level > 0 and tile_type not in walkable_roof_tiles:
                        continue
                    self._add_concrete_base(x, y, z_level, opacity=255)
                    tiles_processed += 1
        
        # Pass 2: Dirt/grass/rubble overlays (render BEFORE roads) - Z0 only
        if z_level == 0:
            for y in range(self.grid.height):
                for x in range(self.grid.width):
                    overlay_type = self.grid.get_overlay_tile(x, y, z_level)
                    if overlay_type:
                        self._add_overlay_sprite(x, y, z_level, overlay_type, opacity=255)
                        tiles_processed += 1
        
        # Pass 3: Roads/streets (render AFTER dirt, BEFORE structures) - Z0 only
        if z_level == 0:
            for y in range(self.grid.height):
                for x in range(self.grid.width):
                    tile_type = self.grid.get_tile(x, y, z_level)
                    if tile_type and ("street" in tile_type or "road" in tile_type):
                        self._add_road_sprite(x, y, z_level, tile_type, opacity=255)
                        tiles_processed += 1
        
        # Pass 4: Floors (render BEFORE walls so walls are always on top)
        for y in range(self.grid.height):
            for x in range(self.grid.width):
                tile_type = self.grid.get_tile(x, y, z_level)
                if tile_type and ("floor" in tile_type):
                    # Z1+: Only render if walkable
                    if z_level > 0 and tile_type not in walkable_roof_tiles:
                        continue
                    self._add_structure_sprite(x, y, z_level, tile_type, opacity=255)
                    tiles_processed += 1
        
        # Pass 5: Walls and other structures (render AFTER floors)
        for y in range(self.grid.height):
            for x in range(self.grid.width):
                tile_type = self.grid.get_tile(x, y, z_level)
                # Skip ground tiles, roads, and floors - they're handled in earlier passes
                if tile_type and not ("street" in tile_type or "road" in tile_type or "ground_" in tile_type or "floor" in tile_type):
                    # Z1+: Only render if walkable
                    if z_level > 0 and tile_type not in walkable_roof_tiles:
                        continue
                    self._add_structure_sprite(x, y, z_level, tile_type, opacity=255)
                    tiles_processed += 1
        
        print(f"[GridRenderer] Built {len(self.tile_sprite_list)} tile sprites ({tiles_processed} non-empty tiles)")
    
    def _build_z_level_cache(self, z_level: int):
        """Build and cache sprite list for a specific Z-level.
        
        This creates a static snapshot of the Z-level that can be reused
        when viewing upper levels, avoiding expensive re-rendering.
        """
        cache_list = arcade.SpriteList(use_spatial_hash=True)
        
        # Determine if this is ground level or rooftop
        walkable_roof_tiles = {
            "roof_access", "roof_floor", "fire_escape", "finished_fire_escape",
            "fire_escape_platform", "window_tile", "roof", "bridge", "finished_bridge"
        }
        
        # Helper to add sprite to cache
        def add_to_cache(x, y, z, tile_type, opacity=255):
            texture = self.get_tile_texture(tile_type, x, y, z)
            if texture:
                sprite = arcade.Sprite()
                sprite.texture = texture
                sprite.center_x = x * TILE_SIZE + TILE_SIZE // 2
                sprite.center_y = y * TILE_SIZE + TILE_SIZE // 2
                sprite.alpha = opacity
                cache_list.append(sprite)
        
        # Pass 1: Concrete base
        for y in range(self.grid.height):
            for x in range(self.grid.width):
                tile_type = self.grid.get_tile(x, y, z_level)
                if tile_type:
                    if z_level > 0 and tile_type not in walkable_roof_tiles:
                        continue
                    add_to_cache(x, y, z_level, "ground_concrete")
        
        # Pass 2: Overlays (Z0 only)
        if z_level == 0:
            for y in range(self.grid.height):
                for x in range(self.grid.width):
                    overlay_type = self.grid.get_overlay_tile(x, y, z_level)
                    if overlay_type:
                        add_to_cache(x, y, z_level, overlay_type)
        
        # Pass 3: Roads (Z0 only)
        if z_level == 0:
            for y in range(self.grid.height):
                for x in range(self.grid.width):
                    tile_type = self.grid.get_tile(x, y, z_level)
                    if tile_type and ("street" in tile_type or "road" in tile_type):
                        add_to_cache(x, y, z_level, tile_type)
        
        # Pass 4: Floors
        for y in range(self.grid.height):
            for x in range(self.grid.width):
                tile_type = self.grid.get_tile(x, y, z_level)
                if tile_type and ("floor" in tile_type):
                    if z_level > 0 and tile_type not in walkable_roof_tiles:
                        continue
                    add_to_cache(x, y, z_level, tile_type)
        
        # Pass 5: Walls and structures
        for y in range(self.grid.height):
            for x in range(self.grid.width):
                tile_type = self.grid.get_tile(x, y, z_level)
                if tile_type and not ("street" in tile_type or "road" in tile_type or "ground_" in tile_type or "floor" in tile_type):
                    if z_level > 0 and tile_type not in walkable_roof_tiles:
                        continue
                    add_to_cache(x, y, z_level, tile_type)
        
        self.z_level_cache[z_level] = cache_list
        print(f"[GridRenderer] Cached {len(cache_list)} sprites for Z={z_level}")
    
    def invalidate_cache(self, z_level: int = None):
        """Invalidate cached sprite list(s) when tiles change.
        
        Args:
            z_level: Specific Z-level to invalidate, or None to clear all caches
        """
        if z_level is not None:
            if z_level in self.z_level_cache:
                del self.z_level_cache[z_level]
                print(f"[GridRenderer] Invalidated cache for Z={z_level}")
        else:
            self.z_level_cache.clear()
            print(f"[GridRenderer] Cleared all Z-level caches")
    
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
    
    def _add_concrete_base(self, x: int, y: int, z: int, opacity: int = 255):
        """Add concrete base layer (always rendered first)."""
        screen_x = x * TILE_SIZE
        screen_y = y * TILE_SIZE
        
        base_texture = self.get_tile_texture("ground_concrete_0", x, y, z)
        if base_texture:
            base_sprite = arcade.Sprite()
            base_sprite.texture = base_texture
            base_sprite.center_x = screen_x + TILE_SIZE // 2
            base_sprite.center_y = screen_y + TILE_SIZE // 2
            base_sprite.alpha = opacity
            self.tile_sprite_list.append(base_sprite)
        
        self.rendered_tiles.add((x, y, z))
    
    def _add_road_sprite(self, x: int, y: int, z: int, tile_type: str, opacity: int = 255):
        """Add road/street sprite with autotiling (rendered after dirt, before structures)."""
        screen_x = x * TILE_SIZE
        screen_y = y * TILE_SIZE
        
        # Get autotiled road texture
        texture = self.get_tile_texture(tile_type, x, y, z)
        if texture:
            sprite = arcade.Sprite()
            sprite.texture = texture
            sprite.center_x = screen_x + TILE_SIZE // 2
            sprite.center_y = screen_y + TILE_SIZE // 2
            sprite.alpha = opacity
            self.tile_sprite_list.append(sprite)
    
    def _add_structure_sprite(self, x: int, y: int, z: int, tile_type: str, opacity: int = 255):
        """Add structure sprite (walls, floors, buildings) - rendered last.
        
        Handles construction darkening: tiles under construction use same sprite but darkened.
        """
        screen_x = x * TILE_SIZE
        screen_y = y * TILE_SIZE
        
        # Check if this is under construction (not finished yet)
        is_construction = self._is_construction_tile(tile_type)
        
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
            return
        
        # Render structure texture
        texture = self.get_tile_texture(tile_type, x, y, z)
        if texture:
            sprite = arcade.Sprite()
            sprite.texture = texture
            sprite.center_x = screen_x + TILE_SIZE // 2
            sprite.center_y = screen_y + TILE_SIZE // 2
            sprite.alpha = opacity
            
            # CONSTRUCTION DARKENING: Under construction tiles use same sprite but darkened
            if is_construction:
                # Darken by reducing color values (0.6 = 60% brightness)
                sprite.color = (153, 153, 153)  # RGB(153,153,153) = 60% of 255
            
            self.tile_sprite_list.append(sprite)
    
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
        
        Uses smart batching to avoid rebuilding entire sprite list on every change.
        Marks tiles as dirty and rebuilds in batches.
        Invalidates Z-level cache when tiles change.
        """
        # Invalidate cache for this Z-level since tiles changed
        self.invalidate_cache(z)
        
        # Mark this tile as needing update
        if not hasattr(self, '_dirty_tiles'):
            self._dirty_tiles = set()
        self._dirty_tiles.add((x, y, z))
        
        # If we have many dirty tiles, batch rebuild
        # Otherwise, do single tile update for performance
        if len(self._dirty_tiles) > 100:
            self.build_tile_sprites(self.current_z)
            self._dirty_tiles.clear()
        else:
            # Single tile update - remove old sprites at this position
            sprites_to_remove = []
            for sprite in self.tile_sprite_list:
                sprite_x = int((sprite.center_x - TILE_SIZE // 2) / TILE_SIZE)
                sprite_y = int((sprite.center_y - TILE_SIZE // 2) / TILE_SIZE)
                if sprite_x == x and sprite_y == y:
                    sprites_to_remove.append(sprite)
            
            for sprite in sprites_to_remove:
                sprite.remove_from_sprite_lists()
            
            # Add new sprites for this tile using layered system
            tile_type = self.grid.get_tile(x, y, z)
            
            # Layer 1: Concrete base
            if tile_type:
                self._add_concrete_base(x, y, z)
            
            # Layer 2: Dirt overlay (if exists)
            overlay_type = self.grid.get_overlay_tile(x, y, z)
            if overlay_type:
                self._add_overlay_sprite(x, y, z, overlay_type)
            
            # Layer 3: Roads (if applicable)
            if tile_type and ("street" in tile_type or "road" in tile_type):
                self._add_road_sprite(x, y, z, tile_type)
            
            # Layer 4: Structures (if applicable)
            if tile_type and not ("street" in tile_type or "road" in tile_type or "ground_" in tile_type):
                self._add_structure_sprite(x, y, z, tile_type)
    
    def draw(self):
        """Draw all tile sprites."""
        self.tile_sprite_list.draw()
