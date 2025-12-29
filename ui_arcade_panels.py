"""ARCADE UI PANELS - Left sidebar and right panel for colonist details.

This module provides the main UI panels for the Arcade version:
- LeftSidebar: 4 tabs (COLONISTS, JOBS, ITEMS, ROOMS)
- ColonistDetailPanel: 9 tabs (Status, Bio, Body, Links, Stats, Drives, Mind, Chat, Help)

All panels are native Arcade widgets with cyberpunk styling.
"""

import arcade
from typing import Dict, List, Optional, Callable, Tuple

# Import constants from main
from config import SCREEN_W, SCREEN_H

# Import UI constants from ui_arcade.py - SINGLE SOURCE OF TRUTH
from ui_arcade import (
    LEFT_SIDEBAR_WIDTH,
    RIGHT_PANEL_WIDTH,
    TOP_BAR_HEIGHT,
    BOTTOM_BAR_HEIGHT,
    PADDING,
    PADDING_SMALL,
    COLOR_BG_DARKEST,
    COLOR_BG_DARK,
    COLOR_BG_PANEL,
    COLOR_BG_ELEVATED,
    COLOR_NEON_CYAN as COLOR_ACCENT_CYAN,
    COLOR_NEON_MAGENTA as COLOR_ACCENT_MAGENTA,
    COLOR_NEON_PINK as COLOR_ACCENT_PINK,
    COLOR_NEON_PURPLE,
    COLOR_TEXT_BRIGHT,
    COLOR_TEXT_NORMAL,
    COLOR_TEXT_DIM,
    COLOR_TEXT_CYAN,
    COLOR_TEXT_MAGENTA,
    COLOR_GOOD,
    COLOR_WARNING,
    COLOR_DANGER,
    COLOR_BORDER_BRIGHT,
    COLOR_BORDER_DIM,
    UI_FONT,
    UI_FONT_MONO,
)

# Additional colors for panels
COLOR_TAB_ACTIVE = COLOR_ACCENT_PINK
COLOR_TAB_INACTIVE = (20, 25, 35)


