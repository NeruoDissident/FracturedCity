"""UI Layout and Panel System for Fractured City.

Provides a cyberpunk-styled UI layout with:
- Top bar: Time, Z-level, resources, alerts
- Left sidebar: Tabbed panels (Build, Colonists, Items)
- Bottom bar: Tile info, selected colonist, tooltips
- Map viewport: Main game area (center)

This module only handles visual layout and rendering.
All game logic remains in existing modules.
"""

import pygame
from typing import Optional, List, Dict, Tuple, Callable
from config import SCREEN_W, SCREEN_H
from ui_config import TOOLTIPS, SUBMENUS, get_tooltip, add_tooltip, get_submenu

# ============================================================================
# CYBERPUNK COLOR PALETTE
# ============================================================================

# Base colors - deep dark backgrounds
COLOR_BG_DARK = (12, 14, 18)           # Darkest background
COLOR_BG_PANEL = (18, 22, 28)          # Panel background
COLOR_BG_PANEL_LIGHT = (28, 34, 42)    # Lighter panel areas
COLOR_BG_HEADER = (22, 28, 36)         # Header backgrounds

# Accent colors - neon cyan/teal
COLOR_ACCENT_CYAN = (0, 220, 220)      # Primary accent (borders, highlights)
COLOR_ACCENT_CYAN_DIM = (0, 100, 110)  # Dimmed cyan
COLOR_ACCENT_CYAN_GLOW = (0, 255, 255) # Bright glow

# Accent colors - neon pink/magenta
COLOR_ACCENT_PINK = (255, 50, 130)     # Hot pink accent
COLOR_ACCENT_PINK_DIM = (180, 40, 90)  # Dimmed pink
COLOR_ACCENT_PURPLE = (180, 80, 220)   # Purple accent

# Alert colors
COLOR_ALERT_RED = (255, 60, 80)        # Danger/critical (neon red)
COLOR_ALERT_YELLOW = (255, 200, 50)    # Warning (neon yellow)
COLOR_ALERT_GREEN = (50, 255, 120)     # Good/success (neon green)

# Text colors
COLOR_TEXT_BRIGHT = (230, 240, 250)    # Primary text
COLOR_TEXT_DIM = (120, 130, 145)       # Secondary text
COLOR_TEXT_ACCENT = (0, 240, 240)      # Cyan highlighted text
COLOR_TEXT_PINK = (255, 100, 160)      # Pink highlighted text

# Tab colors
COLOR_TAB_ACTIVE = (255, 50, 130)      # Active tab (hot pink)
COLOR_TAB_INACTIVE = (35, 42, 52)      # Inactive tab

# ============================================================================
# CYBERPUNK FONTS
# ============================================================================

# Font paths - will try system fonts, fallback to default
FONT_MONO = None  # Will be initialized
FONT_DIGITAL = None  # For numbers

def get_cyber_font(size: int, bold: bool = False) -> pygame.font.Font:
    """Get a monospace/cyber style font."""
    # Try various monospace fonts in order of preference
    mono_fonts = ['Consolas', 'Source Code Pro', 'Fira Code', 'Courier New', 'monospace']
    for font_name in mono_fonts:
        try:
            return pygame.font.SysFont(font_name, size, bold=bold)
        except:
            continue
    return pygame.font.Font(None, size)

def get_digital_font(size: int) -> pygame.font.Font:
    """Get a digital clock style font for numbers."""
    # Try digital-style fonts
    digital_fonts = ['DSEG7 Classic', 'Digital-7', 'LCD', 'Consolas', 'monospace']
    for font_name in digital_fonts:
        try:
            return pygame.font.SysFont(font_name, size)
        except:
            continue
    return pygame.font.Font(None, size)

# ============================================================================
# LAYOUT CONSTANTS
# ============================================================================

TOP_BAR_HEIGHT = 36
LEFT_SIDEBAR_WIDTH = 200  # Narrower - build menu moved to bottom
RIGHT_PANEL_WIDTH = 380   # Colonist management panel (narrower, taller)
BOTTOM_BAR_HEIGHT = 44    # Build tools bar (thinner)
PANEL_PADDING = 8
BORDER_WIDTH = 2

# Calculate viewport area (map is between left sidebar and right panel, above bottom bar)
VIEWPORT_X = LEFT_SIDEBAR_WIDTH
VIEWPORT_Y = TOP_BAR_HEIGHT
VIEWPORT_W = SCREEN_W - LEFT_SIDEBAR_WIDTH - RIGHT_PANEL_WIDTH
VIEWPORT_H = SCREEN_H - TOP_BAR_HEIGHT - BOTTOM_BAR_HEIGHT


# ============================================================================
# DRAWING UTILITIES
# ============================================================================

def draw_panel_border(surface: pygame.Surface, rect: pygame.Rect, 
                      color: Tuple[int, int, int] = COLOR_ACCENT_CYAN_DIM,
                      width: int = 1, corner_size: int = 8) -> None:
    """Draw a cyberpunk-style panel border with corner accents."""
    x, y, w, h = rect.x, rect.y, rect.width, rect.height
    
    # Main border lines
    pygame.draw.line(surface, color, (x + corner_size, y), (x + w - corner_size, y), width)
    pygame.draw.line(surface, color, (x + corner_size, y + h - 1), (x + w - corner_size, y + h - 1), width)
    pygame.draw.line(surface, color, (x, y + corner_size), (x, y + h - corner_size), width)
    pygame.draw.line(surface, color, (x + w - 1, y + corner_size), (x + w - 1, y + h - corner_size), width)
    
    # Corner accents (brighter)
    bright = COLOR_ACCENT_CYAN
    # Top-left
    pygame.draw.line(surface, bright, (x, y + corner_size), (x, y), width)
    pygame.draw.line(surface, bright, (x, y), (x + corner_size, y), width)
    # Top-right
    pygame.draw.line(surface, bright, (x + w - corner_size, y), (x + w - 1, y), width)
    pygame.draw.line(surface, bright, (x + w - 1, y), (x + w - 1, y + corner_size), width)
    # Bottom-left
    pygame.draw.line(surface, bright, (x, y + h - corner_size), (x, y + h - 1), width)
    pygame.draw.line(surface, bright, (x, y + h - 1), (x + corner_size, y + h - 1), width)
    # Bottom-right
    pygame.draw.line(surface, bright, (x + w - corner_size, y + h - 1), (x + w - 1, y + h - 1), width)
    pygame.draw.line(surface, bright, (x + w - 1, y + h - corner_size), (x + w - 1, y + h - 1), width)


def draw_glow_line(surface: pygame.Surface, start: Tuple[int, int], 
                   end: Tuple[int, int], color: Tuple[int, int, int], width: int = 1) -> None:
    """Draw a line with a subtle glow effect."""
    # Draw glow (wider, more transparent)
    glow_surf = pygame.Surface((surface.get_width(), surface.get_height()), pygame.SRCALPHA)
    glow_color = (*color, 40)
    pygame.draw.line(glow_surf, glow_color, start, end, width + 4)
    surface.blit(glow_surf, (0, 0))
    # Draw main line
    pygame.draw.line(surface, color, start, end, width)


# ============================================================================
# TOP BAR
# ============================================================================

