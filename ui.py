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
from ui_layout import RIGHT_PANEL_WIDTH, TOP_BAR_HEIGHT

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
        self.hovered_item: Optional[str] = None  # Track which item is hovered for tooltip
        self._font = font
        self._item_ids = []  # Map button index to item id
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
        self._item_ids = []
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
            self._item_ids.append(item["id"])
        
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
            self.hovered_item = None
            return
        
        self.hovered_item = None
        for i, btn in enumerate(self.buttons):
            btn.update(mouse_pos)
            if btn.hovered and i < len(self._item_ids):
                self.hovered_item = self._item_ids[i]
    
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
    
    def draw(self, surface: pygame.Surface, font: pygame.font.Font, tooltips: Dict[str, str] = None) -> None:
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
        
        # Draw tooltip box for hovered item
        if self.hovered_item and tooltips:
            tooltip_data = tooltips.get(self.hovered_item)
            if tooltip_data:
                # Support both old string format and new tuple format
                if isinstance(tooltip_data, str):
                    title = self.hovered_item.replace("_", " ").title()
                    desc = tooltip_data
                    extra = ""
                else:
                    title, desc, extra = tooltip_data
                
                # Fonts
                title_font = pygame.font.Font(None, 26)
                desc_font = pygame.font.Font(None, 22)
                extra_font = pygame.font.Font(None, 20)
                
                # Render text
                title_surf = title_font.render(title, True, (255, 220, 150))
                desc_surf = desc_font.render(desc, True, (220, 220, 220))
                extra_surf = extra_font.render(extra, True, (150, 180, 220)) if extra else None
                
                # Calculate box size
                padding = 16
                line_spacing = 6
                box_width = max(title_surf.get_width(), desc_surf.get_width())
                if extra_surf:
                    box_width = max(box_width, extra_surf.get_width())
                box_width += padding * 2
                box_width = max(box_width, 250)  # Minimum width for readability
                
                box_height = padding + title_surf.get_height() + line_spacing
                box_height += desc_surf.get_height() + line_spacing
                if extra_surf:
                    box_height += extra_surf.get_height() + line_spacing
                box_height += padding
                
                # Position tooltip to the right of the menu
                from config import SCREEN_W, SCREEN_H
                
                # Try right side first
                tooltip_x = self.panel_rect.right + 12
                tooltip_y = self.panel_rect.top
                
                # If it goes off right edge, try left side
                if tooltip_x + box_width > SCREEN_W - 10:
                    tooltip_x = self.panel_rect.left - box_width - 12
                
                # If left side is also off-screen, just put it at the right edge of screen
                if tooltip_x < 10:
                    tooltip_x = SCREEN_W - box_width - 10
                
                # Vertical: keep it above the action bar
                if tooltip_y + box_height > SCREEN_H - 60:
                    tooltip_y = SCREEN_H - 60 - box_height
                
                # Don't go above screen top
                if tooltip_y < 10:
                    tooltip_y = 10
                
                # Draw box with shadow
                box_rect = pygame.Rect(tooltip_x, tooltip_y, box_width, box_height)
                shadow_rect = box_rect.copy()
                shadow_rect.x += 4
                shadow_rect.y += 4
                pygame.draw.rect(surface, (15, 15, 20), shadow_rect, border_radius=8)
                
                # Main box with gradient-like effect
                pygame.draw.rect(surface, (45, 45, 55), box_rect, border_radius=8)
                pygame.draw.rect(surface, (70, 70, 90), box_rect, 2, border_radius=8)
                
                # Draw text
                y = tooltip_y + padding
                surface.blit(title_surf, (tooltip_x + padding, y))
                y += title_surf.get_height() + line_spacing
                
                # Draw separator line
                pygame.draw.line(surface, (80, 80, 100), 
                               (tooltip_x + padding, y - 2), 
                               (tooltip_x + box_width - padding, y - 2), 1)
                
                surface.blit(desc_surf, (tooltip_x + padding, y))
                y += desc_surf.get_height() + line_spacing
                
                if extra_surf:
                    surface.blit(extra_surf, (tooltip_x + padding, y))


