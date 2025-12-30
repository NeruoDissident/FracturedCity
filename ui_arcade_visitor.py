"""
Arcade native UI for visitor/wanderer interaction.

Shows visitor character sheet with Accept/Deny buttons.
"""

import arcade
from typing import Optional, Callable


class VisitorPanel:
    """Panel for interacting with visitors/wanderers."""
    
    def __init__(self):
        self.visible = False
        self.wanderer: Optional[dict] = None
        
        # Panel dimensions
        self.panel_width = 500
        self.panel_height = 600
        self.panel_x = 0
        self.panel_y = 0
        
        # Button dimensions
        self.button_width = 200
        self.button_height = 40
        
        # Callbacks
        self.on_accept: Optional[Callable] = None
        self.on_deny: Optional[Callable] = None
        
        # Colors (cyberpunk theme)
        self.bg_color = (20, 20, 30, 240)
        self.border_color = (0, 220, 220, 255)  # Cyan
        self.accept_color = (0, 220, 120, 255)  # Green
        self.deny_color = (220, 60, 80, 255)    # Red
        self.text_color = (200, 200, 220, 255)
        self.header_color = (0, 220, 220, 255)
    
    def open(self, wanderer: dict):
        """Open panel for a wanderer."""
        self.wanderer = wanderer
        self.visible = True
        
        # Center panel on screen
        from config import SCREEN_W, SCREEN_H
        self.panel_x = (SCREEN_W - self.panel_width) // 2
        self.panel_y = (SCREEN_H - self.panel_height) // 2
    
    def close(self):
        """Close the panel."""
        self.visible = False
        self.wanderer = None
    
    def handle_click(self, x: int, y: int) -> bool:
        """Handle mouse click. Returns True if click was consumed."""
        if not self.visible or not self.wanderer:
            return False
        
        # Check if click is outside panel (close)
        if not self._point_in_panel(x, y):
            self.close()
            return True
        
        # Check accept button
        accept_rect = self._get_accept_button_rect()
        if self._point_in_rect(x, y, accept_rect):
            if self.on_accept:
                self.on_accept(self.wanderer)
            self.close()
            return True
        
        # Check deny button
        deny_rect = self._get_deny_button_rect()
        if self._point_in_rect(x, y, deny_rect):
            if self.on_deny:
                self.on_deny(self.wanderer)
            self.close()
            return True
        
        return True  # Consume click even if not on button
    
    def draw(self, mouse_x: int, mouse_y: int):
        """Draw the visitor panel."""
        if not self.visible or not self.wanderer:
            return
        
        colonist = self.wanderer.get("colonist")
        if not colonist:
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
        
        # Draw header
        header_text = f">> VISITOR: {colonist.name.upper()} <<"
        arcade.draw_text(
            header_text,
            self.panel_x + self.panel_width // 2,
            self.panel_y + self.panel_height - 40,
            self.header_color,
            font_size=20,
            anchor_x="center",
            bold=True
        )
        
        # Draw character info
        y_offset = self.panel_y + self.panel_height - 100
        
        # Basic stats
        stats = [
            f"Age: {colonist.age}",
            f"Origin: {colonist.origin.name if hasattr(colonist, 'origin') else 'Unknown'}",
            f"Role: {colonist.role if hasattr(colonist, 'role') else 'None'}",
            f"",
            f"SKILLS:",
            f"  Melee: {colonist.melee_skill:.1f}" if hasattr(colonist, 'melee_skill') else "  Melee: 0",
            f"",
            f"TRAITS:",
        ]
        
        # Add traits if available
        if hasattr(colonist, 'traits') and colonist.traits:
            trait_list = list(colonist.traits)[:3]  # Convert set to list, show first 3
            for trait in trait_list:
                stats.append(f"  • {trait}")
        else:
            stats.append("  None")
        
        for stat in stats:
            arcade.draw_text(
                stat,
                self.panel_x + 30,
                y_offset,
                self.text_color,
                font_size=14,
                anchor_x="left"
            )
            y_offset -= 25
        
        # Draw accept button
        accept_rect = self._get_accept_button_rect()
        accept_hover = self._point_in_rect(mouse_x, mouse_y, accept_rect)
        accept_color = tuple(min(c + 40, 255) for c in self.accept_color[:3]) + (255,) if accept_hover else self.accept_color
        
        arcade.draw_lrbt_rectangle_filled(
            accept_rect[0], accept_rect[0] + accept_rect[2],
            accept_rect[1], accept_rect[1] + accept_rect[3],
            accept_color
        )
        arcade.draw_text(
            ">> JACK IN <<",
            accept_rect[0] + accept_rect[2] // 2,
            accept_rect[1] + accept_rect[3] // 2,
            (0, 0, 0, 255),
            font_size=16,
            anchor_x="center",
            anchor_y="center",
            bold=True
        )
        
        # Draw deny button
        deny_rect = self._get_deny_button_rect()
        deny_hover = self._point_in_rect(mouse_x, mouse_y, deny_rect)
        deny_color = tuple(min(c + 40, 255) for c in self.deny_color[:3]) + (255,) if deny_hover else self.deny_color
        
        arcade.draw_lrbt_rectangle_filled(
            deny_rect[0], deny_rect[0] + deny_rect[2],
            deny_rect[1], deny_rect[1] + deny_rect[3],
            deny_color
        )
        arcade.draw_text(
            "// FLATLINE //",
            deny_rect[0] + deny_rect[2] // 2,
            deny_rect[1] + deny_rect[3] // 2,
            (0, 0, 0, 255),
            font_size=16,
            anchor_x="center",
            anchor_y="center",
            bold=True
        )
    
    def _get_accept_button_rect(self):
        """Get accept button rect (x, y, width, height)."""
        x = self.panel_x + 50
        y = self.panel_y + 30
        return (x, y, self.button_width, self.button_height)
    
    def _get_deny_button_rect(self):
        """Get deny button rect (x, y, width, height)."""
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
_visitor_panel: Optional[VisitorPanel] = None


def get_visitor_panel() -> VisitorPanel:
    """Get or create the global visitor panel."""
    global _visitor_panel
    if _visitor_panel is None:
        _visitor_panel = VisitorPanel()
    return _visitor_panel
