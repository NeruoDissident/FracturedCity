"""
Arcade-based game entry point for Fractured City.

This is the new main file using Python Arcade for GPU-accelerated rendering.
Game logic from the original main.py will be integrated here.
"""

import arcade
import pygame
from config import SCREEN_W, SCREEN_H, TILE_SIZE, GRID_W, GRID_H, COLONIST_COUNT
from grid import Grid
from grid_arcade import GridRenderer
from colonist_arcade import ColonistRenderer
from colonist import create_colonists, update_colonists

# Initialize Pygame for UI rendering (surfaces only, no window)
pygame.init()

# Window title
WINDOW_TITLE = "Fractured City (Arcade)"

class FracturedCityWindow(arcade.Window):
    """Main game window using Arcade."""
    
    def __init__(self):
        # Set background color BEFORE creating window to prevent white flash
        super().__init__(SCREEN_W, SCREEN_H, WINDOW_TITLE, resizable=True)
        
        # Set dark background color
        arcade.set_background_color((12, 14, 18))  # Dark cyberpunk background
        
        # Clear to dark immediately
        self.clear()
        
        # Game state
        self.grid = None
        self.grid_renderer = None
        self.colonist_renderer = None
        self.colonists = []
        self.tick_count = 0
        
        # Camera for scrolling (Arcade 3.0 API)
        self.camera = arcade.camera.Camera2D()
        self.gui_camera = arcade.camera.Camera2D()  # Fixed UI camera
        
        # Sprite lists (GPU batching)
        self.colonist_sprite_list = arcade.SpriteList()
        
        # Camera movement
        self.camera_speed = 20  # Increased from 10 for faster panning
        self.keys_pressed = set()
        
        # Zoom
        self.zoom_level = 1.0
        self.min_zoom = 0.25
        self.max_zoom = 2.0
        
        # Game speed
        self.game_speed = 3  # Default to 3x speed (1-5 range)
        
        # Pygame surface for UI rendering (reuse existing UI code)
        self.ui_surface = None
        self.ui_texture = None
        self.ui_sprite = None
        self.ui_sprite_list = arcade.SpriteList()
        
        # Mouse state
        self.mouse_x = 0
        self.mouse_y = 0
        self.hovered_tile = None  # (x, y, z) or None
        self.selected_tile = None  # (x, y, z) or None
        self.selected_colonist = None
        
        # Drag state for building (matches Pygame implementation)
        self.drag_start = None  # (tile_x, tile_y) or None
        self.drag_end = None  # (tile_x, tile_y) or None - updated during mouse motion
        self.drag_mode = None  # "wall", "floor", "stockpile", etc.
        
        # Sprite cache for tiles and colonists (avoid reloading every frame)
        self.texture_cache = {}
        
        # Track wanderer/fixer colonist UIDs in renderer
        self.tracked_wanderer_uids = set()
        self.tracked_fixer_uids = set()
    
    def _sync_wanderers_with_renderer(self):
        """Sync wanderers and fixers with colonist renderer."""
        from wanderers import get_wanderers, get_fixers
        
        # Get current wanderers/fixers
        wanderers = get_wanderers()
        fixers = get_fixers()
        
        # Track current UIDs
        current_wanderer_uids = {w["colonist"].uid for w in wanderers}
        current_fixer_uids = {f["colonist"].uid for f in fixers}
        
        # Add new wanderers to renderer
        for wanderer in wanderers:
            colonist = wanderer["colonist"]
            if colonist.uid not in self.tracked_wanderer_uids:
                self.colonist_renderer.add_colonist(colonist)
                self.tracked_wanderer_uids.add(colonist.uid)
        
        # Add new fixers to renderer
        for fixer in fixers:
            colonist = fixer["colonist"]
            if colonist.uid not in self.tracked_fixer_uids:
                self.colonist_renderer.add_colonist(colonist)
                self.tracked_fixer_uids.add(colonist.uid)
        
        # Remove departed wanderers from renderer (but NOT recruited ones)
        departed_wanderers = self.tracked_wanderer_uids - current_wanderer_uids
        for uid in departed_wanderers:
            # Check if this colonist was recruited (is now in main colonist list)
            is_recruited = any(c.uid == uid for c in self.colonists)
            if not is_recruited:
                # Only remove if not recruited - rejected/left wanderers
                for sprite_uid, sprite in list(self.colonist_renderer.colonist_sprites.items()):
                    if sprite_uid == uid:
                        self.colonist_renderer.remove_colonist(sprite.colonist)
                        break
            self.tracked_wanderer_uids.discard(uid)
        
        # Remove departed fixers from renderer
        departed_fixers = self.tracked_fixer_uids - current_fixer_uids
        for uid in departed_fixers:
            for sprite_uid, sprite in list(self.colonist_renderer.colonist_sprites.items()):
                if sprite_uid == uid:
                    self.colonist_renderer.remove_colonist(sprite.colonist)
                    break
            self.tracked_fixer_uids.discard(uid)
    
    def snap_camera_to_tile(self, x: int, y: int, z: int):
        """Snap camera to a specific tile position."""
        # Switch to target Z-level if different
        if z != self.grid.current_z:
            self.grid.current_z = z
            self.grid_renderer.build_tile_sprites(z_level=z)
            print(f"[Camera] Switched to Z={z}")
        
        # Move camera to tile (camera position is viewport center)
        target_x = x * TILE_SIZE + TILE_SIZE // 2
        target_y = y * TILE_SIZE + TILE_SIZE // 2
        self.camera.position = (target_x, target_y)
        print(f"[Camera] Snapped to ({x}, {y}, {z})")
    
    def open_colonist_detail(self, colonist):
        """Open colonist detail panel for a specific colonist."""
        if colonist in self.colonists:
            index = self.colonists.index(colonist)
            self.colonist_detail_panel.open(self.colonists, index)
            print(f"[UI] Opened detail panel for {colonist.name}")
        
    def setup(self):
        """Initialize game state."""
        print("[Arcade] Setting up game...")
        
        # Show loading screen during setup
        self.clear()
        arcade.draw_text(
            text="LOADING...",
            x=SCREEN_W / 2,
            y=SCREEN_H / 2,
            color=(0, 220, 220),  # Neon cyan
            font_size=32,
            bold=True,
            anchor_x="center",
            anchor_y="center"
        )
        arcade.draw_text(
            text="Generating world...",
            x=SCREEN_W / 2,
            y=SCREEN_H / 2 - 50,
            color=(120, 130, 145),  # Dim gray
            font_size=16,
            anchor_x="center",
            anchor_y="center"
        )
        self.flip()  # Show loading screen immediately
        
        # Initialize tileset system (must be done after Arcade window is created)
        from tileset_loader import initialize_tilesets
        initialize_tilesets()
        
        # Initialize audio system and start music
        from audio import init_audio
        init_audio()
        
        # Create grid (uses global config values)
        self.grid = Grid()
        
        # Generate CITY WORLD (roads, buildings, dirt patches)
        from city_generator import CityGenerator
        worldgen = CityGenerator(self.grid)
        spawn_x, spawn_y = worldgen.generate_city()
        
        print(f"[Arcade] World generated with colonist spawn at ({spawn_x}, {spawn_y})")
        
        # Create grid renderer and build tile sprites
        self.grid_renderer = GridRenderer(self.grid)
        self.grid_renderer.build_tile_sprites(z_level=0)
        
        # Wire grid tile changes to renderer updates (for construction, demolition, etc.)
        self.grid.on_tile_change = self.grid_renderer.update_tile
        
        # Create colonists at spawn location (from worldgen)
        self.colonists = create_colonists(COLONIST_COUNT, spawn_x, spawn_y)
        
        # Create starter stockpile with resources (uses existing system)
        from resources import _create_starter_stockpile
        _create_starter_stockpile(self.grid, (spawn_x, spawn_y))
        
        # Create colonist renderer and add all colonists
        self.colonist_renderer = ColonistRenderer()
        for colonist in self.colonists:
            self.colonist_renderer.add_colonist(colonist)
        
        # Center camera on spawn (Camera2D position is viewport CENTER)
        cam_x = spawn_x * TILE_SIZE
        cam_y = spawn_y * TILE_SIZE
        self.camera.position = (cam_x, cam_y)
        
        # Initialize native Arcade UI
        from ui_arcade import ArcadeUI
        self.ui = ArcadeUI()
        
        # Initialize left sidebar
        from ui_arcade_panels import LeftSidebar, ColonistDetailPanel
        self.left_sidebar = LeftSidebar()
        self.colonist_detail_panel = ColonistDetailPanel()
        
        # Wire sidebar callbacks
        self.left_sidebar.on_colonist_locate = self.snap_camera_to_tile
        self.left_sidebar.on_colonist_click = self.open_colonist_detail
        
        # Initialize notification panel
        from ui_arcade_notifications import get_notification_panel
        self.notification_panel = get_notification_panel()
        
        # Initialize right panel with colonists (always visible)
        self.colonist_detail_panel.colonists = self.colonists
        
        print(f"[Arcade] Setup complete! {len(self.colonists)} colonists spawned.")
        print("[Arcade] Use WASD or Arrow Keys to move camera")
        print("[Arcade] Use Mouse Wheel to zoom")
    
    def on_show(self):
        """Called when window is shown - clear to dark immediately."""
        arcade.set_background_color((12, 14, 18))
        self.clear()
    
    def on_draw(self):
        """Render the game."""
        self.clear()
        
        # Use game camera for world rendering
        self.camera.use()
        
        # Draw tiles using GPU batching (existing system)
        if self.grid_renderer:
            self.grid_renderer.draw()
        
        # Draw colonists using GPU batching (existing system)
        if self.colonist_renderer:
            self.colonist_renderer.draw(current_z=self.grid.current_z)
        
        # Draw construction overlays (material icons + progress bars)
        self._draw_construction_overlays()
        
        # Draw zones and designations (stockpiles, harvest highlights)
        self._draw_zones_and_designations()
        
        # Draw stockpile storage (items in stockpiles)
        self._draw_stockpile_storage()
        
        # Draw world items (items on ground waiting for pickup)
        self._draw_world_items()
        
        # Draw tile highlights (still in world camera view)
        # Draw selected tile first (under hover)
        if self.selected_tile:
            tile_x, tile_y, tile_z = self.selected_tile
            # Semi-transparent pink fill
            arcade.draw_lrbt_rectangle_filled(
                left=tile_x * TILE_SIZE,
                right=(tile_x + 1) * TILE_SIZE,
                bottom=tile_y * TILE_SIZE,
                top=(tile_y + 1) * TILE_SIZE,
                color=(255, 50, 130, 60)  # Pink with alpha
            )
            # Thick pink border
            arcade.draw_lrbt_rectangle_outline(
                left=tile_x * TILE_SIZE,
                right=(tile_x + 1) * TILE_SIZE,
                bottom=tile_y * TILE_SIZE,
                top=(tile_y + 1) * TILE_SIZE,
                color=(255, 50, 130, 255),  # Bright pink
                border_width=4
            )
        
        # Draw drag preview (if dragging)
        if self.drag_start and self.drag_end and self.drag_mode:
            start_x, start_y = self.drag_start
            end_x, end_y = self.drag_end
            
            # Get tiles that will be affected
            if self.drag_mode in ("wall", "door"):
                # Line drag
                preview_tiles = self._get_drag_line(self.drag_start, self.drag_end)
            elif self.drag_mode in ("floor", "stockpile", "roof", "harvest", "salvage") or self.drag_mode.startswith("room_"):
                # Rectangle drag
                preview_tiles = self._get_drag_rect(self.drag_start, self.drag_end)
            else:
                preview_tiles = [self.drag_end]
            
            # Draw highlighted tiles
            for tx, ty in preview_tiles:
                # Semi-transparent yellow fill
                arcade.draw_lrbt_rectangle_filled(
                    left=tx * TILE_SIZE,
                    right=(tx + 1) * TILE_SIZE,
                    bottom=ty * TILE_SIZE,
                    top=(ty + 1) * TILE_SIZE,
                    color=(255, 220, 0, 80)  # Yellow with alpha
                )
                # Yellow border
                arcade.draw_lrbt_rectangle_outline(
                    left=tx * TILE_SIZE,
                    right=(tx + 1) * TILE_SIZE,
                    bottom=ty * TILE_SIZE,
                    top=(ty + 1) * TILE_SIZE,
                    color=(255, 220, 0, 200),  # Bright yellow
                    border_width=2
                )
        
        # Draw hover highlight on top
        if self.hovered_tile:
            tile_x, tile_y, tile_z = self.hovered_tile
            
            # Check if we're placing a multi-tile structure
            width, height = 1, 1
            if self.drag_mode:
                # Check for workstation
                from buildings import BUILDING_TYPES, get_building_size
                if self.drag_mode in BUILDING_TYPES:
                    width, height = get_building_size(self.drag_mode)
                # Check for furniture
                elif self.drag_mode.startswith("furn_"):
                    from furniture import get_furniture_size
                    item_id = self.drag_mode[5:]
                    width, height = get_furniture_size(item_id)
            
            # Draw footprint for all tiles that will be occupied
            for dy in range(height):
                for dx in range(width):
                    footprint_x = tile_x + dx
                    footprint_y = tile_y + dy
                    
                    # Semi-transparent cyan fill
                    arcade.draw_lrbt_rectangle_filled(
                        left=footprint_x * TILE_SIZE,
                        right=(footprint_x + 1) * TILE_SIZE,
                        bottom=footprint_y * TILE_SIZE,
                        top=(footprint_y + 1) * TILE_SIZE,
                        color=(0, 220, 220, 40)  # Cyan with alpha
                    )
                    # Thick cyan border
                    arcade.draw_lrbt_rectangle_outline(
                        left=footprint_x * TILE_SIZE,
                        right=(footprint_x + 1) * TILE_SIZE,
                        bottom=footprint_y * TILE_SIZE,
                        top=(footprint_y + 1) * TILE_SIZE,
                        color=(0, 220, 220, 255),  # Bright cyan
                        border_width=4
                    )
        
        # Draw day/night cycle overlay (still in world camera)
        self._draw_day_night_overlay()
        
        # Use GUI camera for UI (default viewport, no zoom/pan)
        self.gui_camera.use()
        
        # GUI camera should have default projection (0,0 at bottom-left, SCREEN_W,SCREEN_H at top-right)
        # This matches the mouse coordinate system
        
        # Draw native Arcade UI
        from time_system import get_display_string
        import zones as zones_module
        import jobs as jobs_module
        
        # Gather game data for UI
        game_data = {
            "time_str": get_display_string(),
            "z_level": 0,
            "paused": False,
            "game_speed": 1,
            "resources": {
                "wood": zones_module.get_total_stored("wood"),
                "scrap": zones_module.get_total_stored("scrap"),
                "metal": zones_module.get_total_stored("metal"),
                "mineral": zones_module.get_total_stored("mineral"),
                "power": zones_module.get_total_stored("power"),
                "raw_food": zones_module.get_total_stored("raw_food"),
                "cooked_meal": zones_module.get_total_stored("cooked_meal"),
            },
            "colonist_objects": [c for c in self.colonists if not c.is_dead],
            "job_count": len(jobs_module.get_all_available_jobs()),
        }
        
        # Draw clean native Arcade UI
        self.ui.draw(game_data)
        
        # Draw left sidebar
        import jobs as jobs_module
        self.left_sidebar.draw(
            colonists=self.colonists,
            jobs=jobs_module.JOB_QUEUE,
            items={},  # TODO: Get from stockpiles
            rooms={}   # TODO: Get from room system
        )
        
        # Draw colonist detail panel (right side)
        self.colonist_detail_panel.draw()
        
        # Draw native Arcade workstation panel
        from ui_arcade_workstation import get_workstation_panel
        ws_panel = get_workstation_panel()
        ws_panel.draw(self.mouse_x, self.mouse_y)
        
        # Draw native Arcade bed assignment panel
        from ui_arcade_bed import get_bed_assignment_panel
        bed_panel = get_bed_assignment_panel()
        bed_panel.draw(self.colonists, self.mouse_x, self.mouse_y)
        
        # Draw visitor panel (popup over everything)
        from ui_arcade_visitor import get_visitor_panel
        visitor_panel = get_visitor_panel()
        visitor_panel.draw(self.mouse_x, self.mouse_y)
        
        # Draw trader panel (popup over everything)
        from ui_arcade_trader import get_trader_panel
        trader_panel = get_trader_panel()
        trader_panel.draw(self.mouse_x, self.mouse_y)
        
        # Draw notification panel (top-right, above everything)
        self.notification_panel.draw()
        
        # Draw selected colonist info (if any)
        if self.selected_colonist:
            info_y = 100
            arcade.draw_text(
                text=f"Selected: {self.selected_colonist.name}",
                x=10,
                y=info_y,
                color=(255, 50, 130),  # Neon pink
                font_size=14,
                bold=True
            )
            status = self.selected_colonist.current_job.type if self.selected_colonist.current_job else "Idle"
            arcade.draw_text(
                text=f"Status: {status}",
                x=10,
                y=info_y - 20,
                color=(230, 240, 250),
                font_size=12
            )
    
    def _draw_stockpile_storage(self):
        """Draw items stored in stockpiles (resources + equipment/furniture)."""
        import zones as zones_module
        
        # Cache for loaded item textures
        if not hasattr(self, '_item_texture_cache'):
            self._item_texture_cache = {}
        
        # Draw resource storage (wood, metal, food, etc.)
        tile_storage = zones_module.get_all_tile_storage()
        
        for (x, y, z), storage in tile_storage.items():
            if z != self.grid.current_z or not storage:
                continue
            
            resource_type = storage.get("type", "")
            amount = storage.get("amount", 0)
            
            if amount <= 0:
                continue
            
            self._draw_stockpile_item(x, y, resource_type, amount)
        
        # Draw equipment/furniture storage (separate system)
        equipment_storage = zones_module.get_all_stored_equipment()
        
        for (x, y, z), items in equipment_storage.items():
            if z != self.grid.current_z or not items:
                continue
            
            # Group items by ID to show stack count
            item_counts = {}
            for item in items:
                item_id = item.get("id", item.get("name", "item"))
                item_counts[item_id] = item_counts.get(item_id, 0) + 1
            
            # Draw first item type (if multiple types, show the first one)
            if item_counts:
                item_id = list(item_counts.keys())[0]
                count = item_counts[item_id]
                self._draw_stockpile_item(x, y, item_id, count)
    
    def _draw_day_night_overlay(self):
        """Draw day/night cycle tint overlay over the entire world."""
        from time_system import get_game_time
        
        game_time = get_game_time()
        if not game_time:
            return
        
        # Get current tint color (RGBA)
        r, g, b, a = game_time.get_tint()
        
        # Only draw if there's visible alpha
        if a > 0:
            # Get camera viewport bounds
            cam_x, cam_y = self.camera.position
            viewport_width = SCREEN_W / self.zoom_level
            viewport_height = SCREEN_H / self.zoom_level
            
            # Draw overlay covering visible area
            left = cam_x - viewport_width / 2
            right = cam_x + viewport_width / 2
            bottom = cam_y - viewport_height / 2
            top = cam_y + viewport_height / 2
            
            arcade.draw_lrbt_rectangle_filled(
                left=left,
                right=right,
                bottom=bottom,
                top=top,
                color=(r, g, b, a)
            )
    
    def _draw_stockpile_item(self, x: int, y: int, item_type: str, amount: int):
        """Draw a single item in a stockpile tile."""
        center_x = (x + 0.5) * TILE_SIZE
        center_y = (y + 0.5) * TILE_SIZE
        
        # Try to load item sprite
        texture = None
        if item_type not in self._item_texture_cache:
            sprite_paths = [
                f"assets/items/{item_type}.png",
                f"assets/furniture/{item_type}.png",
                f"assets/furniture/{item_type}_placed.png",
            ]
            
            for sprite_path in sprite_paths:
                try:
                    texture = arcade.load_texture(sprite_path)
                    self._item_texture_cache[item_type] = texture
                    break
                except:
                    continue
            
            if texture is None:
                self._item_texture_cache[item_type] = None
        else:
            texture = self._item_texture_cache[item_type]
        
        # Draw sprite or fallback
        if texture:
            sprite_size = TILE_SIZE * 0.6
            arcade.draw_texture_rect(
                texture,
                arcade.LRBT(
                    center_x - sprite_size / 2,
                    center_x + sprite_size / 2,
                    center_y - sprite_size / 2,
                    center_y + sprite_size / 2
                )
            )
        else:
            # Fallback: colored square
            if "wood" in item_type:
                color = (139, 90, 43)
            elif "scrap" in item_type or "metal" in item_type:
                color = (120, 120, 140)
            elif "mineral" in item_type:
                color = (100, 100, 120)
            elif "food" in item_type or "meal" in item_type:
                color = (100, 200, 100)
            elif "power" in item_type or "cell" in item_type:
                color = (255, 220, 0)
            elif "bed" in item_type or "chair" in item_type or "stool" in item_type:
                color = (180, 140, 100)  # Brown for furniture
            else:
                color = (150, 150, 200)
            
            square_size = 12
            arcade.draw_lrbt_rectangle_filled(
                center_x - square_size / 2,
                center_x + square_size / 2,
                center_y - square_size / 2,
                center_y + square_size / 2,
                color
            )
            arcade.draw_lrbt_rectangle_outline(
                center_x - square_size / 2,
                center_x + square_size / 2,
                center_y - square_size / 2,
                center_y + square_size / 2,
                (255, 255, 255), 1
            )
        
        # Draw stack count
        if amount > 1:
            text_width = len(str(amount)) * 6 + 4
            arcade.draw_lrbt_rectangle_filled(
                center_x + 6, center_x + 6 + text_width,
                center_y + 4, center_y + 12,
                (0, 0, 0, 200)
            )
            arcade.draw_text(
                str(amount),
                center_x + 8,
                center_y + 8,
                (255, 255, 255),
                font_size=10,
                bold=True,
                anchor_x="left",
                anchor_y="center",
                font_name="Arial"
            )
    
    def _draw_world_items(self):
        """Draw items on the ground (in stockpiles) with stack quantities."""
        from items import get_all_world_items
        
        world_items = get_all_world_items()
        
        # Debug: Print world items on first call
        if not hasattr(self, '_debug_items_printed'):
            self._debug_items_printed = True
            print(f"[Debug] World items count: {len(world_items)}")
            for coord, items in list(world_items.items())[:3]:  # Show first 3
                print(f"  {coord}: {len(items)} items - {[i.get('id', 'unknown') for i in items]}")
        
        # Cache for loaded item textures
        if not hasattr(self, '_item_texture_cache'):
            self._item_texture_cache = {}
        
        for (x, y, z), items in world_items.items():
            if z != self.grid.current_z or not items:
                continue
            
            # Group items by ID to show stack count
            item_stacks = {}
            for item in items:
                item_id = item.get("id", "unknown")
                if item_id not in item_stacks:
                    item_stacks[item_id] = 0
                item_stacks[item_id] += 1
            
            # Draw first item type with stack count
            if item_stacks:
                first_item_id = list(item_stacks.keys())[0]
                stack_count = item_stacks[first_item_id]
                
                center_x = (x + 0.5) * TILE_SIZE
                center_y = (y + 0.5) * TILE_SIZE
                
                # Try to load item sprite
                texture = None
                if first_item_id not in self._item_texture_cache:
                    # Try multiple sprite locations
                    sprite_paths = [
                        f"assets/items/{first_item_id}.png",
                        f"assets/furniture/{first_item_id}.png",
                        f"assets/furniture/{first_item_id}_placed.png",
                    ]
                    
                    for sprite_path in sprite_paths:
                        try:
                            texture = arcade.load_texture(sprite_path)
                            self._item_texture_cache[first_item_id] = texture
                            break
                        except:
                            continue
                    
                    # If no sprite found, cache None
                    if texture is None:
                        self._item_texture_cache[first_item_id] = None
                else:
                    texture = self._item_texture_cache[first_item_id]
                
                # Draw sprite or fallback
                if texture:
                    # Draw item sprite (scaled to fit tile)
                    sprite_size = TILE_SIZE * 0.6  # 60% of tile size
                    arcade.draw_texture_rect(
                        texture,
                        arcade.LRBT(
                            center_x - sprite_size / 2,
                            center_x + sprite_size / 2,
                            center_y - sprite_size / 2,
                            center_y + sprite_size / 2
                        )
                    )
                else:
                    # Fallback: colored square based on item type
                    if "wood" in first_item_id:
                        color = (139, 90, 43)  # Wood brown
                    elif "scrap" in first_item_id or "metal" in first_item_id:
                        color = (120, 120, 140)  # Metal gray
                    elif "mineral" in first_item_id:
                        color = (100, 100, 120)  # Stone gray
                    elif "food" in first_item_id or "meal" in first_item_id:
                        color = (100, 200, 100)  # Green
                    elif "power" in first_item_id or "cell" in first_item_id:
                        color = (255, 220, 0)  # Yellow
                    else:
                        color = (150, 150, 200)  # Blue-gray for equipment
                    
                    # Draw colored square
                    square_size = 10
                    arcade.draw_lrbt_rectangle_filled(
                        center_x - square_size / 2,
                        center_x + square_size / 2,
                        center_y - square_size / 2,
                        center_y + square_size / 2,
                        color
                    )
                    arcade.draw_lrbt_rectangle_outline(
                        center_x - square_size / 2,
                        center_x + square_size / 2,
                        center_y - square_size / 2,
                        center_y + square_size / 2,
                        (255, 255, 255), 1
                    )
                
                # Draw stack count if > 1
                if stack_count > 1:
                    # Background for text
                    text_width = len(str(stack_count)) * 6 + 4
                    arcade.draw_lrbt_rectangle_filled(
                        center_x + 6, center_x + 6 + text_width,
                        center_y + 4, center_y + 12,
                        (0, 0, 0, 200)
                    )
                    arcade.draw_text(
                        str(stack_count),
                        center_x + 8,
                        center_y + 8,
                        (255, 255, 255),
                        font_size=10,
                        bold=True,
                        anchor_x="left",
                        anchor_y="center",
                        font_name="Arial"
                    )
    
    def on_update(self, delta_time):
        """Update game logic."""
        # Camera movement
        cam_x, cam_y = self.camera.position
        
        if arcade.key.W in self.keys_pressed or arcade.key.UP in self.keys_pressed:
            cam_y += self.camera_speed
        if arcade.key.S in self.keys_pressed or arcade.key.DOWN in self.keys_pressed:
            cam_y -= self.camera_speed
        if arcade.key.A in self.keys_pressed or arcade.key.LEFT in self.keys_pressed:
            cam_x -= self.camera_speed
        if arcade.key.D in self.keys_pressed or arcade.key.RIGHT in self.keys_pressed:
            cam_x += self.camera_speed
        
        # Clamp camera to world bounds
        max_x = GRID_W * TILE_SIZE - SCREEN_W
        max_y = GRID_H * TILE_SIZE - SCREEN_H
        cam_x = max(0, min(cam_x, max_x))
        cam_y = max(0, min(cam_y, max_y))
        
        self.camera.position = (cam_x, cam_y)
        
        # Update game logic at current speed
        for _ in range(self.game_speed):
            self.tick_count += 1
            self._run_game_tick()
        
    
    def _run_game_tick(self):
        """Run a single game tick - called multiple times per frame based on game_speed."""
        # Import all game systems
        from resources import update_resource_nodes, process_auto_haul_jobs
        from buildings import update_doors, update_windows, process_crafting_jobs, process_supply_jobs
        from items import process_equipment_haul_jobs, process_auto_equip
        from recreation import spawn_recreation_jobs
        from training import spawn_training_jobs
        from time_system import tick_time
        from notifications import update_notifications
        import jobs as jobs_module
        import zones as zones_module
        import rooms as rooms_module
        
        # Update notifications (always, even when paused)
        update_notifications()
        
        # Game simulation (not paused for now - will add pause later)
        tick_time()  # Advance game time
        
        # Update colonists
        update_colonists(self.colonists, self.grid, self.tick_count)
        
        # Update sprite positions after colonist logic
        if self.colonist_renderer:
            self.colonist_renderer.update_positions()
        
        # Update resource nodes
        update_resource_nodes(self.grid)
        
        # Update doors and windows
        update_doors()
        update_windows()
        
        # Process room updates
        rooms_module.process_dirty_rooms(self.grid)
        
        # Update job timers
        jobs_module.update_job_timers()
        
        # Process auto-haul jobs
        process_auto_haul_jobs(jobs_module, zones_module)
        
        # Process supply jobs for construction
        process_supply_jobs(jobs_module, zones_module)
        
        # Process crafting jobs
        process_crafting_jobs(jobs_module, zones_module)
        
        # Throttled systems (every 10 ticks)
        if self.tick_count % 10 == 0:
            process_equipment_haul_jobs(jobs_module, zones_module)
            zones_module.process_stockpile_relocation(jobs_module)
            zones_module.process_filter_mismatch_relocation(jobs_module)
        
        # Throttled systems (every 60 ticks / once per second)
        if self.tick_count % 60 == 0:
            process_auto_equip(self.colonists, zones_module, jobs_module)
            spawn_recreation_jobs(self.colonists, self.grid, self.tick_count)
            spawn_training_jobs(self.colonists, self.grid, self.tick_count)
        
        # Update wanderers and traders
        if self.tick_count % 60 == 0:
            from wanderers import spawn_wanderer_check, update_wanderers, spawn_fixer_check, update_fixers, process_trade_jobs, get_wanderers, get_fixers
            from resources import get_colonist_spawn_location
            from time_system import get_game_time
            
            colony_center = get_colonist_spawn_location()
            current_day = get_game_time().day
            
            spawn_wanderer_check(current_day, colony_center, self.grid)
            update_wanderers(self.grid, colony_center, self.tick_count)
            spawn_fixer_check(current_day, colony_center, self.grid)
            update_fixers(self.grid, colony_center, self.tick_count)
            process_trade_jobs(jobs_module, zones_module)
            
            # Sync wanderers/fixers with renderer (add new ones, remove departed)
            self._sync_wanderers_with_renderer()
        
        # Update audio
        if self.tick_count % 60 == 0:
            from audio import get_audio_manager
            audio_manager = get_audio_manager()
            audio_manager.update()
    
    def on_key_press(self, key, modifiers):
        """Handle key press."""
        self.keys_pressed.add(key)
        
        # Game speed controls (1-5 keys)
        if key == arcade.key.KEY_1:
            self.game_speed = 1
            print(f"[Speed] Game speed: 1x")
        elif key == arcade.key.KEY_2:
            self.game_speed = 2
            print(f"[Speed] Game speed: 2x")
        elif key == arcade.key.KEY_3:
            self.game_speed = 3
            print(f"[Speed] Game speed: 3x")
        elif key == arcade.key.KEY_4:
            self.game_speed = 4
            print(f"[Speed] Game speed: 4x")
        elif key == arcade.key.KEY_5:
            self.game_speed = 5
            print(f"[Speed] Game speed: 5x")
        
        # Z-level controls
        if key == arcade.key.PAGEUP:
            if self.grid.current_z < self.grid.depth - 1:
                self.grid.current_z += 1
                self.grid_renderer.build_tile_sprites(z_level=self.grid.current_z)
                print(f"[Z-Level] Moved up to Z={self.grid.current_z}")
        elif key == arcade.key.PAGEDOWN:
            if self.grid.current_z > 0:
                self.grid.current_z -= 1
                self.grid_renderer.build_tile_sprites(z_level=self.grid.current_z)
                print(f"[Z-Level] Moved down to Z={self.grid.current_z}")
        
        if key == arcade.key.ESCAPE:
            arcade.close_window()
        
        # Debug keys
        elif key == arcade.key.F4:
            # Debug: Toggle free build mode (no material requirements)
            from buildings import toggle_free_build_mode
            new_state = toggle_free_build_mode()
            status = "ENABLED" if new_state else "DISABLED"
            print(f"[Debug] FREE BUILD MODE: {status}")
            from notifications import add_notification, NotificationType
            add_notification(NotificationType.INFO, 
                           f"FREE BUILD MODE: {status}",
                           "No material requirements" if new_state else "Normal building rules",
                           duration=180)
        
        elif key == arcade.key.F7:
            # Debug: Spawn wanderers (refugees) and fixer (trader)
            from wanderers import _pick_group_spawn_location, _create_wanderer_at, _wanderers, _create_fixer, _fixers
            from resources import get_colonist_spawn_location
            from notifications import add_notification, NotificationType
            import random
            
            colony_center = get_colonist_spawn_location()
            
            # Pick ONE spawn location for the group
            group_spawn = _pick_group_spawn_location(self.grid)
            if group_spawn:
                # Spawn 1-3 wanderers around that point
                num_wanderers = random.randint(1, 3)
                spawned_names = []
                for i in range(num_wanderers):
                    offset_x = (i % 3) - 1
                    offset_y = (i // 3) - 1
                    spawn_x = group_spawn[0] + offset_x
                    spawn_y = group_spawn[1] + offset_y
                    if not self.grid.is_walkable(spawn_x, spawn_y, 0):
                        spawn_x, spawn_y = group_spawn
                    
                    wanderer = _create_wanderer_at(spawn_x, spawn_y, colony_center, self.grid)
                    if wanderer:
                        _wanderers.append(wanderer)
                        spawned_names.append(wanderer["name"])
                
                if spawned_names:
                    print(f"[Debug] Spawned {len(spawned_names)} wanderer(s): {', '.join(spawned_names)}")
                    add_notification(NotificationType.ARRIVAL,
                                   f"// {len(spawned_names)} SIGNAL(S) DETECTED //",
                                   ", ".join(spawned_names),
                                   duration=480,
                                   click_location=group_spawn)
            
            # Also spawn a fixer if none exists
            if len(_fixers) == 0:
                fixer = _create_fixer(colony_center, self.grid)
                if fixer:
                    _fixers.append(fixer)
                    print(f"[Debug] Spawned fixer: {fixer['name']} from {fixer['origin'].name}")
                    fixer_loc = (fixer["x"], fixer["y"])
                    add_notification(NotificationType.INFO,
                                   "// FIXER INBOUND //",
                                   f"{fixer['name']} wants to trade",
                                   duration=480,
                                   click_location=fixer_loc)
            else:
                print("[Debug] Fixer already present, skipping")
        
        elif key == arcade.key.F8:
            # Debug: Print construction site status
            from buildings import get_all_construction_sites, get_missing_materials
            import zones as zones_module
            sites = get_all_construction_sites()
            print(f"[Debug] Construction sites: {len(sites)}")
            for (x, y, z), site in sites.items():
                missing = get_missing_materials(x, y, z)
                print(f"  ({x},{y},z={z}) type={site.get('type')} needed={site.get('materials_needed')} delivered={site.get('materials_delivered')} missing={missing}")
            # Also print stockpile contents
            print("[Debug] Stockpile contents:")
            for res_type in ["wood", "scrap", "metal", "mineral", "power"]:
                total = zones_module.get_total_stored(res_type)
                print(f"  {res_type}: {total}")
        
        elif key == arcade.key.F11:
            # Debug: Spawn a raider
            from wanderers import spawn_raider
            from notifications import add_notification, NotificationType
            raider = spawn_raider(self.grid)
            if raider:
                self.colonists.append(raider)
                self.colonist_renderer.add_colonist(raider)  # Add to renderer
                add_notification(NotificationType.FIGHT_START, f"Raider: {raider.name}", 
                               duration=180, click_location=(raider.x, raider.y))
                print(f"[Debug] Spawned raider: {raider.name} at ({raider.x}, {raider.y})")
        
        elif key == arcade.key.F12:
            # Debug: Toggle BERSERK MODE - everyone fights everyone
            from notifications import add_notification, NotificationType
            alive = [c for c in self.colonists if not c.is_dead]
            if alive:
                # Check if already berserk (toggle off)
                if getattr(alive[0], '_debug_berserk', False):
                    # Turn off berserk
                    for c in alive:
                        c._debug_berserk = False
                        c.is_hostile = False
                        c.in_combat = False
                        c.combat_target = None
                    print("[Debug] BERSERK MODE OFF - peace restored")
                    add_notification(NotificationType.INFO,
                                   "// PEACE PROTOCOL //",
                                   "Combat systems disengaged",
                                   duration=180)
                else:
                    # UNLEASH HELL
                    for c in alive:
                        c._debug_berserk = True
                        c.is_hostile = True
                        c.state = "idle"
                        c.current_job = None
                    print(f"[Debug] BERSERK MODE ON - {len(alive)} colonists going wild!")
                    add_notification(NotificationType.FIGHT_START,
                                   "// BERSERK PROTOCOL //",
                                   f"All {len(alive)} colonists hostile!",
                                   duration=300)
    
    def on_key_release(self, key, modifiers):
        """Handle key release."""
        self.keys_pressed.discard(key)
    
    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        """Handle mouse wheel for zoom and UI scrolling."""
        # Check if bed assignment panel wants to handle scroll
        from ui_arcade_bed import get_bed_assignment_panel
        bed_panel = get_bed_assignment_panel()
        if bed_panel.handle_scroll(x, y, scroll_y, self.colonists):
            return  # Panel consumed the scroll
        
        # Check if workstation panel wants to handle scroll
        from ui_arcade_workstation import get_workstation_panel
        ws_panel = get_workstation_panel()
        if ws_panel.visible:
            if (ws_panel.panel_x <= x <= ws_panel.panel_x + ws_panel.panel_width and
                ws_panel.panel_y <= y <= ws_panel.panel_y + ws_panel.panel_height):
                return  # Don't zoom when over workstation panel
        
        # Simple zoom: just change zoom level, don't move camera
        # This is the most basic zoom that won't cause drift
        if scroll_y > 0:
            self.zoom_level = min(self.zoom_level * 1.1, self.max_zoom)
        else:
            self.zoom_level = max(self.zoom_level * 0.9, self.min_zoom)
        
        self.camera.zoom = self.zoom_level
    
    def on_mouse_motion(self, x, y, dx, dy):
        """Handle mouse movement."""
        self.mouse_x = x
        self.mouse_y = y
        
        # Update action bar tooltip hover
        self.ui.action_bar.update_hover(x, y)
        
        # Update left sidebar hover state
        self.left_sidebar.update_hover(x, y, self.colonists)
        
        # Convert screen coords to world coords
        # Camera2D viewport is CENTERED on camera.position
        cam_x, cam_y = self.camera.position
        
        # Screen coords relative to center, then account for zoom and camera
        # Mouse (0,0) is bottom-left of screen, camera position is center of viewport
        screen_center_x = SCREEN_W / 2
        screen_center_y = SCREEN_H / 2
        
        # Offset from screen center, scaled by zoom, plus camera position
        world_x = ((x - screen_center_x) / self.zoom_level) + cam_x
        world_y = ((y - screen_center_y) / self.zoom_level) + cam_y
        
        # Convert world pixels to tile coordinates
        tile_x = int(world_x // TILE_SIZE)
        tile_y = int(world_y // TILE_SIZE)
        
        # Check if tile is in bounds
        if 0 <= tile_x < GRID_W and 0 <= tile_y < GRID_H:
            self.hovered_tile = (tile_x, tile_y, 0)
            
            # Update drag end position if dragging
            if self.drag_start and self.drag_mode:
                self.drag_end = (tile_x, tile_y)
        else:
            self.hovered_tile = None
    
    def on_mouse_press(self, x, y, button, modifiers):
        """Handle mouse clicks - wire to existing game functions."""
        if button == arcade.MOUSE_BUTTON_LEFT:
            # Check notification panel first (click-to-snap)
            click_location = self.notification_panel.handle_click(x, y)
            if click_location:
                # Snap camera to notification location
                tile_x, tile_y = click_location
                self.snap_camera_to_tile(tile_x, tile_y, self.grid.current_z)
                return
            
            # Check visitor panel (highest priority popup)
            from ui_arcade_visitor import get_visitor_panel
            visitor_panel = get_visitor_panel()
            if visitor_panel.visible and visitor_panel.handle_click(x, y):
                return
            
            # Check trader panel
            from ui_arcade_trader import get_trader_panel
            trader_panel = get_trader_panel()
            if trader_panel.visible and trader_panel.handle_click(x, y):
                return
            
            # Check native Arcade bed assignment panel
            from ui_arcade_bed import get_bed_assignment_panel
            bed_panel = get_bed_assignment_panel()
            if bed_panel.visible and bed_panel.handle_click(x, y, self.colonists):
                return
            
            # Check native Arcade workstation panel
            from ui_arcade_workstation import get_workstation_panel
            ws_panel = get_workstation_panel()
            if ws_panel.visible and ws_panel.handle_click(x, y):
                return
            
            # UI elements use screen coordinates (not world coordinates)
            # Check if click is on colonist detail panel
            if self.colonist_detail_panel.handle_click(x, y):
                return
            
            # Check if click is on left sidebar
            if self.left_sidebar.handle_click(x, y, self.colonists):
                return
            
            # Check if click is on UI
            if self.ui.handle_click(x, y):
                return
            
            # Check if clicking on bed (no tool selected)
            if self.ui.action_bar.active_tool is None:
                # Convert screen to world coordinates
                world_x, world_y = self.camera.position
                viewport_width = SCREEN_W / self.zoom_level
                viewport_height = SCREEN_H / self.zoom_level
                view_left = world_x - viewport_width / 2
                view_bottom = world_y - viewport_height / 2
                
                tile_x = int((view_left + x / self.zoom_level) // TILE_SIZE)
                tile_y = int((view_bottom + y / self.zoom_level) // TILE_SIZE)
                
                tile = self.grid.get_tile(tile_x, tile_y, self.grid.current_z)
                
                # Check for bed click
                if tile == "crash_bed":
                    from beds import get_bed_at
                    bed = get_bed_at(tile_x, tile_y, self.grid.current_z)
                    if bed:
                        bed_panel.open(tile_x, tile_y, self.grid.current_z, x, y)
                        print(f"[Bed] Opened assignment panel for bed at ({tile_x}, {tile_y})")
                        return
            
            # Check if clicking on stockpile zone (no tool selected)
            if self.ui.action_bar.active_tool is None:
                import zones as zones_module
                # Convert screen to world coordinates
                world_x, world_y = self.camera.position
                viewport_width = SCREEN_W / self.zoom_level
                viewport_height = SCREEN_H / self.zoom_level
                view_left = world_x - viewport_width / 2
                view_bottom = world_y - viewport_height / 2
                
                tile_x = int((view_left + x / self.zoom_level) // TILE_SIZE)
                tile_y = int((view_bottom + y / self.zoom_level) // TILE_SIZE)
                
                zone_id = zones_module.get_zone_id_at(tile_x, tile_y, self.grid.current_z)
                if zone_id is not None:
                    # Open stockpile filter UI (Pygame UI for now)
                    from ui import get_stockpile_filter_panel
                    panel = get_stockpile_filter_panel()
                    panel.open(zone_id, x, y)
                    print(f"[Stockpile] Opened filter config for zone {zone_id}")
                    return  # UI consumed the click
            
            # Check if we have an active tool (BUILD/ZONE mode)
            active_tool = self.ui.action_bar.active_tool
            
            if active_tool and self.hovered_tile:
                tile_x, tile_y, tile_z = self.hovered_tile
                self.drag_start = (tile_x, tile_y)
                self.drag_mode = active_tool
                
                # ALWAYS set drag_end immediately so single clicks work
                # User can still drag for walls/floors/zones, but single clicks place immediately
                self.drag_end = (tile_x, tile_y)
                
                from buildings import BUILDING_TYPES
                is_workstation = active_tool in BUILDING_TYPES and BUILDING_TYPES[active_tool].get("workstation")
                is_furniture = active_tool.startswith("furn_")
                is_single_tile = active_tool in ("stage_stairs", "fire_escape", "bridge", "door", "window") or is_workstation or is_furniture
                
                if is_single_tile:
                    print(f"[Build] Placing {active_tool} at ({tile_x}, {tile_y})")
                else:
                    print(f"[Build] Started {active_tool} at ({tile_x}, {tile_y}) - drag to extend")
                return
            
            # Default: select tile or colonist
            if self.hovered_tile:
                self.selected_tile = self.hovered_tile
                print(f"[Mouse] Selected tile: {self.selected_tile}")
                
                tile_x, tile_y, tile_z = self.hovered_tile
                
                # Check if clicked on a colonist first
                clicked_colonist = None
                for colonist in self.colonists:
                    if colonist.x == tile_x and colonist.y == tile_y and not colonist.is_dead:
                        clicked_colonist = colonist
                        break
                
                if clicked_colonist:
                    self.selected_colonist = clicked_colonist
                    print(f"[Mouse] Selected colonist: {clicked_colonist.name}")
                    # Open colonist detail panel
                    self.colonist_detail_panel.open(self.colonists, self.colonists.index(clicked_colonist))
                else:
                    self.selected_colonist = None
                    
                    # Check if clicking on a wanderer/visitor (open visitor panel)
                    from wanderers import get_wanderer_at, get_fixer_at
                    wanderer = get_wanderer_at(tile_x, tile_y, tile_z)
                    if wanderer:
                        from ui_arcade_visitor import get_visitor_panel
                        visitor_panel = get_visitor_panel()
                        
                        # Set up callbacks
                        def accept_visitor(w):
                            from wanderers import recruit_wanderer
                            from resources import get_colonist_spawn_location
                            colonist = recruit_wanderer(w)
                            if colonist:
                                self.colonists.append(colonist)
                                # Colonist already in renderer from wanderer tracking
                                # Give them a path to walk to colony center
                                colony_center = get_colonist_spawn_location()
                                colonist.current_path = colonist._calculate_path(
                                    self.grid, colony_center[0], colony_center[1], 0, self.tick_count
                                )
                                colonist.state = "idle"  # Let them take jobs or wander normally
                                print(f"[Visitor] Accepted {colonist.name}! Pathfinding to colony center at {colony_center}")
                        
                        def deny_visitor(w):
                            from wanderers import reject_wanderer
                            reject_wanderer(w)
                            print(f"[Visitor] Rejected {w['name']}")
                        
                        visitor_panel.on_accept = accept_visitor
                        visitor_panel.on_deny = deny_visitor
                        visitor_panel.open(wanderer)
                        print(f"[Visitor] Opened panel for {wanderer['name']}")
                        return
                    
                    # Check if clicking on a fixer/trader
                    fixer = get_fixer_at(tile_x, tile_y, tile_z)
                    if fixer:
                        from ui_arcade_trader import get_trader_panel
                        trader_panel = get_trader_panel()
                        trader_panel.open(fixer)
                        print(f"[Trader] Opened panel for {fixer['name']}")
                        return
                    
                    # Check if clicking on a workstation (open recipe panel)
                    tile = self.grid.get_tile(tile_x, tile_y, tile_z)
                    if tile and tile.startswith("finished_"):
                        import buildings
                        ws = buildings.get_workstation(tile_x, tile_y, tile_z)
                        if ws is not None:
                            # Open native Arcade workstation panel
                            from ui_arcade_workstation import get_workstation_panel
                            ws_panel = get_workstation_panel()
                            ws_panel.open(tile_x, tile_y, tile_z)
                            print(f"[Workstation] Opened panel for {tile} at ({tile_x}, {tile_y}, {tile_z})")
                        else:
                            print(f"[Workstation] No workstation data found at ({tile_x}, {tile_y}, {tile_z}), tile: {tile}")
        
        elif button == arcade.MOUSE_BUTTON_RIGHT:
            # Right click - cancel mode and drag
            self.drag_start = None
            self.drag_mode = None
            if self.ui.action_bar.active_mode:
                self.ui.action_bar.active_mode = None
                self.ui.action_bar.active_tool = None
                self.ui.action_bar.submenu_visible = False
                print(f"[Mouse] Cancelled mode")
            else:
                print(f"[Mouse] Right click at tile: {self.hovered_tile}")
    
    def on_mouse_release(self, x, y, button, modifiers):
        """Handle mouse release - complete drag and call existing place_* functions."""
        if button == arcade.MOUSE_BUTTON_LEFT and self.drag_start and self.drag_mode:
            if not self.drag_end:
                self.drag_start = None
                self.drag_end = None
                self.drag_mode = None
                return
            
            # Get drag end position
            end_x, end_y = self.drag_end
            start_x, start_y = self.drag_start
            end_z = self.grid.current_z
            
            # Import existing game functions
            from buildings import place_wall, place_floor, place_door
            from zones import create_stockpile_zone
            from rooms import place_roof_area
            from resources import create_gathering_job_for_node
            import jobs as jobs_module
            
            current_z = self.grid.current_z
            
            # Handle different drag modes
            if self.drag_mode == "stockpile":
                # Stockpile zone - rectangle drag
                tiles = self._get_drag_rect((start_x, start_y), (end_x, end_y))
                tiles_3d = [(tx, ty, current_z) for tx, ty in tiles]
                zone_id = create_stockpile_zone(tiles_3d, self.grid, z=current_z)
                if zone_id > 0:
                    print(f"[Zone] Created stockpile zone with {len(tiles)} tile(s)")
                else:
                    print(f"[Zone] Failed to create stockpile - no valid tiles")
            
            elif self.drag_mode == "roof":
                # Roof area - rectangle drag
                from rooms import can_place_roof_area
                can_place, reason = can_place_roof_area(self.grid, start_x, start_y, end_x, end_y, current_z)
                if can_place:
                    if place_roof_area(self.grid, start_x, start_y, end_x, end_y, current_z):
                        print(f"[Zone] Placed roof area")
                else:
                    print(f"[Zone] Cannot place roof: {reason}")
            
            elif self.drag_mode == "harvest":
                # Harvest mode - rectangle drag for resource nodes
                tiles = self._get_drag_rect((start_x, start_y), (end_x, end_y))
                jobs_created = 0
                
                for tx, ty in tiles:
                    tile = self.grid.get_tile(tx, ty, current_z)
                    # Only harvest resource nodes on ground level
                    if current_z == 0 and tile == "resource_node":
                        if create_gathering_job_for_node(jobs_module, self.grid, tx, ty):
                            jobs_created += 1
                            jobs_module.add_designation(tx, ty, current_z, "harvest", "harvest")
                
                if jobs_created > 0:
                    print(f"[Harvest] Designated {jobs_created} resource(s) for harvesting")
            
            elif self.drag_mode == "salvage":
                # Salvage mode - rectangle drag for salvage objects
                from resources import designate_salvage, get_salvage_work_time
                tiles = self._get_drag_rect((start_x, start_y), (end_x, end_y))
                designated_count = 0
                
                for tx, ty in tiles:
                    tile = self.grid.get_tile(tx, ty, 0)  # Salvage only on ground level
                    if tile == "salvage_object":
                        if designate_salvage(tx, ty):
                            # Create salvage job
                            work_time = get_salvage_work_time(tx, ty)
                            jobs_module.add_job(
                                "salvage",
                                tx, ty,
                                required=work_time,
                                category="salvage",
                                z=0,
                            )
                            jobs_module.add_designation(tx, ty, 0, "salvage", "salvage")
                            designated_count += 1
                
                if designated_count > 0:
                    print(f"[Salvage] Designated {designated_count} object(s) for salvage")
            
            elif self.drag_mode.startswith("room_"):
                # Room designation - rectangle drag
                import room_system
                tiles = self._get_drag_rect((start_x, start_y), (end_x, end_y))
                room_type_raw = self.drag_mode[5:]  # Remove "room_" prefix
                
                # Map tool names to room_system names
                room_type_map = {
                    "bedroom": "Bedroom",
                    "kitchen": "Kitchen",
                    "workshop": "Workshop",
                    "barracks": "Barracks",
                    "prison": "Prison",
                    "hospital": "Hospital",
                    "social_venue": "Social Venue",
                    "dining_hall": "Dining Hall",
                }
                room_type = room_type_map.get(room_type_raw, room_type_raw.title())
                
                success, room_id, errors = room_system.create_room(self.grid, tiles, current_z, room_type)
                if success:
                    room_data = room_system.get_room_data(room_id)
                    quality = room_data.get("quality", 0)
                    display_name = room_data.get("display_name", room_type)
                    print(f"[Room] Created {display_name} (ID {room_id}) with {len(tiles)} tiles, quality {quality}")
                else:
                    print(f"[Room] Cannot create {room_type}:")
                    for error in errors:
                        print(f"  - {error}")
            
            elif self.drag_mode.startswith("furn_"):
                # Furniture placement - single click
                from buildings import request_furniture_install
                item_id = self.drag_mode[5:]  # Remove "furn_" prefix
                if request_furniture_install(self.grid, end_x, end_y, current_z, item_id):
                    print(f"[Furniture] Requested install: {item_id} at ({end_x}, {end_y})")
                else:
                    print(f"[Furniture] Cannot install {item_id} at ({end_x}, {end_y})")
            
            else:
                # Build mode - structures and workstations
                # Determine drag type based on building
                if self.drag_mode in ("wall", "wall_advanced", "door", "bar_door", "window", "scrap_bar_counter"):
                    # Line drag for walls/doors/windows
                    tiles = self._get_drag_line((start_x, start_y), (end_x, end_y))
                elif self.drag_mode in ("floor", "stage"):
                    # Rectangle drag for floors
                    tiles = self._get_drag_rect((start_x, start_y), (end_x, end_y))
                else:
                    # Single click for workstations and special structures
                    tiles = [(end_x, end_y)]
                
                # Call existing place_* functions
                from buildings import (
                    place_wall, place_floor, place_door, place_stage, place_stage_stairs,
                    place_fire_escape, place_bridge, place_workstation_generic, BUILDING_TYPES
                )
                
                placed_count = 0
                
                for tx, ty in tiles:
                    success = False
                    
                    # Structures
                    if self.drag_mode == "wall":
                        success = place_wall(self.grid, tx, ty, current_z)
                    elif self.drag_mode == "wall_advanced":
                        from buildings import place_wall_advanced
                        success = place_wall_advanced(self.grid, tx, ty, current_z)
                    elif self.drag_mode == "floor":
                        success = place_floor(self.grid, tx, ty, current_z)
                    elif self.drag_mode == "stage":
                        success = place_stage(self.grid, tx, ty, current_z)
                    elif self.drag_mode == "stage_stairs":
                        success = place_stage_stairs(self.grid, tx, ty, current_z)
                    elif self.drag_mode == "door":
                        success = place_door(self.grid, tx, ty, current_z)
                    elif self.drag_mode == "bar_door":
                        from buildings import place_bar_door
                        success = place_bar_door(self.grid, tx, ty, current_z)
                    elif self.drag_mode == "window":
                        from buildings import place_window
                        success = place_window(self.grid, tx, ty, current_z)
                    elif self.drag_mode == "fire_escape":
                        success = place_fire_escape(self.grid, tx, ty, current_z)
                    elif self.drag_mode == "bridge":
                        success = place_bridge(self.grid, tx, ty, current_z)
                    elif self.drag_mode == "scrap_bar_counter":
                        from buildings import place_scrap_bar_counter
                        success = place_scrap_bar_counter(self.grid, tx, ty, current_z)
                    
                    # Workstations - use generic placement
                    elif self.drag_mode in BUILDING_TYPES and BUILDING_TYPES[self.drag_mode].get("workstation"):
                        success = place_workstation_generic(self.grid, tx, ty, self.drag_mode, current_z)
                    
                    if success:
                        placed_count += 1
                
                if placed_count > 0:
                    building_name = self.drag_mode.replace("_", " ").title()
                    print(f"[Build] Placed {placed_count} {building_name}(s) - colonists will construct them")
            
            # Clear drag state
            self.drag_start = None
            self.drag_end = None
            self.drag_mode = None
    
    def _get_drag_line(self, start, end):
        """Get all tiles in a line from start to end (for walls/doors)."""
        tiles = []
        x0, y0 = start
        x1, y1 = end
        
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        
        x, y = x0, y0
        while True:
            tiles.append((x, y))
            if x == x1 and y == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy
        
        return tiles
    
    def _get_drag_rect(self, start, end):
        """Get all tiles in a rectangle from start to end (for floors/zones)."""
        x0, y0 = start
        x1, y1 = end
        
        min_x = min(x0, x1)
        max_x = max(x0, x1)
        min_y = min(y0, y1)
        max_y = max(y0, y1)
        
        tiles = []
        for x in range(min_x, max_x + 1):
            for y in range(min_y, max_y + 1):
                tiles.append((x, y))
        
        return tiles
    
    def _locate_colonist(self, x: int, y: int, z: int):
        """Move camera to colonist location."""
        # Center camera on colonist
        cam_x = x * TILE_SIZE - SCREEN_W // 2
        cam_y = y * TILE_SIZE - SCREEN_H // 2
        
        # Clamp to world bounds
        max_x = max(0, GRID_W * TILE_SIZE - SCREEN_W / self.zoom_level)
        max_y = max(0, GRID_H * TILE_SIZE - SCREEN_H / self.zoom_level)
        cam_x = max(0, min(cam_x, max_x))
        cam_y = max(0, min(cam_y, max_y))
        
        self.camera.position = (cam_x, cam_y)
    
    def _draw_construction_overlays(self):
        """Draw material icons and progress bars for all construction sites.
        
        Shows visual feedback:
        - Small colored squares for materials (dim if waiting, bright if delivered)
        - Green progress bar at bottom during construction
        """
        from buildings import get_construction_site
        from jobs import get_job_at
        
        z = self.grid.current_z
        
        # Calculate visible tile range
        # Camera position is viewport CENTER, need to calculate top-left corner
        cam_x, cam_y = self.camera.position
        viewport_width = SCREEN_W / self.zoom_level
        viewport_height = SCREEN_H / self.zoom_level
        
        # Top-left corner of viewport in world coordinates
        view_left = cam_x - viewport_width / 2
        view_bottom = cam_y - viewport_height / 2
        
        start_tile_x = max(0, int(view_left // TILE_SIZE) - 1)
        start_tile_y = max(0, int(view_bottom // TILE_SIZE) - 1)
        end_tile_x = min(GRID_W, int((view_left + viewport_width) // TILE_SIZE) + 2)
        end_tile_y = min(GRID_H, int((view_bottom + viewport_height) // TILE_SIZE) + 2)
        
        # Material colors (from config.py)
        MATERIAL_COLORS = {
            "wood": {"bright": (101, 67, 33), "dim": (60, 40, 20)},
            "mineral": {"bright": (64, 164, 164), "dim": (30, 60, 60)},
            "scrap": {"bright": (120, 120, 120), "dim": (40, 40, 40)},
            "metal": {"bright": (180, 180, 200), "dim": (60, 60, 70)},
            "power": {"bright": (255, 220, 80), "dim": (80, 70, 30)},
        }
        DEFAULT_COLOR = {"bright": (100, 100, 100), "dim": (40, 40, 40)}
        PROGRESS_BAR_COLOR = (60, 220, 120)  # Green
        
        for y in range(start_tile_y, end_tile_y):
            for x in range(start_tile_x, end_tile_x):
                tile = self.grid.tiles[z][y][x]
                
                # Only draw overlays for construction tiles (not finished)
                if not tile or tile.startswith("finished_"):
                    continue
                
                # Check if this is a construction site
                site = get_construction_site(x, y, z)
                if site is None:
                    continue
                
                # World position
                world_x = x * TILE_SIZE
                world_y = y * TILE_SIZE
                
                # Draw material icons
                delivered = site.get("materials_delivered", {})
                needed = site.get("materials_needed", {})
                icon_x = world_x + 2
                icon_y = world_y + TILE_SIZE - 8  # Top of tile
                
                for res_type in needed.keys():
                    has_it = delivered.get(res_type, 0) >= needed.get(res_type, 0)
                    colors = MATERIAL_COLORS.get(res_type, DEFAULT_COLOR)
                    icon_color = colors["bright"] if has_it else colors["dim"]
                    
                    # Draw 6x6 square
                    arcade.draw_lrbt_rectangle_filled(
                        left=icon_x,
                        right=icon_x + 6,
                        bottom=icon_y,
                        top=icon_y + 6,
                        color=icon_color
                    )
                    icon_x += 8  # Space icons 8px apart
                
                # Draw progress bar
                job = get_job_at(x, y)
                if job is not None and job.required > 0:
                    progress_ratio = max(0.0, min(1.0, job.progress / job.required))
                    bar_margin = 4
                    bar_height = 4
                    bar_width = int((TILE_SIZE - 2 * bar_margin) * progress_ratio)
                    
                    if bar_width > 0:
                        # Draw progress bar at bottom of tile
                        bar_x = world_x + bar_margin
                        bar_y = world_y + bar_margin
                        
                        arcade.draw_lrbt_rectangle_filled(
                            left=bar_x,
                            right=bar_x + bar_width,
                            bottom=bar_y,
                            top=bar_y + bar_height,
                            color=PROGRESS_BAR_COLOR
                        )
    
    def _draw_zones_and_designations(self):
        """Draw stockpile zones and harvest/haul designations.
        
        Shows visual feedback:
        - Semi-transparent green overlay for stockpile zones
        - Green border for harvest designations
        - Purple border for haul designations
        """
        import zones as zones_module
        from jobs import get_designation_category
        
        z = self.grid.current_z
        
        # Calculate visible tile range
        # Camera position is viewport CENTER, need to calculate top-left corner
        cam_x, cam_y = self.camera.position
        viewport_width = SCREEN_W / self.zoom_level
        viewport_height = SCREEN_H / self.zoom_level
        
        # Top-left corner of viewport in world coordinates
        view_left = cam_x - viewport_width / 2
        view_bottom = cam_y - viewport_height / 2
        
        start_tile_x = max(0, int(view_left // TILE_SIZE) - 1)
        start_tile_y = max(0, int(view_bottom // TILE_SIZE) - 1)
        end_tile_x = min(GRID_W, int((view_left + viewport_width) // TILE_SIZE) + 2)
        end_tile_y = min(GRID_H, int((view_bottom + viewport_height) // TILE_SIZE) + 2)
        
        # Colors from config.py
        COLOR_ZONE_STOCKPILE = (60, 120, 60, 100)  # Semi-transparent green
        COLOR_JOB_CATEGORY_HARVEST = (50, 220, 80)  # Green
        COLOR_JOB_CATEGORY_HAUL = (180, 80, 255)  # Purple
        
        for y in range(start_tile_y, end_tile_y):
            for x in range(start_tile_x, end_tile_x):
                # World position
                world_x = x * TILE_SIZE
                world_y = y * TILE_SIZE
                
                # Draw stockpile zone overlay
                if zones_module.is_stockpile_zone(x, y, z):
                    # Semi-transparent green overlay
                    arcade.draw_lrbt_rectangle_filled(
                        left=world_x,
                        right=world_x + TILE_SIZE,
                        bottom=world_y,
                        top=world_y + TILE_SIZE,
                        color=COLOR_ZONE_STOCKPILE
                    )
                
                # Draw designation borders (harvest, haul, salvage)
                designation_cat = get_designation_category(x, y, z)
                if designation_cat:
                    if designation_cat in ("harvest", "salvage"):
                        border_color = COLOR_JOB_CATEGORY_HARVEST
                    elif designation_cat == "haul":
                        border_color = COLOR_JOB_CATEGORY_HAUL
                    else:
                        border_color = None
                    
                    if border_color:
                        # Draw thick border (2px)
                        arcade.draw_lrbt_rectangle_outline(
                            left=world_x,
                            right=world_x + TILE_SIZE,
                            bottom=world_y,
                            top=world_y + TILE_SIZE,
                            color=border_color,
                            border_width=2
                        )
    
    def on_resize(self, width, height):
        """Handle window resize."""
        super().on_resize(width, height)
        # Camera2D handles resize automatically


def main():
    """Entry point for Arcade version."""
    print("="*60)
    print("FRACTURED CITY - ARCADE VERSION")
    print("="*60)
    print("\nStarting GPU-accelerated renderer...")
    
    window = FracturedCityWindow()
    window.setup()
    arcade.run()


if __name__ == "__main__":
    main()
