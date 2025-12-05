"""Clean bottom-bar action ribbon UI system.

Provides a clean, organized UI with:
- Bottom action bar with main category buttons
- Popup submenus for each category
- Keyboard shortcuts for quick access
- Clear selection states

Main Categories:
- Build (B): Walls, Floors, Movement, Entrance
- Zone (Z): Stockpile, Allow
- Harvest (H): Combined harvest + haul tool
"""

from __future__ import annotations

import pygame
from typing import Optional, Callable, Dict, List

from config import (
    SCREEN_W,
    SCREEN_H,
    COLOR_UI_BUTTON,
    COLOR_UI_BUTTON_HOVER,
    COLOR_UI_BUTTON_ACTIVE,
    COLOR_UI_TEXT,
    COLOR_UI_PANEL,
)

# UI Layout constants
BAR_HEIGHT = 54
BAR_PADDING = 10
BUTTON_HEIGHT = 38
BUTTON_SPACING = 8
SUBMENU_MIN_WIDTH = 160  # Minimum width, will expand to fit content
SUBMENU_ITEM_HEIGHT = 34


class Button:
    """Simple clickable button with optional keybind and cost display."""
    
    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        text: str,
        keybind: str = "",
        cost: str = "",
        on_click: Optional[Callable] = None,
    ):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.keybind = keybind
        self.cost = cost
        self.on_click = on_click
        self.hovered = False
        self.active = False
    
    def update(self, mouse_pos: tuple[int, int]) -> None:
        """Update hover state."""
        self.hovered = self.rect.collidepoint(mouse_pos)
    
    def handle_click(self, mouse_pos: tuple[int, int]) -> bool:
        """Handle click. Returns True if clicked."""
        if self.rect.collidepoint(mouse_pos):
            if self.on_click:
                self.on_click()
            return True
        return False
    
    def draw(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        """Draw the button."""
        # Background color based on state
        if self.active:
            color = COLOR_UI_BUTTON_ACTIVE
        elif self.hovered:
            color = COLOR_UI_BUTTON_HOVER
        else:
            color = COLOR_UI_BUTTON
        
        # Draw rounded rect with subtle gradient effect
        pygame.draw.rect(surface, color, self.rect, border_radius=6)
        
        # Highlight on top edge for depth
        if not self.active:
            highlight_rect = pygame.Rect(self.rect.x + 2, self.rect.y + 1, self.rect.width - 4, 2)
            highlight_color = (min(color[0] + 30, 255), min(color[1] + 30, 255), min(color[2] + 30, 255))
            pygame.draw.rect(surface, highlight_color, highlight_rect, border_radius=2)
        
        # Border
        border_color = (180, 180, 190) if self.hovered else (100, 100, 110)
        pygame.draw.rect(surface, border_color, self.rect, 1, border_radius=6)
        
        # Layout: [keybind] Name                    Cost
        left_margin = 8
        right_margin = 8
        
        # Draw keybind on left if present
        if self.keybind:
            kb_surface = font.render(f"[{self.keybind}]", True, (140, 180, 220))
            kb_rect = kb_surface.get_rect(midleft=(self.rect.left + left_margin, self.rect.centery))
            surface.blit(kb_surface, kb_rect)
            text_left = kb_rect.right + 6
        else:
            text_left = self.rect.left + left_margin
        
        # Draw cost on right if present (dimmer color)
        if self.cost:
            cost_surface = font.render(self.cost, True, (160, 160, 140))
            cost_rect = cost_surface.get_rect(midright=(self.rect.right - right_margin, self.rect.centery))
            surface.blit(cost_surface, cost_rect)
            text_right = cost_rect.left - 6
        else:
            text_right = self.rect.right - right_margin
        
        # Draw main text (left-aligned after keybind, or centered if no cost)
        text_surface = font.render(self.text, True, COLOR_UI_TEXT)
        if self.cost:
            # Left-align after keybind
            text_rect = text_surface.get_rect(midleft=(text_left, self.rect.centery))
        elif self.keybind:
            # Center in remaining space
            text_rect = text_surface.get_rect(midleft=(text_left, self.rect.centery))
        else:
            # Center in button
            text_rect = text_surface.get_rect(center=self.rect.center)
        
        surface.blit(text_surface, text_rect)


class SubMenu:
    """Popup submenu that appears above a main button."""
    
    def __init__(self, items: List[Dict], parent_button: Button, font: Optional[pygame.font.Font] = None):
        self.items = items  # List of {"id": str, "name": str, "keybind": str (optional)}
        self.parent = parent_button
        self.visible = False
        self.buttons: List[Button] = []
        self.panel_width = SUBMENU_MIN_WIDTH
        self.panel_rect = pygame.Rect(0, 0, self.panel_width, 0)
        self.selected_item: Optional[str] = None
        self._font = font
        self._create_buttons()
    
    def _calculate_width(self) -> int:
        """Calculate required width to fit all content."""
        if self._font is None:
            self._font = pygame.font.Font(None, 22)
        
        max_width = SUBMENU_MIN_WIDTH
        for item in self.items:
            # Calculate width needed: padding + keybind + name + cost + padding
            keybind = item.get("keybind", "")
            name = item["name"]
            cost = item.get("cost", "")
            
            kb_width = self._font.size(f"[{keybind}] ")[0] if keybind else 0
            name_width = self._font.size(name)[0]
            cost_width = self._font.size(f"  {cost}")[0] if cost else 0
            
            total = 24 + kb_width + name_width + cost_width + 24  # margins
            max_width = max(max_width, total)
        
        return max_width
    
    def _create_buttons(self) -> None:
        """Create buttons for menu items."""
        self.buttons = []
        padding = 6
        item_spacing = 4
        
        # Calculate width to fit content
        self.panel_width = self._calculate_width()
        self.panel_rect.width = self.panel_width
        
        for i, item in enumerate(self.items):
            y = padding + i * (SUBMENU_ITEM_HEIGHT + item_spacing)
            btn = Button(
                x=padding,
                y=y,
                width=self.panel_width - padding * 2,
                height=SUBMENU_ITEM_HEIGHT,
                text=item["name"],
                keybind=item.get("keybind", ""),
                cost=item.get("cost", ""),
                on_click=lambda item_id=item["id"]: self._select_item(item_id),
            )
            self.buttons.append(btn)
        
        # Update panel height
        total_height = len(self.buttons) * (SUBMENU_ITEM_HEIGHT + item_spacing) + padding * 2 - item_spacing
        self.panel_rect.height = total_height
    
    def _select_item(self, item_id: str) -> None:
        """Handle item selection."""
        self.selected_item = item_id
        self.visible = False
    
    def show(self) -> None:
        """Show the submenu above parent button."""
        self.visible = True
        self.selected_item = None
        # Position above parent button
        self.panel_rect.x = self.parent.rect.x
        self.panel_rect.bottom = self.parent.rect.top - 6
        
        # Ensure menu doesn't go off-screen to the right
        from config import SCREEN_W
        if self.panel_rect.right > SCREEN_W - 10:
            self.panel_rect.right = SCREEN_W - 10
        
        # Update button positions
        padding = 6
        item_spacing = 4
        for i, btn in enumerate(self.buttons):
            btn.rect.x = self.panel_rect.x + padding
            btn.rect.width = self.panel_width - padding * 2
            btn.rect.y = self.panel_rect.y + padding + i * (SUBMENU_ITEM_HEIGHT + item_spacing)
    
    def hide(self) -> None:
        """Hide the submenu."""
        self.visible = False
    
    def update(self, mouse_pos: tuple[int, int]) -> None:
        """Update hover states."""
        if not self.visible:
            return
        for btn in self.buttons:
            btn.update(mouse_pos)
    
    def handle_click(self, mouse_pos: tuple[int, int]) -> bool:
        """Handle click. Returns True if consumed."""
        if not self.visible:
            return False
        
        if self.panel_rect.collidepoint(mouse_pos):
            for btn in self.buttons:
                if btn.handle_click(mouse_pos):
                    return True
            return True
        
        # Click outside - close
        self.hide()
        return False
    
    def draw(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        """Draw the submenu."""
        if not self.visible:
            return
        
        # Panel background with shadow effect
        shadow_rect = self.panel_rect.copy()
        shadow_rect.x += 3
        shadow_rect.y += 3
        pygame.draw.rect(surface, (20, 20, 25), shadow_rect, border_radius=8)
        
        # Main panel
        pygame.draw.rect(surface, COLOR_UI_PANEL, self.panel_rect, border_radius=8)
        pygame.draw.rect(surface, (100, 100, 110), self.panel_rect, 1, border_radius=8)
        
        for btn in self.buttons:
            btn.draw(surface, font)


class ActionBar:
    """Bottom action bar with main category buttons and submenus."""
    
    # Menu structure - costs shown in parentheses
    BUILD_MENU = {
        "walls": [
            {"id": "wall", "name": "Wall", "cost": "2 wood", "keybind": "1"},
            {"id": "wall_advanced", "name": "Reinforced Wall", "cost": "2 mineral", "keybind": "2"},
        ],
        "floors": [
            {"id": "floor", "name": "Wood Floor", "cost": "1 wood", "keybind": "1"},
        ],
        "movement": [
            {"id": "fire_escape", "name": "Fire Escape", "cost": "1 wood, 1 metal", "keybind": "1"},
            {"id": "bridge", "name": "Bridge", "cost": "2 wood, 1 metal", "keybind": "2"},
        ],
        "entrance": [
            {"id": "door", "name": "Door", "cost": "1 wood, 1 metal", "keybind": "1"},
            {"id": "window", "name": "Window", "cost": "1 wood, 1 mineral", "keybind": "2"},
        ],
        "workstations": [
            {"id": "salvagers_bench", "name": "Salvager's Bench", "cost": "3 wood, 2 scrap", "keybind": "1"},
            {"id": "generator", "name": "Generator", "cost": "2 wood, 2 metal", "keybind": "2"},
            {"id": "stove", "name": "Stove", "cost": "2 metal, 1 mineral", "keybind": "3"},
        ],
    }
    
    ZONE_MENU = [
        {"id": "stockpile", "name": "Stockpile", "keybind": "1"},
        {"id": "allow", "name": "Allow", "keybind": "2"},
        {"id": "demolish", "name": "Demolish", "keybind": "3"},
    ]
    
    def __init__(self):
        self.font: Optional[pygame.font.Font] = None
        
        # Main action buttons
        self.main_buttons: Dict[str, Button] = {}
        self.submenus: Dict[str, SubMenu] = {}
        self.build_submenus: Dict[str, SubMenu] = {}
        
        # State
        self.active_menu: Optional[str] = None  # "build", "zone", "harvest"
        self.active_submenu: Optional[str] = None  # "walls", "floors", etc.
        self.current_tool: Optional[str] = None  # "wall", "stockpile", "harvest", etc.
        
        # Bar rect
        self.bar_rect = pygame.Rect(0, SCREEN_H - BAR_HEIGHT, SCREEN_W, BAR_HEIGHT)
        
        self._create_ui()
    
    def _create_ui(self) -> None:
        """Create all UI elements."""
        # Main buttons - centered in bar (4 buttons now)
        button_width = 90
        num_buttons = 4
        total_width = button_width * num_buttons + BUTTON_SPACING * (num_buttons - 1)
        start_x = (SCREEN_W - total_width) // 2
        button_y = SCREEN_H - BAR_HEIGHT + (BAR_HEIGHT - BUTTON_HEIGHT) // 2
        
        # Build button
        self.main_buttons["build"] = Button(
            x=start_x,
            y=button_y,
            width=button_width,
            height=BUTTON_HEIGHT,
            text="Build",
            keybind="B",
        )
        
        # Zone button
        self.main_buttons["zone"] = Button(
            x=start_x + (button_width + BUTTON_SPACING),
            y=button_y,
            width=button_width,
            height=BUTTON_HEIGHT,
            text="Zone",
            keybind="Z",
        )
        
        # Salvage button (new core action)
        self.main_buttons["salvage"] = Button(
            x=start_x + (button_width + BUTTON_SPACING) * 2,
            y=button_y,
            width=button_width,
            height=BUTTON_HEIGHT,
            text="Salvage",
            keybind="",  # No keybind - conflicts with WASD camera
        )
        
        # Harvest button
        self.main_buttons["harvest"] = Button(
            x=start_x + (button_width + BUTTON_SPACING) * 3,
            y=button_y,
            width=button_width,
            height=BUTTON_HEIGHT,
            text="Harvest",
            keybind="H",
        )
        
        # Build category submenu (Walls, Floors, Movement, Entrance, Workstations)
        build_categories = [
            {"id": "walls", "name": "Walls", "keybind": "1"},
            {"id": "floors", "name": "Floors", "keybind": "2"},
            {"id": "movement", "name": "Movement", "keybind": "3"},
            {"id": "entrance", "name": "Entrance", "keybind": "4"},
            {"id": "workstations", "name": "Workstations", "keybind": "5"},
        ]
        self.submenus["build"] = SubMenu(build_categories, self.main_buttons["build"])
        
        # Zone submenu
        self.submenus["zone"] = SubMenu(self.ZONE_MENU, self.main_buttons["zone"])
        
        # Build sub-submenus (one for each category)
        for cat_id, items in self.BUILD_MENU.items():
            # Create a temporary parent for positioning
            self.build_submenus[cat_id] = SubMenu(items, self.main_buttons["build"])
    
    def init_font(self) -> None:
        """Initialize font after pygame.init()."""
        self.font = pygame.font.Font(None, 22)
    
    def _close_all_menus(self) -> None:
        """Close all open menus."""
        for menu in self.submenus.values():
            menu.hide()
        for menu in self.build_submenus.values():
            menu.hide()
        self.active_menu = None
        self.active_submenu = None
        for btn in self.main_buttons.values():
            btn.active = False
    
    def _open_menu(self, menu_id: str) -> None:
        """Open a main menu."""
        self._close_all_menus()
        self.active_menu = menu_id
        self.main_buttons[menu_id].active = True
        
        if menu_id == "harvest":
            # Harvest is a direct tool, no submenu
            self.current_tool = "harvest"
        elif menu_id == "salvage":
            # Salvage is a direct tool, no submenu
            self.current_tool = "salvage"
        elif menu_id in self.submenus:
            self.submenus[menu_id].show()
    
    def _open_build_submenu(self, category: str) -> None:
        """Open a build category submenu."""
        # Close the main build menu
        self.submenus["build"].hide()
        self.active_submenu = category
        
        # Position and show the category submenu
        submenu = self.build_submenus[category]
        submenu.panel_rect.x = self.main_buttons["build"].rect.x
        submenu.panel_rect.bottom = self.main_buttons["build"].rect.top - 6
        
        # Ensure menu doesn't go off-screen to the right
        if submenu.panel_rect.right > SCREEN_W - 10:
            submenu.panel_rect.right = SCREEN_W - 10
        
        # Update button positions
        padding = 6
        item_spacing = 4
        for i, btn in enumerate(submenu.buttons):
            btn.rect.x = submenu.panel_rect.x + padding
            btn.rect.y = submenu.panel_rect.y + padding + i * (SUBMENU_ITEM_HEIGHT + item_spacing)
        
        submenu.visible = True
    
    def get_current_tool(self) -> Optional[str]:
        """Get the currently selected tool."""
        return self.current_tool
    
    def cancel_tool(self) -> None:
        """Cancel current tool selection."""
        self.current_tool = None
        self._close_all_menus()
    
    def handle_key(self, key: int) -> bool:
        """Handle keyboard input. Returns True if consumed."""
        # Main menu shortcuts
        if key == pygame.K_b:
            if self.active_menu == "build":
                self.cancel_tool()
            else:
                self._open_menu("build")
            return True
        
        if key == pygame.K_z:
            if self.current_tool == "zone":
                self.cancel_tool()
            else:
                self._open_menu("zone")
            return True
        
        # K_s keybinding removed - conflicts with camera movement (WASD)
        # Use UI button to access salvage tool
        
        if key == pygame.K_h:
            if self.current_tool == "harvest":
                self.cancel_tool()
            else:
                self._open_menu("harvest")
            return True
        
        # Number keys for submenu selection
        if key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5):
            num = key - pygame.K_1  # 0-4
            
            if self.active_menu == "build" and self.active_submenu is None:
                # Select build category
                categories = ["walls", "floors", "movement", "entrance", "workstations"]
                if num < len(categories):
                    self._open_build_submenu(categories[num])
                    return True
            
            elif self.active_menu == "build" and self.active_submenu:
                # Select item from build category
                items = self.BUILD_MENU.get(self.active_submenu, [])
                if num < len(items):
                    self.current_tool = items[num]["id"]
                    self._close_all_menus()
                    self.main_buttons["build"].active = True
                    return True
            
            elif self.active_menu == "zone":
                # Select zone item
                if num < len(self.ZONE_MENU):
                    self.current_tool = self.ZONE_MENU[num]["id"]
                    self._close_all_menus()
                    self.main_buttons["zone"].active = True
                    return True
        
        # Escape to cancel
        if key == pygame.K_ESCAPE:
            if self.current_tool or self.active_menu:
                self.cancel_tool()
                return True
        
        return False
    
    def update(self, mouse_pos: tuple[int, int]) -> None:
        """Update hover states."""
        for btn in self.main_buttons.values():
            btn.update(mouse_pos)
        
        for menu in self.submenus.values():
            menu.update(mouse_pos)
        
        for menu in self.build_submenus.values():
            menu.update(mouse_pos)
        
        # Check for submenu selections
        if self.active_menu == "build" and self.active_submenu is None:
            submenu = self.submenus["build"]
            if submenu.selected_item:
                self._open_build_submenu(submenu.selected_item)
                submenu.selected_item = None
        
        elif self.active_menu == "build" and self.active_submenu:
            submenu = self.build_submenus[self.active_submenu]
            if submenu.selected_item:
                self.current_tool = submenu.selected_item
                submenu.selected_item = None
                self._close_all_menus()
                self.main_buttons["build"].active = True
        
        elif self.active_menu == "zone":
            submenu = self.submenus["zone"]
            if submenu.selected_item:
                self.current_tool = submenu.selected_item
                submenu.selected_item = None
                self._close_all_menus()
                self.main_buttons["zone"].active = True
    
    def handle_click(self, mouse_pos: tuple[int, int], button: int) -> bool:
        """Handle mouse click. Returns True if consumed."""
        if button == 1:  # Left click
            # Check submenus first (they're on top)
            for menu in self.build_submenus.values():
                if menu.handle_click(mouse_pos):
                    return True
            
            for menu in self.submenus.values():
                if menu.handle_click(mouse_pos):
                    return True
            
            # Check main buttons
            for btn_id, btn in self.main_buttons.items():
                if btn.rect.collidepoint(mouse_pos):
                    if self.active_menu == btn_id and self.current_tool:
                        # Clicking active button cancels
                        self.cancel_tool()
                    else:
                        self._open_menu(btn_id)
                    return True
            
            # Check if click is in bar area (consume but don't act)
            if self.bar_rect.collidepoint(mouse_pos):
                return True
        
        elif button == 3:  # Right click cancels
            if self.current_tool or self.active_menu:
                self.cancel_tool()
                return True
        
        return False
    
    def draw(self, surface: pygame.Surface) -> None:
        """Draw the action bar and menus."""
        if self.font is None:
            self.init_font()
        
        # Draw bar background with gradient effect
        pygame.draw.rect(surface, COLOR_UI_PANEL, self.bar_rect)
        # Top highlight line
        pygame.draw.line(surface, (70, 70, 85), 
                        (0, self.bar_rect.top), (SCREEN_W, self.bar_rect.top), 2)
        pygame.draw.line(surface, (50, 50, 60), 
                        (0, self.bar_rect.top + 2), (SCREEN_W, self.bar_rect.top + 2), 1)
        
        # Draw current tool indicator on LEFT side (before buttons)
        if self.current_tool:
            tool_name = self.current_tool.replace("_", " ").title()
            
            # Tool name with colored background pill
            tool_text = f" {tool_name} "
            tool_surface = self.font.render(tool_text, True, (255, 255, 255))
            tool_rect = tool_surface.get_rect(midleft=(12, self.bar_rect.centery))
            
            # Background pill
            pill_rect = tool_rect.inflate(8, 6)
            pygame.draw.rect(surface, (80, 120, 160), pill_rect, border_radius=4)
            pygame.draw.rect(surface, (100, 150, 200), pill_rect, 1, border_radius=4)
            surface.blit(tool_surface, tool_rect)
            
            # Cancel hint on RIGHT side
            hint_text = "[ESC] Cancel"
            hint_surface = self.font.render(hint_text, True, (140, 140, 150))
            hint_rect = hint_surface.get_rect(midright=(SCREEN_W - 12, self.bar_rect.centery))
            surface.blit(hint_surface, hint_rect)
        
        # Draw main buttons
        for btn in self.main_buttons.values():
            btn.draw(surface, self.font)
        
        # Draw submenus
        for menu in self.submenus.values():
            menu.draw(surface, self.font)
        
        for menu in self.build_submenus.values():
            menu.draw(surface, self.font)


# ============================================================================
# Stockpile Filter Panel
# ============================================================================

class StockpileFilterPanel:
    """UI panel for editing stockpile zone filters."""
    
    RESOURCE_TYPES = ["wood", "mineral", "scrap", "metal", "power", "raw_food", "cooked_meal"]
    RESOURCE_COLORS = {
        "wood": (139, 90, 43),
        "mineral": (80, 200, 200),
        "scrap": (120, 120, 120),
        "metal": (180, 180, 200),
        "power": (255, 220, 80),
        "raw_food": (180, 220, 100),
        "cooked_meal": (220, 160, 80),
    }
    RESOURCE_NAMES = {
        "wood": "Wood",
        "mineral": "Mineral",
        "scrap": "Scrap",
        "metal": "Metal",
        "power": "Power",
        "raw_food": "Raw Food",
        "cooked_meal": "Meal",
    }
    
    def __init__(self):
        self.visible = False
        self.zone_id: Optional[int] = None
        self.zone_info: Optional[dict] = None
        self.panel_rect = pygame.Rect(0, 0, 180, 260)  # Taller for more items
        self.filter_rects: Dict[str, pygame.Rect] = {}
        self.font: Optional[pygame.font.Font] = None
    
    def init_font(self) -> None:
        self.font = pygame.font.Font(None, 22)
    
    def open(self, zone_id: int, screen_x: int, screen_y: int) -> None:
        """Open the filter panel for a zone at screen position."""
        import zones
        self.zone_id = zone_id
        self.zone_info = zones.get_zone_info(zone_id)
        if self.zone_info is None:
            return
        
        self.visible = True
        
        # Position panel near click but keep on screen
        self.panel_rect.x = min(screen_x, SCREEN_W - self.panel_rect.width - 10)
        self.panel_rect.y = min(screen_y, SCREEN_H - self.panel_rect.height - 60)
        
        # Build filter toggle rects
        self._build_filter_rects()
    
    def _build_filter_rects(self) -> None:
        """Build clickable rectangles for each filter toggle."""
        self.filter_rects.clear()
        y = self.panel_rect.y + 40
        for res_type in self.RESOURCE_TYPES:
            self.filter_rects[res_type] = pygame.Rect(
                self.panel_rect.x + 10, y, self.panel_rect.width - 20, 28
            )
            y += 30
    
    def close(self) -> None:
        """Close the panel."""
        self.visible = False
        self.zone_id = None
        self.zone_info = None
    
    def handle_click(self, mouse_pos: tuple[int, int]) -> bool:
        """Handle click. Returns True if consumed."""
        if not self.visible:
            return False
        
        # Click outside panel closes it
        if not self.panel_rect.collidepoint(mouse_pos):
            self.close()
            return True
        
        # Check filter toggles
        import zones
        for res_type, rect in self.filter_rects.items():
            if rect.collidepoint(mouse_pos):
                new_val = zones.toggle_zone_filter(self.zone_id, res_type)
                if new_val is not None:
                    # Refresh zone info
                    self.zone_info = zones.get_zone_info(self.zone_id)
                return True
        
        return True  # Consume click on panel
    
    def draw(self, surface: pygame.Surface) -> None:
        """Draw the filter panel."""
        if not self.visible or self.zone_info is None:
            return
        
        if self.font is None:
            self.init_font()
        
        # Panel background
        pygame.draw.rect(surface, (40, 42, 48), self.panel_rect, border_radius=6)
        pygame.draw.rect(surface, (80, 85, 95), self.panel_rect, 1, border_radius=6)
        
        # Title
        title = self.font.render("Stockpile Filters", True, (220, 220, 220))
        surface.blit(title, (self.panel_rect.x + 10, self.panel_rect.y + 10))
        
        # Filter toggles
        filters = self.zone_info.get("filters", {})
        for res_type, rect in self.filter_rects.items():
            allowed = filters.get(res_type, True)
            
            # Background
            bg_color = (50, 70, 50) if allowed else (70, 50, 50)
            pygame.draw.rect(surface, bg_color, rect, border_radius=4)
            
            # Resource color indicator
            color = self.RESOURCE_COLORS.get(res_type, (150, 150, 150))
            indicator_rect = pygame.Rect(rect.x + 4, rect.y + 6, 16, 16)
            pygame.draw.rect(surface, color, indicator_rect, border_radius=2)
            
            # Resource name
            display_name = self.RESOURCE_NAMES.get(res_type, res_type.capitalize())
            name_text = self.font.render(display_name, True, (200, 200, 200))
            surface.blit(name_text, (rect.x + 26, rect.y + 6))
            
            # Status indicator
            status = "✓" if allowed else "✗"
            status_color = (100, 200, 100) if allowed else (200, 100, 100)
            status_text = self.font.render(status, True, status_color)
            surface.blit(status_text, (rect.right - 20, rect.y + 6))


# Global stockpile filter panel
_stockpile_filter_panel: Optional[StockpileFilterPanel] = None


def get_stockpile_filter_panel() -> StockpileFilterPanel:
    """Get or create the global stockpile filter panel."""
    global _stockpile_filter_panel
    if _stockpile_filter_panel is None:
        _stockpile_filter_panel = StockpileFilterPanel()
    return _stockpile_filter_panel


# ============================================================================
# Colonist Job Tags Panel
# ============================================================================

class ColonistJobTagsPanel:
    """UI panel for toggling colonist job tags."""
    
    JOB_TAGS = [
        ("can_build", "Build", "Construction, walls, floors"),
        ("can_haul", "Haul", "Move resources to stockpiles"),
        ("can_craft", "Craft", "Work at crafting benches"),
        ("can_cook", "Cook", "Prepare meals at stove"),
        ("can_scavenge", "Scavenge", "Salvage and harvest"),
    ]
    
    def __init__(self):
        self.visible = False
        self.colonist = None
        self.panel_rect = pygame.Rect(0, 0, 300, 550)  # Larger to fit environment data + affinities
        self.toggle_rects: Dict[str, pygame.Rect] = {}
        self.font: Optional[pygame.font.Font] = None
        self.show_env_data = True  # Toggle for environment data display
    
    def init_font(self) -> None:
        self.font = pygame.font.Font(None, 20)
    
    def open(self, colonist, screen_x: int, screen_y: int) -> None:
        """Open the panel for a colonist at screen position."""
        self.colonist = colonist
        self.visible = True
        
        # Position panel near click but keep on screen
        self.panel_rect.x = min(screen_x, SCREEN_W - self.panel_rect.width - 10)
        self.panel_rect.y = min(screen_y, SCREEN_H - self.panel_rect.height - 60)
        
        # Build toggle rects
        padding = 8
        item_height = 32
        for i, (tag_id, _, _) in enumerate(self.JOB_TAGS):
            rect = pygame.Rect(
                self.panel_rect.x + padding,
                self.panel_rect.y + 30 + i * item_height,
                self.panel_rect.width - padding * 2,
                item_height - 4
            )
            self.toggle_rects[tag_id] = rect
    
    def close(self) -> None:
        """Close the panel."""
        self.visible = False
        self.colonist = None
    
    def handle_click(self, mouse_pos: tuple[int, int]) -> bool:
        """Handle mouse click. Returns True if consumed."""
        if not self.visible or self.colonist is None:
            return False
        
        # Check if click is in panel
        if not self.panel_rect.collidepoint(mouse_pos):
            self.close()
            return False
        
        # Check toggle clicks
        for tag_id, rect in self.toggle_rects.items():
            if rect.collidepoint(mouse_pos):
                # Toggle the tag
                current = self.colonist.job_tags.get(tag_id, True)
                self.colonist.job_tags[tag_id] = not current
                return True
        
        return True  # Consume click even if not on a toggle
    
    def draw(self, surface: pygame.Surface) -> None:
        """Draw the panel."""
        if not self.visible or self.colonist is None:
            return
        
        if self.font is None:
            self.init_font()
        
        # Panel background with shadow
        shadow_rect = self.panel_rect.copy()
        shadow_rect.x += 3
        shadow_rect.y += 3
        pygame.draw.rect(surface, (20, 20, 25), shadow_rect, border_radius=8)
        
        # Main panel
        pygame.draw.rect(surface, COLOR_UI_PANEL, self.panel_rect, border_radius=8)
        pygame.draw.rect(surface, (100, 100, 110), self.panel_rect, 1, border_radius=8)
        
        # Title
        title_text = self.font.render("Job Tags", True, (220, 220, 230))
        title_rect = title_text.get_rect(centerx=self.panel_rect.centerx, y=self.panel_rect.y + 8)
        surface.blit(title_text, title_rect)
        
        # Draw toggles
        for tag_id, tag_name, tag_desc in self.JOB_TAGS:
            rect = self.toggle_rects[tag_id]
            enabled = self.colonist.job_tags.get(tag_id, True)
            
            # Toggle background
            bg_color = (60, 120, 80) if enabled else (80, 60, 60)
            pygame.draw.rect(surface, bg_color, rect, border_radius=4)
            pygame.draw.rect(surface, (100, 100, 110), rect, 1, border_radius=4)
            
            # Checkbox
            checkbox_size = 16
            checkbox_rect = pygame.Rect(rect.x + 6, rect.centery - checkbox_size // 2, checkbox_size, checkbox_size)
            pygame.draw.rect(surface, (40, 40, 45), checkbox_rect, border_radius=2)
            pygame.draw.rect(surface, (120, 120, 130), checkbox_rect, 1, border_radius=2)
            
            if enabled:
                # Checkmark
                pygame.draw.line(surface, (150, 255, 150), 
                               (checkbox_rect.x + 3, checkbox_rect.centery),
                               (checkbox_rect.centerx, checkbox_rect.bottom - 4), 2)
                pygame.draw.line(surface, (150, 255, 150),
                               (checkbox_rect.centerx, checkbox_rect.bottom - 4),
                               (checkbox_rect.right - 3, checkbox_rect.y + 3), 2)
            
            # Label
            label_text = self.font.render(tag_name, True, (220, 220, 230))
            label_rect = label_text.get_rect(left=checkbox_rect.right + 8, centery=rect.centery - 4)
            surface.blit(label_text, label_rect)
            
            # Description (smaller)
            font_small = pygame.font.Font(None, 16)
            desc_text = font_small.render(tag_desc, True, (150, 150, 160))
            desc_rect = desc_text.get_rect(left=checkbox_rect.right + 8, top=label_rect.bottom + 2)
            surface.blit(desc_text, desc_rect)
        
        # Draw environment data section if enabled
        if self.show_env_data and hasattr(self.colonist, 'recent_context') and len(self.colonist.recent_context) > 0:
            env_y = self.panel_rect.y + 190  # Start below job tags
            
            # Section title
            env_title = self.font.render("Environment Data", True, (200, 200, 255))
            surface.blit(env_title, (self.panel_rect.x + 10, env_y))
            env_y += 25
            
            # Get most recent sample
            recent = self.colonist.recent_context[-1]
            font_tiny = pygame.font.Font(None, 16)
            
            # Display key environment parameters
            env_params = [
                f"Tick: {recent.get('tick', 0)}",
                f"Pos: ({recent.get('x', 0)}, {recent.get('y', 0)}, {recent.get('z', 0)})",
                f"Interference: {recent.get('interference', 0.0):.2f}",
                f"Pressure: {recent.get('pressure', 0.0):.2f}",
                f"Echo: {recent.get('echo', 0.0):.2f}",
                f"Integrity: {recent.get('integrity', 1.0):.2f}",
                f"Outside: {recent.get('is_outside', True)}",
                f"Room: {recent.get('room_id', 'None')}",
                f"Exits: {recent.get('exit_count', 0)}",
                f"Nearby: {recent.get('nearby_colonists', 0)}",
            ]
            
            for param in env_params:
                param_text = font_tiny.render(param, True, (180, 180, 190))
                surface.blit(param_text, (self.panel_rect.x + 15, env_y))
                env_y += 18
            
            # Show sample count
            sample_count_text = font_tiny.render(f"Samples: {len(self.colonist.recent_context)}/10", True, (150, 150, 160))
            surface.blit(sample_count_text, (self.panel_rect.x + 15, env_y))
            env_y += 25
            
            # Draw affinity section
            affinity_title = self.font.render("Affinities", True, (255, 200, 100))
            surface.blit(affinity_title, (self.panel_rect.x + 10, env_y))
            env_y += 20
            
            # Display affinity values with color coding
            # Positive = green, Negative = red, Neutral = gray
            affinities = [
                ("Interference", self.colonist.affinity_interference),
                ("Echo", self.colonist.affinity_echo),
                ("Pressure", self.colonist.affinity_pressure),
                ("Integrity", self.colonist.affinity_integrity),
                ("Outside", self.colonist.affinity_outside),
                ("Crowding", self.colonist.affinity_crowding),
            ]
            
            for name, value in affinities:
                # Color based on value
                if value > 0.1:
                    color = (100, 255, 100)  # Green for positive
                elif value < -0.1:
                    color = (255, 100, 100)  # Red for negative
                else:
                    color = (180, 180, 180)  # Gray for neutral
                
                # Format with sign
                sign = "+" if value >= 0 else ""
                affinity_text = font_tiny.render(f"{name}: {sign}{value:.2f}", True, color)
                surface.blit(affinity_text, (self.panel_rect.x + 15, env_y))
                env_y += 16


# Compatibility layer for existing code
class ConstructionUI:
    """Wrapper for backward compatibility with existing code."""
    
    def __init__(self):
        self.action_bar = ActionBar()
    
    def init_font(self) -> None:
        self.action_bar.init_font()
    
    def get_build_mode(self) -> Optional[str]:
        return self.action_bar.get_current_tool()
    
    def cancel_build_mode(self) -> None:
        self.action_bar.cancel_tool()
    
    def update(self, mouse_pos: tuple[int, int]) -> None:
        self.action_bar.update(mouse_pos)
    
    def handle_click(self, mouse_pos: tuple[int, int], button: int) -> bool:
        return self.action_bar.handle_click(mouse_pos, button)
    
    def handle_key(self, key: int) -> bool:
        return self.action_bar.handle_key(key)
    
    def draw(self, surface: pygame.Surface) -> None:
        self.action_bar.draw(surface)


# Global UI instances
_construction_ui: Optional[ConstructionUI] = None
_colonist_panel: Optional[ColonistJobTagsPanel] = None


def get_construction_ui() -> ConstructionUI:
    """Get or create the global construction UI instance."""
    global _construction_ui
    if _construction_ui is None:
        _construction_ui = ConstructionUI()
    return _construction_ui


def get_colonist_panel() -> ColonistJobTagsPanel:
    """Get or create the global colonist panel instance."""
    global _colonist_panel
    if _colonist_panel is None:
        _colonist_panel = ColonistJobTagsPanel()
    return _colonist_panel
