"""
Center popup panel for detailed animal information.

Dwarf Fortress-style popup with tabs, reusing colonist popup structure.
Shows animal stats with progressive reveal based on tame level.
"""

import arcade
from typing import Optional, List, Tuple

from ui_arcade import (
    COLOR_BG_PANEL, COLOR_BG_ELEVATED, COLOR_BG_DARK, COLOR_BG_DARKEST,
    COLOR_NEON_CYAN, COLOR_NEON_PINK, COLOR_NEON_MAGENTA, COLOR_NEON_PURPLE,
    COLOR_TEXT_BRIGHT, COLOR_TEXT_NORMAL, COLOR_TEXT_DIM,
    COLOR_BORDER_BRIGHT, COLOR_BORDER_DIM,
    COLOR_GOOD, COLOR_WARNING, COLOR_DANGER,
    UI_FONT, UI_FONT_MONO,
    SCREEN_W, SCREEN_H
)


class AnimalPopup:
    """Center popup panel for detailed animal information."""
    
    TABS = ["Status", "Bio", "Body", "Links", "Stats", "Jobs", "Drives", "Mind", "Products", "Pen"]
    
    def __init__(self):
        self.visible = False
        self.is_embedded = False  # New flag for embedded mode
        self.animals = []
        self.current_index = 0
        self.current_tab = 0
        
        # Panel dimensions (centered on screen)
        self.panel_width = 700
        self.panel_height = 800
        self.panel_x = (SCREEN_W - self.panel_width) // 2
        self.panel_y = (SCREEN_H - self.panel_height) // 2
        
        # Tab dimensions
        self.tab_height = 40
        self.tab_width = self.panel_width // len(self.TABS)
        
        # Scroll state
        self.scroll_offset = 0
        self.max_scroll = 0
        
        # Clickable areas (rebuilt each frame)
        self.close_button_rect = None
        self.tab_rects = []
        self.hunt_button_rect = None
        
    def open(self, animals: List, animal_index: int = 0):
        """Open the popup for a specific animal."""
        self.visible = True
        self.animals = animals
        self.current_index = animal_index
        
        # Only reset tab if not embedded
        if not self.is_embedded:
            self.current_tab = 0
            self.scroll_offset = 0
        
    def close(self):
        """Close the popup."""
        self.visible = False
        self.animals = []
        
    def next_animal(self):
        """Switch to next animal."""
        if self.animals:
            self.current_index = (self.current_index + 1) % len(self.animals)
    
    def prev_animal(self):
        """Switch to previous animal."""
        if self.animals:
            self.current_index = (self.current_index - 1) % len(self.animals)
    
    def handle_click(self, x: int, y: int) -> bool:
        """Handle mouse click. Returns True if consumed."""
        if not self.visible:
            return False
        
        # === Window Chrome Interactions (Only if not embedded) ===
        if not self.is_embedded:
            # Check if click is outside panel - close popup
            if not (self.panel_x <= x <= self.panel_x + self.panel_width and
                    self.panel_y <= y <= self.panel_y + self.panel_height):
                self.close()
                return True  # Consume the click to prevent world interaction
            
            # Check close button
            if self.close_button_rect:
                left, right, bottom, top = self.close_button_rect
                if left <= x <= right and bottom <= y <= top:
                    self.close()
                    return True
            
            # Check prev/next buttons
            btn_y = self.panel_y + self.panel_height - 35
            prev_x = self.panel_x + self.panel_width - 100
            next_x = self.panel_x + self.panel_width - 55
            
            if prev_x <= x <= prev_x + 35 and btn_y <= y <= btn_y + 25:
                self.prev_animal()
                return True
            
            if next_x <= x <= next_x + 35 and btn_y <= y <= btn_y + 25:
                self.next_animal()
                return True
        else:
            # Embedded mode: Bounds check is handled by parent, but we double check
            if not (self.panel_x <= x <= self.panel_x + self.panel_width and
                    self.panel_y <= y <= self.panel_y + self.panel_height):
                return False
        
        # === Content Interactions ===
        
        # Check tabs
        for i, rect in enumerate(self.tab_rects):
            left, right, bottom, top = rect
            if left <= x <= right and bottom <= y <= top:
                self.current_tab = i
                return True
        
        # Check hunt button (Status tab only)
        if self.current_tab == 0 and self.hunt_button_rect:
            left, right, bottom, top = self.hunt_button_rect
            if left <= x <= right and bottom <= y <= top:
                animal = self.animals[self.current_index]
                from animals import mark_for_hunt, unmark_for_hunt
                
                if animal.marked_for_hunt:
                    unmark_for_hunt(animal)
                else:
                    mark_for_hunt(animal)
                
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
        
    def draw_embedded(self, x: int, y: int, width: int, height: int, mouse_x: int, mouse_y: int):
        """Draw the panel embedded within another view (e.g. Dashboard).
        
        Args:
            x, y, width, height: Geometry to draw into (y is bottom)
            mouse_x, mouse_y: Current mouse position for hover effects
        """
        self.is_embedded = True
        self.visible = True
        
        # Update geometry
        self.panel_x = x
        self.panel_y = y
        self.panel_width = width
        self.panel_height = height
        
        # Recalculate tab width for new size
        self.tab_width = self.panel_width // len(self.TABS)
        
        # Draw content (skipping overlay and frame)
        self._draw_content(mouse_x, mouse_y)
    
    def draw(self, mouse_x: int, mouse_y: int):
        """Draw the popup panel as a standalone modal."""
        if not self.visible or not self.animals:
            return
            
        self.is_embedded = False
        
        if self.current_index >= len(self.animals):
            self.current_index = 0
        
        animal = self.animals[self.current_index]
        
        # Close panel if viewing a dead animal
        if not animal.is_alive():
            self.visible = False
            return
        
        # Reset clickable areas
        self.tab_rects = []
        self.hunt_button_rect = None
        
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
            COLOR_NEON_MAGENTA, 2
        )
        
        # Draw Window Chrome
        self._draw_chrome(animal)
        
        # Draw Content
        self._draw_content(mouse_x, mouse_y)

    def _draw_chrome(self, animal):
        """Draw window chrome (Title bar, close button, nav buttons)."""
        # Draw title bar
        title_height = 50
        arcade.draw_lrbt_rectangle_filled(
            self.panel_x, self.panel_x + self.panel_width,
            self.panel_y + self.panel_height - title_height, self.panel_y + self.panel_height,
            COLOR_BG_ELEVATED
        )
        
        # Draw animal name/species
        species_name = animal.species_data["name"]
        variant_text = f"#{animal.variant}"
        arcade.draw_text(
            f"{species_name} {variant_text}".upper(),
            self.panel_x + 20,
            self.panel_y + self.panel_height - 35,
            COLOR_NEON_MAGENTA,
            font_size=18,
            font_name=UI_FONT,
            bold=True
        )
        
        # Draw animal counter
        counter_text = f"{self.current_index + 1}/{len(self.animals)}"
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
            COLOR_NEON_MAGENTA, 1
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
            COLOR_NEON_MAGENTA, 1
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

    def _draw_content(self, mouse_x, mouse_y):
        """Draw the main content (Tabs + Tab Content)."""
        if not self.animals:
            return
            
        if self.current_index >= len(self.animals):
            self.current_index = 0
        
        animal = self.animals[self.current_index]
        
        # Reset clickable areas
        self.tab_rects = []
        self.hunt_button_rect = None
        
        # Adjust layout based on mode
        if self.is_embedded:
            # Embedded: Tabs start at top of panel
            title_height = 0 
            top_y = self.panel_y + self.panel_height
        else:
            # Standalone: Tabs start below title bar
            title_height = 50
            top_y = self.panel_y + self.panel_height - title_height

        # Draw tabs
        tab_y = top_y
        for i, tab_name in enumerate(self.TABS):
            tab_x = self.panel_x + i * self.tab_width
            
            # Tab background
            is_active = (i == self.current_tab)
            bg_color = COLOR_NEON_MAGENTA if is_active else COLOR_BG_DARK
            arcade.draw_lrbt_rectangle_filled(
                tab_x, tab_x + self.tab_width,
                tab_y - self.tab_height, tab_y,
                bg_color
            )
            
            # Tab border
            border_color = COLOR_NEON_PINK if is_active else COLOR_BORDER_DIM
            arcade.draw_lrbt_rectangle_outline(
                tab_x, tab_x + self.tab_width,
                tab_y - self.tab_height, tab_y,
                border_color, 2 if is_active else 1
            )
            
            # Tab text
            text_color = COLOR_TEXT_BRIGHT if is_active else COLOR_TEXT_DIM
            # Font size adjustments for narrow tabs in embedded mode
            font_size = 10 if self.is_embedded and self.tab_width < 60 else 12
            
            arcade.draw_text(
                tab_name[:3] if self.is_embedded and self.tab_width < 40 else tab_name,
                tab_x + self.tab_width // 2,
                tab_y - self.tab_height // 2 - 5,
                text_color,
                font_size=font_size,
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
            self._draw_status_tab(animal, content_y, content_height)
        elif self.current_tab == 1:
            self._draw_bio_tab(animal, content_y, content_height)
        elif self.current_tab == 2:
            self._draw_body_tab(animal, content_y, content_height)
        elif self.current_tab == 3:
            self._draw_links_tab(animal, content_y, content_height)
        elif self.current_tab == 4:
            self._draw_stats_tab(animal, content_y, content_height)
        elif self.current_tab == 5:
            self._draw_jobs_tab(animal, content_y, content_height)
        elif self.current_tab == 6:
            self._draw_drives_tab(animal, content_y, content_height)
        elif self.current_tab == 7:
            self._draw_mind_tab(animal, content_y, content_height)
        elif self.current_tab == 8:
            self._draw_products_tab(animal, content_y, content_height)
        elif self.current_tab == 9:
            self._draw_pen_tab(animal, content_y, content_height)
    
    def _get_tame_tier(self, tame_progress: int) -> int:
        """Get information tier based on tame progress."""
        if tame_progress >= 100:
            return 4
        elif tame_progress >= 75:
            return 3
        elif tame_progress >= 50:
            return 2
        elif tame_progress >= 25:
            return 1
        else:
            return 0
    
    def _draw_locked_stat(self, x: int, y: int, label: str, required_tier: int, current_tier: int) -> int:
        """Draw a locked stat with tier requirement. Returns Y offset used."""
        is_locked = current_tier < required_tier
        
        if is_locked:
            arcade.draw_text(
                f"{label}:",
                x, y,
                COLOR_TEXT_DIM,
                font_size=9,
                font_name=UI_FONT
            )
            arcade.draw_text(
                "???",
                x + 100, y,
                (80, 80, 100),
                font_size=9,
                font_name=UI_FONT_MONO
            )
            arcade.draw_text(
                "🔒",
                x + 140, y,
                (100, 100, 120),
                font_size=8
            )
            return 18
        
        return 0
    
    def _draw_status_tab(self, animal, start_y: int, height: int):
        """Draw Status tab - core animal state."""
        y = start_y - self.scroll_offset
        content_x = self.panel_x + 20
        tier = self._get_tame_tier(animal.tame_progress)
        
        # === HUNT BUTTON (Top right) ===
        button_width = 120
        button_height = 30
        button_x = self.panel_x + self.panel_width - button_width - 30
        button_y = y
        
        is_marked = animal.marked_for_hunt
        button_color = COLOR_DANGER if is_marked else COLOR_NEON_MAGENTA
        button_text = "Cancel Hunt" if is_marked else "Hunt"
        
        arcade.draw_lrbt_rectangle_filled(
            button_x, button_x + button_width,
            button_y - button_height, button_y,
            button_color
        )
        arcade.draw_lrbt_rectangle_outline(
            button_x, button_x + button_width,
            button_y - button_height, button_y,
            COLOR_BORDER_BRIGHT, 2
        )
        arcade.draw_text(
            button_text,
            button_x + button_width / 2,
            button_y - button_height / 2 - 4,
            COLOR_TEXT_BRIGHT,
            font_size=10,
            anchor_x="center",
            anchor_y="center",
            font_name=UI_FONT,
            bold=True
        )
        
        # Store button bounds for click detection
        self.hunt_button_rect = (button_x, button_x + button_width, button_y - button_height, button_y)
        
        y -= 45
        
        # === TAME PROGRESS BAR ===
        arcade.draw_text(
            "TAME PROGRESS",
            content_x, y,
            COLOR_NEON_MAGENTA,
            font_size=10,
            bold=True,
            font_name=UI_FONT
        )
        y -= 25
        
        bar_width = self.panel_width - 60
        bar_height = 20
        bar_x = content_x + 5
        
        # Background
        arcade.draw_lrbt_rectangle_filled(
            bar_x, bar_x + bar_width,
            y, y + bar_height,
            (20, 20, 30)
        )
        
        # Fill based on tame progress
        fill_width = (animal.tame_progress / 100.0) * bar_width
        if animal.tame_progress < 25:
            fill_color = (255, 80, 80)
        elif animal.tame_progress < 50:
            fill_color = (255, 180, 80)
        elif animal.tame_progress < 75:
            fill_color = (255, 255, 80)
        elif animal.tame_progress < 100:
            fill_color = (150, 255, 150)
        else:
            fill_color = (0, 255, 150)
        
        arcade.draw_lrbt_rectangle_filled(
            bar_x, bar_x + fill_width,
            y, y + bar_height,
            fill_color
        )
        
        # Border
        arcade.draw_lrbt_rectangle_outline(
            bar_x, bar_x + bar_width,
            y, y + bar_height,
            COLOR_BORDER_BRIGHT, 1
        )
        
        # Percentage text
        arcade.draw_text(
            f"{animal.tame_progress}%",
            bar_x + bar_width / 2, y + bar_height / 2,
            COLOR_TEXT_BRIGHT,
            font_size=10,
            bold=True,
            anchor_x="center",
            anchor_y="center",
            font_name=UI_FONT_MONO
        )
        
        y -= 35
        
        # === STATE ===
        state_text = animal.state.value.replace("_", " ").title()
        state_color = self._get_state_color(animal.state.value)
        
        arcade.draw_text(
            "State:",
            content_x, y,
            COLOR_TEXT_NORMAL,
            font_size=9,
            font_name=UI_FONT
        )
        arcade.draw_text(
            state_text,
            content_x + 100, y,
            state_color,
            font_size=9,
            bold=True,
            font_name=UI_FONT
        )
        y -= 20
        
        # === LOCATION ===
        arcade.draw_text(
            "Location:",
            content_x, y,
            COLOR_TEXT_NORMAL,
            font_size=9,
            font_name=UI_FONT
        )
        arcade.draw_text(
            f"({animal.x}, {animal.y}, Z{animal.z})",
            content_x + 100, y,
            COLOR_NEON_CYAN,
            font_size=9,
            font_name=UI_FONT_MONO
        )
        y -= 25
        
        # === TIER 1+ STATS (25%+) ===
        if tier >= 1:
            # Health
            arcade.draw_text(
                "Health:",
                content_x, y,
                COLOR_TEXT_NORMAL,
                font_size=9,
                font_name=UI_FONT
            )
            health_pct = (animal.health / animal.species_data["health"]) * 100
            health_color = COLOR_GOOD if health_pct > 75 else (COLOR_WARNING if health_pct > 25 else COLOR_DANGER)
            arcade.draw_text(
                f"{animal.health}/{animal.species_data['health']} ({int(health_pct)}%)",
                content_x + 100, y,
                health_color,
                font_size=9,
                font_name=UI_FONT_MONO
            )
            y -= 18
            
            # Hunger
            arcade.draw_text(
                "Hunger:",
                content_x, y,
                COLOR_TEXT_NORMAL,
                font_size=9,
                font_name=UI_FONT
            )
            hunger_color = COLOR_GOOD if animal.hunger < 25 else (COLOR_WARNING if animal.hunger < 75 else COLOR_DANGER)
            arcade.draw_text(
                f"{animal.hunger}/100",
                content_x + 100, y,
                hunger_color,
                font_size=9,
                font_name=UI_FONT_MONO
            )
            y -= 18
            
            # Age
            arcade.draw_text(
                "Age:",
                content_x, y,
                COLOR_TEXT_NORMAL,
                font_size=9,
                font_name=UI_FONT
            )
            arcade.draw_text(
                f"{animal.age} days",
                content_x + 100, y,
                COLOR_TEXT_BRIGHT,
                font_size=9,
                font_name=UI_FONT_MONO
            )
            y -= 25
        else:
            offset = self._draw_locked_stat(content_x, y, "Health", 1, tier)
            if offset: y -= offset
            offset = self._draw_locked_stat(content_x, y, "Hunger", 1, tier)
            if offset: y -= offset
            offset = self._draw_locked_stat(content_x, y, "Age", 1, tier)
            if offset: y -= 25
        
        # === TIER 2+ STATS (50%+) ===
        if tier >= 2:
            arcade.draw_text(
                "BEHAVIOR",
                content_x, y,
                COLOR_NEON_MAGENTA,
                font_size=10,
                bold=True,
                font_name=UI_FONT
            )
            y -= 20
            
            # Aggression
            arcade.draw_text(
                "Aggression:",
                content_x, y,
                COLOR_TEXT_NORMAL,
                font_size=9,
                font_name=UI_FONT
            )
            aggro_pct = int(animal.species_data["aggression"] * 100)
            aggro_color = COLOR_DANGER if aggro_pct > 50 else (COLOR_WARNING if aggro_pct > 20 else COLOR_GOOD)
            arcade.draw_text(
                f"{aggro_pct}%",
                content_x + 100, y,
                aggro_color,
                font_size=9,
                font_name=UI_FONT_MONO
            )
            y -= 18
            
            # Flee distance
            arcade.draw_text(
                "Flee Range:",
                content_x, y,
                COLOR_TEXT_NORMAL,
                font_size=9,
                font_name=UI_FONT
            )
            arcade.draw_text(
                f"{animal.species_data['flee_distance']} tiles",
                content_x + 100, y,
                COLOR_TEXT_BRIGHT,
                font_size=9,
                font_name=UI_FONT_MONO
            )
            y -= 25
        else:
            offset = self._draw_locked_stat(content_x, y, "Behavior", 2, tier)
            if offset: y -= 25
        
        # === TIER 4 STATS (100% - Fully Tamed) ===
        if tier >= 4:
            arcade.draw_text(
                "OWNERSHIP",
                content_x, y,
                COLOR_NEON_MAGENTA,
                font_size=10,
                bold=True,
                font_name=UI_FONT
            )
            y -= 20
            
            if animal.owner:
                arcade.draw_text(
                    "Owner:",
                    content_x, y,
                    COLOR_TEXT_NORMAL,
                    font_size=9,
                    font_name=UI_FONT
                )
                arcade.draw_text(
                    f"Colonist #{animal.owner}",
                    content_x + 100, y,
                    COLOR_NEON_CYAN,
                    font_size=9,
                    font_name=UI_FONT
                )
            else:
                arcade.draw_text(
                    "Owner: None (Colony Animal)",
                    content_x, y,
                    COLOR_TEXT_DIM,
                    font_size=9,
                    font_name=UI_FONT
                )
    
    def _draw_bio_tab(self, animal, start_y: int, height: int):
        """Draw Bio tab - species info and lore."""
        y = start_y - self.scroll_offset
        content_x = self.panel_x + 20
        tier = self._get_tame_tier(animal.tame_progress)
        
        # Species name
        arcade.draw_text(
            animal.species_data["name"].upper(),
            content_x, y,
            COLOR_NEON_MAGENTA,
            font_size=12,
            bold=True,
            font_name=UI_FONT
        )
        y -= 25
        
        # Basic species info
        arcade.draw_text(
            f"Variant: {animal.variant}",
            content_x, y,
            COLOR_TEXT_NORMAL,
            font_size=9,
            font_name=UI_FONT
        )
        y -= 18
        
        arcade.draw_text(
            f"Size: {animal.species_data['size']} tile(s)",
            content_x, y,
            COLOR_TEXT_NORMAL,
            font_size=9,
            font_name=UI_FONT
        )
        y -= 18
        
        arcade.draw_text(
            f"Speed: {animal.species_data['speed']}x",
            content_x, y,
            COLOR_TEXT_NORMAL,
            font_size=9,
            font_name=UI_FONT
        )
        y -= 30
        
        # Habitat info (tier 1+)
        if tier >= 1:
            arcade.draw_text(
                "HABITAT",
                content_x, y,
                COLOR_NEON_MAGENTA,
                font_size=10,
                bold=True,
                font_name=UI_FONT
            )
            y -= 20
            
            z_levels = ", ".join([f"Z{z}" for z in animal.species_data["z_levels"]])
            arcade.draw_text(
                f"Levels: {z_levels}",
                content_x, y,
                COLOR_TEXT_NORMAL,
                font_size=9,
                font_name=UI_FONT
            )
            y -= 18
            
            locations = ", ".join(animal.species_data["spawn_locations"])
            arcade.draw_text(
                f"Found in: {locations}",
                content_x, y,
                COLOR_TEXT_NORMAL,
                font_size=9,
                font_name=UI_FONT
            )
            y -= 30
        
        # Yields (tier 2+)
        if tier >= 2:
            arcade.draw_text(
                "YIELDS",
                content_x, y,
                COLOR_NEON_MAGENTA,
                font_size=10,
                bold=True,
                font_name=UI_FONT
            )
            y -= 20
            
            min_meat, max_meat = animal.species_data["meat_yield"]
            arcade.draw_text(
                f"Meat: {min_meat}-{max_meat}",
                content_x, y,
                (255, 180, 100),
                font_size=9,
                font_name=UI_FONT
            )
            y -= 18
            
            for material, (min_amt, max_amt) in animal.species_data["materials"].items():
                arcade.draw_text(
                    f"{material.replace('_', ' ').title()}: {min_amt}-{max_amt}",
                    content_x, y,
                    (150, 200, 255),
                    font_size=9,
                    font_name=UI_FONT
                )
                y -= 18
    
    def _draw_stats_tab(self, animal, start_y: int, height: int):
        """Draw Stats tab - detailed statistics."""
        y = start_y - self.scroll_offset
        content_x = self.panel_x + 20
        tier = self._get_tame_tier(animal.tame_progress)
        
        arcade.draw_text(
            "STATISTICS",
            content_x, y,
            COLOR_NEON_MAGENTA,
            font_size=11,
            bold=True,
            font_name=UI_FONT
        )
        y -= 25
        
        if tier >= 1:
            stats = [
                ("Max Health", f"{animal.species_data['health']} HP"),
                ("Current Health", f"{animal.health} HP"),
                ("Speed", f"{animal.species_data['speed']}x"),
                ("Aggression", f"{int(animal.species_data['aggression'] * 100)}%"),
                ("Flee Distance", f"{animal.species_data['flee_distance']} tiles"),
                ("Tame Difficulty", f"{animal.species_data['tame_difficulty']}/100"),
            ]
            
            for label, value in stats:
                arcade.draw_text(
                    f"{label}:",
                    content_x, y,
                    COLOR_TEXT_NORMAL,
                    font_size=9,
                    font_name=UI_FONT
                )
                arcade.draw_text(
                    value,
                    content_x + 120, y,
                    COLOR_TEXT_BRIGHT,
                    font_size=9,
                    font_name=UI_FONT_MONO
                )
                y -= 18
        else:
            arcade.draw_text(
                "Tame this animal to unlock statistics.",
                content_x, y,
                COLOR_TEXT_DIM,
                font_size=9,
                font_name=UI_FONT
            )
    
    def _draw_products_tab(self, animal, start_y: int, height: int):
        """Draw Products tab - eggs, milk, etc."""
        y = start_y - self.scroll_offset
        content_x = self.panel_x + 20
        tier = self._get_tame_tier(animal.tame_progress)
        
        arcade.draw_text(
            "PRODUCTS",
            content_x, y,
            COLOR_NEON_MAGENTA,
            font_size=11,
            bold=True,
            font_name=UI_FONT
        )
        y -= 25
        
        if tier >= 3:
            if animal.can_lay_eggs:
                arcade.draw_text(
                    "Eggs: Yes",
                    content_x, y,
                    COLOR_GOOD,
                    font_size=9,
                    font_name=UI_FONT
                )
                y -= 18
            else:
                arcade.draw_text(
                    "Eggs: No",
                    content_x, y,
                    COLOR_TEXT_DIM,
                    font_size=9,
                    font_name=UI_FONT
                )
                y -= 18
            
            arcade.draw_text(
                "Other products: None",
                content_x, y,
                COLOR_TEXT_DIM,
                font_size=9,
                font_name=UI_FONT
            )
        else:
            arcade.draw_text(
                "Tame to 75% to unlock product information.",
                content_x, y,
                COLOR_TEXT_DIM,
                font_size=9,
                font_name=UI_FONT
            )
    
    def _draw_pen_tab(self, animal, start_y: int, height: int):
        """Draw Pen tab - housing preferences."""
        y = start_y - self.scroll_offset
        content_x = self.panel_x + 20
        tier = self._get_tame_tier(animal.tame_progress)
        
        arcade.draw_text(
            "PEN REQUIREMENTS",
            content_x, y,
            COLOR_NEON_MAGENTA,
            font_size=11,
            bold=True,
            font_name=UI_FONT
        )
        y -= 25
        
        if tier >= 3:
            if animal.pen_location:
                px, py, pz = animal.pen_location
                arcade.draw_text(
                    f"Assigned Pen: ({px}, {py}, Z{pz})",
                    content_x, y,
                    COLOR_GOOD,
                    font_size=9,
                    font_name=UI_FONT
                )
            else:
                arcade.draw_text(
                    "Assigned Pen: None",
                    content_x, y,
                    COLOR_WARNING,
                    font_size=9,
                    font_name=UI_FONT
                )
            y -= 25
            
            arcade.draw_text(
                "Pen preferences will be shown here.",
                content_x, y,
                COLOR_TEXT_DIM,
                font_size=9,
                font_name=UI_FONT
            )
        else:
            arcade.draw_text(
                "Tame to 75% to unlock pen information.",
                content_x, y,
                COLOR_TEXT_DIM,
                font_size=9,
                font_name=UI_FONT
            )
    
    def _draw_body_tab(self, animal, start_y: int, height: int):
        """Draw Body tab - body parts and injuries."""
        y = start_y - self.scroll_offset
        content_x = self.panel_x + 20
        tier = self._get_tame_tier(animal.tame_progress)
        
        if tier >= 2:  # 50%+ tamed
            from body import PartCategory
            
            arcade.draw_text(
                "BODY PARTS",
                content_x, y,
                COLOR_NEON_MAGENTA,
                font_size=11,
                bold=True,
                font_name=UI_FONT
            )
            y -= 25
            
            # Group by category
            for category in PartCategory:
                parts = animal.body.get_parts_by_category(category)
                if not parts:
                    continue
                
                # Category header
                arcade.draw_text(
                    category.value.replace("_", " ").title(),
                    content_x, y,
                    COLOR_TEXT_BRIGHT,
                    font_size=10,
                    bold=True,
                    font_name=UI_FONT
                )
                y -= 20
                
                # List parts
                for part_id, part in parts:
                    condition = part.get_condition_text()
                    color = part.get_color()
                    
                    arcade.draw_text(
                        f"{part.name}: {condition}",
                        content_x + 10, y,
                        color,
                        font_size=9,
                        font_name=UI_FONT
                    )
                    y -= 16
                
                y -= 10
        else:
            arcade.draw_text(
                "Tame to 50% to unlock body information.",
                content_x, y,
                COLOR_TEXT_DIM,
                font_size=9,
                font_name=UI_FONT
            )
    
    def _draw_links_tab(self, animal, start_y: int, height: int):
        """Draw Links tab - relationships."""
        y = start_y - self.scroll_offset
        content_x = self.panel_x + 20
        tier = self._get_tame_tier(animal.tame_progress)
        
        arcade.draw_text(
            "RELATIONSHIPS",
            content_x, y,
            COLOR_NEON_MAGENTA,
            font_size=11,
            bold=True,
            font_name=UI_FONT
        )
        y -= 25
        
        if tier >= 3:  # 75%+ tamed
            if animal.relationships:
                for entity_uid, rel_data in animal.relationships.items():
                    arcade.draw_text(
                        f"Entity #{entity_uid}: {rel_data.get('type', 'Unknown')}",
                        content_x, y,
                        COLOR_TEXT_NORMAL,
                        font_size=9,
                        font_name=UI_FONT
                    )
                    y -= 16
            else:
                arcade.draw_text(
                    "No relationships yet.",
                    content_x, y,
                    COLOR_TEXT_DIM,
                    font_size=9,
                    font_name=UI_FONT
                )
        else:
            arcade.draw_text(
                "Tame to 75% to unlock relationship information.",
                content_x, y,
                COLOR_TEXT_DIM,
                font_size=9,
                font_name=UI_FONT
            )
    
    def _draw_jobs_tab(self, animal, start_y: int, height: int):
        """Draw Jobs tab - work assignments."""
        y = start_y - self.scroll_offset
        content_x = self.panel_x + 20
        tier = self._get_tame_tier(animal.tame_progress)
        
        arcade.draw_text(
            "WORK ASSIGNMENTS",
            content_x, y,
            COLOR_NEON_MAGENTA,
            font_size=11,
            bold=True,
            font_name=UI_FONT
        )
        y -= 25
        
        if tier >= 4:  # 100% tamed
            for job_tag, enabled in animal.job_tags.items():
                job_name = job_tag.replace("can_", "").replace("_", " ").title()
                status = "✓ Enabled" if enabled else "✗ Disabled"
                color = COLOR_GOOD if enabled else COLOR_TEXT_DIM
                
                arcade.draw_text(
                    f"{job_name}: {status}",
                    content_x, y,
                    color,
                    font_size=9,
                    font_name=UI_FONT
                )
                y -= 18
        else:
            arcade.draw_text(
                "Fully tame this animal to assign jobs.",
                content_x, y,
                COLOR_TEXT_DIM,
                font_size=9,
                font_name=UI_FONT
            )
    
    def _draw_drives_tab(self, animal, start_y: int, height: int):
        """Draw Drives tab - needs and comfort."""
        y = start_y - self.scroll_offset
        content_x = self.panel_x + 20
        tier = self._get_tame_tier(animal.tame_progress)
        
        arcade.draw_text(
            "NEEDS & DRIVES",
            content_x, y,
            COLOR_NEON_MAGENTA,
            font_size=11,
            bold=True,
            font_name=UI_FONT
        )
        y -= 25
        
        if tier >= 1:  # 25%+ tamed
            for drive_name, value in animal.drives.items():
                display_name = drive_name.replace("_", " ").title()
                
                # Color based on value
                if value < 30:
                    color = COLOR_DANGER
                elif value < 60:
                    color = COLOR_WARNING
                else:
                    color = COLOR_GOOD
                
                arcade.draw_text(
                    f"{display_name}: {int(value)}%",
                    content_x, y,
                    color,
                    font_size=9,
                    font_name=UI_FONT
                )
                y -= 18
        else:
            arcade.draw_text(
                "Tame to 25% to see needs.",
                content_x, y,
                COLOR_TEXT_DIM,
                font_size=9,
                font_name=UI_FONT
            )
    
    def _draw_mind_tab(self, animal, start_y: int, height: int):
        """Draw Mind tab - thoughts and personality."""
        y = start_y - self.scroll_offset
        content_x = self.panel_x + 20
        tier = self._get_tame_tier(animal.tame_progress)
        
        arcade.draw_text(
            "THOUGHTS & PERSONALITY",
            content_x, y,
            COLOR_NEON_MAGENTA,
            font_size=11,
            bold=True,
            font_name=UI_FONT
        )
        y -= 25
        
        if tier >= 3:  # 75%+ tamed
            if animal.thoughts:
                for thought in animal.thoughts[-10:]:  # Last 10 thoughts
                    arcade.draw_text(
                        thought,
                        content_x, y,
                        COLOR_TEXT_NORMAL,
                        font_size=9,
                        font_name=UI_FONT
                    )
                    y -= 16
            else:
                arcade.draw_text(
                    "No recent thoughts.",
                    content_x, y,
                    COLOR_TEXT_DIM,
                    font_size=9,
                    font_name=UI_FONT
                )
        else:
            arcade.draw_text(
                "Tame to 75% to understand their thoughts.",
                content_x, y,
                COLOR_TEXT_DIM,
                font_size=9,
                font_name=UI_FONT
            )
    
    def _get_state_color(self, state: str) -> Tuple[int, int, int]:
        """Get color for animal state."""
        if state == "idle":
            return (150, 150, 170)
        elif state == "wandering":
            return (100, 200, 255)
        elif state == "fleeing":
            return (255, 100, 100)
        elif state == "eating":
            return (100, 255, 150)
        elif state == "sleeping":
            return (150, 150, 200)
        elif state == "tamed_idle":
            return (150, 255, 150)
        else:
            return COLOR_TEXT_NORMAL


# Singleton instance
_animal_popup: Optional[AnimalPopup] = None


def get_animal_popup() -> AnimalPopup:
    """Get or create the animal popup singleton."""
    global _animal_popup
    if _animal_popup is None:
        _animal_popup = AnimalPopup()
    return _animal_popup
