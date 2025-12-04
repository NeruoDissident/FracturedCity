"""Grid management and tile rendering.

Responsible for:
- storing tile state
- providing helpers to mutate/query tiles
- drawing the grid and tile contents to a Pygame surface

The tile representation is intentionally simple (string markers) so it can be
extended later to richer objects (rooms, zones, buildings, etc.).
"""

import pygame

from config import (
    TILE_SIZE,
    GRID_W,
    GRID_H,
    GRID_Z,
    COLOR_GRID_LINES,
    COLOR_TILE_SELECTED,
    COLOR_TILE_BUILDING,
    COLOR_TILE_FINISHED_BUILDING,
    COLOR_TILE_WALL,
    COLOR_TILE_FINISHED_WALL,
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
from jobs import get_job_at
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
        
        # Current view level (for rendering)
        self.current_z = 0

    def in_bounds(self, x: int, y: int, z: int = 0) -> bool:
        """Return True if (x, y, z) lies inside the grid."""
        return 0 <= x < self.width and 0 <= y < self.height and 0 <= z < self.depth

    def set_tile(self, x: int, y: int, value: str, z: int = 0) -> None:
        """Set the logical value of a tile if coordinates are valid.
        
        Automatically updates walkability for building tiles.
        """
        if self.in_bounds(x, y, z):
            self.tiles[z][y][x] = value
            # Only finished buildings/walls block movement, not those under construction
            # Doors are handled specially - they can be opened
            # Fire escapes are walkable (they're transition points)
            # roof tiles are NOT walkable - must be converted to roof_access first
            if value in ("finished_building", "finished_wall", "finished_wall_advanced", "roof", "finished_salvagers_bench", "finished_generator", "finished_stove"):
                self.walkable[z][y][x] = False
            elif value == "finished_window":
                # Windows are passable (like doors) - colonists can climb through
                self.walkable[z][y][x] = True
            elif value in ("empty", "building", "wall", "wall_advanced", "door", "floor", "finished_floor", "roof_floor", "roof_access", "fire_escape", "finished_fire_escape", "window_tile", "fire_escape_platform", "window", "bridge", "finished_bridge", "salvagers_bench", "generator", "stove"):
                # window_tile: passable wall with fire escape window
                # fire_escape_platform: external platform for fire escape
                # roof_access: walkable/buildable rooftop tile (player-allowed)
                # roof_floor: legacy walkable roof (kept for compatibility)
                # bridge/finished_bridge: walkable connections between buildings
                self.walkable[z][y][x] = True

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

    def draw(self, surface: pygame.Surface, hovered_tile: tuple[int, int] | None = None) -> None:
        """Render the grid and its tiles to the given surface.
        
        If hovered_tile is provided, that tile will be highlighted momentarily.
        Only draws tiles from the current Z-level.
        """
        z = self.current_z
        is_ground_level = (z == 0)

        for y in range(self.height):
            for x in range(self.width):
                rect = pygame.Rect(
                    x * TILE_SIZE,
                    y * TILE_SIZE,
                    TILE_SIZE,
                    TILE_SIZE,
                )

                tile = self.tiles[z][y][x]

                # Draw stockpile zone background (on current Z level)
                # Resource stacks are drawn later, after floor tiles
                if zones.is_stockpile_zone(x, y, z):
                    # Semi-transparent green overlay
                    zone_surface = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
                    zone_surface.fill(COLOR_ZONE_STOCKPILE)
                    surface.blit(zone_surface, rect.topleft)
                
                # Momentary hover highlight (no sticky selection)
                if hovered_tile is not None and hovered_tile == (x, y):
                    pygame.draw.rect(surface, COLOR_TILE_SELECTED, rect)
                elif tile == "building":
                    pygame.draw.rect(surface, COLOR_TILE_BUILDING, rect)

                    # Optional: small progress bar for the construction job on
                    # this tile, if one exists.
                    job = get_job_at(x, y)
                    if job is not None and job.required > 0:
                        progress_ratio = max(0.0, min(1.0, job.progress / job.required))
                        bar_margin = 4
                        bar_height = 4
                        bar_width = int((TILE_SIZE - 2 * bar_margin) * progress_ratio)
                        bar_rect = pygame.Rect(
                            rect.left + bar_margin,
                            rect.bottom - bar_margin - bar_height,
                            bar_width,
                            bar_height,
                        )
                        if bar_width > 0:
                            pygame.draw.rect(surface, COLOR_CONSTRUCTION_PROGRESS, bar_rect)
                elif tile == "finished_building":
                    pygame.draw.rect(surface, COLOR_TILE_FINISHED_BUILDING, rect)
                elif tile == "wall":
                    pygame.draw.rect(surface, COLOR_TILE_WALL, rect)
                    
                    # Show delivered materials as small icons
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
                    
                    # Progress bar for wall construction
                    job = get_job_at(x, y)
                    if job is not None and job.required > 0:
                        progress_ratio = max(0.0, min(1.0, job.progress / job.required))
                        bar_margin = 4
                        bar_height = 4
                        bar_width = int((TILE_SIZE - 2 * bar_margin) * progress_ratio)
                        bar_rect = pygame.Rect(
                            rect.left + bar_margin,
                            rect.bottom - bar_margin - bar_height,
                            bar_width,
                            bar_height,
                        )
                        if bar_width > 0:
                            pygame.draw.rect(surface, COLOR_CONSTRUCTION_PROGRESS, bar_rect)
                elif tile == "finished_wall":
                    pygame.draw.rect(surface, COLOR_TILE_FINISHED_WALL, rect)
                elif tile == "wall_advanced":
                    # Reinforced wall under construction - darker gray
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
                        bar_width = int((TILE_SIZE - 2 * bar_margin) * progress_ratio)
                        bar_rect = pygame.Rect(
                            rect.left + bar_margin,
                            rect.bottom - bar_margin - bar_height,
                            bar_width,
                            bar_height,
                        )
                        if bar_width > 0:
                            pygame.draw.rect(surface, COLOR_CONSTRUCTION_PROGRESS, bar_rect)
                elif tile == "finished_wall_advanced":
                    # Finished reinforced wall - steel blue
                    pygame.draw.rect(surface, (80, 90, 110), rect)
                elif tile == "door":
                    # Door tile - check if open or closed
                    is_open = buildings.is_door_open(x, y)
                    site = buildings.get_construction_site(x, y, z)
                    
                    if site is not None:
                        # Under construction - brown/orange tint
                        pygame.draw.rect(surface, (100, 70, 40), rect)
                        
                        # Show delivered materials
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
                        
                        # Progress bar
                        job = get_job_at(x, y)
                        if job is not None and job.required > 0:
                            progress_ratio = max(0.0, min(1.0, job.progress / job.required))
                            bar_margin = 4
                            bar_height = 4
                            bar_width = int((TILE_SIZE - 2 * bar_margin) * progress_ratio)
                            bar_rect = pygame.Rect(
                                rect.left + bar_margin,
                                rect.bottom - bar_margin - bar_height,
                                bar_width,
                                bar_height,
                            )
                            if bar_width > 0:
                                pygame.draw.rect(surface, COLOR_CONSTRUCTION_PROGRESS, bar_rect)
                    elif is_open:
                        # Open door - lighter, with gap in middle
                        pygame.draw.rect(surface, (60, 50, 40), rect)
                        # Draw open gap
                        gap_rect = pygame.Rect(rect.left + 6, rect.top + 2, rect.width - 12, rect.height - 4)
                        pygame.draw.rect(surface, (30, 25, 20), gap_rect)
                    else:
                        # Closed door - solid brown
                        pygame.draw.rect(surface, (120, 80, 50), rect)
                        # Door handle
                        handle_rect = pygame.Rect(rect.right - 8, rect.centery - 2, 4, 4)
                        pygame.draw.rect(surface, (180, 150, 100), handle_rect)
                elif tile == "window":
                    # Window under construction - light blue-gray
                    pygame.draw.rect(surface, (100, 110, 130), rect)
                    
                    # Show delivered materials
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
                        
                        # Progress bar
                        job = get_job_at(x, y)
                        if job is not None and job.required > 0:
                            progress_ratio = max(0.0, min(1.0, job.progress / job.required))
                            bar_margin = 4
                            bar_height = 4
                            bar_width = int((TILE_SIZE - 2 * bar_margin) * progress_ratio)
                            bar_rect = pygame.Rect(
                                rect.left + bar_margin,
                                rect.bottom - bar_margin - bar_height,
                                bar_width,
                                bar_height,
                            )
                            if bar_width > 0:
                                pygame.draw.rect(surface, COLOR_CONSTRUCTION_PROGRESS, bar_rect)
                elif tile == "finished_window":
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
                    # Floor under construction - light tan with wood icon
                    pygame.draw.rect(surface, (140, 120, 90), rect)
                    
                    # Show delivered materials
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
                        
                        # Progress bar
                        job = get_job_at(x, y)
                        if job is not None and job.required > 0:
                            progress_ratio = max(0.0, min(1.0, job.progress / job.required))
                            bar_margin = 4
                            bar_height = 4
                            bar_width = int((TILE_SIZE - 2 * bar_margin) * progress_ratio)
                            bar_rect = pygame.Rect(
                                rect.left + bar_margin,
                                rect.bottom - bar_margin - bar_height,
                                bar_width,
                                bar_height,
                            )
                            if bar_width > 0:
                                pygame.draw.rect(surface, COLOR_CONSTRUCTION_PROGRESS, bar_rect)
                elif tile == "finished_floor":
                    # Finished floor - warm wood color with subtle plank pattern
                    pygame.draw.rect(surface, (160, 130, 90), rect)
                    # Draw subtle plank lines
                    plank_color = (140, 110, 70)
                    pygame.draw.line(surface, plank_color, (rect.left, rect.top + 8), (rect.right, rect.top + 8), 1)
                    pygame.draw.line(surface, plank_color, (rect.left, rect.bottom - 8), (rect.right, rect.bottom - 8), 1)
                elif tile == "salvagers_bench":
                    # Salvager's bench under construction - rusty orange
                    pygame.draw.rect(surface, (140, 90, 50), rect)
                    
                    # Show delivered materials
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
                            bar_width = int((TILE_SIZE - 2 * bar_margin) * progress_ratio)
                            bar_rect = pygame.Rect(
                                rect.left + bar_margin,
                                rect.bottom - bar_margin - bar_height,
                                bar_width,
                                bar_height,
                            )
                            if bar_width > 0:
                                pygame.draw.rect(surface, COLOR_CONSTRUCTION_PROGRESS, bar_rect)
                elif tile == "finished_salvagers_bench":
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
                elif tile == "finished_generator":
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
                    
                    # Orange heat indicator when working
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
                elif tile == "fire_escape":
                    # Fire escape under construction - orange/red base
                    pygame.draw.rect(surface, (180, 80, 40), rect)
                    
                    # Show delivered materials
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
                        
                        # Progress bar
                        job = get_job_at(x, y)
                        if job is not None and job.required > 0:
                            progress_ratio = max(0.0, min(1.0, job.progress / job.required))
                            bar_margin = 4
                            bar_height = 4
                            bar_width = int((TILE_SIZE - 2 * bar_margin) * progress_ratio)
                            bar_rect = pygame.Rect(
                                rect.left + bar_margin,
                                rect.bottom - bar_margin - bar_height,
                                bar_width,
                                bar_height,
                            )
                            if bar_width > 0:
                                pygame.draw.rect(surface, COLOR_CONSTRUCTION_PROGRESS, bar_rect)
                elif tile == "finished_fire_escape":
                    # Finished fire escape - cool red/orange with grate pattern
                    # Main body - dark red metal
                    pygame.draw.rect(surface, (140, 50, 30), rect)
                    
                    # Draw grate pattern (horizontal and vertical lines)
                    grate_color = (100, 35, 20)
                    highlight_color = (180, 70, 40)
                    
                    # Horizontal grate lines
                    for gy_offset in range(4, TILE_SIZE - 2, 6):
                        pygame.draw.line(surface, grate_color, 
                                       (rect.left + 2, rect.top + gy_offset),
                                       (rect.right - 2, rect.top + gy_offset), 1)
                    
                    # Vertical grate lines
                    for gx_offset in range(4, TILE_SIZE - 2, 6):
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
                    for gy_offset in range(2, TILE_SIZE, 4):
                        pygame.draw.line(surface, grate_color,
                                       (rect.left, rect.top + gy_offset),
                                       (rect.right, rect.top + gy_offset), 1)
                    for gx_offset in range(2, TILE_SIZE, 4):
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
                    for py_offset in range(4, TILE_SIZE, 6):
                        pygame.draw.line(surface, plank_color,
                                       (rect.left + 2, rect.top + py_offset),
                                       (rect.right - 2, rect.top + py_offset), 1)
                    
                    # Metal edge supports
                    pygame.draw.rect(surface, edge_color, (rect.left, rect.top, 3, rect.height))
                    pygame.draw.rect(surface, edge_color, (rect.right - 3, rect.top, 3, rect.height))
                    
                    # Highlight for 3D effect
                    if is_finished:
                        pygame.draw.line(surface, (180, 140, 100), rect.topleft, (rect.right - 1, rect.top), 1)
                
                # Draw stockpile resource stacks ON TOP of floor tiles (on current Z level)
                if zones.is_stockpile_zone(x, y, z):
                    tile_storage = zones.get_tile_storage(x, y, z)
                    if tile_storage is not None:
                        res_type = tile_storage.get("type", "")
                        amount = tile_storage.get("amount", 0)
                        
                        # Color based on resource type
                        if res_type == "wood":
                            stack_color = COLOR_RESOURCE_NODE_WOOD
                        elif res_type == "scrap":
                            stack_color = COLOR_RESOURCE_NODE_SCRAP
                        elif res_type == "metal":
                            stack_color = COLOR_RESOURCE_NODE_METAL
                        elif res_type == "mineral":
                            stack_color = COLOR_RESOURCE_NODE_MINERAL
                        elif res_type == "raw_food":
                            stack_color = COLOR_RESOURCE_NODE_RAW_FOOD
                        elif res_type == "cooked_meal":
                            stack_color = COLOR_RESOURCE_NODE_COOKED_MEAL
                        elif res_type == "power":
                            stack_color = COLOR_RESOURCE_NODE_POWER
                        else:
                            stack_color = (150, 150, 150)
                        
                        # Draw stack - size based on amount (max 10)
                        fill_ratio = min(1.0, amount / 10.0)
                        stack_size = int(8 + 16 * fill_ratio)  # 8 to 24 pixels
                        stack_rect = pygame.Rect(
                            rect.centerx - stack_size // 2,
                            rect.centery - stack_size // 2,
                            stack_size,
                            stack_size,
                        )
                        pygame.draw.rect(surface, stack_color, stack_rect)
                        pygame.draw.rect(surface, (255, 255, 255), stack_rect, 1)
                
                # Roof tile rendering (for z=1 level)
                if tile == "roof":
                    # Dark purple roof tile with pattern
                    pygame.draw.rect(surface, (60, 40, 80), rect)
                    # Diagonal lines pattern
                    for i in range(0, TILE_SIZE * 2, 8):
                        pygame.draw.line(surface, (80, 60, 100),
                                       (rect.left + i, rect.top),
                                       (rect.left, rect.top + i), 1)
                
                elif tile == "roof_floor" or tile == "roof_access":
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
                        if resource_type == "wood":
                            color = COLOR_RESOURCE_NODE_WOOD
                        elif resource_type == "scrap":
                            color = COLOR_RESOURCE_NODE_SCRAP
                        elif resource_type == "metal":
                            color = COLOR_RESOURCE_NODE_METAL
                        elif resource_type == "mineral":
                            color = COLOR_RESOURCE_NODE_MINERAL
                        elif resource_type == "raw_food":
                            color = COLOR_RESOURCE_NODE_RAW_FOOD
                        else:
                            color = COLOR_RESOURCE_NODE_DEFAULT
                        
                        # Darken if depleted
                        node_state = node.get("state")
                        from resources import NodeState
                        if node_state == NodeState.DEPLETED:
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
                                bar_width = int((TILE_SIZE - 2 * bar_margin) * progress_ratio)
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

                # Draw roof overlay if this tile has a roof (ground level only - shows roof above)
                if is_ground_level and rooms.has_roof(x, y):
                    # Semi-transparent dark overlay to show roof coverage
                    roof_surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
                    roof_surf.fill((40, 30, 50, 140))  # Dark purple-ish tint
                    surface.blit(roof_surf, rect)
                    # Draw subtle roof pattern (diagonal lines)
                    for i in range(0, TILE_SIZE * 2, 8):
                        start_x = rect.left + i
                        start_y = rect.top
                        end_x = rect.left + i - TILE_SIZE
                        end_y = rect.bottom
                        pygame.draw.line(surface, (60, 50, 70, 100), 
                                       (max(rect.left, start_x), max(rect.top, start_y + (start_x - max(rect.left, start_x)))),
                                       (max(rect.left, end_x + TILE_SIZE), min(rect.bottom, end_y)), 1)

                # Grid lines are always drawn on top of tile background.
                pygame.draw.rect(surface, COLOR_GRID_LINES, rect, 1)
                
                # Job category debug border - only for tiles with active jobs (ground level only)
                if is_ground_level:
                    job = get_job_at(x, y)
                    if job is not None:
                        category_color = None
                        if job.category == "wall":
                            category_color = COLOR_JOB_CATEGORY_WALL
                        elif job.category == "harvest":
                            category_color = COLOR_JOB_CATEGORY_HARVEST
                        elif job.category == "construction":
                            category_color = COLOR_JOB_CATEGORY_CONSTRUCTION
                        elif job.category == "haul":
                            category_color = COLOR_JOB_CATEGORY_HAUL
                        
                        if category_color is not None:
                            # Draw thick border inside the tile
                            pygame.draw.rect(surface, category_color, rect, 2)
