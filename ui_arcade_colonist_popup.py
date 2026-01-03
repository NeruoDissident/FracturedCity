"""
Center popup panel for detailed colonist information.

Dwarf Fortress-style popup with tabs and collapsible equipment tree.
Designed to be reusable for all entities (colonists, animals, robots).
"""

import arcade
from typing import Optional, List, Dict, Tuple, Callable

from ui_arcade import (
    COLOR_BG_PANEL, COLOR_BG_ELEVATED, COLOR_BG_DARK, COLOR_BG_DARKEST,
    COLOR_NEON_CYAN, COLOR_NEON_PINK, COLOR_NEON_MAGENTA, COLOR_NEON_PURPLE,
    COLOR_TEXT_BRIGHT, COLOR_TEXT_NORMAL, COLOR_TEXT_DIM,
    COLOR_BORDER_BRIGHT, COLOR_BORDER_DIM,
    COLOR_GOOD, COLOR_WARNING, COLOR_DANGER,
    UI_FONT, UI_FONT_MONO,
    SCREEN_W, SCREEN_H
)

# Equipment category definitions
EQUIPMENT_CATEGORIES = {
    "head": {
        "name": "HEAD",
        "slots": ["head"],
        "icon_color": (200, 200, 255),
        "description": "Helmets, hats, hoods"
    },
    "eyes": {
        "name": "EYES",
        "slots": ["eyes"],
        "icon_color": (150, 200, 255),
        "description": "Glasses, goggles, eyepatches, monocles"
    },
    "chest": {
        "name": "CHEST",
        "slots": ["chest_layer1", "chest_layer2", "chest_layer3"],
        "layer_names": ["Underwear", "Shirt/Vest", "Jacket/Coat"],
        "icon_color": (255, 200, 150),
        "description": "Layered torso clothing"
    },
    "hands": {
        "name": "HANDS",
        "slots": ["hand_left", "hand_right"],
        "slot_names": ["Left Hand", "Right Hand"],
        "icon_color": (200, 255, 200),
        "description": "Gloves, tools, weapons"
    },
    "waist": {
        "name": "WAIST",
        "slots": ["belt", "pocket_watch", "holster"],
        "slot_names": ["Belt", "Pocket", "Holster"],
        "icon_color": (255, 255, 150),
        "description": "Belts, pouches, holsters"
    },
    "legs": {
        "name": "LEGS",
        "slots": ["legs_layer1", "legs_layer2"],
        "layer_names": ["Underwear", "Pants/Skirt"],
        "icon_color": (200, 150, 255),
        "description": "Layered leg clothing"
    },
    "feet": {
        "name": "FEET",
        "slots": ["feet"],
        "icon_color": (150, 150, 200),
        "description": "Boots, shoes, sandals"
    },
    "accessories": {
        "name": "ACCESSORIES",
        "slots": ["necklace", "earring_left", "earring_right", "ring_left", "ring_right"],
        "slot_names": ["Necklace", "Left Ear", "Right Ear", "Left Ring", "Right Ring"],
        "icon_color": (255, 200, 255),
        "description": "Jewelry, charms, trinkets"
    },
    "implants": {
        "name": "IMPLANTS",
        "slots": ["implant_neural", "implant_ocular", "implant_cardiac"],
        "slot_names": ["Neural", "Ocular", "Cardiac"],
        "icon_color": (100, 255, 255),
        "description": "Cybernetic implants"
    }
}


