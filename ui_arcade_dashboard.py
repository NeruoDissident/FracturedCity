"""
Net-Log Dashboard System (Mega-Dashboard).

A centralized management interface for the colony, inspired by Dwarf Fortress/RimWorld.
- Full-screen modal overlay.
- Tab-based navigation (Overview, Roster, Logistics, etc.).
- Dense data tables.
- Context-sensitive detail inspector.
"""

import arcade
from typing import Optional, List, Dict, Tuple, Any

from config import SCREEN_W, SCREEN_H
from ui_arcade import (
    COLOR_BG_DARKEST, COLOR_BG_PANEL, COLOR_BG_DARK, COLOR_BG_ELEVATED,
    COLOR_NEON_CYAN, COLOR_NEON_MAGENTA, COLOR_NEON_PINK,
    COLOR_TEXT_BRIGHT, COLOR_TEXT_NORMAL, COLOR_TEXT_DIM,
    COLOR_BORDER_BRIGHT, COLOR_BORDER_DIM,
    UI_FONT, UI_FONT_MONO,
    COLOR_GOOD, COLOR_WARNING, COLOR_DANGER
)

# Reuse the existing ColonistPopup for the detail panel
from ui_arcade_colonist_popup import ColonistPopup
from ui_arcade_animal_popup import AnimalPopup
from ui_arcade_tab_inventory import draw_inventory_tab
from ui_arcade_tab_production import draw_production_tab
from ui_arcade_tab_jobs import draw_jobs_tab
from ui_arcade_tab_fauna import draw_fauna_tab