class LeftSidebar:
    """Left sidebar with 4 tabs: COLONISTS, JOBS, ITEMS, ROOMS."""
    
    TABS = ["COLONISTS", "JOBS", "ITEMS", "ROOMS"]
    
    def __init__(self):
        self.x = 0
        self.y = BOTTOM_BAR_HEIGHT
        self.width = LEFT_SIDEBAR_WIDTH
        self.height = SCREEN_H - TOP_BAR_HEIGHT - BOTTOM_BAR_HEIGHT
        
        # Tab state
        self.current_tab = 0  # 0=COLONISTS, 1=JOBS, 2=ITEMS, 3=ROOMS
        self.tab_height = 40
        
        # Colonist list state
        self.colonist_scroll = 0
        self.colonist_item_height = 50
        self.hovered_colonist_index = -1
        
        # Callbacks
        self.on_colonist_locate: Optional[Callable] = None  # (x, y, z) -> None
        self.on_colonist_click: Optional[Callable] = None   # (colonist) -> None
    
    def handle_click(self, x: int, y: int, colonists: List) -> bool:
        """Handle mouse click. Returns True if consumed."""
        # Check if click is in sidebar area
        if not (self.x <= x <= self.x + self.width and self.y <= y <= self.y + self.height):
            return False
        
        # Check tab clicks
        tab_y = self.y
        for i, tab_name in enumerate(self.TABS):
            tab_rect_x = self.x
            tab_rect_y = tab_y + i * self.tab_height
            tab_rect_w = self.width
            tab_rect_h = self.tab_height
            
            if (tab_rect_x <= x <= tab_rect_x + tab_rect_w and 
                tab_rect_y <= y <= tab_rect_y + tab_rect_h):
                self.current_tab = i
                return True
        
        # Check colonist list clicks (COLONISTS tab only)
        if self.current_tab == 0:
            content_y = self.y + len(self.TABS) * self.tab_height + 10
            for i, colonist in enumerate(colonists):
                item_y = content_y + i * self.colonist_item_height - self.colonist_scroll
                
                # Skip if not visible
                if item_y < content_y or item_y > self.y + self.height:
                    continue
                
                if (self.x <= x <= self.x + self.width and 
                    item_y <= y <= item_y + self.colonist_item_height):
                    # Left half = locate, right half = open panel
                    if x < self.x + self.width / 2:
                        # Locate colonist
                        if self.on_colonist_locate:
                            self.on_colonist_locate(colonist.x, colonist.y, colonist.z)
                    else:
                        # Open detail panel
                        if self.on_colonist_click:
                            self.on_colonist_click(colonist)
                    return True
        
        return True  # Consumed click (in sidebar area)
    
    def update_hover(self, mouse_x: int, mouse_y: int, colonists: List) -> None:
        """Update hover state for colonist list."""
        self.hovered_colonist_index = -1
        
        if self.current_tab != 0:  # Only for COLONISTS tab
            return
        
        if not (self.x <= mouse_x <= self.x + self.width):
            return
        
        content_y = self.y + len(self.TABS) * self.tab_height + 10
        for i, colonist in enumerate(colonists):
            item_y = content_y + i * self.colonist_item_height - self.colonist_scroll
            
            if (item_y >= content_y and item_y <= self.y + self.height and
                item_y <= mouse_y <= item_y + self.colonist_item_height):
                self.hovered_colonist_index = i
                break
    
    def draw(self, colonists: List, jobs: List, items: Dict, rooms: Dict) -> None:
        """Draw the left sidebar with premium cyberpunk styling."""
        # === MAIN BACKGROUND ===
        arcade.draw_lrbt_rectangle_filled(
            left=self.x,
            right=self.x + self.width,
            bottom=self.y,
            top=self.y + self.height,
            color=COLOR_BG_PANEL
        )
        
        # Right border with cyan glow
        arcade.draw_line(
            self.x + self.width, self.y,
            self.x + self.width, self.y + self.height,
            COLOR_ACCENT_CYAN, 3
        )
        
        # Subtle inner glow on right edge
        for i in range(6):
            alpha = 15 - i * 2
            arcade.draw_line(
                self.x + self.width - i - 1, self.y,
                self.x + self.width - i - 1, self.y + self.height,
                (*COLOR_ACCENT_CYAN, alpha), 1
            )
        
        # === DRAW TABS ===
        tab_y = self.y
        for i, tab_name in enumerate(self.TABS):
            is_active = (i == self.current_tab)
            
            tab_bottom = tab_y + i * self.tab_height
            tab_top = tab_y + (i + 1) * self.tab_height
            
            if is_active:
                # Active tab - bright with magenta accent
                arcade.draw_lrbt_rectangle_filled(
                    left=self.x,
                    right=self.x + self.width,
                    bottom=tab_bottom,
                    top=tab_top,
                    color=(40, 50, 70)
                )
                # Magenta left border accent
                arcade.draw_line(
                    self.x, tab_bottom,
                    self.x, tab_top,
                    COLOR_ACCENT_MAGENTA, 4
                )
                # Cyan bottom border
                arcade.draw_line(
                    self.x, tab_bottom,
                    self.x + self.width, tab_bottom,
                    COLOR_ACCENT_CYAN, 2
                )
                text_color = COLOR_TEXT_BRIGHT
            else:
                # Inactive tab - darker
                arcade.draw_lrbt_rectangle_filled(
                    left=self.x,
                    right=self.x + self.width,
                    bottom=tab_bottom,
                    top=tab_top,
                    color=COLOR_BG_DARK
                )
                # Dim separator
                arcade.draw_line(
                    self.x, tab_bottom,
                    self.x + self.width, tab_bottom,
                    COLOR_BORDER_DIM, 1
                )
                text_color = COLOR_TEXT_DIM
            
            # Tab text
            arcade.draw_text(
                text=tab_name,
                x=self.x + self.width / 2,
                y=tab_bottom + self.tab_height / 2,
                color=text_color,
                font_size=11,
                bold=is_active,
                anchor_x="center",
                anchor_y="center",
                font_name=UI_FONT
            )
        
        # Draw content based on active tab
        content_y = self.y + len(self.TABS) * self.tab_height + 10
        
        if self.current_tab == 0:
            # COLONISTS tab
            self._draw_colonists_tab(colonists, content_y)
        elif self.current_tab == 1:
            # JOBS tab
            self._draw_jobs_tab(jobs, content_y)
        elif self.current_tab == 2:
            # ITEMS tab (placeholder)
            arcade.draw_text(
                text="ITEMS",
                x=self.x + 10,
                y=content_y,
                color=COLOR_TEXT_DIM,
                font_size=10
            )
        elif self.current_tab == 3:
            # ROOMS tab - show all rooms grouped by type
            self._draw_rooms_tab(rooms, content_y)
    
    def _draw_colonists_tab(self, colonists: List, content_y: int) -> None:
        """Draw the COLONISTS tab content."""
        # Header
        arcade.draw_text(
            text=f"Colonists ({len(colonists)})",
            x=self.x + 10,
            y=content_y,
            color=COLOR_ACCENT_CYAN,
            font_size=11,
            bold=True,
            font_name=UI_FONT
        )
        
        content_y += 20
        
        # Draw colonist list
        for i, colonist in enumerate(colonists):
            item_y = content_y + i * self.colonist_item_height - self.colonist_scroll
            
            # Skip if not visible
            if item_y < content_y or item_y > self.y + self.height:
                continue
            
            # Highlight if hovered
            is_hovered = (i == self.hovered_colonist_index)
            if is_hovered:
                arcade.draw_lrbt_rectangle_filled(
                    left=self.x + 2,
                    right=self.x + self.width - 2,
                    bottom=item_y,
                    top=item_y + self.colonist_item_height - 2,
                    color=(40, 45, 55)
                )
            
            # Colonist name
            arcade.draw_text(
                text=colonist.name,
                x=self.x + 10,
                y=item_y + 30,
                color=COLOR_TEXT_BRIGHT,
                font_size=11,
                bold=True,
                font_name=UI_FONT
            )
            
            # Status
            status_text = colonist.state.replace("_", " ").title()
            status_color = self._get_status_color(colonist.state)
            
            arcade.draw_text(
                text=status_text,
                x=self.x + 10,
                y=item_y + 15,
                color=status_color,
                font_size=9,
                font_name=UI_FONT
            )
            
            # Status indicator (colored dot)
            arcade.draw_circle_filled(
                center_x=self.x + self.width - 15,
                center_y=item_y + 25,
                radius=4,
                color=status_color
            )
            
            # Separator line
            arcade.draw_line(
                start_x=self.x + 5,
                start_y=item_y,
                end_x=self.x + self.width - 5,
                end_y=item_y,
                color=COLOR_TEXT_DIM,
                line_width=1
            )
    
    def _draw_rooms_tab(self, rooms: Dict, content_y: int) -> None:
        """Draw the ROOMS tab content - grouped by main type with subtypes."""
        import room_system
        
        # Get all rooms from room_system
        all_rooms = room_system.get_all_rooms()
        
        if not all_rooms:
            arcade.draw_text(
                text="No rooms designated",
                x=self.x + 10,
                y=content_y,
                color=COLOR_TEXT_DIM,
                font_size=10,
                font_name=UI_FONT
            )
            return
        
        # Header
        arcade.draw_text(
            text=f"Rooms ({len(all_rooms)})",
            x=self.x + 10,
            y=content_y,
            color=COLOR_ACCENT_CYAN,
            font_size=11,
            bold=True,
            font_name=UI_FONT
        )
        
        content_y += 25
        
        # Group rooms by main type
        room_groups = {}
        for room_id, room_data in all_rooms.items():
            main_type = room_data.get("type", "Unknown")
            display_name = room_data.get("name", main_type)  # Room system stores as "name", not "display_name"
            quality = room_data.get("quality", 0)
            
            if main_type not in room_groups:
                room_groups[main_type] = []
            
            room_groups[main_type].append({
                "id": room_id,
                "display_name": display_name,
                "quality": quality
            })
        
        # Draw each room type group
        for main_type, room_list in sorted(room_groups.items()):
            type_color = self._get_room_type_color(main_type)
            
            # Main type header with total count
            arcade.draw_text(
                text=f"{main_type} ({len(room_list)})",
                x=self.x + 10,
                y=content_y,
                color=type_color,
                font_size=10,
                bold=True,
                font_name=UI_FONT
            )
            content_y += 18
            
            # Group by display_name (subtype)
            subtype_groups = {}
            for room in room_list:
                subtype = room["display_name"]
                if subtype not in subtype_groups:
                    subtype_groups[subtype] = []
                subtype_groups[subtype].append(room)
            
            # Only show subtypes if there are multiple OR if display_name differs from main_type
            show_subtypes = len(subtype_groups) > 1 or (len(subtype_groups) == 1 and list(subtype_groups.keys())[0] != main_type)
            
            if show_subtypes:
                # Draw each subtype indented
                for subtype, subtype_rooms in sorted(subtype_groups.items()):
                    # Indented subtype with count
                    arcade.draw_text(
                        text=f"  {subtype} ({len(subtype_rooms)})",
                        x=self.x + 15,
                        y=content_y,
                        color=COLOR_TEXT_BRIGHT,
                        font_size=9,
                        font_name=UI_FONT
                    )
                    
                    # Average quality indicator
                    avg_quality = sum(r["quality"] for r in subtype_rooms) / len(subtype_rooms)
                    quality_color = self._get_quality_color(avg_quality)
                    arcade.draw_text(
                        text=f"Q:{int(avg_quality)}",
                        x=self.x + self.width - 40,
                        y=content_y,
                        color=quality_color,
                        font_size=8,
                        font_name=UI_FONT_MONO
                    )
                    content_y += 16
            else:
                # Single room type with no subtypes - just show quality on same line as header
                avg_quality = sum(r["quality"] for r in room_list) / len(room_list)
                quality_color = self._get_quality_color(avg_quality)
                arcade.draw_text(
                    text=f"Q:{int(avg_quality)}",
                    x=self.x + self.width - 40,
                    y=content_y - 18,  # Align with header
                    color=quality_color,
                    font_size=9,
                    bold=True,
                    font_name=UI_FONT_MONO
                )
            
            content_y += 5  # Extra spacing between main types
    
    def _get_room_type_color(self, room_type: str) -> tuple:
        """Get color for room type."""
        colors = {
            "Bedroom": (180, 140, 200),  # Purple
            "Kitchen": (0, 255, 180),     # Aqua
            "Workshop": (255, 220, 80),   # Gold
            "Barracks": (255, 90, 90),    # Red
            "Prison": (150, 150, 150),    # Gray
            "Hospital": (100, 255, 100),  # Green
            "Social Venue": (255, 100, 255),  # Magenta
            "Dining Hall": (255, 200, 100),   # Orange
        }
        return colors.get(room_type, COLOR_TEXT_BRIGHT)
    
    def _get_quality_color(self, quality: int) -> tuple:
        """Get color based on quality score (0-100)."""
        if quality >= 80:
            return (0, 255, 150)  # Bright green
        elif quality >= 60:
            return (150, 255, 100)  # Yellow-green
        elif quality >= 40:
            return (255, 200, 50)  # Yellow
        elif quality >= 20:
            return (255, 150, 50)  # Orange
        else:
            return (255, 100, 100)  # Red
    
    def _draw_jobs_tab(self, jobs: List, content_y: int) -> None:
        """Draw the JOBS tab content - grouped by category."""
        # Header
        total_jobs = len(jobs)
        total_assigned = sum(1 for j in jobs if j.assigned)
        total_open = total_jobs - total_assigned
        
        arcade.draw_text(
            text=f"Jobs: {total_assigned}/{total_jobs} assigned",
            x=self.x + 10,
            y=content_y,
            color=COLOR_ACCENT_CYAN,
            font_size=11,
            bold=True,
            font_name=UI_FONT
        )
        
        content_y += 25
        
        # Group jobs by category
        category_counts = {}
        for job in jobs:
            cat = job.category
            if cat not in category_counts:
                category_counts[cat] = {"total": 0, "assigned": 0}
            category_counts[cat]["total"] += 1
            if job.assigned:
                category_counts[cat]["assigned"] += 1
        
        # Define display order and labels for categories
        category_display = [
            ("construction", "Construction"),
            ("crafting", "Crafting"),
            ("haul", "Hauling"),
            ("supply", "Supply"),
            ("harvest", "Harvest"),
            ("salvage", "Salvage"),
            ("equip", "Equip"),
            ("cooking", "Cooking"),
            ("training", "Training"),
            ("recreation", "Recreation"),
            ("misc", "Misc"),
        ]
        
        # Draw each category
        for category, label in category_display:
            if category not in category_counts:
                continue
            
            counts = category_counts[category]
            assigned = counts["assigned"]
            total = counts["total"]
            open_count = total - assigned
            
            # Category name and counts
            cat_color = self._get_job_color(category)
            arcade.draw_text(
                text=label,
                x=self.x + 10,
                y=content_y,
                color=cat_color,
                font_size=10,
                bold=True,
                font_name=UI_FONT
            )
            
            # Assigned/Total count
            count_text = f"{assigned}/{total}"
            arcade.draw_text(
                text=count_text,
                x=self.x + self.width - 50,
                y=content_y,
                color=COLOR_TEXT_BRIGHT,
                font_size=10,
                bold=True,
                font_name=UI_FONT_MONO
            )
            
            # Open jobs indicator
            if open_count > 0:
                arcade.draw_circle_filled(
                    center_x=self.x + self.width - 15,
                    center_y=content_y + 5,
                    radius=3,
                    color=(255, 200, 50)  # Yellow dot for open jobs
                )
            
            content_y += 22
        
        # If no jobs, show message
        if total_jobs == 0:
            arcade.draw_text(
                text="No active jobs",
                x=self.x + 10,
                y=content_y,
                color=COLOR_TEXT_DIM,
                font_size=10,
                font_name=UI_FONT
            )
    
    def _get_job_color(self, category: str) -> Tuple[int, int, int]:
        """Get color for job category."""
        if category in ("construction", "wall"):
            return (100, 200, 100)  # Green
        elif category == "haul":
            return (180, 80, 255)  # Purple
        elif category == "harvest":
            return (50, 220, 80)  # Bright green
        elif category == "crafting":
            return (0, 220, 220)  # Cyan
        elif category == "salvage":
            return (255, 180, 100)  # Orange
        else:
            return (200, 200, 200)  # White
    
    def _get_status_color(self, state: str) -> Tuple[int, int, int]:
        """Get color for colonist status."""
        if state == "idle":
            return (120, 130, 145)  # Dim gray
        elif state in ("moving_to_job", "working"):
            return (100, 200, 100)  # Green
        elif state == "hauling":
            return (180, 80, 255)  # Purple
        elif state == "eating":
            return (255, 180, 100)  # Orange
        elif state in ("crafting_fetch", "crafting_work"):
            return (0, 220, 220)  # Cyan
        else:
            return (200, 200, 200)  # White


