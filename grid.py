"""Grid management and tile rendering.

Responsible for:
- storing tile state
- providing helpers to mutate/query tiles
- drawing the grid and tile contents to a Pygame surface

The tile representation is intentionally simple (string markers) so it can be
extended later to richer objects (rooms, zones, buildings, etc.).
"""

import pygame
import sprites
import config

from config import (
    GRID_W,
    GRID_H,
    GRID_Z,
    SCREEN_W,
    SCREEN_H,
    COLOR_GRID_LINES,
    COLOR_TILE_SELECTED,
    COLOR_TILE_BUILDING,
    COLOR_TILE_FINISHED_BUILDING,
    COLOR_TILE_WALL,
    COLOR_TILE_FINISHED_WALL,
    COLOR_TILE_STREET,
    COLOR_TILE_STREET_DESIGNATED,
    COLOR_TILE_STREET_CRACKED,
    COLOR_TILE_STREET_SCAR,
    COLOR_TILE_STREET_RIPPED,
    COLOR_TILE_SIDEWALK,
    COLOR_TILE_SIDEWALK_DESIGNATED,
    COLOR_TILE_SCORCHED,
    COLOR_TILE_DEBRIS,
    COLOR_TILE_WEEDS,
    COLOR_TILE_PROP_BARREL,
    COLOR_TILE_PROP_SIGN,
    COLOR_TILE_PROP_SCRAP,
    COLOR_TILE_DIRT,
    COLOR_TILE_GRASS,
    COLOR_TILE_ROCK,
    COLOR_TILE_EMPTY,
    COLOR_CONSTRUCTION_PROGRESS,
    COLOR_RESOURCE_NODE_WOOD,
    COLOR_RESOURCE_NODE_SCRAP,
    COLOR_RESOURCE_NODE_MINERAL,
    COLOR_RESOURCE_NODE_METAL,
    COLOR_RESOURCE_NODE_POWER,
    COLOR_RESOURCE_NODE_RAW_FOOD,
    COLOR_RESOURCE_NODE_COOKED_MEAL,
    COLOR_RESOURCE_NODE_DEFAULT,
    COLOR_NODE_RESERVED,
    COLOR_NODE_IN_PROGRESS,
    COLOR_NODE_DEPLETED,
    COLOR_RESOURCE_PILE,
    COLOR_JOB_CATEGORY_WALL,
    COLOR_JOB_CATEGORY_HARVEST,
    COLOR_JOB_CATEGORY_CONSTRUCTION,
    COLOR_JOB_CATEGORY_HAUL,
    COLOR_ZONE_STOCKPILE,
    COLOR_ZONE_STOCKPILE_BORDER,
)
from jobs import get_job_at, get_designation_category
import resources
import zones
import buildings
import rooms