class Dashboard:
    """The main dashboard controller."""
    
    TABS = [
        {"id": "overview", "label": "OVERVIEW", "icon": "Create"}, # Material Icon names (placeholders)
        {"id": "roster", "label": "ROSTER", "icon": "People"},
        {"id": "logistics", "label": "LOGISTICS", "icon": "Inventory"},
        {"id": "production", "label": "PRODUCTION", "icon": "Factory"},
        {"id": "tasks", "label": "TASKS", "icon": "Task"},
        {"id": "fauna", "label": "FAUNA", "icon": "Pets"},
    ]
    
    def __init__(self, screen_width=SCREEN_W, screen_height=SCREEN_H):
        self.visible = False
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        # Layout metrics
        self.nav_width = 200
        self.detail_width = 450 # Wider detail panel for the reused popup content
        self.header_height = 60
        
        # State
        self.current_tab_id = "roster" # Default to roster for now
        self.selected_item = None # The item currently being inspected
        
        # Sub-components
        self.colonist_popup = ColonistPopup()
        self.animal_popup = AnimalPopup()
        self.current_table_items = []
        
        # Scroll states for tables
        self.table_scroll_y = 0
        self.table_hover_row = -1
        
    def toggle(self):
        """Toggle dashboard visibility."""
        self.visible = not self.visible
        if self.visible:
            # Refresh data or state if needed
            pass

    def on_resize(self, width: int, height: int):
        self.screen_width = width
        self.screen_height = height

    def handle_input(self, key, modifiers):
        """Handle keyboard input when dashboard is open."""
        if not self.visible:
            return False
            
        if key == arcade.key.ESCAPE:
            self.visible = False
            return True
            
        return False

    def handle_mouse_scroll(self, x, y, scroll_x, scroll_y):
        """Handle scroll events."""
        if not self.visible:
            return False
            
        # Check if scrolling in Table Area
        table_rect = self._get_content_rect()
        if (table_rect[0] <= x <= table_rect[1] and 
            table_rect[2] <= y <= table_rect[3]):
            self.table_scroll_y -= scroll_y * 30
            # Clamp scroll (would need content height calc)
            if self.table_scroll_y < 0: self.table_scroll_y = 0
            return True
            
        # Check if scrolling in Detail Panel
        # We can pass this to the colonist popup if we're inspecting a colonist
        if self.selected_item and self.current_tab_id == "roster":
             # We might need to map coordinate space if popup expects screen coords
             pass

        return False

    def handle_mouse_press(self, x, y, button, modifiers):
        """Handle mouse clicks."""
        if not self.visible:
            return False
            
        # 1. Navigation Rail
        if x < self.nav_width:
            # Clicked nav area
            tab_h = 50
            start_y = self.screen_height - self.header_height - 20
            
            for i, tab in enumerate(self.TABS):
                tab_y = start_y - (i * tab_h)
                if tab_y - tab_h <= y <= tab_y:
                    self.current_tab_id = tab["id"]
                    self.table_scroll_y = 0 # Reset scroll
                    self.selected_item = None # Clear selection
                    return True
        
        # 2. Detail Panel (Right)
        detail_rect = self._get_detail_rect()
        if (detail_rect[0] <= x <= detail_rect[1] and 
            detail_rect[2] <= y <= detail_rect[3]):
            
            # Pass click to detail component
            if self.current_tab_id == "roster" and self.selected_item:
                # Hack: Temporarily update popup geometry to match click
                self.colonist_popup.panel_x = detail_rect[0]
                self.colonist_popup.panel_y = detail_rect[2]
                self.colonist_popup.panel_width = detail_rect[1] - detail_rect[0]
                self.colonist_popup.panel_height = detail_rect[3] - detail_rect[2]
                
                # We need to set visible=True for handle_click to work, even though we draw it manually
                was_visible = self.colonist_popup.visible
                self.colonist_popup.visible = True 
                consumed = self.colonist_popup.handle_click(x, y)
                self.colonist_popup.visible = was_visible # Restore
                if consumed: return True

        # 3. Content Area (Table)
        content_rect = self._get_content_rect()
        if (content_rect[0] <= x <= content_rect[1] and 
            content_rect[2] <= y <= content_rect[3]):
            
            self._handle_table_click(x, y, content_rect)
            return True

        return True # Consume all clicks while dashboard is open

    def handle_mouse_motion(self, x, y, dx, dy):
        """Handle hover states."""
        if not self.visible:
            return
            
        content_rect = self._get_content_rect()
        if (content_rect[0] <= x <= content_rect[1] and 
            content_rect[2] <= y <= content_rect[3]):
            
            if self.current_tab_id == "roster":
                # Calculate hovered row
                rel_y = content_rect[3] - y + self.table_scroll_y
                header_h = 40
                row_h = 40
                
                if rel_y > header_h:
                    row_idx = int((rel_y - header_h) / row_h)
                    self.table_hover_row = row_idx
                else:
                    self.table_hover_row = -1
        else:
            self.table_hover_row = -1

    def _get_content_rect(self):
        """Return (left, right, bottom, top) of main content area."""
        return (
            self.nav_width, 
            self.screen_width - self.detail_width,
            0,
            self.screen_height - self.header_height
        )

    def _get_detail_rect(self):
        """Return (left, right, bottom, top) of detail panel."""
        return (
            self.screen_width - self.detail_width,
            self.screen_width,
            0,
            self.screen_height - self.header_height
        )

    def draw(self, game_data: Dict, mouse_x: int, mouse_y: int):
        """Main draw loop for dashboard."""
        if not self.visible:
            return
            
        # Reset table items for this frame (will be populated by tab draw func)
        self.current_table_items = []

        # 1. Dim background overlay
        arcade.draw_lrbt_rectangle_filled(0, self.screen_width, 0, self.screen_height, (0, 0, 0, 245))

        # 2. Header
        arcade.draw_lrbt_rectangle_filled(0, self.screen_width, self.screen_height - self.header_height, self.screen_height, COLOR_BG_PANEL)
        arcade.draw_line(0, self.screen_height - self.header_height, self.screen_width, self.screen_height - self.header_height, COLOR_BORDER_BRIGHT, 2)
        
        arcade.draw_text(
            "NET-LOG // COLONY MANAGEMENT", 
            20, self.screen_height - 40, 
            COLOR_NEON_CYAN, 
            font_size=20, 
            font_name=UI_FONT, 
            bold=True
        )

        # 3. Navigation Rail
        self._draw_nav_rail(mouse_x, mouse_y)

        # 4. Content Area
        rect = self._get_content_rect()
        # Clip content (scissor) would be good here, but for now just draw carefully
        
        if self.current_tab_id == "roster":
            self._draw_roster_tab(rect, game_data)
        elif self.current_tab_id == "logistics":
            draw_inventory_tab(self, rect, game_data)
        elif self.current_tab_id == "production":
            draw_production_tab(self, rect, game_data)
        elif self.current_tab_id == "tasks":
            draw_jobs_tab(self, rect, game_data)
        elif self.current_tab_id == "fauna":
            draw_fauna_tab(self, rect, game_data)
        elif self.current_tab_id == "overview":
            self._draw_placeholder_tab(rect, "Overview - Coming Soon")
        else:
            self._draw_placeholder_tab(rect, f"{self.current_tab_id.title()} - Coming Soon")

        # 5. Detail Panel
        self._draw_detail_panel(game_data, mouse_x, mouse_y)

    def _draw_nav_rail(self, mouse_x, mouse_y):
        """Draw left navigation tabs."""
        arcade.draw_lrbt_rectangle_filled(0, self.nav_width, 0, self.screen_height - self.header_height, COLOR_BG_DARK)
        arcade.draw_line(self.nav_width, 0, self.nav_width, self.screen_height - self.header_height, COLOR_BORDER_DIM, 1)
        
        start_y = self.screen_height - self.header_height - 20
        tab_h = 50
        
        for i, tab in enumerate(self.TABS):
            y = start_y - (i * tab_h)
            is_active = (tab["id"] == self.current_tab_id)
            
            # Check hover
            is_hovered = False
            if mouse_x < self.nav_width:
                if y - tab_h <= mouse_y <= y:
                    is_hovered = True
            
            # Hover/Active background
            if is_active:
                arcade.draw_lrbt_rectangle_filled(0, self.nav_width, y - tab_h, y, (30, 35, 45))
                arcade.draw_line(0, y - tab_h, 0, y, COLOR_NEON_MAGENTA, 4) # Left accent
            elif is_hovered:
                arcade.draw_lrbt_rectangle_filled(0, self.nav_width, y - tab_h, y, (25, 30, 40))
                arcade.draw_line(0, y - tab_h, 0, y, (100, 100, 100), 2) # Gray accent
            
            color = COLOR_NEON_CYAN if is_active else (COLOR_TEXT_BRIGHT if is_hovered else COLOR_TEXT_DIM)
            arcade.draw_text(
                tab["label"], 
                20, y - 30, 
                color, 
                font_size=12, 
                font_name=UI_FONT,
                bold=is_active or is_hovered
            )

    def _draw_placeholder_tab(self, rect, text):
        arcade.draw_text(
            text, 
            rect[0] + 50, rect[3] - 100, 
            COLOR_TEXT_DIM, 
            font_size=20, 
            font_name=UI_FONT
        )

    def _draw_roster_tab(self, rect, game_data):
        """Draw colonist table."""
        colonists = game_data.get("colonist_objects", [])
        self.current_table_items = colonists
        
        x, right, bottom, top = rect
        y = top - self.table_scroll_y
        
        # Column Config
        cols = [
            {"label": "NAME", "w": 150},
            {"label": "ROLE", "w": 100},
            {"label": "JOB", "w": 150},
            {"label": "MOOD", "w": 100},
            {"label": "VITALS", "w": 150},
        ]
        
        # Draw Header (Fixed at top of content area)
        header_y = top
        curr_x = x
        arcade.draw_lrbt_rectangle_filled(x, right, header_y - 40, header_y, COLOR_BG_ELEVATED)
        
        for col in cols:
            arcade.draw_text(col["label"], curr_x + 10, header_y - 25, COLOR_TEXT_DIM, font_size=10, font_name=UI_FONT, bold=True)
            curr_x += col["w"]
            
        # Draw Rows
        row_y = header_y - 40 - self.table_scroll_y
        row_h = 40
        
        for i, col in enumerate(colonists):
            # Culling
            if row_y < bottom - row_h: break
            if row_y > header_y: 
                row_y -= row_h
                continue
            
            # Hover highlight
            is_hovered = (i == self.table_hover_row)
            is_selected = (self.selected_item == col)
            
            if is_selected:
                arcade.draw_lrbt_rectangle_filled(x, right, row_y - row_h, row_y, (40, 30, 50))
                arcade.draw_lrbt_rectangle_outline(x, right, row_y - row_h, row_y, COLOR_NEON_MAGENTA, 1)
            elif is_hovered:
                arcade.draw_lrbt_rectangle_filled(x, right, row_y - row_h, row_y, (25, 30, 40))
                
            # Draw Data
            curr_x = x
            
            # 1. Name
            arcade.draw_text(col.name, curr_x + 10, row_y - 25, COLOR_TEXT_BRIGHT, font_size=11, font_name=UI_FONT)
            curr_x += cols[0]["w"]
            
            # 2. Role
            role = getattr(col, 'role', 'Colonist').title()
            arcade.draw_text(role, curr_x + 10, row_y - 25, COLOR_TEXT_NORMAL, font_size=10, font_name=UI_FONT)
            curr_x += cols[1]["w"]
            
            # 3. Job
            job_txt = col.current_job.type.replace("_", " ").title() if col.current_job else "Idle"
            arcade.draw_text(job_txt, curr_x + 10, row_y - 25, COLOR_TEXT_DIM, font_size=10, font_name=UI_FONT)
            curr_x += cols[2]["w"]
            
            # 4. Mood
            mood = getattr(col, 'mood_state', 'Neutral')
            mood_score = getattr(col, 'mood_score', 0)
            mood_col = COLOR_GOOD if mood_score > 5 else (COLOR_WARNING if mood_score > -5 else COLOR_DANGER)
            arcade.draw_text(mood, curr_x + 10, row_y - 25, mood_col, font_size=10, font_name=UI_FONT)
            curr_x += cols[3]["w"]
            
            # 5. Vitals (Health/Hunger)
            hp = int(col.health)
            hung = int(col.hunger)
            arcade.draw_text(f"HP:{hp}% Food:{100-hung}%", curr_x + 10, row_y - 25, COLOR_TEXT_NORMAL, font_size=10, font_name=UI_FONT_MONO)
            
            # Separator
            arcade.draw_line(x, row_y, right, row_y, (30, 35, 45), 1)
            
            row_y -= row_h

    def _handle_table_click(self, x, y, rect):
        """Generic handler for table clicks."""
        if self.table_hover_row != -1:
            if hasattr(self, 'current_table_items') and 0 <= self.table_hover_row < len(self.current_table_items):
                item = self.current_table_items[self.table_hover_row]
                self.selected_item = item
                
                if self.current_tab_id == "roster":
                    self.colonist_popup.set_colonists_list(self.current_table_items)
                    self.colonist_popup.open(item)
                elif self.current_tab_id == "fauna":
                    self.animal_popup.open(self.current_table_items, self.table_hover_row)

    def _draw_detail_panel(self, game_data, mouse_x, mouse_y):
        """Draw the right-side detail panel."""
        rect = self._get_detail_rect()
        x, right, bottom, top = rect
        
        # Background
        arcade.draw_lrbt_rectangle_filled(x, right, bottom, top, COLOR_BG_PANEL)
        arcade.draw_line(x, bottom, x, top, COLOR_BORDER_BRIGHT, 2)
        
        if self.current_tab_id == "roster" and self.selected_item:
            # Reuse ColonistPopup logic
            # We "trick" the popup into drawing within our rect
            # This requires the popup to respect its internal geometry which we override
            
            self.colonist_popup.panel_x = x
            self.colonist_popup.panel_y = bottom
            self.colonist_popup.panel_width = right - x
            self.colonist_popup.panel_height = top - bottom
            self.colonist_popup.visible = True
            
            # Since popup.draw() normally draws a modal overlay and centers itself,
            # we need to be careful. The existing ColonistPopup code uses self.panel_x/y/w/h
            # so overriding them SHOULD work, provided we suppressed the overlay.
            # But ColonistPopup.draw() hardcodes the overlay drawing.
            # It's better to refactor ColonistPopup to have a `draw_panel(x, y, w, h)` method.
            # For now, we'll let it draw and accept the overlay might act weird if not clipped,
            # OR we patch ColonistPopup.draw to skip overlay if a flag is set.
            
            # Hack: Manually calling internal draw methods of ColonistPopup
            # This avoids drawing the overlay and close button
            
            # We need to set up the popup state
            if self.colonist_popup.colonist != self.selected_item:
                 self.colonist_popup.open(self.selected_item)
            
            # Draw Title Bar (Custom for Dashboard)
            # arcade.draw_text("DETAILS", x + 10, top - 30, COLOR_NEON_MAGENTA, font_size=12, bold=True)
            
            # Draw content
            if hasattr(self.colonist_popup, 'draw_embedded'):
                self.colonist_popup.draw_embedded(x, bottom, right - x, top - bottom, mouse_x, mouse_y)
            else:
                arcade.draw_text("Popup update required...", x + 20, top - 100, COLOR_TEXT_DIM)
                
        elif self.current_tab_id == "fauna" and self.selected_item:
            # Reuse AnimalPopup logic
            self.animal_popup.panel_x = x
            self.animal_popup.panel_y = bottom
            self.animal_popup.panel_width = right - x
            self.animal_popup.panel_height = top - bottom
            self.animal_popup.visible = True
            
            if hasattr(self.animal_popup, 'draw_embedded'):
                self.animal_popup.draw_embedded(x, bottom, right - x, top - bottom, mouse_x, mouse_y)
            else:
                arcade.draw_text("Animal Popup update required...", x + 20, top - 100, COLOR_TEXT_DIM)
                
        else:
            # Empty state
            arcade.draw_text("Select an item to view details", x + 50, top - 100, COLOR_TEXT_DIM, font_size=12)

