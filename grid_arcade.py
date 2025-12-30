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
        
        # Separate SpriteList for each Z-level (no sprite reuse between levels)
        # Each Z-level is built once and never modified
        self.z_level_sprite_lists = {
            0: arcade.SpriteList(use_spatial_hash=True),
            1: arcade.SpriteList(use_spatial_hash=True),
            2: arcade.SpriteList(use_spatial_hash=True),
        }
        
        # Track which Z-levels have been built
        self.z_levels_built = set()
        
        # Current Z-level being viewed
        self.current_z = 0
        
        # Texture cache to avoid reloading same textures (textures can be shared)
        self.texture_cache = {}
        
        # Dirty tile tracking - only rebuild tiles that changed
        self.dirty_tiles = set()  # Set of (x, y, z) tuples
        
        # Sprite position index for fast lookup: {(x, y, z): [sprite1, sprite2, ...]}
        self.sprite_index = {}
        
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
            "fire_escape": "window_tile",  # Fire escape under construction shows window_tile sprite
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
                    if not hasattr(self, '_unknown_resource_logged'):
                        self._unknown_resource_logged = True
                        print(f"[GridRenderer] Unknown resource type: {resource_type}")
                    return None  # Unknown resource type
                
                # Debug first few resource texture loads
                if not hasattr(self, '_resource_texture_count'):
                    self._resource_texture_count = 0
                if self._resource_texture_count < 3:
                    self._resource_texture_count += 1
                    print(f"[GridRenderer] Loading resource texture: {tile_type} for {resource_type} at ({x}, {y})")
            else:
                if not hasattr(self, '_no_node_data_logged'):
                    self._no_node_data_logged = True
                    print(f"[GridRenderer] No node data found for resource_node at ({x}, {y})")
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
        """Build sprite list for a Z-level.
        
        Each Z-level gets its own independent SpriteList with new sprite instances.
        Textures are shared (cached), but sprite objects are unique per level.
        
        Args:
            z_level: Z-level to render
            force_rebuild: If True, rebuild even if already built
        """
        self.current_z = z_level
        
        # Check if this Z-level already built
        if z_level in self.z_levels_built and not force_rebuild:
            print(f"[GridRenderer] Z={z_level} already built, switching to it")
            return
        
        print(f"[GridRenderer] Building Z={z_level}...")
        
        # Get the SpriteList for this Z-level
        sprite_list = self.z_level_sprite_lists.get(z_level)
        if sprite_list is None:
            print(f"[GridRenderer] Creating new SpriteList for Z={z_level}")
            sprite_list = arcade.SpriteList(use_spatial_hash=True)
            self.z_level_sprite_lists[z_level] = sprite_list
        
        # Clear existing sprites if rebuilding
        sprite_list.clear()
        
        # Build sprites for this Z-level
        self._build_z_level_sprites(z_level, sprite_list)
        
        # Mark as built
        self.z_levels_built.add(z_level)
        
        print(f"[GridRenderer] Built {len(sprite_list)} sprites for Z={z_level}")
    
    def _build_z_level_sprites(self, z_level: int, sprite_list: arcade.SpriteList):
        """Build sprites for a specific Z-level.
        
        Creates new sprite instances for each tile on this Z-level.
        Textures are shared via cache, but sprite objects are unique.
        
        Args:
            z_level: Z-level to build
            sprite_list: SpriteList to add sprites to
        """
        
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
                
                # Debug: Log first few resource sprite additions (AFTER all properties set)
                if tile_type in ["wood_node", "mineral_node", "raw_food_node", "scrap_node", "resource_node", "salvage_object"]:
                    if not hasattr(add_to_cache, '_resource_sprite_count'):
                        add_to_cache._resource_sprite_count = 0
                    if add_to_cache._resource_sprite_count < 3:
                        add_to_cache._resource_sprite_count += 1
                        print(f"[GridRenderer] ✓ Resource sprite: {tile_type} at grid({x},{y}) -> screen({sprite.center_x},{sprite.center_y}), tex:{texture.width}x{texture.height}, alpha:{sprite.alpha}")
                
                sprite_list.append(sprite)
        
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
        floor_count = 0
        floor_texture_fails = 0
        for y in range(self.grid.height):
            for x in range(self.grid.width):
                tile_type = self.grid.get_tile(x, y, z_level)
                if tile_type and ("floor" in tile_type):
                    if z_level > 0 and tile_type not in walkable_roof_tiles:
                        continue
                    # Test if texture loads
                    test_texture = self.get_tile_texture(tile_type, x, y, z_level)
                    if not test_texture:
                        floor_texture_fails += 1
                        if floor_texture_fails == 1:
                            print(f"[GridRenderer] FAILED to load floor texture for '{tile_type}' at ({x},{y})")
                    add_to_cache(x, y, z_level, tile_type)
                    floor_count += 1
        if not hasattr(self, '_floor_render_logged'):
            self._floor_render_logged = True
            print(f"[GridRenderer] Pass 4: Found {floor_count} floor tiles to render ({floor_texture_fails} texture load failures)")
        
        # Pass 5: Resource nodes and salvage objects (overlay above floors)
        if z_level == 0:
            resource_count = 0
            for y in range(self.grid.height):
                for x in range(self.grid.width):
                    tile_type = self.grid.get_tile(x, y, z_level)
                    if tile_type and (tile_type == "resource_node" or tile_type == "salvage_object"):
                        add_to_cache(x, y, z_level, tile_type)
                        resource_count += 1
            if not hasattr(self, '_resource_render_logged'):
                self._resource_render_logged = True
                print(f"[GridRenderer] Pass 5: Found {resource_count} resource tiles to render")
        
        # Pass 6: Walls and structures
        for y in range(self.grid.height):
            for x in range(self.grid.width):
                tile_type = self.grid.get_tile(x, y, z_level)
                if tile_type and not ("street" in tile_type or "road" in tile_type or "ground_" in tile_type or "floor" in tile_type or tile_type == "resource_node" or tile_type == "salvage_object"):
                    if z_level > 0 and tile_type not in walkable_roof_tiles:
                        continue
                    add_to_cache(x, y, z_level, tile_type)
        
        print(f"[GridRenderer] Cached {len(sprite_list)} sprites for Z={z_level}")
        
        # Index all sprites by position for fast lookup
        self._index_sprites(z_level, sprite_list)
    
    def _index_sprites(self, z_level: int, sprite_list: arcade.SpriteList):
        """Index sprites by tile position for fast lookup."""
        for sprite in sprite_list:
            # Calculate tile position from sprite center
            tile_x = int((sprite.center_x - TILE_SIZE // 2) / TILE_SIZE)
            tile_y = int((sprite.center_y - TILE_SIZE // 2) / TILE_SIZE)
            key = (tile_x, tile_y, z_level)
            
            if key not in self.sprite_index:
                self.sprite_index[key] = []
            self.sprite_index[key].append(sprite)
    
    def _rebuild_dirty_tiles(self):
        """Rebuild only tiles marked as dirty."""
        if not self.dirty_tiles:
            return
        
        # Initialize tracking set for multi-tile structures
        self._rendered_multitile_tiles = set()
        
        # Group dirty tiles by Z-level
        tiles_by_z = {}
        for x, y, z in self.dirty_tiles:
            if z not in tiles_by_z:
                tiles_by_z[z] = []
            tiles_by_z[z].append((x, y))
        
        # Rebuild tiles for each Z-level
        for z_level, tiles in tiles_by_z.items():
            sprite_list = self.z_level_sprite_lists.get(z_level)
            if sprite_list is None:
                continue
            
            for x, y in tiles:
                # Remove old sprites at this position
                key = (x, y, z_level)
                if key in self.sprite_index:
                    for sprite in self.sprite_index[key]:
                        try:
                            sprite_list.remove(sprite)
                        except ValueError:
                            # Sprite already removed or not in this list
                            pass
                    del self.sprite_index[key]
                
                # Add new sprites for this tile
                self._add_tile_sprites(x, y, z_level, sprite_list)
        
        # Clear dirty tiles
        self.dirty_tiles.clear()
    
    def _add_tile_sprites(self, x: int, y: int, z: int, sprite_list: arcade.SpriteList):
        """Add sprites for a single tile (all layers)."""
        tile_type = self.grid.get_tile(x, y, z)
        if not tile_type:
            return
        
        # On upper Z-levels, render all buildable tiles (walls, floors, etc.)
        # Skip only ground-level stuff like streets and resource nodes
        
        # Helper to create and add sprite
        def add_sprite(tile_type_to_render):
            texture = self.get_tile_texture(tile_type_to_render, x, y, z)
            if texture:
                sprite = arcade.Sprite()
                sprite.texture = texture
                sprite.center_x = x * TILE_SIZE + TILE_SIZE // 2
                sprite.center_y = y * TILE_SIZE + TILE_SIZE // 2
                sprite_list.append(sprite)
                
                # Index sprite by position
                key = (x, y, z)
                if key not in self.sprite_index:
                    self.sprite_index[key] = []
                self.sprite_index[key].append(sprite)
        
        # Layer 1: Concrete base (always)
        add_sprite("ground_concrete")
        
        # Layer 2: Overlay (if exists)
        if z == 0:
            overlay_type = self.grid.get_overlay_tile(x, y, z)
            if overlay_type:
                add_sprite(overlay_type)
        
        # Layer 3: Roads (if applicable)
        if z == 0 and ("street" in tile_type or "road" in tile_type):
            add_sprite(tile_type)
        
        # Layer 4: Floors
        if "floor" in tile_type:
            add_sprite(tile_type)
        
        # Layer 5: Resources
        if z == 0 and tile_type in ("resource_node", "salvage_object"):
            add_sprite(tile_type)
        
        # Layer 6: Structures (walls, buildings, etc.)
        if not ("street" in tile_type or "road" in tile_type or "ground_" in tile_type or 
                "floor" in tile_type or tile_type in ("resource_node", "salvage_object")):
            # Use _add_structure_sprite for proper multi-tile handling
            self._add_structure_sprite(x, y, z, tile_type, 255, sprite_list)
    
    def invalidate_cache(self, z_level: int = None):
        """Invalidate Z-level(s) to force rebuild when tiles change.
        
        Args:
            z_level: Specific Z-level to invalidate, or None to clear all
        """
        if z_level is not None:
            if z_level in self.z_levels_built:
                self.z_levels_built.discard(z_level)
                self.sprite_index.clear()  # Clear index when invalidating
                print(f"[GridRenderer] Invalidated Z={z_level} - will rebuild on next view")
        else:
            self.z_levels_built.clear()
            self.sprite_index.clear()
            print(f"[GridRenderer] Cleared all Z-level build flags")
    
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
    
    def _add_structure_sprite(self, x: int, y: int, z: int, tile_type: str, opacity: int = 255, sprite_list: arcade.SpriteList = None):
        """Add structure sprite (walls, floors, buildings) - rendered last.
        
        Handles construction darkening: tiles under construction use same sprite but darkened.
        Supports multi-tile structures (workstations, furniture) with automatic sprite tiling.
        
        Args:
            sprite_list: Optional sprite list to append to. If None, uses self.tile_sprite_list.
        """
        # Use provided sprite_list or fall back to self.tile_sprite_list
        target_list = sprite_list if sprite_list is not None else self.tile_sprite_list
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
            # Check if this is multi-tile furniture
            from furniture import get_furniture_size
            width, height = get_furniture_size(tile_type)
            
            if width > 1 or height > 1:
                # Skip if this tile is already part of a rendered multi-tile structure
                if (x, y, z) in self._rendered_multitile_tiles:
                    return
                
                # Multi-tile furniture - render all tiles
                self._render_multi_tile_structure(x, y, z, tile_type, width, height, opacity, is_construction, is_furniture=True, sprite_list=target_list)
                
                # Mark all tiles in footprint as rendered
                for dy in range(height):
                    for dx in range(width):
                        self._rendered_multitile_tiles.add((x + dx, y + dy, z))
            else:
                # Single-tile furniture - original behavior
                # Draw floor first
                floor_texture = self.get_tile_texture("finished_floor", x, y, z)
                if floor_texture:
                    floor_sprite = arcade.Sprite()
                    floor_sprite.texture = floor_texture
                    floor_sprite.center_x = screen_x + TILE_SIZE // 2
                    floor_sprite.center_y = screen_y + TILE_SIZE // 2
                    floor_sprite.alpha = opacity
                    target_list.append(floor_sprite)
                
                # Draw furniture on top
                furniture_texture = self._get_furniture_texture(tile_type)
                if furniture_texture:
                    furniture_sprite = arcade.Sprite()
                    furniture_sprite.texture = furniture_texture
                    furniture_sprite.center_x = screen_x + TILE_SIZE // 2
                    furniture_sprite.center_y = screen_y + TILE_SIZE // 2
                    furniture_sprite.alpha = opacity
                    target_list.append(furniture_sprite)
            return
        
        # Check if this is a workstation (need to render floor underneath)
        from buildings import BUILDING_TYPES, get_building_size
        building_def = BUILDING_TYPES.get(tile_type) or BUILDING_TYPES.get(tile_type.replace("finished_", ""))
        is_workstation = building_def and building_def.get("workstation", False)
        
        if is_workstation:
            # Render floor layer first if it exists
            if hasattr(self.grid, 'base_tiles'):
                base_tile = self.grid.base_tiles.get((x, y, z))
                if base_tile:
                    floor_texture = self.get_tile_texture(base_tile, x, y, z)
                    if floor_texture:
                        floor_sprite = arcade.Sprite()
                        floor_sprite.texture = floor_texture
                        floor_sprite.center_x = screen_x + TILE_SIZE // 2
                        floor_sprite.center_y = screen_y + TILE_SIZE // 2
                        floor_sprite.alpha = opacity
                        target_list.append(floor_sprite)
        
        # Check if this is a multi-tile workstation
        width, height = get_building_size(tile_type)
        
        if width > 1 or height > 1:
            # Skip if this tile is already part of a rendered multi-tile structure
            if (x, y, z) in self._rendered_multitile_tiles:
                return
            
            # Multi-tile workstation - render all tiles from origin
            self._render_multi_tile_structure(x, y, z, tile_type, width, height, opacity, is_construction, is_furniture=False, sprite_list=target_list)
            
            # Mark all tiles in footprint as rendered to avoid duplicates
            for dy in range(height):
                for dx in range(width):
                    self._rendered_multitile_tiles.add((x + dx, y + dy, z))
            return
        
        # Single-tile structure - render workstation sprite on top
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
            
            target_list.append(sprite)
    
    def _render_multi_tile_structure(self, origin_x: int, origin_y: int, z: int, tile_type: str, 
                                     width: int, height: int, opacity: int, is_construction: bool, is_furniture: bool, sprite_list: arcade.SpriteList = None):
        """Render a multi-tile structure (workstation or furniture).
        
        Args:
            sprite_list: Optional sprite list to append to. If None, uses self.tile_sprite_list.
        
        Sprite naming convention:
        - 1x2 (vertical): tiletype.png (bottom), tiletype_top.png
        - 2x1 (horizontal): tiletype.png (left), tiletype_right.png
        - 2x2: tiletype_sw.png, tiletype_se.png, tiletype_nw.png, tiletype_ne.png
        - 3x3: tiletype_sw.png, tiletype_s.png, tiletype_se.png, 
               tiletype_w.png, tiletype_center.png, tiletype_e.png,
               tiletype_nw.png, tiletype_n.png, tiletype_ne.png
        """
        # Use provided sprite_list or fall back to self.tile_sprite_list
        target_list = sprite_list if sprite_list is not None else self.tile_sprite_list
        
        # Always draw floor tiles first for multi-tile structures
        for dy in range(height):
            for dx in range(width):
                tile_x = origin_x + dx
                tile_y = origin_y + dy
                screen_x = tile_x * TILE_SIZE
                screen_y = tile_y * TILE_SIZE
                
                # Check if there's a stored base tile (floor)
                floor_tile = None
                if hasattr(self.grid, 'base_tiles'):
                    floor_tile = self.grid.base_tiles.get((tile_x, tile_y, z))
                
                # Default to finished_floor if no base tile stored
                if not floor_tile:
                    floor_tile = "finished_floor"
                
                floor_texture = self.get_tile_texture(floor_tile, tile_x, tile_y, z)
                if floor_texture:
                    floor_sprite = arcade.Sprite()
                    floor_sprite.texture = floor_texture
                    floor_sprite.center_x = screen_x + TILE_SIZE // 2
                    floor_sprite.center_y = screen_y + TILE_SIZE // 2
                    floor_sprite.alpha = opacity
                    target_list.append(floor_sprite)
        
        # Render structure tiles
        for dy in range(height):
            for dx in range(width):
                tile_x = origin_x + dx
                tile_y = origin_y + dy
                screen_x = tile_x * TILE_SIZE
                screen_y = tile_y * TILE_SIZE
                
                # Determine sprite suffix based on position
                suffix = self._get_multi_tile_suffix(dx, dy, width, height)
                
                # Load texture with suffix
                sprite_name = f"{tile_type}{suffix}"
                texture = self._get_multi_tile_texture(sprite_name, is_furniture)
                
                if texture:
                    sprite = arcade.Sprite()
                    sprite.texture = texture
                    sprite.center_x = screen_x + TILE_SIZE // 2
                    sprite.center_y = screen_y + TILE_SIZE // 2
                    sprite.alpha = opacity
                    
                    # CONSTRUCTION DARKENING
                    if is_construction:
                        sprite.color = (153, 153, 153)
                    
                    target_list.append(sprite)
    
    def _get_multi_tile_suffix(self, dx: int, dy: int, width: int, height: int) -> str:
        """Get the sprite suffix for a tile in a multi-tile structure.
        
        Returns empty string for origin tile, or suffix like '_top', '_right', '_nw', etc.
        """
        # 2x1 horizontal (stove)
        if width == 2 and height == 1:
            if dx == 0:
                return ""  # Left tile (origin)
            else:
                return "_right"
        
        # 1x2 vertical (bed)
        if width == 1 and height == 2:
            if dy == 0:
                return ""  # Bottom tile (origin)
            else:
                return "_top"
        
        # 2x2 (generator)
        if width == 2 and height == 2:
            if dy == 0:  # Bottom row
                return "_sw" if dx == 0 else "_se"
            else:  # Top row
                return "_nw" if dx == 0 else "_ne"
        
        # 3x3 (forge, still)
        if width == 3 and height == 3:
            if dy == 0:  # Bottom row
                if dx == 0: return "_sw"
                elif dx == 1: return "_s"
                else: return "_se"
            elif dy == 1:  # Middle row
                if dx == 0: return "_w"
                elif dx == 1: return "_center"
                else: return "_e"
            else:  # Top row
                if dx == 0: return "_nw"
                elif dx == 1: return "_n"
                else: return "_ne"
        
        # Fallback for other sizes
        return f"_{dx}_{dy}"
    
    def _get_multi_tile_texture(self, sprite_name: str, is_furniture: bool):
        """Load texture for multi-tile structure part."""
        cache_key = (sprite_name, 0)
        if cache_key in self.texture_cache:
            return self.texture_cache[cache_key]
        
        if is_furniture:
            sprite_path = f"assets/furniture/{sprite_name}.png"
        else:
            sprite_path = f"assets/workstations/{sprite_name}.png"
        
        try:
            texture = arcade.load_texture(sprite_path)
            self.texture_cache[cache_key] = texture
            return texture
        except:
            # Fallback: try without suffix (use single sprite for all tiles)
            base_name = sprite_name.split('_')[0]
            fallback_key = (base_name, 0)
            if fallback_key in self.texture_cache:
                return self.texture_cache[fallback_key]
            
            fallback_path = f"assets/furniture/{base_name}.png" if is_furniture else f"assets/workstations/{base_name}.png"
            try:
                texture = arcade.load_texture(fallback_path)
                self.texture_cache[fallback_key] = texture
                return texture
            except:
                return None
    
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
        
        Marks specific tile as dirty. Actual rebuild happens once per frame in draw().
        Only rebuilds changed tiles, not entire Z-level.
        """
        # Mark this specific tile as dirty
        self.dirty_tiles.add((x, y, z))
    
    def draw(self):
        """Draw sprites for current Z-level only.
        
        Rebuilds only dirty tiles since last frame.
        This ensures we only rebuild changed tiles, not entire Z-level.
        """
        # Build entire Z-level if never built
        if self.current_z not in self.z_levels_built:
            self.build_tile_sprites(self.current_z, force_rebuild=True)
        
        # Rebuild dirty tiles (batched once per frame)
        if self.dirty_tiles:
            self._rebuild_dirty_tiles()
        
        # Draw current Z-level
        current_list = self.z_level_sprite_lists.get(self.current_z)
        if current_list:
            current_list.draw()