class TopBar:
    """Top bar showing time, z-level, resources, game speed, and alerts."""
    
    def __init__(self):
        self.rect = pygame.Rect(0, 0, SCREEN_W, TOP_BAR_HEIGHT)
        self.font = None
        self.font_small = None
        self.speed_rects = []  # Clickable speed buttons
        
    def init_fonts(self) -> None:
        if self.font is None:
            self.font = get_cyber_font(18)
            self.font_small = get_cyber_font(14)
            self.font_digital = get_cyber_font(20, bold=True)  # For time display
    
    def handle_click(self, mouse_pos: tuple[int, int], game_data: dict) -> tuple[bool, int]:
        """Handle click on top bar. Returns (consumed, new_speed) or (consumed, -1) for pause toggle."""
        if not self.rect.collidepoint(mouse_pos):
            return False, 0
        
        # Check speed buttons
        for rect, speed in self.speed_rects:
            if rect.collidepoint(mouse_pos):
                if speed == 0:  # Pause button
                    return True, -1  # Signal to toggle pause
                return True, speed
        
        return False, 0
    
    def draw(self, surface: pygame.Surface, game_data: dict) -> None:
        """Draw the top bar.
        
        game_data should contain:
        - time_str: Display time string
        - z_level: Current Z level
        - paused: Whether game is paused
        - game_speed: Current speed (1-5)
        - resources: Dict of resource_type -> amount
        """
        self.init_fonts()
        self.speed_rects.clear()
        
        # Background
        pygame.draw.rect(surface, COLOR_BG_PANEL, self.rect)
        
        # Bottom border with glow
        pygame.draw.line(surface, COLOR_ACCENT_CYAN_DIM, 
                        (0, self.rect.bottom - 1), (SCREEN_W, self.rect.bottom - 1), 1)
        
        x_cursor = 8
        
        # Time display (left side with digital clock style) - wider box
        time_str = game_data.get("time_str", "Day 1, 00:00")
        time_box = pygame.Rect(x_cursor, 4, 180, TOP_BAR_HEIGHT - 8)
        pygame.draw.rect(surface, COLOR_BG_DARK, time_box, border_radius=4)
        pygame.draw.rect(surface, COLOR_ACCENT_CYAN, time_box, 1, border_radius=4)
        
        # Neon clock icon
        clock_x = x_cursor + 14
        pygame.draw.circle(surface, COLOR_ACCENT_PINK, (clock_x, TOP_BAR_HEIGHT // 2), 8, 1)
        pygame.draw.line(surface, COLOR_ACCENT_PINK, (clock_x, TOP_BAR_HEIGHT // 2), (clock_x, TOP_BAR_HEIGHT // 2 - 5), 2)
        pygame.draw.line(surface, COLOR_ACCENT_CYAN, (clock_x, TOP_BAR_HEIGHT // 2), (clock_x + 4, TOP_BAR_HEIGHT // 2 + 1), 2)
        
        # Digital-style time text
        time_surf = self.font_digital.render(time_str, True, COLOR_ACCENT_CYAN_GLOW)
        surface.blit(time_surf, (x_cursor + 28, (TOP_BAR_HEIGHT - time_surf.get_height()) // 2))
        x_cursor += 195
        
        # Game speed controls
        paused = game_data.get("paused", False)
        game_speed = game_data.get("game_speed", 1)
        
        # Pause button
        pause_rect = pygame.Rect(x_cursor, 6, 24, TOP_BAR_HEIGHT - 12)
        pause_color = (200, 200, 80) if paused else (80, 80, 80)
        pygame.draw.rect(surface, COLOR_BG_DARK, pause_rect, border_radius=3)
        pygame.draw.rect(surface, pause_color, pause_rect, 1, border_radius=3)
        # Pause icon (two bars)
        pygame.draw.rect(surface, pause_color, (x_cursor + 7, 10, 3, TOP_BAR_HEIGHT - 20))
        pygame.draw.rect(surface, pause_color, (x_cursor + 14, 10, 3, TOP_BAR_HEIGHT - 20))
        self.speed_rects.append((pause_rect, 0))
        x_cursor += 28
        
        # Speed buttons 1-5
        for spd in range(1, 6):
            btn_rect = pygame.Rect(x_cursor, 6, 20, TOP_BAR_HEIGHT - 12)
            is_active = (game_speed == spd) and not paused
            btn_bg = (60, 80, 60) if is_active else COLOR_BG_DARK
            btn_border = (100, 200, 100) if is_active else (60, 60, 60)
            pygame.draw.rect(surface, btn_bg, btn_rect, border_radius=3)
            pygame.draw.rect(surface, btn_border, btn_rect, 1, border_radius=3)
            
            spd_surf = self.font_small.render(str(spd), True, (200, 255, 200) if is_active else (120, 120, 120))
            surface.blit(spd_surf, (btn_rect.centerx - spd_surf.get_width() // 2,
                                   btn_rect.centery - spd_surf.get_height() // 2))
            self.speed_rects.append((btn_rect, spd))
            x_cursor += 24
        
        x_cursor += 12  # Gap before resources
        
        # Resources with neon cyberpunk terminal icons
        resources = game_data.get("resources", {})
        # (type, name, neon_color, glow_color)
        resource_display = [
            ("wood", "Wood", (180, 120, 60), (255, 180, 100)),      # Warm amber
            ("metal", "Metal", (140, 180, 220), (180, 220, 255)),   # Cool steel blue
            ("scrap", "Scrap", (160, 140, 120), (200, 180, 160)),   # Rust/gray
            ("mineral", "Mineral", (80, 220, 200), (120, 255, 240)), # Cyan crystal
            ("power", "Power", (255, 220, 60), (255, 255, 120)),    # Electric yellow
            ("raw_food", "Food", (140, 200, 100), (180, 255, 140)), # Bio green
            ("cooked_meal", "Meals", (220, 160, 80), (255, 200, 120)), # Orange-brown
        ]
        
        for res_type, name, neon_color, glow_color in resource_display:
            amount = resources.get(res_type, 0)
            if amount > 0 or res_type in ["wood", "metal", "power"]:
                # Draw neon icon box
                icon_rect = pygame.Rect(x_cursor, 8, 18, TOP_BAR_HEIGHT - 16)
                
                # Glow effect (subtle)
                glow_rect = icon_rect.inflate(2, 2)
                pygame.draw.rect(surface, (glow_color[0]//4, glow_color[1]//4, glow_color[2]//4), glow_rect, border_radius=3)
                
                # Icon background
                pygame.draw.rect(surface, (20, 22, 28), icon_rect, border_radius=2)
                pygame.draw.rect(surface, neon_color, icon_rect, 1, border_radius=2)
                
                # Draw resource-specific neon symbol
                cx, cy = icon_rect.centerx, icon_rect.centery
                if res_type == "wood":
                    # Tree/log symbol - vertical line with branches
                    pygame.draw.line(surface, neon_color, (cx, cy + 5), (cx, cy - 5), 2)
                    pygame.draw.line(surface, neon_color, (cx - 4, cy - 2), (cx, cy - 5), 1)
                    pygame.draw.line(surface, neon_color, (cx + 4, cy - 2), (cx, cy - 5), 1)
                elif res_type == "metal":
                    # Ingot/bar symbol
                    pygame.draw.polygon(surface, neon_color, [
                        (cx - 5, cy + 3), (cx - 3, cy - 3), (cx + 5, cy - 3), (cx + 3, cy + 3)
                    ])
                elif res_type == "scrap":
                    # Gear/cog symbol
                    pygame.draw.circle(surface, neon_color, (cx, cy), 4, 1)
                    for angle in range(0, 360, 60):
                        import math
                        rad = math.radians(angle)
                        px = cx + int(5 * math.cos(rad))
                        py = cy + int(5 * math.sin(rad))
                        pygame.draw.rect(surface, neon_color, (px - 1, py - 1, 2, 2))
                elif res_type == "mineral":
                    # Crystal symbol
                    pygame.draw.polygon(surface, neon_color, [
                        (cx, cy - 6), (cx + 4, cy), (cx, cy + 6), (cx - 4, cy)
                    ], 1)
                    pygame.draw.line(surface, glow_color, (cx, cy - 4), (cx, cy + 4), 1)
                elif res_type == "power":
                    # Lightning bolt
                    pygame.draw.polygon(surface, neon_color, [
                        (cx + 2, cy - 6), (cx - 2, cy - 1), (cx + 1, cy - 1),
                        (cx - 2, cy + 6), (cx + 2, cy + 1), (cx - 1, cy + 1)
                    ])
                elif res_type == "raw_food":
                    # Leaf/plant symbol
                    pygame.draw.ellipse(surface, neon_color, (cx - 4, cy - 3, 8, 6), 1)
                    pygame.draw.line(surface, neon_color, (cx, cy + 3), (cx, cy + 5), 1)
                
                x_cursor += 22
                
                # Name: Amount with neon glow text - more spacing
                text = f"{name}: {amount}"
                text_surf = self.font_small.render(text, True, neon_color)
                surface.blit(text_surf, (x_cursor, TOP_BAR_HEIGHT // 2 - text_surf.get_height() // 2))
                x_cursor += text_surf.get_width() + 24  # More gap between resources
        
        # Z-level indicator (right side)
        z_level = game_data.get("z_level", 0)
        z_text = f"Z: {z_level}"
        z_surf = self.font.render(z_text, True, COLOR_TEXT_ACCENT)
        z_x = SCREEN_W - z_surf.get_width() - 12
        surface.blit(z_surf, (z_x, (TOP_BAR_HEIGHT - z_surf.get_height()) // 2))


# ============================================================================
# LEFT SIDEBAR
# ============================================================================

class LeftSidebar:
    """Left sidebar with tabbed panels (build menu moved to bottom bar)."""
    
    TABS = ["COLONISTS", "JOBS", "ITEMS", "ROOMS"]  # BUILD moved to bottom bar
    
    # NOTE: Submenu definitions moved to ui_config.py - use get_submenu() to access
    
    def __init__(self):
        self.rect = pygame.Rect(0, TOP_BAR_HEIGHT, LEFT_SIDEBAR_WIDTH, 
                               SCREEN_H - TOP_BAR_HEIGHT - BOTTOM_BAR_HEIGHT)
        self.current_tab = 0
        self.font = None
        self.font_small = None
        self.font_tiny = None
        self.tab_rects: List[pygame.Rect] = []
        self.hovered_tab = -1
        
        # Build menu items
        self.build_items: List[dict] = []
        self.hovered_item = -1
        self.item_rects: List[pygame.Rect] = []
        
        # Submenu state
        self.active_submenu: Optional[str] = None  # Which category's submenu is open
        self.submenu_items: List[dict] = []
        self.submenu_rects: List[pygame.Rect] = []
        self.hovered_submenu_item = -1
        self.submenu_rect: Optional[pygame.Rect] = None
        
        # Dynamic submenus (loaded from game data)
        self.stations_menu: List[dict] = []
        self.furniture_menu: List[dict] = []
        
        # Colonist list state (for click handling)
        self.colonist_rects: List[pygame.Rect] = []
        self.colonist_refs: List = []  # Actual colonist objects
        self.hovered_colonist = -1
        self.colonist_scroll = 0
        
        # Callbacks
        self.on_colonist_click: Optional[Callable] = None  # (colonist) -> None
        self.on_colonist_locate: Optional[Callable] = None  # (x, y, z) -> None
        
    def init_fonts(self) -> None:
        if self.font is None:
            self.font = get_cyber_font(16)
            self.font_small = get_cyber_font(13)
            self.font_tiny = get_cyber_font(11)
    
    def load_dynamic_menus(self) -> None:
        """Load stations and furniture menus from game data."""
        try:
            import buildings
            self.stations_menu = []
            for b_id, b_def in buildings.BUILDING_TYPES.items():
                if b_def.get("workstation", False):
                    materials = b_def.get("materials", {}) or {}
                    cost = ", ".join(f"{amt} {res}" for res, amt in materials.items()) if materials else "Free"
                    self.stations_menu.append({
                        "id": b_id,
                        "name": b_def.get("name", b_id),
                        "cost": cost,
                    })
        except:
            pass
        
        try:
            import items as items_module
            self.furniture_menu = []
            # Get furniture items
            furniture_defs = items_module.get_items_with_tag("furniture")
            for item_def in furniture_defs:
                self.furniture_menu.append({
                    "id": f"furn_{item_def.id}",
                    "name": item_def.name,
                    "cost": "From stockpile",
                })
            # Get instrument items
            instrument_defs = items_module.get_items_with_tag("instrument")
            for item_def in instrument_defs:
                self.furniture_menu.append({
                    "id": f"furn_{item_def.id}",
                    "name": item_def.name,
                    "cost": "From stockpile",
                })
        except:
            pass
    
    def get_submenu_items(self, category: str) -> List[dict]:
        """Get submenu items for a category."""
        if category == "stations":
            if not self.stations_menu:
                self.load_dynamic_menus()
            return self.stations_menu
        elif category == "furniture":
            if not self.furniture_menu:
                self.load_dynamic_menus()
            return self.furniture_menu
        return get_submenu(category)
    
    def close_submenu(self) -> None:
        """Close any open submenu."""
        self.active_submenu = None
        self.submenu_items = []
        self.submenu_rects = []
        self.submenu_rect = None
    
    def handle_click(self, pos: Tuple[int, int]) -> Optional[str]:
        """Handle mouse click. Returns selected item ID or None."""
        # Check submenu clicks first (if open)
        if self.active_submenu and self.submenu_rect and self.submenu_rect.collidepoint(pos):
            for i, sub_rect in enumerate(self.submenu_rects):
                if sub_rect.collidepoint(pos) and i < len(self.submenu_items):
                    item_id = self.submenu_items[i].get("id")
                    self.active_submenu = None  # Close submenu after selection
                    return item_id
            return None  # Clicked in submenu area but not on item
        
        # Click outside submenu closes it
        if self.active_submenu:
            self.active_submenu = None
        
        if not self.rect.collidepoint(pos):
            return None
        
        # Check tab clicks
        for i, tab_rect in enumerate(self.tab_rects):
            if tab_rect.collidepoint(pos):
                self.current_tab = i
                return None
        
        # Check colonist clicks (COLONISTS tab - now tab 0)
        if self.current_tab == 0:
            for i, col_rect in enumerate(self.colonist_rects):
                if col_rect.collidepoint(pos) and i < len(self.colonist_refs):
                    colonist = self.colonist_refs[i]
                    # Left side = locate, right side = open panel
                    if pos[0] < col_rect.centerx:
                        # Left half - jump to colonist
                        if self.on_colonist_locate and hasattr(colonist, 'x'):
                            self.on_colonist_locate(colonist.x, colonist.y, colonist.z)
                    else:
                        # Right half - open colonist panel
                        if self.on_colonist_click:
                            self.on_colonist_click(colonist)
                    return None
        
        return None
    
    def _build_submenu_rects(self, parent_rect: pygame.Rect) -> None:
        """Build submenu item rectangles."""
        self.submenu_rects.clear()
        
        item_height = 32
        padding = 8
        
        # Calculate width based on longest item name + cost
        self.init_fonts()
        min_width = 180
        max_width = 320
        
        measured_width = min_width
        for item in self.submenu_items:
            name = item.get("name", "")
            cost = item.get("cost", "")
            # Measure name + cost with some spacing
            name_width = self.font.size(name)[0]
            cost_width = self.font_small.size(cost)[0] if cost else 0
            total_width = name_width + cost_width + padding * 4 + 20  # Extra spacing
            measured_width = max(measured_width, total_width)
        
        submenu_width = min(max_width, measured_width)
        
        # Calculate submenu position
        submenu_x = LEFT_SIDEBAR_WIDTH + 4
        submenu_y = parent_rect.y
        submenu_height = len(self.submenu_items) * (item_height + 2) + padding * 2
        
        # Keep on screen
        if submenu_y + submenu_height > SCREEN_H:
            submenu_y = SCREEN_H - submenu_height - 10
        
        self.submenu_rect = pygame.Rect(submenu_x, submenu_y, submenu_width, submenu_height)
        
        y = submenu_y + padding
        for item in self.submenu_items:
            rect = pygame.Rect(submenu_x + padding, y, submenu_width - padding * 2, item_height)
            self.submenu_rects.append(rect)
            y += item_height + 2
    
    def update(self, mouse_pos: Tuple[int, int]) -> None:
        """Update hover states."""
        self.hovered_tab = -1
        self.hovered_item = -1
        self.hovered_submenu_item = -1
        
        # Check submenu hover first
        if self.active_submenu and self.submenu_rect:
            if self.submenu_rect.collidepoint(mouse_pos):
                for i, sub_rect in enumerate(self.submenu_rects):
                    if sub_rect.collidepoint(mouse_pos):
                        self.hovered_submenu_item = i
                        return
        
        if not self.rect.collidepoint(mouse_pos):
            return
        
        for i, tab_rect in enumerate(self.tab_rects):
            if tab_rect.collidepoint(mouse_pos):
                self.hovered_tab = i
                return
        
        for i, item_rect in enumerate(self.item_rects):
            if item_rect.collidepoint(mouse_pos):
                self.hovered_item = i
                return
    
    def draw(self, surface: pygame.Surface, game_data: dict) -> None:
        """Draw the left sidebar."""
        self.init_fonts()
        
        # Background
        pygame.draw.rect(surface, COLOR_BG_PANEL, self.rect)
        
        # Right border
        pygame.draw.line(surface, COLOR_ACCENT_CYAN_DIM,
                        (self.rect.right - 1, self.rect.top),
                        (self.rect.right - 1, self.rect.bottom), 1)
        
        # Draw tabs
        self.tab_rects.clear()
        tab_y = self.rect.top + 4
        tab_height = 28
        
        for i, tab_name in enumerate(self.TABS):
            tab_rect = pygame.Rect(4, tab_y, LEFT_SIDEBAR_WIDTH - 8, tab_height)
            self.tab_rects.append(tab_rect)
            
            # Tab background
            if i == self.current_tab:
                pygame.draw.rect(surface, COLOR_TAB_ACTIVE, tab_rect, border_radius=4)
                text_color = COLOR_TEXT_BRIGHT
            elif i == self.hovered_tab:
                pygame.draw.rect(surface, COLOR_BG_PANEL_LIGHT, tab_rect, border_radius=4)
                pygame.draw.rect(surface, COLOR_ACCENT_CYAN_DIM, tab_rect, 1, border_radius=4)
                text_color = COLOR_TEXT_BRIGHT
            else:
                pygame.draw.rect(surface, COLOR_TAB_INACTIVE, tab_rect, border_radius=4)
                text_color = COLOR_TEXT_DIM
            
            # Tab text
            tab_surf = self.font.render(tab_name, True, text_color)
            text_x = tab_rect.centerx - tab_surf.get_width() // 2
            text_y = tab_rect.centery - tab_surf.get_height() // 2
            surface.blit(tab_surf, (text_x, text_y))
            
            tab_y += tab_height + 2
        
        # Separator line
        sep_y = tab_y + 4
        pygame.draw.line(surface, COLOR_ACCENT_CYAN_DIM, (8, sep_y), (LEFT_SIDEBAR_WIDTH - 8, sep_y), 1)
        
        # Draw content based on current tab
        # TABS = ["COLONISTS", "JOBS", "ITEMS", "ROOMS"] - BUILD moved to bottom bar
        content_y = sep_y + 8
        
        if self.current_tab == 0:
            self._draw_colonists_content(surface, content_y, game_data)
        elif self.current_tab == 1:
            self._draw_jobs_content(surface, content_y, game_data)
        elif self.current_tab == 2:
            self._draw_items_content(surface, content_y, game_data)
        elif self.current_tab == 3:
            self._draw_rooms_content(surface, content_y, game_data)
        
        # Draw current tool indicator at bottom of sidebar
        current_tool = game_data.get("current_tool")
        if current_tool:
            tool_y = self.rect.bottom - 60
            
            # Separator
            pygame.draw.line(surface, COLOR_ACCENT_CYAN_DIM, (8, tool_y - 8), (LEFT_SIDEBAR_WIDTH - 8, tool_y - 8), 1)
            
            # Tool box
            tool_box = pygame.Rect(8, tool_y, LEFT_SIDEBAR_WIDTH - 16, 50)
            pygame.draw.rect(surface, COLOR_BG_DARK, tool_box, border_radius=6)
            pygame.draw.rect(surface, COLOR_ACCENT_CYAN, tool_box, 2, border_radius=6)
            
            # Tool name
            tool_name = current_tool.replace("_", " ").title()
            tool_surf = self.font.render(tool_name, True, COLOR_TEXT_ACCENT)
            surface.blit(tool_surf, (tool_box.x + 8, tool_box.y + 8))
            
            # Cancel hint
            hint_surf = self.font_small.render("[ESC] Cancel", True, COLOR_TEXT_DIM)
            surface.blit(hint_surf, (tool_box.x + 8, tool_box.y + 28))
    
    def _draw_build_content(self, surface: pygame.Surface, start_y: int, game_data: dict) -> None:
        """Draw build menu content."""
        self.item_rects.clear()
        self.build_items.clear()  # Clear to avoid duplicates
        
        # Get current tool to highlight active item
        current_tool = game_data.get("current_tool")
        
        # Get build categories from existing UI
        categories = [
            ("Build", "B", "build"),
            ("Floor", "F", "floors"),
            ("Access", "E", "access"),
            ("Stations", "T", "stations"),
            ("Furniture", "R", "furniture"),
            ("Zone", "Z", "zone"),
            ("Demolish", "X", "demolish"),
            ("Salvage", "V", "salvage"),
            ("Harvest", "H", "harvest"),
        ]
        
        y = start_y
        item_height = 32
        
        for i, (name, key, item_id) in enumerate(categories):
            item_rect = pygame.Rect(8, y, LEFT_SIDEBAR_WIDTH - 16, item_height)
            self.item_rects.append(item_rect)
            self.build_items.append({"id": item_id, "name": name, "keybind": key})
            
            # Check if this is the active tool
            is_active = (current_tool == item_id or 
                        (current_tool and current_tool.startswith(item_id)))
            
            # Background - highlight active tool
            if is_active:
                pygame.draw.rect(surface, COLOR_TAB_ACTIVE, item_rect, border_radius=4)
                pygame.draw.rect(surface, COLOR_ACCENT_CYAN, item_rect, 2, border_radius=4)
            elif i == self.hovered_item:
                pygame.draw.rect(surface, COLOR_BG_PANEL_LIGHT, item_rect, border_radius=4)
                pygame.draw.rect(surface, COLOR_ACCENT_CYAN, item_rect, 1, border_radius=4)
            else:
                pygame.draw.rect(surface, COLOR_BG_DARK, item_rect, border_radius=4)
            
            # Keybind box
            kb_rect = pygame.Rect(item_rect.x + 4, item_rect.y + 4, 24, item_height - 8)
            kb_color = COLOR_ACCENT_CYAN if is_active else COLOR_BG_PANEL
            pygame.draw.rect(surface, kb_color, kb_rect, border_radius=3)
            pygame.draw.rect(surface, COLOR_ACCENT_CYAN_DIM, kb_rect, 1, border_radius=3)
            
            kb_text_color = COLOR_BG_DARK if is_active else COLOR_TEXT_ACCENT
            kb_surf = self.font_small.render(key, True, kb_text_color)
            kb_x = kb_rect.centerx - kb_surf.get_width() // 2
            kb_y = kb_rect.centery - kb_surf.get_height() // 2
            surface.blit(kb_surf, (kb_x, kb_y))
            
            # Item name
            text_color = COLOR_TEXT_BRIGHT if (is_active or i == self.hovered_item) else COLOR_TEXT_DIM
            name_surf = self.font.render(name, True, text_color)
            surface.blit(name_surf, (item_rect.x + 34, item_rect.centery - name_surf.get_height() // 2))
            
            y += item_height + 4
    
    def _draw_colonists_content(self, surface: pygame.Surface, start_y: int, game_data: dict) -> None:
        """Draw robust colonists list with hunger, tiredness, job info."""
        colonists = game_data.get("colonist_objects", [])  # Actual colonist objects
        mouse_pos = pygame.mouse.get_pos()
        
        self.colonist_rects.clear()
        self.colonist_refs.clear()
        
        # Header
        header_surf = self.font_small.render(f"COLONISTS ({len(colonists)})", True, COLOR_ACCENT_CYAN)
        surface.blit(header_surf, (12, start_y))
        
        y = start_y + 20
        row_height = 52
        max_visible = (self.rect.bottom - y - 60) // row_height
        
        for i, c in enumerate(colonists[:max_visible]):
            if hasattr(c, 'is_dead') and c.is_dead:
                continue
                
            row_rect = pygame.Rect(6, y, LEFT_SIDEBAR_WIDTH - 12, row_height - 2)
            self.colonist_rects.append(row_rect)
            self.colonist_refs.append(c)
            
            # Hover highlight
            is_hovered = row_rect.collidepoint(mouse_pos)
            if is_hovered:
                pygame.draw.rect(surface, COLOR_BG_PANEL_LIGHT, row_rect, border_radius=4)
                pygame.draw.rect(surface, COLOR_ACCENT_CYAN_DIM, row_rect, 1, border_radius=4)
            
            # Name (left side)
            name = getattr(c, 'name', 'Unknown')
            name_surf = self.font.render(name, True, COLOR_TEXT_BRIGHT)
            surface.blit(name_surf, (12, y + 2))
            
            # Current job/state
            state = getattr(c, 'state', 'idle')
            job = getattr(c, 'current_job', None)
            if job:
                job_text = f"{job.type.replace('_', ' ').title()}"
            else:
                job_text = state.replace('_', ' ').title()
            
            state_color = COLOR_ALERT_GREEN if state == "working" else COLOR_TEXT_DIM
            state_surf = self.font_small.render(job_text, True, state_color)
            surface.blit(state_surf, (12, y + 20))
            
            # Hunger bar (right side)
            hunger = getattr(c, 'hunger', 100)
            hunger_pct = max(0, min(1, hunger / 100))
            bar_x = LEFT_SIDEBAR_WIDTH - 70
            bar_y = y + 4
            bar_w = 55
            bar_h = 8
            
            # Background
            pygame.draw.rect(surface, (40, 40, 50), (bar_x, bar_y, bar_w, bar_h), border_radius=2)
            # Fill
            hunger_color = COLOR_ALERT_RED if hunger_pct > 0.5 else (COLOR_ALERT_YELLOW if hunger_pct > 0.25 else COLOR_ALERT_GREEN)
            fill_w = int(bar_w * hunger_pct)
            if fill_w > 0:
                pygame.draw.rect(surface, hunger_color, (bar_x, bar_y, fill_w, bar_h), border_radius=2)
            # Label
            hunger_label = self.font_tiny.render("STARVE", True, COLOR_TEXT_DIM)
            surface.blit(hunger_label, (bar_x, bar_y + bar_h + 1))
            
            # Tiredness bar
            tiredness = getattr(c, 'tiredness', 0)
            tired_pct = max(0, min(1, tiredness / 100))
            bar_y2 = y + 24
            
            pygame.draw.rect(surface, (40, 40, 50), (bar_x, bar_y2, bar_w, bar_h), border_radius=2)
            tired_color = COLOR_ALERT_GREEN if tired_pct < 0.5 else (COLOR_ALERT_YELLOW if tired_pct < 0.75 else COLOR_ALERT_RED)
            fill_w2 = int(bar_w * tired_pct)
            if fill_w2 > 0:
                pygame.draw.rect(surface, tired_color, (bar_x, bar_y2, fill_w2, bar_h), border_radius=2)
            tired_label = self.font_tiny.render("DRAIN", True, COLOR_TEXT_DIM)
            surface.blit(tired_label, (bar_x, bar_y2 + bar_h + 1))
            
            y += row_height
        
        # Hint at bottom
        if colonists:
            hint_y = self.rect.bottom - 55
            hint_surf = self.font_tiny.render("Click left=locate, right=details", True, COLOR_TEXT_DIM)
            surface.blit(hint_surf, (12, hint_y))
    
    def _draw_jobs_content(self, surface: pygame.Surface, start_y: int, game_data: dict) -> None:
        """Draw jobs overview."""
        jobs_module = game_data.get("jobs_module")
        
        y = start_y
        
        # Header
        header_surf = self.font_small.render("JOB QUEUE", True, COLOR_ACCENT_CYAN)
        surface.blit(header_surf, (12, y))
        y += 20
        
        if jobs_module:
            from jobs import JOB_QUEUE
            total_jobs = len(JOB_QUEUE)
            assigned = sum(1 for j in JOB_QUEUE if j.assigned)
            
            # Summary
            summary = f"{assigned}/{total_jobs} jobs assigned"
            summary_surf = self.font.render(summary, True, COLOR_TEXT_BRIGHT)
            surface.blit(summary_surf, (12, y))
            y += 24
            
            # Job type breakdown
            job_counts = {}
            for j in JOB_QUEUE:
                jtype = j.type
                if jtype not in job_counts:
                    job_counts[jtype] = {"total": 0, "assigned": 0}
                job_counts[jtype]["total"] += 1
                if j.assigned:
                    job_counts[jtype]["assigned"] += 1
            
            for jtype, counts in sorted(job_counts.items()):
                type_text = f"{jtype.replace('_', ' ').title()}: {counts['assigned']}/{counts['total']}"
                type_color = COLOR_ALERT_GREEN if counts['assigned'] == counts['total'] else COLOR_TEXT_DIM
                type_surf = self.font_small.render(type_text, True, type_color)
                surface.blit(type_surf, (16, y))
                y += 18
                
                if y > self.rect.bottom - 80:
                    break
    
    def _draw_items_content(self, surface: pygame.Surface, start_y: int, game_data: dict) -> None:
        """Draw items/inventory content."""
        import zones
        
        y = start_y
        header_surf = self.font_small.render("STOCKPILE ITEMS", True, COLOR_ACCENT_CYAN)
        surface.blit(header_surf, (12, y))
        y += 20
        
        # Aggregate items
        item_counts = {}
        for coord, storage in zones.get_all_tile_storage().items():
            if storage:
                item_type = storage.get("type", "unknown")
                amount = storage.get("amount", 0)
                item_counts[item_type] = item_counts.get(item_type, 0) + amount
        
        if not item_counts:
            empty_surf = self.font_small.render("No items in stockpiles", True, COLOR_TEXT_DIM)
            surface.blit(empty_surf, (12, y))
        else:
            for item_type, count in sorted(item_counts.items()):
                item_text = f"{item_type.replace('_', ' ').title()}: {count}"
                item_surf = self.font_small.render(item_text, True, COLOR_TEXT_BRIGHT)
                surface.blit(item_surf, (16, y))
                y += 18
                
                if y > self.rect.bottom - 80:
                    break
    
    def _draw_rooms_content(self, surface: pygame.Surface, start_y: int, game_data: dict) -> None:
        """Draw rooms list - using manual room system."""
        import room_system
        
        y = start_y
        header_surf = self.font_small.render("ROOMS", True, COLOR_ACCENT_CYAN)
        surface.blit(header_surf, (12, y))
        y += 20
        
        all_rooms = room_system.get_all_rooms()
        
        if not all_rooms:
            empty_surf = self.font_small.render("No rooms created", True, COLOR_TEXT_DIM)
            surface.blit(empty_surf, (12, y))
            y += 18
            hint_surf = self.font_tiny.render("Press M to create rooms", True, COLOR_TEXT_DIM)
            surface.blit(hint_surf, (12, y))
        else:
            room_counts = {}
            for room_data in all_rooms.values():
                rtype = room_data.get("type", "Unknown")
                room_counts[rtype] = room_counts.get(rtype, 0) + 1
            
            for rtype, count in sorted(room_counts.items()):
                room_text = f"{rtype}: {count}"
                room_surf = self.font_small.render(room_text, True, COLOR_TEXT_BRIGHT)
                surface.blit(room_surf, (16, y))
                y += 18
                
                if y > self.rect.bottom - 80:
                    break
    
    def get_tooltips(self) -> dict:
        """Get tooltip data from ui_config."""
        return TOOLTIPS
    
    def draw_submenu(self, surface: pygame.Surface) -> None:
        """Draw the cascading submenu if active."""
        if not self.active_submenu or not self.submenu_rect:
            return
        
        self.init_fonts()
        tooltips = self.get_tooltips()
        
        # Draw submenu background with shadow
        shadow_rect = self.submenu_rect.copy()
        shadow_rect.x += 4
        shadow_rect.y += 4
        pygame.draw.rect(surface, (10, 12, 16), shadow_rect, border_radius=6)
        
        # Main background
        pygame.draw.rect(surface, COLOR_BG_PANEL, self.submenu_rect, border_radius=6)
        draw_panel_border(surface, self.submenu_rect, COLOR_ACCENT_CYAN_DIM, corner_size=6)
        
        # Draw items
        hovered_tooltip = None
        hovered_rect = None
        
        for i, (item, rect) in enumerate(zip(self.submenu_items, self.submenu_rects)):
            # Background
            if i == self.hovered_submenu_item:
                pygame.draw.rect(surface, COLOR_BG_PANEL_LIGHT, rect, border_radius=4)
                pygame.draw.rect(surface, COLOR_ACCENT_CYAN, rect, 1, border_radius=4)
                text_color = COLOR_TEXT_BRIGHT
                # Get tooltip for hovered item
                item_id = item.get("id", "")
                if item_id in tooltips:
                    hovered_tooltip = tooltips[item_id]
                    hovered_rect = rect
            else:
                text_color = COLOR_TEXT_DIM
            
            # Item name
            name = item.get("name", "Unknown")
            name_surf = self.font.render(name, True, text_color)
            surface.blit(name_surf, (rect.x + 8, rect.centery - name_surf.get_height() // 2))
            
            # Cost (right-aligned)
            cost = item.get("cost", "")
            if cost:
                cost_surf = self.font_small.render(cost, True, COLOR_TEXT_DIM)
                cost_x = rect.right - cost_surf.get_width() - 8
                surface.blit(cost_surf, (cost_x, rect.centery - cost_surf.get_height() // 2))
        
        # Draw tooltip box for hovered item
        if hovered_tooltip and hovered_rect:
            self._draw_tooltip(surface, hovered_tooltip, hovered_rect)
    
    def _draw_tooltip(self, surface: pygame.Surface, tooltip_data: tuple, anchor_rect: pygame.Rect) -> None:
        """Draw a tooltip box next to the anchor rect."""
        if not tooltip_data:
            return
        
        # Parse tooltip data
        if isinstance(tooltip_data, tuple) and len(tooltip_data) >= 2:
            title = tooltip_data[0]
            desc = tooltip_data[1]
            extra = tooltip_data[2] if len(tooltip_data) > 2 else ""
        else:
            title = str(tooltip_data)
            desc = ""
            extra = ""
        
        # Calculate tooltip size
        padding = 8
        max_width = 280
        
        title_font = pygame.font.Font(None, 22)
        desc_font = pygame.font.Font(None, 18)
        
        title_surf = title_font.render(title, True, COLOR_TEXT_ACCENT)
        
        # Word wrap description
        desc_lines = []
        if desc:
            words = desc.split()
            current_line = ""
            for word in words:
                test_line = current_line + " " + word if current_line else word
                test_surf = desc_font.render(test_line, True, COLOR_TEXT_DIM)
                if test_surf.get_width() > max_width - padding * 2:
                    if current_line:
                        desc_lines.append(current_line)
                    current_line = word
                else:
                    current_line = test_line
            if current_line:
                desc_lines.append(current_line)
        
        # Calculate box size
        box_width = max(title_surf.get_width() + padding * 2, max_width)
        box_height = padding * 2 + title_surf.get_height() + 4
        box_height += len(desc_lines) * 18
        if extra:
            box_height += 20
        
        # Position tooltip to the right of submenu
        tooltip_x = self.submenu_rect.right + 8
        tooltip_y = anchor_rect.top
        
        # Keep on screen
        if tooltip_x + box_width > SCREEN_W:
            tooltip_x = self.submenu_rect.left - box_width - 8
        if tooltip_y + box_height > SCREEN_H:
            tooltip_y = SCREEN_H - box_height - 10
        
        tooltip_rect = pygame.Rect(tooltip_x, tooltip_y, box_width, box_height)
        
        # Draw shadow
        shadow_rect = tooltip_rect.copy()
        shadow_rect.x += 3
        shadow_rect.y += 3
        pygame.draw.rect(surface, (10, 12, 16), shadow_rect, border_radius=6)
        
        # Draw background
        pygame.draw.rect(surface, COLOR_BG_PANEL, tooltip_rect, border_radius=6)
        pygame.draw.rect(surface, COLOR_ACCENT_CYAN, tooltip_rect, 1, border_radius=6)
        
        # Draw content
        y = tooltip_rect.top + padding
        surface.blit(title_surf, (tooltip_rect.left + padding, y))
        y += title_surf.get_height() + 4
        
        for line in desc_lines:
            line_surf = desc_font.render(line, True, COLOR_TEXT_DIM)
            surface.blit(line_surf, (tooltip_rect.left + padding, y))
            y += 18
        
        if extra:
            y += 4
            extra_surf = desc_font.render(extra, True, COLOR_TEXT_ACCENT)
            surface.blit(extra_surf, (tooltip_rect.left + padding, y))


# ============================================================================
# BOTTOM BUILD BAR
# ============================================================================

class BottomBuildBar:
    """Bottom bar with build tool buttons (horizontal layout)."""
    
    # Build categories - same as old sidebar BUILD tab
    BUILD_CATEGORIES = [
        ("Build", "B", "build"),
        ("Floor", "F", "floors"),
        ("Access", "E", "access"),
        ("Stations", "T", "stations"),
        ("Furniture", "R", "furniture"),
        ("Rooms", "M", "rooms"),
        ("Zone", "Z", "zone"),
        ("Demolish", "X", "demolish"),
        ("Salvage", "V", "salvage"),
        ("Harvest", "H", "harvest"),
    ]
    
    # NOTE: Submenu definitions moved to ui_config.py - use get_submenu() to access
    
    def __init__(self):
        self.rect = pygame.Rect(LEFT_SIDEBAR_WIDTH, SCREEN_H - BOTTOM_BAR_HEIGHT, 
                               SCREEN_W - LEFT_SIDEBAR_WIDTH - RIGHT_PANEL_WIDTH, BOTTOM_BAR_HEIGHT)
        self.font = None
        self.font_small = None
        
        # Button state
        self.button_rects: List[pygame.Rect] = []
        self.hovered_button = -1
        
        # Submenu state
        self.active_submenu: Optional[str] = None
        self.submenu_items: List[dict] = []
        self.submenu_rects: List[pygame.Rect] = []
        self.submenu_rect: Optional[pygame.Rect] = None
        self.hovered_submenu_item = -1
        
        # Dynamic menus
        self.stations_menu: List[dict] = []
        self.furniture_menu: List[dict] = []
        
    def init_fonts(self) -> None:
        if self.font is None:
            self.font = get_cyber_font(15)
            self.font_small = get_cyber_font(12)
    
    def load_dynamic_menus(self) -> None:
        """Load stations and furniture menus from game data."""
        try:
            from buildings import BUILDING_TYPES
            self.stations_menu = []
            for bld_id, bld_data in BUILDING_TYPES.items():
                # Only include workstations
                if not bld_data.get("workstation", False):
                    continue
                cost_parts = []
                for res, amt in bld_data.get("materials", {}).items():
                    cost_parts.append(f"{amt} {res}")
                cost_str = ", ".join(cost_parts) if cost_parts else ""
                self.stations_menu.append({
                    "id": bld_id,  # Use raw ID, not prefixed
                    "name": bld_data.get("name", bld_id.replace("_", " ").title()),
                    "cost": cost_str,
                })
        except Exception as e:
            print(f"[UI] Failed to load stations menu: {e}")
        
        try:
            import items as items_module
            self.furniture_menu = []
            # Get furniture items
            furniture_defs = items_module.get_items_with_tag("furniture")
            for item_def in furniture_defs:
                self.furniture_menu.append({
                    "id": f"furn_{item_def.id}",
                    "name": item_def.name,
                    "cost": "From stockpile",
                })
            # Get instrument items
            instrument_defs = items_module.get_items_with_tag("instrument")
            for item_def in instrument_defs:
                self.furniture_menu.append({
                    "id": f"furn_{item_def.id}",
                    "name": item_def.name,
                    "cost": "From stockpile",
                })
        except:
            pass
    
    def get_submenu_items(self, category: str) -> List[dict]:
        """Get submenu items for a category."""
        if category == "stations":
            if not self.stations_menu:
                self.load_dynamic_menus()
            return self.stations_menu
        elif category == "furniture":
            if not self.furniture_menu:
                self.load_dynamic_menus()
            return self.furniture_menu
        return get_submenu(category)
    
    def close_submenu(self) -> None:
        """Close any open submenu."""
        self.active_submenu = None
        self.submenu_items = []
        self.submenu_rects = []
        self.submenu_rect = None
    
    def update(self, mouse_pos: Tuple[int, int]) -> None:
        """Update hover states."""
        self.hovered_button = -1
        self.hovered_submenu_item = -1
        
        # Check button hovers
        for i, btn_rect in enumerate(self.button_rects):
            if btn_rect.collidepoint(mouse_pos):
                self.hovered_button = i
                break
        
        # Check submenu hovers
        if self.submenu_rect and self.submenu_rect.collidepoint(mouse_pos):
            for i, sub_rect in enumerate(self.submenu_rects):
                if sub_rect.collidepoint(mouse_pos):
                    self.hovered_submenu_item = i
                    break
    
    def handle_click(self, pos: Tuple[int, int]) -> Optional[str]:
        """Handle mouse click. Returns selected item ID or None."""
        # Check submenu clicks first
        if self.active_submenu and self.submenu_rect and self.submenu_rect.collidepoint(pos):
            for i, sub_rect in enumerate(self.submenu_rects):
                if sub_rect.collidepoint(pos) and i < len(self.submenu_items):
                    item_id = self.submenu_items[i].get("id")
                    self.active_submenu = None
                    return item_id
            return None
        
        # Click outside submenu closes it
        if self.active_submenu:
            self.active_submenu = None
        
        # Check button clicks
        for i, btn_rect in enumerate(self.button_rects):
            if btn_rect.collidepoint(pos) and i < len(self.BUILD_CATEGORIES):
                _, _, item_id = self.BUILD_CATEGORIES[i]
                submenu_items = self.get_submenu_items(item_id)
                if submenu_items:
                    if self.active_submenu == item_id:
                        self.active_submenu = None
                    else:
                        self.active_submenu = item_id
                        self.submenu_items = submenu_items
                        self._build_submenu_rects(btn_rect)
                    return None
                else:
                    return item_id
        
        return None
    
    def _build_submenu_rects(self, parent_rect: pygame.Rect) -> None:
        """Build submenu item rectangles (pops up above the button)."""
        self.submenu_rects.clear()
        
        item_height = 32
        padding = 8
        
        # Calculate width
        max_name_width = 100
        for item in self.submenu_items:
            name = item.get("name", "")
            cost = item.get("cost", "")
            test_width = len(name) * 8 + len(cost) * 6 + 40
            max_name_width = max(max_name_width, test_width)
        
        submenu_width = max_name_width + padding * 2
        submenu_height = len(self.submenu_items) * item_height + padding * 2
        
        # Position above the button
        submenu_x = parent_rect.centerx - submenu_width // 2
        submenu_y = parent_rect.top - submenu_height - 4
        
        # Keep on screen
        if submenu_x < LEFT_SIDEBAR_WIDTH:
            submenu_x = LEFT_SIDEBAR_WIDTH
        if submenu_x + submenu_width > SCREEN_W - RIGHT_PANEL_WIDTH:
            submenu_x = SCREEN_W - RIGHT_PANEL_WIDTH - submenu_width
        
        self.submenu_rect = pygame.Rect(submenu_x, submenu_y, submenu_width, submenu_height)
        
        # Build item rects
        y = submenu_y + padding
        for _ in self.submenu_items:
            item_rect = pygame.Rect(submenu_x + padding, y, submenu_width - padding * 2, item_height - 4)
            self.submenu_rects.append(item_rect)
            y += item_height
    
    def draw(self, surface: pygame.Surface, game_data: dict) -> None:
        """Draw the bottom build bar."""
        self.init_fonts()
        self.button_rects.clear()
        
        current_tool = game_data.get("current_tool")
        
        # Background
        pygame.draw.rect(surface, COLOR_BG_PANEL, self.rect)
        pygame.draw.line(surface, COLOR_ACCENT_CYAN_DIM,
                        (self.rect.left, self.rect.top), (self.rect.right, self.rect.top), 1)
        
        # Calculate button layout - compact for thinner bar
        num_buttons = len(self.BUILD_CATEGORIES)
        total_width = self.rect.width - 16
        button_width = min(110, total_width // num_buttons - 6)
        button_height = 32
        start_x = self.rect.left + 8
        button_y = self.rect.top + (BOTTOM_BAR_HEIGHT - button_height) // 2
        
        for i, (name, key, item_id) in enumerate(self.BUILD_CATEGORIES):
            btn_x = start_x + i * (button_width + 6)
            btn_rect = pygame.Rect(btn_x, button_y, button_width, button_height)
            self.button_rects.append(btn_rect)
            
            # Check if active
            is_active = (current_tool == item_id or 
                        (current_tool and current_tool.startswith(item_id)) or
                        self.active_submenu == item_id)
            
            # Background
            if is_active:
                pygame.draw.rect(surface, COLOR_TAB_ACTIVE, btn_rect, border_radius=4)
                pygame.draw.rect(surface, COLOR_ACCENT_CYAN, btn_rect, 2, border_radius=4)
            elif i == self.hovered_button:
                pygame.draw.rect(surface, COLOR_BG_PANEL_LIGHT, btn_rect, border_radius=4)
                pygame.draw.rect(surface, COLOR_ACCENT_CYAN, btn_rect, 1, border_radius=4)
            else:
                pygame.draw.rect(surface, COLOR_BG_DARK, btn_rect, border_radius=4)
                pygame.draw.rect(surface, COLOR_ACCENT_CYAN_DIM, btn_rect, 1, border_radius=4)
            
            # Keybind badge
            kb_rect = pygame.Rect(btn_rect.x + 4, btn_rect.y + 4, 18, 16)
            kb_color = COLOR_ACCENT_CYAN if is_active else COLOR_BG_PANEL
            pygame.draw.rect(surface, kb_color, kb_rect, border_radius=2)
            
            kb_text_color = COLOR_BG_DARK if is_active else COLOR_TEXT_ACCENT
            kb_surf = self.font_small.render(key, True, kb_text_color)
            surface.blit(kb_surf, (kb_rect.centerx - kb_surf.get_width() // 2, 
                                   kb_rect.centery - kb_surf.get_height() // 2))
            
            # Button name
            text_color = COLOR_TEXT_BRIGHT if is_active else COLOR_TEXT_DIM
            name_surf = self.font.render(name, True, text_color)
            name_x = btn_rect.x + 26
            name_y = btn_rect.centery - name_surf.get_height() // 2
            surface.blit(name_surf, (name_x, name_y))
    
    def draw_submenu(self, surface: pygame.Surface) -> None:
        """Draw the submenu popup (above buttons)."""
        if not self.active_submenu or not self.submenu_rect:
            return
        
        self.init_fonts()
        
        # Shadow
        shadow_rect = self.submenu_rect.copy()
        shadow_rect.x += 4
        shadow_rect.y += 4
        pygame.draw.rect(surface, (10, 12, 16), shadow_rect, border_radius=6)
        
        # Background
        pygame.draw.rect(surface, COLOR_BG_PANEL, self.submenu_rect, border_radius=6)
        draw_panel_border(surface, self.submenu_rect, COLOR_ACCENT_CYAN_DIM, corner_size=6)
        
        # Draw items and track hovered item for tooltip
        hovered_tooltip = None
        hovered_rect = None
        
        for i, (item, rect) in enumerate(zip(self.submenu_items, self.submenu_rects)):
            if i == self.hovered_submenu_item:
                pygame.draw.rect(surface, COLOR_BG_PANEL_LIGHT, rect, border_radius=4)
                pygame.draw.rect(surface, COLOR_ACCENT_CYAN, rect, 1, border_radius=4)
                text_color = COLOR_TEXT_BRIGHT
                # Get tooltip for hovered item
                item_id = item.get("id", "")
                if item_id in TOOLTIPS:
                    hovered_tooltip = TOOLTIPS[item_id]
                    hovered_rect = rect
            else:
                text_color = COLOR_TEXT_DIM
            
            name = item.get("name", "Unknown")
            name_surf = self.font.render(name, True, text_color)
            surface.blit(name_surf, (rect.x + 8, rect.centery - name_surf.get_height() // 2))
            
            cost = item.get("cost", "")
            if cost:
                cost_surf = self.font_small.render(cost, True, COLOR_TEXT_DIM)
                cost_x = rect.right - cost_surf.get_width() - 8
                surface.blit(cost_surf, (cost_x, rect.centery - cost_surf.get_height() // 2))
        
        # Draw tooltip for hovered item
        if hovered_tooltip and hovered_rect:
            self._draw_tooltip(surface, hovered_tooltip, hovered_rect)
    
    def _draw_tooltip(self, surface: pygame.Surface, tooltip_data: tuple, anchor_rect: pygame.Rect) -> None:
        """Draw a tooltip box next to the anchor rect."""
        if not tooltip_data:
            return
        
        # Parse tooltip data
        if isinstance(tooltip_data, tuple) and len(tooltip_data) >= 2:
            title = tooltip_data[0]
            desc = tooltip_data[1]
            extra = tooltip_data[2] if len(tooltip_data) > 2 else ""
        else:
            title = str(tooltip_data)
            desc = ""
            extra = ""
        
        # Calculate tooltip size
        padding = 8
        max_width = 280
        
        title_font = get_cyber_font(16, bold=True)
        desc_font = get_cyber_font(13)
        
        title_surf = title_font.render(title, True, COLOR_ACCENT_CYAN)
        
        # Wrap description text
        desc_lines = []
        if desc:
            words = desc.split()
            current_line = ""
            for word in words:
                test_line = current_line + " " + word if current_line else word
                if desc_font.size(test_line)[0] <= max_width - padding * 2:
                    current_line = test_line
                else:
                    if current_line:
                        desc_lines.append(current_line)
                    current_line = word
            if current_line:
                desc_lines.append(current_line)
        
        # Calculate box size
        box_width = max(title_surf.get_width() + padding * 2, max_width)
        box_height = padding + title_surf.get_height() + 4
        box_height += len(desc_lines) * 18
        if extra:
            box_height += 20
        
        # Position tooltip above submenu
        tooltip_x = anchor_rect.left
        tooltip_y = self.submenu_rect.top - box_height - 8
        
        # Keep on screen
        if tooltip_y < TOP_BAR_HEIGHT:
            tooltip_y = self.submenu_rect.bottom + 8
        if tooltip_x + box_width > SCREEN_W:
            tooltip_x = SCREEN_W - box_width - 10
        
        tooltip_rect = pygame.Rect(tooltip_x, tooltip_y, box_width, box_height)
        
        # Draw shadow
        shadow_rect = tooltip_rect.copy()
        shadow_rect.x += 3
        shadow_rect.y += 3
        pygame.draw.rect(surface, (10, 12, 16), shadow_rect, border_radius=6)
        
        # Draw background
        pygame.draw.rect(surface, COLOR_BG_PANEL, tooltip_rect, border_radius=6)
        pygame.draw.rect(surface, COLOR_ACCENT_CYAN, tooltip_rect, 1, border_radius=6)
        
        # Draw content
        y = tooltip_rect.top + padding
        surface.blit(title_surf, (tooltip_rect.left + padding, y))
        y += title_surf.get_height() + 4
        
        for line in desc_lines:
            line_surf = desc_font.render(line, True, COLOR_TEXT_DIM)
            surface.blit(line_surf, (tooltip_rect.left + padding, y))
            y += 18
        
        if extra:
            y += 4
            extra_surf = desc_font.render(extra, True, COLOR_TEXT_ACCENT)
            surface.blit(extra_surf, (tooltip_rect.left + padding, y))


# ============================================================================
# MAIN LAYOUT MANAGER
# ============================================================================

class UILayoutManager:
    """Manages the overall UI layout."""
    
    def __init__(self):
        self.top_bar = TopBar()
        self.left_sidebar = LeftSidebar()
        self.bottom_bar = BottomBuildBar()
        
        # Viewport rect (where the map is drawn)
        self.viewport_rect = pygame.Rect(VIEWPORT_X, VIEWPORT_Y, VIEWPORT_W, VIEWPORT_H)
        
        # Right panel rect (for colonist management - drawn by ui.py)
        self.right_panel_rect = pygame.Rect(SCREEN_W - RIGHT_PANEL_WIDTH, TOP_BAR_HEIGHT,
                                            RIGHT_PANEL_WIDTH, SCREEN_H - TOP_BAR_HEIGHT)
    
    def update(self, mouse_pos: Tuple[int, int]) -> None:
        """Update UI hover states."""
        self.left_sidebar.update(mouse_pos)
        self.bottom_bar.update(mouse_pos)
    
    def close_submenu(self) -> None:
        """Close any open submenu."""
        self.left_sidebar.close_submenu()
        self.bottom_bar.close_submenu()
    
    def handle_click(self, pos: Tuple[int, int]) -> Optional[str]:
        """Handle mouse click. Returns action ID or None."""
        # Check bottom bar first (build tools)
        result = self.bottom_bar.handle_click(pos)
        if result:
            return result
        
        # Check sidebar
        result = self.left_sidebar.handle_click(pos)
        if result:
            return result
        
        return None
    
    def is_point_in_ui(self, x: int, y: int) -> bool:
        """Check if point is in UI panels (not viewport)."""
        if y < TOP_BAR_HEIGHT:
            return True
        if x < LEFT_SIDEBAR_WIDTH:
            return True
        # NOTE: Right panel clicks are handled by colonist/visitor panels themselves
        # Don't block world clicks in that area - panels check their own visibility
        if y > SCREEN_H - BOTTOM_BAR_HEIGHT:
            return True
        # Check if in active submenus
        if self.left_sidebar.submenu_rect and self.left_sidebar.submenu_rect.collidepoint(x, y):
            return True
        if self.bottom_bar.submenu_rect and self.bottom_bar.submenu_rect.collidepoint(x, y):
            return True
        return False
    
    def draw(self, surface: pygame.Surface, game_data: dict) -> None:
        """Draw all UI panels."""
        self.top_bar.draw(surface, game_data)
        self.left_sidebar.draw(surface, game_data)
        self.bottom_bar.draw(surface, game_data)
        
        # Fill bottom-left corner (where sidebar meets bottom bar)
        corner_rect = pygame.Rect(0, SCREEN_H - BOTTOM_BAR_HEIGHT, LEFT_SIDEBAR_WIDTH, BOTTOM_BAR_HEIGHT)
        pygame.draw.rect(surface, COLOR_BG_PANEL, corner_rect)
        pygame.draw.line(surface, COLOR_ACCENT_CYAN_DIM,
                        (corner_rect.right, corner_rect.top),
                        (corner_rect.right, corner_rect.bottom), 1)
        
        # Draw right panel background (colonist panel draws its own content)
        pygame.draw.rect(surface, COLOR_BG_PANEL, self.right_panel_rect)
        pygame.draw.line(surface, COLOR_ACCENT_CYAN_DIM,
                        (self.right_panel_rect.left, self.right_panel_rect.top),
                        (self.right_panel_rect.left, self.right_panel_rect.bottom), 1)
        
        # Draw viewport border
        draw_panel_border(surface, self.viewport_rect)
        
        # Draw cascading submenus on top
        self.left_sidebar.draw_submenu(surface)
        self.bottom_bar.draw_submenu(surface)


# Global instance
_layout_manager: Optional[UILayoutManager] = None


def get_ui_layout() -> UILayoutManager:
    """Get or create the global UI layout manager."""
    global _layout_manager
    if _layout_manager is None:
        _layout_manager = UILayoutManager()
    return _layout_manager