class ActionBar:
    """Bottom action bar with main category buttons and submenus."""
    
    # Tooltips for items - explains what each thing does
    # Format: {id: (title, description, extra_info)}
    TOOLTIPS = {
        # Walls
        "wall": (
            "Wooden Wall",
            "A basic wall made of wood. Blocks movement and line of sight.",
            "Cost: 2 wood"
        ),
        "wall_advanced": (
            "Reinforced Wall", 
            "A stronger wall made of minerals. More durable and provides better insulation.",
            "Cost: 2 mineral"
        ),
        # Floors
        "floor": (
            "Wood Floor",
            "Wooden flooring that makes rooms feel complete. Colonists prefer walking on floors.",
            "Cost: 1 wood"
        ),
        # Access
        "door": (
            "Door",
            "Allows colonists to pass through walls. Opens and closes automatically.",
            "Cost: 1 wood, 1 metal"
        ),
        "window": (
            "Window",
            "Colonists can pass through like a door. Lets light into rooms and can be opened for ventilation.",
            "Cost: 1 wood, 1 mineral"
        ),
        "fire_escape": (
            "Fire Escape",
            "Vertical ladder that provides access between floors. Must be placed on the edge of a building.",
            "Cost: 1 wood, 1 metal"
        ),
        "bridge": (
            "Bridge",
            "A horizontal walkway that spans gaps between buildings or over open areas.",
            "Cost: 2 wood, 1 metal"
        ),
        # Zones
        "stockpile": (
            "Stockpile Zone",
            "Designate an area for storing resources. Colonists will haul items here. Click and drag to create.",
            "Right-click stockpile to set filters"
        ),
        "allow": (
            "Allowed Area",
            "Mark tiles where colonists are allowed to walk. Use to restrict movement or create paths.",
            "Drag to paint allowed tiles"
        ),
        "roof_zone": (
            "Roof Zone",
            "Designate an area to be automatically roofed. Roofs provide shelter from weather.",
            "Requires enclosed walls"
        ),
        "demolish": (
            "Demolish",
            "Remove buildings, walls, floors, and other constructions. Resources are lost.",
            "Click or drag to demolish"
        ),
        # Tools
        "harvest": (
            "Harvest",
            "Gather resources from plants, trees, and resource nodes. Colonists will collect the materials.",
            "Click or drag to mark for harvest"
        ),
        "salvage": (
            "Salvage",
            "Carefully deconstruct buildings to recover some materials. Better than demolish for reclaiming resources.",
            "Click buildings to salvage"
        ),
        # Workstations
        "salvagers_bench": (
            "Salvager's Bench",
            "Strip down scrap into usable metal. Essential for turning junk into the chrome that keeps your crew alive.",
            "Processes: Scrap → Metal"
        ),
        "generator": (
            "Generator",
            "Cranks out power cells to juice your machines. No cells, no craft - keep this thing humming.",
            "Produces: Power Cells"
        ),
        "stove": (
            "Stove",
            "Turns raw ingredients into actual food. Hot meals keep morale up and bellies full.",
            "Produces: Cooked Meals"
        ),
        "gutter_forge": (
            "Gutter Forge",
            "Where street iron gets hammered into blades and knuckle rigs. Crude but deadly.",
            "Crafts: Weapons, Gauntlets"
        ),
        "skinshop_loom": (
            "Skinshop Loom",
            "Stitches together armor from scavenged hides and synth-weave. Protection for the meat underneath.",
            "Crafts: Armor, Protective Gear"
        ),
        "cortex_spindle": (
            "Cortex Spindle",
            "Delicate work - neural implants, lucky charms, and trauma patches. Handles the stuff between your ears.",
            "Crafts: Implants, Charms, Medical"
        ),
    }
    
    # Menu structure - flattened, less nesting
    # Build = walls only
    BUILD_MENU = [
        {"id": "wall", "name": "Wall", "cost": "2 wood", "keybind": "1"},
        {"id": "wall_advanced", "name": "Reinforced Wall", "cost": "2 mineral", "keybind": "2"},
    ]
    
    # Floors - just floor for now, more types later
    FLOORS_MENU = [
        {"id": "floor", "name": "Wood Floor", "cost": "1 wood", "keybind": "1"},
    ]
    
    # Access = doors, windows, fire escape, bridge (combined entrance + movement)
    ACCESS_MENU = [
        {"id": "door", "name": "Door", "cost": "1 wood, 1 metal", "keybind": "1"},
        {"id": "window", "name": "Window", "cost": "1 wood, 1 mineral", "keybind": "2"},
        {"id": "fire_escape", "name": "Fire Escape", "cost": "1 wood, 1 metal", "keybind": "3"},
        {"id": "bridge", "name": "Bridge", "cost": "2 wood, 1 metal", "keybind": "4"},
    ]
    
    # Workstations - populated at runtime
    STATIONS_MENU = []
    
    # Furniture - populated at runtime
    FURNITURE_MENU = []
    
    # Zones = stockpile, allow, roof (no demolish)
    ZONE_MENU = [
        {"id": "stockpile", "name": "Stockpile", "keybind": "1"},
        {"id": "allow", "name": "Allow", "keybind": "2"},
        {"id": "roof", "name": "Roof", "keybind": "3"},
    ]
    
    def __init__(self):
        self.font: Optional[pygame.font.Font] = None
        
        # Main action buttons
        self.main_buttons: Dict[str, Button] = {}
        self.submenus: Dict[str, SubMenu] = {}
        
        # State
        self.active_menu: Optional[str] = None  # "build", "zone", "harvest"
        self.active_submenu: Optional[str] = None  # "walls", "floors", etc.
        self.current_tool: Optional[str] = None  # "wall", "stockpile", "harvest", etc.
        
        # Bar rect
        self.bar_rect = pygame.Rect(0, SCREEN_H - BAR_HEIGHT, SCREEN_W, BAR_HEIGHT)
        
        self._create_ui()
    
    def _build_workstation_menu_items(self) -> None:
        """Populate the Workstations submenu from BUILDING_TYPES."""
        try:
            import buildings as buildings_module
        except ImportError:
            ActionBar.STATIONS_MENU = []
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
                cost = "Free"
            # Get description and power requirement
            desc = b_def.get("description", "A workstation for crafting.")
            power = b_def.get("power_required", 0)
            ws_defs.append((b_id, name, cost, desc, power))
        
        menu_items: List[dict] = []
        for idx, (b_id, display_name, cost, desc, power) in enumerate(ws_defs):
            keybind = str(idx + 1) if idx < 9 else ""
            menu_items.append({
                "id": b_id,
                "name": display_name,
                "cost": cost,
                "keybind": keybind,
            })
            # Only add tooltip if not already defined (custom tooltips take priority)
            if b_id not in ActionBar.TOOLTIPS:
                extra = f"Cost: {cost}"
                if power > 0:
                    extra += f" | Requires {power} power"
                ActionBar.TOOLTIPS[b_id] = (display_name, desc, extra)
        
        ActionBar.STATIONS_MENU = menu_items
    
    def _build_furniture_menu_items(self) -> None:
        """Populate the Furniture submenu from items tagged as furniture."""
        try:
            import items as items_module
        except ImportError:
            ActionBar.FURNITURE_MENU = []
            return
        
        furniture_defs = items_module.get_items_with_tag("furniture")
        if not furniture_defs:
            ActionBar.FURNITURE_MENU = []
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
        
        ActionBar.FURNITURE_MENU = menu_items
    
    def _create_ui(self) -> None:
        """Create all UI elements."""
        # Populate dynamic menus first
        self._build_workstation_menu_items()
        self._build_furniture_menu_items()
        
        # Main buttons - auto-sized to fit text
        button_y = SCREEN_H - BAR_HEIGHT + (BAR_HEIGHT - BUTTON_HEIGHT) // 2
        
        # Define buttons with their labels
        # NOTE: Cannot use W, A, S, D - reserved for camera movement
        button_defs = [
            ("build", "Build", "B"),
            ("floors", "Floor", "F"),
            ("access", "Access", "E"),  # E for Entry/Exit points
            ("stations", "Stations", "T"),
            ("furniture", "Furniture", "R"),  # R for fुRniture
            ("zone", "Zone", "Z"),
            ("demolish", "Demolish", "X"),
            ("salvage", "Salvage", "V"),  # V for salVage
            ("harvest", "Harvest", "H"),
        ]
        
        # Calculate widths based on text - use temp font
        temp_font = pygame.font.Font(None, 22)
        button_widths = []
        for btn_id, text, keybind in button_defs:
            # Width = keybind + text + padding
            kb_width = temp_font.size(f"[{keybind}] ")[0] if keybind else 0
            text_width = temp_font.size(text)[0]
            width = kb_width + text_width + 24  # padding
            width = max(width, 70)  # minimum width
            button_widths.append(width)
        
        # Calculate total width and center
        total_width = sum(button_widths) + BUTTON_SPACING * (len(button_defs) - 1)
        start_x = (SCREEN_W - total_width) // 2
        
        # Create buttons
        current_x = start_x
        for i, (btn_id, text, keybind) in enumerate(button_defs):
            self.main_buttons[btn_id] = Button(
                x=current_x,
                y=button_y,
                width=button_widths[i],
                height=BUTTON_HEIGHT,
                text=text,
                keybind=keybind,
            )
            current_x += button_widths[i] + BUTTON_SPACING
        
        # Create submenus for each category
        self.submenus["build"] = SubMenu(self.BUILD_MENU, self.main_buttons["build"])
        self.submenus["floors"] = SubMenu(self.FLOORS_MENU, self.main_buttons["floors"])
        self.submenus["access"] = SubMenu(self.ACCESS_MENU, self.main_buttons["access"])
        self.submenus["stations"] = SubMenu(self.STATIONS_MENU, self.main_buttons["stations"])
        self.submenus["furniture"] = SubMenu(self.FURNITURE_MENU, self.main_buttons["furniture"])
        self.submenus["zone"] = SubMenu(self.ZONE_MENU, self.main_buttons["zone"])
        
        # No submenus needed for demolish/salvage/harvest - they're direct tools
    
    def init_font(self) -> None:
        """Initialize font after pygame.init()."""
        self.font = pygame.font.Font(None, 22)  # Normal readable font
    
    def _close_all_menus(self) -> None:
        """Close all open menus."""
        for menu in self.submenus.values():
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
        elif menu_id == "demolish":
            # Demolish is a direct tool, no submenu
            self.current_tool = "demolish"
        elif menu_id == "salvage":
            # Salvage is a direct tool, no submenu
            self.current_tool = "salvage"
        elif menu_id in self.submenus:
            self.submenus[menu_id].show()
    
    def get_current_tool(self) -> Optional[str]:
        """Get the currently selected tool."""
        return self.current_tool
    
    def cancel_tool(self) -> None:
        """Cancel current tool selection."""
        self.current_tool = None
        self._close_all_menus()
    
    def handle_key(self, key: int) -> bool:
        """Handle keyboard input. Returns True if consumed."""
        # Main menu shortcuts - new flattened structure
        if key == pygame.K_b:
            if self.active_menu == "build":
                self.cancel_tool()
            else:
                self._open_menu("build")
            return True
        
        if key == pygame.K_f:
            if self.active_menu == "floors":
                self.cancel_tool()
            else:
                self._open_menu("floors")
            return True
        
        if key == pygame.K_e:
            if self.active_menu == "access":
                self.cancel_tool()
            else:
                self._open_menu("access")
            return True
        
        if key == pygame.K_t:
            if self.active_menu == "stations":
                self.cancel_tool()
            else:
                self._open_menu("stations")
            return True
        
        if key == pygame.K_r:
            if self.active_menu == "furniture":
                self.cancel_tool()
            else:
                self._open_menu("furniture")
            return True
        
        if key == pygame.K_z:
            if self.active_menu == "zone":
                self.cancel_tool()
            else:
                self._open_menu("zone")
            return True
        
        if key == pygame.K_x:
            if self.current_tool == "demolish":
                self.cancel_tool()
            else:
                self._open_menu("demolish")
            return True
        
        if key == pygame.K_h:
            if self.current_tool == "harvest":
                self.cancel_tool()
            else:
                self._open_menu("harvest")
            return True
        
        if key == pygame.K_v:
            if self.current_tool == "salvage":
                self.cancel_tool()
            else:
                self._open_menu("salvage")
            return True
        
        # Number keys for submenu selection
        if key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5, pygame.K_6, pygame.K_7, pygame.K_8, pygame.K_9):
            num = key - pygame.K_1  # 0-based index
            
            # Get the active submenu items
            menu_items = None
            menu_key = None
            if self.active_menu == "build":
                menu_items = self.BUILD_MENU
                menu_key = "build"
            elif self.active_menu == "floors":
                menu_items = self.FLOORS_MENU
                menu_key = "floors"
            elif self.active_menu == "access":
                menu_items = self.ACCESS_MENU
                menu_key = "access"
            elif self.active_menu == "stations":
                menu_items = self.STATIONS_MENU
                menu_key = "stations"
            elif self.active_menu == "furniture":
                menu_items = self.FURNITURE_MENU
                menu_key = "furniture"
            elif self.active_menu == "zone":
                menu_items = self.ZONE_MENU
                menu_key = "zone"
            
            if menu_items and num < len(menu_items):
                self.current_tool = menu_items[num]["id"]
                self._close_all_menus()
                self.main_buttons[menu_key].active = True
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
        
        # Check for submenu selections - now flat structure
        for menu_id in ["build", "floors", "access", "stations", "furniture", "zone"]:
            if self.active_menu == menu_id and menu_id in self.submenus:
                submenu = self.submenus[menu_id]
                if submenu.selected_item:
                    self.current_tool = submenu.selected_item
                    submenu.selected_item = None
                    self._close_all_menus()
                    self.main_buttons[menu_id].active = True
                    break
    
    def handle_click(self, mouse_pos: tuple[int, int], button: int) -> bool:
        """Handle mouse click. Returns True if consumed."""
        if button == 1:  # Left click
            # Check submenus first (they're on top)
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
            # Get tooltip data
            tooltip_data = self.TOOLTIPS.get(self.current_tool)
            if isinstance(tooltip_data, tuple):
                tool_name, tool_desc, tool_extra = tooltip_data
            else:
                tool_name = self.current_tool.replace("_", " ").title()
                tool_desc = tooltip_data if tooltip_data else ""
                tool_extra = ""
            
            # Tool name with colored background pill
            title_font = pygame.font.Font(None, 24)
            tool_surface = title_font.render(f" {tool_name} ", True, (255, 255, 255))
            tool_rect = tool_surface.get_rect(midleft=(12, self.bar_rect.centery - 10))
            
            # Background pill
            pill_rect = tool_rect.inflate(10, 8)
            pygame.draw.rect(surface, (80, 120, 160), pill_rect, border_radius=6)
            pygame.draw.rect(surface, (100, 150, 200), pill_rect, 2, border_radius=6)
            surface.blit(tool_surface, tool_rect)
            
            # Description below tool name
            if tool_desc:
                desc_font = pygame.font.Font(None, 20)
                desc_surface = desc_font.render(tool_desc, True, (180, 180, 190))
                desc_rect = desc_surface.get_rect(midleft=(12, self.bar_rect.centery + 12))
                surface.blit(desc_surface, desc_rect)
            
            # Cancel hint on RIGHT side
            hint_text = "[ESC] Cancel"
            hint_surface = self.font.render(hint_text, True, (140, 140, 150))
            hint_rect = hint_surface.get_rect(midright=(SCREEN_W - 12, self.bar_rect.centery))
            surface.blit(hint_surface, hint_rect)
        
        # Draw main buttons
        for btn in self.main_buttons.values():
            btn.draw(surface, self.font)
        
        # Draw submenus with tooltips
        for menu in self.submenus.values():
            menu.draw(surface, self.font, self.TOOLTIPS)


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
# Bed Assignment Panel
# ============================================================================

