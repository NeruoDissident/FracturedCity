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
    
    # Menu structure - base categories. Some entries (workstations, furniture)
    # are populated at runtime from data definitions.
    BUILD_MENU = {
        "walls": [
            {"id": "wall", "name": "Wall", "cost": "2 wood", "keybind": "1"},
            {"id": "wall_advanced", "name": "Reinforced Wall", "cost": "2 mineral", "keybind": "2"},
        ],
        "floors": [
            {"id": "floor", "name": "Wood Floor", "cost": "1 wood", "keybind": "1"},
            {"id": "roof", "name": "Roof", "cost": "free", "keybind": "2"},
        ],
        "movement": [
            {"id": "fire_escape", "name": "Fire Escape", "cost": "1 wood, 1 metal", "keybind": "1"},
            {"id": "bridge", "name": "Bridge", "cost": "2 wood, 1 metal", "keybind": "2"},
        ],
        "entrance": [
            {"id": "door", "name": "Door", "cost": "1 wood, 1 metal", "keybind": "1"},
            {"id": "window", "name": "Window", "cost": "1 wood, 1 mineral", "keybind": "2"},
        ],
        # Workstations category is populated at runtime from BUILDING_TYPES
        "workstations": [],
        # Furniture category is populated at runtime from items tagged as "furniture"
        "furniture": [],
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
    
    def _build_workstation_menu_items(self) -> None:
        """Populate the Workstations build submenu from BUILDING_TYPES.
        
        Any building definition with workstation=True will appear here. This
        makes adding new stations mostly data-only (edit buildings.py).
        """
        try:
            import buildings as buildings_module
        except ImportError:
            ActionBar.BUILD_MENU["workstations"] = []
            return
        
        ws_defs = []
        for b_id, b_def in buildings_module.BUILDING_TYPES.items():
            if not b_def.get("workstation", False):
                continue
            name = b_def.get("name", b_id)
            materials = b_def.get("materials", {}) or {}
            if materials:
                parts = [f"{amount} {res}" for res, amount in materials.items()]
                cost = ", ".join(parts)
            else:
                cost = ""
            ws_defs.append((b_id, name, cost))
        
        menu_items: List[dict] = []
        for idx, (b_id, display_name, cost) in enumerate(ws_defs):
            keybind = str(idx + 1) if idx < 9 else ""
            menu_items.append({
                "id": b_id,
                "name": display_name,
                "cost": cost,
                "keybind": keybind,
            })
        
        ActionBar.BUILD_MENU["workstations"] = menu_items
    
    def _build_furniture_menu_items(self) -> None:
        """Populate the Furniture build submenu from items tagged as furniture.
        
        Each furniture item becomes a tool id of the form "furn_<item_id>" so
        placement logic can treat all furniture generically.
        """
        try:
            import items as items_module
        except ImportError:
            # If items registry is not available yet, leave furniture menu empty
            ActionBar.BUILD_MENU["furniture"] = []
            return
        
        furniture_defs = items_module.get_items_with_tag("furniture")
        if not furniture_defs:
            ActionBar.BUILD_MENU["furniture"] = []
            return
        
        # Stable ordering by display name
        furniture_defs = sorted(furniture_defs, key=lambda d: d.name)
        menu_items = []
        for idx, item_def in enumerate(furniture_defs):
            keybind = str(idx + 1) if idx < 9 else ""
            menu_items.append({
                "id": f"furn_{item_def.id}",
                "name": item_def.name,
                "cost": "From stockpile",
                "keybind": keybind,
            })
        
        ActionBar.BUILD_MENU["furniture"] = menu_items
    
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
        
        # Build category submenu (Walls, Floors, Movement, Entrance, Workstations, Furniture)
        build_categories = [
            {"id": "walls", "name": "Walls", "keybind": "1"},
            {"id": "floors", "name": "Floors", "keybind": "2"},
            {"id": "movement", "name": "Movement", "keybind": "3"},
            {"id": "entrance", "name": "Entrance", "keybind": "4"},
            {"id": "workstations", "name": "Workstations", "keybind": "5"},
            {"id": "furniture", "name": "Furniture", "keybind": "6"},
        ]
        self.submenus["build"] = SubMenu(build_categories, self.main_buttons["build"])
        
        # Zone submenu
        self.submenus["zone"] = SubMenu(self.ZONE_MENU, self.main_buttons["zone"])
        
        # Build sub-submenus (one for each category)
        # Populate dynamic menus (workstations, furniture) from data definitions
        self._build_workstation_menu_items()
        self._build_furniture_menu_items()
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
        if key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5, pygame.K_6):
            num = key - pygame.K_1  # 0-based index
            
            if self.active_menu == "build" and self.active_submenu is None:
                # Select build category
                categories = ["walls", "floors", "movement", "entrance", "workstations", "furniture"]
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
    
    RESOURCE_TYPES = ["wood", "mineral", "scrap", "metal", "power", "raw_food", "cooked_meal", "equipment"]
    RESOURCE_COLORS = {
        "wood": (139, 90, 43),
        "mineral": (80, 200, 200),
        "scrap": (120, 120, 120),
        "metal": (180, 180, 200),
        "power": (255, 220, 80),
        "raw_food": (180, 220, 100),
        "cooked_meal": (220, 160, 80),
        "equipment": (160, 140, 200),
    }
    RESOURCE_NAMES = {
        "wood": "Wood",
        "mineral": "Mineral",
        "scrap": "Scrap",
        "metal": "Metal",
        "power": "Power",
        "raw_food": "Raw Food",
        "cooked_meal": "Meal",
        "equipment": "Equipment & Furniture",
    }
    
    def __init__(self):
        self.visible = False
        self.zone_id: Optional[int] = None
        self.zone_info: Optional[dict] = None
        self.panel_rect = pygame.Rect(0, 0, 180, 290)  # Taller for more items
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
# Workstation Panel - Recipe selection and crafting info
# ============================================================================

