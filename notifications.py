"""
Event notification system for Fractured City.

Shows pop-up notifications for major events like fights, deaths, romance.
"""

import pygame
from typing import List, Tuple, Optional
from enum import Enum


class NotificationType(Enum):
    DEATH = "death"
    FIGHT_START = "fight_start"
    FIGHT_END = "fight_end"
    ROMANCE = "romance"
    ARRIVAL = "arrival"
    INFO = "info"


# Colors for notification types
NOTIFICATION_COLORS = {
    NotificationType.DEATH: (255, 80, 80),       # Red
    NotificationType.FIGHT_START: (255, 160, 60), # Orange
    NotificationType.FIGHT_END: (255, 220, 100),  # Yellow
    NotificationType.ROMANCE: (255, 150, 200),    # Pink
    NotificationType.ARRIVAL: (100, 200, 255),    # Blue
    NotificationType.INFO: (200, 200, 200),       # Gray
}

# Icons/prefixes for notification types
NOTIFICATION_ICONS = {
    NotificationType.DEATH: "💀",
    NotificationType.FIGHT_START: "⚔️",
    NotificationType.FIGHT_END: "🏳️",
    NotificationType.ROMANCE: "❤️",
    NotificationType.ARRIVAL: "👤",
    NotificationType.INFO: "ℹ️",
}


class Notification:
    """A single notification."""
    
    def __init__(self, ntype: NotificationType, title: str, detail: str = "", 
                 duration: int = 300):
        self.type = ntype
        self.title = title
        self.detail = detail
        self.duration = duration  # Ticks to display
        self.age = 0
        self.alpha = 255
    
    def update(self) -> bool:
        """Update notification. Returns False when expired."""
        self.age += 1
        
        # Fade out in last 60 ticks
        if self.age > self.duration - 60:
            self.alpha = max(0, int(255 * (self.duration - self.age) / 60))
        
        return self.age < self.duration
    
    @property
    def color(self) -> Tuple[int, int, int]:
        return NOTIFICATION_COLORS.get(self.type, (200, 200, 200))
    
    @property
    def icon(self) -> str:
        return NOTIFICATION_ICONS.get(self.type, "•")


# Global notification queue
_notifications: List[Notification] = []
_max_visible = 5
_font: pygame.font.Font = None
_font_small: pygame.font.Font = None


def _init_fonts():
    global _font, _font_small
    if _font is None:
        _font = pygame.font.SysFont("Segoe UI", 16, bold=True)
        _font_small = pygame.font.SysFont("Segoe UI", 13)


def add_notification(ntype: NotificationType, title: str, detail: str = "",
                     duration: int = 300):
    """Add a notification to the queue."""
    global _notifications
    
    notif = Notification(ntype, title, detail, duration)
    _notifications.insert(0, notif)  # Add to front
    
    # Limit total notifications
    if len(_notifications) > 20:
        _notifications = _notifications[:20]


def update_notifications():
    """Update all notifications, removing expired ones."""
    global _notifications
    _notifications = [n for n in _notifications if n.update()]


def draw_notifications(surface: pygame.Surface):
    """Draw notifications in top-left corner."""
    _init_fonts()
    
    if not _notifications:
        return
    
    x = 10
    y = 50  # Below time display
    
    for i, notif in enumerate(_notifications[:_max_visible]):
        # Background
        title_surf = _font.render(f"{notif.icon} {notif.title}", True, notif.color)
        
        width = title_surf.get_width() + 20
        height = 28
        
        if notif.detail:
            detail_surf = _font_small.render(notif.detail, True, (180, 180, 180))
            width = max(width, detail_surf.get_width() + 20)
            height = 46
        
        # Draw background with alpha
        bg = pygame.Surface((width, height), pygame.SRCALPHA)
        bg.fill((30, 30, 35, min(220, notif.alpha)))
        
        # Border
        border_color = (*notif.color, notif.alpha)
        pygame.draw.rect(bg, border_color, (0, 0, width, height), 2)
        
        surface.blit(bg, (x, y))
        
        # Title with alpha
        title_surf.set_alpha(notif.alpha)
        surface.blit(title_surf, (x + 8, y + 4))
        
        # Detail
        if notif.detail:
            detail_surf.set_alpha(notif.alpha)
            surface.blit(detail_surf, (x + 8, y + 24))
        
        y += height + 4


# =============================================================================
# CONVENIENCE FUNCTIONS FOR COMMON EVENTS
# =============================================================================

def notify_death(victim_name: str, cause: str = ""):
    """Notify of a colonist death."""
    detail = cause if cause else ""
    add_notification(NotificationType.DEATH, f"{victim_name} has died", detail, duration=480)


def notify_fight_start(attacker_name: str, defender_name: str, reason: str = ""):
    """Notify of a fight starting."""
    title = f"{attacker_name} attacked {defender_name}!"
    add_notification(NotificationType.FIGHT_START, title, reason, duration=300)


def notify_fight_end(name: str, outcome: str):
    """Notify of a fight ending."""
    add_notification(NotificationType.FIGHT_END, f"{name} {outcome}", duration=240)


def notify_romance(name1: str, name2: str):
    """Notify of a new romance."""
    add_notification(NotificationType.ROMANCE, f"{name1} & {name2} are together!", duration=360)


def notify_arrival(name: str, arrival_type: str = "wanderer"):
    """Notify of a new arrival."""
    add_notification(NotificationType.ARRIVAL, f"A {arrival_type} has arrived: {name}", duration=360)


def notify_info(message: str, duration: int = 240):
    """Generic info notification."""
    add_notification(NotificationType.INFO, message, duration=duration)
