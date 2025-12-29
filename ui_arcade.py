"""
Native Arcade UI system for Fractured City.

Clean, cyberpunk-themed UI with GPU-accelerated rendering.
Designed for 1440p base resolution, scales to 1080p-4K.
"""

import arcade
from typing import Optional, List, Dict, Tuple
from config import SCREEN_W, SCREEN_H

# ============================================================================
# PREMIUM CYBERPUNK COLOR PALETTE
# ============================================================================

# Neon accents - vibrant and glowing
COLOR_NEON_CYAN = (0, 255, 255)        # Electric cyan
COLOR_NEON_MAGENTA = (255, 0, 255)     # Hot magenta
COLOR_NEON_PURPLE = (200, 100, 255)    # Neon purple
COLOR_NEON_BLUE = (0, 150, 255)        # Electric blue
COLOR_NEON_PINK = (255, 50, 150)       # Hot pink

# Backgrounds - deep and rich
COLOR_BG_DARKEST = (8, 10, 15)         # Deepest background
COLOR_BG_DARK = (15, 18, 25)           # Dark background
COLOR_BG_PANEL = (20, 25, 35)          # Panel background
COLOR_BG_ELEVATED = (25, 30, 42)       # Elevated elements

# Gradients (start, end)
GRADIENT_PANEL = ((20, 25, 35), (15, 20, 30))
GRADIENT_BUTTON = ((30, 35, 50), (20, 25, 40))
GRADIENT_HEADER = ((25, 30, 45), (20, 25, 35))

# Glows and borders
COLOR_GLOW_CYAN = (0, 255, 255, 80)    # Cyan glow (with alpha)
COLOR_GLOW_MAGENTA = (255, 0, 255, 80) # Magenta glow
COLOR_BORDER_BRIGHT = (60, 80, 120)    # Bright border
COLOR_BORDER_DIM = (30, 40, 60)        # Dim border

# Text - high contrast
COLOR_TEXT_BRIGHT = (240, 250, 255)    # Brightest text
COLOR_TEXT_NORMAL = (200, 210, 230)    # Normal text
COLOR_TEXT_DIM = (150, 165, 190)       # Dimmed text (raised for readability)
COLOR_TEXT_CYAN = (0, 255, 255)        # Cyan highlight
COLOR_TEXT_MAGENTA = (255, 0, 255)     # Magenta highlight

# Fonts (Windows-first, with safe fallbacks)
# arcade.draw_text expects `font_name` to be a string or a tuple of strings.
UI_FONT = ("Bahnschrift", "Segoe UI", "Arial")
UI_FONT_MONO = ("Cascadia Mono", "Consolas", "Courier New")

# Status colors
COLOR_GOOD = (0, 255, 150)             # Success/good
COLOR_WARNING = (255, 200, 0)          # Warning
COLOR_DANGER = (255, 50, 100)          # Danger/critical
COLOR_INFO = (0, 200, 255)             # Information

# ============================================================================
# LAYOUT CONSTANTS - SINGLE SOURCE OF TRUTH
# ============================================================================

TOP_BAR_HEIGHT = 40
BOTTOM_BAR_HEIGHT = 50
RIGHT_PANEL_WIDTH = 300  # Room for full tab labels + readable content
LEFT_SIDEBAR_WIDTH = 220  # Slightly wider for better readability

PADDING = 12
PADDING_SMALL = 6
BORDER_WIDTH = 2
GLOW_WIDTH = 4

# Tab dimensions for vertical tabs
TAB_WIDTH = 45
TAB_HEIGHT = 50

# ============================================================================
# UI COMPONENTS
# ============================================================================