class ColonistPopup:
    """Center popup panel for detailed colonist information."""
    
    TABS = ["Status", "Equipment", "Bio", "Body", "Links", "Stats", "Drives", "Mind", "Thoughts"]
    
    def __init__(self):
        self.visible = False
        self.colonist = None
        self.colonists_list = []  # For relationship lookups
        self.current_index = 0  # Index in colonists_list
        self.current_tab = 0  # 0=Status, 1=Equipment, 2=Bio, 3=Stats, 4=Thoughts
        
        # Panel dimensions (centered on screen)
        self.panel_width = 700
        self.panel_height = 800
        self.panel_x = (SCREEN_W - self.panel_width) // 2
        self.panel_y = (SCREEN_H - self.panel_height) // 2
        
        # Tab dimensions
        self.tab_height = 40
        self.tab_width = self.panel_width // len(self.TABS)
        
        # Equipment tree state (which categories are expanded)
        self.expanded_categories = set()  # Set of category keys that are expanded
        
        # Scroll state
        self.scroll_offset = 0
        self.max_scroll = 0
        
        # Clickable areas (rebuilt each frame)
        self.close_button_rect = None
        self.tab_rects = []
        self.category_rects = {}  # category_key -> rect
        self.equipment_rects = []  # List of (rect, item, action) tuples
    
    def set_colonists_list(self, colonists: list):
        """Set the colonists list for relationship lookups."""
        self.colonists_list = colonists
        
    def open(self, colonist):
        """Open the popup for a specific colonist."""
        self.visible = True
        self.colonist = colonist
        # Find index in colonists_list
        if colonist in self.colonists_list:
            self.current_index = self.colonists_list.index(colonist)
        else:
            self.current_index = 0
        self.current_tab = 0
        self.scroll_offset = 0
        # Expand all categories by default for now
        self.expanded_categories = set(EQUIPMENT_CATEGORIES.keys())
    
    def next_colonist(self):
        """Switch to next colonist."""
        if self.colonists_list:
            self.current_index = (self.current_index + 1) % len(self.colonists_list)
            self.colonist = self.colonists_list[self.current_index]
            self.scroll_offset = 0
    
    def prev_colonist(self):
        """Switch to previous colonist."""
        if self.colonists_list:
            self.current_index = (self.current_index - 1) % len(self.colonists_list)
            self.colonist = self.colonists_list[self.current_index]
            self.scroll_offset = 0
        
    def close(self):
        """Close the popup."""
        self.visible = False
        self.colonist = None
        
    def handle_click(self, x: int, y: int) -> bool:
        """Handle mouse click. Returns True if consumed."""
        if not self.visible:
            return False
        
        # Check close button
        if self.close_button_rect:
            if (self.close_button_rect[0] <= x <= self.close_button_rect[1] and
                self.close_button_rect[2] <= y <= self.close_button_rect[3]):
                self.close()
                return True
        
        # Check prev/next buttons (before outside panel check)
        btn_y = self.panel_y + self.panel_height - 35
        prev_x = self.panel_x + self.panel_width - 100
        next_x = self.panel_x + self.panel_width - 55
        
        if prev_x <= x <= prev_x + 35 and btn_y <= y <= btn_y + 25:
            self.prev_colonist()
            return True
        
        if next_x <= x <= next_x + 35 and btn_y <= y <= btn_y + 25:
            self.next_colonist()
            return True
        
        # Check if click is outside panel (close on outside click)
        if not (self.panel_x <= x <= self.panel_x + self.panel_width and
                self.panel_y <= y <= self.panel_y + self.panel_height):
            self.close()
            return True
        
        # Check tab clicks
        for i, rect in enumerate(self.tab_rects):
            if rect[0] <= x <= rect[1] and rect[2] <= y <= rect[3]:
                self.current_tab = i
                self.scroll_offset = 0
                return True
        
        # Check equipment category clicks (expand/collapse)
        if self.current_tab == 1:  # Equipment tab
            for category_key, rect in self.category_rects.items():
                if rect[0] <= x <= rect[1] and rect[2] <= y <= rect[3]:
                    # Toggle expansion
                    if category_key in self.expanded_categories:
                        self.expanded_categories.remove(category_key)
                    else:
                        self.expanded_categories.add(category_key)
                    return True
        
        # Check work assignment button clicks (Status tab)
        if self.current_tab == 0 and self.colonist:  # Status tab
            # Check Enable All button
            if hasattr(self, 'enable_all_rect'):
                rect = self.enable_all_rect
                if rect[0] <= x <= rect[1] and rect[2] <= y <= rect[3]:
                    # Enable all job tags
                    for tag_id in ["can_build", "can_haul", "can_craft", "can_cook", "can_scavenge"]:
                        self.colonist.job_tags[tag_id] = True
                    return True
            
            # Check Disable All button
            if hasattr(self, 'disable_all_rect'):
                rect = self.disable_all_rect
                if rect[0] <= x <= rect[1] and rect[2] <= y <= rect[3]:
                    # Disable all job tags
                    for tag_id in ["can_build", "can_haul", "can_craft", "can_cook", "can_scavenge"]:
                        self.colonist.job_tags[tag_id] = False
                    return True
            
            # Check individual job toggle buttons
            if hasattr(self, 'work_button_rects'):
                for rect_data in self.work_button_rects:
                    left, right, bottom, top, tag_id = rect_data
                    if left <= x <= right and bottom <= y <= top:
                        # Toggle this specific job tag
                        self.colonist.job_tags[tag_id] = not self.colonist.job_tags.get(tag_id, True)
                        return True
        
        return True  # Consume all clicks on panel
    
    def handle_scroll(self, x: int, y: int, scroll_y: float) -> bool:
        """Handle mouse wheel scroll. Returns True if consumed."""
        if not self.visible:
            return False
        
        # Check if mouse is over panel
        if not (self.panel_x <= x <= self.panel_x + self.panel_width and
                self.panel_y <= y <= self.panel_y + self.panel_height):
            return False
        
        # Scroll content
        self.scroll_offset -= int(scroll_y * 20)
        self.scroll_offset = max(0, min(self.scroll_offset, self.max_scroll))
        
        return True
    
    def draw(self, mouse_x: int, mouse_y: int):
        """Draw the popup panel."""
        if not self.visible or self.colonist is None:
            return
        
        # Reset clickable areas
        self.tab_rects = []
        self.category_rects = {}
        self.equipment_rects = []
        
        # Draw semi-transparent overlay
        arcade.draw_lrbt_rectangle_filled(
            0, SCREEN_W, 0, SCREEN_H,
            (0, 0, 0, 180)
        )
        
        # Draw panel background
        arcade.draw_lrbt_rectangle_filled(
            self.panel_x, self.panel_x + self.panel_width,
            self.panel_y, self.panel_y + self.panel_height,
            COLOR_BG_PANEL
        )
        arcade.draw_lrbt_rectangle_outline(
            self.panel_x, self.panel_x + self.panel_width,
            self.panel_y, self.panel_y + self.panel_height,
            COLOR_BORDER_BRIGHT, 2
        )
        
        # Draw title bar
        title_height = 50
        arcade.draw_lrbt_rectangle_filled(
            self.panel_x, self.panel_x + self.panel_width,
            self.panel_y + self.panel_height - title_height, self.panel_y + self.panel_height,
            COLOR_BG_ELEVATED
        )
        
        # Draw colonist name
        name = getattr(self.colonist, 'name', 'Unknown')
        arcade.draw_text(
            name.upper(),
            self.panel_x + 20,
            self.panel_y + self.panel_height - 35,
            COLOR_NEON_CYAN,
            font_size=18,
            font_name=UI_FONT,
            bold=True
        )
        
        # Draw colonist counter
        if self.colonists_list:
            counter_text = f"{self.current_index + 1}/{len(self.colonists_list)}"
            arcade.draw_text(
                counter_text,
                self.panel_x + self.panel_width - 150,
                self.panel_y + self.panel_height - 30,
                COLOR_TEXT_DIM,
                font_size=10,
                anchor_x="right",
                font_name=UI_FONT_MONO
            )
        
        # Draw prev/next buttons
        btn_y = self.panel_y + self.panel_height - 35
        prev_x = self.panel_x + self.panel_width - 100
        next_x = self.panel_x + self.panel_width - 55
        
        # Prev button
        arcade.draw_lrbt_rectangle_filled(
            prev_x, prev_x + 35,
            btn_y, btn_y + 25,
            (30, 35, 50)
        )
        arcade.draw_lrbt_rectangle_outline(
            prev_x, prev_x + 35,
            btn_y, btn_y + 25,
            COLOR_NEON_CYAN, 1
        )
        arcade.draw_text(
            "<",
            prev_x + 17, btn_y + 12,
            COLOR_TEXT_BRIGHT,
            font_size=12,
            anchor_x="center", anchor_y="center",
            bold=True
        )
        
        # Next button
        arcade.draw_lrbt_rectangle_filled(
            next_x, next_x + 35,
            btn_y, btn_y + 25,
            (30, 35, 50)
        )
        arcade.draw_lrbt_rectangle_outline(
            next_x, next_x + 35,
            btn_y, btn_y + 25,
            COLOR_NEON_CYAN, 1
        )
        arcade.draw_text(
            ">",
            next_x + 17, btn_y + 12,
            COLOR_TEXT_BRIGHT,
            font_size=12,
            anchor_x="center", anchor_y="center",
            bold=True
        )
        
        # Draw close button
        close_size = 30
        close_x = self.panel_x + self.panel_width - close_size - 10
        close_y = self.panel_y + self.panel_height - close_size - 10
        self.close_button_rect = (close_x, close_x + close_size, close_y, close_y + close_size)
        
        arcade.draw_lrbt_rectangle_filled(
            close_x, close_x + close_size,
            close_y, close_y + close_size,
            COLOR_DANGER
        )
        arcade.draw_text(
            "X",
            close_x + 8,
            close_y + 5,
            COLOR_TEXT_BRIGHT,
            font_size=16,
            font_name=UI_FONT,
            bold=True
        )
        
        # Draw tabs
        tab_y = self.panel_y + self.panel_height - title_height
        for i, tab_name in enumerate(self.TABS):
            tab_x = self.panel_x + i * self.tab_width
            
            # Tab background
            is_active = (i == self.current_tab)
            bg_color = COLOR_NEON_PINK if is_active else COLOR_BG_DARK
            arcade.draw_lrbt_rectangle_filled(
                tab_x, tab_x + self.tab_width,
                tab_y - self.tab_height, tab_y,
                bg_color
            )
            
            # Tab border
            border_color = COLOR_NEON_CYAN if is_active else COLOR_BORDER_DIM
            arcade.draw_lrbt_rectangle_outline(
                tab_x, tab_x + self.tab_width,
                tab_y - self.tab_height, tab_y,
                border_color, 2 if is_active else 1
            )
            
            # Tab text
            text_color = COLOR_TEXT_BRIGHT if is_active else COLOR_TEXT_DIM
            arcade.draw_text(
                tab_name,
                tab_x + self.tab_width // 2,
                tab_y - self.tab_height // 2 - 5,
                text_color,
                font_size=12,
                font_name=UI_FONT,
                anchor_x="center",
                bold=is_active
            )
            
            # Store clickable rect
            self.tab_rects.append((tab_x, tab_x + self.tab_width, tab_y - self.tab_height, tab_y))
        
        # Draw tab content
        content_y = tab_y - self.tab_height - 10
        content_height = content_y - self.panel_y - 10
        
        if self.current_tab == 0:
            self._draw_status_tab(content_y, content_height)
        elif self.current_tab == 1:
            self._draw_equipment_tab(content_y, content_height, mouse_x, mouse_y)
        elif self.current_tab == 2:
            self._draw_bio_tab(content_y, content_height)
        elif self.current_tab == 3:
            self._draw_body_tab(content_y, content_height)
        elif self.current_tab == 4:
            self._draw_links_tab(content_y, content_height)
        elif self.current_tab == 5:
            self._draw_stats_tab(content_y, content_height)
        elif self.current_tab == 6:
            self._draw_drives_tab(content_y, content_height)
        elif self.current_tab == 7:
            self._draw_mind_tab(content_y, content_height)
        elif self.current_tab == 8:
            self._draw_thoughts_tab(content_y, content_height)
    
    def _draw_status_tab(self, start_y: int, height: int):
        """Draw the Status tab with improved layout and visual sections."""
        y = start_y - self.scroll_offset
        col1_x = self.panel_x + 20
        col2_x = self.panel_x + int(self.panel_width * 0.52)
        section_color = (180, 200, 220)
        value_color = (220, 220, 230)
        muted_color = (140, 140, 150)
        separator_color = (60, 70, 80)
        
        # === CURRENT TASK SECTION (Full Width, Prominent) ===
        left_y = y - 15
        
        # Section header with background
        arcade.draw_lrbt_rectangle_filled(
            col1_x - 5, self.panel_x + self.panel_width - 20,
            left_y - 80, left_y + 5,
            (35, 40, 50)
        )
        arcade.draw_lrbt_rectangle_outline(
            col1_x - 5, self.panel_x + self.panel_width - 20,
            left_y - 80, left_y + 5,
            COLOR_NEON_CYAN, 1
        )
        
        arcade.draw_text(text="CURRENT TASK", x=col1_x, y=left_y - 8, color=COLOR_NEON_CYAN, font_size=11, bold=True, font_name=UI_FONT)
        left_y -= 28
        
        # Task details
        state = self.colonist.state
        job_desc = state.replace('_', ' ').title()
        
        if self.colonist.current_job:
            job = self.colonist.current_job
            job_type = job.type.replace('_', ' ').title()
            
            # Build detailed description
            details = []
            if hasattr(job, 'target_x') and hasattr(job, 'target_y'):
                details.append(f"Location: ({job.target_x}, {job.target_y})")
            if hasattr(job, 'resource_type'):
                details.append(f"Resource: {job.resource_type}")
            if hasattr(job, 'building_id'):
                details.append(f"Building: {job.building_id}")
            
            arcade.draw_text(text=f"Action: {job_type}", x=col1_x + 5, y=left_y, color=value_color, font_size=11, font_name=UI_FONT)
            left_y -= 20
            
            for detail in details:
                arcade.draw_text(text=detail, x=col1_x + 5, y=left_y, color=muted_color, font_size=10, font_name=UI_FONT_MONO)
                left_y -= 18
        else:
            arcade.draw_text(text=job_desc, x=col1_x + 5, y=left_y, color=value_color, font_size=11, font_name=UI_FONT)
            left_y -= 20
        
        left_y -= 30
        
        # === VITAL STATS SECTION ===
        arcade.draw_text(text="VITAL STATS", x=col1_x, y=left_y, color=section_color, font_size=12, bold=True, font_name=UI_FONT)
        left_y -= 8
        arcade.draw_line(col1_x, left_y, col1_x + 200, left_y, separator_color, 1)
        left_y -= 18
        
        bar_width = 180
        bar_height = 10
        
        # Hunger
        hunger_val = self.colonist.hunger
        hunger_color = (100, 200, 100) if hunger_val < 50 else (200, 200, 100) if hunger_val < 70 else (200, 100, 100)
        arcade.draw_text(text="Hunger", x=col1_x, y=left_y, color=section_color, font_size=10, font_name=UI_FONT)
        arcade.draw_text(text=f"{int(hunger_val)}%", x=col1_x + 200, y=left_y, color=value_color, font_size=10, font_name=UI_FONT_MONO)
        left_y -= 16
        self._draw_bar(col1_x, left_y, bar_width, bar_height, hunger_val, 100, hunger_color)
        left_y -= 28
        
        # Comfort
        comfort_val = getattr(self.colonist, 'comfort', 0.0)
        comfort_color = (100, 200, 150) if comfort_val > 0 else (200, 150, 100) if comfort_val < 0 else (150, 150, 150)
        comfort_display = (comfort_val + 10) / 20 * 100
        arcade.draw_text(text="Comfort", x=col1_x, y=left_y, color=section_color, font_size=10, font_name=UI_FONT)
        arcade.draw_text(text=f"{comfort_val:+.1f}", x=col1_x + 200, y=left_y, color=value_color, font_size=10, font_name=UI_FONT_MONO)
        left_y -= 16
        self._draw_bar(col1_x, left_y, bar_width, bar_height, comfort_display, 100, comfort_color)
        left_y -= 28
        
        # Stress
        stress_val = getattr(self.colonist, 'stress', 0.0)
        stress_color = (200, 100, 100) if stress_val > 2 else (200, 200, 100) if stress_val > 0 else (100, 150, 200)
        stress_display = (stress_val + 10) / 20 * 100
        arcade.draw_text(text="Stress", x=col1_x, y=left_y, color=section_color, font_size=10, font_name=UI_FONT)
        arcade.draw_text(text=f"{stress_val:+.1f}", x=col1_x + 200, y=left_y, color=value_color, font_size=10, font_name=UI_FONT_MONO)
        left_y -= 16
        self._draw_bar(col1_x, left_y, bar_width, bar_height, stress_display, 100, stress_color)
        left_y -= 35
        
        # === SOCIAL & ROLE SECTION ===
        arcade.draw_text(text="SOCIAL & ROLE", x=col1_x, y=left_y, color=section_color, font_size=12, bold=True, font_name=UI_FONT)
        left_y -= 8
        arcade.draw_line(col1_x, left_y, col1_x + 200, left_y, separator_color, 1)
        left_y -= 18
        
        # Role
        role = getattr(self.colonist, 'role', 'generalist')
        arcade.draw_text(text="Role:", x=col1_x, y=left_y, color=section_color, font_size=10, font_name=UI_FONT)
        arcade.draw_text(text=role.capitalize(), x=col1_x + 50, y=left_y, color=(200, 200, 255), font_size=10, font_name=UI_FONT)
        left_y -= 28
        
        # Needs of the Many
        needs_val = getattr(self.colonist, 'needs_of_the_many', 5)
        if needs_val <= 3:
            needs_color = (255, 100, 100)
        elif needs_val <= 7:
            needs_color = (255, 200, 100)
        else:
            needs_color = (100, 255, 100)
        needs_display = (needs_val / 10.0) * 100
        arcade.draw_text(text="Needs of the Many", x=col1_x, y=left_y, color=section_color, font_size=10, font_name=UI_FONT)
        arcade.draw_text(text=f"{needs_val}/10", x=col1_x + 200, y=left_y, color=value_color, font_size=10, font_name=UI_FONT_MONO)
        left_y -= 16
        self._draw_bar(col1_x, left_y, bar_width, bar_height, needs_display, 100, needs_color)
        left_y -= 35
        
        # === PERSONALITY SECTION ===
        arcade.draw_text(text="PERSONALITY", x=col1_x, y=left_y, color=section_color, font_size=12, bold=True, font_name=UI_FONT)
        left_y -= 8
        arcade.draw_line(col1_x, left_y, col1_x + 200, left_y, separator_color, 1)
        left_y -= 18
        
        # Preferences
        preferences = getattr(self.colonist, 'preferences', {})
        pref_display = {
            "Integrity": preferences.get('likes_integrity', 0.0),
            "Echo": preferences.get('likes_echo', 0.0),
        }
        
        arcade.draw_text(text="Preferences:", x=col1_x, y=left_y, color=section_color, font_size=10, font_name=UI_FONT)
        left_y -= 18
        
        active_prefs = [(name, val) for name, val in pref_display.items() if abs(val) > 0.1]
        if active_prefs:
            for pref_name, pref_val in active_prefs:
                pref_color = (100, 200, 100) if pref_val > 0.5 else (200, 100, 100) if pref_val < -0.5 else (150, 150, 150)
                arcade.draw_text(text=f"  {pref_name}:", x=col1_x, y=left_y, color=muted_color, font_size=10, font_name=UI_FONT)
                arcade.draw_text(text=f"{pref_val:+.1f}", x=col1_x + 100, y=left_y, color=pref_color, font_size=11, font_name=UI_FONT_MONO)
                left_y -= 18
        else:
            arcade.draw_text(text="  None", x=col1_x, y=left_y, color=muted_color, font_size=10, font_name=UI_FONT)
            left_y -= 18
        left_y -= 12
        
        # Personality Drift
        total_drift = getattr(self.colonist, 'last_total_drift', 0.0)
        drift_strongest = getattr(self.colonist, 'last_drift_strongest', ('none', 0.0))
        arcade.draw_text(text="Drift Rate:", x=col1_x, y=left_y, color=section_color, font_size=10, font_name=UI_FONT)
        arcade.draw_text(text=f"{total_drift:.6f}", x=col1_x + 100, y=left_y, color=muted_color, font_size=10, font_name=UI_FONT_MONO)
        left_y -= 18
        
        drift_param, drift_val = drift_strongest
        if abs(drift_val) > 0.000001:
            strongest_text = drift_param
        else:
            strongest_text = "(none)"
        arcade.draw_text(text="Strongest:", x=col1_x, y=left_y, color=section_color, font_size=10, font_name=UI_FONT)
        arcade.draw_text(text=strongest_text, x=col1_x + 100, y=left_y, color=muted_color, font_size=10, font_name=UI_FONT)
        
        # === RIGHT COLUMN ===
        right_y = y - 15
        
        # === CARRYING SECTION ===
        arcade.draw_text(text="CARRYING", x=col2_x, y=right_y, color=section_color, font_size=12, bold=True, font_name=UI_FONT)
        right_y -= 8
        arcade.draw_line(col2_x, right_y, col2_x + 150, right_y, separator_color, 1)
        right_y -= 18
        
        # Get what colonist is carrying
        carrying = getattr(self.colonist, 'carrying', None)
        
        # Draw 2 rows of 3 inventory slots
        for i in range(6):
            row = i // 3
            col = i % 3
            slot_x = col2_x + col * 38
            slot_y = right_y - row * 38
            slot_size = 34
            
            # Draw slot background
            arcade.draw_lrbt_rectangle_filled(slot_x, slot_x + slot_size, slot_y - slot_size, slot_y, (30, 35, 40))
            arcade.draw_lrbt_rectangle_outline(slot_x, slot_x + slot_size, slot_y - slot_size, slot_y, (80, 90, 100), 1)
            
            # Draw carried item in first slot only (colonists carry 1 item at a time)
            if i == 0 and carrying is not None:
                item_type = carrying.get("type", "")
                amount = carrying.get("amount", 1)
                
                # Try to get item name from item data
                item_data = carrying.get("item", {})
                if isinstance(item_data, dict):
                    item_name = item_data.get("name", item_type)
                else:
                    item_name = item_type
                
                # Draw item sprite (reuse stockpile rendering logic)
                center_x = slot_x + slot_size / 2
                center_y = slot_y - slot_size / 2
                
                # Try to load sprite
                sprite_paths = [
                    f"assets/items/{item_type}.png",
                    f"assets/furniture/{item_type}.png",
                ]
                
                texture = None
                for sprite_path in sprite_paths:
                    try:
                        texture = arcade.load_texture(sprite_path)
                        break
                    except:
                        continue
                
                if texture:
                    # Draw sprite
                    sprite_size = slot_size * 0.7
                    arcade.draw_texture_rectangle(
                        center_x, center_y,
                        sprite_size, sprite_size,
                        texture
                    )
                else:
                    # Fallback: colored square matching stockpile colors
                    if "wood" in item_type:
                        color = (139, 90, 43)
                    elif "scrap" in item_type or "metal" in item_type:
                        color = (120, 120, 140)
                    elif "mineral" in item_type:
                        color = (100, 100, 120)
                    elif "food" in item_type or "meal" in item_type:
                        color = (100, 200, 100)
                    else:
                        color = (150, 150, 200)
                    
                    square_size = 16
                    arcade.draw_lrbt_rectangle_filled(
                        center_x - square_size / 2,
                        center_x + square_size / 2,
                        center_y - square_size / 2,
                        center_y + square_size / 2,
                        color
                    )
                
                # Draw amount badge if > 1
                if amount > 1:
                    badge_text = str(amount)
                    badge_x = slot_x + slot_size - 10
                    badge_y = slot_y - slot_size + 5
                    arcade.draw_lrbt_rectangle_filled(
                        badge_x - 8, badge_x + 8,
                        badge_y - 6, badge_y + 6,
                        (0, 0, 0, 200)
                    )
                    arcade.draw_text(
                        badge_text,
                        badge_x, badge_y,
                        (255, 255, 255),
                        font_size=8,
                        anchor_x="center",
                        anchor_y="center",
                        font_name=UI_FONT_MONO
                    )
        
        right_y -= 90
        
        # Draw item details below slots if carrying something
        if carrying is not None:
            item_type = carrying.get("type", "")
            item_data = carrying.get("item", {})
            if isinstance(item_data, dict):
                item_name = item_data.get("name", item_type)
            else:
                item_name = item_type
            
            # Truncate long names
            display_name = item_name[:18] if len(item_name) > 18 else item_name
            arcade.draw_text(
                text=display_name,
                x=col2_x,
                y=right_y,
                color=value_color,
                font_size=11,
                bold=True,
                font_name=UI_FONT
            )
            right_y -= 16
            
            # Show pickup and destination locations if available
            if self.colonist.current_job:
                job = self.colonist.current_job
                
                # Determine descriptive location names
                from zones import is_stockpile_zone
                
                # Pickup location description
                pickup_x, pickup_y, pickup_z = job.x, job.y, job.z
                if is_stockpile_zone(pickup_x, pickup_y, pickup_z):
                    pickup_desc = "stockpile"
                elif job.type == "haul" and job.category == "harvest":
                    pickup_desc = "resource node"
                elif job.type == "haul":
                    pickup_desc = "ground"
                else:
                    pickup_desc = f"({pickup_x}, {pickup_y})"
                
                # Destination location description
                dest_desc = None
                if hasattr(job, 'dest_x') and job.dest_x is not None:
                    dest_x = job.dest_x
                    dest_y = job.dest_y
                    dest_z = job.dest_z if job.dest_z is not None else 0
                    
                    if is_stockpile_zone(dest_x, dest_y, dest_z):
                        dest_desc = "stockpile"
                    elif job.type == "supply":
                        dest_desc = "construction site"
                    elif job.type == "install_furniture":
                        dest_desc = "placement site"
                    else:
                        dest_desc = f"({dest_x}, {dest_y})"
                
                # Draw route description
                if dest_desc:
                    route_text = f"{pickup_desc} → {dest_desc}"
                else:
                    route_text = f"From: {pickup_desc}"
                
                arcade.draw_text(
                    text=route_text,
                    x=col2_x,
                    y=right_y,
                    color=muted_color,
                    font_size=10,
                    font_name=UI_FONT
                )
                right_y -= 16
            
            right_y -= 10
        
        # === MOOD SECTION ===
        arcade.draw_text(text="MOOD", x=col2_x, y=right_y, color=section_color, font_size=12, bold=True, font_name=UI_FONT)
        right_y -= 8
        arcade.draw_line(col2_x, right_y, col2_x + 150, right_y, separator_color, 1)
        right_y -= 18
        
        mood_state = getattr(self.colonist, 'mood_state', 'Focused')
        mood_score = getattr(self.colonist, 'mood_score', 0.0)
        from colonist import Colonist
        mood_color = Colonist.get_mood_color(mood_state)
        
        arcade.draw_text(text=mood_state, x=col2_x, y=right_y, color=mood_color, font_size=11, bold=True, font_name=UI_FONT)
        right_y -= 20
        arcade.draw_text(text=f"Score: {mood_score:+.1f}", x=col2_x, y=right_y, color=muted_color, font_size=11, font_name=UI_FONT_MONO)
        right_y -= 18
        arcade.draw_text(text="(See 'Drives' tab for details)", x=col2_x, y=right_y, color=muted_color, font_size=10, font_name=UI_FONT)
        right_y -= 35
        
        # === WORK ASSIGNMENTS SECTION ===
        arcade.draw_text(text="WORK ASSIGNMENTS", x=col2_x, y=right_y, color=section_color, font_size=12, bold=True, font_name=UI_FONT)
        right_y -= 8
        arcade.draw_line(col2_x, right_y, col2_x + 150, right_y, separator_color, 1)
        right_y -= 15
        
        # Enable All / Disable All buttons
        btn_width = 48
        btn_height = 18
        btn_gap = 4
        
        # Enable All button
        enable_all_x = col2_x
        arcade.draw_lrbt_rectangle_filled(enable_all_x, enable_all_x + btn_width, right_y - btn_height, right_y, (40, 70, 50))
        arcade.draw_lrbt_rectangle_outline(enable_all_x, enable_all_x + btn_width, right_y - btn_height, right_y, (80, 140, 90), 1)
        arcade.draw_text(text="Enable All", x=enable_all_x + btn_width // 2, y=right_y - btn_height // 2, color=(180, 230, 180), font_size=9, anchor_x="center", anchor_y="center", font_name=UI_FONT)
        
        # Disable All button
        disable_all_x = enable_all_x + btn_width + btn_gap
        arcade.draw_lrbt_rectangle_filled(disable_all_x, disable_all_x + btn_width, right_y - btn_height, right_y, (70, 40, 40))
        arcade.draw_lrbt_rectangle_outline(disable_all_x, disable_all_x + btn_width, right_y - btn_height, right_y, (110, 70, 70), 1)
        arcade.draw_text(text="Disable All", x=disable_all_x + btn_width // 2, y=right_y - btn_height // 2, color=(230, 180, 180), font_size=9, anchor_x="center", anchor_y="center", font_name=UI_FONT)
        
        # Store Enable/Disable All button rects
        self.enable_all_rect = (enable_all_x, enable_all_x + btn_width, right_y - btn_height, right_y)
        self.disable_all_rect = (disable_all_x, disable_all_x + btn_width, right_y - btn_height, right_y)
        
        right_y -= btn_height + 10
        
        job_tags = [
            ("can_build", "Build"),
            ("can_haul", "Haul"),
            ("can_craft", "Craft"),
            ("can_cook", "Cook"),
            ("can_scavenge", "Scavenge"),
        ]
        
        # Store button rects for click handling
        if not hasattr(self, 'work_button_rects'):
            self.work_button_rects = []
        self.work_button_rects = []
        
        for tag_id, tag_name in job_tags:
            enabled = self.colonist.job_tags.get(tag_id, True)
            if enabled:
                bg_color = (50, 90, 60)
                text_color = (180, 230, 180)
            else:
                bg_color = (70, 50, 50)
                text_color = (160, 130, 130)
            
            # Draw button
            btn_height = 24
            arcade.draw_lrbt_rectangle_filled(col2_x, col2_x + 100, right_y - btn_height, right_y, bg_color)
            arcade.draw_lrbt_rectangle_outline(col2_x, col2_x + 100, right_y - btn_height, right_y, (80, 140, 90) if enabled else (110, 70, 70), 1)
            arcade.draw_text(text=tag_name, x=col2_x + 50, y=right_y - btn_height // 2, color=text_color, font_size=9, anchor_x="center", anchor_y="center", font_name=UI_FONT)
            
            # Store rect for future click handling
            self.work_button_rects.append((col2_x, col2_x + 100, right_y - btn_height, right_y, tag_id))
            right_y -= btn_height + 8
        
    def _draw_equipment_tab(self, start_y: int, height: int, mouse_x: int, mouse_y: int):
        """Draw the Equipment tab with collapsible categories."""
        y = start_y - self.scroll_offset
        x = self.panel_x + 20
        line_height = 30
        indent = 20
        
        # Get colonist equipment
        equipment = getattr(self.colonist, 'equipment', {})
        
        # Draw each category
        for category_key, category_data in EQUIPMENT_CATEGORIES.items():
            is_expanded = category_key in self.expanded_categories
            
            # Category header
            icon = "▼" if is_expanded else "▶"
            category_name = category_data["name"]
            icon_color = category_data["icon_color"]
            
            # Draw category background (clickable)
            cat_rect = (x, x + self.panel_width - 40, y - line_height, y)
            self.category_rects[category_key] = cat_rect
            
            # Hover effect
            is_hovered = (cat_rect[0] <= mouse_x <= cat_rect[1] and
                         cat_rect[2] <= mouse_y <= cat_rect[3]) if hasattr(self, 'panel_x') else False
            
            if is_hovered:
                arcade.draw_lrbt_rectangle_filled(
                    cat_rect[0], cat_rect[1], cat_rect[2], cat_rect[3],
                    (40, 45, 55)
                )
            
            # Draw expand/collapse icon
            arcade.draw_text(
                icon,
                x, y - 20,
                COLOR_NEON_CYAN,
                font_size=12,
                font_name=UI_FONT
            )
            
            # Draw category name
            arcade.draw_text(
                category_name,
                x + 25, y - 20,
                icon_color,
                font_size=12,
                font_name=UI_FONT,
                bold=True
            )
            
            y -= line_height
            
            # Draw slots if expanded
            if is_expanded:
                slots = category_data["slots"]
                slot_names = category_data.get("slot_names") or category_data.get("layer_names")
                
                for i, slot in enumerate(slots):
                    slot_name = slot_names[i] if slot_names else slot.replace('_', ' ').title()
                    equipped_item = equipment.get(slot)
                    
                    # Draw placeholder icon
                    icon_size = 20
                    icon_x = x + indent
                    icon_y = y - line_height // 2 + 5
                    arcade.draw_lrbt_rectangle_filled(
                        icon_x, icon_x + icon_size,
                        icon_y - icon_size // 2, icon_y + icon_size // 2,
                        icon_color if equipped_item else (60, 60, 70)
                    )
                    arcade.draw_lrbt_rectangle_outline(
                        icon_x, icon_x + icon_size,
                        icon_y - icon_size // 2, icon_y + icon_size // 2,
                        COLOR_BORDER_DIM, 1
                    )
                    
                    # Draw slot name and item
                    if equipped_item:
                        item_name = equipped_item.get('name', 'Unknown Item')
                        arcade.draw_text(
                            f"{item_name} ({slot_name})",
                            icon_x + icon_size + 10,
                            y - 20,
                            COLOR_TEXT_NORMAL,
                            font_size=10,
                            font_name=UI_FONT
                        )
                    else:
                        arcade.draw_text(
                            f"(empty) ({slot_name})",
                            icon_x + icon_size + 10,
                            y - 20,
                            COLOR_TEXT_DIM,
                            font_size=10,
                            font_name=UI_FONT
                        )
                    
                    y -= line_height
                
                # Add spacing after category
                y -= 10
        
        # Calculate max scroll
        content_height = start_y - y
        visible_height = height
        self.max_scroll = max(0, content_height - visible_height)
    
    def _draw_bar(self, x: float, y: float, width: float, height: float, value: float, max_value: float, color: Tuple[int, int, int]):
        """Helper to draw a stat bar."""
        # Background
        arcade.draw_lrbt_rectangle_filled(x, x + width, y - height, y, COLOR_BG_DARK)
        # Fill
        fill_width = (value / max_value) * width
        arcade.draw_lrbt_rectangle_filled(x, x + fill_width, y - height, y, color)
    
    def _draw_bio_tab(self, start_y: int, height: int):
        """Draw the Bio tab - colonist's backstory as flowing prose with colored traits."""
        y = start_y - self.scroll_offset
        col1_x = self.panel_x + 20
        normal_color = (180, 180, 190)
        
        # Header
        arcade.draw_text(
            text="BACKSTORY",
            x=col1_x,
            y=y,
            color=(200, 180, 255),
            font_size=13,
            bold=True,
            font_name=UI_FONT
        )
        y -= 18
        
        # Get cached rich backstory (generated once at colonist creation)
        backstory_segments = getattr(self.colonist, 'rich_backstory', [])
        
        if not backstory_segments:
            arcade.draw_text(
                text="(no backstory)",
                x=col1_x,
                y=y,
                color=COLOR_TEXT_DIM,
                font_size=11,
                font_name=UI_FONT
            )
            return
        
        # Render flowing text with inline colored traits
        max_text_width = self.panel_width - 45
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
                # Estimate word width
                word_width = len(word_with_space) * 6
                
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
                    font_size=11,
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
            font_size=13,
            bold=True,
            font_name=UI_FONT
        )
        y -= 16
        
        from traits import get_trait_labels, TRAIT_COLORS
        traits = getattr(self.colonist, 'traits', {})
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
                font_size=11,
                font_name=UI_FONT
            )
            y -= 14
    
    def _draw_body_tab(self, start_y: int, height: int):
        """Draw the Body tab - detailed body part status like Dwarf Fortress."""
        from body import Body, PartCategory, PartStatus
        
        col1_x = self.panel_x + 20
        
        # Get or create body
        body = getattr(self.colonist, 'body', None)
        if body is None:
            body = Body()
            self.colonist.body = body
        
        y = start_y - self.scroll_offset
        line_h = 11
        col2_x = self.panel_x + int(self.panel_width * 0.5)
        
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
            font_size=13,
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
                font_size=11
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
                font_size=10
            )
        
        # LEFT COLUMN
        left_y = y
        
        # HEAD
        arcade.draw_text(text="HEAD", x=col1_x, y=left_y, color=COLOR_NEON_PINK, font_size=11, bold=True)
        left_y -= 14
        for part_id, part in body.get_parts_by_category(PartCategory.HEAD):
            if not part.is_internal:
                draw_part(part.name, part, col1_x + 4, left_y, part_id)
                left_y -= line_h
        left_y -= 4
        
        # TORSO
        arcade.draw_text(text="TORSO", x=col1_x, y=left_y, color=COLOR_NEON_PINK, font_size=11, bold=True)
        left_y -= 14
        for part_id, part in body.get_parts_by_category(PartCategory.TORSO):
            draw_part(part.name, part, col1_x + 4, left_y, part_id)
            left_y -= line_h
        left_y -= 4
        
        # LEFT ARM
        arcade.draw_text(text="L ARM", x=col1_x, y=left_y, color=COLOR_NEON_PINK, font_size=11, bold=True)
        left_y -= 14
        for part_id, part in body.get_parts_by_category(PartCategory.ARM_LEFT):
            name = part.name.replace("Left ", "")
            draw_part(name, part, col1_x + 4, left_y, part_id)
            left_y -= line_h
        left_y -= 4
        
        # LEFT LEG
        arcade.draw_text(text="L LEG", x=col1_x, y=left_y, color=COLOR_NEON_PINK, font_size=11, bold=True)
        left_y -= 14
        for part_id, part in body.get_parts_by_category(PartCategory.LEG_LEFT):
            name = part.name.replace("Left ", "")
            draw_part(name, part, col1_x + 4, left_y, part_id)
            left_y -= line_h
        
        # RIGHT COLUMN
        right_y = y
        
        # RIGHT ARM
        arcade.draw_text(text="R ARM", x=col2_x, y=right_y, color=COLOR_NEON_PINK, font_size=11, bold=True)
        right_y -= 14
        for part_id, part in body.get_parts_by_category(PartCategory.ARM_RIGHT):
            name = part.name.replace("Right ", "")
            draw_part(name, part, col2_x + 4, right_y, part_id)
            right_y -= line_h
        right_y -= 4
        
        # RIGHT LEG
        arcade.draw_text(text="R LEG", x=col2_x, y=right_y, color=COLOR_NEON_PINK, font_size=11, bold=True)
        right_y -= 14
        for part_id, part in body.get_parts_by_category(PartCategory.LEG_RIGHT):
            name = part.name.replace("Right ", "")
            draw_part(name, part, col2_x + 4, right_y, part_id)
            right_y -= line_h
        
        # BOTTOM SECTION - Combat log
        bottom_y = min(left_y, right_y) - 12
        arcade.draw_text(text="COMBAT LOG", x=col1_x, y=bottom_y, color=(255, 80, 80), font_size=11, bold=True)
        bottom_y -= 14
        
        combat_log = body.get_recent_combat_log(5)
        if combat_log:
            for entry in combat_log:
                arcade.draw_text(
                    text=entry[:50],
                    x=col1_x + 4,
                    y=bottom_y,
                    color=COLOR_TEXT_DIM,
                    font_size=9
                )
                bottom_y -= 10
        else:
            arcade.draw_text(
                text="No injuries recorded",
                x=col1_x + 4,
                y=bottom_y,
                color=COLOR_TEXT_DIM,
                font_size=10
            )
            bottom_y -= 10
        
        bottom_y -= 8
        
        # EFFECTS
        arcade.draw_text(text="EFFECTS", x=col1_x, y=bottom_y, color=(220, 180, 100), font_size=11, bold=True)
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
                        font_size=10
                    )
                    bottom_y -= 10
                    shown += 1
        else:
            arcade.draw_text(
                text="None",
                x=col1_x + 4,
                y=bottom_y,
                color=(50, 255, 120),
                font_size=10
            )
    
    def _draw_links_tab(self, start_y: int, height: int):
        """Draw the Links tab - colonist's relationships with others."""
        from relationships import (get_all_relationships, get_relationship_label, 
                                   get_relationship_color, get_family_bonds, find_colonist_by_id)
        
        col1_x = self.panel_x + 20
        y = start_y - self.scroll_offset
        
        # Age display
        age = getattr(self.colonist, 'age', 25)
        arcade.draw_text(
            text=f"Age: {age}",
            x=col1_x,
            y=y,
            color=(200, 200, 210),
            font_size=12
        )
        y -= 24
        
        # Family section
        arcade.draw_text(
            text="FAMILY",
            x=col1_x,
            y=y,
            color=(200, 180, 255),
            font_size=13,
            bold=True
        )
        y -= 16
        
        # Get colonists list from main game (passed during popup creation)
        colonists = getattr(self, 'colonists_list', [])
        
        family_bonds = get_family_bonds(self.colonist)
        if family_bonds:
            for other_id, bond in family_bonds:
                other = find_colonist_by_id(other_id, colonists)
                if other:
                    bond_name = bond.value.title()
                    other_name = other.name.split()[0]
                    bond_text = f"• {other_name} ({bond_name})"
                    arcade.draw_text(
                        text=bond_text,
                        x=col1_x + 8,
                        y=y,
                        color=(200, 180, 255),
                        font_size=10
                    )
                    y -= 14
        else:
            arcade.draw_text(
                text="(no family in colony)",
                x=col1_x + 8,
                y=y,
                color=COLOR_TEXT_DIM,
                font_size=10
            )
            y -= 14
        
        y -= 10
        
        # Relationships section
        arcade.draw_text(
            text="RELATIONSHIPS",
            x=col1_x,
            y=y,
            color=(180, 200, 220),
            font_size=13,
            bold=True
        )
        y -= 16
        
        relationships = get_all_relationships(self.colonist, colonists)
        
        if not relationships:
            arcade.draw_text(
                text="(no relationships yet)",
                x=col1_x + 8,
                y=y,
                color=COLOR_TEXT_DIM,
                font_size=10
            )
            return
        
        # Show all relationships (sorted by score) with detailed info
        shown = 0
        for other, rel_data in relationships:
            # Check if we're running out of space
            if y < self.panel_y + 100:
                remaining = len(relationships) - shown
                if remaining > 0:
                    arcade.draw_text(
                        text=f"... and {remaining} more",
                        x=col1_x + 8,
                        y=y,
                        color=COLOR_TEXT_DIM,
                        font_size=10
                    )
                break
            
            other_name = other.name.split()[0]
            label = get_relationship_label(self.colonist, other)
            score = rel_data["score"]
            color = get_relationship_color(self.colonist, other)
            
            # Main relationship line: "Name - Label (±score)"
            score_sign = "+" if score >= 0 else ""
            rel_text = f"• {other_name} - {label} ({score_sign}{score})"
            
            arcade.draw_text(
                text=rel_text,
                x=col1_x + 8,
                y=y,
                color=color,
                font_size=10
            )
            y -= 12
            
            # Additional details on second line
            details = []
            interactions = rel_data.get("interactions", 0)
            if interactions > 0:
                details.append(f"{interactions} talks")
            
            if rel_data.get("shared_origin", False):
                details.append("shared origin")
            
            if rel_data.get("shared_experience", False):
                details.append("shared experience")
            
            history = rel_data.get("history", [])
            if history:
                # Show most recent history event
                recent_event = history[-1] if isinstance(history, list) else str(history)
                if isinstance(recent_event, str) and len(recent_event) < 30:
                    details.append(recent_event)
            
            if details:
                detail_text = "    " + ", ".join(details)
                arcade.draw_text(
                    text=detail_text[:55],
                    x=col1_x + 8,
                    y=y,
                    color=(140, 140, 150),
                    font_size=9
                )
                y -= 11
            else:
                y -= 3
            
            shown += 1
    
    def _draw_stats_tab(self, start_y: int, height: int):
        """Draw the Stats tab - D&D style wall of text with all stats."""
        y = start_y - self.scroll_offset
        col1_x = self.panel_x + 20
        muted_color = (140, 140, 150)
        value_color = (220, 220, 230)
        bonus_color = (100, 200, 100)
        penalty_color = (200, 100, 100)
        header_color = (180, 200, 220)
        
        # Get equipment stats
        equip_stats = self.colonist.get_equipment_stats()
        
        # === TRAITS ===
        arcade.draw_text(text="=== TRAITS ===", x=col1_x, y=y, color=(200, 180, 255), font_size=12, bold=True)
        y -= 14
        
        from traits import get_trait_labels
        traits = getattr(self.colonist, 'traits', {})
        trait_labels = get_trait_labels(traits)
        
        for label in trait_labels:
            trait_color = (255, 200, 100) if label.startswith("★") else (180, 200, 220)
            arcade.draw_text(text=label, x=col1_x + 4, y=y, color=trait_color, font_size=10)
            y -= 11
        
        if not trait_labels:
            arcade.draw_text(text="(no traits)", x=col1_x + 4, y=y, color=muted_color, font_size=10)
            y -= 11
        y -= 6
        
        # === MOVEMENT ===
        arcade.draw_text(text="=== MOVEMENT ===", x=col1_x, y=y, color=header_color, font_size=12, bold=True)
        y -= 14
        
        base_move = self.colonist.move_speed
        equip_mod = self.colonist.get_equipment_speed_modifier()
        mood_mod = self.colonist.get_mood_speed_modifier()
        effective_move = base_move * equip_mod * mood_mod
        move_text = f"{effective_move:.1f} ticks"
        if effective_move < base_move:
            move_text += " (FAST)"
        elif effective_move > base_move:
            move_text += " (slow)"
        arcade.draw_text(text=f"Move Delay:      {move_text}", x=col1_x, y=y, color=value_color, font_size=10)
        y -= 11
        
        walk_steady = equip_stats.get("walk_steady", 0)
        steady_text = f"{walk_steady:+.0%}" if walk_steady != 0 else "0%"
        arcade.draw_text(text=f"Walk Steady:     {steady_text}", x=col1_x, y=y, color=value_color, font_size=10)
        y -= 11
        
        haul_cap = self.colonist.get_equipment_haul_capacity()
        haul_text = f"{haul_cap:.0%}"
        arcade.draw_text(text=f"Haul Capacity:   {haul_text}", x=col1_x, y=y, color=value_color, font_size=10)
        y -= 14
        
        # === WORK SPEEDS ===
        arcade.draw_text(text="=== WORK SPEEDS ===", x=col1_x, y=y, color=header_color, font_size=12, bold=True)
        y -= 14
        
        build_mod = self.colonist._calculate_work_modifier("construction")
        build_text = f"{build_mod:.0%}"
        if build_mod > 1.0:
            build_text += " (FAST)"
        elif build_mod < 1.0:
            build_text += " (slow)"
        arcade.draw_text(text=f"Build Speed:     {build_text}", x=col1_x, y=y, color=value_color, font_size=10)
        y -= 11
        
        harvest_mod = self.colonist._calculate_work_modifier("gathering")
        harvest_text = f"{harvest_mod:.0%}"
        if harvest_mod > 1.0:
            harvest_text += " (FAST)"
        elif harvest_mod < 1.0:
            harvest_text += " (slow)"
        arcade.draw_text(text=f"Harvest Speed:   {harvest_text}", x=col1_x, y=y, color=value_color, font_size=10)
        y -= 11
        
        craft_mod = self.colonist._calculate_work_modifier("crafting")
        craft_text = f"{craft_mod:.0%}"
        if craft_mod > 1.0:
            craft_text += " (FAST)"
        elif craft_mod < 1.0:
            craft_text += " (slow)"
        arcade.draw_text(text=f"Craft Speed:     {craft_text}", x=col1_x, y=y, color=value_color, font_size=10)
        y -= 14
        
        # === SURVIVAL ===
        arcade.draw_text(text="=== SURVIVAL ===", x=col1_x, y=y, color=header_color, font_size=12, bold=True)
        y -= 14
        
        hazard = equip_stats.get("hazard_resist", 0)
        arcade.draw_text(text=f"Hazard Resist:   {hazard:.0%}", x=col1_x, y=y, color=value_color, font_size=10)
        y -= 11
        
        warmth = equip_stats.get("warmth", 0)
        arcade.draw_text(text=f"Warmth:          {warmth:+.1f}", x=col1_x, y=y, color=value_color, font_size=10)
        y -= 11
        
        cooling = equip_stats.get("cooling", 0)
        arcade.draw_text(text=f"Cooling:         {cooling:+.1f}", x=col1_x, y=y, color=value_color, font_size=10)
        y -= 14
        
        # === MENTAL ===
        arcade.draw_text(text="=== MENTAL ===", x=col1_x, y=y, color=header_color, font_size=12, bold=True)
        y -= 14
        
        mood_score = getattr(self.colonist, 'mood_score', 0)
        mood_state = getattr(self.colonist, 'mood_state', 'Focused')
        from colonist import Colonist
        mood_color = Colonist.get_mood_color(mood_state)
        arcade.draw_text(text=f"Mood: {mood_state} ({mood_score:+.1f})", x=col1_x, y=y, color=mood_color, font_size=10)
        y -= 11
        
        stress = getattr(self.colonist, 'stress', 0)
        stress_color = (100, 200, 100) if stress < 3 else (200, 200, 100) if stress < 6 else (200, 100, 100)
        arcade.draw_text(text=f"Stress: {stress:.1f}", x=col1_x, y=y, color=stress_color, font_size=10)
        y -= 11
        
        stress_resist = equip_stats.get("stress_resist", 0)
        arcade.draw_text(text=f"Stress Resist:   {stress_resist:.0%}", x=col1_x, y=y, color=value_color, font_size=10)
        y -= 11
        
        comfort = equip_stats.get("comfort", 0)
        arcade.draw_text(text=f"Comfort Bonus:   {comfort:+.2f}", x=col1_x, y=y, color=value_color, font_size=10)
        y -= 14
        
        # === EQUIPMENT BONUSES ===
        arcade.draw_text(text="=== EQUIPMENT BONUSES ===", x=col1_x, y=y, color=(255, 200, 150), font_size=12, bold=True)
        y -= 16
        
        equipment = getattr(self.colonist, 'equipment', {})
        has_any = False
        
        for slot, item_data in equipment.items():
            if item_data is None:
                continue
            has_any = True
            
            item_name = item_data.get("name", slot)
            if len(item_name) > 25:
                item_name = item_name[:22] + "..."
            
            arcade.draw_text(text=f"[{slot.upper()}] {item_name}", x=col1_x, y=y, color=(180, 180, 200), font_size=10)
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
                    arcade.draw_text(text=mod_text, x=col1_x + 8, y=y, color=mod_color, font_size=9)
                    y -= 9
        
        if not has_any:
            arcade.draw_text(text="(no equipment)", x=col1_x, y=y, color=muted_color, font_size=10)
    
    def _draw_drives_tab(self, start_y: int, height: int):
        """Draw the Drives tab - ONLY unmet needs that require action."""
        y = start_y - self.scroll_offset
        col1_x = self.panel_x + 20
        muted_color = (140, 140, 150)
        
        # Collect ONLY unmet needs
        needs = []
        
        # === Bed Need ===
        try:
            from beds import get_colonist_bed
            colonist_id = id(self.colonist)
            bed_pos = get_colonist_bed(colonist_id)
            
            if bed_pos is None:
                needs.append(("Needs: Assigned bed", (200, 100, 100)))
        except Exception:
            pass
        
        # === Sleep Need ===
        tiredness = getattr(self.colonist, 'tiredness', 0.0)
        if tiredness > 60:
            needs.append(("Needs: Sleep", (200, 100, 100)))
        
        # === Social Need ===
        try:
            from relationships import get_all_relationships
            colonists = getattr(self, 'colonists_list', [])
            relationships = get_all_relationships(self.colonist, colonists)
            
            if not relationships:
                needs.append(("Needs: Social interaction", (200, 200, 100)))
        except Exception:
            pass
        
        # === Hunger Need ===
        hunger = getattr(self.colonist, 'hunger', 0.0)
        if hunger > 40:
            needs.append(("Needs: Food", (200, 100, 100)))
        
        # Draw needs list or "All needs met" message
        if needs:
            for need_text, need_color in needs:
                arcade.draw_text(text=f"• {need_text}", x=col1_x + 8, y=y, color=need_color, font_size=11)
                y -= 13
        else:
            # No unmet needs
            arcade.draw_text(text="All needs met", x=col1_x + 8, y=y, color=(100, 200, 100), font_size=11)
    
    def _draw_mind_tab(self, start_y: int, height: int):
        """Draw the Mind tab - colonist's internal monologue."""
        from colonist import THOUGHT_TYPES
        
        y = start_y - self.scroll_offset
        col1_x = self.panel_x + 20
        muted_color = (140, 140, 150)
        header_color = (180, 200, 220)
        
        # Header
        arcade.draw_text(text="Recent Thoughts", x=col1_x, y=y, color=header_color, font_size=13, bold=True)
        y -= 18
        
        # Get recent thoughts
        thoughts = self.colonist.get_recent_thoughts(12)
        
        if not thoughts:
            arcade.draw_text(text="(no thoughts yet)", x=col1_x, y=y, color=muted_color, font_size=10)
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
            arcade.draw_text(text=text[:50], x=col1_x + 14, y=y, color=(200, 200, 210), font_size=10)
            
            # Draw mood effect indicator if significant
            if abs(mood_effect) >= 0.05:
                effect_color = (100, 200, 100) if mood_effect > 0 else (200, 100, 100)
                effect_text = f"+{mood_effect:.1f}" if mood_effect > 0 else f"{mood_effect:.1f}"
                arcade.draw_text(text=effect_text, x=self.panel_x + self.panel_width - 60, y=y, color=effect_color, font_size=10)
            
            y -= 14
            
            if y < self.panel_y + 100:
                arcade.draw_text(text="...", x=col1_x, y=y, color=muted_color, font_size=10)
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
            arcade.draw_text(text=label, x=legend_x + 12, y=y, color=muted_color, font_size=9)
            legend_x += 60
            if legend_x > self.panel_x + self.panel_width - 60:
                legend_x = col1_x
                y -= 12
    
    def _draw_thoughts_tab(self, start_y: int, height: int):
        """Draw the Thoughts tab (Chat) - per-colonist conversation log."""
        from conversations import get_conversation_log
        
        y = start_y - self.scroll_offset
        col1_x = self.panel_x + 20
        muted_color = (140, 140, 150)
        header_color = (180, 200, 220)
        my_color = (200, 150, 255)
        other_color = (150, 255, 200)
        
        # Header
        arcade.draw_text(text="Chat Log", x=col1_x, y=y, color=header_color, font_size=13, bold=True)
        y -= 18
        
        # Get recent conversations
        colonist_key = getattr(self.colonist, "uid", None)
        if colonist_key is None:
            colonist_key = id(self.colonist)
        conversations = get_conversation_log(colonist_key, 15)
        
        if not conversations:
            arcade.draw_text(text="(no conversations yet)", x=col1_x, y=y, color=muted_color, font_size=10)
            return
        
        # Draw each conversation
        colonist_first_name = self.colonist.name.split()[0]
        
        for conv in conversations:
            if y < self.panel_y + 100:
                break
            
            other_name = conv.get("other_name", "???").split()[0]
            my_line = conv.get("my_line", "")
            their_line = conv.get("their_line", "")
            is_speaker = conv.get("is_speaker", True)
            
            # If this colonist spoke first, show their line first
            if is_speaker:
                # My line (purple)
                my_text = f"{colonist_first_name}: \"{my_line}\""
                arcade.draw_text(text=my_text[:60], x=col1_x + 4, y=y, color=my_color, font_size=10)
                y -= 13
                
                if y < self.panel_y + 100:
                    break
                
                # Their response (cyan)
                their_text = f"    {other_name}: \"{their_line}\""
                arcade.draw_text(text=their_text[:60], x=col1_x + 4, y=y, color=other_color, font_size=10)
                y -= 13
            else:
                # They spoke first (cyan)
                their_text = f"{other_name}: \"{their_line}\""
                arcade.draw_text(text=their_text[:60], x=col1_x + 4, y=y, color=other_color, font_size=10)
                y -= 13
                
                if y < self.panel_y + 100:
                    break
                
                # My response (purple)
                my_text = f"    {colonist_first_name}: \"{my_line}\""
                arcade.draw_text(text=my_text[:60], x=col1_x + 4, y=y, color=my_color, font_size=10)
                y -= 13
    
    def _draw_stat_bar(self, x: int, y: int, label: str, value: float, max_value: float, color: Tuple[int, int, int]):
        """Draw a stat bar with label."""
        bar_width = 300
        bar_height = 20
        
        # Label
        arcade.draw_text(
            label,
            x, y,
            COLOR_TEXT_NORMAL,
            font_size=11,
            font_name=UI_FONT
        )
        
        # Bar background
        bar_y = y - bar_height - 5
        arcade.draw_lrbt_rectangle_filled(
            x, x + bar_width,
            bar_y - bar_height // 2, bar_y + bar_height // 2,
            COLOR_BG_DARKEST
        )
        
        # Bar fill
        fill_width = int((value / max_value) * bar_width)
        if fill_width > 0:
            arcade.draw_lrbt_rectangle_filled(
                x, x + fill_width,
                bar_y - bar_height // 2, bar_y + bar_height // 2,
                color
            )
        
        # Bar outline
        arcade.draw_lrbt_rectangle_outline(
            x, x + bar_width,
            bar_y - bar_height // 2, bar_y + bar_height // 2,
            COLOR_BORDER_DIM, 1
        )
        
        # Percentage text
        arcade.draw_text(
            f"{int(value)}%",
            x + bar_width + 10,
            y - bar_height,
            COLOR_TEXT_DIM,
            font_size=10,
            font_name=UI_FONT_MONO
        )


# Singleton instance
_colonist_popup: Optional[ColonistPopup] = None


def get_colonist_popup() -> ColonistPopup:
    """Get or create the colonist popup singleton."""
    global _colonist_popup
    if _colonist_popup is None:
        _colonist_popup = ColonistPopup()
    return _colonist_popup