class Grid:
    """Logical grid backing the world tiles.

    For now tiles are simple string markers:
    - "empty"
    - "building"
    - "finished_building"
    - "resource_node"
    - "resource_pile"

    Walkability is tracked separately to support pathfinding.
    
    The grid supports multiple Z-levels:
    - z=0: Ground level (main gameplay)
    - z=1: Rooftop level (roof tiles from enclosed rooms)
    """

    def __init__(self) -> None:
        self.width = GRID_W
        self.height = GRID_H
        self.depth = GRID_Z  # Number of Z-levels
        
        # 3D tile array: tiles[z][y][x]
        self.tiles: list[list[list[str]]] = [
            [["empty" for _ in range(self.width)] for _ in range(self.height)]
            for _ in range(self.depth)
        ]
        
        # 3D walkability map: walkable[z][y][x]
        # Z=0 (ground) defaults to walkable
        # Z>0 (upper levels) default to NOT walkable - must be explicitly allowed
        self.walkable: list[list[list[bool]]] = []
        for z in range(self.depth):
            if z == 0:
                # Ground level - all tiles walkable by default
                self.walkable.append([[True for _ in range(self.width)] for _ in range(self.height)])
            else:
                # Upper levels - all tiles blocked by default until allowed
                self.walkable.append([[False for _ in range(self.width)] for _ in range(self.height)])
        
        # Environmental parameters for each tile: env_data[z][y][x]
        # Each tile has: interference, pressure, echo, integrity, is_outside, room_id, exit_count
        self.env_data: list[list[list[dict]]] = [
            [[self._default_env_data() for _ in range(self.width)] for _ in range(self.height)]
            for _ in range(self.depth)
        ]
        
        # Base tiles under furniture - stores original tile type before furniture placement
        # Key: (x, y, z), Value: original tile type (e.g., "finished_floor", "finished_stage")
        self.base_tiles: dict[tuple[int, int, int], str] = {}
        
        # Current view level (for rendering)
        self.current_z = 0
        
        # Camera system for viewport (world coordinates in pixels)
        self.camera_x = 0
        self.camera_y = 0

    def _default_env_data(self) -> dict:
        """Create default environmental data for a tile."""
        return {
            "interference": 0.0,
            "pressure": 0.0,
            "echo": 0.0,
            "integrity": 1.0,
            "is_outside": True,
            "room_id": None,
            "exit_count": 0,
        }
    
    def get_env_data(self, x: int, y: int, z: int = 0) -> dict:
        """Get environmental data for a tile."""
        if not self.in_bounds(x, y, z):
            return self._default_env_data()
        return self.env_data[z][y][x]
    
    def set_env_param(self, x: int, y: int, z: int, param: str, value) -> None:
        """Set a specific environmental parameter for a tile."""
        if not self.in_bounds(x, y, z):
            return
        self.env_data[z][y][x][param] = value
    
    def update_env_data(self, x: int, y: int, z: int, **kwargs) -> None:
        """Update multiple environmental parameters for a tile."""
        if not self.in_bounds(x, y, z):
            return
        for key, value in kwargs.items():
            self.env_data[z][y][x][key] = value
    
    def calculate_exit_count(self, x: int, y: int, z: int) -> int:
        """Calculate number of adjacent walkable tiles."""
        count = 0
        for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
            nx, ny = x + dx, y + dy
            if self.in_bounds(nx, ny, z) and self.is_walkable(nx, ny, z):
                count += 1
        return count

    def in_bounds(self, x: int, y: int, z: int = 0) -> bool:
        """Return True if (x, y, z) lies inside the grid."""
        return 0 <= x < self.width and 0 <= y < self.height and 0 <= z < self.depth

    def set_tile(self, x: int, y: int, value: str, z: int = 0) -> None:
        """Set the logical value of a tile if coordinates are valid.
        
        Automatically updates walkability for building tiles and initializes environmental parameters.
        """
        if self.in_bounds(x, y, z):
            self.tiles[z][y][x] = value
            # Only finished buildings/walls block movement, not those under construction
            # Doors are handled specially - they can be opened
            # Fire escapes are walkable (they're transition points)
            # roof tiles are NOT walkable - must be converted to roof_access first
            if value in ("finished_building", "finished_wall", "finished_wall_advanced", "roof", "finished_salvagers_bench", "finished_generator", "finished_stove", "finished_gutter_forge", "finished_skinshop_loom", "finished_cortex_spindle", "finished_barracks"):
                self.walkable[z][y][x] = False
            elif value == "finished_window":
                # Windows are passable (like doors) - colonists can climb through
                self.walkable[z][y][x] = True
            elif value in ("empty", "building", "wall", "wall_advanced", "door", "floor", "finished_floor", "roof_floor", "roof_access", "fire_escape", "finished_fire_escape", "window_tile", "fire_escape_platform", "window", "bridge", "finished_bridge", "salvagers_bench", "generator", "stove", "gutter_forge", "skinshop_loom", "cortex_spindle", "barracks", "street", "street_cracked", "street_scar", "street_ripped", "street_designated", "sidewalk", "sidewalk_designated", "debris", "weeds", "prop_barrel", "prop_sign", "prop_scrap", "dirt", "grass", "rock", "scorched", "gutter_slab", "crash_bed"):
                # window_tile: passable wall with fire escape window
                # fire_escape_platform: external platform for fire escape
                # roof_access: walkable/buildable rooftop tile (player-allowed)
                # roof_floor: legacy walkable roof (kept for compatibility)
                # bridge/finished_bridge: walkable connections between buildings
                # street/street_designated: walkable city streets
                # sidewalk/debris/weeds/props: decorative, walkable
                # dirt/grass/rock: natural ground tiles
                self.walkable[z][y][x] = True
            
            # Initialize environmental parameters based on tile type
            self._init_env_params_for_tile(x, y, z, value)
    
    def _init_env_params_for_tile(self, x: int, y: int, z: int, tile_type: str) -> None:
        """Initialize environmental parameters based on tile type."""
        # Ruins have degraded environmental values
        if tile_type in ("debris", "weeds", "prop_barrel", "prop_sign", "prop_scrap"):
            self.update_env_data(x, y, z,
                echo=0.3,
                integrity=0.4,
                interference=0.1,
                is_outside=True
            )
        # New construction has clean values
        elif tile_type in ("building", "wall", "wall_advanced", "floor", "door", "window",
                          "salvagers_bench", "generator", "stove", "gutter_forge", "skinshop_loom", "cortex_spindle", "bridge", "fire_escape", "gutter_slab", "crash_bed"):
            self.update_env_data(x, y, z,
                echo=0.0,
                integrity=1.0,
                interference=0.0,
                is_outside=False  # Construction is typically inside
            )
        # Finished construction maintains clean values
        elif tile_type in ("finished_building", "finished_wall", "finished_wall_advanced",
                          "finished_floor", "finished_window", "finished_bridge",
                          "finished_salvagers_bench", "finished_generator", "finished_stove",
                          "finished_gutter_forge", "finished_skinshop_loom", "finished_cortex_spindle"):
            self.update_env_data(x, y, z,
                echo=0.0,
                integrity=1.0,
                interference=0.0,
                is_outside=False  # Finished buildings are inside
            )
        # Outside tiles keep defaults
        else:
            # Already has default values, but ensure is_outside is True
            self.set_env_param(x, y, z, "is_outside", True)
        
        # Update exit count
        exit_count = self.calculate_exit_count(x, y, z)
        self.set_env_param(x, y, z, "exit_count", exit_count)

    def get_tile(self, x: int, y: int, z: int = 0) -> str | None:
        """Get the tile value or None if out of bounds."""
        if self.in_bounds(x, y, z):
            return self.tiles[z][y][x]
        return None

    def is_walkable(self, x: int, y: int, z: int = 0) -> bool:
        """Return True if colonists can walk on this tile."""
        if not self.in_bounds(x, y, z):
            return False
        return self.walkable[z][y][x]
    
    def set_current_z(self, z: int) -> None:
        """Set the current view Z-level."""
        if 0 <= z < self.depth:
            self.current_z = z
    
    def get_current_z(self) -> int:
        """Get the current view Z-level."""
        return self.current_z
    
    # --- Camera System ---
    
    def pan_camera(self, dx: int, dy: int) -> None:
        """Pan the camera by (dx, dy) pixels. Clamps to world bounds."""
        # Calculate world size in pixels
        world_width_px = self.width * config.TILE_SIZE
        world_height_px = self.height * config.TILE_SIZE
        
        # Update camera position directly
        self.camera_x += dx
        self.camera_y += dy
        
        # Clamp to world bounds
        max_camera_x = max(0, world_width_px - SCREEN_W)
        max_camera_y = max(0, world_height_px - SCREEN_H)
        
        self.camera_x = max(0, min(self.camera_x, max_camera_x))
        self.camera_y = max(0, min(self.camera_y, max_camera_y))
    
    def center_camera_on(self, tile_x: int, tile_y: int) -> None:
        """Center the camera on a specific tile coordinate."""
        # Calculate world size in pixels
        world_width_px = self.width * config.TILE_SIZE
        world_height_px = self.height * config.TILE_SIZE
        
        # Calculate target camera position (tile center - half screen)
        target_x = tile_x * config.TILE_SIZE + config.TILE_SIZE // 2 - SCREEN_W // 2
        target_y = tile_y * config.TILE_SIZE + config.TILE_SIZE // 2 - SCREEN_H // 2
        
        # Clamp to world bounds
        max_camera_x = max(0, world_width_px - SCREEN_W)
        max_camera_y = max(0, world_height_px - SCREEN_H)
        
        self.camera_x = max(0, min(target_x, max_camera_x))
        self.camera_y = max(0, min(target_y, max_camera_y))
    
    def screen_to_world(self, screen_x: int, screen_y: int) -> tuple[int, int]:
        """Convert screen coordinates to world tile coordinates.
        
        Returns (tile_x, tile_y) in world space.
        """
        world_x = screen_x + int(self.camera_x)
        world_y = screen_y + int(self.camera_y)
        tile_x = world_x // config.TILE_SIZE
        tile_y = world_y // config.TILE_SIZE
        return (tile_x, tile_y)
    
    # --- Visual Helpers ---
    
    def _get_tile_seed(self, x: int, y: int, z: int) -> int:
        """Generate a deterministic seed for tile variation based on position."""
        return (x * 7919 + y * 6547 + z * 4973) & 0xFFFFFFFF
    
    def _try_draw_tile_sprite(self, surface: pygame.Surface, tile_type: str, rect: pygame.Rect, x: int, y: int, z: int, use_construction_tint: bool = False) -> bool:
        """Try to draw a tile sprite. Returns True if sprite was drawn, False if should use procedural.
        
        Args:
            surface: Surface to draw on
            tile_type: Type of tile
            rect: Rectangle to draw in
            x, y, z: Tile coordinates (for variation)
            use_construction_tint: If True, try to load finished sprite with construction tint
            
        Returns:
            True if sprite was drawn, False if procedural drawing should be used
        """
        import config
        
        # If construction tint requested, try to load the finished version with tint
        if use_construction_tint:
            # For resource nodes, use the same sprite name with tint (don't add "finished_")
            if "_node" in tile_type:
                tile_sprite = sprites.get_tile_sprite(tile_type, x, y, z, config.TILE_SIZE, apply_construction_tint=True)
            else:
                # Map construction tile to finished version
                finished_type = tile_type.replace("wall", "finished_wall").replace("floor", "finished_floor").replace("door", "finished_door").replace("window", "finished_window").replace("bridge", "finished_bridge").replace("fire_escape", "finished_fire_escape")
                if not finished_type.startswith("finished_"):
                    finished_type = "finished_" + tile_type
                
                tile_sprite = sprites.get_tile_sprite(finished_type, x, y, z, config.TILE_SIZE, apply_construction_tint=True)
            
            if tile_sprite:
                surface.blit(tile_sprite, rect.topleft)
                return True
        
        # Normal sprite loading (no tint)
        tile_sprite = sprites.get_tile_sprite(tile_type, x, y, z, config.TILE_SIZE)
        if tile_sprite:
            surface.blit(tile_sprite, rect.topleft)
            return True
        return False
    
    def _get_tile_color_variation(self, base_color: tuple[int, int, int], x: int, y: int, z: int, variation: int = 10) -> tuple[int, int, int]:
        """Add subtle random color variation to a base color.
        
        Args:
            base_color: RGB tuple
            x, y, z: Tile position
            variation: Max variation amount (default 10)
        
        Returns:
            Modified RGB tuple with subtle variation
        """
        import random
        seed = self._get_tile_seed(x, y, z)
        rng = random.Random(seed)
        
        r = max(0, min(255, base_color[0] + rng.randint(-variation, variation)))
        g = max(0, min(255, base_color[1] + rng.randint(-variation, variation)))
        b = max(0, min(255, base_color[2] + rng.randint(-variation, variation)))
        
        return (r, g, b)
    
    def _get_tile_variant(self, x: int, y: int, z: int, max_variant: int, salt: int = 0) -> int:
        """Return a deterministic variant index for a tile position."""
        import random
        if max_variant <= 0:
            return 0
        seed = self._get_tile_seed(x, y, z) ^ salt
        rng = random.Random(seed)
        return rng.randint(0, max_variant - 1)
    
    def _get_floor_variant(self, x: int, y: int, z: int) -> int:
        """Get floor pattern variant (0-2) for this tile position."""
        return self._get_tile_variant(x, y, z, 3, salt=0xF10A4)
    
    def _draw_mineral_node(self, surface: pygame.Surface, rect: pygame.Rect, x: int, y: int, z: int, depleted: bool) -> None:
        """Render a mineral resource node with one of several rock variants."""
        # Try to load sprite first (mineral_node_0 through mineral_node_7)
        if self._try_draw_tile_sprite(surface, "mineral_node", rect, x, y, z, use_construction_tint=depleted):
            return
        
        # Fallback to procedural rendering
        import random
        
        base_palette = [
            (70, 72, 78),
            (94, 96, 105),
            (120, 122, 130),
        ]
        palette_index = self._get_tile_variant(x, y, z, len(base_palette), salt=0x5B1C3)
        base_color = base_palette[palette_index]
        
        color = self._get_tile_color_variation(base_color, x, y, z, 10)
        if depleted:
            color = (color[0] // 3, color[1] // 3, color[2] // 3)
        shadow = (max(0, color[0] - 35), max(0, color[1] - 35), max(0, color[2] - 35))
        highlight_delta = 12 if depleted else 45
        highlight = (
            min(255, color[0] + highlight_delta),
            min(255, color[1] + highlight_delta),
            min(255, color[2] + highlight_delta),
        )
        
        pygame.draw.rect(surface, shadow, rect)
        
        seed = self._get_tile_seed(x, y, z)
        rng = random.Random(seed ^ 0x9E3779B9)
        variant = self._get_tile_variant(x, y, z, 3, salt=0xA713F)
        
        if variant == 0:
            # Jagged shard cluster
            shard_points = [
                (rect.left + 4, rect.bottom - 3),
                (rect.left + 6 + rng.randint(0, 2), rect.top + 10),
                (rect.centerx, rect.top + 4 + rng.randint(0, 2)),
                (rect.right - 5, rect.centery - 4),
                (rect.right - 3, rect.bottom - 6),
                (rect.centerx - 4, rect.bottom - 2),
            ]
            pygame.draw.polygon(surface, color, shard_points)
            pygame.draw.lines(surface, highlight, False, shard_points[1:-1], 2)
        elif variant == 1:
            # Veined slab with mineral streaks
            slab_rect = pygame.Rect(rect.left + 3, rect.top + 5, rect.width - 6, rect.height - 8)
            pygame.draw.rect(surface, color, slab_rect)
            for offset in (-4, 0, 4):
                start = (slab_rect.left + 2, slab_rect.bottom - 4 + offset)
                end = (slab_rect.right - 2, slab_rect.top + 6 + offset // 2)
                pygame.draw.line(surface, highlight if offset == 0 else shadow, start, end, 2)
        else:
            # Rounded boulder cluster
            centers = [
                (rect.left + 8 + rng.randint(-1, 1), rect.bottom - 8 + rng.randint(-1, 1)),
                (rect.centerx + rng.randint(-2, 2), rect.centery + rng.randint(-2, 2)),
                (rect.right - 8 + rng.randint(-1, 1), rect.bottom - 10 + rng.randint(-1, 1)),
            ]
            radii = [7, 5, 4]
            for idx, (cx, cy) in enumerate(centers):
                radius = max(2, radii[idx])
                body_color = color if idx == 0 else (
                    max(0, color[0] - 15 * idx),
                    max(0, color[1] - 15 * idx),
                    max(0, color[2] - 15 * idx),
                )
                pygame.draw.circle(surface, body_color, (cx, cy), radius)
                if not depleted:
                    pygame.draw.circle(surface, highlight, (cx - 2, cy - 2), max(1, radius - 3), 1)
        
        if not depleted:
            # Small glint in top corner
            glint_center = (rect.right - 6, rect.top + 6)
            pygame.draw.circle(surface, highlight, glint_center, 2)
    
    def _draw_wood_node(self, surface: pygame.Surface, rect: pygame.Rect, x: int, y: int, z: int, depleted: bool) -> None:
        """Render a wood resource node with tree/lumber variants."""
        # Try to load sprite first (wood_node_0 through wood_node_5)
        if self._try_draw_tile_sprite(surface, "wood_node", rect, x, y, z, use_construction_tint=depleted):
            return
        
        # Fallback to procedural rendering
        import random
        
        # Brown palette for wood
        base_palette = [
            (100, 70, 40),   # Dark brown
            (120, 85, 50),   # Medium brown
            (90, 60, 35),    # Reddish brown
        ]
        palette_index = self._get_tile_variant(x, y, z, len(base_palette), salt=0x1D001)
        base_color = base_palette[palette_index]
        
        color = self._get_tile_color_variation(base_color, x, y, z, 12)
        if depleted:
            color = (color[0] // 3, color[1] // 3, color[2] // 3)
        
        shadow = (max(0, color[0] - 30), max(0, color[1] - 25), max(0, color[2] - 20))
        highlight = (min(255, color[0] + 35), min(255, color[1] + 30), min(255, color[2] + 25))
        foliage = (50, 90, 45) if not depleted else (20, 35, 18)
        foliage_light = (70, 120, 60) if not depleted else (28, 48, 24)
        
        # Background
        pygame.draw.rect(surface, shadow, rect)
        
        seed = self._get_tile_seed(x, y, z)
        rng = random.Random(seed ^ 0x1E33)
        variant = self._get_tile_variant(x, y, z, 4, salt=0xF0E15)
        
        if variant == 0:
            # Single tree with foliage
            trunk_w = 4 + rng.randint(0, 2)
            trunk_h = 12 + rng.randint(0, 4)
            trunk_x = rect.centerx - trunk_w // 2 + rng.randint(-2, 2)
            trunk_rect = pygame.Rect(trunk_x, rect.bottom - trunk_h - 2, trunk_w, trunk_h)
            pygame.draw.rect(surface, color, trunk_rect)
            pygame.draw.line(surface, highlight, (trunk_rect.left, trunk_rect.top), 
                           (trunk_rect.left, trunk_rect.bottom), 1)
            # Foliage (triangle/circle cluster)
            foliage_y = trunk_rect.top - 4
            pygame.draw.circle(surface, foliage, (trunk_x + trunk_w // 2, foliage_y), 8)
            pygame.draw.circle(surface, foliage_light, (trunk_x + trunk_w // 2 - 2, foliage_y - 2), 3)
        elif variant == 1:
            # Two small trees
            for offset in [-6, 6]:
                tx = rect.centerx + offset + rng.randint(-1, 1)
                trunk_rect = pygame.Rect(tx - 2, rect.bottom - 10, 3, 8)
                pygame.draw.rect(surface, color, trunk_rect)
                pygame.draw.circle(surface, foliage, (tx, rect.bottom - 14), 5)
                pygame.draw.circle(surface, foliage_light, (tx - 1, rect.bottom - 15), 2)
        elif variant == 2:
            # Log pile (harvested look)
            log_color = color
            for i in range(3):
                log_y = rect.bottom - 6 - i * 5
                log_w = 18 - i * 3
                log_rect = pygame.Rect(rect.centerx - log_w // 2, log_y, log_w, 4)
                pygame.draw.ellipse(surface, log_color, log_rect)
                pygame.draw.ellipse(surface, highlight, log_rect, 1)
                log_color = (max(0, log_color[0] - 10), max(0, log_color[1] - 8), max(0, log_color[2] - 5))
        else:
            # Stump with scattered wood
            stump_rect = pygame.Rect(rect.centerx - 5, rect.centery, 10, 8)
            pygame.draw.ellipse(surface, color, stump_rect)
            pygame.draw.ellipse(surface, highlight, stump_rect, 1)
            # Rings on top
            pygame.draw.circle(surface, shadow, (rect.centerx, rect.centery + 2), 3, 1)
            # Scattered planks
            for _ in range(2):
                px = rect.left + 4 + rng.randint(0, 16)
                py = rect.top + 4 + rng.randint(0, 8)
                pygame.draw.rect(surface, highlight, (px, py, 6, 2))
    
    def _draw_scrap_node(self, surface: pygame.Surface, rect: pygame.Rect, x: int, y: int, z: int, depleted: bool) -> None:
        """Render a scrap resource node with junk pile variants."""
        import random
        
        # Gray/rust palette for scrap
        base_palette = [
            (90, 85, 80),    # Gray
            (110, 90, 75),   # Rusty
            (80, 80, 90),    # Blue-gray
        ]
        palette_index = self._get_tile_variant(x, y, z, len(base_palette), salt=0x5C4A9)
        base_color = base_palette[palette_index]
        
        color = self._get_tile_color_variation(base_color, x, y, z, 10)
        if depleted:
            color = (color[0] // 3, color[1] // 3, color[2] // 3)
        
        shadow = (max(0, color[0] - 25), max(0, color[1] - 25), max(0, color[2] - 25))
        highlight = (min(255, color[0] + 40), min(255, color[1] + 35), min(255, color[2] + 30))
        rust = (min(255, color[0] + 30), max(0, color[1] - 10), max(0, color[2] - 20))
        
        pygame.draw.rect(surface, shadow, rect)
        
        seed = self._get_tile_seed(x, y, z)
        rng = random.Random(seed ^ 0x10A1C)
        variant = self._get_tile_variant(x, y, z, 3, salt=0x911E)
        
        if variant == 0:
            # Twisted metal pile
            for i in range(4):
                sx = rect.left + 3 + rng.randint(0, 14)
                sy = rect.top + 5 + rng.randint(0, 12)
                sw = 4 + rng.randint(0, 6)
                sh = 2 + rng.randint(0, 2)
                piece_color = rust if rng.random() < 0.4 else color
                pygame.draw.rect(surface, piece_color, (sx, sy, sw, sh))
            # Central chunk
            pygame.draw.rect(surface, color, (rect.centerx - 4, rect.centery - 2, 8, 6))
            pygame.draw.rect(surface, highlight, (rect.centerx - 4, rect.centery - 2, 8, 6), 1)
        elif variant == 1:
            # Stacked debris
            for i in range(3):
                dy = rect.bottom - 5 - i * 6
                dw = 16 - i * 3
                debris_rect = pygame.Rect(rect.centerx - dw // 2, dy, dw, 5)
                piece_color = color if i % 2 == 0 else rust
                pygame.draw.rect(surface, piece_color, debris_rect)
                pygame.draw.line(surface, highlight, debris_rect.topleft, debris_rect.topright, 1)
        else:
            # Scattered parts
            parts = [(5, 6, 6, 4), (12, 4, 5, 5), (8, 12, 7, 3), (15, 10, 4, 6), (3, 14, 8, 3)]
            for px, py, pw, ph in parts:
                piece_color = rust if rng.random() < 0.3 else color
                pygame.draw.rect(surface, piece_color, (rect.left + px, rect.top + py, pw, ph))
            # Highlight on top piece
            pygame.draw.rect(surface, highlight, (rect.left + 12, rect.top + 4, 5, 5), 1)
        
        if not depleted:
            # Metallic glint
            pygame.draw.circle(surface, (200, 200, 210), (rect.right - 5, rect.top + 5), 2)
    
    def _draw_stockpile_resource(self, surface: pygame.Surface, rect: pygame.Rect, 
                                  res_type: str, amount: int, x: int, y: int, z: int) -> None:
        """Draw a resource stack on a stockpile tile matching the map node style."""
        import random
        
        fill_ratio = min(1.0, amount / 10.0)
        seed = self._get_tile_seed(x, y, z)
        rng = random.Random(seed)
        
        if res_type == "wood":
            # Log pile that grows
            num_logs = 1 + int(fill_ratio * 4)
            log_color = (120, 85, 50)
            highlight = (150, 115, 75)
            for i in range(num_logs):
                log_y = rect.centery + 6 - i * 4
                log_w = 12 + int(fill_ratio * 6)
                log_rect = pygame.Rect(rect.centerx - log_w // 2, log_y, log_w, 3)
                pygame.draw.ellipse(surface, log_color, log_rect)
                pygame.draw.ellipse(surface, highlight, log_rect, 1)
        elif res_type == "scrap":
            # Junk pile that grows
            num_pieces = 2 + int(fill_ratio * 4)
            for i in range(num_pieces):
                px = rect.centerx - 6 + rng.randint(0, 12)
                py = rect.centery - 4 + rng.randint(0, 8) - int(fill_ratio * 4)
                pw = 3 + rng.randint(0, 4)
                ph = 2 + rng.randint(0, 2)
                piece_color = (110, 90, 75) if rng.random() < 0.4 else (90, 85, 80)
                pygame.draw.rect(surface, piece_color, (px, py, pw, ph))
            pygame.draw.rect(surface, (130, 125, 120), (rect.centerx - 3, rect.centery - 2, 6, 4), 1)
        elif res_type == "mineral":
            # Rock pile that grows
            num_rocks = 1 + int(fill_ratio * 3)
            base_y = rect.centery + 4
            for i in range(num_rocks):
                rx = rect.centerx - 4 + (i % 2) * 4 + rng.randint(-2, 2)
                ry = base_y - i * 4
                radius = 4 + int(fill_ratio * 2)
                rock_color = (94, 96, 105)
                pygame.draw.circle(surface, rock_color, (rx, ry), radius)
                pygame.draw.circle(surface, (130, 132, 145), (rx - 1, ry - 1), radius - 2, 1)
        elif res_type == "metal":
            # Metal ingots stacked
            num_bars = 1 + int(fill_ratio * 3)
            bar_color = (160, 165, 180)
            highlight = (200, 205, 220)
            for i in range(num_bars):
                bar_y = rect.centery + 4 - i * 5
                bar_rect = pygame.Rect(rect.centerx - 6, bar_y, 12, 4)
                pygame.draw.rect(surface, bar_color, bar_rect)
                pygame.draw.line(surface, highlight, bar_rect.topleft, bar_rect.topright, 1)
        elif res_type == "power":
            # Glowing power cells
            num_cells = 1 + int(fill_ratio * 2)
            for i in range(num_cells):
                cx = rect.centerx - 4 + i * 4
                cy = rect.centery + 2 - i * 3
                pygame.draw.rect(surface, (200, 180, 60), (cx - 3, cy - 4, 6, 8))
                pygame.draw.rect(surface, (255, 240, 100), (cx - 2, cy - 2, 4, 4))
        elif res_type == "raw_food":
            # Food crates/sacks
            size = 6 + int(fill_ratio * 6)
            pygame.draw.rect(surface, (140, 160, 90), 
                           (rect.centerx - size // 2, rect.centery - size // 2, size, size))
            pygame.draw.rect(surface, (170, 195, 110), 
                           (rect.centerx - size // 2, rect.centery - size // 2, size, size), 1)
        elif res_type == "cooked_meal":
            # Meal containers
            size = 6 + int(fill_ratio * 6)
            pygame.draw.ellipse(surface, (180, 140, 90), 
                              (rect.centerx - size // 2, rect.centery - size // 2 + 2, size, size - 2))
            pygame.draw.ellipse(surface, (210, 170, 110), 
                              (rect.centerx - size // 2, rect.centery - size // 2 + 2, size, size - 2), 1)
        else:
            # Generic box
            size = int(8 + 16 * fill_ratio)
            stack_rect = pygame.Rect(rect.centerx - size // 2, rect.centery - size // 2, size, size)
            pygame.draw.rect(surface, (150, 150, 150), stack_rect)
            pygame.draw.rect(surface, (200, 200, 200), stack_rect, 1)
    
    def _draw_street_tile(self, surface: pygame.Surface, rect: pygame.Rect, x: int, y: int, z: int, tile_type: str) -> None:
        """Render street tiles with cobblestone pattern and damage variations."""
        import random
        
        base_colors = {
            "street": COLOR_TILE_STREET,
            "street_cracked": COLOR_TILE_STREET_CRACKED,
            "street_scar": COLOR_TILE_STREET_SCAR,
            "street_ripped": COLOR_TILE_STREET_RIPPED,
        }
        base_color = base_colors.get(tile_type, COLOR_TILE_STREET)
        color = self._get_tile_color_variation(base_color, x, y, z, 4)
        pygame.draw.rect(surface, color, rect)
        
        seed = self._get_tile_seed(x, y, z) ^ 0x57F9A
        rng = random.Random(seed)
        
        # Cobblestone/rock pattern for all street types
        dark_grout = (max(0, color[0] - 12), max(0, color[1] - 12), max(0, color[2] - 14))
        light_stone = (min(255, color[0] + 8), min(255, color[1] + 10), min(255, color[2] + 12))
        
        # Draw irregular stone pattern
        variant = self._get_tile_variant(x, y, z, 3, salt=0xC0BB1E)
        
        if variant == 0:
            # Horizontal stones
            pygame.draw.line(surface, dark_grout, (rect.left, rect.top + 8), (rect.right, rect.top + 8), 1)
            pygame.draw.line(surface, dark_grout, (rect.left, rect.bottom - 8), (rect.right, rect.bottom - 8), 1)
            pygame.draw.line(surface, dark_grout, (rect.centerx, rect.top), (rect.centerx, rect.top + 8), 1)
            pygame.draw.line(surface, dark_grout, (rect.centerx - 6, rect.top + 8), (rect.centerx - 6, rect.bottom - 8), 1)
            pygame.draw.line(surface, dark_grout, (rect.centerx + 6, rect.bottom - 8), (rect.centerx + 6, rect.bottom), 1)
        elif variant == 1:
            # Offset brick pattern
            pygame.draw.line(surface, dark_grout, (rect.left, rect.centery), (rect.right, rect.centery), 1)
            pygame.draw.line(surface, dark_grout, (rect.left + 6, rect.top), (rect.left + 6, rect.centery), 1)
            pygame.draw.line(surface, dark_grout, (rect.right - 6, rect.top), (rect.right - 6, rect.centery), 1)
            pygame.draw.line(surface, dark_grout, (rect.centerx, rect.centery), (rect.centerx, rect.bottom), 1)
        else:
            # Irregular stones
            pygame.draw.line(surface, dark_grout, (rect.left + 4, rect.top), (rect.left + 4, rect.bottom), 1)
            pygame.draw.line(surface, dark_grout, (rect.right - 5, rect.top), (rect.right - 5, rect.bottom), 1)
            pygame.draw.line(surface, dark_grout, (rect.left + 4, rect.top + 10), (rect.right - 5, rect.top + 10), 1)
            pygame.draw.line(surface, dark_grout, (rect.left, rect.bottom - 6), (rect.left + 4, rect.bottom - 6), 1)
        
        # Add subtle highlight on some stones
        if rng.random() < 0.3:
            hx = rect.left + rng.randint(3, rect.width - 6)
            hy = rect.top + rng.randint(3, rect.height - 6)
            pygame.draw.rect(surface, light_stone, (hx, hy, 3, 2))
        
        if tile_type == "street":
            return
        
        crack_color = (max(0, color[0] - 20), max(0, color[1] - 20), max(0, color[2] - 22))
        highlight = (min(255, color[0] + 25), min(255, color[1] + 22), min(255, color[2] + 20))
        
        if tile_type == "street_cracked":
            # Several fine cracks
            for _ in range(3):
                start = (rect.left + rng.randint(2, rect.width - 2), rect.top + rng.randint(2, rect.height - 2))
                end = (start[0] + rng.randint(-6, 6), start[1] + rng.randint(-6, 6))
                pygame.draw.line(surface, crack_color, start, end, 1)
        elif tile_type == "street_scar":
            # One or two deep scars with lighter edges
            for _ in range(2):
                scar_rect = pygame.Rect(
                    rect.left + rng.randint(2, 6),
                    rect.top + rng.randint(2, 6),
                    rect.width - rng.randint(6, 12),
                    3
                )
                pygame.draw.rect(surface, crack_color, scar_rect)
                pygame.draw.line(surface, highlight, scar_rect.topleft, scar_rect.topright, 1)
        elif tile_type == "street_ripped":
            # Jagged hole exposing a darker sub-layer
            rip_points = [
                (rect.left + rng.randint(2, 6), rect.top + rng.randint(8, rect.height - 4)),
                (rect.left + rng.randint(rect.width // 3, rect.width // 2), rect.top + rng.randint(2, rect.height - 2)),
                (rect.right - rng.randint(2, 6), rect.bottom - rng.randint(4, 8)),
                (rect.centerx, rect.bottom - rng.randint(2, 4)),
            ]
            hole_color = (max(0, color[0] - 25), max(0, color[1] - 25), max(0, color[2] - 28))
            pygame.draw.polygon(surface, hole_color, rip_points)
            pygame.draw.lines(surface, highlight, True, rip_points, 2)
            
            # Mineral flecks
            from config import COLOR_RESOURCE_NODE_MINERAL
            for _ in range(3):
                cx = rect.left + rng.randint(3, rect.width - 4)
                cy = rect.top + rng.randint(3, rect.height - 4)
                pygame.draw.circle(surface, COLOR_RESOURCE_NODE_MINERAL, (cx, cy), 2)
    
    def _draw_sidewalk_tile(self, surface: pygame.Surface, rect: pygame.Rect, x: int, y: int, z: int, designated: bool = False) -> None:
        """Render sidewalk tiles with brick pattern."""
        import random
        
        base_color = COLOR_TILE_SIDEWALK_DESIGNATED if designated else COLOR_TILE_SIDEWALK
        color = self._get_tile_color_variation(base_color, x, y, z, 3)
        pygame.draw.rect(surface, color, rect)
        
        # Brick pattern - darker mortar lines
        mortar = (max(0, color[0] - 10), max(0, color[1] - 10), max(0, color[2] - 12))
        light_brick = (min(255, color[0] + 6), min(255, color[1] + 5), min(255, color[2] + 4))
        
        seed = self._get_tile_seed(x, y, z)
        rng = random.Random(seed ^ 0xB41C1)
        
        # Horizontal mortar lines (3 rows of bricks)
        brick_h = config.TILE_SIZE // 3
        for row in range(1, 3):
            y_pos = rect.top + row * brick_h
            pygame.draw.line(surface, mortar, (rect.left, y_pos), (rect.right, y_pos), 1)
        
        # Vertical mortar lines (offset per row for brick pattern)
        brick_w = config.TILE_SIZE // 2
        for row in range(3):
            y_start = rect.top + row * brick_h
            y_end = y_start + brick_h
            offset = (row % 2) * (brick_w // 2)
            
            for col in range(3):
                x_pos = rect.left + offset + col * brick_w
                if rect.left < x_pos < rect.right:
                    pygame.draw.line(surface, mortar, (x_pos, y_start), (x_pos, y_end), 1)
        
        # Subtle brick highlights
        if rng.random() < 0.25:
            bx = rect.left + rng.randint(2, rect.width - 5)
            by = rect.top + rng.randint(2, rect.height - 5)
            pygame.draw.rect(surface, light_brick, (bx, by, 4, 2))
    
    # --- Interior Lighting System ---
    
    def is_interior_tile(self, x: int, y: int, z: int) -> bool:
        """Check if a tile is considered interior (enclosed by walls).
        
        A tile is interior if:
        - It is a floor tile (finished_floor or floor), AND
        - All four cardinal directions have solid blocking tiles
        
        This is used for visual tinting only, not game mechanics.
        Ruined buildings with missing walls will not be considered interior.
        """
        tile = self.get_tile(x, y, z)
        
        # Only floor tiles can be interior
        if tile not in ["finished_floor", "floor", "crash_bed"]:
            return False
        
        # Check all four cardinal directions for solid tiles
        # Solid tiles include: walls, doors, windows, finished buildings
        solid_tiles = {
            "finished_wall", "finished_wall_advanced", "wall", "wall_advanced",
            "finished_building", "door", "window", "finished_window",
            "finished_salvagers_bench", "finished_generator", "finished_stove",
            "finished_gutter_forge", "finished_skinshop_loom", "finished_cortex_spindle",
            "finished_barracks"
        }
        
        # North
        north = self.get_tile(x, y - 1, z)
        if north not in solid_tiles:
            return False
        
        # South
        south = self.get_tile(x, y + 1, z)
        if south not in solid_tiles:
            return False
        
        # East
        east = self.get_tile(x + 1, y, z)
        if east not in solid_tiles:
            return False
        
        # West
        west = self.get_tile(x - 1, y, z)
        if west not in solid_tiles:
            return False
        
        return True
    
    def world_to_screen(self, world_x: int, world_y: int) -> tuple[int, int]:
        """Convert world pixel coordinates to screen coordinates.
        
        Returns (screen_x, screen_y).
        """
        screen_x = world_x - self.camera_x
        screen_y = world_y - self.camera_y
        return (screen_x, screen_y)
    
    def _draw_layer_below(self, surface: pygame.Surface, below_z: int, cam_x: int, cam_y: int,
                          start_x: int, start_y: int, end_x: int, end_y: int) -> None:
        """Draw the Z-level below with transparency for context.
        
        Renders sprites at reduced opacity for the floor below so players can see what's underneath.
        """
        # Create a temporary surface for the layer below with alpha channel
        tile_size = config.TILE_SIZE
        visible_w = (end_x - start_x) * tile_size
        visible_h = (end_y - start_y) * tile_size
        if visible_w <= 0 or visible_h <= 0:
            return
        
        # Create temporary surface for below layer
        temp_surface = pygame.Surface((visible_w, visible_h), pygame.SRCALPHA)
        
        # Draw tiles from the level below
        for y in range(start_y, end_y):
            for x in range(start_x, end_x):
                world_x = x * tile_size
                world_y = y * tile_size
                screen_x = world_x - cam_x
                screen_y = world_y - cam_y
                
                # Position on temp surface
                temp_x = (x - start_x) * tile_size
                temp_y = (y - start_y) * tile_size
                temp_rect = pygame.Rect(temp_x, temp_y, tile_size, tile_size)
                
                tile = self.tiles[below_z][y][x]
                
                # Try to draw sprite first, fallback to dimmed procedural
                sprite_drawn = False
                if tile in ("finished_floor", "finished_wall", "finished_wall_advanced"):
                    tile_sprite = sprites.get_tile_sprite(tile, x, y, below_z, tile_size)
                    if tile_sprite:
                        temp_surface.blit(tile_sprite, temp_rect.topleft)
                        sprite_drawn = True
                
                # Fallback to dimmed procedural colors if no sprite
                if not sprite_drawn:
                    # Get base color for tile and dim it significantly
                    if tile == "empty" or tile is None:
                        base_color = self._get_tile_color_variation(COLOR_TILE_EMPTY, x, y, below_z, 8)
                    elif tile == "dirt":
                        base_color = self._get_tile_color_variation(COLOR_TILE_DIRT, x, y, below_z, 10)
                    elif tile == "grass":
                        base_color = self._get_tile_color_variation(COLOR_TILE_GRASS, x, y, below_z, 12)
                    elif tile == "rock":
                        base_color = self._get_tile_color_variation(COLOR_TILE_ROCK, x, y, below_z, 8)
                    elif tile == "scorched":
                        base_color = self._get_tile_color_variation(COLOR_TILE_SCORCHED, x, y, below_z, 6)
                    elif tile == "debris":
                        base_color = self._get_tile_color_variation(COLOR_TILE_DEBRIS, x, y, below_z, 12)
                    elif tile == "weeds":
                        base_color = self._get_tile_color_variation(COLOR_TILE_WEEDS, x, y, below_z, 10)
                    elif tile in ("sidewalk", "sidewalk_designated"):
                        base_color = COLOR_TILE_SIDEWALK
                    elif tile in ("street", "street_cracked", "street_scar", "street_ripped"):
                        base_color = COLOR_TILE_STREET
                    elif tile == "floor":
                        base_color = (140, 120, 90)
                    elif tile == "finished_floor":
                        base_color = (160, 130, 90)
                    elif tile in ("wall", "finished_wall", "wall_advanced", "finished_wall_advanced"):
                        base_color = COLOR_TILE_FINISHED_WALL
                    elif tile in ("door", "window", "finished_window", "window_tile"):
                        base_color = COLOR_TILE_FINISHED_WALL
                    elif tile in ("building", "finished_building"):
                        base_color = COLOR_TILE_FINISHED_BUILDING
                    elif tile == "roof":
                        base_color = (60, 40, 80)
                    elif tile in ("roof_access", "roof_floor"):
                        base_color = (160, 130, 90)
                    elif tile.startswith("prop_"):
                        if tile == "prop_barrel":
                            base_color = COLOR_TILE_PROP_BARREL
                        elif tile == "prop_sign":
                            base_color = COLOR_TILE_PROP_SIGN
                        elif tile == "prop_scrap":
                            base_color = COLOR_TILE_PROP_SCRAP
                        else:
                            base_color = (70, 65, 60)
                    elif tile.startswith("finished_"):
                        base_color = (90, 85, 80)
                    else:
                        base_color = (60, 60, 70)
                    
                    # Dim the color to 40% brightness
                    dimmed = (base_color[0] * 4 // 10, base_color[1] * 4 // 10, base_color[2] * 4 // 10)
                    pygame.draw.rect(temp_surface, dimmed, temp_rect)
        
        # Apply 40% opacity to entire layer and blit to main surface
        temp_surface.set_alpha(100)  # 100/255 ≈ 40% opacity
        surface.blit(temp_surface, (start_x * tile_size - cam_x, start_y * tile_size - cam_y))

    def draw(self, surface: pygame.Surface, hovered_tile: tuple[int, int] | None = None) -> None:
        """Render the grid and its tiles to the given surface.
        
        If hovered_tile is provided, that tile will be highlighted momentarily.
        Only draws tiles from the current Z-level.
        Uses camera offset to render only visible portion of the world.
        """
        z = self.current_z
        is_ground_level = (z == 0)
        
        # Cache TILE_SIZE for performance (avoid thousands of attribute lookups per frame)
        tile_size = config.TILE_SIZE
        
        # Calculate visible tile range based on camera position (convert float to int)
        cam_x = int(self.camera_x)
        cam_y = int(self.camera_y)
        start_tile_x = max(0, cam_x // tile_size)
        start_tile_y = max(0, cam_y // tile_size)
        end_tile_x = min(self.width, (cam_x + SCREEN_W) // tile_size + 1)
        end_tile_y = min(self.height, (cam_y + SCREEN_H) // tile_size + 1)
        
        # Draw layer below with transparency when viewing upper floors
        if z > 0:
            self._draw_layer_below(surface, z - 1, cam_x, cam_y, start_tile_x, start_tile_y, end_tile_x, end_tile_y)

        for y in range(start_tile_y, end_tile_y):
            for x in range(start_tile_x, end_tile_x):
                # World position in pixels
                world_x = x * tile_size
                world_y = y * tile_size
                
                # Screen position (apply camera offset)
                screen_x = world_x - cam_x
                screen_y = world_y - cam_y
                
                rect = pygame.Rect(
                    screen_x,
                    screen_y,
                    tile_size,
                    tile_size,
                )

                tile = self.tiles[z][y][x]

                # Draw base ground tiles first (beneath everything else)
                # On upper floors, skip empty tiles so layer below shows through
                if tile == "empty" or tile is None:
                    if is_ground_level:
                        # Try sprite first, fallback to procedural
                        if not self._try_draw_tile_sprite(surface, "empty", rect, x, y, z):
                            # Ground level: draw earth tones
                            color = self._get_tile_color_variation(COLOR_TILE_EMPTY, x, y, z, 8)
                            pygame.draw.rect(surface, color, rect)
                        
                        # Check if this empty tile is a stockpile - if so, don't skip rendering
                        if not zones.is_stockpile_zone(x, y, z):
                            continue
                    else:
                        # Upper floors: don't draw empty tiles (layer below visible)
                        continue
                elif tile == "dirt":
                    # Try sprite first, fallback to procedural
                    if not self._try_draw_tile_sprite(surface, "dirt", rect, x, y, z):
                        color = self._get_tile_color_variation(COLOR_TILE_DIRT, x, y, z, 10)
                        pygame.draw.rect(surface, color, rect)
                elif tile == "grass":
                    # Try sprite first, fallback to procedural
                    if not self._try_draw_tile_sprite(surface, "grass", rect, x, y, z):
                        color = self._get_tile_color_variation(COLOR_TILE_GRASS, x, y, z, 12)
                        pygame.draw.rect(surface, color, rect)
                elif tile == "rock":
                    # Try sprite first, fallback to procedural
                    if not self._try_draw_tile_sprite(surface, "rock", rect, x, y, z):
                        color = self._get_tile_color_variation(COLOR_TILE_ROCK, x, y, z, 8)
                        pygame.draw.rect(surface, color, rect)
                elif tile == "scorched":
                    # Try sprite first, fallback to procedural
                    if not self._try_draw_tile_sprite(surface, "scorched", rect, x, y, z):
                        color = self._get_tile_color_variation(COLOR_TILE_SCORCHED, x, y, z, 6)
                        pygame.draw.rect(surface, color, rect)
                # Decorative tiles with subtle color variation
                elif tile == "sidewalk":
                    # Try sprite first, fallback to procedural
                    if not self._try_draw_tile_sprite(surface, "sidewalk", rect, x, y, z):
                        self._draw_sidewalk_tile(surface, rect, x, y, z, designated=False)
                elif tile == "sidewalk_designated":
                    # Try sprite first, fallback to procedural
                    if not self._try_draw_tile_sprite(surface, "sidewalk", rect, x, y, z):
                        self._draw_sidewalk_tile(surface, rect, x, y, z, designated=True)
                elif tile == "debris":
                    # Try sprite first, fallback to procedural
                    if not self._try_draw_tile_sprite(surface, "debris", rect, x, y, z):
                        color = self._get_tile_color_variation(COLOR_TILE_DEBRIS, x, y, z, 12)
                        pygame.draw.rect(surface, color, rect)
                elif tile == "weeds":
                    # Try sprite first, fallback to procedural
                    if not self._try_draw_tile_sprite(surface, "weeds", rect, x, y, z):
                        color = self._get_tile_color_variation(COLOR_TILE_WEEDS, x, y, z, 10)
                        pygame.draw.rect(surface, color, rect)
                elif tile == "prop_barrel":
                    # Try sprite first, fallback to procedural
                    if not self._try_draw_tile_sprite(surface, "prop_barrel", rect, x, y, z):
                        color = self._get_tile_color_variation(COLOR_TILE_PROP_BARREL, x, y, z, 15)
                        pygame.draw.rect(surface, color, rect)
                elif tile == "prop_sign":
                    # Try sprite first, fallback to procedural
                    if not self._try_draw_tile_sprite(surface, "prop_sign", rect, x, y, z):
                        color = self._get_tile_color_variation(COLOR_TILE_PROP_SIGN, x, y, z, 12)
                        pygame.draw.rect(surface, color, rect)
                elif tile == "prop_scrap":
                    # Try sprite first, fallback to procedural
                    if not self._try_draw_tile_sprite(surface, "prop_scrap", rect, x, y, z):
                        color = self._get_tile_color_variation(COLOR_TILE_PROP_SCRAP, x, y, z, 15)
                        pygame.draw.rect(surface, color, rect)

                # Stockpile zone background moved to after floor rendering (see line ~1821)
                
                # Momentary hover highlight (no sticky selection)
                if hovered_tile is not None and hovered_tile == (x, y):
                    pygame.draw.rect(surface, COLOR_TILE_SELECTED, rect)
                elif tile == "building":
                    # Try sprite first (uses finished_building with construction tint), fallback to procedural
                    if not self._try_draw_tile_sprite(surface, "building", rect, x, y, z, use_construction_tint=True):
                        pygame.draw.rect(surface, COLOR_TILE_BUILDING, rect)

                    # Optional: small progress bar for the construction job on
                    # this tile, if one exists.
                    job = get_job_at(x, y)
                    if job is not None and job.required > 0:
                        progress_ratio = max(0.0, min(1.0, job.progress / job.required))
                        bar_margin = 4
                        bar_height = 4
                        bar_width = int((config.TILE_SIZE - 2 * bar_margin) * progress_ratio)
                        bar_rect = pygame.Rect(
                            rect.left + bar_margin,
                            rect.bottom - bar_margin - bar_height,
                            bar_width,
                            bar_height,
                        )
                        if bar_width > 0:
                            pygame.draw.rect(surface, COLOR_CONSTRUCTION_PROGRESS, bar_rect)
                elif tile == "finished_building":
                    # Try sprite first, fallback to procedural
                    if not self._try_draw_tile_sprite(surface, "finished_building", rect, x, y, z):
                        pygame.draw.rect(surface, COLOR_TILE_FINISHED_BUILDING, rect)
                elif tile == "wall":
                    # Try sprite first (uses finished_wall with construction tint), fallback to procedural
                    if not self._try_draw_tile_sprite(surface, "wall", rect, x, y, z, use_construction_tint=True):
                        pygame.draw.rect(surface, COLOR_TILE_WALL, rect)
                    
                    # Show delivered materials as small icons (overlay on sprite or procedural)
                    site = buildings.get_construction_site(x, y, z)
                    if site is not None:
                        delivered = site.get("materials_delivered", {})
                        needed = site.get("materials_needed", {})
                        icon_x = rect.left + 2
                        for res_type in needed.keys():
                            has_it = delivered.get(res_type, 0) >= needed.get(res_type, 0)
                            if res_type == "wood":
                                icon_color = COLOR_RESOURCE_NODE_WOOD if has_it else (60, 40, 20)
                            elif res_type == "mineral":
                                icon_color = COLOR_RESOURCE_NODE_MINERAL if has_it else (30, 60, 60)
                            else:
                                icon_color = (100, 100, 100) if has_it else (40, 40, 40)
                            icon_rect = pygame.Rect(icon_x, rect.top + 2, 6, 6)
                            pygame.draw.rect(surface, icon_color, icon_rect)
                            icon_x += 8
                    
                    # Progress bar for wall construction (overlay on sprite or procedural)
                    job = get_job_at(x, y)
                    if job is not None and job.required > 0:
                        progress_ratio = max(0.0, min(1.0, job.progress / job.required))
                        bar_margin = 4
                        bar_height = 4
                        bar_width = int((config.TILE_SIZE - 2 * bar_margin) * progress_ratio)
                        bar_rect = pygame.Rect(
                            rect.left + bar_margin,
                            rect.bottom - bar_margin - bar_height,
                            bar_width,
                            bar_height,
                        )
                        if bar_width > 0:
                            pygame.draw.rect(surface, COLOR_CONSTRUCTION_PROGRESS, bar_rect)
                elif tile == "finished_wall":
                    # Try sprite first, fallback to procedural
                    if not self._try_draw_tile_sprite(surface, "finished_wall", rect, x, y, z):
                        pygame.draw.rect(surface, COLOR_TILE_FINISHED_WALL, rect)
                elif tile == "scrap_bar_counter":
                    # Try sprite with construction tint
                    self._try_draw_tile_sprite(surface, "finished_scrap_bar_counter", rect, x, y, z, use_construction_tint=True)
                    
                    # Material icons
                    site = buildings.get_construction_site(x, y, z)
                    if site is not None:
                        delivered = site.get("materials_delivered", {})
                        needed = site.get("materials_needed", {})
                        icon_x = rect.left + 2
                        for res_type in needed.keys():
                            has_it = delivered.get(res_type, 0) >= needed.get(res_type, 0)
                            if res_type == "wood":
                                icon_color = COLOR_RESOURCE_NODE_WOOD if has_it else (60, 40, 20)
                            elif res_type == "scrap":
                                icon_color = (150, 100, 50) if has_it else (60, 40, 20)
                            else:
                                icon_color = (100, 100, 100) if has_it else (40, 40, 40)
                            icon_rect = pygame.Rect(icon_x, rect.top + 2, 6, 6)
                            pygame.draw.rect(surface, icon_color, icon_rect)
                            icon_x += 8
                    
                    # Progress bar
                    job = get_job_at(x, y)
                    if job is not None and job.required > 0:
                        progress_ratio = max(0.0, min(1.0, job.progress / job.required))
                        bar_margin = 4
                        bar_height = 4
                        bar_width = int((config.TILE_SIZE - 2 * bar_margin) * progress_ratio)
                        bar_rect = pygame.Rect(rect.left + bar_margin, rect.bottom - bar_margin - bar_height, bar_width, bar_height)
                        if bar_width > 0:
                            pygame.draw.rect(surface, COLOR_CONSTRUCTION_PROGRESS, bar_rect)
                elif tile == "finished_scrap_bar_counter":
                    # Try sprite only - no procedural fallback
                    self._try_draw_tile_sprite(surface, "finished_scrap_bar_counter", rect, x, y, z)
                elif tile in ("street", "street_cracked", "street_scar", "street_ripped"):
                    # Try sprite first, fallback to procedural
                    if not self._try_draw_tile_sprite(surface, tile, rect, x, y, z):
                        self._draw_street_tile(surface, rect, x, y, z, tile)
                elif tile == "street_designated":
                    # Street designated for harvesting - warmer tone with harvest indicator
                    color = self._get_tile_color_variation(COLOR_TILE_STREET_DESIGNATED, x, y, z, 8)
                    pygame.draw.rect(surface, color, rect)
                    # Small pickaxe/mining indicator
                    pygame.draw.circle(surface, (180, 160, 120), (rect.centerx, rect.centery), 4)
                    pygame.draw.circle(surface, (100, 90, 70), (rect.centerx, rect.centery), 4, 1)
                elif tile == "sidewalk_designated":
                    # Sidewalk designated for harvesting
                    color = self._get_tile_color_variation(COLOR_TILE_SIDEWALK_DESIGNATED, x, y, z, 8)
                    pygame.draw.rect(surface, color, rect)
                    # Small pickaxe/mining indicator
                    pygame.draw.circle(surface, (180, 160, 120), (rect.centerx, rect.centery), 4)
                    pygame.draw.circle(surface, (100, 90, 70), (rect.centerx, rect.centery), 4, 1)
                elif tile == "wall_advanced":
                    # Try sprite first (uses finished_wall_advanced with construction tint), fallback to procedural
                    if not self._try_draw_tile_sprite(surface, "wall_advanced", rect, x, y, z, use_construction_tint=True):
                        pygame.draw.rect(surface, (60, 60, 70), rect)
                    
                    # Show delivered materials as small icons
                    site = buildings.get_construction_site(x, y, z)
                    if site is not None:
                        delivered = site.get("materials_delivered", {})
                        needed = site.get("materials_needed", {})
                        icon_x = rect.left + 2
                        for res_type in needed.keys():
                            has_it = delivered.get(res_type, 0) >= needed.get(res_type, 0)
                            if res_type == "mineral":
                                icon_color = COLOR_RESOURCE_NODE_MINERAL if has_it else (30, 60, 60)
                            elif res_type == "metal":
                                icon_color = COLOR_RESOURCE_NODE_METAL if has_it else (40, 40, 50)
                            elif res_type == "scrap":
                                icon_color = COLOR_RESOURCE_NODE_SCRAP if has_it else (40, 40, 50)
                            else:
                                icon_color = (100, 100, 100) if has_it else (40, 40, 40)
                            icon_rect = pygame.Rect(icon_x, rect.top + 2, 6, 6)
                            pygame.draw.rect(surface, icon_color, icon_rect)
                            icon_x += 8
                    
                    # Progress bar
                    job = get_job_at(x, y)
                    if job is not None and job.required > 0:
                        progress_ratio = max(0.0, min(1.0, job.progress / job.required))
                        bar_margin = 4
                        bar_height = 4
                        bar_width = int((config.TILE_SIZE - 2 * bar_margin) * progress_ratio)
                        bar_rect = pygame.Rect(
                            rect.left + bar_margin,
                            rect.bottom - bar_margin - bar_height,
                            bar_width,
                            bar_height,
                        )
                        if bar_width > 0:
                            pygame.draw.rect(surface, COLOR_CONSTRUCTION_PROGRESS, bar_rect)
                elif tile == "finished_wall_advanced":
                    # Try sprite first, fallback to procedural
                    if not self._try_draw_tile_sprite(surface, "finished_wall_advanced", rect, x, y, z):
                        pygame.draw.rect(surface, (80, 90, 110), rect)
                elif tile == "door":
                    # Door tile - check if open or closed
                    is_open = buildings.is_door_open(x, y)
                    site = buildings.get_construction_site(x, y, z)
                    
                    if site is not None:
                        # Try sprite first (uses finished_door with construction tint), fallback to procedural
                        if not self._try_draw_tile_sprite(surface, "door", rect, x, y, z, use_construction_tint=True):
                            pygame.draw.rect(surface, (100, 70, 40), rect)
                        
                        # Show delivered materials (overlay on sprite or procedural)
                        delivered = site.get("materials_delivered", {})
                        needed = site.get("materials_needed", {})
                        icon_x = rect.left + 2
                        for res_type in needed.keys():
                            has_it = delivered.get(res_type, 0) >= needed.get(res_type, 0)
                            if res_type == "metal":
                                icon_color = COLOR_RESOURCE_NODE_METAL if has_it else (40, 40, 50)
                            else:
                                icon_color = (100, 100, 100) if has_it else (40, 40, 40)
                            icon_rect = pygame.Rect(icon_x, rect.top + 2, 6, 6)
                            pygame.draw.rect(surface, icon_color, icon_rect)
                            icon_x += 8
                        
                        # Progress bar (overlay on sprite or procedural)
                        job = get_job_at(x, y)
                        if job is not None and job.required > 0:
                            progress_ratio = max(0.0, min(1.0, job.progress / job.required))
                            bar_margin = 4
                            bar_height = 4
                            bar_width = int((config.TILE_SIZE - 2 * bar_margin) * progress_ratio)
                            bar_rect = pygame.Rect(
                                rect.left + bar_margin,
                                rect.bottom - bar_margin - bar_height,
                                bar_width,
                                bar_height,
                            )
                            if bar_width > 0:
                                pygame.draw.rect(surface, COLOR_CONSTRUCTION_PROGRESS, bar_rect)
                    elif is_open:
                        # Try sprite first for open door, fallback to procedural
                        if not self._try_draw_tile_sprite(surface, "finished_door", rect, x, y, z):
                            pygame.draw.rect(surface, (60, 50, 40), rect)
                            # Draw open gap
                            gap_rect = pygame.Rect(rect.left + 6, rect.top + 2, rect.width - 12, rect.height - 4)
                            pygame.draw.rect(surface, (30, 25, 20), gap_rect)
                    else:
                        # Try sprite first for closed door, fallback to procedural
                        if not self._try_draw_tile_sprite(surface, "finished_door", rect, x, y, z):
                            pygame.draw.rect(surface, (120, 80, 50), rect)
                            # Door handle
                            handle_rect = pygame.Rect(rect.right - 8, rect.centery - 2, 4, 4)
                            pygame.draw.rect(surface, (180, 150, 100), handle_rect)
                elif tile == "bar_door":
                    # Bar door - saloon-style swinging door
                    import random
                    is_open = buildings.is_door_open(x, y)
                    site = buildings.get_construction_site(x, y, z)
                    
                    if site is not None:
                        # Under construction - rusty brown
                        pygame.draw.rect(surface, (90, 65, 45), rect)
                        
                        # Show delivered materials
                        delivered = site.get("materials_delivered", {})
                        needed = site.get("materials_needed", {})
                        icon_x = rect.left + 2
                        for res_type in needed.keys():
                            has_it = delivered.get(res_type, 0) >= needed.get(res_type, 0)
                            if res_type == "scrap":
                                icon_color = (150, 100, 50) if has_it else (60, 40, 20)
                            elif res_type == "wood":
                                icon_color = COLOR_RESOURCE_NODE_WOOD if has_it else (60, 40, 20)
                            else:
                                icon_color = (100, 100, 100) if has_it else (40, 40, 40)
                            icon_rect = pygame.Rect(icon_x, rect.top + 2, 6, 6)
                            pygame.draw.rect(surface, icon_color, icon_rect)
                            icon_x += 8
                        
                        # Progress bar
                        job = get_job_at(x, y)
                        if job is not None and job.required > 0:
                            progress_ratio = max(0.0, min(1.0, job.progress / job.required))
                            bar_margin = 4
                            bar_height = 4
                            bar_width = int((config.TILE_SIZE - 2 * bar_margin) * progress_ratio)
                            bar_rect = pygame.Rect(rect.left + bar_margin, rect.bottom - bar_margin - bar_height, bar_width, bar_height)
                            if bar_width > 0:
                                pygame.draw.rect(surface, COLOR_CONSTRUCTION_PROGRESS, bar_rect)
                    elif is_open:
                        # Try sprite first for open bar door, fallback to procedural
                        if not self._try_draw_tile_sprite(surface, "bar_door", rect, x, y, z):
                            pygame.draw.rect(surface, (70, 55, 40), rect)
                            # Left door swung left
                            left_door = pygame.Rect(rect.left, rect.top + 4, 6, rect.height - 8)
                            pygame.draw.rect(surface, (85, 65, 50), left_door)
                            # Right door swung right
                            right_door = pygame.Rect(rect.right - 6, rect.top + 4, 6, rect.height - 8)
                            pygame.draw.rect(surface, (85, 65, 50), right_door)
                            # Open gap in middle
                            gap_rect = pygame.Rect(rect.left + 8, rect.top + 2, rect.width - 16, rect.height - 4)
                            pygame.draw.rect(surface, (40, 35, 30), gap_rect)
                    else:
                        # Try sprite first for closed bar door, fallback to procedural
                        if not self._try_draw_tile_sprite(surface, "bar_door", rect, x, y, z):
                            seed = self._get_tile_seed(x, y, z)
                            rng = random.Random(seed)
                            base_color = (90, 70, 50)
                            color = self._get_tile_color_variation(base_color, x, y, z, 6)
                            pygame.draw.rect(surface, color, rect)
                            
                            # Double door split in middle
                            pygame.draw.line(surface, (60, 50, 40), (rect.centerx, rect.top), (rect.centerx, rect.bottom), 2)
                            
                            # Horizontal slats (saloon style)
                            slat_color = (max(0, color[0] - 15), max(0, color[1] - 10), max(0, color[2] - 8))
                            for i in range(3):
                                slat_y = rect.top + (i + 1) * (rect.height // 4)
                                pygame.draw.line(surface, slat_color, (rect.left + 2, slat_y), (rect.right - 2, slat_y), 1)
                            
                            # Rust spots
                            if rng.random() < 0.5:
                                rust_x = rect.left + rng.randint(4, rect.width - 6)
                                rust_y = rect.top + rng.randint(4, rect.height - 6)
                                pygame.draw.rect(surface, (70, 50, 35), (rust_x, rust_y, 2, 2))
                elif tile == "window":
                    # Try sprite first (uses finished_window with construction tint), fallback to procedural
                    if not self._try_draw_tile_sprite(surface, "window", rect, x, y, z, use_construction_tint=True):
                        pygame.draw.rect(surface, (100, 110, 130), rect)
                    
                    # Show delivered materials (overlay on sprite or procedural)
                    site = buildings.get_construction_site(x, y, z)
                    if site is not None:
                        delivered = site.get("materials_delivered", {})
                        needed = site.get("materials_needed", {})
                        icon_x = rect.left + 2
                        for res_type in needed.keys():
                            has_it = delivered.get(res_type, 0) >= needed.get(res_type, 0)
                            if res_type == "wood":
                                icon_color = COLOR_RESOURCE_NODE_WOOD if has_it else (60, 40, 20)
                            elif res_type == "mineral":
                                icon_color = COLOR_RESOURCE_NODE_MINERAL if has_it else (30, 60, 60)
                            else:
                                icon_color = (100, 100, 100) if has_it else (40, 40, 40)
                            icon_rect = pygame.Rect(icon_x, rect.top + 2, 6, 6)
                            pygame.draw.rect(surface, icon_color, icon_rect)
                            icon_x += 8
                        
                        # Progress bar (overlay on sprite or procedural)
                        job = get_job_at(x, y)
                        if job is not None and job.required > 0:
                            progress_ratio = max(0.0, min(1.0, job.progress / job.required))
                            bar_margin = 4
                            bar_height = 4
                            bar_width = int((config.TILE_SIZE - 2 * bar_margin) * progress_ratio)
                            bar_rect = pygame.Rect(
                                rect.left + bar_margin,
                                rect.bottom - bar_margin - bar_height,
                                bar_width,
                                bar_height,
                            )
                            if bar_width > 0:
                                pygame.draw.rect(surface, COLOR_CONSTRUCTION_PROGRESS, bar_rect)
                elif tile == "finished_window":
                    # Try sprite first, fallback to procedural
                    if not self._try_draw_tile_sprite(surface, "finished_window", rect, x, y, z):
                        # Finished window - wall with glass pane (can be open or closed)
                        is_open = buildings.is_window_open(x, y, z)
                        
                        # Wall frame
                        pygame.draw.rect(surface, COLOR_TILE_FINISHED_WALL, rect)
                        
                        # Glass pane in center
                        glass_margin = 6
                        glass_rect = pygame.Rect(
                            rect.left + glass_margin,
                            rect.top + glass_margin,
                            rect.width - glass_margin * 2,
                            rect.height - glass_margin * 2
                        )
                        
                        if is_open:
                            # Open window - dark opening with frame
                            pygame.draw.rect(surface, (40, 35, 30), glass_rect)  # Dark opening
                            # Window frame on sides (pushed open)
                            frame_color = (100, 130, 150)
                            pygame.draw.rect(surface, frame_color, 
                                           (glass_rect.left, glass_rect.top, 3, glass_rect.height))
                            pygame.draw.rect(surface, frame_color, 
                                           (glass_rect.right - 3, glass_rect.top, 3, glass_rect.height))
                        else:
                            # Closed window - glass pane
                            pygame.draw.rect(surface, (140, 180, 200), glass_rect)  # Light blue glass
                            # Glass highlight
                            pygame.draw.line(surface, (180, 210, 230), 
                                           (glass_rect.left + 2, glass_rect.top + 2),
                                           (glass_rect.left + 2, glass_rect.bottom - 2), 1)
                            # Cross pattern for window panes
                            pygame.draw.line(surface, COLOR_TILE_FINISHED_WALL,
                                           (glass_rect.centerx, glass_rect.top),
                                           (glass_rect.centerx, glass_rect.bottom), 1)
                            pygame.draw.line(surface, COLOR_TILE_FINISHED_WALL,
                                           (glass_rect.left, glass_rect.centery),
                                           (glass_rect.right, glass_rect.centery), 1)
                elif tile == "floor":
                    # Try sprite first (uses finished_floor with construction tint), fallback to procedural
                    if not self._try_draw_tile_sprite(surface, "floor", rect, x, y, z, use_construction_tint=True):
                        pygame.draw.rect(surface, (140, 120, 90), rect)
                    
                    # Show delivered materials (overlay on sprite or procedural)
                    site = buildings.get_construction_site(x, y, z)
                    if site is not None:
                        delivered = site.get("materials_delivered", {})
                        needed = site.get("materials_needed", {})
                        icon_x = rect.left + 2
                        for res_type in needed.keys():
                            has_it = delivered.get(res_type, 0) >= needed.get(res_type, 0)
                            if res_type == "wood":
                                icon_color = COLOR_RESOURCE_NODE_WOOD if has_it else (60, 40, 20)
                            else:
                                icon_color = (100, 100, 100) if has_it else (40, 40, 40)
                            icon_rect = pygame.Rect(icon_x, rect.top + 2, 6, 6)
                            pygame.draw.rect(surface, icon_color, icon_rect)
                            icon_x += 8
                        
                        # Progress bar (overlay on sprite or procedural)
                        job = get_job_at(x, y)
                        if job is not None and job.required > 0:
                            progress_ratio = max(0.0, min(1.0, job.progress / job.required))
                            bar_margin = 4
                            bar_height = 4
                            bar_width = int((config.TILE_SIZE - 2 * bar_margin) * progress_ratio)
                            bar_rect = pygame.Rect(
                                rect.left + bar_margin,
                                rect.bottom - bar_margin - bar_height,
                                bar_width,
                                bar_height,
                            )
                            if bar_width > 0:
                                pygame.draw.rect(surface, COLOR_CONSTRUCTION_PROGRESS, bar_rect)
                    
                    # Interior lighting tint - darken enclosed floor tiles (even under construction)
                    if self.is_interior_tile(x, y, z):
                        # ADJUSTABLE: Same darkness level as finished floors
                        interior_darkness = 50
                        tint_surface = pygame.Surface((config.TILE_SIZE, config.TILE_SIZE), pygame.SRCALPHA)
                        tint_surface.fill((0, 0, 0, interior_darkness))
                        surface.blit(tint_surface, rect.topleft)
                elif tile == "finished_floor":
                    # Try sprite first, fallback to procedural
                    if not self._try_draw_tile_sprite(surface, "finished_floor", rect, x, y, z):
                        # Finished floor - warm wood color with subtle variation and pattern variants
                        base_color = (160, 130, 90)
                        floor_color = self._get_tile_color_variation(base_color, x, y, z, 8)
                        pygame.draw.rect(surface, floor_color, rect)
                        
                        # Draw floor pattern based on variant
                        variant = self._get_floor_variant(x, y, z)
                        plank_color = (max(0, floor_color[0] - 20), max(0, floor_color[1] - 20), max(0, floor_color[2] - 20))
                        
                        if variant == 0:
                            # Horizontal planks
                            pygame.draw.line(surface, plank_color, (rect.left, rect.top + 8), (rect.right, rect.top + 8), 1)
                            pygame.draw.line(surface, plank_color, (rect.left, rect.bottom - 8), (rect.right, rect.bottom - 8), 1)
                        elif variant == 1:
                            # Vertical planks
                            pygame.draw.line(surface, plank_color, (rect.left + 8, rect.top), (rect.left + 8, rect.bottom), 1)
                            pygame.draw.line(surface, plank_color, (rect.right - 8, rect.top), (rect.right - 8, rect.bottom), 1)
                        else:
                            # Diagonal pattern (concrete/stone)
                            pygame.draw.line(surface, plank_color, (rect.left, rect.top), (rect.right, rect.bottom), 1)
                    
                    # Interior lighting tint - darken enclosed floor tiles (applies to both sprite and procedural)
                    if self.is_interior_tile(x, y, z):
                        # ADJUSTABLE: Interior darkness level (0-255, higher = darker)
                        # Current: 50 = ~20% darker, subtle but noticeable
                        # Increase to 70-80 for stronger effect, decrease to 30-40 for lighter
                        interior_darkness = 50
                        tint_surface = pygame.Surface((config.TILE_SIZE, config.TILE_SIZE), pygame.SRCALPHA)
                        tint_surface.fill((0, 0, 0, interior_darkness))
                        surface.blit(tint_surface, rect.topleft)
                elif tile == "stage":
                    # Try sprite with construction tint
                    self._try_draw_tile_sprite(surface, "finished_stage", rect, x, y, z, use_construction_tint=True)
                    
                    # Material icons
                    site = buildings.get_construction_site(x, y, z)
                    if site is not None:
                        delivered = site.get("materials_delivered", {})
                        needed = site.get("materials_needed", {})
                        icon_x = rect.left + 2
                        for res_type in needed.keys():
                            has_it = delivered.get(res_type, 0) >= needed.get(res_type, 0)
                            if res_type == "wood":
                                icon_color = COLOR_RESOURCE_NODE_WOOD if has_it else (60, 40, 20)
                            elif res_type == "scrap":
                                icon_color = (150, 100, 50) if has_it else (60, 40, 20)
                            else:
                                icon_color = (100, 100, 100) if has_it else (40, 40, 40)
                            icon_rect = pygame.Rect(icon_x, rect.top + 2, 6, 6)
                            pygame.draw.rect(surface, icon_color, icon_rect)
                            icon_x += 8
                    
                    # Progress bar
                    job = get_job_at(x, y)
                    if job is not None and job.required > 0:
                        progress_ratio = max(0.0, min(1.0, job.progress / job.required))
                        bar_margin = 4
                        bar_height = 4
                        bar_width = int((config.TILE_SIZE - 2 * bar_margin) * progress_ratio)
                        bar_rect = pygame.Rect(rect.left + bar_margin, rect.bottom - bar_margin - bar_height, bar_width, bar_height)
                        if bar_width > 0:
                            pygame.draw.rect(surface, COLOR_CONSTRUCTION_PROGRESS, bar_rect)
                elif tile == "finished_stage":
                    # Try sprite first, fallback to procedural
                    self._try_draw_tile_sprite(surface, "finished_stage", rect, x, y, z)
                elif tile == "finished_stage_stairs":
                    # Try sprite first, fallback to procedural
                    self._try_draw_tile_sprite(surface, "finished_stage_stairs", rect, x, y, z)
                elif tile == "gutter_slab":
                    # Gutter Slab - cyberpunk work surface: stained concrete with neon edge
                    base_color = (45, 40, 50)  # Dark, slightly purple concrete
                    slab_color = self._get_tile_color_variation(base_color, x, y, z, 6)
                    pygame.draw.rect(surface, slab_color, rect)

                    # Slight inset to suggest a heavy slab sitting on the floor
                    inset_rect = pygame.Rect(rect.left + 2, rect.top + 2, rect.width - 4, rect.height - 4)
                    pygame.draw.rect(surface, (30, 25, 35), inset_rect, 1)

                    # Neon edge line on one side (cyan/magenta mix)
                    neon_color = (140, 30, 180)
                    pygame.draw.line(surface, neon_color, (inset_rect.left, inset_rect.bottom - 3), (inset_rect.right, inset_rect.bottom - 3), 2)

                    # Rat-blood smear – irregular dark red streak
                    blood_color = (110, 20, 25)
                    smear_points = [
                        (inset_rect.left + 4, inset_rect.top + inset_rect.height // 2),
                        (inset_rect.left + inset_rect.width // 3, inset_rect.top + inset_rect.height // 2 + 2),
                        (inset_rect.left + inset_rect.width // 2, inset_rect.top + inset_rect.height // 2 + 1),
                        (inset_rect.left + inset_rect.width // 2 + 4, inset_rect.top + inset_rect.height // 2 + 3),
                    ]
                    pygame.draw.lines(surface, blood_color, False, smear_points, 2)

                    # Slight dirty overlay for grime
                    grime_surface = pygame.Surface((config.TILE_SIZE, config.TILE_SIZE), pygame.SRCALPHA)
                    grime_surface.fill((10, 5, 10, 40))
                    surface.blit(grime_surface, rect.topleft)
                elif tile == "crash_bed":
                    # Draw floor first, then furniture sprite on top
                    # Draw finished floor as base
                    if not self._try_draw_tile_sprite(surface, "finished_floor", rect, x, y, z):
                        # Fallback floor color
                        base_color = (160, 130, 90)
                        floor_color = self._get_tile_color_variation(base_color, x, y, z, 8)
                        pygame.draw.rect(surface, floor_color, rect)
                    
                    # Draw furniture sprite on top
                    self._try_draw_tile_sprite(surface, "crash_bed", rect, x, y, z)
                elif tile == "comfort_chair":
                    # Draw floor first, then chair sprite on top
                    if not self._try_draw_tile_sprite(surface, "finished_floor", rect, x, y, z):
                        base_color = (160, 130, 90)
                        floor_color = self._get_tile_color_variation(base_color, x, y, z, 8)
                        pygame.draw.rect(surface, floor_color, rect)
                    
                    # Draw chair sprite on top
                    self._try_draw_tile_sprite(surface, "comfort_chair", rect, x, y, z)
                elif tile == "bar_stool":
                    # Draw floor first, then stool sprite on top
                    if not self._try_draw_tile_sprite(surface, "finished_floor", rect, x, y, z):
                        base_color = (160, 130, 90)
                        floor_color = self._get_tile_color_variation(base_color, x, y, z, 8)
                        pygame.draw.rect(surface, floor_color, rect)
                    
                    # Draw stool sprite on top
                    self._try_draw_tile_sprite(surface, "bar_stool", rect, x, y, z)
                elif tile == "scrap_guitar_placed":
                    # Draw base tile first (stage or floor), then guitar sprite on top
                    base_tile = self.base_tiles.get((x, y, z), "finished_floor")
                    if not self._try_draw_tile_sprite(surface, base_tile, rect, x, y, z):
                        base_color = (160, 130, 90)
                        floor_color = self._get_tile_color_variation(base_color, x, y, z, 8)
                        pygame.draw.rect(surface, floor_color, rect)
                    
                    # Draw guitar sprite on top
                    self._try_draw_tile_sprite(surface, "scrap_guitar_placed", rect, x, y, z)
                elif tile == "drum_kit_placed":
                    # Draw base tile first (stage or floor), then drum kit sprite on top
                    base_tile = self.base_tiles.get((x, y, z), "finished_floor")
                    if not self._try_draw_tile_sprite(surface, base_tile, rect, x, y, z):
                        base_color = (160, 130, 90)
                        floor_color = self._get_tile_color_variation(base_color, x, y, z, 8)
                        pygame.draw.rect(surface, floor_color, rect)
                    
                    # Draw drum kit sprite on top
                    self._try_draw_tile_sprite(surface, "drum_kit_placed", rect, x, y, z)
                elif tile == "synth_placed":
                    # Draw base tile first (stage or floor), then synth sprite on top
                    base_tile = self.base_tiles.get((x, y, z), "finished_floor")
                    if not self._try_draw_tile_sprite(surface, base_tile, rect, x, y, z):
                        base_color = (160, 130, 90)
                        floor_color = self._get_tile_color_variation(base_color, x, y, z, 8)
                        pygame.draw.rect(surface, floor_color, rect)
                    
                    # Draw synth sprite on top
                    self._try_draw_tile_sprite(surface, "synth_placed", rect, x, y, z)
                elif tile == "harmonica_placed":
                    # Draw base tile first (stage or floor), then harmonica sprite on top
                    base_tile = self.base_tiles.get((x, y, z), "finished_floor")
                    if not self._try_draw_tile_sprite(surface, base_tile, rect, x, y, z):
                        base_color = (160, 130, 90)
                        floor_color = self._get_tile_color_variation(base_color, x, y, z, 8)
                        pygame.draw.rect(surface, floor_color, rect)
                    
                    # Draw harmonica sprite on top
                    self._try_draw_tile_sprite(surface, "harmonica_placed", rect, x, y, z)
                elif tile == "amp_placed":
                    # Draw base tile first (stage or floor), then amp sprite on top
                    base_tile = self.base_tiles.get((x, y, z), "finished_floor")
                    if not self._try_draw_tile_sprite(surface, base_tile, rect, x, y, z):
                        base_color = (160, 130, 90)
                        floor_color = self._get_tile_color_variation(base_color, x, y, z, 8)
                        pygame.draw.rect(surface, floor_color, rect)
                    
                    # Draw amp sprite on top
                    self._try_draw_tile_sprite(surface, "amp_placed", rect, x, y, z)
                elif tile in ("salvagers_bench", "generator", "stove", "gutter_forge", "skinshop_loom", "cortex_spindle", "barracks", "spark_bench", "tinker_station", "gutter_still"):
                    # UNIFIED WORKSTATION UNDER CONSTRUCTION GRAPHIC
                    # Try to load finished sprite with construction tint first
                    finished_tile_name = f"finished_{tile}"
                    if not self._try_draw_tile_sprite(surface, finished_tile_name, rect, x, y, z, use_construction_tint=True):
                        # Fallback: Dark base with construction scaffolding look
                        pygame.draw.rect(surface, (40, 45, 50), rect)
                        
                        # Diagonal construction stripes (cyberpunk scaffolding)
                        stripe_color = (60, 70, 80)
                        for i in range(0, rect.width + rect.height, 8):
                            start_x = rect.left + i
                            start_y = rect.top
                            end_x = rect.left
                            end_y = rect.top + i
                            if start_x > rect.right:
                                start_x = rect.right
                                start_y = rect.top + (i - rect.width)
                            if end_y > rect.bottom:
                                end_y = rect.bottom
                                end_x = rect.left + (i - rect.height)
                            pygame.draw.line(surface, stripe_color, (start_x, start_y), (end_x, end_y), 1)
                        
                        # Frame border (construction site outline)
                        pygame.draw.rect(surface, (80, 90, 100), rect, 1)
                    
                    # Show delivered materials as colored dots
                    site = buildings.get_construction_site(x, y, z)
                    if site is not None:
                        delivered = site.get("materials_delivered", {})
                        needed = site.get("materials_needed", {})
                        icon_x = rect.left + 4
                        for res_type in needed.keys():
                            has_it = delivered.get(res_type, 0) >= needed.get(res_type, 0)
                            # Material indicator colors
                            if res_type == "wood":
                                icon_color = (140, 100, 60) if has_it else (60, 40, 20)
                            elif res_type == "metal":
                                icon_color = (180, 180, 200) if has_it else (60, 60, 70)
                            elif res_type == "scrap":
                                icon_color = (160, 120, 80) if has_it else (50, 40, 30)
                            elif res_type == "mineral":
                                icon_color = (100, 180, 180) if has_it else (40, 60, 60)
                            elif res_type == "power":
                                icon_color = (255, 220, 80) if has_it else (80, 70, 30)
                            else:
                                icon_color = (120, 120, 120) if has_it else (40, 40, 40)
                            # Draw material dot with glow if delivered
                            if has_it:
                                pygame.draw.circle(surface, icon_color, (icon_x + 3, rect.top + 6), 4)
                            else:
                                pygame.draw.circle(surface, icon_color, (icon_x + 3, rect.top + 6), 3, 1)
                            icon_x += 8
                        
                        # Cyan construction progress bar
                        job = get_job_at(x, y)
                        if job is not None and job.required > 0:
                            progress_ratio = max(0.0, min(1.0, job.progress / job.required))
                            bar_width = int((rect.width - 8) * progress_ratio)
                            bar_rect = pygame.Rect(rect.left + 4, rect.bottom - 6, bar_width, 3)
                            if bar_width > 0:
                                # Glow effect
                                glow_rect = pygame.Rect(rect.left + 4, rect.bottom - 7, bar_width, 5)
                                pygame.draw.rect(surface, (0, 180, 200, 60), glow_rect)
                                # Main bar
                                pygame.draw.rect(surface, (0, 220, 255), bar_rect)
                elif tile == "finished_salvagers_bench":
                    # Try sprite first, fallback to procedural
                    if not self._try_draw_tile_sprite(surface, "finished_salvagers_bench", rect, x, y, z):
                        # Finished salvager's bench - workstation appearance
                        # Base - dark wood
                        pygame.draw.rect(surface, (80, 60, 40), rect)
                        
                        # Work surface - metal top
                        surface_rect = pygame.Rect(rect.left + 3, rect.top + 3, rect.width - 6, rect.height - 8)
                        pygame.draw.rect(surface, (100, 100, 110), surface_rect)
                        
                        # Anvil/tool shape in center
                        anvil_rect = pygame.Rect(rect.centerx - 4, rect.centery - 3, 8, 6)
                        pygame.draw.rect(surface, (60, 60, 70), anvil_rect)
                    
                    # Show work progress if active
                    ws = buildings.get_workstation(x, y, z)
                    if ws and ws.get("working", False):
                        progress = ws.get("progress", 0)
                        recipe = buildings.get_workstation_recipe(x, y, z)
                        if recipe:
                            work_time = recipe.get("work_time", 60)
                            progress_ratio = min(1.0, progress / work_time)
                            bar_width = int((rect.width - 8) * progress_ratio)
                            bar_rect = pygame.Rect(rect.left + 4, rect.bottom - 6, bar_width, 4)
                            pygame.draw.rect(surface, (100, 200, 100), bar_rect)
                elif tile == "finished_gutter_still":
                    # Try sprite first, fallback to procedural
                    if not self._try_draw_tile_sprite(surface, "finished_gutter_still", rect, x, y, z):
                        # Gutter still - makeshift distillery
                        # Base - dark rusty metal
                        pygame.draw.rect(surface, (70, 55, 45), rect)
                        # Tank/barrel shape
                        barrel_rect = pygame.Rect(rect.left + 3, rect.top + 3, rect.width - 6, rect.height - 8)
                        pygame.draw.rect(surface, (85, 65, 50), barrel_rect)
                        # Pipes/tubes
                        pygame.draw.line(surface, (60, 50, 40), (rect.left + 6, rect.top + 8), (rect.right - 6, rect.top + 8), 2)
                        pygame.draw.line(surface, (60, 50, 40), (rect.centerx, rect.top + 8), (rect.centerx, rect.bottom - 6), 1)
                    # Show work progress if active
                    ws = buildings.get_workstation(x, y, z)
                    if ws and ws.get("working", False):
                        progress = ws.get("progress", 0)
                        recipe = buildings.get_workstation_recipe(x, y, z)
                        if recipe:
                            work_time = recipe.get("work_time", 120)
                            progress_ratio = min(1.0, progress / work_time)
                            bar_width = int((rect.width - 8) * progress_ratio)
                            bar_rect = pygame.Rect(rect.left + 4, rect.bottom - 6, bar_width, 4)
                            pygame.draw.rect(surface, (150, 100, 50), bar_rect)
                elif tile == "finished_spark_bench":
                    # Try sprite first, fallback to procedural
                    if not self._try_draw_tile_sprite(surface, "finished_spark_bench", rect, x, y, z):
                        # Spark Bench - electronics workstation
                        # Base - dark metal with blue tint
                        pygame.draw.rect(surface, (50, 60, 70), rect)
                        # Work surface with circuit pattern
                        surface_rect = pygame.Rect(rect.left + 3, rect.top + 3, rect.width - 6, rect.height - 8)
                        pygame.draw.rect(surface, (70, 80, 90), surface_rect)
                        # Circuit traces (lines)
                        pygame.draw.line(surface, (100, 180, 200), (rect.left + 5, rect.centery), (rect.right - 5, rect.centery), 1)
                        pygame.draw.line(surface, (100, 180, 200), (rect.centerx, rect.top + 5), (rect.centerx, rect.bottom - 5), 1)
                        # Sparks/LEDs (small dots)
                        pygame.draw.rect(surface, (200, 220, 100), (rect.left + 8, rect.top + 8, 2, 2))
                        pygame.draw.rect(surface, (100, 200, 255), (rect.right - 10, rect.top + 8, 2, 2))
                    # Show work progress if active
                    ws = buildings.get_workstation(x, y, z)
                    if ws and ws.get("working", False):
                        progress = ws.get("progress", 0)
                        recipe = buildings.get_workstation_recipe(x, y, z)
                        if recipe:
                            work_time = recipe.get("work_time", 60)
                            progress_ratio = min(1.0, progress / work_time)
                            bar_width = int((rect.width - 8) * progress_ratio)
                            bar_rect = pygame.Rect(rect.left + 4, rect.bottom - 6, bar_width, 4)
                            pygame.draw.rect(surface, (100, 200, 255), bar_rect)
                elif tile == "finished_tinker_station":
                    # Try sprite first, fallback to procedural
                    if not self._try_draw_tile_sprite(surface, "finished_tinker_station", rect, x, y, z):
                        # Tinker Station - general crafts workbench
                        # Base - wood with metal accents
                        pygame.draw.rect(surface, (90, 70, 50), rect)
                        # Work surface
                        surface_rect = pygame.Rect(rect.left + 3, rect.top + 3, rect.width - 6, rect.height - 8)
                        pygame.draw.rect(surface, (110, 90, 60), surface_rect)
                        # Tools scattered on surface (small shapes)
                        pygame.draw.rect(surface, (140, 140, 140), (rect.left + 6, rect.centery - 2, 4, 2))  # Wrench
                        pygame.draw.rect(surface, (160, 120, 80), (rect.right - 10, rect.centery, 3, 4))  # Screwdriver
                        pygame.draw.line(surface, (120, 100, 80), (rect.left + 8, rect.top + 6), (rect.right - 8, rect.top + 6), 1)  # Edge detail
                    # Show work progress if active
                    ws = buildings.get_workstation(x, y, z)
                    if ws and ws.get("working", False):
                        progress = ws.get("progress", 0)
                        recipe = buildings.get_workstation_recipe(x, y, z)
                        if recipe:
                            work_time = recipe.get("work_time", 80)
                            progress_ratio = min(1.0, progress / work_time)
                            bar_width = int((rect.width - 8) * progress_ratio)
                            bar_rect = pygame.Rect(rect.left + 4, rect.bottom - 6, bar_width, 4)
                            pygame.draw.rect(surface, (200, 150, 100), bar_rect)
                elif tile == "finished_generator":
                    # Try sprite first, fallback to procedural
                    if not self._try_draw_tile_sprite(surface, "finished_generator", rect, x, y, z):
                        # Finished generator - industrial appearance
                        # Base - dark metal
                        pygame.draw.rect(surface, (50, 55, 60), rect)
                        
                        # Generator body - lighter metal
                        body_rect = pygame.Rect(rect.left + 4, rect.top + 4, rect.width - 8, rect.height - 8)
                        pygame.draw.rect(surface, (80, 85, 95), body_rect)
                        
                        # Yellow power indicator
                        indicator_rect = pygame.Rect(rect.centerx - 3, rect.top + 6, 6, 6)
                        pygame.draw.rect(surface, (255, 220, 80), indicator_rect)
                        
                        # Vent lines
                        for i in range(3):
                            y_pos = rect.centery + (i - 1) * 5
                            pygame.draw.line(surface, (40, 45, 50),
                                           (rect.left + 6, y_pos),
                                           (rect.right - 6, y_pos), 2)
                    
                    # Show work progress if active
                    ws = buildings.get_workstation(x, y, z)
                    if ws and ws.get("working", False):
                        progress = ws.get("progress", 0)
                        recipe = buildings.get_workstation_recipe(x, y, z)
                        if recipe:
                            work_time = recipe.get("work_time", 80)
                            progress_ratio = min(1.0, progress / work_time)
                            bar_width = int((rect.width - 8) * progress_ratio)
                            bar_rect = pygame.Rect(rect.left + 4, rect.bottom - 6, bar_width, 4)
                            pygame.draw.rect(surface, (255, 220, 80), bar_rect)
                elif tile == "finished_stove":
                    # Try sprite first, fallback to procedural
                    if not self._try_draw_tile_sprite(surface, "finished_stove", rect, x, y, z):
                        # Finished stove - kitchen appliance appearance
                        # Base - dark metal
                        pygame.draw.rect(surface, (60, 55, 50), rect)
                        
                        # Stove body - warm metal
                        body_rect = pygame.Rect(rect.left + 3, rect.top + 3, rect.width - 6, rect.height - 6)
                        pygame.draw.rect(surface, (90, 80, 70), body_rect)
                        
                        # Burner circles (2x2 grid)
                        burner_color = (40, 35, 30)
                        for bx, by in [(0, 0), (1, 0), (0, 1), (1, 1)]:
                            cx = rect.left + 8 + bx * 10
                            cy = rect.top + 8 + by * 10
                            pygame.draw.circle(surface, burner_color, (cx, cy), 4)
                    
                    # Orange heat indicator when working (overlay on sprite or procedural)
                    ws = buildings.get_workstation(x, y, z)
                    if ws and ws.get("working", False):
                        # Glowing burner
                        pygame.draw.circle(surface, (255, 120, 40), (rect.left + 8, rect.top + 8), 4)
                        
                        # Progress bar
                        progress = ws.get("progress", 0)
                        recipe = buildings.get_workstation_recipe(x, y, z)
                        if recipe:
                            work_time = recipe.get("work_time", 60)
                            progress_ratio = min(1.0, progress / work_time)
                            bar_width = int((rect.width - 8) * progress_ratio)
                            bar_rect = pygame.Rect(rect.left + 4, rect.bottom - 6, bar_width, 4)
                            pygame.draw.rect(surface, (255, 160, 80), bar_rect)
                elif tile == "finished_gutter_forge":
                    # Try sprite first, fallback to procedural
                    if not self._try_draw_tile_sprite(surface, "finished_gutter_forge", rect, x, y, z):
                        # Finished Gutter Forge - industrial forge appearance
                        pygame.draw.rect(surface, (60, 50, 45), rect)
                        # Forge body
                        body_rect = pygame.Rect(rect.left + 3, rect.top + 3, rect.width - 6, rect.height - 6)
                        pygame.draw.rect(surface, (90, 75, 60), body_rect)
                        # Anvil shape
                        pygame.draw.rect(surface, (70, 70, 80), (rect.centerx - 5, rect.centery - 2, 10, 6))
                    ws = buildings.get_workstation(x, y, z)
                    if ws:
                        # Show recipe indicator (first 2 chars of recipe name)
                        recipe = buildings.get_workstation_recipe(x, y, z)
                        if recipe:
                            recipe_short = recipe.get("name", "?")[:2].upper()
                            recipe_font = pygame.font.Font(None, 14)
                            recipe_text = recipe_font.render(recipe_short, True, (200, 180, 140))
                            surface.blit(recipe_text, (rect.right - 14, rect.top + 2))
                        # Orange glow when working
                        if ws.get("working", False):
                            pygame.draw.circle(surface, (255, 140, 40), (rect.left + 8, rect.top + 8), 4)
                            progress = ws.get("progress", 0)
                            if recipe:
                                work_time = recipe.get("work_time", 80)
                                progress_ratio = min(1.0, progress / work_time)
                                bar_width = int((rect.width - 8) * progress_ratio)
                                bar_rect = pygame.Rect(rect.left + 4, rect.bottom - 6, bar_width, 4)
                                pygame.draw.rect(surface, (255, 140, 40), bar_rect)
                elif tile == "finished_skinshop_loom":
                    # Try sprite first, fallback to procedural
                    if not self._try_draw_tile_sprite(surface, "finished_skinshop_loom", rect, x, y, z):
                        # Finished Skinshop Loom - textile/leather workstation
                        pygame.draw.rect(surface, (80, 60, 50), rect)
                        body_rect = pygame.Rect(rect.left + 3, rect.top + 3, rect.width - 6, rect.height - 6)
                        pygame.draw.rect(surface, (110, 85, 65), body_rect)
                        # Thread/fabric lines
                        for i in range(3):
                            y_pos = rect.top + 8 + i * 6
                            pygame.draw.line(surface, (140, 110, 80), (rect.left + 5, y_pos), (rect.right - 5, y_pos), 1)
                    ws = buildings.get_workstation(x, y, z)
                    if ws:
                        # Show recipe indicator
                        recipe = buildings.get_workstation_recipe(x, y, z)
                        if recipe:
                            recipe_short = recipe.get("name", "?")[:2].upper()
                            recipe_font = pygame.font.Font(None, 14)
                            recipe_text = recipe_font.render(recipe_short, True, (180, 150, 120))
                            surface.blit(recipe_text, (rect.right - 14, rect.top + 2))
                        if ws.get("working", False):
                            progress = ws.get("progress", 0)
                            if recipe:
                                work_time = recipe.get("work_time", 70)
                                progress_ratio = min(1.0, progress / work_time)
                                bar_width = int((rect.width - 8) * progress_ratio)
                                bar_rect = pygame.Rect(rect.left + 4, rect.bottom - 6, bar_width, 4)
                                pygame.draw.rect(surface, (180, 140, 100), bar_rect)
                elif tile == "finished_cortex_spindle":
                    # Try sprite first, fallback to procedural
                    if not self._try_draw_tile_sprite(surface, "finished_cortex_spindle", rect, x, y, z):
                        # Finished Cortex Spindle - high-tech implant station
                        pygame.draw.rect(surface, (50, 45, 70), rect)
                        body_rect = pygame.Rect(rect.left + 3, rect.top + 3, rect.width - 6, rect.height - 6)
                        pygame.draw.rect(surface, (70, 65, 100), body_rect)
                        # Central spindle/crystal
                        pygame.draw.circle(surface, (120, 100, 180), (rect.centerx, rect.centery), 5)
                        pygame.draw.circle(surface, (180, 160, 220), (rect.centerx, rect.centery), 3)
                    ws = buildings.get_workstation(x, y, z)
                    if ws:
                        # Show recipe indicator
                        recipe = buildings.get_workstation_recipe(x, y, z)
                        if recipe:
                            recipe_short = recipe.get("name", "?")[:2].upper()
                            recipe_font = pygame.font.Font(None, 14)
                            recipe_text = recipe_font.render(recipe_short, True, (180, 160, 220))
                            surface.blit(recipe_text, (rect.right - 14, rect.top + 2))
                        if ws.get("working", False):
                            # Pulsing glow effect
                            pygame.draw.circle(surface, (200, 150, 255), (rect.centerx, rect.centery), 6, 1)
                            progress = ws.get("progress", 0)
                            if recipe:
                                work_time = recipe.get("work_time", 100)
                                progress_ratio = min(1.0, progress / work_time)
                                bar_width = int((rect.width - 8) * progress_ratio)
                                bar_rect = pygame.Rect(rect.left + 4, rect.bottom - 6, bar_width, 4)
                                pygame.draw.rect(surface, (180, 140, 255), bar_rect)
                elif tile == "finished_barracks":
                    # Try sprite first, fallback to procedural
                    if not self._try_draw_tile_sprite(surface, "finished_barracks", rect, x, y, z):
                        # Finished Barracks - military/tactical station
                        # Dark reinforced base (darker than other stations)
                        pygame.draw.rect(surface, (45, 50, 55), rect)
                        
                        # Armored plating body
                        body_rect = pygame.Rect(rect.left + 2, rect.top + 2, rect.width - 4, rect.height - 4)
                        pygame.draw.rect(surface, (65, 70, 80), body_rect)
                        
                        # Corner armor plates (reinforced look)
                        plate_color = (85, 90, 100)
                        plate_size = 6
                        # Top-left
                        pygame.draw.rect(surface, plate_color, (rect.left + 2, rect.top + 2, plate_size, plate_size))
                        # Top-right
                        pygame.draw.rect(surface, plate_color, (rect.right - plate_size - 2, rect.top + 2, plate_size, plate_size))
                        # Bottom-left
                        pygame.draw.rect(surface, plate_color, (rect.left + 2, rect.bottom - plate_size - 2, plate_size, plate_size))
                        # Bottom-right
                        pygame.draw.rect(surface, plate_color, (rect.right - plate_size - 2, rect.bottom - plate_size - 2, plate_size, plate_size))
                        
                        # Central tactical display (cyan hologram)
                        display_rect = pygame.Rect(rect.centerx - 5, rect.centery - 4, 10, 8)
                        pygame.draw.rect(surface, (30, 40, 45), display_rect)
                        pygame.draw.rect(surface, (0, 200, 220), display_rect, 1)
                        
                        # Tactical grid pattern on display
                        pygame.draw.line(surface, (0, 180, 200), 
                                       (rect.centerx - 4, rect.centery), 
                                       (rect.centerx + 4, rect.centery), 1)
                        pygame.draw.line(surface, (0, 180, 200), 
                                       (rect.centerx, rect.centery - 3), 
                                       (rect.centerx, rect.centery + 3), 1)
                    
                    # Check if training is active
                    ws = buildings.get_workstation(x, y, z)
                    if ws and ws.get("working", False):
                        # Training active - pulsing orange/red indicator
                        pygame.draw.circle(surface, (255, 140, 60), (rect.left + 6, rect.top + 6), 3)
                        # Outer glow
                        pygame.draw.circle(surface, (255, 100, 40), (rect.left + 6, rect.top + 6), 4, 1)
                elif tile == "fire_escape":
                    # Try sprite first (uses finished_fire_escape with construction tint), fallback to procedural
                    if not self._try_draw_tile_sprite(surface, "fire_escape", rect, x, y, z, use_construction_tint=True):
                        pygame.draw.rect(surface, (180, 80, 40), rect)
                    
                    # Show delivered materials (overlay on sprite or procedural)
                    site = buildings.get_construction_site(x, y, z)
                    if site is not None:
                        delivered = site.get("materials_delivered", {})
                        needed = site.get("materials_needed", {})
                        icon_x = rect.left + 2
                        for res_type in needed.keys():
                            has_it = delivered.get(res_type, 0) >= needed.get(res_type, 0)
                            if res_type == "wood":
                                icon_color = COLOR_RESOURCE_NODE_WOOD if has_it else (60, 40, 20)
                            elif res_type == "mineral":
                                icon_color = COLOR_RESOURCE_NODE_MINERAL if has_it else (30, 60, 60)
                            else:
                                icon_color = (100, 100, 100) if has_it else (40, 40, 40)
                            icon_rect = pygame.Rect(icon_x, rect.top + 2, 6, 6)
                            pygame.draw.rect(surface, icon_color, icon_rect)
                            icon_x += 8
                        
                        # Progress bar (overlay on sprite or procedural)
                        job = get_job_at(x, y)
                        if job is not None and job.required > 0:
                            progress_ratio = max(0.0, min(1.0, job.progress / job.required))
                            bar_margin = 4
                            bar_height = 4
                            bar_width = int((config.TILE_SIZE - 2 * bar_margin) * progress_ratio)
                            bar_rect = pygame.Rect(
                                rect.left + bar_margin,
                                rect.bottom - bar_margin - bar_height,
                                bar_width,
                                bar_height,
                            )
                            if bar_width > 0:
                                pygame.draw.rect(surface, COLOR_CONSTRUCTION_PROGRESS, bar_rect)
                elif tile == "finished_fire_escape":
                    # Try sprite first, fallback to procedural
                    if not self._try_draw_tile_sprite(surface, "finished_fire_escape", rect, x, y, z):
                        # Finished fire escape - cool red/orange with grate pattern
                        # Main body - dark red metal
                        pygame.draw.rect(surface, (140, 50, 30), rect)
                        
                        # Draw grate pattern (horizontal and vertical lines)
                        grate_color = (100, 35, 20)
                        highlight_color = (180, 70, 40)
                        
                        # Horizontal grate lines
                        for gy_offset in range(4, config.TILE_SIZE - 2, 6):
                            pygame.draw.line(surface, grate_color, 
                                           (rect.left + 2, rect.top + gy_offset),
                                           (rect.right - 2, rect.top + gy_offset), 1)
                        
                        # Vertical grate lines
                        for gx_offset in range(4, config.TILE_SIZE - 2, 6):
                            pygame.draw.line(surface, grate_color,
                                           (rect.left + gx_offset, rect.top + 2),
                                           (rect.left + gx_offset, rect.bottom - 2), 1)
                        
                        # Highlight edges for 3D effect
                        pygame.draw.line(surface, highlight_color, rect.topleft, (rect.right - 1, rect.top), 2)
                        pygame.draw.line(surface, highlight_color, rect.topleft, (rect.left, rect.bottom - 1), 2)
                        
                        # Draw ladder rungs in center
                        ladder_color = (200, 100, 50)
                        center_x = rect.centerx
                        for rung_y in range(rect.top + 6, rect.bottom - 4, 8):
                            pygame.draw.line(surface, ladder_color,
                                           (center_x - 6, rung_y),
                                           (center_x + 6, rung_y), 2)
                        
                        # Ladder rails
                        pygame.draw.line(surface, ladder_color,
                                   (center_x - 8, rect.top + 2),
                                   (center_x - 8, rect.bottom - 2), 2)
                        pygame.draw.line(surface, ladder_color,
                                   (center_x + 8, rect.top + 2),
                                   (center_x + 8, rect.bottom - 2), 2)
                        
                        # Small up/down arrow indicator
                        arrow_color = (255, 200, 100)
                        # Up arrow
                        pygame.draw.polygon(surface, arrow_color, [
                            (rect.right - 8, rect.top + 8),
                            (rect.right - 4, rect.top + 12),
                            (rect.right - 12, rect.top + 12),
                        ])
                        # Down arrow
                        pygame.draw.polygon(surface, arrow_color, [
                            (rect.right - 8, rect.bottom - 8),
                            (rect.right - 4, rect.bottom - 12),
                            (rect.right - 12, rect.bottom - 12),
                        ])
                
                elif tile == "window_tile":
                    # Window tile - wall with passable window opening
                    # Base wall color (same as finished wall)
                    pygame.draw.rect(surface, COLOR_TILE_FINISHED_WALL, rect)
                    
                    # Draw window opening in center - darker interior
                    window_margin = 6
                    window_rect = pygame.Rect(
                        rect.left + window_margin,
                        rect.top + window_margin,
                        rect.width - 2 * window_margin,
                        rect.height - 2 * window_margin
                    )
                    pygame.draw.rect(surface, (30, 30, 40), window_rect)
                    
                    # Window frame - lighter border
                    frame_color = (120, 100, 80)
                    pygame.draw.rect(surface, frame_color, window_rect, 2)
                    
                    # Cross bars on window
                    pygame.draw.line(surface, frame_color,
                                   (window_rect.centerx, window_rect.top),
                                   (window_rect.centerx, window_rect.bottom), 2)
                    pygame.draw.line(surface, frame_color,
                                   (window_rect.left, window_rect.centery),
                                   (window_rect.right, window_rect.centery), 2)
                
                elif tile == "fire_escape_platform":
                    # External fire escape platform - metal grating
                    # Dark metal base
                    pygame.draw.rect(surface, (70, 65, 60), rect)
                    
                    # Grate pattern
                    grate_color = (50, 45, 40)
                    for gy_offset in range(2, config.TILE_SIZE, 4):
                        pygame.draw.line(surface, grate_color,
                                       (rect.left, rect.top + gy_offset),
                                       (rect.right, rect.top + gy_offset), 1)
                    for gx_offset in range(2, config.TILE_SIZE, 4):
                        pygame.draw.line(surface, grate_color,
                                       (rect.left + gx_offset, rect.top),
                                       (rect.left + gx_offset, rect.bottom), 1)
                    
                    # Highlight edges
                    highlight_color = (100, 95, 90)
                    pygame.draw.line(surface, highlight_color, rect.topleft, (rect.right - 1, rect.top), 1)
                    pygame.draw.line(surface, highlight_color, rect.topleft, (rect.left, rect.bottom - 1), 1)
                    
                    # Railing indicator on edges
                    rail_color = (90, 80, 70)
                    pygame.draw.rect(surface, rail_color, (rect.left, rect.top, rect.width, 3))
                    pygame.draw.rect(surface, rail_color, (rect.left, rect.bottom - 3, rect.width, 3))
                
                elif tile in ("bridge", "finished_bridge"):
                    # Try sprite first, fallback to procedural
                    sprite_name = "finished_bridge" if tile == "finished_bridge" else "bridge"
                    use_tint = (tile == "bridge")  # Apply construction tint for under-construction bridge
                    if not self._try_draw_tile_sprite(surface, sprite_name, rect, x, y, z, use_construction_tint=use_tint):
                        # Bridge - wooden planks with metal supports
                        is_finished = tile == "finished_bridge"
                        
                        if is_finished:
                            # Finished bridge - warm wood color
                            base_color = (140, 100, 60)
                            plank_color = (120, 80, 45)
                            edge_color = (80, 60, 40)
                        else:
                            # Under construction - blueprint style
                            base_color = (80, 80, 100)
                            plank_color = (60, 60, 80)
                            edge_color = (50, 50, 70)
                        
                        # Base
                        pygame.draw.rect(surface, base_color, rect)
                        
                        # Plank lines (horizontal)
                        for py_offset in range(4, config.TILE_SIZE, 6):
                            pygame.draw.line(surface, plank_color,
                                           (rect.left + 2, rect.top + py_offset),
                                           (rect.right - 2, rect.top + py_offset), 1)
                        
                        # Metal edge supports
                        pygame.draw.rect(surface, edge_color, (rect.left, rect.top, 3, rect.height))
                        pygame.draw.rect(surface, edge_color, (rect.right - 3, rect.top, 3, rect.height))
                        
                        # Highlight for 3D effect
                        if is_finished:
                            pygame.draw.line(surface, (180, 140, 100), rect.topleft, (rect.right - 1, rect.top), 1)
                
                # Draw stockpile zone background AFTER floor tiles (on current Z level)
                if zones.is_stockpile_zone(x, y, z):
                    # Semi-transparent green overlay
                    zone_surface = pygame.Surface((config.TILE_SIZE, config.TILE_SIZE), pygame.SRCALPHA)
                    zone_surface.fill(COLOR_ZONE_STOCKPILE)
                    surface.blit(zone_surface, rect.topleft)
                    
                    # Draw resource stacks and equipment on top
                    tile_storage = zones.get_tile_storage(x, y, z)
                    equipment_storage = zones.get_equipment_at_tile(x, y, z)
                    
                    if tile_storage is not None:
                        res_type = tile_storage.get("type", "")
                        amount = tile_storage.get("amount", 0)
                        
                        # Use styled stockpile resource drawing
                        self._draw_stockpile_resource(surface, rect, res_type, amount, x, y, z)
                    
                    # Draw equipment stored in stockpile
                    if equipment_storage:
                        from items import get_item_def
                        first_item = equipment_storage[0]
                        item_id = first_item.get("id", "")
                        item_def = get_item_def(item_id)
                        if item_def and item_def.icon_color:
                            equip_color = item_def.icon_color
                        else:
                            equip_color = (160, 140, 200)
                        
                        # Draw diamond in center (or offset if resources present)
                        cx = rect.centerx + (8 if tile_storage else 0)
                        cy = rect.centery
                        points = [(cx, cy - 6), (cx + 6, cy), (cx, cy + 6), (cx - 6, cy)]
                        pygame.draw.polygon(surface, equip_color, points)
                        pygame.draw.polygon(surface, (255, 255, 255), points, 1)
                        
                        # Show count if multiple
                        if len(equipment_storage) > 1:
                            count_font = pygame.font.Font(None, 14)
                            count_text = count_font.render(str(len(equipment_storage)), True, (255, 255, 255))
                            surface.blit(count_text, (cx + 4, cy - 8))
                
                # Roof tile rendering (for z=1 level)
                if tile == "roof":
                    # Dark purple roof tile with pattern
                    pygame.draw.rect(surface, (60, 40, 80), rect)
                    # Diagonal lines pattern
                    for i in range(0, config.TILE_SIZE * 2, 8):
                        pygame.draw.line(surface, (80, 60, 100),
                                       (rect.left + i, rect.top),
                                       (rect.left, rect.top + i), 1)
                
                elif tile == "roof_floor" or tile == "roof_access":
                    # Try sprite first, fallback to procedural
                    sprite_name = "roof_access" if tile == "roof_access" else "roof_floor"
                    if not self._try_draw_tile_sprite(surface, sprite_name, rect, x, y, z):
                        # Allowed rooftop floor - looks exactly like finished_floor
                        # Same warm wood color with subtle plank pattern
                        pygame.draw.rect(surface, (160, 130, 90), rect)
                    # Draw subtle plank lines (same as finished_floor)
                    plank_color = (140, 110, 70)
                    pygame.draw.line(surface, plank_color, (rect.left, rect.top + 8), (rect.right, rect.top + 8), 1)
                    pygame.draw.line(surface, plank_color, (rect.left, rect.bottom - 8), (rect.right, rect.bottom - 8), 1)
                
                elif tile == "resource_node":
                    # Get node data to determine color by resource type
                    node = resources.get_node_at(x, y)
                    if node:
                        resource_type = node.get("resource", "")
                        node_state = node.get("state")
                        from resources import NodeState
                        depleted = node_state == NodeState.DEPLETED
                        
                        rendered = False
                        if resource_type == "wood":
                            self._draw_wood_node(surface, rect, x, y, z, depleted)
                            rendered = True
                        elif resource_type == "scrap":
                            self._draw_scrap_node(surface, rect, x, y, z, depleted)
                            rendered = True
                        elif resource_type == "metal":
                            color = COLOR_RESOURCE_NODE_METAL
                        elif resource_type == "mineral":
                            self._draw_mineral_node(surface, rect, x, y, z, depleted)
                            rendered = True
                        elif resource_type == "raw_food":
                            # Try to load sprite first (raw_food_node_0 through raw_food_node_X)
                            if self._try_draw_tile_sprite(surface, "raw_food_node", rect, x, y, z, use_construction_tint=depleted):
                                rendered = True
                            else:
                                color = COLOR_RESOURCE_NODE_RAW_FOOD
                        else:
                            color = COLOR_RESOURCE_NODE_DEFAULT
                        
                        if not rendered:
                            if depleted:
                                color = (color[0] // 3, color[1] // 3, color[2] // 3)
                            pygame.draw.rect(surface, color, rect)
                        
                        # Draw state symbol overlay
                        if node_state == NodeState.RESERVED:
                            # Yellow diamond - waiting for colonist to arrive
                            cx = rect.centerx
                            cy = rect.centery
                            size = 6
                            points = [
                                (cx, cy - size),  # top
                                (cx + size, cy),  # right
                                (cx, cy + size),  # bottom
                                (cx - size, cy),  # left
                            ]
                            pygame.draw.polygon(surface, COLOR_NODE_RESERVED, points)
                        elif node_state == NodeState.IN_PROGRESS:
                            # Green progress bar at bottom - like construction tiles
                            job = get_job_at(x, y)
                            if job is not None and job.required > 0:
                                progress_ratio = max(0.0, min(1.0, job.progress / job.required))
                                bar_margin = 4
                                bar_height = 4
                                bar_width = int((config.TILE_SIZE - 2 * bar_margin) * progress_ratio)
                                bar_rect = pygame.Rect(
                                    rect.left + bar_margin,
                                    rect.bottom - bar_margin - bar_height,
                                    bar_width,
                                    bar_height,
                                )
                                if bar_width > 0:
                                    pygame.draw.rect(surface, COLOR_NODE_IN_PROGRESS, bar_rect)
                    else:
                        pygame.draw.rect(surface, COLOR_RESOURCE_NODE_DEFAULT, rect)
                elif tile == "resource_pile":
                    pygame.draw.rect(surface, COLOR_RESOURCE_PILE, rect)
                elif tile == "salvage_object":
                    # Salvage object - rusted metal/tech appearance
                    salvage = resources.get_salvage_object_at(x, y)
                    if salvage:
                        is_designated = salvage.get("designated", False)
                        salvage_type = salvage.get("type", "ruined_tech")
                        
                        # Try to load sprite first (scrap_node_0 through scrap_node_5)
                        if not self._try_draw_tile_sprite(surface, "scrap_node", rect, x, y, z, use_construction_tint=is_designated):
                            # Fallback to procedural rendering
                            # Base color varies by type
                            if salvage_type == "ruined_tech":
                                base_color = (140, 80, 50)  # Rusty orange
                                detail_color = (80, 70, 60)
                            elif salvage_type == "ruined_wall":
                                base_color = (85, 75, 70)  # Dark gray-brown (ruined wall)
                                detail_color = (60, 55, 50)
                            else:  # salvage_pile
                                base_color = (100, 90, 80)  # Grayish brown
                                detail_color = (70, 65, 55)
                            
                            pygame.draw.rect(surface, base_color, rect)
                            
                            # Draw type-specific details
                            if salvage_type == "ruined_wall":
                                # Cracked wall pattern
                                pygame.draw.line(surface, detail_color,
                                               (rect.left + 3, rect.top + 3),
                                               (rect.centerx, rect.centery), 2)
                                pygame.draw.line(surface, detail_color,
                                               (rect.right - 3, rect.top + 5),
                                               (rect.centerx, rect.centery), 2)
                                pygame.draw.line(surface, detail_color,
                                               (rect.centerx, rect.centery),
                                               (rect.left + 5, rect.bottom - 3), 2)
                            else:
                                # Metal scraps pattern
                                pygame.draw.line(surface, detail_color, 
                                               (rect.left + 4, rect.top + 6),
                                               (rect.right - 4, rect.top + 6), 2)
                                pygame.draw.line(surface, detail_color,
                                               (rect.left + 6, rect.centery),
                                               (rect.right - 6, rect.centery), 2)
                                pygame.draw.line(surface, detail_color,
                                               (rect.left + 4, rect.bottom - 6),
                                               (rect.right - 4, rect.bottom - 6), 2)
                        
                        # Yellow border if designated
                        if is_designated:
                            pygame.draw.rect(surface, (255, 200, 50), rect, 2)
                    else:
                        pygame.draw.rect(surface, (100, 80, 60), rect)
                
                # Draw resource items (dropped items awaiting pickup) - ground level only
                if is_ground_level:
                    resource_item = resources.get_resource_item_at(x, y)
                    if resource_item:
                        item_type = resource_item.get("type", "")
                        if item_type == "wood":
                            item_color = COLOR_RESOURCE_NODE_WOOD
                        elif item_type == "scrap":
                            item_color = COLOR_RESOURCE_NODE_SCRAP
                        elif item_type == "metal":
                            item_color = COLOR_RESOURCE_NODE_METAL
                        elif item_type == "mineral":
                            item_color = COLOR_RESOURCE_NODE_MINERAL
                        elif item_type == "power":
                            item_color = COLOR_RESOURCE_NODE_POWER
                        elif item_type == "raw_food":
                            item_color = COLOR_RESOURCE_NODE_RAW_FOOD
                        elif item_type == "cooked_meal":
                            item_color = COLOR_RESOURCE_NODE_COOKED_MEAL
                        else:
                            item_color = (200, 200, 200)
                        
                        # Draw small square in corner to indicate dropped item
                        item_size = 8
                        item_rect = pygame.Rect(
                            rect.right - item_size - 2,
                            rect.top + 2,
                            item_size,
                            item_size,
                        )
                        pygame.draw.rect(surface, item_color, item_rect)
                        pygame.draw.rect(surface, (255, 255, 255), item_rect, 1)  # White border
                
                # Draw world items (equipment/crafted items) on any Z level
                from items import get_world_items_at, get_item_def
                world_items = get_world_items_at(x, y, z)
                if world_items:
                    # Get first item's color
                    first_item = world_items[0]
                    item_id = first_item.get("id", "")
                    item_def = get_item_def(item_id)
                    if item_def and item_def.icon_color:
                        item_color = item_def.icon_color
                    else:
                        item_color = (160, 140, 200)  # Default purple for equipment
                    
                    # Draw diamond shape in bottom-left corner
                    cx = rect.left + 6
                    cy = rect.bottom - 6
                    points = [(cx, cy - 4), (cx + 4, cy), (cx, cy + 4), (cx - 4, cy)]
                    pygame.draw.polygon(surface, item_color, points)
                    pygame.draw.polygon(surface, (255, 255, 255), points, 1)
                    
                    # Show count if multiple
                    if len(world_items) > 1:
                        count_font = pygame.font.Font(None, 14)
                        count_text = count_font.render(str(len(world_items)), True, (255, 255, 255))
                        surface.blit(count_text, (cx + 5, cy - 6))

                # Grid lines - teal-tinted dotted lines to match UI theme
                # Draw dotted grid lines (every 4 pixels)
                grid_color = COLOR_GRID_LINES
                dot_spacing = 4
                
                # Right edge (vertical dotted line)
                for py in range(rect.top, rect.bottom, dot_spacing * 2):
                    pygame.draw.line(surface, grid_color, (rect.right - 1, py), (rect.right - 1, min(py + dot_spacing, rect.bottom)), 1)
                
                # Bottom edge (horizontal dotted line)
                for px in range(rect.left, rect.right, dot_spacing * 2):
                    pygame.draw.line(surface, grid_color, (px, rect.bottom - 1), (min(px + dot_spacing, rect.right), rect.bottom - 1), 1)
                
                # Thicker solid lines every 10 tiles for better readability (teal accent)
                grid_major_color = (60, 100, 110)  # Brighter teal for major lines
                if x % 10 == 0:
                    pygame.draw.line(surface, grid_major_color, (rect.left, rect.top), (rect.left, rect.bottom), 1)
                if y % 10 == 0:
                    pygame.draw.line(surface, grid_major_color, (rect.left, rect.top), (rect.right, rect.top), 1)
                
                # Job/designation category debug border - for tiles with active jobs or designations
                if is_ground_level:
                    category_color = None
                    
                    # First check for active job
                    job = get_job_at(x, y)
                    if job is not None:
                        if job.category == "wall":
                            category_color = COLOR_JOB_CATEGORY_WALL
                        elif job.category == "harvest":
                            category_color = COLOR_JOB_CATEGORY_HARVEST
                        elif job.category == "construction":
                            category_color = COLOR_JOB_CATEGORY_CONSTRUCTION
                        elif job.category == "haul":
                            category_color = COLOR_JOB_CATEGORY_HAUL
                        elif job.category == "salvage":
                            category_color = COLOR_JOB_CATEGORY_HARVEST  # Use harvest color for salvage
                    
                    # If no job, check for designation (persistent highlight)
                    if category_color is None:
                        designation_cat = get_designation_category(x, y, self.current_z)
                        if designation_cat == "harvest":
                            category_color = COLOR_JOB_CATEGORY_HARVEST
                        elif designation_cat == "haul":
                            category_color = COLOR_JOB_CATEGORY_HAUL
                        elif designation_cat == "salvage":
                            category_color = COLOR_JOB_CATEGORY_HARVEST  # Use harvest color for salvage
                    
                    if category_color is not None:
                        # Draw thick border inside the tile
                        pygame.draw.rect(surface, category_color, rect, 2)
