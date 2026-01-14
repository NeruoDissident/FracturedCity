"""
Arcade-native stockpile filter panel.

Simple checkbox list to toggle resource filters for stockpile zones.
"""

import arcade
from typing import Optional, Dict, List, Tuple

# Cyberpunk color palette
COLOR_BG_PANEL = (20, 25, 35, 240)
COLOR_BG_ELEVATED = (30, 35, 45)
COLOR_BORDER = (0, 220, 220)  # Cyan
COLOR_TEXT_BRIGHT = (240, 250, 255)
COLOR_TEXT_DIM = (150, 165, 190)
COLOR_CHECKBOX_ON = (0, 220, 120)  # Green
COLOR_CHECKBOX_OFF = (80, 90, 110)  # Gray

# Resource type definitions
RESOURCE_TYPES = ["wood", "mineral", "scrap", "metal", "power", "raw_food", "cooked_meal", "equipment"]
RESOURCE_NAMES = {
    "wood": "Wood",
    "mineral": "Mineral",
    "scrap": "Scrap",
    "metal": "Metal",
    "power": "Power",
    "raw_food": "Raw Food",
    "cooked_meal": "Meals",
    "equipment": "Equipment & Furniture",
}
RESOURCE_COLORS = {
    "wood": (139, 90, 43),
    "mineral": (80, 200, 200),
    "scrap": (120, 120, 120),
    "metal": (180, 180, 200),
    "power": (255, 220, 80),
    "raw_food": (180, 220, 100),
    "cooked_meal": (220, 160, 80),
    "equipment": (160, 140, 200),
}