class TopBar:
    """Top bar showing resources, time, and alerts."""
    
    def __init__(self):
        self.x = 0
        self.y = SCREEN_H - TOP_BAR_HEIGHT
        self.width = SCREEN_W
        self.height = TOP_BAR_HEIGHT
        
    def draw(self, game_data: Dict):
        """Draw the top bar with resources and time."""
        # Background
        arcade.draw_lrbt_rectangle_filled(
            left=0,
            right=self.width,
            bottom=self.y,
            top=self.y + self.height,
            color=COLOR_BG_PANEL
        )
        
        # Border (neon cyan bottom line)
        arcade.draw_line(
            start_x=0,
            start_y=self.y,
            end_x=self.width,
            end_y=self.y,
            color=COLOR_NEON_CYAN,
            line_width=BORDER_WIDTH
        )
        
        # Time display (left side)
        time_str = game_data.get("time_str", "Day 0, 00:00")
        arcade.draw_text(
            text=time_str,
            x=PADDING * 2,
            y=self.y + self.height / 2 - 8,
            color=COLOR_TEXT_CYAN,
            font_size=16,
            bold=True,
            font_name=UI_FONT
        )
        
        # Resources (right-aligned, avoids right panel)
        resources = game_data.get("resources", {})
        
        resource_order = ["wood", "scrap", "metal", "mineral", "power", "raw_food", "cooked_meal"]
        resource_colors = {
            "wood": (139, 90, 43),      # Brown
            "scrap": (150, 150, 150),   # Gray
            "metal": (180, 180, 200),   # Silver
            "mineral": (100, 150, 200), # Blue-gray
            "power": COLOR_NEON_CYAN,   # Cyan
            "raw_food": (100, 200, 100), # Green
            "cooked_meal": (255, 180, 100) # Orange
        }
        
        def _draw_resource_icon(kind: str, cx: float, cy: float, accent: Tuple[int, int, int]) -> None:
            # Backplate
            arcade.draw_circle_filled(cx, cy, 8, COLOR_BG_ELEVATED)
            arcade.draw_circle_outline(cx, cy, 8, COLOR_BORDER_BRIGHT, 1)

            if kind == "power":
                pts = [(cx - 2, cy + 6), (cx + 1, cy + 1), (cx - 1, cy + 1), (cx + 2, cy - 6), (cx - 1, cy - 1), (cx + 1, cy - 1)]
                arcade.draw_polygon_filled(pts, accent)
            elif kind == "mineral":
                pts = [(cx, cy + 6), (cx + 5, cy), (cx, cy - 6), (cx - 5, cy)]
                arcade.draw_polygon_filled(pts, accent)
            elif kind == "metal":
                pts = [(cx - 5, cy + 3), (cx, cy + 6), (cx + 5, cy + 3), (cx + 5, cy - 3), (cx, cy - 6), (cx - 5, cy - 3)]
                arcade.draw_polygon_filled(pts, accent)
            elif kind == "wood":
                arcade.draw_lrbt_rectangle_filled(
                    left=cx - 5,
                    right=cx + 5,
                    bottom=cy - 3,
                    top=cy + 3,
                    color=accent
                )
                arcade.draw_line(cx - 4, cy - 2, cx + 4, cy + 2, (60, 40, 20), 1)
            elif kind == "scrap":
                arcade.draw_circle_filled(cx, cy, 4, accent)
                for dx, dy in [(0, 6), (6, 0), (0, -6), (-6, 0)]:
                    arcade.draw_line(cx, cy, cx + dx, cy + dy, accent, 2)
            elif kind == "raw_food":
                pts = [(cx - 1, cy + 6), (cx + 5, cy + 1), (cx + 1, cy - 6), (cx - 5, cy - 1)]
                arcade.draw_polygon_filled(pts, accent)
                arcade.draw_line(cx - 2, cy - 5, cx + 2, cy + 5, (30, 80, 40), 1)
            elif kind == "cooked_meal":
                arcade.draw_arc_outline(cx, cy - 1, 12, 8, (180, 120, 60), 0, 180, 2)
                arcade.draw_line(cx - 6, cy - 1, cx + 6, cy - 1, (180, 120, 60), 2)
            else:
                arcade.draw_circle_filled(cx, cy, 4, accent)

        y_center = self.y + self.height / 2
        slot_w = 78
        right_edge = SCREEN_W - RIGHT_PANEL_WIDTH - PADDING
        start_x = right_edge - slot_w * len(resource_order)
        if start_x < 260:
            start_x = 260

        for i, resource in enumerate(resource_order):
            amount = resources.get(resource, 0)
            accent = resource_colors.get(resource, COLOR_TEXT_BRIGHT)
            base_x = start_x + i * slot_w

            _draw_resource_icon(resource, base_x + 10, y_center, accent)
            arcade.draw_text(
                text=str(amount),
                x=base_x + 22,
                y=y_center - 9,
                color=COLOR_TEXT_BRIGHT,
                font_size=13,
                bold=True,
                font_name=UI_FONT_MONO
            )

        # Subtle top edge highlight to make the bar feel like a "window" frame
        arcade.draw_line(0, self.y + self.height, self.width, self.y + self.height, COLOR_BORDER_DIM, 1)


