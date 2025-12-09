"""
Master Lists UI for Fractured City.

Provides scrollable lists for:
- Colonists (click to open bio or jump to location)
- Buildings/Workstations (click to jump)
- Items/Stockpiles (click to jump)
- Beds (click to manage assignments)

Press L to toggle lists panel.
"""

import pygame
from typing import List, Tuple, Optional, Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from colonist import Colonist
    from grid import Grid

# Colors
BG_COLOR = (30, 30, 35)
HEADER_COLOR = (45, 45, 55)
TAB_COLOR = (40, 40, 50)
TAB_ACTIVE_COLOR = (60, 60, 80)
TAB_HOVER_COLOR = (50, 50, 65)
TEXT_COLOR = (220, 220, 220)
TEXT_DIM_COLOR = (150, 150, 150)
HIGHLIGHT_COLOR = (70, 90, 120)
BORDER_COLOR = (80, 80, 100)
SCROLLBAR_BG = (50, 50, 60)
SCROLLBAR_FG = (100, 100, 120)

# Status colors
STATUS_GOOD = (100, 200, 100)
STATUS_WARN = (200, 200, 100)
STATUS_BAD = (200, 100, 100)


class ListsPanel:
    """Master lists panel with tabs for different categories."""
    
    def __init__(self, screen_width: int, screen_height: int):
        self.visible = False
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        # Panel dimensions
        self.width = 400
        self.height = 500
        self.x = 10
        self.y = 60  # Below top bar
        
        # Tabs
        self.tabs = ["Colonists", "Buildings", "Items", "Beds"]
        self.current_tab = 0
        self.tab_height = 30
        
        # Scrolling
        self.scroll_offset = 0
        self.max_scroll = 0
        self.row_height = 28
        self.dragging_scrollbar = False
        
        # Selection
        self.hovered_row = -1
        self.selected_row = -1
        
        # Callbacks
        self.on_jump_to: Optional[Callable[[int, int, int], None]] = None
        self.on_open_colonist: Optional[Callable[["Colonist"], None]] = None
        self.on_open_bed: Optional[Callable[[int, int, int], None]] = None
        
        # Cached data
        self._colonists: List["Colonist"] = []
        self._buildings: List[dict] = []
        self._items: List[dict] = []
        self._beds: List[dict] = []
        
        # Fonts
        self.font = None
        self.font_small = None
        self.font_bold = None
        
    def _init_fonts(self):
        """Initialize fonts (must be called after pygame.init)."""
        if self.font is None:
            self.font = pygame.font.SysFont("Segoe UI", 14)
            self.font_small = pygame.font.SysFont("Segoe UI", 12)
            self.font_bold = pygame.font.SysFont("Segoe UI", 14, bold=True)
    
    def toggle(self):
        """Toggle panel visibility."""
        self.visible = not self.visible
        if self.visible:
            self.scroll_offset = 0
            self.selected_row = -1
    
    def update_data(self, colonists: List["Colonist"], grid: "Grid"):
        """Update cached data from game state."""
        self._colonists = [c for c in colonists if not c.is_dead]
        self._update_buildings(grid)
        self._update_items(grid)
        self._update_beds()
    
    def _update_buildings(self, grid: "Grid"):
        """Scan for buildings and workstations."""
        from buildings import get_all_workstations
        
        self._buildings = []
        
        # Get workstations - returns dict of {(x,y,z): data}
        for (x, y, z), ws_data in get_all_workstations().items():
            self._buildings.append({
                "name": ws_data.get("type", "Workstation").replace("_", " ").title(),
                "x": x,
                "y": y,
                "z": z,
                "type": "workstation",
                "status": "Active" if ws_data.get("active", True) else "Inactive",
            })
        
        # Sort by name
        self._buildings.sort(key=lambda b: b["name"])
    
    def _update_items(self, grid: "Grid"):
        """Scan for items in stockpiles."""
        import zones
        
        self._items = []
        item_counts = {}  # {item_type: [(x, y, z, count), ...]}
        
        # Get stockpile contents
        all_storage = zones.get_all_tile_storage()
        for (x, y, z), storage in all_storage.items():
            if storage:
                item_type = storage.get("type", "unknown")
                count = storage.get("amount", 1)  # Note: it's "amount" not "count"
                if item_type not in item_counts:
                    item_counts[item_type] = []
                item_counts[item_type].append((x, y, z, count))
        
        # Convert to list
        for item_type, locations in item_counts.items():
            total = sum(loc[3] for loc in locations)
            # Use first location as jump target
            x, y, z, _ = locations[0]
            self._items.append({
                "name": item_type.replace("_", " ").title(),
                "type": item_type,
                "count": total,
                "locations": len(locations),
                "x": x,
                "y": y,
                "z": z,
            })
        
        # Sort by name
        self._items.sort(key=lambda i: i["name"])
    
    def _update_beds(self):
        """Get bed data."""
        from beds import get_all_beds, get_colonist_bed
        
        self._beds = []
        for (x, y, z), data in get_all_beds():
            assigned_names = []
            for cid in data["assigned"]:
                for c in self._colonists:
                    if id(c) == cid:
                        assigned_names.append(c.name.split()[0])
                        break
            
            self._beds.append({
                "x": x,
                "y": y,
                "z": z,
                "quality": data["quality"],
                "assigned": assigned_names,
                "slots_free": 2 - len(data["assigned"]),
            })
        
        # Sort by position
        self._beds.sort(key=lambda b: (b["z"], b["y"], b["x"]))
    
    def _get_current_list(self) -> List[dict]:
        """Get the list for current tab."""
        if self.current_tab == 0:
            return [{"colonist": c} for c in self._colonists]
        elif self.current_tab == 1:
            return self._buildings
        elif self.current_tab == 2:
            return self._items
        elif self.current_tab == 3:
            return self._beds
        return []
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle input events. Returns True if consumed."""
        if not self.visible:
            return False
        
        self._init_fonts()
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            
            # Check if click is in panel
            if not (self.x <= mx <= self.x + self.width and 
                    self.y <= my <= self.y + self.height):
                return False
            
            # Tab clicks
            tab_y = self.y + 5
            tab_w = (self.width - 20) // len(self.tabs)
            for i, tab in enumerate(self.tabs):
                tab_x = self.x + 10 + i * tab_w
                if tab_x <= mx <= tab_x + tab_w and tab_y <= my <= tab_y + self.tab_height:
                    self.current_tab = i
                    self.scroll_offset = 0
                    self.selected_row = -1
                    return True
            
            # Scrollbar click
            scrollbar_x = self.x + self.width - 15
            content_y = self.y + self.tab_height + 15
            content_h = self.height - self.tab_height - 25
            if scrollbar_x <= mx <= scrollbar_x + 10 and content_y <= my <= content_y + content_h:
                self.dragging_scrollbar = True
                return True
            
            # Row click
            if event.button == 1:  # Left click
                row = self._get_row_at(mx, my)
                if row >= 0:
                    self._handle_row_click(row, double=False)
                    return True
            
            # Scroll wheel
            if event.button == 4:  # Scroll up
                self.scroll_offset = max(0, self.scroll_offset - self.row_height * 2)
                return True
            elif event.button == 5:  # Scroll down
                self.scroll_offset = min(self.max_scroll, self.scroll_offset + self.row_height * 2)
                return True
            
            return True  # Consume click in panel
        
        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging_scrollbar = False
        
        elif event.type == pygame.MOUSEMOTION:
            mx, my = event.pos
            
            if self.dragging_scrollbar:
                content_y = self.y + self.tab_height + 15
                content_h = self.height - self.tab_height - 25
                rel_y = (my - content_y) / content_h
                self.scroll_offset = int(rel_y * self.max_scroll)
                self.scroll_offset = max(0, min(self.max_scroll, self.scroll_offset))
                return True
            
            # Update hover
            self.hovered_row = self._get_row_at(mx, my)
        
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.visible = False
                return True
        
        return False
    
    def _get_row_at(self, mx: int, my: int) -> int:
        """Get row index at mouse position, or -1."""
        content_x = self.x + 10
        content_y = self.y + self.tab_height + 15
        content_w = self.width - 35
        content_h = self.height - self.tab_height - 25
        
        if not (content_x <= mx <= content_x + content_w and 
                content_y <= my <= content_y + content_h):
            return -1
        
        rel_y = my - content_y + self.scroll_offset
        row = int(rel_y // self.row_height)
        
        items = self._get_current_list()
        if 0 <= row < len(items):
            return row
        return -1
    
    def _handle_row_click(self, row: int, double: bool):
        """Handle click on a row."""
        items = self._get_current_list()
        if row < 0 or row >= len(items):
            return
        
        item = items[row]
        self.selected_row = row
        
        if self.current_tab == 0:  # Colonists
            colonist = item.get("colonist")
            if colonist and self.on_open_colonist:
                # Check colonist is still valid (not dead)
                if not getattr(colonist, 'is_dead', False):
                    self.on_open_colonist(colonist)
        
        elif self.current_tab == 1:  # Buildings
            if self.on_jump_to:
                self.on_jump_to(item["x"], item["y"], item["z"])
        
        elif self.current_tab == 2:  # Items
            if self.on_jump_to:
                self.on_jump_to(item["x"], item["y"], item["z"])
        
        elif self.current_tab == 3:  # Beds
            if self.on_jump_to:
                self.on_jump_to(item["x"], item["y"], item["z"])
    
    def draw(self, surface: pygame.Surface):
        """Draw the lists panel."""
        if not self.visible:
            return
        
        self._init_fonts()
        
        # Background
        panel_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        pygame.draw.rect(surface, BG_COLOR, panel_rect)
        pygame.draw.rect(surface, BORDER_COLOR, panel_rect, 2)
        
        # Header
        header_rect = pygame.Rect(self.x, self.y, self.width, self.tab_height + 10)
        pygame.draw.rect(surface, HEADER_COLOR, header_rect)
        
        # Tabs
        tab_w = (self.width - 20) // len(self.tabs)
        for i, tab in enumerate(self.tabs):
            tab_x = self.x + 10 + i * tab_w
            tab_y = self.y + 5
            tab_rect = pygame.Rect(tab_x, tab_y, tab_w - 2, self.tab_height)
            
            # Tab background
            if i == self.current_tab:
                pygame.draw.rect(surface, TAB_ACTIVE_COLOR, tab_rect)
            else:
                pygame.draw.rect(surface, TAB_COLOR, tab_rect)
            
            # Tab text
            text = self.font.render(tab, True, TEXT_COLOR)
            text_x = tab_x + (tab_w - text.get_width()) // 2
            text_y = tab_y + (self.tab_height - text.get_height()) // 2
            surface.blit(text, (text_x, text_y))
            
            # Count badge
            count = self._get_tab_count(i)
            if count > 0:
                count_text = self.font_small.render(str(count), True, TEXT_DIM_COLOR)
                surface.blit(count_text, (tab_x + tab_w - count_text.get_width() - 8, tab_y + 2))
        
        # Content area
        content_x = self.x + 10
        content_y = self.y + self.tab_height + 15
        content_w = self.width - 35
        content_h = self.height - self.tab_height - 25
        
        # Clip to content area
        clip_rect = pygame.Rect(content_x, content_y, content_w, content_h)
        old_clip = surface.get_clip()
        surface.set_clip(clip_rect)
        
        # Draw rows
        items = self._get_current_list()
        self.max_scroll = max(0, len(items) * self.row_height - content_h)
        
        for i, item in enumerate(items):
            row_y = content_y + i * self.row_height - self.scroll_offset
            
            # Skip if not visible
            if row_y + self.row_height < content_y or row_y > content_y + content_h:
                continue
            
            # Row background
            row_rect = pygame.Rect(content_x, row_y, content_w, self.row_height - 2)
            if i == self.selected_row:
                pygame.draw.rect(surface, HIGHLIGHT_COLOR, row_rect)
            elif i == self.hovered_row:
                pygame.draw.rect(surface, TAB_HOVER_COLOR, row_rect)
            
            # Draw row content based on tab
            self._draw_row(surface, item, content_x, row_y, content_w)
        
        surface.set_clip(old_clip)
        
        # Scrollbar
        if self.max_scroll > 0:
            scrollbar_x = self.x + self.width - 15
            scrollbar_h = content_h * (content_h / (len(items) * self.row_height))
            scrollbar_h = max(20, scrollbar_h)
            scrollbar_y = content_y + (self.scroll_offset / self.max_scroll) * (content_h - scrollbar_h)
            
            # Track
            pygame.draw.rect(surface, SCROLLBAR_BG, 
                           (scrollbar_x, content_y, 10, content_h))
            # Thumb
            pygame.draw.rect(surface, SCROLLBAR_FG,
                           (scrollbar_x, scrollbar_y, 10, scrollbar_h))
    
    def _get_tab_count(self, tab_index: int) -> int:
        """Get item count for a tab."""
        if tab_index == 0:
            return len(self._colonists)
        elif tab_index == 1:
            return len(self._buildings)
        elif tab_index == 2:
            return len(self._items)
        elif tab_index == 3:
            return len(self._beds)
        return 0
    
    def _draw_row(self, surface: pygame.Surface, item: dict, x: int, y: int, w: int):
        """Draw a single row based on current tab."""
        if self.current_tab == 0:
            self._draw_colonist_row(surface, item["colonist"], x, y, w)
        elif self.current_tab == 1:
            self._draw_building_row(surface, item, x, y, w)
        elif self.current_tab == 2:
            self._draw_item_row(surface, item, x, y, w)
        elif self.current_tab == 3:
            self._draw_bed_row(surface, item, x, y, w)
    
    def _draw_colonist_row(self, surface: pygame.Surface, colonist: "Colonist", 
                           x: int, y: int, w: int):
        """Draw a colonist row."""
        # Name
        name_text = self.font_bold.render(colonist.name, True, TEXT_COLOR)
        surface.blit(name_text, (x + 5, y + 2))
        
        # Status (mood + current action)
        mood = colonist.mood_state
        mood_colors = {
            "Euphoric": STATUS_GOOD,
            "Calm": STATUS_GOOD,
            "Focused": TEXT_COLOR,
            "Uneasy": STATUS_WARN,
            "Stressed": STATUS_BAD,
            "Overwhelmed": STATUS_BAD,
        }
        mood_color = mood_colors.get(mood, TEXT_COLOR)
        
        status = f"{mood}"
        if colonist.state != "idle":
            status += f" - {colonist.state}"
        
        status_text = self.font_small.render(status, True, mood_color)
        surface.blit(status_text, (x + 5, y + 14))
        
        # Health bar (small)
        bar_x = x + w - 55
        bar_y = y + 8
        bar_w = 50
        bar_h = 8
        pygame.draw.rect(surface, (60, 60, 60), (bar_x, bar_y, bar_w, bar_h))
        health_w = int(bar_w * colonist.health / 100)
        health_color = STATUS_GOOD if colonist.health > 50 else STATUS_WARN if colonist.health > 25 else STATUS_BAD
        pygame.draw.rect(surface, health_color, (bar_x, bar_y, health_w, bar_h))
    
    def _draw_building_row(self, surface: pygame.Surface, item: dict, 
                           x: int, y: int, w: int):
        """Draw a building row."""
        # Name
        name_text = self.font_bold.render(item["name"], True, TEXT_COLOR)
        surface.blit(name_text, (x + 5, y + 2))
        
        # Position and status
        pos_text = f"({item['x']}, {item['y']})"
        if item["z"] > 0:
            pos_text += f" Z{item['z']}"
        
        info_text = self.font_small.render(f"{pos_text} - {item['status']}", True, TEXT_DIM_COLOR)
        surface.blit(info_text, (x + 5, y + 14))
    
    def _draw_item_row(self, surface: pygame.Surface, item: dict, 
                       x: int, y: int, w: int):
        """Draw an item row."""
        # Name and count
        name_text = self.font_bold.render(f"{item['name']} x{item['count']}", True, TEXT_COLOR)
        surface.blit(name_text, (x + 5, y + 2))
        
        # Locations
        loc_text = f"in {item['locations']} location{'s' if item['locations'] > 1 else ''}"
        info_text = self.font_small.render(loc_text, True, TEXT_DIM_COLOR)
        surface.blit(info_text, (x + 5, y + 14))
    
    def _draw_bed_row(self, surface: pygame.Surface, item: dict, 
                      x: int, y: int, w: int):
        """Draw a bed row."""
        # Position and quality
        quality_names = {1: "Basic", 2: "Good", 3: "Excellent"}
        quality = quality_names.get(item["quality"], "Basic")
        
        name_text = self.font_bold.render(f"{quality} Bed ({item['x']}, {item['y']})", True, TEXT_COLOR)
        surface.blit(name_text, (x + 5, y + 2))
        
        # Assigned colonists
        if item["assigned"]:
            assigned_str = ", ".join(item["assigned"])
        else:
            assigned_str = "Unassigned"
        
        slots_color = STATUS_GOOD if item["slots_free"] > 0 else TEXT_DIM_COLOR
        info_text = self.font_small.render(f"{assigned_str} ({item['slots_free']} free)", True, slots_color)
        surface.blit(info_text, (x + 5, y + 14))


# =============================================================================
# GLOBAL INSTANCE
# =============================================================================

_lists_panel: Optional[ListsPanel] = None


def get_lists_panel(screen_width: int = 1280, screen_height: int = 720) -> ListsPanel:
    """Get or create the global lists panel."""
    global _lists_panel
    if _lists_panel is None:
        _lists_panel = ListsPanel(screen_width, screen_height)
    return _lists_panel


def toggle_lists_panel():
    """Toggle the lists panel visibility."""
    panel = get_lists_panel()
    panel.toggle()


def is_lists_panel_visible() -> bool:
    """Check if lists panel is visible."""
    panel = get_lists_panel()
    return panel.visible