class BedAssignmentPanel:
    """UI panel for assigning colonists to beds."""
    
    def __init__(self):
        self.visible = False
        self.bed_pos: Optional[tuple[int, int, int]] = None
        self.panel_rect = pygame.Rect(0, 0, 220, 300)
        self.colonist_rects: list[pygame.Rect] = []
        self.unassign_rects: list[pygame.Rect] = []  # X buttons to unassign
        self.font: Optional[pygame.font.Font] = None
        self.font_small: Optional[pygame.font.Font] = None
        self.scroll_offset = 0
    
    def init_font(self) -> None:
        self.font = pygame.font.Font(None, 24)
        self.font_small = pygame.font.Font(None, 20)
    
    def open(self, x: int, y: int, z: int, screen_x: int, screen_y: int) -> None:
        """Open the panel for a bed at world position."""
        from beds import get_bed_at
        
        bed = get_bed_at(x, y, z)
        if bed is None:
            return
        
        self.bed_pos = (x, y, z)
        self.visible = True
        self.scroll_offset = 0
        
        # Position panel near click but keep on screen
        self.panel_rect.x = min(screen_x + 20, SCREEN_W - self.panel_rect.width - 10)
        self.panel_rect.y = min(screen_y, SCREEN_H - self.panel_rect.height - 60)
    
    def close(self) -> None:
        """Close the panel."""
        self.visible = False
        self.bed_pos = None
    
    def handle_click(self, mouse_pos: tuple[int, int], colonists: list) -> bool:
        """Handle click. Returns True if consumed."""
        if not self.visible:
            return False
        
        # Click outside panel closes it
        if not self.panel_rect.collidepoint(mouse_pos):
            self.close()
            return True
        
        from beds import assign_colonist_to_bed, unassign_colonist, get_bed_occupants
        
        # Check unassign buttons first
        for i, rect in enumerate(self.unassign_rects):
            if rect.collidepoint(mouse_pos):
                occupants = get_bed_occupants(*self.bed_pos)
                if i < len(occupants):
                    unassign_colonist(occupants[i])
                return True
        
        # Check colonist assignment clicks
        for i, rect in enumerate(self.colonist_rects):
            if rect.collidepoint(mouse_pos):
                # Get unassigned colonists
                unassigned = self._get_unassigned_colonists(colonists)
                if i < len(unassigned):
                    colonist = unassigned[i]
                    assign_colonist_to_bed(id(colonist), *self.bed_pos)
                return True
        
        return True  # Consume click on panel
    
    def _get_unassigned_colonists(self, colonists: list) -> list:
        """Get colonists not assigned to any bed."""
        from beds import get_colonist_bed
        return [c for c in colonists if not c.is_dead and get_colonist_bed(id(c)) is None]
    
    def _get_colonist_by_id(self, colonist_id: int, colonists: list):
        """Find colonist by id()."""
        for c in colonists:
            if id(c) == colonist_id:
                return c
        return None
    
    def draw(self, surface: pygame.Surface, colonists: list) -> None:
        """Draw the bed assignment panel."""
        if not self.visible or self.bed_pos is None:
            return
        
        if self.font is None:
            self.init_font()
        
        from beds import get_bed_at, get_bed_occupants
        
        bed = get_bed_at(*self.bed_pos)
        if bed is None:
            self.close()
            return
        
        # Panel background
        pygame.draw.rect(surface, (40, 42, 48), self.panel_rect, border_radius=6)
        pygame.draw.rect(surface, (100, 180, 180), self.panel_rect, 2, border_radius=6)
        
        # Title
        title = self.font.render("Crash Bed", True, (100, 200, 200))
        surface.blit(title, (self.panel_rect.x + 10, self.panel_rect.y + 10))
        
        # Quality indicator
        quality = bed.get("quality", 1)
        quality_text = "★" * quality + "☆" * (3 - quality)
        quality_surf = self.font_small.render(quality_text, True, (255, 220, 100))
        surface.blit(quality_surf, (self.panel_rect.right - 60, self.panel_rect.y + 12))
        
        y = self.panel_rect.y + 40
        
        # Current occupants section
        occupants = get_bed_occupants(*self.bed_pos)
        
        section_title = self.font_small.render(f"Assigned ({len(occupants)}/2):", True, (180, 180, 180))
        surface.blit(section_title, (self.panel_rect.x + 10, y))
        y += 24
        
        self.unassign_rects.clear()
        
        if not occupants:
            empty_text = self.font_small.render("(none)", True, (120, 120, 120))
            surface.blit(empty_text, (self.panel_rect.x + 20, y))
            y += 24
        else:
            for occ_id in occupants:
                colonist = self._get_colonist_by_id(occ_id, colonists)
                name = colonist.name if colonist else f"#{occ_id}"
                
                # Name
                name_surf = self.font_small.render(name, True, (200, 200, 200))
                surface.blit(name_surf, (self.panel_rect.x + 20, y))
                
                # Unassign button (X)
                x_rect = pygame.Rect(self.panel_rect.right - 30, y, 20, 20)
                self.unassign_rects.append(x_rect)
                pygame.draw.rect(surface, (100, 60, 60), x_rect, border_radius=3)
                x_text = self.font_small.render("✗", True, (200, 100, 100))
                surface.blit(x_text, (x_rect.x + 4, x_rect.y + 2))
                
                y += 26
        
        y += 10
        
        # Separator
        pygame.draw.line(surface, (80, 85, 95), 
                        (self.panel_rect.x + 10, y),
                        (self.panel_rect.right - 10, y), 1)
        y += 10
        
        # Available colonists section
        unassigned = self._get_unassigned_colonists(colonists)
        
        avail_title = self.font_small.render(f"Available ({len(unassigned)}):", True, (180, 180, 180))
        surface.blit(avail_title, (self.panel_rect.x + 10, y))
        y += 24
        
        self.colonist_rects.clear()
        
        # Can only assign if bed has space
        can_assign = len(occupants) < 2
        
        if not unassigned:
            empty_text = self.font_small.render("(all assigned)", True, (120, 120, 120))
            surface.blit(empty_text, (self.panel_rect.x + 20, y))
        else:
            for colonist in unassigned[:8]:  # Show max 8
                rect = pygame.Rect(self.panel_rect.x + 10, y, self.panel_rect.width - 20, 24)
                self.colonist_rects.append(rect)
                
                # Highlight if hoverable
                mouse_pos = pygame.mouse.get_pos()
                if can_assign and rect.collidepoint(mouse_pos):
                    pygame.draw.rect(surface, (60, 80, 60), rect, border_radius=3)
                
                # Name
                text_color = (200, 200, 200) if can_assign else (100, 100, 100)
                name_surf = self.font_small.render(colonist.name, True, text_color)
                surface.blit(name_surf, (rect.x + 10, rect.y + 4))
                
                y += 26
        
        # Hint at bottom
        if not can_assign:
            hint = self.font_small.render("Bed is full", True, (200, 150, 100))
            surface.blit(hint, (self.panel_rect.x + 10, self.panel_rect.bottom - 25))


# Global bed assignment panel
_bed_assignment_panel: Optional[BedAssignmentPanel] = None


def get_bed_assignment_panel() -> BedAssignmentPanel:
    """Get or create the global bed assignment panel."""
    global _bed_assignment_panel
    if _bed_assignment_panel is None:
        _bed_assignment_panel = BedAssignmentPanel()
    return _bed_assignment_panel


# ============================================================================
# Fixer Trade Panel
# ============================================================================