class ColonistListPanel:
    """Right panel showing colonist list."""
    
    def __init__(self):
        self.x = SCREEN_W - RIGHT_PANEL_WIDTH
        self.y = 0
        self.width = RIGHT_PANEL_WIDTH
        self.height = SCREEN_H - TOP_BAR_HEIGHT
        
    def draw(self, game_data: Dict):
        """Draw colonist list panel."""
        # Background
        arcade.draw_lrbt_rectangle_filled(
            left=self.x,
            right=self.x + self.width,
            bottom=self.y,
            top=self.y + self.height,
            color=COLOR_BG_PANEL
        )
        
        # Border (neon pink left line)
        arcade.draw_line(
            start_x=self.x,
            start_y=self.y,
            end_x=self.x,
            end_y=self.y + self.height,
            color=COLOR_NEON_PINK,
            line_width=BORDER_WIDTH
        )
        
        # Header
        arcade.draw_text(
            text="COLONISTS",
            x=self.x + PADDING,
            y=self.y + self.height - 30,
            color=COLOR_NEON_PINK,
            font_size=18,
            bold=True
        )
        
        # Colonist list
        colonists = game_data.get("colonist_objects", [])
        y_offset = self.y + self.height - 60
        
        for i, colonist in enumerate(colonists[:20]):  # Show first 20
            name = colonist.name
            status = colonist.current_job.type if colonist.current_job else "Idle"
            
            # Name (bright)
            arcade.draw_text(
                text=name,
                x=self.x + PADDING,
                y=y_offset - i * 30,
                color=COLOR_TEXT_BRIGHT,
                font_size=12,
                bold=True
            )
            
            # Status (dim)
            arcade.draw_text(
                text=status,
                x=self.x + PADDING,
                y=y_offset - i * 30 - 14,
                color=COLOR_TEXT_DIM,
                font_size=10
            )