class ColonistDetailPanel:
    """Right panel showing detailed colonist information with VERTICAL tabs."""
    
    TABS = ["Status", "Bio", "Body", "Links", "Stats", "Drives", "Mind", "Chat", "Help"]
    
    def __init__(self):
        self.visible = True  # Always visible
        self.colonists = []  # Reference to all colonists
        self.current_index = 0  # Currently viewed colonist
        self.current_tab = 0  # 0=Status, 1=Bio, etc.
        
        # Panel dimensions - more compact
        self.width = RIGHT_PANEL_WIDTH
        self.height = SCREEN_H - TOP_BAR_HEIGHT - BOTTOM_BAR_HEIGHT
        self.x = SCREEN_W - self.width
        self.y = BOTTOM_BAR_HEIGHT
        
        # VERTICAL tab dimensions (on left side of panel)
        self.tab_width = 78
        self.tab_height = 32
        self.tab_spacing = 3
    
    def open(self, colonists: List, colonist_index: int = 0):
        """Open the panel for a specific colonist."""
        self.colonists = colonists
        self.current_index = colonist_index
        self.visible = True
    
    def close(self):
        """Close the panel."""
        self.visible = False
    
    def next_colonist(self):
        """Switch to next colonist."""
        if self.colonists:
            self.current_index = (self.current_index + 1) % len(self.colonists)
    
    def prev_colonist(self):
        """Switch to previous colonist."""
        if self.colonists:
            self.current_index = (self.current_index - 1) % len(self.colonists)
    
    def handle_click(self, x: int, y: int) -> bool:
        """Handle mouse click. Returns True if consumed."""
        if not self.visible:
            return False
        
        # Check if click is in panel area
        if not (self.x <= x <= self.x + self.width and self.y <= y <= self.y + self.height):
            return False
        
        # Check VERTICAL tab clicks (on left side of panel)
        header_height = 50
        header_y = self.y + self.height - header_height
        tab_start_y = header_y - 10 - self.tab_height
        for i in range(len(self.TABS)):
            tab_y = tab_start_y - i * (self.tab_height + self.tab_spacing)
            if (self.x + 5 <= x <= self.x + 5 + self.tab_width and 
                tab_y <= y <= tab_y + self.tab_height):
                self.current_tab = i
                return True
        
        # Check prev/next buttons (at top of panel, next to name)
        btn_y = self.y + self.height - 35
        
        if (self.x + self.width - 100 <= x <= self.x + self.width - 60 and btn_y <= y <= btn_y + 25):
            self.prev_colonist()
            return True
        
        if (self.x + self.width - 55 <= x <= self.x + self.width - 15 and btn_y <= y <= btn_y + 25):
            self.next_colonist()
            return True
        
        return True  # Consumed click (in panel area)
    
    def draw(self):
        """Draw the colonist detail panel with VERTICAL tabs and premium styling."""
        if not self.visible or not self.colonists:
            return
        
        colonist = self.colonists[self.current_index]
        
        # === MAIN PANEL BACKGROUND ===
        # Dark background with subtle gradient
        arcade.draw_lrbt_rectangle_filled(
            left=self.x,
            right=self.x + self.width,
            bottom=self.y,
            top=self.y + self.height,
            color=COLOR_BG_PANEL
        )
        
        # Left border with cyan glow
        arcade.draw_line(
            self.x, self.y,
            self.x, self.y + self.height,
            COLOR_ACCENT_CYAN, 3
        )
        
        # Subtle inner glow on left edge
        for i in range(8):
            alpha = 20 - i * 2
            arcade.draw_line(
                self.x + i, self.y,
                self.x + i, self.y + self.height,
                (*COLOR_ACCENT_CYAN, alpha), 1
            )
        
        # === HEADER SECTION ===
        header_height = 50
        header_y = self.y + self.height - header_height
        
        # Header background (darker)
        arcade.draw_lrbt_rectangle_filled(
            left=self.x,
            right=self.x + self.width,
            bottom=header_y,
            top=self.y + self.height,
            color=(15, 18, 25)
        )
        
        # Header bottom border
        arcade.draw_line(
            self.x, header_y,
            self.x + self.width, header_y,
            COLOR_ACCENT_CYAN, 2
        )
        
        # Colonist name (left side)
        arcade.draw_text(
            colonist.name,
            self.x + self.tab_width + 15,
            self.y + self.height - 30,
            COLOR_ACCENT_PINK,
            font_size=14,
            bold=True,
            font_name=UI_FONT
        )
        
        # === PREV/NEXT BUTTONS ===
        btn_y = self.y + self.height - 35
        btn_height = 25
        
        # Prev button
        prev_x = self.x + self.width - 100
        arcade.draw_lrbt_rectangle_filled(
            left=prev_x,
            right=prev_x + 35,
            bottom=btn_y,
            top=btn_y + btn_height,
            color=(30, 35, 50)
        )
        arcade.draw_lrbt_rectangle_outline(
            left=prev_x,
            right=prev_x + 35,
            top=btn_y + btn_height,
            bottom=btn_y,
            color=COLOR_ACCENT_CYAN,
            border_width=1
        )
        arcade.draw_text(
            text="<",
            x=prev_x + 17, y=btn_y + 12,
            color=COLOR_TEXT_BRIGHT,
            font_size=12,
            anchor_x="center", anchor_y="center",
            bold=True
        )
        
        # Next button
        next_x = self.x + self.width - 55
        arcade.draw_lrbt_rectangle_filled(
            left=next_x,
            right=next_x + 35,
            bottom=btn_y,
            top=btn_y + btn_height,
            color=(30, 35, 50)
        )
        arcade.draw_lrbt_rectangle_outline(
            left=next_x,
            right=next_x + 35,
            top=btn_y + btn_height,
            bottom=btn_y,
            color=COLOR_ACCENT_CYAN,
            border_width=1
        )
        arcade.draw_text(
            text=">",
            x=next_x + 17, y=btn_y + 12,
            color=COLOR_TEXT_BRIGHT,
            font_size=12,
            anchor_x="center", anchor_y="center",
            bold=True
        )
        
        # Counter text
        counter_text = f"{self.current_index + 1}/{len(self.colonists)}"
        arcade.draw_text(
            counter_text,
            self.x + self.width - 110,
            self.y + self.height - 30,
            COLOR_TEXT_DIM,
            font_size=10,
            anchor_x="right",
            font_name=UI_FONT_MONO
        )
        
        # === VERTICAL TABS (on left side) ===
        tab_start_y = header_y - 10 - self.tab_height
        
        for i, tab_name in enumerate(self.TABS):
            tab_x = self.x + 5
            tab_y = tab_start_y - i * (self.tab_height + self.tab_spacing)
            is_active = (i == self.current_tab)
            
            if is_active:
                # Active tab - bright with glow
                arcade.draw_lrbt_rectangle_filled(
                    left=tab_x,
                    right=tab_x + self.tab_width,
                    bottom=tab_y,
                    top=tab_y + self.tab_height,
                    color=(40, 50, 60)
                )
                # Cyan border with glow
                arcade.draw_lrbt_rectangle_outline(
                    left=tab_x,
                    right=tab_x + self.tab_width,
                    bottom=tab_y,
                    top=tab_y + self.tab_height,
                    color=COLOR_ACCENT_CYAN,
                    border_width=2
                )
                # Glow effect
                arcade.draw_lrbt_rectangle_outline(
                    left=tab_x - 1,
                    right=tab_x + self.tab_width + 1,
                    bottom=tab_y - 1,
                    top=tab_y + self.tab_height + 1,
                    color=(*COLOR_ACCENT_CYAN, 60),
                    border_width=3
                )
                text_color = COLOR_ACCENT_CYAN
            else:
                # Inactive tab - darker
                arcade.draw_lrbt_rectangle_filled(
                    left=tab_x,
                    right=tab_x + self.tab_width,
                    bottom=tab_y,
                    top=tab_y + self.tab_height,
                    color=(20, 25, 35)
                )
                arcade.draw_lrbt_rectangle_outline(
                    left=tab_x,
                    right=tab_x + self.tab_width,
                    bottom=tab_y,
                    top=tab_y + self.tab_height,
                    color=(40, 50, 60),
                    border_width=1
                )
                text_color = COLOR_TEXT_DIM
            
            # Tab text
            arcade.draw_text(
                tab_name,
                tab_x + 10,
                y=tab_y + self.tab_height / 2,
                color=text_color,
                font_size=10,
                bold=is_active,
                anchor_x="left",
                anchor_y="center",
                font_name=UI_FONT
            )
        
        # === CONTENT AREA (to the RIGHT of tabs) ===
        content_x = self.x + self.tab_width + 10  # Start after tabs
        content_width = self.width - self.tab_width - 15
        content_y = self.y + self.height - 60  # Start below header
        content_height = self.height - 70  # Full vertical space
        
        # Draw content based on active tab
        if self.current_tab == 0:
            self._draw_status_tab(colonist, content_x, content_y, content_width, content_height)
        elif self.current_tab == 1:
            self._draw_bio_tab(colonist, content_x, content_y, content_width, content_height)
        elif self.current_tab == 2:
            self._draw_body_tab(colonist, content_x, content_y, content_width, content_height)
        elif self.current_tab == 3:
            self._draw_links_tab(colonist, content_x, content_y, content_width, content_height)
        elif self.current_tab == 4:
            self._draw_stats_tab(colonist, content_x, content_y, content_width, content_height)
        elif self.current_tab == 5:
            self._draw_drives_tab(colonist, content_x, content_y, content_width, content_height)
        elif self.current_tab == 6:
            self._draw_mind_tab(colonist, content_x, content_y, content_width, content_height)
        elif self.current_tab == 7:
            self._draw_chat_tab(colonist, content_x, content_y, content_width, content_height)
        elif self.current_tab == 8:
            self._draw_help_tab(colonist, content_x, content_y, content_width, content_height)
        
        return
        
        # Navigation buttons
        btn_y = self.y + 10
        
        # Prev button
        arcade.draw_lrbt_rectangle_filled(
            left=self.x + 20,
            right=self.x + 80,
            bottom=btn_y,
            top=btn_y + 30,
            color=COLOR_BG_DARK
        )
        arcade.draw_lrbt_rectangle_outline(
            left=self.x + 20,
            right=self.x + 80,
            top=btn_y + 30,
            bottom=btn_y,
            color=COLOR_ACCENT_CYAN,
            border_width=1
        )
        arcade.draw_text(
            text="< Prev",
            x=self.x + 50,
            y=btn_y + 15,
            color=COLOR_TEXT_BRIGHT,
            font_size=10,
            anchor_x="center",
            anchor_y="center"
        )
        
        # Next button
        arcade.draw_lrbt_rectangle_filled(
            left=self.x + self.width - 80,
            right=self.x + self.width - 20,
            bottom=btn_y,
            top=btn_y + 30,
            color=COLOR_BG_DARK
        )
        arcade.draw_lrbt_rectangle_outline(
            left=self.x + self.width - 80,
            right=self.x + self.width - 20,
            top=btn_y + 30,
            bottom=btn_y,
            color=COLOR_ACCENT_CYAN,
            border_width=1
        )
        arcade.draw_text(
            text="Next >",
            x=self.x + self.width - 50,
            y=btn_y + 15,
            color=COLOR_TEXT_BRIGHT,
            font_size=10,
            anchor_x="center",
            anchor_y="center"
        )
    
    def _draw_status_tab(self, colonist, content_x: int, content_y: int, content_width: int, content_height: int):
        """Draw the STATUS tab - matches pygame Overview tab exactly."""
        y = content_y - 10
        col1_x = content_x + 5
        col2_x = content_x + max(118, int(content_width * 0.56))
        section_color = (180, 200, 220)
        value_color = (220, 220, 230)
        muted_color = (140, 140, 150)
        
        # === LEFT COLUMN ===
        left_y = y
        
        # Current Task
        arcade.draw_text(text="Current Task", x=col1_x, y=left_y, color=section_color, font_size=10, bold=True, font_name=UI_FONT)
        left_y -= 16
        
        state = colonist.state
        job_desc = state
        if colonist.current_job:
            job_type = colonist.current_job.type
            job_desc = f"{state} ({job_type})"
        arcade.draw_text(text=job_desc[:34], x=col1_x + 4, y=left_y, color=value_color, font_size=9, font_name=UI_FONT)
        left_y -= 28
        
        # Hunger
        arcade.draw_text(text="Hunger", x=col1_x, y=left_y, color=section_color, font_size=10, bold=True, font_name=UI_FONT)
        left_y -= 16
        hunger_val = colonist.hunger
        hunger_color = (100, 200, 100) if hunger_val < 50 else (200, 200, 100) if hunger_val < 70 else (200, 100, 100)
        bar_width = max(80, min(130, int(col2_x - col1_x - 14)))
        bar_height = 8
        self._draw_bar(col1_x + 4, left_y, bar_width, bar_height, hunger_val, 100, hunger_color)
        left_y -= 24
        
        # Comfort
        arcade.draw_text(text="Comfort", x=col1_x, y=left_y, color=section_color, font_size=10, bold=True, font_name=UI_FONT)
        left_y -= 16
        comfort_val = getattr(colonist, 'comfort', 0.0)
        comfort_color = (100, 200, 150) if comfort_val > 0 else (200, 150, 100) if comfort_val < 0 else (150, 150, 150)
        comfort_display = (comfort_val + 10) / 20 * 100
        self._draw_bar(col1_x + 4, left_y, bar_width, bar_height, comfort_display, 100, comfort_color)
        left_y -= 24
        
        # Stress
        arcade.draw_text(text="Stress", x=col1_x, y=left_y, color=section_color, font_size=10, bold=True, font_name=UI_FONT)
        left_y -= 16
        stress_val = getattr(colonist, 'stress', 0.0)
        stress_color = (200, 100, 100) if stress_val > 2 else (200, 200, 100) if stress_val > 0 else (100, 150, 200)
        stress_display = (stress_val + 10) / 20 * 100
        self._draw_bar(col1_x + 4, left_y, bar_width, bar_height, stress_display, 100, stress_color)
        left_y -= 24
        
        # Role
        role = getattr(colonist, 'role', 'generalist')
        arcade.draw_text(text=f"Role: {role.capitalize()}", x=col1_x + 4, y=left_y, color=(200, 200, 255), font_size=9, font_name=UI_FONT)
        left_y -= 22
        
        # Needs of the Many
        arcade.draw_text(text="Needs of the Many", x=col1_x, y=left_y, color=section_color, font_size=10, bold=True, font_name=UI_FONT)
        left_y -= 16
        needs_val = getattr(colonist, 'needs_of_the_many', 5)
        if needs_val <= 3:
            needs_color = (255, 100, 100)
        elif needs_val <= 7:
            needs_color = (255, 200, 100)
        else:
            needs_color = (100, 255, 100)
        needs_display = (needs_val / 10.0) * 100
        self._draw_bar(col1_x + 4, left_y, bar_width, bar_height, needs_display, 100, needs_color)
        left_y -= 30
        
        # Preferences
        arcade.draw_text(text="Preferences", x=col1_x, y=left_y, color=(150, 200, 255), font_size=10, bold=True, font_name=UI_FONT)
        left_y -= 18
        
        preferences = getattr(colonist, 'preferences', {})
        pref_display = {
            "Integrity": preferences.get('likes_integrity', 0.0),
            "Echo": preferences.get('likes_echo', 0.0),
        }
        
        active_prefs = [(name, val) for name, val in pref_display.items() if abs(val) > 0.1]
        if active_prefs:
            for pref_name, pref_val in active_prefs:
                pref_color = (100, 200, 100) if pref_val > 0.5 else (200, 100, 100) if pref_val < -0.5 else (150, 150, 150)
                arcade.draw_text(text=f"{pref_name}: {pref_val:+.1f}", x=col1_x + 4, y=left_y, color=pref_color, font_size=9, font_name=UI_FONT_MONO)
                left_y -= 18
        left_y -= 20
        
        # Personality Drift
        arcade.draw_text(text="Personality Drift", x=col1_x, y=left_y, color=(200, 180, 255), font_size=10, bold=True, font_name=UI_FONT)
        left_y -= 18
        total_drift = getattr(colonist, 'last_total_drift', 0.0)
        drift_strongest = getattr(colonist, 'last_drift_strongest', ('none', 0.0))
        arcade.draw_text(text=f"Rate: {total_drift:.6f}", x=col1_x + 4, y=left_y, color=muted_color, font_size=9, font_name=UI_FONT_MONO)
        left_y -= 16
        drift_param, drift_val = drift_strongest
        if abs(drift_val) > 0.000001:
            strongest_text = f"Strongest: {drift_param}"
        else:
            strongest_text = "Strongest: (none)"
        arcade.draw_text(text=strongest_text, x=col1_x + 4, y=left_y, color=muted_color, font_size=9, font_name=UI_FONT)
        
        # === RIGHT COLUMN ===
        right_y = y
        
        # Carrying (placeholder - 6 small slots)
        arcade.draw_text(text="Carrying", x=col2_x, y=right_y, color=(200, 180, 255), font_size=10, bold=True, font_name=UI_FONT)
        right_y -= 16
        # Draw 2 rows of 3 small inventory slots
        for i in range(6):
            row = i // 3
            col = i % 3
            slot_x = col2_x + col * 27
            slot_y = right_y - row * 27
            arcade.draw_lrbt_rectangle_filled(slot_x, slot_x + 24, slot_y - 24, slot_y, (30, 35, 40))
            arcade.draw_lrbt_rectangle_outline(slot_x, slot_x + 24, slot_y - 24, slot_y, (80, 90, 100), 1)
        right_y -= 60
        
        # Mood
        arcade.draw_text(text="Mood", x=col2_x, y=right_y, color=(255, 180, 220), font_size=10, bold=True, font_name=UI_FONT)
        right_y -= 16
        mood_state = getattr(colonist, 'mood_state', 'Focused')
        mood_score = getattr(colonist, 'mood_score', 0.0)
        from colonist import Colonist
        mood_color = Colonist.get_mood_color(mood_state)
        arcade.draw_text(text=mood_state, x=col2_x + 4, y=right_y, color=mood_color, font_size=10, bold=True, font_name=UI_FONT)
        arcade.draw_text(text=f"({mood_score:+.1f})", x=col2_x + 62, y=right_y, color=muted_color, font_size=9, font_name=UI_FONT_MONO)
        right_y -= 16
        arcade.draw_text(text="(See 'Drives' tab for details)", x=col2_x + 4, y=right_y, color=muted_color, font_size=8, font_name=UI_FONT)
        right_y -= 24
        
        # Work Assignments
        arcade.draw_text(text="Work Assignments", x=col2_x, y=right_y, color=(180, 220, 180), font_size=10, bold=True, font_name=UI_FONT)
        right_y -= 18
        
        job_tags = [
            ("can_build", "Build"),
            ("can_haul", "Haul"),
            ("can_craft", "Craft"),
            ("can_cook", "Cook"),
            ("can_scavenge", "Scavenge"),
        ]
        
        for tag_id, tag_name in job_tags:
            enabled = colonist.job_tags.get(tag_id, True)
            if enabled:
                bg_color = (50, 90, 60)
                text_color = (180, 230, 180)
            else:
                bg_color = (70, 50, 50)
                text_color = (160, 130, 130)
            
            arcade.draw_lrbt_rectangle_filled(col2_x, col2_x + 85, right_y - 28, right_y, bg_color)
            arcade.draw_lrbt_rectangle_outline(col2_x, col2_x + 85, right_y - 28, right_y, (80, 140, 90) if enabled else (110, 70, 70), 1)
            arcade.draw_text(text=tag_name, x=col2_x + 42, y=right_y - 14, color=text_color, font_size=9, anchor_x="center", anchor_y="center", font_name=UI_FONT)
            right_y -= 34
        
        # === EQUIPMENT SECTION (Bottom, full width) ===
        equip_y = min(left_y, right_y) - 20
        arcade.draw_text(text="Equipment", x=col1_x, y=equip_y, color=(255, 200, 150), font_size=10, bold=True, font_name=UI_FONT)
        equip_y -= 22
        
        equipment = getattr(colonist, 'equipment', {})
        equipment_layout = [("Head", "head"), ("Body", "body"), ("Hands", "hands"), ("Feet", "feet"), ("Implant", "implant"), ("Charm", "charm")]
        
        for i, (display_name, slot_key) in enumerate(equipment_layout):
            row = i // 2
            col = i % 2
            slot_x = col1_x + col * 90
            slot_y = equip_y - row * 46
            item = equipment.get(slot_key)
            
            # Slot box
            arcade.draw_lrbt_rectangle_filled(slot_x, slot_x + 80, slot_y - 40, slot_y, (30, 35, 40))
            arcade.draw_lrbt_rectangle_outline(slot_x, slot_x + 80, slot_y - 40, slot_y, (80, 140, 90), 1)
            
            # Slot label
            arcade.draw_text(text=display_name, x=slot_x + 4, y=slot_y - 10, color=COLOR_TEXT_DIM, font_size=8, font_name=UI_FONT)
            
            # Item name if equipped
            if item:
                item_name = item.get('name', 'Item') if isinstance(item, dict) else str(item)
                arcade.draw_text(text=item_name[:14], x=slot_x + 4, y=slot_y - 24, color=COLOR_TEXT_BRIGHT, font_size=8, font_name=UI_FONT)
            else:
                arcade.draw_text(text="Empty", x=slot_x + 4, y=slot_y - 24, color=(80, 80, 90), font_size=8, font_name=UI_FONT)
    
    def _draw_bar(self, x: float, y: float, width: float, height: float, value: float, max_value: float, color: Tuple[int, int, int]):
        """Helper to draw a stat bar."""
        # Background
        arcade.draw_lrbt_rectangle_filled(x, x + width, y - height, y, COLOR_BG_DARK)
        # Fill
        fill_width = (value / max_value) * width
        arcade.draw_lrbt_rectangle_filled(x, x + fill_width, y - height, y, color)
    
    def _draw_bio_tab(self, colonist, content_x: int, content_y: int, content_width: int, content_height: int):
        """Draw the BIO tab - colonist's backstory as flowing prose with colored traits."""
        y = content_y - 10
        col1_x = content_x + 10
        normal_color = (180, 180, 190)
        
        # Header
        arcade.draw_text(
            text="BACKSTORY",
            x=col1_x,
            y=y,
            color=(200, 180, 255),
            font_size=10,
            bold=True,
            font_name=UI_FONT
        )
        y -= 18
        
        # Get cached rich backstory (generated once at colonist creation)
        backstory_segments = getattr(colonist, 'rich_backstory', [])
        
        if not backstory_segments:
            arcade.draw_text(
                text="(no backstory)",
                x=col1_x,
                y=y,
                color=COLOR_TEXT_DIM,
                font_size=9,
                font_name=UI_FONT
            )
            return
        
        # Render flowing text with inline colored traits
        max_text_width = content_width - 25
        line_x = col1_x
        line_start_x = col1_x
        
        for segment in backstory_segments:
            text = segment["text"]
            is_trait = segment.get("is_trait", False)
            color = segment.get("color", normal_color) if is_trait else normal_color
            
            # Split into words to handle wrapping
            words = text.split() if text.strip() else [text]
            
            for word in words:
                word_with_space = word + " " if word.strip() else word
                # Estimate word width (arcade doesn't have size() method, approximate)
                word_width = len(word_with_space) * 6  # Rough estimate
                
                # Check if we need to wrap
                if line_x + word_width > line_start_x + max_text_width and line_x > line_start_x:
                    # Move to next line
                    y -= 16
                    line_x = line_start_x
                
                # Draw the word
                arcade.draw_text(
                    text=word_with_space,
                    x=line_x,
                    y=y,
                    color=color,
                    font_size=9,
                    font_name=UI_FONT
                )
                line_x += word_width
        
        # Move past the last line
        y -= 24
        
        # Also show trait labels for quick reference
        arcade.draw_text(
            text="TRAITS",
            x=col1_x,
            y=y,
            color=(180, 200, 220),
            font_size=10,
            bold=True,
            font_name=UI_FONT
        )
        y -= 16
        
        from traits import get_trait_labels, TRAIT_COLORS
        traits = getattr(colonist, 'traits', {})
        trait_labels = get_trait_labels(traits)
        
        for label in trait_labels:
            if label.startswith("★"):
                trait_color = TRAIT_COLORS.get("major", (255, 200, 100))
            else:
                trait_color = (180, 200, 220)
            arcade.draw_text(
                text=f"• {label}",
                x=col1_x + 8,
                y=y,
                color=trait_color,
                font_size=9,
                font_name=UI_FONT
            )
            y -= 14
    
    def _draw_body_tab(self, colonist, content_x: int, content_y: int, content_width: int, content_height: int):
        """Draw the BODY tab - detailed body part status like Dwarf Fortress."""
        from body import Body, PartCategory, PartStatus
        
        col1_x = content_x + 5
        
        # Get or create body
        body = getattr(colonist, 'body', None)
        if body is None:
            body = Body()
            colonist.body = body
        
        y = content_y - 10
        line_h = 11
        # col1_x already set above
        col2_x = content_x + 100
        
        # Overall health header
        overall = body.get_overall_health()
        blood_loss = getattr(body, 'blood_loss', 0.0)
        
        if overall >= 90:
            health_color = (50, 255, 120)
        elif overall >= 70:
            health_color = (180, 220, 100)
        elif overall >= 50:
            health_color = (220, 180, 60)
        else:
            health_color = (255, 80, 80)
        
        arcade.draw_text(
            text=f"INTEGRITY: {overall:.0f}%",
            x=col1_x,
            y=y,
            color=health_color,
            font_size=10,
            bold=True
        )
        
        # Blood loss indicator
        if blood_loss > 0:
            if blood_loss >= 70:
                blood_color = (255, 50, 50)
                blood_text = f"BLOOD: CRITICAL ({100 - blood_loss:.0f}%)"
            elif blood_loss >= 40:
                blood_color = (255, 100, 80)
                blood_text = f"BLOOD: LOW ({100 - blood_loss:.0f}%)"
            else:
                blood_color = (255, 150, 100)
                blood_text = f"BLOOD: {100 - blood_loss:.0f}%"
            arcade.draw_text(
                text=blood_text,
                x=col1_x + 140,
                y=y,
                color=blood_color,
                font_size=9
            )
        
        y -= 18
        
        # Helper to draw a part line
        def draw_part(part_name, part, px, py, part_id=""):
            color = part.get_color()
            # Short status
            if part.status == PartStatus.MISSING:
                status_text = "GONE"
            elif part.status == PartStatus.CYBERNETIC:
                status_text = f"CYB {part.health:.0f}%"
            elif part_id == "teeth":
                teeth_count = int(32 * part.health / 100)
                status_text = f"{teeth_count}/32"
            elif part.health >= 95:
                status_text = "OK"
            else:
                status_text = f"{part.health:.0f}%"
            
            # Shorten names
            short_name = part_name.replace("Left ", "L ").replace("Right ", "R ")
            short_name = short_name.replace("Upper ", "Up ").replace("Lower ", "Lo ")
            
            arcade.draw_text(
                text=f"{short_name}: {status_text}",
                x=px,
                y=py,
                color=color,
                font_size=8
            )
        
        # LEFT COLUMN
        left_y = y
        
        # HEAD
        arcade.draw_text(text="HEAD", x=col1_x, y=left_y, color=COLOR_ACCENT_PINK, font_size=9, bold=True)
        left_y -= 14
        for part_id, part in body.get_parts_by_category(PartCategory.HEAD):
            if not part.is_internal:
                draw_part(part.name, part, col1_x + 4, left_y, part_id)
                left_y -= line_h
        left_y -= 4
        
        # TORSO
        arcade.draw_text(text="TORSO", x=col1_x, y=left_y, color=COLOR_ACCENT_PINK, font_size=9, bold=True)
        left_y -= 14
        for part_id, part in body.get_parts_by_category(PartCategory.TORSO):
            draw_part(part.name, part, col1_x + 4, left_y, part_id)
            left_y -= line_h
        left_y -= 4
        
        # LEFT ARM
        arcade.draw_text(text="L ARM", x=col1_x, y=left_y, color=COLOR_ACCENT_PINK, font_size=9, bold=True)
        left_y -= 14
        for part_id, part in body.get_parts_by_category(PartCategory.ARM_LEFT):
            name = part.name.replace("Left ", "")
            draw_part(name, part, col1_x + 4, left_y, part_id)
            left_y -= line_h
        left_y -= 4
        
        # LEFT LEG
        arcade.draw_text(text="L LEG", x=col1_x, y=left_y, color=COLOR_ACCENT_PINK, font_size=9, bold=True)
        left_y -= 14
        for part_id, part in body.get_parts_by_category(PartCategory.LEG_LEFT):
            name = part.name.replace("Left ", "")
            draw_part(name, part, col1_x + 4, left_y, part_id)
            left_y -= line_h
        
        # RIGHT COLUMN
        right_y = y
        
        # RIGHT ARM
        arcade.draw_text(text="R ARM", x=col2_x, y=right_y, color=COLOR_ACCENT_PINK, font_size=9, bold=True)
        right_y -= 14
        for part_id, part in body.get_parts_by_category(PartCategory.ARM_RIGHT):
            name = part.name.replace("Right ", "")
            draw_part(name, part, col2_x + 4, right_y, part_id)
            right_y -= line_h
        right_y -= 4
        
        # RIGHT LEG
        arcade.draw_text(text="R LEG", x=col2_x, y=right_y, color=COLOR_ACCENT_PINK, font_size=9, bold=True)
        right_y -= 14
        for part_id, part in body.get_parts_by_category(PartCategory.LEG_RIGHT):
            name = part.name.replace("Right ", "")
            draw_part(name, part, col2_x + 4, right_y, part_id)
            right_y -= line_h
        
        # BOTTOM SECTION - Combat log
        bottom_y = min(left_y, right_y) - 12
        arcade.draw_text(text="COMBAT LOG", x=col1_x, y=bottom_y, color=(255, 80, 80), font_size=9, bold=True)
        bottom_y -= 14
        
        combat_log = body.get_recent_combat_log(5)
        if combat_log:
            for entry in combat_log:
                arcade.draw_text(
                    text=entry[:50],  # Truncate long entries
                    x=col1_x + 4,
                    y=bottom_y,
                    color=COLOR_TEXT_DIM,
                    font_size=7
                )
                bottom_y -= 10
        else:
            arcade.draw_text(
                text="No injuries recorded",
                x=col1_x + 4,
                y=bottom_y,
                color=COLOR_TEXT_DIM,
                font_size=8
            )
            bottom_y -= 10
        
        bottom_y -= 8
        
        # EFFECTS
        arcade.draw_text(text="EFFECTS", x=col1_x, y=bottom_y, color=(220, 180, 100), font_size=9, bold=True)
        bottom_y -= 14
        
        modifiers = body.get_stat_modifiers()
        if modifiers:
            shown = 0
            for stat, penalty in sorted(modifiers.items()):
                if abs(penalty) > 0.1 and shown < 4:
                    text = f"{stat}: {penalty:+.0f}%"
                    color = (255, 100, 100) if penalty < 0 else (100, 255, 100)
                    arcade.draw_text(
                        text=text,
                        x=col1_x + 4,
                        y=bottom_y,
                        color=color,
                        font_size=8
                    )
                    bottom_y -= 10
                    shown += 1
        else:
            arcade.draw_text(
                text="None",
                x=col1_x + 4,
                y=bottom_y,
                color=(50, 255, 120),
                font_size=8
            )
    
    def _get_mood_color(self, mood_score: float) -> Tuple[int, int, int]:
        """Get color for mood score."""
        if mood_score > 5:
            return (100, 255, 100)  # Bright green
        elif mood_score > 0:
            return (150, 220, 150)  # Light green
        elif mood_score > -5:
            return (255, 200, 100)  # Orange
        else:
            return (255, 100, 100)  # Red
    
    def _get_hunger_color(self, hunger: float) -> Tuple[int, int, int]:
        """Get color for hunger level."""
        if hunger < 30:
            return (100, 200, 100)  # Green
        elif hunger < 70:
            return (255, 200, 100)  # Orange
        else:
            return (255, 100, 100)  # Red
    
    def _get_health_color(self, health: float) -> Tuple[int, int, int]:
        """Get color for health percentage."""
        if health > 80:
            return (100, 200, 100)  # Green
        elif health > 50:
            return (255, 200, 100)  # Orange
        else:
            return (255, 100, 100)  # Red
    
    def _draw_links_tab(self, colonist, content_x: int, content_y: int, content_width: int, content_height: int):
        """Draw the LINKS tab - colonist's relationships with others."""
        from relationships import (get_all_relationships, get_relationship_label, 
                                   get_relationship_color, get_family_bonds, find_colonist_by_id)
        
        col1_x = content_x + 5
        y = content_y - 10
        
        # Age display
        age = getattr(colonist, 'age', 25)
        arcade.draw_text(
            text=f"Age: {age}",
            x=col1_x,
            y=y,
            color=(200, 200, 210),
            font_size=10
        )
        y -= 24
        
        # Family section
        arcade.draw_text(
            text="FAMILY",
            x=col1_x,
            y=y,
            color=(200, 180, 255),
            font_size=10,
            bold=True
        )
        y -= 16
        
        family_bonds = get_family_bonds(colonist)
        if family_bonds:
            for other_id, bond in family_bonds:
                other = find_colonist_by_id(other_id, self.colonists)
                if other:
                    bond_name = bond.value.title()
                    other_name = other.name.split()[0]
                    bond_text = f"• {other_name} ({bond_name})"
                    arcade.draw_text(
                        text=bond_text,
                        x=col1_x + 8,
                        y=y,
                        color=(200, 180, 255),
                        font_size=8
                    )
                    y -= 14
        else:
            arcade.draw_text(
                text="(no family in colony)",
                x=col1_x + 8,
                y=y,
                color=COLOR_TEXT_DIM,
                font_size=8
            )
            y -= 14
        
        y -= 10
        
        # Relationships section
        arcade.draw_text(
            text="RELATIONSHIPS",
            x=col1_x,
            y=y,
            color=(180, 200, 220),
            font_size=10,
            bold=True
        )
        y -= 16
        
        relationships = get_all_relationships(colonist, self.colonists)
        
        if not relationships:
            arcade.draw_text(
                text="(no relationships yet)",
                x=col1_x + 8,
                y=y,
                color=COLOR_TEXT_DIM,
                font_size=8
            )
            return
        
        # Show all relationships (sorted by score)
        shown = 0
        for other, rel_data in relationships:
            if shown >= 12:  # Limit display
                arcade.draw_text(
                    text="...",
                    x=col1_x + 8,
                    y=y,
                    color=COLOR_TEXT_DIM,
                    font_size=8
                )
                break
            
            other_name = other.name.split()[0]
            label = get_relationship_label(colonist, other)
            score = rel_data["score"]
            color = get_relationship_color(colonist, other)
            
            # Format: "Name - Label (±score)"
            score_sign = "+" if score >= 0 else ""
            rel_text = f"• {other_name} - {label} ({score_sign}{score})"
            
            arcade.draw_text(
                text=rel_text,
                x=col1_x + 8,
                y=y,
                color=color,
                font_size=8
            )
            y -= 14
            shown += 1
    
    def _draw_stats_tab(self, colonist, content_x: int, content_y: int, content_width: int, content_height: int):
        """Draw the STATS tab - D&D style wall of text with all stats."""
        y = content_y - 10
        col1_x = content_x + 5
        muted_color = (140, 140, 150)
        value_color = (220, 220, 230)
        bonus_color = (100, 200, 100)
        penalty_color = (200, 100, 100)
        header_color = (180, 200, 220)
        
        # Get equipment stats
        equip_stats = colonist.get_equipment_stats()
        
        # === TRAITS ===
        arcade.draw_text(text="=== TRAITS ===", x=col1_x, y=y, color=(200, 180, 255), font_size=9, bold=True)
        y -= 14
        
        from traits import get_trait_labels
        traits = getattr(colonist, 'traits', {})
        trait_labels = get_trait_labels(traits)
        
        for label in trait_labels:
            trait_color = (255, 200, 100) if label.startswith("★") else (180, 200, 220)
            arcade.draw_text(text=label, x=col1_x + 4, y=y, color=trait_color, font_size=8)
            y -= 11
        
        if not trait_labels:
            arcade.draw_text(text="(no traits)", x=col1_x + 4, y=y, color=muted_color, font_size=8)
            y -= 11
        y -= 6
        
        # === MOVEMENT ===
        arcade.draw_text(text="=== MOVEMENT ===", x=col1_x, y=y, color=header_color, font_size=9, bold=True)
        y -= 14
        
        base_move = colonist.move_speed
        equip_mod = colonist.get_equipment_speed_modifier()
        mood_mod = colonist.get_mood_speed_modifier()
        effective_move = base_move * equip_mod * mood_mod
        move_text = f"{effective_move:.1f} ticks"
        if effective_move < base_move:
            move_text += " (FAST)"
        elif effective_move > base_move:
            move_text += " (slow)"
        arcade.draw_text(text=f"Move Delay:      {move_text}", x=col1_x, y=y, color=value_color, font_size=8)
        y -= 11
        
        walk_steady = equip_stats.get("walk_steady", 0)
        steady_text = f"{walk_steady:+.0%}" if walk_steady != 0 else "0%"
        arcade.draw_text(text=f"Walk Steady:     {steady_text}", x=col1_x, y=y, color=value_color, font_size=8)
        y -= 11
        
        haul_cap = colonist.get_equipment_haul_capacity()
        haul_text = f"{haul_cap:.0%}"
        arcade.draw_text(text=f"Haul Capacity:   {haul_text}", x=col1_x, y=y, color=value_color, font_size=8)
        y -= 14
        
        # === WORK SPEEDS ===
        arcade.draw_text(text="=== WORK SPEEDS ===", x=col1_x, y=y, color=header_color, font_size=9, bold=True)
        y -= 14
        
        build_mod = colonist._calculate_work_modifier("construction")
        build_text = f"{build_mod:.0%}"
        if build_mod > 1.0:
            build_text += " (FAST)"
        elif build_mod < 1.0:
            build_text += " (slow)"
        arcade.draw_text(text=f"Build Speed:     {build_text}", x=col1_x, y=y, color=value_color, font_size=8)
        y -= 11
        
        harvest_mod = colonist._calculate_work_modifier("gathering")
        harvest_text = f"{harvest_mod:.0%}"
        if harvest_mod > 1.0:
            harvest_text += " (FAST)"
        elif harvest_mod < 1.0:
            harvest_text += " (slow)"
        arcade.draw_text(text=f"Harvest Speed:   {harvest_text}", x=col1_x, y=y, color=value_color, font_size=8)
        y -= 11
        
        craft_mod = colonist._calculate_work_modifier("crafting")
        craft_text = f"{craft_mod:.0%}"
        if craft_mod > 1.0:
            craft_text += " (FAST)"
        elif craft_mod < 1.0:
            craft_text += " (slow)"
        arcade.draw_text(text=f"Craft Speed:     {craft_text}", x=col1_x, y=y, color=value_color, font_size=8)
        y -= 14
        
        # === SURVIVAL ===
        arcade.draw_text(text="=== SURVIVAL ===", x=col1_x, y=y, color=header_color, font_size=9, bold=True)
        y -= 14
        
        hazard = equip_stats.get("hazard_resist", 0)
        arcade.draw_text(text=f"Hazard Resist:   {hazard:.0%}", x=col1_x, y=y, color=value_color, font_size=8)
        y -= 11
        
        warmth = equip_stats.get("warmth", 0)
        arcade.draw_text(text=f"Warmth:          {warmth:+.1f}", x=col1_x, y=y, color=value_color, font_size=8)
        y -= 11
        
        cooling = equip_stats.get("cooling", 0)
        arcade.draw_text(text=f"Cooling:         {cooling:+.1f}", x=col1_x, y=y, color=value_color, font_size=8)
        y -= 14
        
        # === MENTAL ===
        arcade.draw_text(text="=== MENTAL ===", x=col1_x, y=y, color=header_color, font_size=9, bold=True)
        y -= 14
        
        mood_score = getattr(colonist, 'mood_score', 0)
        mood_state = getattr(colonist, 'mood_state', 'Focused')
        from colonist import Colonist
        mood_color = Colonist.get_mood_color(mood_state)
        arcade.draw_text(text=f"Mood: {mood_state} ({mood_score:+.1f})", x=col1_x, y=y, color=mood_color, font_size=8)
        y -= 11
        
        stress = getattr(colonist, 'stress', 0)
        stress_color = (100, 200, 100) if stress < 3 else (200, 200, 100) if stress < 6 else (200, 100, 100)
        arcade.draw_text(text=f"Stress: {stress:.1f}", x=col1_x, y=y, color=stress_color, font_size=8)
        y -= 11
        
        stress_resist = equip_stats.get("stress_resist", 0)
        arcade.draw_text(text=f"Stress Resist:   {stress_resist:.0%}", x=col1_x, y=y, color=value_color, font_size=8)
        y -= 11
        
        comfort = equip_stats.get("comfort", 0)
        arcade.draw_text(text=f"Comfort Bonus:   {comfort:+.2f}", x=col1_x, y=y, color=value_color, font_size=8)
        y -= 14
        
        # === EQUIPMENT BONUSES ===
        arcade.draw_text(text="=== EQUIPMENT BONUSES ===", x=col1_x, y=y, color=(255, 200, 150), font_size=9, bold=True)
        y -= 16
        
        equipment = getattr(colonist, 'equipment', {})
        has_any = False
        
        for slot, item_data in equipment.items():
            if item_data is None:
                continue
            has_any = True
            
            item_name = item_data.get("name", slot)
            if len(item_name) > 25:
                item_name = item_name[:22] + "..."
            
            arcade.draw_text(text=f"[{slot.upper()}] {item_name}", x=col1_x, y=y, color=(180, 180, 200), font_size=8)
            y -= 10
            
            if item_data.get("generated"):
                for mod in item_data.get("modifiers", [])[:3]:
                    stat = mod.get("stat", "").replace("_", " ").title()
                    val = mod.get("value", 0)
                    trigger = mod.get("trigger", "always")
                    
                    sign = "+" if val >= 0 else ""
                    if trigger == "always":
                        mod_text = f"  {sign}{val:.1f} {stat}"
                    else:
                        trigger_text = trigger.replace("_", " ")
                        mod_text = f"  {sign}{val:.1f} {stat} ({trigger_text})"
                    
                    mod_color = bonus_color if val >= 0 else penalty_color
                    arcade.draw_text(text=mod_text, x=col1_x + 8, y=y, color=mod_color, font_size=7)
                    y -= 9
        
        if not has_any:
            arcade.draw_text(text="(no equipment)", x=col1_x, y=y, color=muted_color, font_size=8)
    
    def _draw_drives_tab(self, colonist, content_x: int, content_y: int, content_width: int, content_height: int):
        """Draw the DRIVES tab - ONLY unmet needs that require action."""
        y = content_y - 10
        col1_x = content_x + 5
        muted_color = (140, 140, 150)
        
        # Collect ONLY unmet needs
        needs = []
        
        # === Bed Need ===
        try:
            from beds import get_colonist_bed
            colonist_id = id(colonist)
            bed_pos = get_colonist_bed(colonist_id)
            
            if bed_pos is None:
                needs.append(("Needs: Assigned bed", (200, 100, 100)))
        except Exception:
            pass
        
        # === Sleep Need ===
        tiredness = getattr(colonist, 'tiredness', 0.0)
        if tiredness > 60:
            needs.append(("Needs: Sleep", (200, 100, 100)))
        
        # === Social Need ===
        try:
            from relationships import get_all_relationships
            relationships = get_all_relationships(colonist, self.colonists)
            
            if not relationships:
                needs.append(("Needs: Social interaction", (200, 200, 100)))
        except Exception:
            pass
        
        # === Hunger Need ===
        hunger = getattr(colonist, 'hunger', 0.0)
        if hunger > 40:
            needs.append(("Needs: Food", (200, 100, 100)))
        
        # Draw needs list or "All needs met" message
        if needs:
            for need_text, need_color in needs:
                arcade.draw_text(text=f"• {need_text}", x=col1_x + 8, y=y, color=need_color, font_size=9)
                y -= 13
        else:
            # No unmet needs
            arcade.draw_text(text="All needs met", x=col1_x + 8, y=y, color=(100, 200, 100), font_size=9)
    
    def _draw_mind_tab(self, colonist, content_x: int, content_y: int, content_width: int, content_height: int):
        """Draw the MIND tab - colonist's internal monologue."""
        from colonist import THOUGHT_TYPES
        
        y = content_y - 10
        col1_x = content_x + 5
        muted_color = (140, 140, 150)
        header_color = (180, 200, 220)
        
        # Header
        arcade.draw_text(text="Recent Thoughts", x=col1_x, y=y, color=header_color, font_size=10, bold=True)
        y -= 18
        
        # Get recent thoughts
        thoughts = colonist.get_recent_thoughts(12)
        
        if not thoughts:
            arcade.draw_text(text="(no thoughts yet)", x=col1_x, y=y, color=muted_color, font_size=8)
            return
        
        # Draw each thought
        for thought in thoughts:
            thought_type = thought.get("type", "idle")
            text = thought.get("text", "")
            mood_effect = thought.get("mood_effect", 0.0)
            
            # Get color for thought type
            type_color = THOUGHT_TYPES.get(thought_type, (180, 180, 180))
            
            # Draw bullet point with type color
            arcade.draw_circle_filled(col1_x + 4, y + 4, 3, type_color)
            
            # Draw thought text
            arcade.draw_text(text=text[:50], x=col1_x + 14, y=y, color=(200, 200, 210), font_size=8)
            
            # Draw mood effect indicator if significant
            if abs(mood_effect) >= 0.05:
                effect_color = (100, 200, 100) if mood_effect > 0 else (200, 100, 100)
                effect_text = f"+{mood_effect:.1f}" if mood_effect > 0 else f"{mood_effect:.1f}"
                arcade.draw_text(text=effect_text, x=content_x + content_width - 40, y=y, color=effect_color, font_size=8)
            
            y -= 14
            
            if y < self.y + 100:
                arcade.draw_text(text="...", x=col1_x, y=y, color=muted_color, font_size=8)
                break
        
        # Draw legend at bottom
        y -= 10
        legend_x = col1_x
        legend_items = [
            ("environment", "Environment"),
            ("social", "Social"),
            ("work", "Work"),
            ("need", "Need"),
            ("mood", "Mood"),
            ("idle", "Idle"),
        ]
        
        for thought_type, label in legend_items:
            type_color = THOUGHT_TYPES.get(thought_type, (180, 180, 180))
            arcade.draw_circle_filled(legend_x + 4, y + 4, 3, type_color)
            arcade.draw_text(text=label, x=legend_x + 12, y=y, color=muted_color, font_size=7)
            legend_x += 60
            if legend_x > content_x + content_width - 40:
                legend_x = col1_x
                y -= 12
    
    def _draw_chat_tab(self, colonist, content_x: int, content_y: int, content_width: int, content_height: int):
        """Draw the CHAT tab - per-colonist conversation log."""
        from conversations import get_conversation_log
        
        y = content_y - 10
        col1_x = content_x + 5
        muted_color = (140, 140, 150)
        header_color = (180, 200, 220)
        my_color = (200, 150, 255)
        other_color = (150, 255, 200)
        
        # Header
        arcade.draw_text(text="Chat Log", x=col1_x, y=y, color=header_color, font_size=10, bold=True)
        y -= 18
        
        # Get recent conversations
        colonist_key = getattr(colonist, "uid", None)
        if colonist_key is None:
            colonist_key = id(colonist)
        conversations = get_conversation_log(colonist_key, 15)
        
        if not conversations:
            arcade.draw_text(text="(no conversations yet)", x=col1_x, y=y, color=muted_color, font_size=8)
            return
        
        # Draw each conversation
        colonist_first_name = colonist.name.split()[0]
        
        for conv in conversations:
            if y < self.y + 100:
                break
            
            other_name = conv.get("other_name", "???").split()[0]
            my_line = conv.get("my_line", "")
            their_line = conv.get("their_line", "")
            is_speaker = conv.get("is_speaker", True)
            
            # If this colonist spoke first, show their line first
            if is_speaker:
                # My line (purple)
                my_text = f"{colonist_first_name}: \"{my_line}\""
                arcade.draw_text(text=my_text[:60], x=col1_x + 4, y=y, color=my_color, font_size=8)
                y -= 13
                
                if y < self.y + 100:
                    break
                
                # Their response (cyan)
                their_text = f"    {other_name}: \"{their_line}\""
                arcade.draw_text(text=their_text[:60], x=col1_x + 4, y=y, color=other_color, font_size=8)
                y -= 13
            else:
                # They spoke first (cyan)
                their_text = f"{other_name}: \"{their_line}\""
                arcade.draw_text(text=their_text[:60], x=col1_x + 4, y=y, color=other_color, font_size=8)
                y -= 13
                
                if y < self.y + 100:
                    break
                
                # My response (purple)
                my_text = f"    {colonist_first_name}: \"{my_line}\""
                arcade.draw_text(text=my_text[:60], x=col1_x + 4, y=y, color=my_color, font_size=8)
                y -= 13
    
    def _draw_help_tab(self, colonist, content_x: int, content_y: int, content_width: int, content_height: int):
        """Draw the HELP tab - controls and tips."""
        y = content_y - 10
        col1_x = content_x + 5
        
        arcade.draw_text(
            text="CONTROLS",
            x=col1_x,
            y=y,
            color=COLOR_ACCENT_CYAN,
            font_size=10,
            bold=True
        )
        y -= 25
        
        controls = [
            "WASD / Arrows: Move camera",
            "Mouse Wheel: Zoom",
            "Click colonist: View details",
            "< Prev / Next >: Cycle colonists",
            "Tabs: Switch information views",
        ]
        
        for control in controls:
            arcade.draw_text(
                text=control,
                x=self.x + 20,
                y=y,
                color=COLOR_TEXT_BRIGHT,
                font_size=9
            )
            y -= 18
