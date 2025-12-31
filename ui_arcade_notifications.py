"""
Arcade-native notification system for Fractured City.

Displays notifications with cyberpunk styling and click-to-snap functionality.
"""

import arcade
from typing import Optional, Tuple, List
from config import SCREEN_W, SCREEN_H
from notifications import NotificationType, get_notifications

# Cyberpunk color palette
COLOR_BG_PANEL = (20, 25, 35)
COLOR_BG_DARK = (15, 18, 25)
COLOR_BORDER_BRIGHT = (60, 80, 120)
COLOR_TEXT_BRIGHT = (240, 250, 255)
COLOR_TEXT_DIM = (150, 165, 190)
COLOR_NEON_CYAN = (0, 255, 255)
COLOR_NEON_MAGENTA = (255, 0, 255)

# Notification type colors (matching old system)
NOTIFICATION_COLORS = {
    NotificationType.DEATH: (255, 80, 80),       # Red
    NotificationType.FIGHT_START: (255, 160, 60), # Orange
    NotificationType.FIGHT_END: (255, 220, 100),  # Yellow
    NotificationType.ROMANCE: (255, 150, 200),    # Pink
    NotificationType.ARRIVAL: (100, 200, 255),    # Blue
    NotificationType.INFO: (200, 200, 200),       # Gray
}

# Notification type prefixes (cyberpunk style)
NOTIFICATION_PREFIXES = {
    NotificationType.DEATH: "[X]",
    NotificationType.FIGHT_START: "[!]",
    NotificationType.FIGHT_END: "[~]",
    NotificationType.ROMANCE: "[♥]",
    NotificationType.ARRIVAL: "[>]",
    NotificationType.INFO: "[i]",
}


class NotificationPanel:
    """Arcade-native notification panel with click-to-snap functionality."""
    
    def __init__(self, screen_width=SCREEN_W, screen_height=SCREEN_H):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.max_visible = 5
        self.notification_height = 70
        self.notification_width = 380
        self.padding = 12
        self.spacing = 8
        
        # Position: center-top (avoid overlapping right panel)
        self.x = (screen_width - self.notification_width) // 2
        self.y = screen_height - 60  # Below top bar
        
        # Track notification rects for click detection
        self.notification_rects = []  # List of (notif, x, y, w, h)
    
    def on_resize(self, width: int, height: int):
        """Update dimensions on window resize."""
        self.screen_width = width
        self.screen_height = height
        self.x = (width - self.notification_width) // 2
        self.y = height - 60
    
    def draw(self):
        """Draw all active notifications."""
        from notifications import get_notifications
        
        # Recalculate position every frame to stay centered at top
        self.x = (self.screen_width - self.notification_width) // 2
        self.y = self.screen_height - 60
        
        notifications = get_notifications()
        visible_notifications = notifications[:self.max_visible]
        
        # Clear rect tracking
        self.notification_rects = []
        
        # Draw each notification
        for i, notif in enumerate(visible_notifications):
            notif_y = self.y - i * (self.notification_height + self.spacing)
            self._draw_notification(notif, self.x, notif_y)
    
    def _draw_notification(self, notif, x: int, y: int):
        """Draw a single notification."""
        width = self.notification_width
        height = self.notification_height
        
        # Store rect for click detection
        self.notification_rects.append((notif, x, y, width, height))
        
        # Calculate alpha based on age
        alpha = notif.alpha
        
        # Background with alpha
        bg_color = (*COLOR_BG_PANEL, alpha)
        arcade.draw_lrbt_rectangle_filled(
            left=x,
            right=x + width,
            bottom=y - height,
            top=y,
            color=bg_color
        )
        
        # Get notification type color
        type_color = NOTIFICATION_COLORS.get(notif.type, (200, 200, 200))
        accent_color = (*type_color, alpha)
        
        # Left accent bar
        arcade.draw_lrbt_rectangle_filled(
            left=x,
            right=x + 4,
            bottom=y - height,
            top=y,
            color=accent_color
        )
        
        # Border
        border_color = (*COLOR_BORDER_BRIGHT, alpha)
        arcade.draw_lrbt_rectangle_outline(
            left=x,
            right=x + width,
            bottom=y - height,
            top=y,
            color=border_color,
            border_width=1
        )
        
        # Prefix/icon
        prefix = NOTIFICATION_PREFIXES.get(notif.type, "[•]")
        text_color = (*type_color, alpha)
        
        arcade.draw_text(
            text=prefix,
            x=x + 12,
            y=y - 22,
            color=text_color,
            font_size=14,
            bold=True,
            font_name=("Bahnschrift", "Segoe UI", "Arial")
        )
        
        # Title
        title_color = (*COLOR_TEXT_BRIGHT, alpha)
        arcade.draw_text(
            text=notif.title,
            x=x + 40,
            y=y - 22,
            color=title_color,
            font_size=13,
            bold=True,
            font_name=("Bahnschrift", "Segoe UI", "Arial")
        )
        
        # Detail text (if present)
        if notif.detail:
            detail_color = (*COLOR_TEXT_DIM, alpha)
            arcade.draw_text(
                text=notif.detail,
                x=x + 12,
                y=y - 42,
                color=detail_color,
                font_size=11,
                font_name=("Segoe UI", "Arial")
            )
        
        # Click hint (if clickable)
        if notif.click_location:
            hint_color = (*COLOR_NEON_CYAN, alpha)
            arcade.draw_text(
                text="[click to locate]",
                x=x + width - 10,
                y=y - height + 8,
                color=hint_color,
                font_size=9,
                anchor_x="right",
                font_name=("Consolas", "Courier New")
            )
    
    def handle_click(self, x: int, y: int) -> Optional[Tuple[int, int]]:
        """Check if a notification was clicked. Returns (x, y) location or None."""
        for notif, notif_x, notif_y, notif_w, notif_h in self.notification_rects:
            # Check if click is within notification bounds
            # notif_y is TOP of notification, notif_y - notif_h is BOTTOM
            if (notif_x <= x <= notif_x + notif_w and 
                notif_y - notif_h <= y <= notif_y):
                # Return click location if notification has one
                if notif.click_location:
                    print(f"[Notification] Clicked notification: {notif.title} -> snap to {notif.click_location}")
                    return notif.click_location
                else:
                    print(f"[Notification] Clicked notification: {notif.title} (no location)")
        return None


# Singleton instance
_notification_panel: Optional[NotificationPanel] = None


def get_notification_panel(screen_width=SCREEN_W, screen_height=SCREEN_H) -> NotificationPanel:
    """Get the singleton notification panel instance."""
    global _notification_panel
    if _notification_panel is None:
        _notification_panel = NotificationPanel(screen_width, screen_height)
    return _notification_panel
