"""UI Panels for Fractured City (Arcade Version).

This module provides the main UI panels for the Arcade version:
- LeftSidebar: 5 tabs (COLONISTS, ANIMALS, JOBS, ITEMS, ROOMS)

Detail panels are now center popups:
- ColonistPopup: ui_arcade_colonist_popup.py
- AnimalPopup: ui_arcade_animal_popup.py

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
    """Left sidebar with 5 tabs: COLONISTS, ANIMALS, JOBS, ITEMS, ROOMS."""
    
    TABS = ["COLONISTS", "ANIMALS", "JOBS", "ITEMS", "ROOMS"]
    
    def __init__(self, screen_width=SCREEN_W, screen_height=SCREEN_H):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.x = 0
        self.y = BOTTOM_BAR_HEIGHT
        self.width = LEFT_SIDEBAR_WIDTH
        self.height = screen_height - TOP_BAR_HEIGHT - BOTTOM_BAR_HEIGHT
        
        # Tab state
        self.current_tab = 0  # 0=COLONISTS, 1=JOBS, 2=ITEMS, 3=ROOMS
        self.tab_height = 40
        
        # Colonist list state
        self.colonist_scroll = 0
        self.colonist_item_height = 50
        self.hovered_colonist_index = -1
        
        # Animal list state
        self.animal_scroll = 0
        self.animal_item_height = 50
        self.hovered_animal_index = -1
        self.collapsed_species = set()  # Set of collapsed species IDs
        self.species_group_height = 30  # Height of species header
        
        # Callbacks
        self.on_colonist_locate: Optional[Callable] = None  # (x, y, z) -> None
        self.on_colonist_click: Optional[Callable] = None   # (colonist) -> None
        self.on_animal_locate: Optional[Callable] = None    # (x, y, z) -> None
        self.on_animal_click: Optional[Callable] = None     # (animal) -> None
    
    def on_resize(self, width: int, height: int):
        """Update dimensions on window resize."""
        self.screen_width = width
        self.screen_height = height
        self.height = height - TOP_BAR_HEIGHT - BOTTOM_BAR_HEIGHT
    
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
        
        # Check animal list clicks (ANIMALS tab only)
        if self.current_tab == 1:
            from animals import get_all_animals
            from collections import defaultdict
            
            animals = get_all_animals()
            content_y = self.y + len(self.TABS) * self.tab_height + 10
            list_start_y = content_y + 20
            
            # Group animals by species
            species_groups = defaultdict(list)
            for animal in animals:
                species_groups[animal.species].append(animal)
            
            # Check clicks on species groups and animals
            current_y = list_start_y - self.animal_scroll
            
            for species_id in sorted(species_groups.keys()):
                animals_in_group = species_groups[species_id]
                is_collapsed = species_id in self.collapsed_species
                
                # Check species header click
                if (self.x <= x <= self.x + self.width and
                    current_y <= y <= current_y + self.species_group_height):
                    # Toggle collapse state
                    if is_collapsed:
                        self.collapsed_species.discard(species_id)
                    else:
                        self.collapsed_species.add(species_id)
                    return True
                
                current_y += self.species_group_height
                
                # Check animal clicks if not collapsed
                if not is_collapsed:
                    for animal in animals_in_group:
                        if (self.x <= x <= self.x + self.width and
                            current_y <= y <= current_y + self.animal_item_height):
                            # Left half = locate, right half = open panel
                            if x < self.x + self.width / 2:
                                # Locate animal
                                if self.on_animal_locate:
                                    self.on_animal_locate(animal.x, animal.y, animal.z)
                            else:
                                # Open detail panel
                                if self.on_animal_click:
                                    self.on_animal_click(animal)
                            return True
                        current_y += self.animal_item_height
                else:
                    # Skip collapsed animals
                    pass
        
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
        # Recalculate height every frame to ensure proper sizing
        self.height = self.screen_height - TOP_BAR_HEIGHT - BOTTOM_BAR_HEIGHT
        
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
            # ANIMALS tab
            from animals import get_all_animals
            from ui_arcade_panels_animals import draw_animals_tab
            animals = get_all_animals()
            draw_animals_tab(self, animals, content_y)
        elif self.current_tab == 2:
            # JOBS tab
            self._draw_jobs_tab(jobs, content_y)
        elif self.current_tab == 3:
            # ITEMS tab - show resources with icons
            self._draw_items_tab(items, content_y)
        elif self.current_tab == 4:
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
    
    def _draw_items_tab(self, items: Dict, content_y: int) -> None:
        """Draw the ITEMS tab content - resources with icons."""
        # Header
        arcade.draw_text(
            text="Resources",
            x=self.x + 10,
            y=content_y,
            color=COLOR_ACCENT_CYAN,
            font_size=11,
            bold=True,
            font_name=UI_FONT
        )
        
        content_y += 25
        
        # Resource order and colors
        resource_order = ["wood", "scrap", "metal", "mineral", "power", "raw_food", "cooked_meal"]
        resource_colors = {
            "wood": (139, 90, 43),
            "scrap": (150, 150, 150),
            "metal": (180, 180, 200),
            "mineral": (100, 150, 200),
            "power": COLOR_ACCENT_CYAN,
            "raw_food": (100, 200, 100),
            "cooked_meal": (255, 180, 100)
        }
        resource_labels = {
            "wood": "Wood",
            "scrap": "Scrap",
            "metal": "Metal",
            "mineral": "Mineral",
            "power": "Power",
            "raw_food": "Raw Food",
            "cooked_meal": "Cooked Meal"
        }
        
        # Draw each resource with icon
        for resource in resource_order:
            amount = items.get(resource, 0)
            accent = resource_colors.get(resource, COLOR_TEXT_BRIGHT)
            label = resource_labels.get(resource, resource)
            
            # Draw icon
            icon_x = self.x + 20
            icon_y = content_y + 10
            self._draw_resource_icon(resource, icon_x, icon_y, accent)
            
            # Draw label
            arcade.draw_text(
                text=label,
                x=self.x + 45,
                y=content_y + 5,
                color=COLOR_TEXT_BRIGHT,
                font_size=11,
                bold=True,
                font_name=UI_FONT
            )
            
            # Draw amount
            arcade.draw_text(
                text=str(amount),
                x=self.x + self.width - 15,
                y=content_y + 5,
                color=accent,
                font_size=11,
                bold=True,
                anchor_x="right",
                font_name=UI_FONT
            )
            
            content_y += 35
    
    def _draw_resource_icon(self, kind: str, cx: float, cy: float, accent: Tuple[int, int, int]) -> None:
        """Draw a resource icon (same as top bar icons)."""
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