class WorkstationPanel:
    """UI panel for viewing/selecting workstation recipes."""
    
    def __init__(self):
        self.visible = False
        self.workstation_pos: Optional[tuple[int, int, int]] = None
        self.workstation_data: Optional[dict] = None
        self.recipes: list[dict] = []
        self.panel_rect = pygame.Rect(0, 0, 280, 320)
        self.recipe_rects: list[pygame.Rect] = []
        self.font: Optional[pygame.font.Font] = None
        self.font_small: Optional[pygame.font.Font] = None
        # Order control button rects (set during draw)
        self.button_craft_one_rect: Optional[pygame.Rect] = None
        self.button_auto_rect: Optional[pygame.Rect] = None
        self.target_minus_rect: Optional[pygame.Rect] = None
        self.target_plus_rect: Optional[pygame.Rect] = None
    
    def init_font(self) -> None:
        self.font = pygame.font.Font(None, 24)
        self.font_small = pygame.font.Font(None, 20)
    
    def open(self, x: int, y: int, z: int, screen_x: int, screen_y: int) -> None:
        """Open the workstation panel."""
        import buildings
        
        self.workstation_pos = (x, y, z)
        self.workstation_data = buildings.get_workstation(x, y, z)
        if self.workstation_data is None:
            return
        
        self.recipes = buildings.get_workstation_recipes(x, y, z)
        self.visible = True
        
        # Dynamically adjust panel height based on recipe count so nothing is squished
        base_height = 220  # Minimum height for title + status + orders
        if self.recipes:
            # Each recipe row uses ~65px vertical space, starting after ~50px header
            num_recipes = len(self.recipes)
            recipes_block = 110 + max(0, num_recipes - 1) * 65  # first row + spacing
            bottom_margin = 90  # Space for Orders strip + status text
            needed_height = recipes_block + bottom_margin
            # Clamp to screen height with some safety margin from bottom
            max_height = SCREEN_H - 80
            self.panel_rect.height = max(base_height, min(needed_height, max_height))
        else:
            self.panel_rect.height = base_height
        
        # Position panel near click but keep on screen after resizing
        self.panel_rect.x = min(screen_x + 10, SCREEN_W - self.panel_rect.width - 10)
        self.panel_rect.y = min(screen_y, SCREEN_H - self.panel_rect.height - 60)
        
        self._build_recipe_rects()
    
    def _build_recipe_rects(self) -> None:
        """Build clickable rectangles for each recipe."""
        self.recipe_rects.clear()
        y = self.panel_rect.y + 50
        for _ in self.recipes:
            self.recipe_rects.append(pygame.Rect(
                self.panel_rect.x + 10, y, self.panel_rect.width - 20, 60
            ))
            y += 65
    
    def close(self) -> None:
        """Close the panel."""
        self.visible = False
        self.workstation_pos = None
        self.workstation_data = None
        self.recipes = []
        self.button_craft_one_rect = None
        self.button_auto_rect = None
        self.target_minus_rect = None
        self.target_plus_rect = None
    
    def handle_click(self, mouse_pos: tuple[int, int]) -> bool:
        """Handle click. Returns True if consumed."""
        if not self.visible:
            return False
        
        # Click outside panel closes it
        if not self.panel_rect.collidepoint(mouse_pos):
            self.close()
            return True
        
        # Check recipe selection
        import buildings
        for i, rect in enumerate(self.recipe_rects):
            if rect.collidepoint(mouse_pos) and i < len(self.recipes):
                recipe = self.recipes[i]
                if self.workstation_pos:
                    x, y, z = self.workstation_pos
                    buildings.set_workstation_recipe(x, y, z, recipe["id"])
                    print(f"[Workstation] Selected: {recipe['name']}")
                    # Refresh data
                    self.workstation_data = buildings.get_workstation(x, y, z)
                return True
        
        # Order controls (Craft 1 / Auto / Target)
        ws = self.workstation_data
        if ws is not None:
            # Craft 1 - enqueue a single crafting job for the selected recipe
            if self.button_craft_one_rect and self.button_craft_one_rect.collidepoint(mouse_pos):
                ws["craft_queue"] = ws.get("craft_queue", 0) + 1
                return True
            
            # Toggle auto mode between infinite and target
            if self.button_auto_rect and self.button_auto_rect.collidepoint(mouse_pos):
                current_mode = ws.get("auto_mode", "infinite")
                ws["auto_mode"] = "target" if current_mode == "infinite" else "infinite"
                return True
            
            # Adjust target count (used when auto_mode == "target")
            if self.target_minus_rect and self.target_minus_rect.collidepoint(mouse_pos):
                current = ws.get("target_count", 0)
                ws["target_count"] = max(0, current - 1)
                # If we have a non-zero target, ensure mode is target
                if ws["target_count"] > 0:
                    ws["auto_mode"] = "target"
                return True
            if self.target_plus_rect and self.target_plus_rect.collidepoint(mouse_pos):
                current = ws.get("target_count", 0)
                ws["target_count"] = min(99, current + 1)
                ws["auto_mode"] = "target"
                return True
        
        return True  # Consume click on panel
    
    def draw(self, surface: pygame.Surface) -> None:
        """Draw the workstation panel."""
        if not self.visible or self.workstation_data is None:
            return
        
        if self.font is None:
            self.init_font()
        
        import buildings
        from items import get_item_def
        
        # Panel background
        pygame.draw.rect(surface, (30, 35, 45), self.panel_rect)
        pygame.draw.rect(surface, (80, 90, 100), self.panel_rect, 2)
        
        # Title
        ws_type = self.workstation_data.get("type", "Workstation")
        building_def = buildings.BUILDING_TYPES.get(ws_type, {})
        title = building_def.get("name", ws_type.replace("_", " ").title())
        title_surf = self.font.render(title, True, (220, 220, 230))
        surface.blit(title_surf, (self.panel_rect.x + 10, self.panel_rect.y + 10))
        
        # Current recipe indicator
        selected_id = self.workstation_data.get("selected_recipe")
        
        # Draw recipes
        for i, (recipe, rect) in enumerate(zip(self.recipes, self.recipe_rects)):
            is_selected = recipe["id"] == selected_id
            
            # Background
            bg_color = (50, 60, 70) if is_selected else (40, 45, 55)
            pygame.draw.rect(surface, bg_color, rect)
            border_color = (100, 180, 100) if is_selected else (60, 70, 80)
            pygame.draw.rect(surface, border_color, rect, 2 if is_selected else 1)
            
            # Recipe name
            name_color = (180, 220, 180) if is_selected else (180, 180, 190)
            name_surf = self.font.render(recipe["name"], True, name_color)
            surface.blit(name_surf, (rect.x + 8, rect.y + 5))
            
            # Cost line
            inputs = recipe.get("input", {})
            cost_parts = [f"{amt} {res}" for res, amt in inputs.items()]
            cost_text = "Cost: " + ", ".join(cost_parts) if cost_parts else "Cost: Free"
            cost_surf = self.font_small.render(cost_text, True, (140, 140, 150))
            surface.blit(cost_surf, (rect.x + 8, rect.y + 24))
            
            # Effect line - get from item definition
            output_item = recipe.get("output_item")
            if output_item:
                item_def = get_item_def(output_item)
                if item_def:
                    effects = []
                    if item_def.speed_bonus != 0:
                        effects.append(f"Speed {item_def.speed_bonus:+.0%}")
                    if item_def.work_bonus != 0:
                        effects.append(f"Work {item_def.work_bonus:+.0%}")
                    if item_def.comfort != 0:
                        effects.append(f"Comfort {item_def.comfort:+.2f}")
                    if item_def.hazard_resist != 0:
                        effects.append(f"Hazard {item_def.hazard_resist:+.0%}")
                    
                    effect_text = ", ".join(effects) if effects else f"Slot: {item_def.slot}"
                    effect_color = (100, 180, 220)
                else:
                    effect_text = f"Creates: {output_item}"
                    effect_color = (140, 140, 150)
            else:
                # Resource output
                outputs = recipe.get("output", {})
                output_parts = [f"{amt} {res}" for res, amt in outputs.items()]
                effect_text = "→ " + ", ".join(output_parts) if output_parts else ""
                effect_color = (180, 180, 100)
            
            effect_surf = self.font_small.render(effect_text, True, effect_color)
            surface.blit(effect_surf, (rect.x + 8, rect.y + 42))
        
        # Status at bottom
        progress = self.workstation_data.get("progress", 0)
        if progress > 0 and selected_id:
            # Find work time for selected recipe
            for recipe in self.recipes:
                if recipe["id"] == selected_id:
                    work_time = recipe.get("work_time", 100)
                    pct = min(100, int(progress / work_time * 100))
                    status = f"Crafting: {pct}%"
                    break
            else:
                status = "Idle"
        else:
            status = "Click recipe to select"
        
        status_y = self.panel_rect.bottom - 25
        status_surf = self.font_small.render(status, True, (140, 160, 180))
        surface.blit(status_surf, (self.panel_rect.x + 10, status_y))

        # Orders controls (Craft 1 / Auto / Target)
        # Reset button rects each frame
        self.button_craft_one_rect = None
        self.button_auto_rect = None
        self.target_minus_rect = None
        self.target_plus_rect = None

        # Only show order controls if there is at least one recipe
        if self.recipes:
            ws = self.workstation_data
            auto_mode = ws.get("auto_mode", "infinite")
            target_count = ws.get("target_count", 0)
            craft_queue = ws.get("craft_queue", 0)

            orders_y = self.panel_rect.bottom - 70
            label_surf = self.font_small.render("Orders:", True, (150, 160, 190))
            surface.blit(label_surf, (self.panel_rect.x + 10, orders_y))

            btn_w = 70
            btn_h = 20
            y_btn = orders_y + 18

            # Craft 1 button
            craft_rect = pygame.Rect(self.panel_rect.x + 10, y_btn, btn_w, btn_h)
            self.button_craft_one_rect = craft_rect
            pygame.draw.rect(surface, (60, 70, 80), craft_rect)
            pygame.draw.rect(surface, (100, 110, 130), craft_rect, 1)
            craft_label = self.font_small.render("Craft 1", True, (220, 225, 230))
            surface.blit(craft_label, (craft_rect.x + 6, craft_rect.y + 2))

            # Show queued count if any
            if craft_queue > 0:
                queue_text = f"x{craft_queue}"
                queue_surf = self.font_small.render(queue_text, True, (170, 190, 210))
                surface.blit(queue_surf, (craft_rect.right + 4, craft_rect.y + 2))

            # Auto-mode button
            auto_rect = pygame.Rect(craft_rect.right + 10, y_btn, btn_w, btn_h)
            self.button_auto_rect = auto_rect
            auto_active = (auto_mode == "infinite")
            auto_bg = (70, 90, 70) if auto_active else (60, 70, 80)
            auto_border = (120, 180, 120) if auto_active else (100, 110, 130)
            pygame.draw.rect(surface, auto_bg, auto_rect)
            pygame.draw.rect(surface, auto_border, auto_rect, 1)
            auto_text = "∞ Auto" if auto_mode == "infinite" else "Target"
            auto_label = self.font_small.render(auto_text, True, (220, 230, 220))
            surface.blit(auto_label, (auto_rect.x + 6, auto_rect.y + 2))

            # Target controls
            target_label = self.font_small.render("Target:", True, (150, 160, 190))
            target_label_x = auto_rect.right + 10
            surface.blit(target_label, (target_label_x, orders_y + 2))

            minus_rect = pygame.Rect(target_label_x, y_btn, 18, btn_h)
            plus_rect = pygame.Rect(target_label_x + 60, y_btn, 18, btn_h)
            self.target_minus_rect = minus_rect
            self.target_plus_rect = plus_rect

            # Minus button
            pygame.draw.rect(surface, (60, 70, 80), minus_rect)
            pygame.draw.rect(surface, (100, 110, 130), minus_rect, 1)
            minus_label = self.font_small.render("-", True, (220, 225, 230))
            surface.blit(minus_label, (minus_rect.x + 5, minus_rect.y + 2))

            # Plus button
            pygame.draw.rect(surface, (60, 70, 80), plus_rect)
            pygame.draw.rect(surface, (100, 110, 130), plus_rect, 1)
            plus_label = self.font_small.render("+", True, (220, 225, 230))
            surface.blit(plus_label, (plus_rect.x + 4, plus_rect.y + 2))

            # Target value between buttons
            value_text = str(target_count)
            value_surf = self.font_small.render(value_text, True, (200, 210, 230))
            value_x = minus_rect.right + 8
            value_y = y_btn + 2
            surface.blit(value_surf, (value_x, value_y))


# Global workstation panel
_workstation_panel: Optional[WorkstationPanel] = None