class ActionBar:
    """Bottom action bar with Build/Zone/Harvest buttons and submenus.
    
    Wires to existing game functions - does NOT implement game logic.
    Calls existing place_wall(), place_floor(), etc. from buildings.py.
    """
    
    def __init__(self):
        self.x = 0
        self.y = 0
        self.width = SCREEN_W
        self.height = BOTTOM_BAR_HEIGHT
        
        # Main button layout - single row at bottom
        self.button_width = 115
        self.button_height = 38
        self.button_spacing = 6
        
        # Main category buttons - all in single row at bottom
        btn_start_x = LEFT_SIDEBAR_WIDTH + 15
        btn_y = self.y + (self.height - self.button_height) / 2
        
        # Single row of all buttons
        self.buttons = [
            {"label": "Build", "x": btn_start_x + (self.button_width + self.button_spacing) * 0, "y": btn_y, "mode": "walls"},
            {"label": "Floor", "x": btn_start_x + (self.button_width + self.button_spacing) * 1, "y": btn_y, "mode": "floors"},
            {"label": "Access", "x": btn_start_x + (self.button_width + self.button_spacing) * 2, "y": btn_y, "mode": "access"},
            {"label": "Stations", "x": btn_start_x + (self.button_width + self.button_spacing) * 3, "y": btn_y, "mode": "workstations"},
            {"label": "Furniture", "x": btn_start_x + (self.button_width + self.button_spacing) * 4, "y": btn_y, "mode": "furniture"},
            {"label": "Zone", "x": btn_start_x + (self.button_width + self.button_spacing) * 5, "y": btn_y, "mode": "zone"},
            {"label": "Rooms", "x": btn_start_x + (self.button_width + self.button_spacing) * 6, "y": btn_y, "mode": "rooms"},
            {"label": "Harvest", "x": btn_start_x + (self.button_width + self.button_spacing) * 7, "y": btn_y, "mode": "harvest"},
            {"label": "Salvage", "x": btn_start_x + (self.button_width + self.button_spacing) * 8, "y": btn_y, "mode": "salvage"},
        ]
        
        # Active mode tracking
        self.active_mode = None
        self.active_tool = None
        
        # Tooltip state
        self.hovered_item_id = None
        self.tooltip_data = None  # (title, description, extra)
        
        # Submenu definitions - organized by category
        self.walls_submenu = [
            {"label": "Wall", "tool": "wall", "cost": "1 wood, 1 mineral"},
            {"label": "Reinforced Wall", "tool": "wall_advanced", "cost": "2 mineral"},
            {"label": "Bar Counter", "tool": "scrap_bar_counter", "cost": "2 scrap, 1 wood"},
        ]
        
        self.floors_submenu = [
            {"label": "Floor", "tool": "floor", "cost": "1 wood"},
            {"label": "Stage", "tool": "stage", "cost": "2 wood, 1 scrap"},
            {"label": "Stage Stairs", "tool": "stage_stairs", "cost": "1 wood, 1 scrap"},
        ]
        
        self.access_submenu = [
            {"label": "Door", "tool": "door", "cost": "1 wood, 1 metal"},
            {"label": "Bar Door", "tool": "bar_door", "cost": "2 scrap, 1 wood"},
            {"label": "Window", "tool": "window", "cost": "1 wood, 1 mineral"},
            {"label": "Fire Escape", "tool": "fire_escape", "cost": "1 wood, 1 metal"},
            {"label": "Bridge", "tool": "bridge", "cost": "2 wood, 1 metal"},
        ]
        
        self.workstations_submenu = [
            {"label": "Gutter Still", "tool": "gutter_still", "cost": "3 scrap, 2 metal"},
            {"label": "Spark Bench", "tool": "spark_bench", "cost": "3 metal, 2 mineral, 2 scrap"},
            {"label": "Tinker Station", "tool": "tinker_station", "cost": "3 wood, 2 metal, 2 scrap"},
            {"label": "Salvager's Bench", "tool": "salvagers_bench", "cost": "3 wood, 2 scrap"},
            {"label": "Generator", "tool": "generator", "cost": "2 wood, 2 metal"},
            {"label": "Stove", "tool": "stove", "cost": "2 metal, 1 mineral"},
            {"label": "Gutter Forge", "tool": "gutter_forge", "cost": "3 metal, 2 scrap"},
            {"label": "Skinshop Loom", "tool": "skinshop_loom", "cost": "3 wood, 2 scrap"},
            {"label": "Cortex Spindle", "tool": "cortex_spindle", "cost": "2 metal, 2 mineral, 1 power"},
        ]
        
        self.furniture_submenu = [
            {"label": "Crash Bed", "tool": "furn_crash_bed"},
            {"label": "Comfort Chair", "tool": "furn_comfort_chair"},
            {"label": "Bar Stool", "tool": "furn_bar_stool"},
            {"label": "Storage Locker", "tool": "furn_storage_locker"},
            {"label": "Dining Table", "tool": "furn_dining_table"},
            {"label": "Wall Lamp", "tool": "furn_wall_lamp"},
            {"label": "Workshop Table", "tool": "furn_workshop_table"},
            {"label": "Tool Rack", "tool": "furn_tool_rack"},
            {"label": "Weapon Rack", "tool": "furn_weapon_rack"},
        ]
        
        self.zone_submenu = [
            {"label": "Stockpile", "tool": "stockpile"},
            {"label": "Roof", "tool": "roof"},
            {"label": "Allow Access", "tool": "allow"},
        ]
        
        self.rooms_submenu = [
            {"label": "Bedroom", "tool": "room_bedroom"},
            {"label": "Kitchen", "tool": "room_kitchen"},
            {"label": "Workshop", "tool": "room_workshop"},
            {"label": "Barracks", "tool": "room_barracks"},
            {"label": "Prison", "tool": "room_prison"},
            {"label": "Hospital", "tool": "room_hospital"},
            {"label": "Social Venue", "tool": "room_social_venue"},
            {"label": "Dining Hall", "tool": "room_dining_hall"},
        ]
        
        # Submenu display state
        self.submenu_visible = False
        self.submenu_items = []
        self.submenu_y = self.y + self.height + 5  # Just above action bar
        
        # Load tooltips from ui_config
        try:
            import sys
            import os
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            from ui_config import get_tooltip
            self.get_tooltip = get_tooltip
        except ImportError:
            self.get_tooltip = lambda item_id: (item_id, "No tooltip available", "")
        
    def update_hover(self, mouse_x: int, mouse_y: int):
        """Update hover state for tooltips."""
        self.hovered_item_id = None
        self.tooltip_data = None
        
        # Check submenu hover first
        if self.submenu_visible and self.submenu_items:
            submenu_height = 40
            item_width = 160
            item_spacing_x = 8
            item_spacing_y = 6
            items_per_row = 3
            start_x = LEFT_SIDEBAR_WIDTH + 15
            base_y = self.y + self.height + 8
            
            for i, item in enumerate(self.submenu_items):
                row = i // items_per_row
                col = i % items_per_row
                item_x = start_x + col * (item_width + item_spacing_x) + row * 25
                item_y = base_y + row * (submenu_height + item_spacing_y)
                
                if (item_x <= mouse_x <= item_x + item_width and
                    item_y <= mouse_y <= item_y + submenu_height):
                    item_id = item.get("tool")
                    if item_id:
                        self.hovered_item_id = item_id
                        self.tooltip_data = self.get_tooltip(item_id)
                    return
        
        # Check main button hover
        for button in self.buttons:
            if (button["x"] <= mouse_x <= button["x"] + self.button_width and
                button["y"] <= mouse_y <= button["y"] + self.button_height):
                # Main buttons don't have tooltips, just submenu items
                return
    
    def draw(self, game_data: Dict):
        """Draw action bar and submenu (if visible)."""
        # Draw submenu FIRST (so it appears above action bar)
        if self.submenu_visible and self.submenu_items:
            self._draw_submenu()
        
        # Draw tooltip if hovering over item
        if self.tooltip_data:
            self._draw_tooltip()
        
        # Background
        arcade.draw_lrbt_rectangle_filled(
            left=0,
            right=self.width,
            bottom=self.y,
            top=self.y + self.height,
            color=COLOR_BG_PANEL
        )
        
        # Border (neon cyan top line)
        arcade.draw_line(
            start_x=0,
            start_y=self.y + self.height,
            end_x=self.width,
            end_y=self.y + self.height,
            color=COLOR_NEON_CYAN,
            line_width=BORDER_WIDTH
        )
        
        # Draw main category buttons
        for button in self.buttons:
            is_active = (self.active_mode == button["mode"])
            
            # Button background with depth
            if is_active:
                button_color = (50, 25, 60)
            else:
                button_color = (20, 25, 35)
            
            arcade.draw_lrbt_rectangle_filled(
                left=button["x"],
                right=button["x"] + self.button_width,
                bottom=button["y"],
                top=button["y"] + self.button_height,
                color=button_color
            )
            
            # Button border
            border_color = COLOR_NEON_PINK if is_active else COLOR_NEON_CYAN
            border_width = 2 if is_active else 1
            arcade.draw_lrbt_rectangle_outline(
                left=button["x"],
                right=button["x"] + self.button_width,
                bottom=button["y"],
                top=button["y"] + self.button_height,
                color=border_color,
                border_width=border_width
            )
            
            # Glow effect for active buttons
            if is_active:
                arcade.draw_lrbt_rectangle_outline(
                    left=button["x"] - 1,
                    right=button["x"] + self.button_width + 1,
                    bottom=button["y"] - 1,
                    top=button["y"] + self.button_height + 1,
                    color=(*COLOR_NEON_PINK, 80),
                    border_width=3
                )
            
            # Button label
            text_color = COLOR_NEON_PINK if is_active else COLOR_TEXT_BRIGHT
            arcade.draw_text(
                text=button["label"],
                x=button["x"] + self.button_width / 2,
                y=button["y"] + self.button_height / 2,
                color=text_color,
                font_size=12,
                bold=is_active,
                anchor_x="center",
                anchor_y="center",
                font_name=UI_FONT
            )
    
    def _draw_submenu(self):
        """Draw submenu items cascading upward above action bar."""
        submenu_height = 40
        item_width = 160
        item_spacing_x = 8
        item_spacing_y = 6
        items_per_row = 3
        
        # Calculate layout
        num_rows = (len(self.submenu_items) + items_per_row - 1) // items_per_row
        
        # Start position (left-aligned with buttons)
        start_x = LEFT_SIDEBAR_WIDTH + 15
        base_y = self.y + self.height + 8
        
        # Draw each submenu item in cascading rows (upward)
        for i, item in enumerate(self.submenu_items):
            row = i // items_per_row
            col = i % items_per_row
            
            # Cascade upward: each row shifts right and up
            item_x = start_x + col * (item_width + item_spacing_x) + row * 25
            item_y = base_y + row * (submenu_height + item_spacing_y)
            
            is_active = (self.active_tool == item["tool"])
            
            # Background with gradient effect
            bg_color = (60, 30, 70) if is_active else (25, 30, 40)
            arcade.draw_lrbt_rectangle_filled(
                left=item_x,
                right=item_x + item_width,
                bottom=item_y,
                top=item_y + submenu_height,
                color=bg_color
            )
            
            # Border with glow for active
            border_color = COLOR_NEON_MAGENTA if is_active else COLOR_NEON_CYAN
            border_width = 2 if is_active else 1
            arcade.draw_lrbt_rectangle_outline(
                left=item_x,
                right=item_x + item_width,
                bottom=item_y,
                top=item_y + submenu_height,
                color=border_color,
                border_width=border_width
            )
            
            # Glow effect for active items
            if is_active:
                arcade.draw_lrbt_rectangle_outline(
                    left=item_x - 1,
                    right=item_x + item_width + 1,
                    bottom=item_y - 1,
                    top=item_y + submenu_height + 1,
                    color=(*COLOR_NEON_MAGENTA, 80),
                    border_width=3
                )
            
            # Label
            text_color = COLOR_NEON_MAGENTA if is_active else COLOR_TEXT_BRIGHT
            arcade.draw_text(
                text=item["label"],
                x=item_x + item_width / 2,
                y=item_y + submenu_height / 2 + 6,
                color=text_color,
                font_size=11,
                bold=is_active,
                anchor_x="center",
                font_name=UI_FONT
            )
            
            # Cost (if present)
            if "cost" in item:
                arcade.draw_text(
                    text=item["cost"],
                    x=item_x + item_width / 2,
                    y=item_y + submenu_height / 2 - 9,
                    color=COLOR_TEXT_DIM if not is_active else (180, 160, 190),
                    font_size=8,
                    anchor_x="center",
                    font_name=UI_FONT_MONO
                )
    
    def _draw_tooltip(self):
        """Draw tooltip box for hovered item."""
        if not self.tooltip_data:
            return
        
        title, description, extra = self.tooltip_data
        
        # Tooltip dimensions
        tooltip_width = 280
        tooltip_padding = 10
        line_height = 16
        
        # Calculate height based on content
        lines = [title]
        # Wrap description
        words = description.split()
        current_line = ""
        for word in words:
            test_line = current_line + " " + word if current_line else word
            if len(test_line) * 7 > tooltip_width - tooltip_padding * 2:
                if current_line:
                    lines.append(current_line)
                current_line = word
            else:
                current_line = test_line
        if current_line:
            lines.append(current_line)
        
        if extra:
            lines.append("")
            lines.append(extra)
        
        tooltip_height = len(lines) * line_height + tooltip_padding * 2 + 8
        
        # Position tooltip above mouse, centered
        mouse_pos = arcade.get_window().mouse
        tooltip_x = mouse_pos["x"] - tooltip_width // 2
        tooltip_y = mouse_pos["y"] + 20
        
        # Keep on screen
        if tooltip_x < 10:
            tooltip_x = 10
        if tooltip_x + tooltip_width > SCREEN_W - 10:
            tooltip_x = SCREEN_W - tooltip_width - 10
        if tooltip_y + tooltip_height > SCREEN_H - 10:
            tooltip_y = mouse_pos["y"] - tooltip_height - 10
        
        # Shadow
        arcade.draw_lrbt_rectangle_filled(
            tooltip_x + 3, tooltip_x + tooltip_width + 3,
            tooltip_y - 3, tooltip_y + tooltip_height - 3,
            (0, 0, 0, 120)
        )
        
        # Background
        arcade.draw_lrbt_rectangle_filled(
            tooltip_x, tooltip_x + tooltip_width,
            tooltip_y, tooltip_y + tooltip_height,
            (15, 18, 25)
        )
        
        # Border
        arcade.draw_lrbt_rectangle_outline(
            tooltip_x, tooltip_x + tooltip_width,
            tooltip_y, tooltip_y + tooltip_height,
            COLOR_NEON_CYAN, 2
        )
        
        # Text
        y = tooltip_y + tooltip_height - tooltip_padding - 14
        for i, line in enumerate(lines):
            if i == 0:
                # Title - bright cyan
                color = COLOR_NEON_CYAN
                bold = True
            elif line == "":
                continue
            elif line.startswith("Cost:") or line.startswith("Crafts:") or line.startswith("Produces:"):
                # Extra info - yellow/orange
                color = (255, 200, 100)
                bold = False
            else:
                # Description - normal text
                color = COLOR_TEXT_NORMAL
                bold = False
            
            arcade.draw_text(
                line,
                tooltip_x + tooltip_padding,
                y,
                color,
                font_size=10 if i == 0 else 9,
                bold=bold,
                font_name=UI_FONT
            )
            y -= line_height
    
    def handle_click(self, mouse_x: int, mouse_y: int) -> bool:
        """Handle mouse click on action bar or submenu. Returns True if click was consumed."""
        # Check submenu clicks first (if visible)
        if self.submenu_visible and self.submenu_items:
            submenu_height = 40
            item_width = 160
            item_spacing_x = 8
            item_spacing_y = 6
            items_per_row = 3
            start_x = LEFT_SIDEBAR_WIDTH + 15
            base_y = self.y + self.height + 8
            
            # Check each submenu item
            for i, item in enumerate(self.submenu_items):
                row = i // items_per_row
                col = i % items_per_row
                item_x = start_x + col * (item_width + item_spacing_x) + row * 25
                item_y = base_y + row * (submenu_height + item_spacing_y)
                
                if (item_x <= mouse_x <= item_x + item_width and
                    item_y <= mouse_y <= item_y + submenu_height):
                    # Submenu item clicked - set active tool
                    self.active_tool = item["tool"]
                    print(f"[ActionBar] Tool selected: {self.active_tool}")
                    return True
        
        # Check if click is in action bar area
        if not (self.y <= mouse_y <= self.y + self.height):
            return False
        
        # Check each main button
        for button in self.buttons:
            if (button["x"] <= mouse_x <= button["x"] + self.button_width and
                button["y"] <= mouse_y <= button["y"] + self.button_height):
                
                # Toggle mode and show/hide submenu
                if self.active_mode == button["mode"]:
                    # Clicking active button - close submenu
                    self.active_mode = None
                    self.active_tool = None
                    self.submenu_visible = False
                    self.submenu_items = []
                else:
                    # Activate new mode
                    self.active_mode = button["mode"]
                    self.active_tool = None
                    
                    # Show appropriate submenu
                    if button["mode"] == "walls":
                        self.submenu_visible = True
                        self.submenu_items = self.walls_submenu
                    elif button["mode"] == "floors":
                        self.submenu_visible = True
                        self.submenu_items = self.floors_submenu
                    elif button["mode"] == "access":
                        self.submenu_visible = True
                        self.submenu_items = self.access_submenu
                    elif button["mode"] == "workstations":
                        self.submenu_visible = True
                        self.submenu_items = self.workstations_submenu
                    elif button["mode"] == "furniture":
                        self.submenu_visible = True
                        self.submenu_items = self.furniture_submenu
                    elif button["mode"] == "zone":
                        self.submenu_visible = True
                        self.submenu_items = self.zone_submenu
                    elif button["mode"] == "rooms":
                        self.submenu_visible = True
                        self.submenu_items = self.rooms_submenu
                    elif button["mode"] == "harvest":
                        # Harvest is direct tool, no submenu
                        self.active_tool = "harvest"
                        self.submenu_visible = False
                        self.submenu_items = []
                    elif button["mode"] == "salvage":
                        # Salvage is direct tool, no submenu
                        self.active_tool = "salvage"
                        self.submenu_visible = False
                        self.submenu_items = []
                
                print(f"[ActionBar] Mode: {self.active_mode}, Tool: {self.active_tool}")
                return True
        
        return False


class ArcadeUI:
    """Main UI manager for Arcade version - Top bar and Bottom action bar only.
    
    Left sidebar and Right panel are in ui_arcade_panels.py and managed separately.
    """
    
    def __init__(self):
        self.top_bar = TopBar()
        self.action_bar = ActionBar()
        
    def draw(self, game_data: Dict):
        """Draw top bar and bottom action bar."""
        self.top_bar.draw(game_data)
        self.action_bar.draw(game_data)
    
    def handle_click(self, mouse_x: int, mouse_y: int) -> bool:
        """Handle mouse click on UI. Returns True if click was consumed."""
        # Check action bar first
        if self.action_bar.handle_click(mouse_x, mouse_y):
            return True
        
        # Add other UI click handlers here
        return False