class FixerTradePanel:
    """UI panel for trading with fixers."""
    
    def __init__(self):
        self.visible = False
        self.fixer: Optional[dict] = None
        self.panel_rect = pygame.Rect(0, 0, 400, 450)
        self.font: Optional[pygame.font.Font] = None
        self.font_small: Optional[pygame.font.Font] = None
        
        # Trade state
        self.player_offer: Dict[str, int] = {}  # {item_id: qty}
        self.fixer_offer: Dict[str, int] = {}   # {item_id: qty}
        
        # Clickable areas
        self.fixer_item_rects: List[Tuple[pygame.Rect, str]] = []
        self.player_item_rects: List[Tuple[pygame.Rect, str]] = []
        self.confirm_rect: Optional[pygame.Rect] = None
        self.cancel_rect: Optional[pygame.Rect] = None
    
    def init_font(self) -> None:
        self.font = pygame.font.Font(None, 24)
        self.font_small = pygame.font.Font(None, 20)
    
    def open(self, fixer: dict) -> None:
        """Open trade panel for a fixer."""
        self.fixer = fixer
        self.visible = True
        self.player_offer.clear()
        self.fixer_offer.clear()
        
        # Center panel
        self.panel_rect.x = (SCREEN_W - self.panel_rect.width) // 2
        self.panel_rect.y = (SCREEN_H - self.panel_rect.height) // 2
    
    def close(self) -> None:
        """Close the panel."""
        self.visible = False
        self.fixer = None
        self.player_offer.clear()
        self.fixer_offer.clear()
    
    def handle_click(self, mouse_pos: tuple[int, int], zones_module) -> bool:
        """Handle click. Returns True if consumed."""
        if not self.visible or not self.fixer:
            return False
        
        # Click outside closes
        if not self.panel_rect.collidepoint(mouse_pos):
            self.close()
            return True
        
        # Check fixer items (click to add to their offer)
        for rect, item_id in self.fixer_item_rects:
            if rect.collidepoint(mouse_pos):
                available = self.fixer["inventory"].get(item_id, 0)
                offered = self.fixer_offer.get(item_id, 0)
                if offered < available:
                    self.fixer_offer[item_id] = offered + 1
                return True
        
        # Check player items (click to add to offer)
        for rect, item_id in self.player_item_rects:
            if rect.collidepoint(mouse_pos):
                available = self._get_player_stock(item_id, zones_module)
                offered = self.player_offer.get(item_id, 0)
                if offered < available:
                    self.player_offer[item_id] = offered + 1
                return True
        
        # Confirm trade
        if self.confirm_rect and self.confirm_rect.collidepoint(mouse_pos):
            if self._execute_trade(zones_module):
                self.close()
            return True
        
        # Cancel
        if self.cancel_rect and self.cancel_rect.collidepoint(mouse_pos):
            self.close()
            return True
        
        return True
    
    def _get_player_stock(self, item_id: str, zones_module) -> int:
        """Get how much of an item the player has in stockpiles."""
        total = 0
        for coord, storage in zones_module.get_all_tile_storage().items():
            if storage and storage.get("type") == item_id:
                total += storage.get("amount", 0)
        return total
    
    def _execute_trade(self, zones_module) -> bool:
        """Queue the trade for colonist execution. Returns True if successful."""
        from economy import is_fair_trade
        from wanderers import queue_trade
        
        if not self.fixer:
            return False
        
        origin = self.fixer["origin"]
        
        # Convert to list format for trade check
        player_items = [(k, v) for k, v in self.player_offer.items() if v > 0]
        fixer_items = [(k, v) for k, v in self.fixer_offer.items() if v > 0]
        
        if not fixer_items:
            return False  # Must get something
        
        # Check if fair
        if not is_fair_trade(player_items, fixer_items, origin):
            print("[Trade] Fixer rejected unfair trade")
            return False
        
        # Check player has the resources in stockpiles
        for item_id, qty in player_items:
            total = 0
            for coord, storage in zones_module.get_all_tile_storage().items():
                if storage and storage.get("type") == item_id:
                    total += storage.get("amount", 0)
            if total < qty:
                print(f"[Trade] Not enough {item_id} in stockpiles ({total}/{qty})")
                return False
        
        # Queue trade for colonist execution (no instant transfer!)
        if queue_trade(self.fixer, self.player_offer, self.fixer_offer):
            from notifications import add_notification, NotificationType
            add_notification(NotificationType.INFO,
                           "// TRADE QUEUED //",
                           f"Colonists will exchange goods with {self.fixer['name']}",
                           duration=360)
            return True
        
        return False
    
    def draw(self, surface: pygame.Surface, zones_module) -> None:
        """Draw the trade panel."""
        if not self.visible or not self.fixer:
            return
        
        if self.font is None:
            self.init_font()
        
        from economy import calculate_fixer_price, get_base_value
        
        origin = self.fixer["origin"]
        
        # Panel background
        pygame.draw.rect(surface, (35, 38, 45), self.panel_rect, border_radius=8)
        pygame.draw.rect(surface, (255, 200, 80), self.panel_rect, 2, border_radius=8)
        
        # Title
        title = self.font.render(f"Trade with {self.fixer['name']}", True, (255, 220, 100))
        surface.blit(title, (self.panel_rect.x + 15, self.panel_rect.y + 12))
        
        # Origin subtitle
        origin_text = self.font_small.render(f"Origin: {origin.name}", True, (150, 150, 150))
        surface.blit(origin_text, (self.panel_rect.x + 15, self.panel_rect.y + 36))
        
        # Divider
        y = self.panel_rect.y + 55
        pygame.draw.line(surface, (80, 85, 95), 
                        (self.panel_rect.x + 10, y),
                        (self.panel_rect.right - 10, y), 1)
        y += 10
        
        # Two columns: Fixer's goods | Your goods
        col_width = (self.panel_rect.width - 30) // 2
        left_x = self.panel_rect.x + 10
        right_x = self.panel_rect.x + 20 + col_width
        
        # Fixer's goods header
        header = self.font_small.render("Fixer's Goods", True, (200, 180, 100))
        surface.blit(header, (left_x, y))
        
        # Your goods header
        header2 = self.font_small.render("Your Stockpile", True, (100, 180, 200))
        surface.blit(header2, (right_x, y))
        y += 22
        
        self.fixer_item_rects.clear()
        self.player_item_rects.clear()
        
        # Fixer's inventory
        fixer_y = y
        for item_id, qty in self.fixer["inventory"].items():
            if qty <= 0:
                continue
            
            offered = self.fixer_offer.get(item_id, 0)
            sell_price = calculate_fixer_price(item_id, origin, is_buying=False)
            
            rect = pygame.Rect(left_x, fixer_y, col_width - 5, 22)
            self.fixer_item_rects.append((rect, item_id))
            
            # Highlight if hovered
            mouse_pos = pygame.mouse.get_pos()
            if rect.collidepoint(mouse_pos):
                pygame.draw.rect(surface, (60, 55, 40), rect, border_radius=3)
            
            # Item name and qty
            display = f"{item_id}: {qty}"
            if offered > 0:
                display = f"{item_id}: {qty} (-{offered})"
            text = self.font_small.render(display, True, (200, 200, 200))
            surface.blit(text, (left_x + 4, fixer_y + 3))
            
            # Price
            price_text = self.font_small.render(f"[{sell_price}]", True, (255, 200, 80))
            surface.blit(price_text, (left_x + col_width - 40, fixer_y + 3))
            
            fixer_y += 24
        
        # Player's stockpile items
        player_y = y
        player_items = {}
        for coord, storage in zones_module.get_all_tile_storage().items():
            if storage:
                item_id = storage.get("type")
                amount = storage.get("amount", 0)
                if item_id and amount > 0:
                    player_items[item_id] = player_items.get(item_id, 0) + amount
        
        for item_id, qty in player_items.items():
            offered = self.player_offer.get(item_id, 0)
            buy_price = calculate_fixer_price(item_id, origin, is_buying=True)
            
            rect = pygame.Rect(right_x, player_y, col_width - 5, 22)
            self.player_item_rects.append((rect, item_id))
            
            mouse_pos = pygame.mouse.get_pos()
            if rect.collidepoint(mouse_pos):
                pygame.draw.rect(surface, (40, 55, 60), rect, border_radius=3)
            
            display = f"{item_id}: {qty}"
            if offered > 0:
                display = f"{item_id}: {qty} (-{offered})"
            text = self.font_small.render(display, True, (200, 200, 200))
            surface.blit(text, (right_x + 4, player_y + 3))
            
            price_text = self.font_small.render(f"[{buy_price}]", True, (100, 200, 255))
            surface.blit(price_text, (right_x + col_width - 40, player_y + 3))
            
            player_y += 24
        
        # Trade summary
        summary_y = self.panel_rect.bottom - 100
        pygame.draw.line(surface, (80, 85, 95),
                        (self.panel_rect.x + 10, summary_y),
                        (self.panel_rect.right - 10, summary_y), 1)
        summary_y += 10
        
        # Calculate values
        from economy import calculate_trade_value
        player_value = calculate_trade_value(
            [(k, v) for k, v in self.player_offer.items() if v > 0],
            origin, is_player_offering=True
        )
        fixer_value = calculate_trade_value(
            [(k, v) for k, v in self.fixer_offer.items() if v > 0],
            origin, is_player_offering=False
        )
        
        # Show values
        your_text = self.font_small.render(f"You offer: {player_value} value", True, (100, 200, 255))
        surface.blit(your_text, (left_x, summary_y))
        
        their_text = self.font_small.render(f"They offer: {fixer_value} value", True, (255, 200, 80))
        surface.blit(their_text, (right_x, summary_y))
        summary_y += 25
        
        # Fair trade indicator
        is_fair = player_value >= fixer_value * 0.9 if fixer_value > 0 else True
        fair_color = (100, 200, 100) if is_fair else (200, 100, 100)
        fair_text = "Fair Trade" if is_fair else "Unfair - Add More"
        fair_surf = self.font_small.render(fair_text, True, fair_color)
        surface.blit(fair_surf, (self.panel_rect.centerx - fair_surf.get_width() // 2, summary_y))
        summary_y += 25
        
        # Buttons
        btn_width = 80
        btn_height = 28
        
        self.confirm_rect = pygame.Rect(
            self.panel_rect.centerx - btn_width - 10, summary_y,
            btn_width, btn_height
        )
        self.cancel_rect = pygame.Rect(
            self.panel_rect.centerx + 10, summary_y,
            btn_width, btn_height
        )
        
        # Confirm button
        confirm_color = (60, 100, 60) if is_fair else (50, 50, 50)
        pygame.draw.rect(surface, confirm_color, self.confirm_rect, border_radius=4)
        pygame.draw.rect(surface, (100, 200, 100) if is_fair else (80, 80, 80), self.confirm_rect, 1, border_radius=4)
        confirm_text = self.font_small.render("Trade", True, (200, 255, 200) if is_fair else (120, 120, 120))
        surface.blit(confirm_text, (self.confirm_rect.centerx - confirm_text.get_width() // 2,
                                    self.confirm_rect.centery - confirm_text.get_height() // 2))
        
        # Cancel button
        pygame.draw.rect(surface, (80, 50, 50), self.cancel_rect, border_radius=4)
        pygame.draw.rect(surface, (200, 100, 100), self.cancel_rect, 1, border_radius=4)
        cancel_text = self.font_small.render("Cancel", True, (255, 200, 200))
        surface.blit(cancel_text, (self.cancel_rect.centerx - cancel_text.get_width() // 2,
                                   self.cancel_rect.centery - cancel_text.get_height() // 2))


# Global fixer trade panel
_fixer_trade_panel: Optional[FixerTradePanel] = None


def get_fixer_trade_panel() -> FixerTradePanel:
    """Get or create the global fixer trade panel."""
    global _fixer_trade_panel
    if _fixer_trade_panel is None:
        _fixer_trade_panel = FixerTradePanel()
    return _fixer_trade_panel


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
                if current_mode == "infinite":
                    ws["auto_mode"] = "target"
                    # Set default target of 5 if switching to target mode with 0
                    if ws.get("target_count", 0) == 0:
                        ws["target_count"] = 5
                else:
                    ws["auto_mode"] = "infinite"
                print(f"[Workstation] Mode: {ws['auto_mode']}, Target: {ws.get('target_count', 0)}")
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
    
    # Tab definitions - short cyberpunk names to fit
    TABS = ["Status", "Bio", "Body", "Links", "Stats", "Mind", "Chat", "Help"]
    
    def __init__(self):
        self.visible = False
        self.colonists: List = []  # Reference to all colonists
        self.current_index = 0  # Currently viewed colonist index
        self.current_tab = 0  # 0 = Overview, 1 = Stats
        self.font: Optional[pygame.font.Font] = None
        self.font_large: Optional[pygame.font.Font] = None
        self.font_small: Optional[pygame.font.Font] = None
        
        # Callback for camera centering when switching colonists
        self.on_colonist_changed: Optional[Callable] = None  # (colonist) -> None
        
        # Panel dimensions - fits in right panel area (always visible)
        self.tab_sidebar_width = 70
        self.panel_width = RIGHT_PANEL_WIDTH - self.tab_sidebar_width
        self.panel_height = SCREEN_H - TOP_BAR_HEIGHT
        
        # Pin to right edge of screen, below top bar
        self.sidebar_rect = pygame.Rect(
            SCREEN_W - RIGHT_PANEL_WIDTH,
            TOP_BAR_HEIGHT,
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
        from ui_layout import get_cyber_font
        self.font = get_cyber_font(15)
        self.font_large = get_cyber_font(20, bold=True)
        self.font_small = get_cyber_font(12)
    
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
            # Center camera on new colonist
            if self.on_colonist_changed and self.current_colonist:
                self.on_colonist_changed(self.current_colonist)
    
    def _next_colonist(self) -> None:
        if self.colonists:
            self.current_index = (self.current_index + 1) % len(self.colonists)
            # Center camera on new colonist
            if self.on_colonist_changed and self.current_colonist:
                self.on_colonist_changed(self.current_colonist)
    
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
        
        # Ensure button positions are updated
        self._update_button_positions()
        
        colonist = self.current_colonist
        if colonist is None:
            return
        
        # === Draw Tab Sidebar (external, left of main panel) ===
        sx = self.sidebar_rect.x
        sy = self.sidebar_rect.y
        sw = self.sidebar_rect.width
        sh = self.sidebar_rect.height
        
        # Sidebar background - cyberpunk dark
        pygame.draw.rect(surface, (14, 18, 24), self.sidebar_rect, border_radius=8)
        pygame.draw.rect(surface, (0, 100, 110), self.sidebar_rect, 1, border_radius=8)
        
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
                bg_color = (180, 40, 90)  # Hot pink active
                border_color = (255, 80, 140)
                text_color = (255, 255, 255)
                # Draw connector to main panel
                pygame.draw.rect(surface, bg_color, 
                               pygame.Rect(sx + sw - 4, tab_y + 4, 8, tab_height - 8))
            else:
                bg_color = (25, 30, 38)
                border_color = (0, 80, 90)
                text_color = (100, 180, 180)
            
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
        pygame.draw.rect(surface, (8, 10, 14), shadow_rect, border_radius=10)
        
        # Main panel background - darker cyberpunk
        pygame.draw.rect(surface, (18, 22, 28), self.panel_rect, border_radius=10)
        pygame.draw.rect(surface, (0, 180, 180), self.panel_rect, 1, border_radius=10)
        
        x = self.panel_rect.x
        y = self.panel_rect.y
        w = self.panel_rect.width
        h = self.panel_rect.height
        
        # === Header Section ===
        # Colonist name (large, neon pink)
        name = getattr(colonist, 'name', f'Colonist {self.current_index + 1}')
        name_surf = self.font_large.render(name, True, (255, 100, 160))
        surface.blit(name_surf, (x + 20, y + 15))
        
        # Colonist counter (cyan)
        counter_text = f"{self.current_index + 1} / {len(self.colonists)}"
        counter_surf = self.font_small.render(counter_text, True, (0, 200, 200))
        surface.blit(counter_surf, (x + 20, y + 42))
        
        # Close button (neon red)
        pygame.draw.rect(surface, (80, 20, 30), self.close_btn_rect, border_radius=4)
        pygame.draw.rect(surface, (255, 60, 80), self.close_btn_rect, 1, border_radius=4)
        close_text = self.font.render("X", True, (255, 100, 100))
        close_rect = close_text.get_rect(center=self.close_btn_rect.center)
        surface.blit(close_text, close_rect)
        
        # Header separator (cyan glow)
        pygame.draw.line(surface, (0, 120, 130), (x + 15, y + 55), (x + w - 15, y + 55), 1)
        
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
            self._draw_body_tab(surface, colonist, x, content_y, content_w, col1_x, col2_x)
        elif self.current_tab == 3:
            self._draw_relations_tab(surface, colonist, x, content_y, content_w, col1_x)
        elif self.current_tab == 4:
            self._draw_stats_tab(surface, colonist, x, content_y, content_w, col1_x)
        elif self.current_tab == 5:
            self._draw_thoughts_tab(surface, colonist, x, content_y, content_w, col1_x)
        elif self.current_tab == 6:
            self._draw_chat_tab(surface, x, content_y, content_w, col1_x)
        elif self.current_tab == 7:
            self._draw_help_tab(surface, x, content_y, content_w, col1_x)
        
        # Draw navigation buttons (shared by all tabs)
        self._draw_navigation_buttons(surface)
        
        # Draw tooltip last (on top of everything)
        self._draw_equipment_tooltip(surface)
    
    def _draw_overview_tab(self, surface, colonist, x: int, content_y: int, w: int, col1_x: int, col2_x: int) -> None:
        """Draw the Overview tab content - USE FULL VERTICAL SPACE."""
        # Calculate available height for content
        panel_bottom = self.panel_rect.bottom - 60  # Leave room for nav buttons
        available_height = panel_bottom - content_y
        
        # Save initial content_y for right column
        initial_content_y = content_y
        
        # === Left Column: Status & Stats ===
        section_color = (180, 200, 220)
        value_color = (220, 220, 230)
        muted_color = (140, 140, 150)
        
        # Current Task
        self._draw_section_header(surface, "Current Task", col1_x, content_y, section_color)
        content_y += 22
        
        state = colonist.state
        job_desc = state
        if colonist.current_job:
            job_type = colonist.current_job.type
            job_desc = f"{state} ({job_type})"
        task_surf = self.font_small.render(job_desc[:28], True, value_color)
        surface.blit(task_surf, (col1_x + 8, content_y))
        content_y += 36
        
        # Hunger
        self._draw_section_header(surface, "Hunger", col1_x, content_y, section_color)
        content_y += 20
        hunger_val = colonist.hunger
        hunger_color = (100, 200, 100) if hunger_val < 50 else (200, 200, 100) if hunger_val < 70 else (200, 100, 100)
        bar_width = min(120, w // 2 - 80)
        self._draw_stat_bar(surface, col1_x + 8, content_y, bar_width, hunger_val, 100, hunger_color)
        content_y += 32
        
        # Comfort
        self._draw_section_header(surface, "Comfort", col1_x, content_y, section_color)
        content_y += 20
        comfort_val = getattr(colonist, 'comfort', 0.0)
        comfort_color = (100, 200, 150) if comfort_val > 0 else (200, 150, 100) if comfort_val < 0 else (150, 150, 150)
        comfort_display = (comfort_val + 10) / 20 * 100  # Map -10..10 to 0..100
        self._draw_stat_bar(surface, col1_x + 8, content_y, bar_width, comfort_display, 100, comfort_color)
        content_y += 32
        
        # Stress
        self._draw_section_header(surface, "Stress", col1_x, content_y, section_color)
        content_y += 20
        stress_val = getattr(colonist, 'stress', 0.0)
        stress_color = (200, 100, 100) if stress_val > 2 else (200, 200, 100) if stress_val > 0 else (100, 150, 200)
        stress_display = (stress_val + 10) / 20 * 100  # Map -10..10 to 0..100
        self._draw_stat_bar(surface, col1_x + 8, content_y, bar_width, stress_display, 100, stress_color)
        content_y += 40
        
        # === Preferences Section ===
        self._draw_section_header(surface, "Preferences", col1_x, content_y, (150, 200, 255))
        content_y += 26
        
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
            content_y += 24
        
        content_y += 28
        
        # === Personality Drift Section ===
        self._draw_section_header(surface, "Personality Drift", col1_x, content_y, (200, 180, 255))
        content_y += 26
        
        total_drift = getattr(colonist, 'last_total_drift', 0.0)
        drift_strongest = getattr(colonist, 'last_drift_strongest', ('none', 0.0))
        
        drift_text = self.font_small.render(f"Rate: {total_drift:.6f}", True, muted_color)
        surface.blit(drift_text, (col1_x + 8, content_y))
        content_y += 24
        
        drift_param, drift_val = drift_strongest
        if abs(drift_val) > 0.000001:
            drift_dir = "+" if drift_val > 0 else ""
            strongest_text = f"Strongest: {drift_param} ({drift_dir}{drift_val:.5f})"
        else:
            strongest_text = "Strongest: (none)"
        strongest_surf = self.font_small.render(strongest_text, True, muted_color)
        surface.blit(strongest_surf, (col1_x + 8, content_y))
        content_y += 36
        
        # Track where left column ends for equipment placement
        left_col_end_y = content_y
        
        # === Right Column: Carrying, Mood, Work Assignments ===
        right_y = initial_content_y
        
        # Carrying Section - use smaller slots that fit
        self._draw_section_header(surface, "Carrying", col2_x, right_y, (200, 180, 255))
        right_y += 22
        
        carried_items = getattr(colonist, 'carried_items', {})
        carried_list = []
        for res_type, amount in carried_items.items():
            if amount > 0:
                carried_list.append({"type": res_type, "amount": amount})
        
        # Smaller slots, 2 rows of 3 to fit width
        inv_slot_size = 24
        inv_gap = 3
        for i in range(6):
            row = i // 3
            col = i % 3
            slot_x = col2_x + col * (inv_slot_size + inv_gap)
            slot_y = right_y + row * (inv_slot_size + inv_gap)
            item = carried_list[i] if i < len(carried_list) else None
            self._draw_inventory_slot(surface, slot_x, slot_y, inv_slot_size, item)
        right_y += 2 * (inv_slot_size + inv_gap) + 20
        
        # Mood display
        self._draw_section_header(surface, "Mood", col2_x, right_y, (255, 180, 220))
        right_y += 22
        
        mood_state = getattr(colonist, 'mood_state', 'Focused')
        mood_score = getattr(colonist, 'mood_score', 0.0)
        from colonist import Colonist
        mood_color = Colonist.get_mood_color(mood_state)
        
        mood_surf = self.font.render(mood_state, True, mood_color)
        surface.blit(mood_surf, (col2_x + 8, right_y))
        
        score_surf = self.font_small.render(f"({mood_score:+.1f})", True, muted_color)
        surface.blit(score_surf, (col2_x + 8 + mood_surf.get_width() + 8, right_y + 2))
        right_y += 40
        
        # === Job Tags Section - spread out vertically ===
        self._draw_section_header(surface, "Work Assignments", col2_x, right_y, (180, 220, 180))
        right_y += 26
        
        tag_width = 90
        tag_height = 32
        tag_gap = 10  # More gap between buttons
        
        for i, (tag_id, tag_name, tag_desc) in enumerate(self.JOB_TAGS):
            tag_x = col2_x
            tag_y = right_y + i * (tag_height + tag_gap)
            
            rect = pygame.Rect(tag_x, tag_y, tag_width, tag_height)
            self.job_tag_rects[tag_id] = rect
            
            enabled = colonist.job_tags.get(tag_id, True)
            
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
            
            tag_surf = self.font_small.render(tag_name, True, text_color)
            tag_rect = tag_surf.get_rect(center=rect.center)
            surface.blit(tag_surf, tag_rect)
        
        right_y += len(self.JOB_TAGS) * (tag_height + tag_gap) + 20
        
        # === Equipment Section (BOTTOM - full width, spread out) ===
        equip_y = max(left_col_end_y, right_y) + 20
        
        self._draw_section_header(surface, "Equipment", col1_x, equip_y, (255, 200, 150))
        equip_y += 28
        
        equipment = getattr(colonist, 'equipment', {})
        
        # Equipment slots - larger with more spacing
        slot_width = 80
        slot_height = 42
        slot_gap = 10
        
        equipment_layout = [
            ("Head", "head"),
            ("Body", "body"),
            ("Hands", "hands"),
            ("Feet", "feet"),
            ("Implant", "implant"),
            ("Charm", "charm"),
        ]
        
        self.equipment_slot_rects.clear()
        
        for i, (display_name, slot_key) in enumerate(equipment_layout):
            row = i // 2
            col = i % 2
            slot_x = col1_x + col * (slot_width + slot_gap)
            slot_y = equip_y + row * (slot_height + slot_gap)
            item = equipment.get(slot_key)
            self._draw_equipment_slot(surface, slot_x, slot_y, slot_width, slot_height, display_name, item)
            
            self.equipment_slot_rects[slot_key] = (
                pygame.Rect(slot_x, slot_y, slot_width, slot_height),
                item
            )
    
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
    
    def _draw_body_tab(self, surface, colonist, x: int, content_y: int, w: int, col1_x: int, col2_x: int) -> None:
        """Draw the Body tab - detailed body part status like Dwarf Fortress."""
        from body import Body, PartCategory, PartStatus
        
        muted_color = (120, 130, 145)
        header_color = (255, 100, 160)  # Pink for headers
        healthy_color = (50, 255, 120)
        
        # Get or create body
        body = getattr(colonist, 'body', None)
        if body is None:
            body = Body()
            colonist.body = body
        
        # Tighter layout - use panel width properly
        panel_right = self.panel_rect.right - 15
        col_width = (panel_right - col1_x) // 2 - 5
        col2_start = col1_x + col_width + 10
        line_h = 11  # Tighter line spacing
        
        # Overall health header
        overall = body.get_overall_health()
        blood_loss = getattr(body, 'blood_loss', 0.0)
        
        if overall >= 90:
            health_color = healthy_color
        elif overall >= 70:
            health_color = (180, 220, 100)
        elif overall >= 50:
            health_color = (220, 180, 60)
        else:
            health_color = (255, 80, 80)
        
        health_text = f"INTEGRITY: {overall:.0f}%"
        health_surf = self.font.render(health_text, True, health_color)
        surface.blit(health_surf, (col1_x, content_y))
        
        # Blood loss indicator (only show if bleeding)
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
            blood_surf = self.font.render(blood_text, True, blood_color)
            surface.blit(blood_surf, (col1_x + 140, content_y))
        
        content_y += 18
        
        # Helper to get short status
        def short_status(part, part_id=""):
            if part.status == PartStatus.MISSING:
                return "GONE"
            if part.status == PartStatus.CYBERNETIC:
                return f"CYB {part.health:.0f}%"
            # Special case for teeth - show as count out of 32
            if part_id == "teeth":
                teeth_count = int(32 * part.health / 100)
                return f"{teeth_count}/32"
            if part.health >= 95:
                return "OK"
            elif part.health >= 70:
                return f"{part.health:.0f}%"
            else:
                return f"{part.health:.0f}%"
        
        # Helper to draw a part line compactly
        def draw_part(part_name, part, px, py, part_id=""):
            color = part.get_color()
            # Shorten part names
            short_name = part_name.replace("Left ", "L ").replace("Right ", "R ")
            short_name = short_name.replace("Upper ", "Up ").replace("Lower ", "Lo ")
            text = f"{short_name}: {short_status(part, part_id)}"
            surf = self.font_small.render(text, True, color)
            surface.blit(surf, (px, py))
        
        # LEFT COLUMN
        left_y = content_y
        
        # HEAD
        self._draw_section_header(surface, "HEAD", col1_x, left_y, header_color)
        left_y += 14
        head_parts = body.get_parts_by_category(PartCategory.HEAD)
        for part_id, part in head_parts:
            if not part.is_internal:
                draw_part(part.name, part, col1_x + 4, left_y, part_id)
                left_y += line_h
        left_y += 4
        
        # TORSO
        self._draw_section_header(surface, "TORSO", col1_x, left_y, header_color)
        left_y += 14
        torso_parts = body.get_parts_by_category(PartCategory.TORSO)
        for part_id, part in torso_parts:
            draw_part(part.name, part, col1_x + 4, left_y, part_id)
            left_y += line_h
        left_y += 4
        
        # LEFT ARM
        self._draw_section_header(surface, "L ARM", col1_x, left_y, header_color)
        left_y += 14
        for part_id, part in body.get_parts_by_category(PartCategory.ARM_LEFT):
            name = part.name.replace("Left ", "")
            draw_part(name, part, col1_x + 4, left_y, part_id)
            left_y += line_h
        left_y += 4
        
        # LEFT LEG
        self._draw_section_header(surface, "L LEG", col1_x, left_y, header_color)
        left_y += 14
        for part_id, part in body.get_parts_by_category(PartCategory.LEG_LEFT):
            name = part.name.replace("Left ", "")
            draw_part(name, part, col1_x + 4, left_y, part_id)
            left_y += line_h
        
        # RIGHT COLUMN
        right_y = content_y
        
        # RIGHT ARM
        self._draw_section_header(surface, "R ARM", col2_start, right_y, header_color)
        right_y += 14
        for part_id, part in body.get_parts_by_category(PartCategory.ARM_RIGHT):
            name = part.name.replace("Right ", "")
            draw_part(name, part, col2_start + 4, right_y, part_id)
            right_y += line_h
        right_y += 4
        
        # RIGHT LEG
        self._draw_section_header(surface, "R LEG", col2_start, right_y, header_color)
        right_y += 14
        for part_id, part in body.get_parts_by_category(PartCategory.LEG_RIGHT):
            name = part.name.replace("Right ", "")
            draw_part(name, part, col2_start + 4, right_y, part_id)
            right_y += line_h
        
        # BOTTOM SECTION - below both columns
        bottom_y = max(left_y, right_y) + 12
        full_width = panel_right - col1_x
        
        # COMBAT LOG - full width
        self._draw_section_header(surface, "COMBAT LOG", col1_x, bottom_y, (255, 80, 80))
        bottom_y += 14
        combat_log = body.get_recent_combat_log(8)
        if combat_log:
            max_text_width = full_width - 8
            text_x = col1_x + 4
            lines_drawn = 0
            max_lines = max(1, (self._content_bottom - bottom_y) // line_h)

            self_first = colonist.name.split()[0] if getattr(colonist, 'name', '') else ""

            def _extract_name_tokens(msg: str) -> set:
                tokens = set()
                if not msg:
                    return tokens
                if msg.startswith("FIGHT STARTED:") and " vs " in msg:
                    try:
                        rest = msg.split(":", 1)[1].strip()
                        left, right = rest.split(" vs ", 1)
                        left = left.strip().split()[0]
                        right = right.strip().split()[0]
                        if left:
                            tokens.add(left)
                        if right:
                            tokens.add(right)
                    except Exception:
                        pass
                for prefix in ("KILLED:", "RETREATED:"):
                    if msg.startswith(prefix):
                        after = msg[len(prefix):].strip()
                        if after:
                            tokens.add(after.split()[0])
                first_word = msg.strip().split()[0] if msg.strip() else ""
                if first_word and first_word[0].isupper() and first_word.isalpha():
                    tokens.add(first_word)
                return tokens

            def _draw_colored_line(line: str, x: int, y: int, name_tokens: set) -> None:
                cursor_x = x
                for word in line.split():
                    color = muted_color
                    if word in name_tokens:
                        color = (120, 200, 255) if word == self_first else (255, 120, 120)
                    surf = self.font_small.render(word + " ", True, color)
                    surface.blit(surf, (cursor_x, y))
                    cursor_x += surf.get_width()

            for entry in combat_log:
                if lines_drawn >= max_lines:
                    break

                words = entry.split() if entry.strip() else [entry]
                current_line = ""
                name_tokens = _extract_name_tokens(entry)
                for word in words:
                    candidate = (current_line + " " + word).strip() if current_line else word
                    if self.font_small.size(candidate)[0] <= max_text_width:
                        current_line = candidate
                        continue

                    # Draw current line and start a new one
                    if current_line:
                        _draw_colored_line(current_line, text_x, bottom_y, name_tokens)
                        bottom_y += line_h
                        lines_drawn += 1
                        if lines_drawn >= max_lines:
                            break
                    current_line = word

                if lines_drawn >= max_lines:
                    break

                if current_line:
                    _draw_colored_line(current_line, text_x, bottom_y, name_tokens)
                    bottom_y += line_h
                    lines_drawn += 1
        else:
            surf = self.font_small.render("No injuries recorded", True, muted_color)
            surface.blit(surf, (col1_x + 4, bottom_y))
            bottom_y += line_h
        bottom_y += 8
        
        # INJURY EFFECTS - full width
        self._draw_section_header(surface, "EFFECTS", col1_x, bottom_y, (220, 180, 100))
        bottom_y += 14
        modifiers = body.get_stat_modifiers()
        if modifiers:
            shown = 0
            for stat, penalty in sorted(modifiers.items()):
                if abs(penalty) > 0.1 and shown < 6:
                    text = f"{stat}: {penalty:+.0f}%"
                    color = (255, 100, 100) if penalty < 0 else (100, 255, 100)
                    surf = self.font_small.render(text, True, color)
                    surface.blit(surf, (col1_x + 4, bottom_y))
                    bottom_y += line_h
                    shown += 1
        else:
            surf = self.font_small.render("None", True, healthy_color)
            surface.blit(surf, (col1_x + 4, bottom_y))
    
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
        
        # Show all relationships (sorted by score)
        shown = 0
        for other, rel_data in relationships:
            if shown >= 12:  # Limit display
                more_text = self.font_small.render("...", True, muted_color)
                surface.blit(more_text, (col1_x + 8, content_y))
                break
            
            other_name = other.name.split()[0]
            label = get_relationship_label(colonist, other)
            score = rel_data["score"]
            color = get_relationship_color(colonist, other)
            
            # Format: "Name - Label (±score)"
            score_sign = "+" if score >= 0 else ""
            rel_text = f"• {other_name} - {label} ({score_sign}{score})"
            
            rel_surf = self.font_small.render(rel_text, True, color)
            surface.blit(rel_surf, (col1_x + 8, content_y))
            content_y += 14
            shown += 1
    
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
    
    def _draw_chat_tab(self, surface, x: int, content_y: int, w: int, col1_x: int) -> None:
        """Draw the Chat tab - per-colonist conversation log."""
        from conversations import get_conversation_log
        
        muted_color = (140, 140, 150)
        header_color = (180, 200, 220)
        my_color = (200, 150, 255)  # Purple for this colonist
        other_color = (150, 255, 200)  # Cyan/green for others
        
        colonist = self.current_colonist
        if not colonist:
            return
        
        # Header
        self._draw_section_header(surface, "Chat Log", col1_x, content_y, header_color)
        content_y += 18
        
        # Get recent conversations from this colonist's perspective
        conversations = get_conversation_log(id(colonist), 15)  # Show up to 15 conversations
        
        if not conversations:
            no_chat = self.font_small.render("(no conversations yet)", True, muted_color)
            surface.blit(no_chat, (col1_x, content_y))
            return
        
        # Draw each conversation from this colonist's perspective
        max_text_width = w - 40
        colonist_first_name = colonist.name.split()[0]
        line_h = 13
        
        def wrap_and_draw_line(text: str, start_x: int, start_y: int, color: tuple, max_width: int) -> int:
            """Wrap text and draw it, returning the final y position."""
            words = text.split()
            current_line = ""
            y = start_y
            
            for word in words:
                candidate = (current_line + " " + word).strip() if current_line else word
                if self.font_small.size(candidate)[0] <= max_width:
                    current_line = candidate
                else:
                    # Draw current line and start a new one
                    if current_line:
                        surf = self.font_small.render(current_line, True, color)
                        surface.blit(surf, (start_x, y))
                        y += line_h
                        if y > 520:
                            return y
                    current_line = word
            
            # Draw final line
            if current_line:
                surf = self.font_small.render(current_line, True, color)
                surface.blit(surf, (start_x, y))
                y += line_h
            
            return y
        
        for convo in conversations:
            if content_y > 520:
                more_text = self.font_small.render("...", True, muted_color)
                surface.blit(more_text, (col1_x, content_y))
                break
            
            other_name = convo.get("other_name", "???").split()[0]  # First name
            my_line = convo.get("my_line", "")
            their_line = convo.get("their_line", "")
            is_speaker = convo.get("is_speaker", True)
            
            # If this colonist spoke first, show their line first
            if is_speaker:
                # My line (purple)
                my_text = f"{colonist_first_name}: {my_line}"
                content_y = wrap_and_draw_line(my_text, col1_x + 4, content_y, my_color, max_text_width)
                
                if content_y > 520:
                    break
                
                # Their response (cyan/green, indented)
                their_text = f"{other_name}: {their_line}"
                content_y = wrap_and_draw_line(their_text, col1_x + 14, content_y, other_color, max_text_width - 10)
                content_y += 2  # Small gap between conversations
            else:
                # They spoke first (cyan/green)
                their_text = f"{other_name}: {their_line}"
                content_y = wrap_and_draw_line(their_text, col1_x + 4, content_y, other_color, max_text_width)
                
                if content_y > 520:
                    break
                
                # My response (purple, indented)
                my_text = f"{colonist_first_name}: {my_line}"
                content_y = wrap_and_draw_line(my_text, col1_x + 14, content_y, my_color, max_text_width - 10)
                content_y += 2  # Small gap between conversations
    
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
        hint_text = self.font_small.render("TAB / Arrows to switch colonists", True, (100, 100, 110))
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


# ============================================================================
# Visitor Interrogation Window - Reuses ColonistManagementPanel with Accept/Deny
# ============================================================================

class VisitorPanel(ColonistManagementPanel):
    """Visitor character sheet - same as colonist panel but with Accept/Deny buttons instead of job tags."""
    
    # Cyberpunk button text
    ACCEPT_TEXT = ">> JACK IN <<"
    DENY_TEXT = "// FLATLINE //"
    
    # Use same tabs as parent but exclude Chat and Help (indices 6, 7)
    # Parent: ["Status", "Bio", "Body", "Links", "Stats", "Mind", "Chat", "Help"]
    # We keep indices 0-5 so content drawing works correctly
    TABS = ["Status", "Bio", "Body", "Links", "Stats", "Mind"]
    
    def __init__(self):
        super().__init__()
        self.wanderer: Optional[dict] = None
        
        # Override panel position - center screen popup (like trader)
        self.panel_width = 450
        self.panel_height = 550
        self.tab_sidebar_width = 70
        
        # Center on screen
        self.panel_rect = pygame.Rect(
            (SCREEN_W - self.panel_width - self.tab_sidebar_width) // 2 + self.tab_sidebar_width,
            (SCREEN_H - self.panel_height) // 2,
            self.panel_width,
            self.panel_height
        )
        self.sidebar_rect = pygame.Rect(
            self.panel_rect.x - self.tab_sidebar_width,
            self.panel_rect.y,
            self.tab_sidebar_width,
            self.panel_height
        )
        
        # Accept/Deny button rects
        self.accept_btn_rect = pygame.Rect(0, 0, 150, 36)
        self.deny_btn_rect = pygame.Rect(0, 0, 150, 36)
        
        # Callbacks
        self.on_accept: Optional[callable] = None
        self.on_deny: Optional[callable] = None
    
    def open(self, wanderer: dict) -> None:
        """Open panel for a specific wanderer."""
        self.wanderer = wanderer
        colonist = wanderer.get("colonist")
        if colonist:
            # Use parent's open with a single-item list
            self.colonists = [colonist]
            self.current_index = 0
            self.visible = True
            self._update_button_positions()
    
    def close(self) -> None:
        super().close()
        self.wanderer = None
    
    def _update_button_positions(self) -> None:
        """Update button positions including Accept/Deny."""
        super()._update_button_positions()
        
        # Accept/Deny buttons replace prev/next
        btn_y = self.panel_rect.bottom - 50
        self.accept_btn_rect.x = self.panel_rect.x + 20
        self.accept_btn_rect.y = btn_y
        self.deny_btn_rect.x = self.panel_rect.right - 170
        self.deny_btn_rect.y = btn_y
    
    def handle_click(self, mouse_pos: tuple[int, int]) -> bool:
        """Handle mouse click with Accept/Deny buttons."""
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
        
        # Check accept button
        if self.accept_btn_rect.collidepoint(mouse_pos):
            if self.on_accept and self.wanderer:
                self.on_accept(self.wanderer)
            self.close()
            return True
        
        # Check deny button
        if self.deny_btn_rect.collidepoint(mouse_pos):
            if self.on_deny and self.wanderer:
                self.on_deny(self.wanderer)
            self.close()
            return True
        
        # Consume click if inside panel or sidebar
        if self.panel_rect.collidepoint(mouse_pos) or self.sidebar_rect.collidepoint(mouse_pos):
            return True
        
        return False
    
    def _draw_navigation_buttons(self, surface: pygame.Surface) -> None:
        """Override to draw Accept/Deny buttons instead of prev/next."""
        # Accept button (cyan/green cyberpunk)
        accept_hover = self.accept_btn_rect.collidepoint(pygame.mouse.get_pos())
        accept_bg = (0, 60, 50) if accept_hover else (0, 40, 35)
        accept_border = (0, 255, 200) if accept_hover else (0, 180, 140)
        pygame.draw.rect(surface, accept_bg, self.accept_btn_rect, border_radius=4)
        pygame.draw.rect(surface, accept_border, self.accept_btn_rect, 2, border_radius=4)
        accept_surf = self.font.render(self.ACCEPT_TEXT, True, accept_border)
        surface.blit(accept_surf, (self.accept_btn_rect.centerx - accept_surf.get_width() // 2,
                                   self.accept_btn_rect.centery - accept_surf.get_height() // 2))
        
        # Deny button (pink/red cyberpunk)
        deny_hover = self.deny_btn_rect.collidepoint(pygame.mouse.get_pos())
        deny_bg = (60, 20, 40) if deny_hover else (40, 15, 25)
        deny_border = (255, 50, 100) if deny_hover else (180, 40, 80)
        pygame.draw.rect(surface, deny_bg, self.deny_btn_rect, border_radius=4)
        pygame.draw.rect(surface, deny_border, self.deny_btn_rect, 2, border_radius=4)
        deny_surf = self.font.render(self.DENY_TEXT, True, deny_border)
        surface.blit(deny_surf, (self.deny_btn_rect.centerx - deny_surf.get_width() // 2,
                                 self.deny_btn_rect.centery - deny_surf.get_height() // 2))
        
        # Visitor status info
        if self.wanderer:
            state = self.wanderer.get("state", "approaching")
            patience = self.wanderer.get("patience", 0)
            patience_pct = int((patience / 3600) * 100) if patience > 0 else 0
            
            status_text = f"STATUS: {state.upper()} | PATIENCE: {patience_pct}%"
            status_surf = self.font_small.render(status_text, True, (100, 120, 130))
            status_x = self.panel_rect.centerx - status_surf.get_width() // 2
            status_y = self.panel_rect.bottom - 18
            surface.blit(status_surf, (status_x, status_y))
    
    def _draw_overview_tab(self, surface, colonist, x: int, content_y: int, w: int, col1_x: int, col2_x: int) -> None:
        """Override to hide job tag toggles for visitors."""
        # Call parent but we'll skip the job tags section by not drawing them
        # Save initial content_y for right column
        initial_content_y = content_y
        
        # === Left Column: Status & Stats ===
        section_color = (180, 200, 220)
        value_color = (220, 220, 230)
        muted_color = (140, 140, 150)
        
        # Current Status (not task, since they're not working)
        self._draw_section_header(surface, "Status", col1_x, content_y, section_color)
        content_y += 18
        
        state = self.wanderer.get("state", "approaching") if self.wanderer else "unknown"
        task_surf = self.font_small.render(state.upper(), True, value_color)
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
        comfort_display = (comfort_val + 10) / 20 * 100
        self._draw_stat_bar(surface, col1_x + 8, content_y, bar_width, comfort_display, 100, comfort_color)
        content_y += 20
        
        # Stress
        self._draw_section_header(surface, "Stress", col1_x, content_y, section_color)
        content_y += 16
        stress_val = getattr(colonist, 'stress', 0.0)
        stress_color = (200, 100, 100) if stress_val > 2 else (200, 200, 100) if stress_val > 0 else (100, 150, 200)
        stress_display = (stress_val + 10) / 20 * 100
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
        
        # === Right Column: Equipment (same as parent) ===
        right_y = initial_content_y
        self._draw_section_header(surface, "Equipment", col2_x, right_y, (200, 180, 140))
        right_y += 20
        
        equipment = getattr(colonist, 'equipment', {})
        self.equipment_slot_rects = {}
        
        slot_names = ["head", "body", "hands", "feet", "implant", "charm"]
        slot_labels = ["Head", "Body", "Hands", "Feet", "Implant", "Charm"]
        
        for slot, label in zip(slot_names, slot_labels):
            item = equipment.get(slot)
            slot_rect = pygame.Rect(col2_x, right_y, 200, 28)
            self.equipment_slot_rects[slot] = (slot_rect, item)
            
            # Slot label
            label_surf = self.font_small.render(f"{label}:", True, muted_color)
            surface.blit(label_surf, (col2_x, right_y + 6))
            
            # Item name or empty
            if item:
                item_name = item.get("name", "Unknown")[:18]
                rarity = item.get("rarity", "common")
                rarity_colors = {
                    "common": (180, 180, 180),
                    "uncommon": (100, 200, 100),
                    "rare": (100, 150, 255),
                    "epic": (200, 100, 255),
                    "legendary": (255, 200, 50),
                }
                item_color = rarity_colors.get(rarity, (180, 180, 180))
                item_surf = self.font.render(item_name, True, item_color)
            else:
                item_surf = self.font_small.render("- empty -", True, (80, 80, 90))
            
            surface.blit(item_surf, (col2_x + 55, right_y + 5))
            right_y += 30


# Global UI instances
_construction_ui: Optional[ConstructionUI] = None
_colonist_panel: Optional[ColonistJobTagsPanel] = None
_colonist_management_panel: Optional[ColonistManagementPanel] = None
_visitor_panel: Optional[VisitorPanel] = None


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


def get_visitor_panel() -> VisitorPanel:
    """Get or create the global visitor panel instance."""
    global _visitor_panel
    if _visitor_panel is None:
        _visitor_panel = VisitorPanel()
    return _visitor_panel