def get_workstation_panel() -> WorkstationPanel:
    """Get or create the global workstation panel."""
    global _workstation_panel
    if _workstation_panel is None:
        _workstation_panel = WorkstationPanel()
    return _workstation_panel


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
        self.panel_rect = pygame.Rect(0, 0, 280, 700)  # Compact panel with scrollable content
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
        
        # Build toggle rects (offset by compact identity section)
        padding = 6
        item_height = 26
        identity_offset = 100  # Compact identity section
        for i, (tag_id, _, _) in enumerate(self.JOB_TAGS):
            rect = pygame.Rect(
                self.panel_rect.x + padding,
                self.panel_rect.y + identity_offset + 20 + i * item_height,
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
        
        # --- Compact Identity Section (top of panel) ---
        identity_y = self.panel_rect.y + 6
        font_tiny = pygame.font.Font(None, 15)
        
        # Colonist name (highlighted)
        name = getattr(self.colonist, 'name', 'Unknown')
        name_font = pygame.font.Font(None, 20)
        name_text = name_font.render(name, True, (255, 220, 150))
        surface.blit(name_text, (self.panel_rect.x + 8, identity_y))
        identity_y += 18
        
        # Bio (compact, max 2 lines)
        bio = getattr(self.colonist, 'bio', '')
        if bio:
            bio_color = (160, 160, 180)
            max_width = self.panel_rect.width - 16
            words = bio.split()
            lines = []
            current_line = ""
            for word in words:
                test_line = current_line + " " + word if current_line else word
                if font_tiny.size(test_line)[0] <= max_width:
                    current_line = test_line
                else:
                    if current_line:
                        lines.append(current_line)
                    current_line = word
            if current_line:
                lines.append(current_line)
            
            for line in lines[:2]:  # Max 2 lines
                bio_text = font_tiny.render(line, True, bio_color)
                surface.blit(bio_text, (self.panel_rect.x + 8, identity_y))
                identity_y += 12
        
        # Compact likes/dislikes on same line if short
        flavor_likes = getattr(self.colonist, 'flavor_likes', [])
        flavor_dislikes = getattr(self.colonist, 'flavor_dislikes', [])
        
        if flavor_likes:
            # Just show first like
            like_text = font_tiny.render(f"♥ {flavor_likes[0][:25]}", True, (120, 170, 120))
            surface.blit(like_text, (self.panel_rect.x + 8, identity_y))
            identity_y += 11
        
        if flavor_dislikes:
            # Just show first dislike
            dislike_text = font_tiny.render(f"✗ {flavor_dislikes[0][:25]}", True, (170, 120, 120))
            surface.blit(dislike_text, (self.panel_rect.x + 8, identity_y))
            identity_y += 11
        
        identity_y += 2
        
        # Separator line
        pygame.draw.line(surface, (70, 70, 80), 
                        (self.panel_rect.x + 8, identity_y),
                        (self.panel_rect.x + self.panel_rect.width - 8, identity_y), 1)
        identity_y += 4
        
        # --- Job Tags Section ---
        title_text = self.font.render("Job Tags", True, (200, 200, 210))
        surface.blit(title_text, (self.panel_rect.x + 8, identity_y))
        
        # Draw toggles (offset by identity section height)
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
            env_y = self.panel_rect.y + 240  # Start below compact identity + job tags
            
            # Section title
            font_tiny = pygame.font.Font(None, 14)
            env_title = font_tiny.render("Environment", True, (180, 180, 220))
            surface.blit(env_title, (self.panel_rect.x + 8, env_y))
            env_y += 14
            
            # Get most recent sample - compact display
            recent = self.colonist.recent_context[-1]
            
            # Two columns for compact display
            col1 = [
                f"Int:{recent.get('interference', 0.0):.1f}",
                f"Prs:{recent.get('pressure', 0.0):.1f}",
                f"Ech:{recent.get('echo', 0.0):.1f}",
            ]
            col2 = [
                f"Itg:{recent.get('integrity', 1.0):.1f}",
                f"Out:{'Y' if recent.get('is_outside', True) else 'N'}",
                f"Crw:{recent.get('nearby_colonists', 0)}",
            ]
            
            for i, (c1, c2) in enumerate(zip(col1, col2)):
                t1 = font_tiny.render(c1, True, (160, 160, 170))
                t2 = font_tiny.render(c2, True, (160, 160, 170))
                surface.blit(t1, (self.panel_rect.x + 8, env_y))
                surface.blit(t2, (self.panel_rect.x + 80, env_y))
                env_y += 11
            
            env_y += 4
            
            # Affinities - compact
            aff_title = font_tiny.render("Affinities", True, (220, 180, 100))
            surface.blit(aff_title, (self.panel_rect.x + 8, env_y))
            env_y += 12
            
            affinities = [
                ("Int", self.colonist.affinity_interference),
                ("Ech", self.colonist.affinity_echo),
                ("Prs", self.colonist.affinity_pressure),
                ("Itg", self.colonist.affinity_integrity),
                ("Out", self.colonist.affinity_outside),
                ("Crw", self.colonist.affinity_crowding),
            ]
            
            # Display in two rows of 3
            for row in range(2):
                x_off = 8
                for col in range(3):
                    idx = row * 3 + col
                    if idx < len(affinities):
                        name, value = affinities[idx]
                        color = (100, 220, 100) if value > 0.1 else (220, 100, 100) if value < -0.1 else (150, 150, 150)
                        sign = "+" if value >= 0 else ""
                        aff_text = font_tiny.render(f"{name}:{sign}{value:.1f}", True, color)
                        surface.blit(aff_text, (self.panel_rect.x + x_off, env_y))
                        x_off += 55
                env_y += 11
            
            env_y += 4
            
            # Preferences - compact
            pref_title = font_tiny.render("Preferences", True, (100, 180, 220))
            surface.blit(pref_title, (self.panel_rect.x + 8, env_y))
            env_y += 12
            
            # Get top preferences - compact inline
            if hasattr(self.colonist, 'get_top_preferences'):
                top_positive, top_negative = self.colonist.get_top_preferences()
                prefs_text = ""
                if top_positive:
                    prefs_text += " ".join([f"+{p[0].replace('likes_','')[:3]}" for p in top_positive[:2]])
                if top_negative:
                    prefs_text += " " + " ".join([f"-{p[0].replace('likes_','')[:3]}" for p in top_negative[:1]])
                if prefs_text:
                    pt = font_tiny.render(prefs_text.strip(), True, (150, 180, 150))
                    surface.blit(pt, (self.panel_rect.x + 8, env_y))
                else:
                    pt = font_tiny.render("(developing)", True, (120, 120, 120))
                    surface.blit(pt, (self.panel_rect.x + 8, env_y))
                env_y += 12
            
            env_y += 4
            
            # Emotional state - compact
            emo_title = font_tiny.render("Mood", True, (220, 160, 200))
            surface.blit(emo_title, (self.panel_rect.x + 8, env_y))
            env_y += 12
            
            # Comfort/Stress on one line
            comfort_val = getattr(self.colonist, 'comfort', 0.0)
            stress_val = getattr(self.colonist, 'stress', 0.0)
            c_color = (100, 200, 100) if comfort_val > 1 else (200, 100, 100) if comfort_val < -1 else (150, 150, 150)
            s_color = (200, 100, 100) if stress_val > 1 else (100, 200, 100) if stress_val < -1 else (150, 150, 150)
            
            cs_text = font_tiny.render(f"C:{comfort_val:+.1f} S:{stress_val:+.1f}", True, (160, 160, 170))
            surface.blit(cs_text, (self.panel_rect.x + 8, env_y))
            
            # Mood state
            mood_state = getattr(self.colonist, 'mood_state', 'Focused')
            from colonist import Colonist
            mood_color = Colonist.get_mood_color(mood_state)
            mood_text = font_tiny.render(mood_state, True, mood_color)
            surface.blit(mood_text, (self.panel_rect.x + 90, env_y))
            env_y += 11
            
            # Speed mod
            if hasattr(self.colonist, 'get_mood_speed_display'):
                speed_mod = self.colonist.get_mood_speed_display()
                sp_color = (100, 200, 100) if speed_mod.startswith("+") else (200, 100, 100) if speed_mod.startswith("-") else (150, 150, 150)
                sp_text = font_tiny.render(f"Speed:{speed_mod}", True, sp_color)
                surface.blit(sp_text, (self.panel_rect.x + 8, env_y))
                env_y += 12
            
            env_y += 4
            
            # Job attraction - compact two-column
            job_title = font_tiny.render("Jobs", True, (220, 200, 130))
            surface.blit(job_title, (self.panel_rect.x + 8, env_y))
            env_y += 12
            
            if hasattr(self.colonist, 'get_job_desirability_summary'):
                desirability = self.colonist.get_job_desirability_summary()
                sorted_jobs = sorted(desirability.items(), key=lambda x: x[1], reverse=True)
                
                # Two columns
                for row in range(3):
                    x_off = 8
                    for col in range(2):
                        idx = row * 2 + col
                        if idx < len(sorted_jobs):
                            job_cat, score = sorted_jobs[idx]
                            jc = (100, 200, 100) if score > 1.1 else (200, 100, 100) if score < 0.9 else (150, 150, 150)
                            jt = font_tiny.render(f"{job_cat[:4]}:{score:.1f}", True, jc)
                            surface.blit(jt, (self.panel_rect.x + x_off, env_y))
                            x_off += 70
                    env_y += 10


# ============================================================================
# Colonist Management Panel (Full-screen detailed view)
# ============================================================================

class ColonistManagementPanel:
    """Large UI panel showing detailed colonist information with equipment slots and job tags."""
    
    # Job tags for toggling work assignments
    JOB_TAGS = [
        ("can_build", "Build", "Construction"),
        ("can_haul", "Haul", "Transport"),
        ("can_craft", "Craft", "Workbenches"),
        ("can_cook", "Cook", "Meals"),
        ("can_scavenge", "Scavenge", "Harvest"),
    ]
    
    # Tab definitions
    TABS = ["Overview", "Bio", "Relations", "Stats", "Thoughts", "Chat", "Help"]
    
    def __init__(self):
        self.visible = False
        self.colonists: List = []  # Reference to all colonists
        self.current_index = 0  # Currently viewed colonist index
        self.current_tab = 0  # 0 = Overview, 1 = Stats
        self.font: Optional[pygame.font.Font] = None
        self.font_large: Optional[pygame.font.Font] = None
        self.font_small: Optional[pygame.font.Font] = None
        
        # Panel dimensions - larger with external tab sidebar
        self.tab_sidebar_width = 80
        self.panel_width = 520
        self.panel_height = 680
        
        # Total width includes sidebar
        total_width = self.tab_sidebar_width + self.panel_width
        
        # Center the whole thing
        self.sidebar_rect = pygame.Rect(
            (SCREEN_W - total_width) // 2,
            (SCREEN_H - self.panel_height) // 2 - 20,
            self.tab_sidebar_width,
            self.panel_height
        )
        self.panel_rect = pygame.Rect(
            self.sidebar_rect.right,
            self.sidebar_rect.y,
            self.panel_width,
            self.panel_height
        )
        
        # Navigation button rects
        self.prev_btn_rect = pygame.Rect(0, 0, 70, 30)
        self.next_btn_rect = pygame.Rect(0, 0, 70, 30)
        self.close_btn_rect = pygame.Rect(0, 0, 28, 28)
        
        # Tab button rects (built dynamically)
        self.tab_rects: List[pygame.Rect] = []
        
        # Job tag toggle rects (built dynamically)
        self.job_tag_rects: Dict[str, pygame.Rect] = {}
        
        # Equipment slot rects for tooltip (built during draw)
        self.equipment_slot_rects: Dict[str, tuple[pygame.Rect, dict]] = {}
        
        # Tooltip state
        self.tooltip_item: Optional[dict] = None
        self.tooltip_pos: tuple[int, int] = (0, 0)
    
    def init_font(self) -> None:
        self.font = pygame.font.Font(None, 20)
        self.font_large = pygame.font.Font(None, 28)
        self.font_small = pygame.font.Font(None, 16)
    
    def open(self, colonists: List, start_index: int = 0) -> None:
        """Open the panel with a list of colonists."""
        self.colonists = colonists
        self.current_index = max(0, min(start_index, len(colonists) - 1))
        self.visible = True
        self._update_button_positions()
    
    def open_for_colonist(self, colonists: List, colonist) -> None:
        """Open the panel focused on a specific colonist."""
        self.colonists = colonists
        try:
            self.current_index = colonists.index(colonist)
        except ValueError:
            self.current_index = 0
        self.visible = True
        self._update_button_positions()
    
    def close(self) -> None:
        self.visible = False
        self.tooltip_item = None
    
    def toggle(self, colonists: List) -> None:
        """Toggle panel visibility."""
        if self.visible:
            self.close()
        else:
            self.open(colonists)
    
    def update(self, mouse_pos: tuple[int, int]) -> None:
        """Update tooltip based on mouse position."""
        if not self.visible or self.current_tab != 0:  # Only Overview tab has equipment
            self.tooltip_item = None
            return
        
        # Check if mouse is over any equipment slot
        self.tooltip_item = None
        for slot_key, (rect, item) in self.equipment_slot_rects.items():
            if rect.collidepoint(mouse_pos) and item:
                self.tooltip_item = item
                self.tooltip_pos = (mouse_pos[0] + 15, mouse_pos[1] + 10)
                break
    
    def _update_button_positions(self) -> None:
        """Update button positions based on panel rect."""
        # Prev/Next at bottom
        self.prev_btn_rect.x = self.panel_rect.x + 20
        self.prev_btn_rect.y = self.panel_rect.bottom - 40
        self.next_btn_rect.x = self.panel_rect.right - 80
        self.next_btn_rect.y = self.panel_rect.bottom - 40
        # Close button top-right
        self.close_btn_rect.x = self.panel_rect.right - 32
        self.close_btn_rect.y = self.panel_rect.y + 8
    
    def handle_click(self, mouse_pos: tuple[int, int]) -> bool:
        """Handle mouse click. Returns True if consumed."""
        if not self.visible:
            return False
        
        # Check close button
        if self.close_btn_rect.collidepoint(mouse_pos):
            self.close()
            return True
        
        # Check tab buttons
        for i, rect in enumerate(self.tab_rects):
            if rect.collidepoint(mouse_pos):
                self.current_tab = i
                return True
        
        # Check prev button
        if self.prev_btn_rect.collidepoint(mouse_pos):
            self._prev_colonist()
            return True
        
        # Check next button
        if self.next_btn_rect.collidepoint(mouse_pos):
            self._next_colonist()
            return True
        
        # Check job tag toggles (only on Overview tab)
        if self.current_tab == 0:
            colonist = self.current_colonist
            if colonist:
                for tag_id, rect in self.job_tag_rects.items():
                    if rect.collidepoint(mouse_pos):
                        # Toggle the job tag
                        current = colonist.job_tags.get(tag_id, True)
                        colonist.job_tags[tag_id] = not current
                        return True
        
        # Consume click if inside panel or sidebar
        if self.panel_rect.collidepoint(mouse_pos) or self.sidebar_rect.collidepoint(mouse_pos):
            return True
        
        return False
    
    def _prev_colonist(self) -> None:
        if self.colonists:
            self.current_index = (self.current_index - 1) % len(self.colonists)
    
    def _next_colonist(self) -> None:
        if self.colonists:
            self.current_index = (self.current_index + 1) % len(self.colonists)
    
    @property
    def current_colonist(self):
        """Get the currently selected colonist."""
        if self.colonists and 0 <= self.current_index < len(self.colonists):
            return self.colonists[self.current_index]
        return None
    
    def draw(self, surface: pygame.Surface) -> None:
        """Draw the management panel."""
        if not self.visible or not self.colonists:
            return
        
        if self.font is None:
            self.init_font()
        
        colonist = self.current_colonist
        if colonist is None:
            return
        
        # === Draw Tab Sidebar (external, left of main panel) ===
        sx = self.sidebar_rect.x
        sy = self.sidebar_rect.y
        sw = self.sidebar_rect.width
        sh = self.sidebar_rect.height
        
        # Sidebar background
        pygame.draw.rect(surface, (28, 30, 38), self.sidebar_rect, border_radius=8)
        pygame.draw.rect(surface, (50, 55, 65), self.sidebar_rect, 1, border_radius=8)
        
        # Tab buttons in sidebar
        tab_height = 32
        tab_gap = 6
        tab_start_y = sy + 60
        self.tab_rects = []
        
        for i, tab_name in enumerate(self.TABS):
            tab_y = tab_start_y + i * (tab_height + tab_gap)
            tab_rect = pygame.Rect(sx + 6, tab_y, sw - 12, tab_height)
            self.tab_rects.append(tab_rect)
            
            is_active = (i == self.current_tab)
            if is_active:
                bg_color = (60, 70, 90)
                border_color = (100, 120, 160)
                text_color = (240, 240, 255)
                # Draw connector to main panel
                pygame.draw.rect(surface, bg_color, 
                               pygame.Rect(sx + sw - 4, tab_y + 4, 8, tab_height - 8))
            else:
                bg_color = (38, 42, 52)
                border_color = (55, 60, 70)
                text_color = (140, 145, 160)
            
            pygame.draw.rect(surface, bg_color, tab_rect, border_radius=4)
            pygame.draw.rect(surface, border_color, tab_rect, 1, border_radius=4)
            
            tab_surf = self.font.render(tab_name, True, text_color)
            tab_text_rect = tab_surf.get_rect(center=tab_rect.center)
            surface.blit(tab_surf, tab_text_rect)
        
        # === Draw Main Panel ===
        # Shadow
        shadow_rect = self.panel_rect.copy()
        shadow_rect.x += 4
        shadow_rect.y += 4
        pygame.draw.rect(surface, (15, 15, 20), shadow_rect, border_radius=10)
        
        # Main panel background
        pygame.draw.rect(surface, (40, 44, 52), self.panel_rect, border_radius=10)
        pygame.draw.rect(surface, (70, 75, 85), self.panel_rect, 2, border_radius=10)
        
        x = self.panel_rect.x
        y = self.panel_rect.y
        w = self.panel_rect.width
        h = self.panel_rect.height
        
        # === Header Section ===
        # Colonist name (large)
        name = getattr(colonist, 'name', f'Colonist {self.current_index + 1}')
        name_surf = self.font_large.render(name, True, (255, 230, 180))
        surface.blit(name_surf, (x + 20, y + 15))
        
        # Colonist counter
        counter_text = f"{self.current_index + 1} / {len(self.colonists)}"
        counter_surf = self.font_small.render(counter_text, True, (140, 140, 150))
        surface.blit(counter_surf, (x + 20, y + 42))
        
        # Close button
        pygame.draw.rect(surface, (80, 50, 50), self.close_btn_rect, border_radius=4)
        pygame.draw.rect(surface, (120, 70, 70), self.close_btn_rect, 1, border_radius=4)
        close_text = self.font.render("X", True, (200, 150, 150))
        close_rect = close_text.get_rect(center=self.close_btn_rect.center)
        surface.blit(close_text, close_rect)
        
        # Header separator
        pygame.draw.line(surface, (60, 65, 75), (x + 15, y + 55), (x + w - 15, y + 55), 1)
        
        # Content area - full width now (no internal tabs)
        content_y = y + 62
        content_h = h - 115  # Leave room for nav buttons
        content_w = w - 40  # Full width minus padding
        col1_x = x + 20
        col2_x = x + w // 2 + 10  # Right column for Overview
        
        # Store content bounds for clipping
        self._content_bottom = content_y + content_h - 10
        
        # Draw tab content
        if self.current_tab == 0:
            self._draw_overview_tab(surface, colonist, x, content_y, content_w, col1_x, col2_x)
        elif self.current_tab == 1:
            self._draw_bio_tab(surface, colonist, x, content_y, content_w, col1_x)
        elif self.current_tab == 2:
            self._draw_relations_tab(surface, colonist, x, content_y, content_w, col1_x)
        elif self.current_tab == 3:
            self._draw_stats_tab(surface, colonist, x, content_y, content_w, col1_x)
        elif self.current_tab == 4:
            self._draw_thoughts_tab(surface, colonist, x, content_y, content_w, col1_x)
        elif self.current_tab == 5:
            self._draw_chat_tab(surface, colonist, x, content_y, content_w, col1_x)
        elif self.current_tab == 6:
            self._draw_help_tab(surface, x, content_y, content_w, col1_x)
        
        # Draw navigation buttons (shared by all tabs)
        self._draw_navigation_buttons(surface)
        
        # Draw tooltip last (on top of everything)
        self._draw_equipment_tooltip(surface)
    
    def _draw_overview_tab(self, surface, colonist, x: int, content_y: int, w: int, col1_x: int, col2_x: int) -> None:
        """Draw the Overview tab content."""
        # Save initial content_y for right column
        initial_content_y = content_y
        
        # === Left Column: Status & Stats ===
        section_color = (180, 200, 220)
        value_color = (220, 220, 230)
        muted_color = (140, 140, 150)
        
        # Current Task
        self._draw_section_header(surface, "Current Task", col1_x, content_y, section_color)
        content_y += 18
        
        state = colonist.state
        job_desc = state
        if colonist.current_job:
            job_type = colonist.current_job.type
            job_desc = f"{state} ({job_type})"
        task_surf = self.font_small.render(job_desc[:28], True, value_color)
        surface.blit(task_surf, (col1_x + 8, content_y))
        content_y += 22
        
        # Hunger
        self._draw_section_header(surface, "Hunger", col1_x, content_y, section_color)
        content_y += 16
        hunger_val = colonist.hunger
        hunger_color = (100, 200, 100) if hunger_val < 50 else (200, 200, 100) if hunger_val < 70 else (200, 100, 100)
        bar_width = min(140, w // 2 - 60)
        self._draw_stat_bar(surface, col1_x + 8, content_y, bar_width, hunger_val, 100, hunger_color)
        content_y += 20
        
        # Comfort
        self._draw_section_header(surface, "Comfort", col1_x, content_y, section_color)
        content_y += 16
        comfort_val = getattr(colonist, 'comfort', 0.0)
        comfort_color = (100, 200, 150) if comfort_val > 0 else (200, 150, 100) if comfort_val < 0 else (150, 150, 150)
        comfort_display = (comfort_val + 10) / 20 * 100  # Map -10..10 to 0..100
        self._draw_stat_bar(surface, col1_x + 8, content_y, bar_width, comfort_display, 100, comfort_color)
        content_y += 20
        
        # Stress
        self._draw_section_header(surface, "Stress", col1_x, content_y, section_color)
        content_y += 16
        stress_val = getattr(colonist, 'stress', 0.0)
        stress_color = (200, 100, 100) if stress_val > 2 else (200, 200, 100) if stress_val > 0 else (100, 150, 200)
        stress_display = (stress_val + 10) / 20 * 100  # Map -10..10 to 0..100
        self._draw_stat_bar(surface, col1_x + 8, content_y, bar_width, stress_display, 100, stress_color)
        content_y += 24
        
        # === Preferences Section ===
        self._draw_section_header(surface, "Preferences", col1_x, content_y, (150, 200, 255))
        content_y += 18
        
        preferences = getattr(colonist, 'preferences', {})
        pref_items = [
            ("Outside", preferences.get('likes_outside', 0.0)),
            ("Integrity", preferences.get('likes_integrity', 0.0)),
            ("Interference", preferences.get('likes_interference', 0.0)),
            ("Echo", preferences.get('likes_echo', 0.0)),
            ("Pressure", preferences.get('likes_pressure', 0.0)),
            ("Crowding", preferences.get('likes_crowding', 0.0)),
        ]
        
        for pref_name, pref_val in pref_items:
            pref_color = (100, 200, 100) if pref_val > 0.5 else (200, 100, 100) if pref_val < -0.5 else (150, 150, 150)
            pref_text = self.font_small.render(f"{pref_name}: {pref_val:+.1f}", True, pref_color)
            surface.blit(pref_text, (col1_x + 8, content_y))
            content_y += 14
        
        content_y += 10
        
        # === Personality Drift Section ===
        self._draw_section_header(surface, "Personality Drift", col1_x, content_y, (200, 180, 255))
        content_y += 18
        
        total_drift = getattr(colonist, 'last_total_drift', 0.0)
        drift_strongest = getattr(colonist, 'last_drift_strongest', ('none', 0.0))
        
        drift_text = self.font_small.render(f"Rate: {total_drift:.6f}", True, muted_color)
        surface.blit(drift_text, (col1_x + 8, content_y))
        content_y += 14
        
        drift_param, drift_val = drift_strongest
        if abs(drift_val) > 0.000001:
            drift_dir = "+" if drift_val > 0 else ""
            strongest_text = f"Strongest: {drift_param} ({drift_dir}{drift_val:.5f})"
        else:
            strongest_text = "Strongest: (none)"
        strongest_surf = self.font_small.render(strongest_text, True, muted_color)
        surface.blit(strongest_surf, (col1_x + 8, content_y))
        
        # === Right Column: Equipment Slots ===
        equip_y = initial_content_y
        
        self._draw_section_header(surface, "Equipment", col2_x, equip_y, (255, 200, 150))
        equip_y += 18
        
        # Get equipment data from colonist
        equipment = getattr(colonist, 'equipment', {})
        
        # Equipment slots in 2 columns, 3 rows
        slot_width = 82
        slot_height = 32
        slot_gap = 4
        
        equipment_layout = [
            ("Head", "head"),
            ("Body", "body"),
            ("Hands", "hands"),
            ("Feet", "feet"),
            ("Implant", "implant"),
            ("Charm", "charm"),
        ]
        
        # Clear equipment slot rects for tooltip tracking
        self.equipment_slot_rects.clear()
        
        for i, (display_name, slot_key) in enumerate(equipment_layout):
            row = i // 2
            col = i % 2
            slot_x = col2_x + col * (slot_width + slot_gap)
            slot_y = equip_y + row * (slot_height + slot_gap)
            item = equipment.get(slot_key)
            self._draw_equipment_slot(surface, slot_x, slot_y, slot_width, slot_height, display_name, item)
            
            # Store rect for tooltip
            self.equipment_slot_rects[slot_key] = (
                pygame.Rect(slot_x, slot_y, slot_width, slot_height),
                item
            )
        
        equip_y += 3 * (slot_height + slot_gap) + 8
        
        # === Inventory Section (shows carried items) ===
        self._draw_section_header(surface, "Carrying", col2_x, equip_y, (200, 180, 255))
        equip_y += 18
        
        # Get carried items from colonist (resource type -> amount)
        carried_items = getattr(colonist, 'carried_items', {})
        
        # Convert to list of items for display (up to 6 slots)
        carried_list = []
        for res_type, amount in carried_items.items():
            if amount > 0:
                carried_list.append({"type": res_type, "amount": amount})
        
        # 6 inventory slots in a row
        inv_slot_size = 26
        inv_gap = 4
        
        for i in range(6):
            slot_x = col2_x + i * (inv_slot_size + inv_gap)
            item = carried_list[i] if i < len(carried_list) else None
            self._draw_inventory_slot(surface, slot_x, equip_y, inv_slot_size, item)
        
        equip_y += inv_slot_size + 12
        
        # Mood display
        self._draw_section_header(surface, "Mood", col2_x, equip_y, (255, 180, 220))
        equip_y += 18
        
        mood_state = getattr(colonist, 'mood_state', 'Focused')
        mood_score = getattr(colonist, 'mood_score', 0.0)
        from colonist import Colonist
        mood_color = Colonist.get_mood_color(mood_state)
        
        mood_surf = self.font.render(mood_state, True, mood_color)
        surface.blit(mood_surf, (col2_x + 8, equip_y))
        
        score_surf = self.font_small.render(f"({mood_score:+.1f})", True, muted_color)
        surface.blit(score_surf, (col2_x + 8 + mood_surf.get_width() + 8, equip_y + 2))
        equip_y += 24
        
        # === Job Tags Section ===
        self._draw_section_header(surface, "Work Assignments", col2_x, equip_y, (180, 220, 180))
        equip_y += 20
        
        # Draw job tag toggles
        tag_width = 80
        tag_height = 22
        tags_per_row = 2
        
        for i, (tag_id, tag_name, tag_desc) in enumerate(self.JOB_TAGS):
            row = i // tags_per_row
            col = i % tags_per_row
            
            tag_x = col2_x + col * (tag_width + 6)
            tag_y = equip_y + row * (tag_height + 4)
            
            rect = pygame.Rect(tag_x, tag_y, tag_width, tag_height)
            self.job_tag_rects[tag_id] = rect
            
            enabled = colonist.job_tags.get(tag_id, True)
            
            # Toggle background
            if enabled:
                bg_color = (50, 90, 60)
                border_color = (80, 140, 90)
                text_color = (180, 230, 180)
            else:
                bg_color = (70, 50, 50)
                border_color = (110, 70, 70)
                text_color = (160, 130, 130)
            
            pygame.draw.rect(surface, bg_color, rect, border_radius=4)
            pygame.draw.rect(surface, border_color, rect, 1, border_radius=4)
            
            # Tag label centered
            tag_surf = self.font_small.render(tag_name, True, text_color)
            tag_rect = tag_surf.get_rect(center=rect.center)
            surface.blit(tag_surf, tag_rect)
    
    def _draw_stats_tab(self, surface, colonist, x: int, content_y: int, w: int, col1_x: int) -> None:
        """Draw the Stats tab - D&D style wall of text with all stats."""
        muted_color = (140, 140, 150)
        value_color = (220, 220, 230)
        bonus_color = (100, 200, 100)
        penalty_color = (200, 100, 100)
        header_color = (180, 200, 220)
        
        # Get equipment stats
        equip_stats = colonist.get_equipment_stats()
        
        # === Traits Section (at top of Stats) ===
        self._draw_section_header(surface, "=== TRAITS ===", col1_x, content_y, (200, 180, 255))
        content_y += 18
        
        # Get trait labels
        from traits import get_trait_labels
        traits = getattr(colonist, 'traits', {})
        trait_labels = get_trait_labels(traits)
        
        for label in trait_labels:
            # Major traits (with star) get special color
            if label.startswith("★"):
                trait_color = (255, 200, 100)  # Gold for major traits
            else:
                trait_color = (180, 200, 220)
            trait_surf = self.font_small.render(label, True, trait_color)
            surface.blit(trait_surf, (col1_x + 8, content_y))
            content_y += 13
        
        if not trait_labels:
            no_traits = self.font_small.render("(no traits)", True, muted_color)
            surface.blit(no_traits, (col1_x + 8, content_y))
            content_y += 13
        
        content_y += 8
        
        # === Movement Section ===
        self._draw_section_header(surface, "=== MOVEMENT ===", col1_x, content_y, header_color)
        content_y += 18
        
        # Move Delay
        base_move = colonist.move_speed
        equip_mod = colonist.get_equipment_speed_modifier()
        mood_mod = colonist.get_mood_speed_modifier()
        effective_move = base_move * equip_mod * mood_mod
        speed_bonus = equip_stats.get("speed_bonus", 0)
        move_text = f"{effective_move:.1f} ticks"
        if effective_move < base_move:
            move_text += " (FAST)"
        elif effective_move > base_move:
            move_text += " (slow)"
        self._draw_stat_line(surface, col1_x, content_y, "Move Delay", 
                            move_text, speed_bonus, value_color, bonus_color, penalty_color)
        content_y += 13
        
        # Walk Steady
        walk_steady = equip_stats.get("walk_steady", 0)
        steady_text = f"{walk_steady:+.0%}" if walk_steady != 0 else "0%"
        self._draw_stat_line(surface, col1_x, content_y, "Walk Steady", 
                            steady_text, walk_steady, value_color, bonus_color, penalty_color)
        content_y += 13
        
        # Haul Capacity
        haul_cap = colonist.get_equipment_haul_capacity()
        haul_bonus = equip_stats.get("haul_capacity", 0)
        haul_text = f"{haul_cap:.0%}"
        if haul_cap > 1.0:
            haul_text += " (MORE)"
        self._draw_stat_line(surface, col1_x, content_y, "Haul Capacity", 
                            haul_text, haul_bonus, value_color, bonus_color, penalty_color)
        content_y += 16
        
        # === Work Speeds Section ===
        self._draw_section_header(surface, "=== WORK SPEEDS ===", col1_x, content_y, header_color)
        content_y += 18
        
        # Build Speed (includes mood/stress effects)
        build_mod = colonist._calculate_work_modifier("construction")
        build_bonus = equip_stats.get("build_speed", 0)
        build_text = f"{build_mod:.0%}"
        if build_mod > 1.0:
            build_text += " (FAST)"
        elif build_mod < 1.0:
            build_text += " (slow)"
        self._draw_stat_line(surface, col1_x, content_y, "Build Speed", 
                            build_text, build_bonus, value_color, bonus_color, penalty_color)
        content_y += 13
        
        # Harvest Speed
        harvest_mod = colonist._calculate_work_modifier("gathering")
        harvest_bonus = equip_stats.get("harvest_speed", 0)
        harvest_text = f"{harvest_mod:.0%}"
        if harvest_mod > 1.0:
            harvest_text += " (FAST)"
        elif harvest_mod < 1.0:
            harvest_text += " (slow)"
        self._draw_stat_line(surface, col1_x, content_y, "Harvest Speed", 
                            harvest_text, harvest_bonus, value_color, bonus_color, penalty_color)
        content_y += 13
        
        # Craft Speed
        craft_mod = colonist._calculate_work_modifier("crafting")
        craft_bonus = equip_stats.get("craft_speed", 0)
        craft_text = f"{craft_mod:.0%}"
        if craft_mod > 1.0:
            craft_text += " (FAST)"
        elif craft_mod < 1.0:
            craft_text += " (slow)"
        self._draw_stat_line(surface, col1_x, content_y, "Craft Speed", 
                            craft_text, craft_bonus, value_color, bonus_color, penalty_color)
        content_y += 16
        
        # === Survival Section ===
        self._draw_section_header(surface, "=== SURVIVAL ===", col1_x, content_y, header_color)
        content_y += 18
        
        hazard = equip_stats.get("hazard_resist", 0)
        self._draw_stat_line(surface, col1_x, content_y, "Hazard Resist", 
                            f"{hazard:.0%}", hazard, value_color, bonus_color, penalty_color)
        content_y += 13
        
        warmth = equip_stats.get("warmth", 0)
        self._draw_stat_line(surface, col1_x, content_y, "Warmth", 
                            f"{warmth:+.1f}", warmth, value_color, bonus_color, penalty_color)
        content_y += 13
        
        cooling = equip_stats.get("cooling", 0)
        self._draw_stat_line(surface, col1_x, content_y, "Cooling", 
                            f"{cooling:+.1f}", cooling, value_color, bonus_color, penalty_color)
        content_y += 16
        
        # === Mental Section ===
        self._draw_section_header(surface, "=== MENTAL ===", col1_x, content_y, header_color)
        content_y += 18
        
        # Mood with color
        mood_score = getattr(colonist, 'mood_score', 0)
        mood_state = getattr(colonist, 'mood_state', 'Focused')
        mood_color = colonist.get_mood_color(mood_state)
        mood_surf = self.font_small.render(f"Mood: {mood_state} ({mood_score:+.1f})", True, mood_color)
        surface.blit(mood_surf, (col1_x, content_y))
        content_y += 13
        
        # Stress with color
        stress = getattr(colonist, 'stress', 0)
        stress_color = (100, 200, 100) if stress < 3 else (200, 200, 100) if stress < 6 else (200, 100, 100)
        stress_surf = self.font_small.render(f"Stress: {stress:.1f}", True, stress_color)
        surface.blit(stress_surf, (col1_x, content_y))
        content_y += 13
        
        # Stress Resist
        stress_resist = equip_stats.get("stress_resist", 0)
        self._draw_stat_line(surface, col1_x, content_y, "Stress Resist", 
                            f"{stress_resist:.0%}", stress_resist, value_color, bonus_color, penalty_color)
        content_y += 13
        
        # Comfort Bonus
        comfort = equip_stats.get("comfort", 0)
        self._draw_stat_line(surface, col1_x, content_y, "Comfort Bonus", 
                            f"{comfort:+.2f}", comfort, value_color, bonus_color, penalty_color)
        content_y += 16
        
        # === Equipment Bonuses Section ===
        self._draw_section_header(surface, "=== EQUIPMENT BONUSES ===", col1_x, content_y, (255, 200, 150))
        content_y += 20
        
        equipment = getattr(colonist, 'equipment', {})
        has_any = False
        
        for slot, item_data in equipment.items():
            if item_data is None:
                continue
            has_any = True
            
            item_name = item_data.get("name", slot)
            # Truncate long names
            if len(item_name) > 25:
                item_name = item_name[:22] + "..."
            
            item_surf = self.font_small.render(f"[{slot.upper()}] {item_name}", True, (180, 180, 200))
            surface.blit(item_surf, (col1_x, content_y))
            content_y += 12
            
            # Show item stats if it's a generated item
            if item_data.get("generated"):
                for mod in item_data.get("modifiers", [])[:3]:  # Limit to 3 per item
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
                    mod_surf = self.font_small.render(mod_text, True, mod_color)
                    surface.blit(mod_surf, (col1_x + 10, content_y))
                    content_y += 11
        
        if not has_any:
            no_equip = self.font_small.render("(no equipment)", True, muted_color)
            surface.blit(no_equip, (col1_x, content_y))
    
    def _draw_bio_tab(self, surface, colonist, x: int, content_y: int, w: int, col1_x: int) -> None:
        """Draw the Bio tab - colonist's backstory as flowing prose."""
        muted_color = (140, 140, 150)
        header_color = (200, 180, 255)
        normal_color = (180, 180, 190)
        
        # Header
        self._draw_section_header(surface, "Backstory", col1_x, content_y, header_color)
        content_y += 18
        
        # Get cached rich backstory (generated once at colonist creation)
        backstory_segments = getattr(colonist, 'rich_backstory', [])
        
        if not backstory_segments:
            no_bio = self.font_small.render("(no backstory)", True, muted_color)
            surface.blit(no_bio, (col1_x, content_y))
            return
        
        # Render flowing text with inline colored traits
        max_text_width = w - 40
        line_x = col1_x + 4
        line_start_x = col1_x + 4
        
        for segment in backstory_segments:
            text = segment["text"]
            is_trait = segment.get("is_trait", False)
            color = segment.get("color", normal_color) if is_trait else normal_color
            
            # Split into words to handle wrapping
            words = text.split() if text.strip() else [text]
            
            for word in words:
                word_with_space = word + " " if word.strip() else word
                word_width = self.font_small.size(word_with_space)[0]
                
                # Check if we need to wrap
                if line_x + word_width > line_start_x + max_text_width and line_x > line_start_x:
                    # Move to next line
                    content_y += 14
                    line_x = line_start_x
                
                # Draw the word
                word_surf = self.font_small.render(word_with_space, True, color)
                surface.blit(word_surf, (line_x, content_y))
                line_x += word_width
        
        # Move past the last line
        content_y += 24
        
        # Also show trait labels for quick reference
        self._draw_section_header(surface, "Traits", col1_x, content_y, (180, 200, 220))
        content_y += 16
        
        from traits import get_trait_labels, TRAIT_COLORS
        traits = getattr(colonist, 'traits', {})
        trait_labels = get_trait_labels(traits)
        
        for label in trait_labels:
            if label.startswith("★"):
                trait_color = TRAIT_COLORS["major"]
            else:
                trait_color = (180, 200, 220)
            trait_surf = self.font_small.render(f"• {label}", True, trait_color)
            surface.blit(trait_surf, (col1_x + 8, content_y))
            content_y += 14
    
    def _draw_relations_tab(self, surface, colonist, x: int, content_y: int, w: int, col1_x: int) -> None:
        """Draw the Relations tab - colonist's relationships with others."""
        from relationships import (get_all_relationships, get_relationship_label, 
                                   get_relationship_color, get_family_bonds, find_colonist_by_id)
        
        muted_color = (140, 140, 150)
        header_color = (180, 200, 220)
        
        # Age display
        age = getattr(colonist, 'age', 25)
        age_surf = self.font.render(f"Age: {age}", True, (200, 200, 210))
        surface.blit(age_surf, (col1_x, content_y))
        content_y += 24
        
        # Family section
        self._draw_section_header(surface, "Family", col1_x, content_y, (200, 180, 255))
        content_y += 16
        
        family_bonds = get_family_bonds(colonist)
        if family_bonds:
            for other_id, bond in family_bonds:
                other = find_colonist_by_id(other_id, self.colonists)
                if other:
                    bond_name = bond.value.title()
                    other_name = other.name.split()[0]
                    bond_text = f"• {other_name} ({bond_name})"
                    bond_surf = self.font_small.render(bond_text, True, (200, 180, 255))
                    surface.blit(bond_surf, (col1_x + 8, content_y))
                    content_y += 14
        else:
            no_family = self.font_small.render("(no family in colony)", True, muted_color)
            surface.blit(no_family, (col1_x + 8, content_y))
            content_y += 14
        
        content_y += 10
        
        # Relationships section
        self._draw_section_header(surface, "Relationships", col1_x, content_y, header_color)
        content_y += 16
        
        relationships = get_all_relationships(colonist, self.colonists)
        
        if not relationships:
            no_rels = self.font_small.render("(no relationships yet)", True, muted_color)
            surface.blit(no_rels, (col1_x + 8, content_y))
            return
        
        # Show top relationships (sorted by score)
        shown = 0
        for other, rel_data in relationships:
            if shown >= 12:  # Limit display
                more_text = self.font_small.render("...", True, muted_color)
                surface.blit(more_text, (col1_x + 8, content_y))
                break
            
            # Skip strangers with 0 interactions
            if rel_data["interactions"] == 0 and rel_data["score"] == 0:
                continue
            
            other_name = other.name.split()[0]
            label = get_relationship_label(colonist, other)
            score = rel_data["score"]
            color = get_relationship_color(colonist, other)
            
            # Format: "Name (Label) +50"
            score_sign = "+" if score >= 0 else ""
            rel_text = f"• {other_name} - {label} ({score_sign}{score})"
            
            rel_surf = self.font_small.render(rel_text, True, color)
            surface.blit(rel_surf, (col1_x + 8, content_y))
            content_y += 14
            shown += 1
        
        if shown == 0:
            no_rels = self.font_small.render("(no relationships yet)", True, muted_color)
            surface.blit(no_rels, (col1_x + 8, content_y))
    
    def _draw_thoughts_tab(self, surface, colonist, x: int, content_y: int, w: int, col1_x: int) -> None:
        """Draw the Thoughts tab - colonist's internal monologue."""
        from colonist import THOUGHT_TYPES
        
        muted_color = (140, 140, 150)
        header_color = (180, 200, 220)
        
        # Header
        self._draw_section_header(surface, "Recent Thoughts", col1_x, content_y, header_color)
        content_y += 18
        
        # Get recent thoughts
        thoughts = colonist.get_recent_thoughts(12)  # Show up to 12 thoughts
        
        if not thoughts:
            no_thoughts = self.font_small.render("(no thoughts yet)", True, muted_color)
            surface.blit(no_thoughts, (col1_x, content_y))
            return
        
        # Draw each thought
        for thought in thoughts:
            thought_type = thought.get("type", "idle")
            text = thought.get("text", "")
            mood_effect = thought.get("mood_effect", 0.0)
            
            # Get color for thought type
            type_color = THOUGHT_TYPES.get(thought_type, (180, 180, 180))
            
            # Draw bullet point with type color
            pygame.draw.circle(surface, type_color, (col1_x + 4, content_y + 6), 3)
            
            # Draw thought text
            text_surf = self.font_small.render(text, True, (200, 200, 210))
            surface.blit(text_surf, (col1_x + 14, content_y))
            
            # Draw mood effect indicator if significant
            if abs(mood_effect) >= 0.05:
                effect_color = (100, 200, 100) if mood_effect > 0 else (200, 100, 100)
                effect_text = f"+{mood_effect:.1f}" if mood_effect > 0 else f"{mood_effect:.1f}"
                effect_surf = self.font_small.render(effect_text, True, effect_color)
                surface.blit(effect_surf, (x + w - 50, content_y))
            
            content_y += 14
            
            # Stop if we run out of space
            if content_y > 520:
                more_text = self.font_small.render("...", True, muted_color)
                surface.blit(more_text, (col1_x, content_y))
                break
        
        # Draw legend at bottom
        content_y += 10
        legend_y = content_y
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
            pygame.draw.circle(surface, type_color, (legend_x + 4, legend_y + 5), 3)
            label_surf = self.font_small.render(label, True, muted_color)
            surface.blit(label_surf, (legend_x + 12, legend_y))
            legend_x += 60
            
            # Wrap to next line if needed
            if legend_x > x + w - 60:
                legend_x = col1_x
                legend_y += 12
    
    def _draw_chat_tab(self, surface, colonist, x: int, content_y: int, w: int, col1_x: int) -> None:
        """Draw the Chat tab - colony-wide conversation log."""
        from conversations import get_conversation_log
        
        muted_color = (140, 140, 150)
        header_color = (180, 200, 220)
        speaker_color = (200, 180, 255)
        listener_color = (180, 220, 200)
        
        # Header
        self._draw_section_header(surface, "Colony Chat Log", col1_x, content_y, header_color)
        content_y += 18
        
        # Get recent conversations
        conversations = get_conversation_log(15)  # Show up to 15 conversations
        
        if not conversations:
            no_chat = self.font_small.render("(no conversations yet)", True, muted_color)
            surface.blit(no_chat, (col1_x, content_y))
            return
        
        # Draw each conversation
        max_text_width = w - 40
        for convo in conversations:
            speaker = convo.get("speaker", "???").split()[0]  # First name
            listener = convo.get("listener", "???").split()[0]
            speaker_line = convo.get("speaker_line", "")
            listener_line = convo.get("listener_line", "")
            
            # Speaker line
            speaker_text = f"{speaker}: {speaker_line}"
            # Truncate if too long
            while self.font_small.size(speaker_text)[0] > max_text_width and len(speaker_text) > 20:
                speaker_text = speaker_text[:-4] + "..."
            
            speaker_surf = self.font_small.render(speaker_text, True, speaker_color)
            surface.blit(speaker_surf, (col1_x + 4, content_y))
            content_y += 13
            
            # Listener response (indented)
            listener_text = f"{listener}: {listener_line}"
            while self.font_small.size(listener_text)[0] > max_text_width - 10 and len(listener_text) > 20:
                listener_text = listener_text[:-4] + "..."
            
            listener_surf = self.font_small.render(listener_text, True, listener_color)
            surface.blit(listener_surf, (col1_x + 14, content_y))
            content_y += 15
            
            # Stop if we run out of space
            if content_y > 520:
                more_text = self.font_small.render("...", True, muted_color)
                surface.blit(more_text, (col1_x, content_y))
                break
    
    def _draw_help_tab(self, surface, x: int, content_y: int, w: int, col1_x: int) -> None:
        """Draw the Help tab - compact stat reference."""
        muted_color = (140, 140, 150)
        header_color = (180, 200, 220)
        highlight_color = (100, 200, 150)
        max_width = w - 20
        
        def draw_help_line(name, desc):
            nonlocal content_y
            # Truncate description to fit
            full_text = f"{name}: {desc}"
            while self.font_small.size(full_text)[0] > max_width and len(full_text) > 30:
                full_text = full_text[:-4] + "..."
            name_surf = self.font_small.render(f"{name}:", True, highlight_color)
            surface.blit(name_surf, (col1_x, content_y))
            desc_surf = self.font_small.render(f" {desc[:45]}", True, muted_color)
            surface.blit(desc_surf, (col1_x + name_surf.get_width(), content_y))
            content_y += 13
        
        # === Movement ===
        self._draw_section_header(surface, "MOVEMENT", col1_x, content_y, header_color)
        content_y += 14
        draw_help_line("Move Delay", "Lower = faster movement")
        draw_help_line("Walk Steady", "Reduces stumble chance")
        draw_help_line("Haul Capacity", "Carry amount multiplier")
        content_y += 4
        
        # === Work ===
        self._draw_section_header(surface, "WORK", col1_x, content_y, header_color)
        content_y += 14
        draw_help_line("Build", "Construction speed")
        draw_help_line("Harvest", "Gathering speed")
        draw_help_line("Craft", "Workstation speed")
        content_y += 4
        
        # === Survival ===
        self._draw_section_header(surface, "SURVIVAL", col1_x, content_y, header_color)
        content_y += 14
        draw_help_line("Hazard Resist", "Reduces env damage")
        draw_help_line("Warmth/Cooling", "Temperature resistance")
        content_y += 4
        
        # === Mental ===
        self._draw_section_header(surface, "MENTAL", col1_x, content_y, header_color)
        content_y += 14
        draw_help_line("Mood", "Affects work speed")
        draw_help_line("Stress", ">6 = penalty, >8 = severe")
        draw_help_line("Stress Resist", "Reduces stress gain")
        draw_help_line("Comfort", "Equipment mood bonus")
        content_y += 4
        
        # === Mood Effects (compact) ===
        self._draw_section_header(surface, "MOOD EFFECTS", col1_x, content_y, header_color)
        content_y += 14
        
        mood_line = "Euphoric +15% | Calm +10% | Focused +5%"
        mood_surf = self.font_small.render(mood_line, True, (100, 200, 150))
        surface.blit(mood_surf, (col1_x, content_y))
        content_y += 13
        
        mood_line2 = "Uneasy -5% | Stressed -15% | Overwhelmed -30%"
        mood_surf2 = self.font_small.render(mood_line2, True, (200, 150, 100))
        surface.blit(mood_surf2, (col1_x, content_y))
    
    def _draw_stat_line(self, surface, x: int, y: int, name: str, value: str, 
                        bonus: float, value_color: tuple, bonus_color: tuple, penalty_color: tuple) -> None:
        """Draw a stat line with name, value, and optional bonus indicator."""
        # Name
        name_surf = self.font_small.render(f"{name}:", True, (160, 160, 170))
        surface.blit(name_surf, (x, y))
        
        # Value
        value_surf = self.font_small.render(value, True, value_color)
        surface.blit(value_surf, (x + 120, y))
        
        # Bonus indicator
        if bonus != 0:
            sign = "+" if bonus > 0 else ""
            bonus_text = f"({sign}{bonus:.0%} equip)"
            color = bonus_color if bonus > 0 else penalty_color
            bonus_surf = self.font_small.render(bonus_text, True, color)
            surface.blit(bonus_surf, (x + 200, y))
    
    def _draw_navigation_buttons(self, surface) -> None:
        """Draw navigation buttons (shared by all tabs)."""
        # Prev button
        pygame.draw.rect(surface, (50, 55, 65), self.prev_btn_rect, border_radius=4)
        pygame.draw.rect(surface, (80, 85, 95), self.prev_btn_rect, 1, border_radius=4)
        prev_text = self.font.render("< Prev", True, (180, 180, 190))
        prev_rect = prev_text.get_rect(center=self.prev_btn_rect.center)
        surface.blit(prev_text, prev_rect)
        
        # Next button
        pygame.draw.rect(surface, (50, 55, 65), self.next_btn_rect, border_radius=4)
        pygame.draw.rect(surface, (80, 85, 95), self.next_btn_rect, 1, border_radius=4)
        next_text = self.font.render("Next >", True, (180, 180, 190))
        next_rect = next_text.get_rect(center=self.next_btn_rect.center)
        surface.blit(next_text, next_rect)
        
        # Hotkey hint
        hint_text = self.font_small.render("TAB to close | Arrow keys to switch", True, (100, 100, 110))
        hint_rect = hint_text.get_rect(centerx=self.panel_rect.centerx, y=self.panel_rect.bottom - 18)
        surface.blit(hint_text, hint_rect)
    
    def _draw_section_header(self, surface, text: str, x: int, y: int, color: tuple) -> None:
        """Draw a section header."""
        header_surf = self.font.render(text, True, color)
        surface.blit(header_surf, (x, y))
    
    def _draw_stat_bar(self, surface, x: int, y: int, width: int, value: float, max_val: float, color: tuple) -> None:
        """Draw a stat bar."""
        bar_height = 8
        # Background
        pygame.draw.rect(surface, (30, 30, 35), (x, y, width, bar_height), border_radius=2)
        # Fill
        fill_width = int(width * min(value, max_val) / max_val)
        if fill_width > 0:
            pygame.draw.rect(surface, color, (x, y, fill_width, bar_height), border_radius=2)
        # Border
        pygame.draw.rect(surface, (60, 60, 70), (x, y, width, bar_height), 1, border_radius=2)
    
    def _draw_equipment_slot(self, surface, x: int, y: int, width: int, height: int, slot_name: str, item) -> None:
        """Draw an equipment slot with item icon and name."""
        # Slot background
        bg_color = (30, 35, 42) if item else (25, 28, 35)
        border_color = (80, 100, 80) if item else (55, 60, 70)
        pygame.draw.rect(surface, bg_color, (x, y, width, height), border_radius=4)
        pygame.draw.rect(surface, border_color, (x, y, width, height), 1, border_radius=4)
        
        # Slot label
        label_surf = self.font_small.render(slot_name, True, (100, 105, 115))
        surface.blit(label_surf, (x + 4, y + 2))
        
        if item and isinstance(item, dict) and "name" in item:
            # Get icon color from item or look up from registry
            icon_color = item.get("icon_color")
            if icon_color is None:
                # Try to get from item registry
                from items import get_item_def
                item_def = get_item_def(item.get("id", ""))
                if item_def:
                    icon_color = item_def.icon_color
                else:
                    icon_color = (150, 150, 150)
            
            # Draw small icon square
            icon_size = 10
            icon_x = x + 4
            icon_y = y + height - 14
            pygame.draw.rect(surface, icon_color, (icon_x, icon_y, icon_size, icon_size), border_radius=2)
            
            # Show item name next to icon
            item_surf = self.font_small.render(item["name"][:10], True, (180, 200, 180))
            surface.blit(item_surf, (icon_x + icon_size + 4, icon_y))
        else:
            # Empty indicator
            empty_surf = self.font_small.render("Empty", True, (60, 60, 65))
            empty_rect = empty_surf.get_rect(centerx=x + width // 2, y=y + height - 14)
            surface.blit(empty_surf, empty_rect)
    
    def _draw_equipment_tooltip(self, surface) -> None:
        """Draw tooltip for hovered equipment item."""
        if self.tooltip_item is None:
            return
        
        item = self.tooltip_item
        from items import get_item_def
        
        # Build tooltip lines
        lines = []
        
        # Item name
        name = item.get("name", "Unknown Item")
        lines.append(("name", name))
        
        # Check if generated item
        if item.get("generated"):
            # Show rarity
            rarity = item.get("rarity", "common")
            lines.append(("rarity", rarity.title()))
            
            # Show modifiers
            for mod in item.get("modifiers", []):
                stat = mod.get("stat", "").replace("_", " ").title()
                value = mod.get("value", 0)
                trigger = mod.get("trigger", "always")
                
                if trigger == "always":
                    line = f"{stat}: {value:+.0%}" if abs(value) < 1 else f"{stat}: {value:+.1f}"
                else:
                    trigger_text = trigger.replace("_", " ")
                    line = f"{stat}: {value:+.0%} ({trigger_text})" if abs(value) < 1 else f"{stat}: {value:+.1f} ({trigger_text})"
                lines.append(("stat", line))
            
            # Show flavor text
            flavor = item.get("flavor")
            if flavor:
                lines.append(("flavor", flavor))
        else:
            # Static item - get from registry
            item_def = get_item_def(item.get("id", ""))
            if item_def:
                # Show stats
                if item_def.speed_bonus != 0:
                    lines.append(("stat", f"Speed: {item_def.speed_bonus:+.0%}"))
                if item_def.work_bonus != 0:
                    lines.append(("stat", f"Work: {item_def.work_bonus:+.0%}"))
                if item_def.comfort != 0:
                    lines.append(("stat", f"Comfort: {item_def.comfort:+.2f}"))
                if item_def.hazard_resist != 0:
                    lines.append(("stat", f"Hazard Resist: {item_def.hazard_resist:+.0%}"))
                
                # Show description
                if item_def.description:
                    lines.append(("flavor", item_def.description))
        
        if not lines:
            return
        
        # Calculate tooltip size
        padding = 8
        line_height = 16
        max_width = 200
        
        # Measure text widths
        for line_type, text in lines:
            text_surf = self.font_small.render(text, True, (255, 255, 255))
            max_width = max(max_width, text_surf.get_width() + padding * 2)
        
        tooltip_height = len(lines) * line_height + padding * 2
        tooltip_width = min(max_width, 280)
        
        # Position tooltip (keep on screen)
        tx, ty = self.tooltip_pos
        if tx + tooltip_width > SCREEN_W:
            tx = SCREEN_W - tooltip_width - 10
        if ty + tooltip_height > SCREEN_H:
            ty = SCREEN_H - tooltip_height - 10
        
        # Draw tooltip background
        tooltip_rect = pygame.Rect(tx, ty, tooltip_width, tooltip_height)
        pygame.draw.rect(surface, (25, 30, 40), tooltip_rect, border_radius=4)
        pygame.draw.rect(surface, (80, 100, 120), tooltip_rect, 1, border_radius=4)
        
        # Draw lines
        y_offset = ty + padding
        for line_type, text in lines:
            if line_type == "name":
                color = (255, 220, 150)  # Gold for name
            elif line_type == "rarity":
                rarity_colors = {
                    "Common": (180, 180, 180),
                    "Uncommon": (100, 200, 100),
                    "Rare": (100, 150, 255),
                    "Epic": (200, 100, 255),
                    "Legendary": (255, 180, 50),
                }
                color = rarity_colors.get(text, (180, 180, 180))
            elif line_type == "stat":
                color = (150, 220, 255)  # Blue for stats
            elif line_type == "flavor":
                color = (140, 140, 150)  # Gray for flavor
            else:
                color = (200, 200, 200)
            
            # Wrap long text
            if len(text) > 35:
                text = text[:32] + "..."
            
            text_surf = self.font_small.render(text, True, color)
            surface.blit(text_surf, (tx + padding, y_offset))
            y_offset += line_height
    
    def _draw_inventory_slot(self, surface, x: int, y: int, size: int, item) -> None:
        """Draw an inventory slot showing carried resources."""
        # Slot background
        bg_color = (30, 35, 42) if item else (22, 25, 30)
        border_color = (70, 90, 70) if item else (45, 50, 55)
        pygame.draw.rect(surface, bg_color, (x, y, size, size), border_radius=3)
        pygame.draw.rect(surface, border_color, (x, y, size, size), 1, border_radius=3)
        
        if item and isinstance(item, dict):
            res_type = item.get("type", "")
            amount = item.get("amount", 1)
            
            # Resource type colors
            type_colors = {
                "wood": (139, 90, 43),
                "scrap": (120, 120, 130),
                "food": (100, 180, 80),
                "cooked_meal": (200, 150, 80),
                "minerals": (100, 140, 180),
            }
            icon_color = type_colors.get(res_type, (150, 150, 150))
            
            # Draw small colored square as icon
            icon_size = 12
            icon_x = x + (size - icon_size) // 2
            icon_y = y + 3
            pygame.draw.rect(surface, icon_color, (icon_x, icon_y, icon_size, icon_size), border_radius=2)
            
            # Draw amount below icon
            amount_text = str(amount) if amount < 100 else "99+"
            amount_surf = self.font_small.render(amount_text, True, (200, 200, 210))
            amount_rect = amount_surf.get_rect(centerx=x + size // 2, y=y + size - 11)
            surface.blit(amount_surf, amount_rect)
        else:
            # Empty dot indicator
            pygame.draw.circle(surface, (40, 42, 48), (x + size // 2, y + size // 2), 3)
    
    def handle_key(self, key: int) -> bool:
        """Handle keyboard input. Returns True if consumed."""
        if not self.visible:
            return False
        
        if key == pygame.K_TAB or key == pygame.K_ESCAPE:
            self.close()
            return True
        elif key == pygame.K_LEFT:
            self._prev_colonist()
            return True
        elif key == pygame.K_RIGHT:
            self._next_colonist()
            return True
        
        return False


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
_colonist_management_panel: Optional[ColonistManagementPanel] = None


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


def get_colonist_management_panel() -> ColonistManagementPanel:
    """Get or create the global colonist management panel instance."""
    global _colonist_management_panel
    if _colonist_management_panel is None:
        _colonist_management_panel = ColonistManagementPanel()
    return _colonist_management_panel