class StockpileFilterPanel:
    """Simple checkbox panel for toggling stockpile resource filters."""
    
    def __init__(self):
        self.visible = False
        self.zone_id: Optional[int] = None
        self.zone_info: Optional[dict] = None
        
        # Panel dimensions
        self.panel_width = 280
        self.panel_height = 320
        self.panel_x = 0
        self.panel_y = 0
        
        # Checkbox tracking (left, right, bottom, top, resource_type)
        self.checkbox_rects: List[Tuple[float, float, float, float, str]] = []
    
    def open(self, zone_id: int, screen_x: int, screen_y: int):
        """Open panel for a stockpile zone."""
        import zones as zones_module
        
        self.zone_id = zone_id
        self.zone_info = zones_module.get_zone_info(zone_id)
        
        if self.zone_info is None:
            return
        
        self.visible = True
        
        # Position panel near click (keep on screen)
        from config import SCREEN_W, SCREEN_H
        self.panel_x = min(screen_x, SCREEN_W - self.panel_width - 10)
        self.panel_y = min(screen_y, SCREEN_H - self.panel_height - 60)
    
    def close(self):
        """Close the panel."""
        self.visible = False
        self.zone_id = None
        self.zone_info = None
    
    def handle_click(self, x: float, y: float) -> bool:
        """Handle mouse click. Returns True if consumed."""
        if not self.visible:
            return False
        
        # Check if click is outside panel (close)
        if not (self.panel_x <= x <= self.panel_x + self.panel_width and
                self.panel_y <= y <= self.panel_y + self.panel_height):
            self.close()
            return True
        
        # Check checkbox clicks
        import zones as zones_module
        for left, right, bottom, top, res_type in self.checkbox_rects:
            if left <= x <= right and bottom <= y <= top:
                # Toggle filter
                old_val = self.zone_info.get(f"allow_{res_type}", True)
                new_val = zones_module.toggle_zone_filter(self.zone_id, res_type)
                if new_val is not None:
                    # Refresh zone info
                    self.zone_info = zones_module.get_zone_info(self.zone_id)
                    print(f"[StockpilePanel] Toggled {res_type}: {old_val} → {new_val}")
                    print(f"[StockpilePanel] Zone info after refresh: allow_{res_type} = {self.zone_info.get(f'allow_{res_type}', 'NOT SET')}")
                return True
        
        return True  # Consume all clicks on panel
    
    def draw(self):
        """Draw the stockpile filter panel."""
        if not self.visible or self.zone_info is None:
            return
        
        # Clear and rebuild checkbox rects each frame
        self.checkbox_rects.clear()
        
        # Panel background
        arcade.draw_lrbt_rectangle_filled(
            self.panel_x,
            self.panel_x + self.panel_width,
            self.panel_y,
            self.panel_y + self.panel_height,
            COLOR_BG_PANEL
        )
        
        # Border
        arcade.draw_lrbt_rectangle_outline(
            self.panel_x,
            self.panel_x + self.panel_width,
            self.panel_y,
            self.panel_y + self.panel_height,
            COLOR_BORDER,
            border_width=2
        )
        
        # Title
        arcade.draw_text(
            "STOCKPILE FILTERS",
            self.panel_x + self.panel_width / 2,
            self.panel_y + self.panel_height - 25,
            COLOR_TEXT_BRIGHT,
            font_size=14,
            anchor_x="center",
            bold=True
        )
        
        # Draw checkboxes (rebuild rects each frame)
        self.checkbox_rects.clear()
        y = self.panel_y + self.panel_height - 60
        
        for res_type in RESOURCE_TYPES:
            filter_key = f"allow_{res_type}"
            # Get current filter state from zone (defaults to True if not set)
            is_enabled = self.zone_info.get(filter_key, True)
            
            # Checkbox square
            checkbox_size = 18
            checkbox_x = self.panel_x + 15
            checkbox_y = y
            
            # Background
            checkbox_color = COLOR_CHECKBOX_ON if is_enabled else COLOR_CHECKBOX_OFF
            arcade.draw_lrbt_rectangle_filled(
                checkbox_x,
                checkbox_x + checkbox_size,
                checkbox_y,
                checkbox_y + checkbox_size,
                checkbox_color
            )
            
            # Border
            arcade.draw_lrbt_rectangle_outline(
                checkbox_x,
                checkbox_x + checkbox_size,
                checkbox_y,
                checkbox_y + checkbox_size,
                COLOR_BORDER,
                border_width=1
            )
            
            # Checkmark if enabled
            if is_enabled:
                arcade.draw_text(
                    "✓",
                    checkbox_x + checkbox_size / 2,
                    checkbox_y + checkbox_size / 2 - 2,
                    COLOR_TEXT_BRIGHT,
                    font_size=16,
                    anchor_x="center",
                    anchor_y="center",
                    bold=True
                )
            
            # Resource name with color indicator
            res_color = RESOURCE_COLORS.get(res_type, (200, 200, 200))
            res_name = RESOURCE_NAMES.get(res_type, res_type)
            
            # Color dot
            arcade.draw_circle_filled(
                checkbox_x + checkbox_size + 15,
                checkbox_y + checkbox_size / 2,
                4,
                res_color
            )
            
            # Label
            arcade.draw_text(
                res_name,
                checkbox_x + checkbox_size + 28,
                checkbox_y + checkbox_size / 2 - 2,
                COLOR_TEXT_BRIGHT if is_enabled else COLOR_TEXT_DIM,
                font_size=12,
                anchor_y="center"
            )
            
            # Store clickable rect (entire row is clickable)
            self.checkbox_rects.append((
                checkbox_x,
                checkbox_x + self.panel_width - 30,
                checkbox_y,
                checkbox_y + checkbox_size,
                res_type
            ))
            
            y -= 32


# Singleton instance
_stockpile_panel: Optional[StockpileFilterPanel] = None


def get_stockpile_panel() -> StockpileFilterPanel:
    """Get the singleton stockpile filter panel."""
    global _stockpile_panel
    if _stockpile_panel is None:
        _stockpile_panel = StockpileFilterPanel()
    return _stockpile_panel
