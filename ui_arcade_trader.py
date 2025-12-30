"""
Arcade-native trader panel for fixer interactions.

Shows fixer info and allows trading (simplified for now).
"""

import arcade
from typing import Optional, Callable
from config import SCREEN_W, SCREEN_H

# Cyberpunk color palette
COLOR_BG_PANEL = (20, 25, 35)
COLOR_BORDER = (255, 200, 80)  # Gold for traders
COLOR_TEXT_BRIGHT = (240, 250, 255)
COLOR_TEXT_DIM = (150, 165, 190)
COLOR_BUTTON_TRADE = (255, 200, 80)
COLOR_BUTTON_CANCEL = (80, 90, 110)


class TraderPanel:
    """Arcade-native trader panel for fixer interactions."""
    
    def __init__(self):
        self.visible = False
        self.fixer: Optional[dict] = None
        
        # Panel dimensions
        self.panel_width = 500
        self.panel_height = 400
        self.panel_x = (SCREEN_W - self.panel_width) // 2
        self.panel_y = (SCREEN_H - self.panel_height) // 2
        
        # Colors
        self.bg_color = COLOR_BG_PANEL
        self.border_color = COLOR_BORDER
        self.text_color = COLOR_TEXT_BRIGHT
        
        # Button dimensions
        self.button_width = 180
        self.button_height = 50
        
        # Callbacks
        self.on_trade: Optional[Callable] = None
        self.on_cancel: Optional[Callable] = None
    
    def open(self, fixer: dict):
        """Open the trader panel for a fixer."""
        self.fixer = fixer
        self.visible = True
    
    def close(self):
        """Close the trader panel."""
        self.visible = False
        self.fixer = None
    
    def handle_click(self, x: int, y: int) -> bool:
        """Handle mouse click. Returns True if consumed."""
        if not self.visible:
            return False
        
        # Check if click is outside panel (close)
        if not self._point_in_panel(x, y):
            self.close()
            return True
        
        # Check trade button (placeholder - will implement full trade UI later)
        trade_rect = self._get_trade_button_rect()
        if self._point_in_rect(x, y, trade_rect):
            print(f"[Trader] Trade with {self.fixer['name']} - full trade UI coming soon!")
            # TODO: Implement full trade UI with inventory selection
            self.close()
            return True
        
        # Check cancel button
        cancel_rect = self._get_cancel_button_rect()
        if self._point_in_rect(x, y, cancel_rect):
            self.close()
            return True
        
        return True  # Consume click even if not on button
    
    def draw(self, mouse_x: int, mouse_y: int):
        """Draw the trader panel."""
        if not self.visible or not self.fixer:
            return
        
        # Draw panel background
        arcade.draw_lrbt_rectangle_filled(
            self.panel_x,
            self.panel_x + self.panel_width,
            self.panel_y,
            self.panel_y + self.panel_height,
            self.bg_color
        )
        
        # Draw border
        arcade.draw_lrbt_rectangle_outline(
            self.panel_x,
            self.panel_x + self.panel_width,
            self.panel_y,
            self.panel_y + self.panel_height,
            self.border_color,
            border_width=3
        )
        
        # Draw title
        arcade.draw_text(
            f"// FIXER: {self.fixer['name']} //",
            self.panel_x + self.panel_width // 2,
            self.panel_y + self.panel_height - 40,
            self.border_color,
            font_size=20,
            anchor_x="center",
            bold=True
        )
        
        # Draw fixer info
        y_offset = self.panel_y + self.panel_height - 100
        
        info = [
            f"Origin: {self.fixer['origin'].name if hasattr(self.fixer.get('origin'), 'name') else 'Unknown'}",
            f"",
            f"INVENTORY:",
        ]
        
        # Show fixer inventory
        if "inventory" in self.fixer and self.fixer["inventory"]:
            for item_id, qty in list(self.fixer["inventory"].items())[:5]:  # Show first 5 items
                info.append(f"  • {item_id}: {qty}")
        else:
            info.append("  (Empty)")
        
        info.append("")
        info.append("Click 'TRADE' to open full trade interface")
        info.append("(Coming soon: drag items to trade)")
        
        for line in info:
            arcade.draw_text(
                line,
                self.panel_x + 30,
                y_offset,
                self.text_color,
                font_size=14,
                anchor_x="left"
            )
            y_offset -= 25
        
        # Draw trade button (placeholder)
        trade_rect = self._get_trade_button_rect()
        trade_hover = self._point_in_rect(mouse_x, mouse_y, trade_rect)
        trade_color = tuple(min(c + 40, 255) for c in COLOR_BUTTON_TRADE[:3]) + (255,) if trade_hover else COLOR_BUTTON_TRADE
        
        arcade.draw_lrbt_rectangle_filled(
            trade_rect[0], trade_rect[0] + trade_rect[2],
            trade_rect[1], trade_rect[1] + trade_rect[3],
            trade_color
        )
        arcade.draw_text(
            "TRADE",
            trade_rect[0] + trade_rect[2] // 2,
            trade_rect[1] + trade_rect[3] // 2,
            (0, 0, 0, 255),
            font_size=16,
            anchor_x="center",
            anchor_y="center",
            bold=True
        )
        
        # Draw cancel button
        cancel_rect = self._get_cancel_button_rect()
        cancel_hover = self._point_in_rect(mouse_x, mouse_y, cancel_rect)
        cancel_color = tuple(min(c + 40, 255) for c in COLOR_BUTTON_CANCEL[:3]) + (255,) if cancel_hover else COLOR_BUTTON_CANCEL
        
        arcade.draw_lrbt_rectangle_filled(
            cancel_rect[0], cancel_rect[0] + cancel_rect[2],
            cancel_rect[1], cancel_rect[1] + cancel_rect[3],
            cancel_color
        )
        arcade.draw_text(
            "CANCEL",
            cancel_rect[0] + cancel_rect[2] // 2,
            cancel_rect[1] + cancel_rect[3] // 2,
            (255, 255, 255, 255),
            font_size=16,
            anchor_x="center",
            anchor_y="center",
            bold=True
        )
    
    def _get_trade_button_rect(self):
        """Get trade button rect (x, y, width, height)."""
        x = self.panel_x + 50
        y = self.panel_y + 30
        return (x, y, self.button_width, self.button_height)
    
    def _get_cancel_button_rect(self):
        """Get cancel button rect (x, y, width, height)."""
        x = self.panel_x + self.panel_width - self.button_width - 50
        y = self.panel_y + 30
        return (x, y, self.button_width, self.button_height)
    
    def _point_in_panel(self, x: int, y: int) -> bool:
        """Check if point is inside panel."""
        return (self.panel_x <= x <= self.panel_x + self.panel_width and
                self.panel_y <= y <= self.panel_y + self.panel_height)
    
    def _point_in_rect(self, x: int, y: int, rect) -> bool:
        """Check if point is inside rect (x, y, width, height)."""
        return (rect[0] <= x <= rect[0] + rect[2] and
                rect[1] <= y <= rect[1] + rect[3])


# Global instance
_trader_panel: Optional[TraderPanel] = None


def get_trader_panel() -> TraderPanel:
    """Get or create the global trader panel."""
    global _trader_panel
    if _trader_panel is None:
        _trader_panel = TraderPanel()
    return _trader_panel
