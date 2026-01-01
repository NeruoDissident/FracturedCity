"""Animal Detail Panel UI for Fractured City.

Comprehensive animal information panel with progressive stat reveal based on tame level.
Follows same structure as ColonistDetailPanel for consistency.
"""

import arcade
from typing import List, Optional, Dict, Tuple

from config import SCREEN_W, SCREEN_H
from ui_arcade import (
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


class AnimalDetailPanel:
    """Right panel showing detailed animal information with progressive reveal.
    
    Stat visibility based on tame progress:
    - 0-24%: Only species, feral/tame bar, basic state
    - 25-49%: + Health, hunger, age
    - 50-74%: + Food preferences, sleep patterns
    - 75-99%: + Pen preferences, product info
    - 100%: Full stats, personality, relationships
    """
    
    TABS = ["Status", "Bio", "Stats", "Products", "Pen", "Help"]
    
    def __init__(self, screen_width=SCREEN_W, screen_height=SCREEN_H):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.visible = False
        self.animals = []  # Reference to all animals
        self.current_index = 0
        self.current_tab = 0
        
        # Panel dimensions
        self.width = RIGHT_PANEL_WIDTH
        self.height = screen_height - TOP_BAR_HEIGHT - BOTTOM_BAR_HEIGHT
        self.x = screen_width - self.width
        self.y = BOTTOM_BAR_HEIGHT
        
        # Vertical tab dimensions
        self.tab_width = 78
        self.tab_height = 32
        self.tab_spacing = 3
    
    def on_resize(self, width: int, height: int):
        """Update dimensions on window resize."""
        self.screen_width = width
        self.screen_height = height
        self.height = height - TOP_BAR_HEIGHT - BOTTOM_BAR_HEIGHT
        self.x = width - self.width
    
    def open(self, animals: List, animal_index: int = 0):
        """Open the panel for a specific animal."""
        self.animals = animals
        self.current_index = animal_index
        self.visible = True
    
    def close(self):
        """Close the panel."""
        self.visible = False
    
    def next_animal(self):
        """Switch to next animal."""
        if self.animals:
            self.current_index = (self.current_index + 1) % len(self.animals)
    
    def prev_animal(self):
        """Switch to previous animal."""
        if self.animals:
            self.current_index = (self.current_index - 1) % len(self.animals)
    
    def handle_click(self, x: int, y: int) -> bool:
        """Handle mouse click.
        
        Returns:
            True if click was handled
        """
        if not self.visible:
            return False
        
        # Check if click is in panel area
        if not (self.x <= x <= self.x + self.width and 
                self.y <= y <= self.y + self.height):
            return False
        
        # Check hunt button click (Status tab only)
        if self.current_tab == 0 and hasattr(self, 'hunt_button_bounds'):
            bx, by, bw, bh = self.hunt_button_bounds
            if bx <= x <= bx + bw and by <= y <= by + bh:
                animal = self.animals[self.current_index]
                from animals import mark_for_hunt, unmark_for_hunt
                
                if animal.marked_for_hunt:
                    unmark_for_hunt(animal)
                else:
                    mark_for_hunt(animal)
                
                return True
        
        # Check vertical tab clicks
        header_height = 50
        header_y = self.y + self.height - header_height
        tab_start_y = header_y - 10 - self.tab_height
        
        for i in range(len(self.TABS)):
            tab_y = tab_start_y - i * (self.tab_height + self.tab_spacing)
            if (self.x + 5 <= x <= self.x + 5 + self.tab_width and 
                tab_y <= y <= tab_y + self.tab_height):
                self.current_tab = i
                return True
        
        # Check prev/next buttons
        btn_y = self.y + self.height - 35
        
        if (self.x + self.width - 100 <= x <= self.x + self.width - 60 and btn_y <= y <= btn_y + 25):
            self.prev_animal()
            return True
        
        if (self.x + self.width - 55 <= x <= self.x + self.width - 15 and btn_y <= y <= btn_y + 25):
            self.next_animal()
            return True
        
        # Check close button
        close_x = self.x + 10
        close_y = self.y + self.height - 35
        if (close_x <= x <= close_x + 60 and close_y <= y <= close_y + 25):
            self.close()
            return True
        
        return True
    
    def draw(self):
        """Draw the animal detail panel."""
        if not self.visible or not self.animals:
            return
        
        if self.current_index >= len(self.animals):
            self.current_index = 0
        
        animal = self.animals[self.current_index]
        
        # Close panel if viewing a dead animal
        if not animal.is_alive():
            self.visible = False
            return
        
        # === MAIN PANEL BACKGROUND ===
        arcade.draw_lrbt_rectangle_filled(
            left=self.x,
            right=self.x + self.width,
            bottom=self.y,
            top=self.y + self.height,
            color=COLOR_BG_PANEL
        )
        
        # Left border with magenta glow (different from colonist cyan)
        arcade.draw_line(
            self.x, self.y,
            self.x, self.y + self.height,
            COLOR_ACCENT_MAGENTA, 3
        )
        
        # Subtle inner glow
        for i in range(8):
            alpha = 20 - i * 2
            arcade.draw_line(
                self.x + i, self.y,
                self.x + i, self.y + self.height,
                (*COLOR_ACCENT_MAGENTA, alpha), 1
            )
        
        # === HEADER SECTION ===
        header_height = 50
        header_y = self.y + self.height - header_height
        
        arcade.draw_lrbt_rectangle_filled(
            left=self.x,
            right=self.x + self.width,
            bottom=header_y,
            top=self.y + self.height,
            color=(15, 18, 25)
        )
        
        arcade.draw_line(
            self.x, header_y,
            self.x + self.width, header_y,
            COLOR_ACCENT_MAGENTA, 2
        )
        
        # Animal name/species
        species_name = animal.species_data["name"]
        variant_text = f"#{animal.variant}"
        arcade.draw_text(
            f"{species_name} {variant_text}",
            self.x + self.tab_width + 15,
            self.y + self.height - 30,
            COLOR_ACCENT_MAGENTA,
            font_size=14,
            bold=True,
            font_name=UI_FONT
        )
        
        # === CLOSE BUTTON ===
        close_x = self.x + 10
        close_y = self.y + self.height - 35
        arcade.draw_lrbt_rectangle_filled(
            left=close_x,
            right=close_x + 60,
            bottom=close_y,
            top=close_y + 25,
            color=(30, 35, 50)
        )
        arcade.draw_lrbt_rectangle_outline(
            left=close_x,
            right=close_x + 60,
            bottom=close_y,
            top=close_y + 25,
            color=COLOR_ACCENT_MAGENTA,
            border_width=1
        )
        arcade.draw_text(
            text="CLOSE",
            x=close_x + 30, y=close_y + 12,
            color=COLOR_TEXT_BRIGHT,
            font_size=9,
            anchor_x="center", anchor_y="center",
            bold=True,
            font_name=UI_FONT
        )
        
        # === PREV/NEXT BUTTONS ===
        btn_y = self.y + self.height - 35
        
        prev_x = self.x + self.width - 100
        arcade.draw_lrbt_rectangle_filled(
            left=prev_x,
            right=prev_x + 35,
            bottom=btn_y,
            top=btn_y + 25,
            color=(30, 35, 50)
        )
        arcade.draw_lrbt_rectangle_outline(
            left=prev_x,
            right=prev_x + 35,
            bottom=btn_y,
            top=btn_y + 25,
            color=COLOR_ACCENT_MAGENTA,
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
        
        next_x = self.x + self.width - 55
        arcade.draw_lrbt_rectangle_filled(
            left=next_x,
            right=next_x + 35,
            bottom=btn_y,
            top=btn_y + 25,
            color=(30, 35, 50)
        )
        arcade.draw_lrbt_rectangle_outline(
            left=next_x,
            right=next_x + 35,
            bottom=btn_y,
            top=btn_y + 25,
            color=COLOR_ACCENT_MAGENTA,
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
        
        counter_text = f"{self.current_index + 1}/{len(self.animals)}"
        arcade.draw_text(
            counter_text,
            self.x + self.width - 110,
            self.y + self.height - 30,
            COLOR_TEXT_DIM,
            font_size=10,
            anchor_x="right",
            font_name=UI_FONT_MONO
        )
        
        # === VERTICAL TABS ===
        tab_start_y = header_y - 10 - self.tab_height
        
        for i, tab_name in enumerate(self.TABS):
            tab_x = self.x + 5
            tab_y = tab_start_y - i * (self.tab_height + self.tab_spacing)
            is_active = (i == self.current_tab)
            
            if is_active:
                arcade.draw_lrbt_rectangle_filled(
                    left=tab_x,
                    right=tab_x + self.tab_width,
                    bottom=tab_y,
                    top=tab_y + self.tab_height,
                    color=(40, 50, 60)
                )
                arcade.draw_lrbt_rectangle_outline(
                    left=tab_x,
                    right=tab_x + self.tab_width,
                    bottom=tab_y,
                    top=tab_y + self.tab_height,
                    color=COLOR_ACCENT_MAGENTA,
                    border_width=2
                )
                arcade.draw_lrbt_rectangle_outline(
                    left=tab_x - 1,
                    right=tab_x + self.tab_width + 1,
                    bottom=tab_y - 1,
                    top=tab_y + self.tab_height + 1,
                    color=(*COLOR_ACCENT_MAGENTA, 60),
                    border_width=3
                )
                text_color = COLOR_ACCENT_MAGENTA
            else:
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
        
        # === CONTENT AREA ===
        content_x = self.x + self.tab_width + 10
        content_width = self.width - self.tab_width - 15
        content_y = self.y + self.height - 60
        content_height = self.height - 70
        
        # Draw content based on active tab
        if self.current_tab == 0:
            self._draw_status_tab(animal, content_x, content_y, content_width, content_height)
        elif self.current_tab == 1:
            self._draw_bio_tab(animal, content_x, content_y, content_width, content_height)
        elif self.current_tab == 2:
            self._draw_stats_tab(animal, content_x, content_y, content_width, content_height)
        elif self.current_tab == 3:
            self._draw_products_tab(animal, content_x, content_y, content_width, content_height)
        elif self.current_tab == 4:
            self._draw_pen_tab(animal, content_x, content_y, content_width, content_height)
        elif self.current_tab == 5:
            self._draw_help_tab(animal, content_x, content_y, content_width, content_height)
    
    def _get_tame_tier(self, tame_progress: int) -> int:
        """Get information tier based on tame progress.
        
        Returns:
            0: 0-24% (minimal info)
            1: 25-49% (basic vitals)
            2: 50-74% (preferences)
            3: 75-99% (advanced)
            4: 100% (complete)
        """
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
        """Draw a locked stat with tier requirement.
        
        Returns:
            Y offset used (for next stat)
        """
        is_locked = current_tier < required_tier
        
        if is_locked:
            # Locked - show ??? and lock icon
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
        
        return 0  # Not locked, caller will draw actual value
    
    def _draw_status_tab(self, animal, content_x: int, content_y: int, content_width: int, content_height: int):
        """Draw Status tab - core animal state."""
        y = content_y - 10
        tier = self._get_tame_tier(animal.tame_progress)
        
        # === HUNT BUTTON (Always visible at top) ===
        button_width = 120
        button_height = 30
        button_x = content_x + content_width - button_width - 10
        button_y = y
        
        # Check if already marked for hunt
        is_marked = animal.marked_for_hunt
        button_color = COLOR_DANGER if is_marked else COLOR_ACCENT_MAGENTA
        button_text = "Cancel Hunt" if is_marked else "Hunt"
        
        # Draw button
        arcade.draw_lrbt_rectangle_filled(
            left=button_x,
            right=button_x + button_width,
            bottom=button_y - button_height,
            top=button_y,
            color=button_color
        )
        arcade.draw_lrbt_rectangle_outline(
            left=button_x,
            right=button_x + button_width,
            bottom=button_y - button_height,
            top=button_y,
            color=COLOR_BORDER_BRIGHT,
            border_width=2
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
        self.hunt_button_bounds = (button_x, button_y - button_height, button_width, button_height)
        
        y -= 45  # Move content down below button
        
        # === FERAL/TAME BAR (Always visible) ===
        arcade.draw_text(
            "TAME PROGRESS",
            content_x, y,
            COLOR_ACCENT_MAGENTA,
            font_size=10,
            bold=True,
            font_name=UI_FONT
        )
        y -= 25
        
        # Progress bar
        bar_width = content_width - 20
        bar_height = 20
        bar_x = content_x + 5
        
        # Background
        arcade.draw_lrbt_rectangle_filled(
            left=bar_x,
            right=bar_x + bar_width,
            bottom=y,
            top=y + bar_height,
            color=(20, 20, 30)
        )
        
        # Fill based on tame progress
        fill_width = (animal.tame_progress / 100.0) * bar_width
        if animal.tame_progress < 25:
            fill_color = (255, 80, 80)  # Red - feral
        elif animal.tame_progress < 50:
            fill_color = (255, 180, 80)  # Orange
        elif animal.tame_progress < 75:
            fill_color = (255, 255, 80)  # Yellow
        elif animal.tame_progress < 100:
            fill_color = (150, 255, 150)  # Light green
        else:
            fill_color = (0, 255, 150)  # Bright green - tamed
        
        arcade.draw_lrbt_rectangle_filled(
            left=bar_x,
            right=bar_x + fill_width,
            bottom=y,
            top=y + bar_height,
            color=fill_color
        )
        
        # Border
        arcade.draw_lrbt_rectangle_outline(
            left=bar_x,
            right=bar_x + bar_width,
            bottom=y,
            top=y + bar_height,
            color=COLOR_BORDER_BRIGHT,
            border_width=1
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
        
        # === STATE (Always visible) ===
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
        
        # === LOCATION (Always visible) ===
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
            COLOR_TEXT_CYAN,
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
            # Locked stats
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
                COLOR_ACCENT_MAGENTA,
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
                COLOR_ACCENT_MAGENTA,
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
                    COLOR_ACCENT_CYAN,
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
    
    def _draw_bio_tab(self, animal, content_x: int, content_y: int, content_width: int, content_height: int):
        """Draw Bio tab - species info and lore."""
        y = content_y - 10
        tier = self._get_tame_tier(animal.tame_progress)
        
        # Species name
        arcade.draw_text(
            animal.species_data["name"].upper(),
            content_x, y,
            COLOR_ACCENT_MAGENTA,
            font_size=12,
            bold=True,
            font_name=UI_FONT
        )
        y -= 25
        
        # Basic species info (always visible)
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
                COLOR_ACCENT_MAGENTA,
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
                COLOR_ACCENT_MAGENTA,
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
    
    def _draw_stats_tab(self, animal, content_x: int, content_y: int, content_width: int, content_height: int):
        """Draw Stats tab - detailed statistics."""
        y = content_y - 10
        tier = self._get_tame_tier(animal.tame_progress)
        
        arcade.draw_text(
            "STATISTICS",
            content_x, y,
            COLOR_ACCENT_MAGENTA,
            font_size=11,
            bold=True,
            font_name=UI_FONT
        )
        y -= 25
        
        # All stats require tier 1+
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
    
    def _draw_products_tab(self, animal, content_x: int, content_y: int, content_width: int, content_height: int):
        """Draw Products tab - eggs, milk, etc."""
        y = content_y - 10
        tier = self._get_tame_tier(animal.tame_progress)
        
        arcade.draw_text(
            "PRODUCTS",
            content_x, y,
            COLOR_ACCENT_MAGENTA,
            font_size=11,
            bold=True,
            font_name=UI_FONT
        )
        y -= 25
        
        if tier >= 3:
            # Show product info for 75%+ tamed
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
            
            # Future: milk, wool, etc.
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
    
    def _draw_pen_tab(self, animal, content_x: int, content_y: int, content_width: int, content_height: int):
        """Draw Pen tab - housing preferences."""
        y = content_y - 10
        tier = self._get_tame_tier(animal.tame_progress)
        
        arcade.draw_text(
            "PEN REQUIREMENTS",
            content_x, y,
            COLOR_ACCENT_MAGENTA,
            font_size=11,
            bold=True,
            font_name=UI_FONT
        )
        y -= 25
        
        if tier >= 3:
            # Show pen info for 75%+ tamed
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
            
            # Future: pen preferences, comfort items, etc.
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
    
    def _draw_help_tab(self, animal, content_x: int, content_y: int, content_width: int, content_height: int):
        """Draw Help tab - taming guide."""
        y = content_y - 10
        
        arcade.draw_text(
            "TAMING GUIDE",
            content_x, y,
            COLOR_ACCENT_MAGENTA,
            font_size=11,
            bold=True,
            font_name=UI_FONT
        )
        y -= 25
        
        help_text = [
            "Information unlocks as you tame:",
            "",
            "0-24%: Basic state only",
            "25-49%: Health, hunger, age",
            "50-74%: Behavior patterns",
            "75-99%: Products, pen info",
            "100%: Full stats, ownership",
            "",
            "Hunt wild animals for meat.",
            "Tame them for products.",
        ]
        
        for line in help_text:
            if line == "":
                y -= 10
                continue
            
            color = COLOR_TEXT_BRIGHT if line.endswith("%:") or line.endswith(":") else COLOR_TEXT_NORMAL
            arcade.draw_text(
                line,
                content_x, y,
                color,
                font_size=9,
                font_name=UI_FONT
            )
            y -= 16
    
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
_animal_panel: Optional[AnimalDetailPanel] = None


def get_animal_panel(screen_width=SCREEN_W, screen_height=SCREEN_H) -> AnimalDetailPanel:
    """Get or create the animal detail panel singleton."""
    global _animal_panel
    if _animal_panel is None:
        _animal_panel = AnimalDetailPanel(screen_width, screen_height)
    return _animal_panel
