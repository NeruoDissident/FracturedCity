"""
New DF-style Workstation UI Panel.

Replaces the old WorkstationPanel with a two-state system:
1. Main view: Active orders list + "New Order" button
2. Recipe selection view: Recipe list with quantity options (1 / Infinite / Target)

Each order shows: recipe name, progress (X/Y), progress bar, cancel button
Orders are processed FIFO (first in, first out)
"""

import pygame
from typing import Optional, List, Dict, Tuple

# Import constants from ui_layout
try:
    from ui_layout import (
        SCREEN_W, SCREEN_H,
        COLOR_BG_PANEL, COLOR_BG_PANEL_LIGHT,
        COLOR_TEXT_BRIGHT, COLOR_TEXT_DIM,
        COLOR_ACCENT_CYAN, COLOR_ACCENT_CYAN_DIM
    )
except ImportError:
    # Fallback if ui_layout doesn't have these
    SCREEN_W = 1920
    SCREEN_H = 1080
    COLOR_BG_PANEL = (30, 35, 45)
    COLOR_BG_PANEL_LIGHT = (40, 45, 55)
    COLOR_TEXT_BRIGHT = (220, 220, 230)
    COLOR_TEXT_DIM = (140, 140, 150)
    COLOR_ACCENT_CYAN = (0, 200, 255)
    COLOR_ACCENT_CYAN_DIM = (0, 150, 200)


class WorkstationOrderPanel:
    """DF-style workstation UI with order management."""
    
    def __init__(self):
        self.visible = False
        self.workstation_pos: Optional[Tuple[int, int, int]] = None
        self.workstation_data: Optional[dict] = None
        self.recipes: List[dict] = []
        
        # UI state
        self.view_mode = "orders"  # "orders" or "recipe_select"
        self.selecting_recipe: Optional[dict] = None  # Recipe being configured
        
        # Panel dimensions
        self.panel_rect = pygame.Rect(0, 0, 350, 550)  # Increased height to show more recipes
        
        # Fonts
        self.font: Optional[pygame.font.Font] = None
        self.font_small: Optional[pygame.font.Font] = None
        self.font_tiny: Optional[pygame.font.Font] = None
        
        # Clickable rects (rebuilt each frame)
        self.new_order_button_rect: Optional[pygame.Rect] = None
        self.recipe_rects: List[pygame.Rect] = []
        self.order_cancel_rects: List[pygame.Rect] = []
        self.quantity_button_rects: Dict[str, pygame.Rect] = {}  # "single", "infinite", "target_minus", "target_plus"
        self.target_value = 5  # For target quantity input
    
    def init_fonts(self) -> None:
        """Initialize fonts if not already done."""
        if self.font is None:
            self.font = pygame.font.Font(None, 24)
            self.font_small = pygame.font.Font(None, 20)
            self.font_tiny = pygame.font.Font(None, 18)
    
    def open(self, x: int, y: int, z: int, screen_x: int, screen_y: int) -> None:
        """Open the workstation panel at the given position."""
        import buildings
        
        self.workstation_pos = (x, y, z)
        self.workstation_data = buildings.get_workstation(x, y, z)
        if self.workstation_data is None:
            return
        
        # Migrate old craft_queue to new orders system if needed
        self._migrate_old_data()
        
        self.recipes = buildings.get_workstation_recipes(x, y, z)
        self.visible = True
        self.view_mode = "orders"
        self.selecting_recipe = None
        
        # Position panel at static location (center of screen, doesn't block sidebars)
        self.panel_rect.x = 400  # Center-left area
        self.panel_rect.y = 200  # Below top UI bar
    
    def _migrate_old_data(self) -> None:
        """Migrate old craft_queue system to new orders system."""
        ws = self.workstation_data
        if ws is None:
            return
        
        # Initialize orders list if it doesn't exist
        if "orders" not in ws:
            ws["orders"] = []
        
        # Migrate old craft_queue if present
        old_queue = ws.get("craft_queue", 0)
        if old_queue > 0 and len(ws["orders"]) == 0:
            # Convert old queue to a single order
            selected_recipe = ws.get("selected_recipe")
            if selected_recipe:
                ws["orders"].append({
                    "recipe_id": selected_recipe,
                    "quantity_type": "target",
                    "target": old_queue,
                    "completed": 0,
                    "in_progress": False
                })
            ws["craft_queue"] = 0  # Clear old field
    
    def close(self) -> None:
        """Close the panel."""
        self.visible = False
        self.workstation_pos = None
        self.workstation_data = None
        self.recipes = []
        self.view_mode = "orders"
        self.selecting_recipe = None
    
    def handle_click(self, mouse_pos: Tuple[int, int]) -> bool:
        """Handle mouse click. Returns True if consumed."""
        if not self.visible:
            return False
        
        # Click outside panel closes it
        if not self.panel_rect.collidepoint(mouse_pos):
            self.close()
            return True
        
        if self.view_mode == "orders":
            return self._handle_orders_view_click(mouse_pos)
        elif self.view_mode == "recipe_select":
            return self._handle_recipe_select_click(mouse_pos)
        
        return True  # Consume click on panel
    
    def _handle_orders_view_click(self, mouse_pos: Tuple[int, int]) -> bool:
        """Handle clicks in orders view."""
        import buildings
        
        # Check "New Order" button
        if self.new_order_button_rect and self.new_order_button_rect.collidepoint(mouse_pos):
            self.view_mode = "recipe_select"
            self.target_value = 5  # Reset target value
            return True
        
        # Check cancel buttons for each order
        ws = self.workstation_data
        if ws and "orders" in ws:
            for i, rect in enumerate(self.order_cancel_rects):
                if rect.collidepoint(mouse_pos) and i < len(ws["orders"]):
                    # Cancel this order
                    cancelled = ws["orders"].pop(i)
                    print(f"[Workstation] Cancelled order: {cancelled['recipe_id']}")
                    return True
        
        return True
    
    def _handle_recipe_select_click(self, mouse_pos: Tuple[int, int]) -> bool:
        """Handle clicks in recipe selection view."""
        # If a recipe is selected, check quantity buttons FIRST
        # (buttons are drawn on top, so they should be checked first)
        if self.selecting_recipe:
            # Single (craft 1)
            if "single" in self.quantity_button_rects:
                if self.quantity_button_rects["single"].collidepoint(mouse_pos):
                    self._add_order("single", 1)
                    return True
            
            # Infinite
            if "infinite" in self.quantity_button_rects:
                if self.quantity_button_rects["infinite"].collidepoint(mouse_pos):
                    self._add_order("infinite", 0)
                    return True
            
            # Target +/-
            if "target_minus" in self.quantity_button_rects:
                if self.quantity_button_rects["target_minus"].collidepoint(mouse_pos):
                    self.target_value = max(1, self.target_value - 1)
                    return True
            
            if "target_plus" in self.quantity_button_rects:
                if self.quantity_button_rects["target_plus"].collidepoint(mouse_pos):
                    self.target_value = min(999, self.target_value + 1)
                    return True
            
            # Target confirm button
            if "target_confirm" in self.quantity_button_rects:
                if self.quantity_button_rects["target_confirm"].collidepoint(mouse_pos):
                    self._add_order("target", self.target_value)
                    return True
        
        # Check recipe selection (after button checks to avoid blocking buttons)
        for i, rect in enumerate(self.recipe_rects):
            if rect.collidepoint(mouse_pos) and i < len(self.recipes):
                self.selecting_recipe = self.recipes[i]
                return True
        
        return True
    
    def _add_order(self, quantity_type: str, target: int) -> None:
        """Add a new order to the workstation."""
        if not self.selecting_recipe or not self.workstation_data:
            return
        
        ws = self.workstation_data
        if "orders" not in ws:
            ws["orders"] = []
        
        order = {
            "recipe_id": self.selecting_recipe["id"],
            "quantity_type": quantity_type,
            "target": target,
            "completed": 0,
            "in_progress": False
        }
        
        ws["orders"].append(order)
        
        # Print confirmation
        recipe_name = self.selecting_recipe["name"]
        if quantity_type == "single":
            print(f"[Workstation] Added order: {recipe_name} x1")
        elif quantity_type == "infinite":
            print(f"[Workstation] Added order: {recipe_name} (infinite)")
        else:
            print(f"[Workstation] Added order: {recipe_name} x{target}")
        
        # Return to orders view
        self.view_mode = "orders"
        self.selecting_recipe = None
    
    def draw(self, surface: pygame.Surface) -> None:
        """Draw the workstation panel."""
        if not self.visible or self.workstation_data is None:
            return
        
        self.init_fonts()
        
        # Panel background
        pygame.draw.rect(surface, COLOR_BG_PANEL, self.panel_rect, border_radius=6)
        pygame.draw.rect(surface, COLOR_ACCENT_CYAN_DIM, self.panel_rect, 2, border_radius=6)
        
        # Title
        import buildings
        ws_type = self.workstation_data.get("type", "Workstation")
        building_def = buildings.BUILDING_TYPES.get(ws_type, {})
        title = building_def.get("name", ws_type.replace("_", " ").title())
        title_surf = self.font.render(title, True, COLOR_TEXT_BRIGHT)
        surface.blit(title_surf, (self.panel_rect.x + 10, self.panel_rect.y + 10))
        
        # Draw appropriate view
        if self.view_mode == "orders":
            self._draw_orders_view(surface)
        elif self.view_mode == "recipe_select":
            self._draw_recipe_select_view(surface)
    
    def _draw_orders_view(self, surface: pygame.Surface) -> None:
        """Draw the active orders list view."""
        import buildings
        
        ws = self.workstation_data
        orders = ws.get("orders", [])
        
        y = self.panel_rect.y + 45
        
        # "New Order" button
        btn_w = 120
        btn_h = 28
        self.new_order_button_rect = pygame.Rect(
            self.panel_rect.x + 10, y, btn_w, btn_h
        )
        pygame.draw.rect(surface, COLOR_ACCENT_CYAN_DIM, self.new_order_button_rect, border_radius=4)
        pygame.draw.rect(surface, COLOR_ACCENT_CYAN, self.new_order_button_rect, 2, border_radius=4)
        btn_text = self.font_small.render("+ New Order", True, COLOR_TEXT_BRIGHT)
        surface.blit(btn_text, (self.new_order_button_rect.x + 12, self.new_order_button_rect.y + 6))
        
        y += 40
        
        # Orders list
        self.order_cancel_rects.clear()
        
        if not orders:
            empty_text = self.font_small.render("No active orders", True, COLOR_TEXT_DIM)
            surface.blit(empty_text, (self.panel_rect.x + 10, y))
        else:
            for i, order in enumerate(orders):
                if y > self.panel_rect.bottom - 60:
                    break  # Don't overflow panel
                
                # Get recipe info
                recipe = None
                for r in self.recipes:
                    if r["id"] == order["recipe_id"]:
                        recipe = r
                        break
                
                if recipe is None:
                    continue
                
                # Order background
                order_rect = pygame.Rect(self.panel_rect.x + 10, y, self.panel_rect.width - 20, 55)
                bg_color = (45, 50, 60) if order.get("in_progress") else (35, 40, 50)
                pygame.draw.rect(surface, bg_color, order_rect, border_radius=4)
                pygame.draw.rect(surface, (60, 70, 80), order_rect, 1, border_radius=4)
                
                # Recipe name
                name_surf = self.font_small.render(recipe["name"], True, COLOR_TEXT_BRIGHT)
                surface.blit(name_surf, (order_rect.x + 6, order_rect.y + 4))
                
                # Progress text
                completed = order.get("completed", 0)
                if order["quantity_type"] == "infinite":
                    progress_text = f"{completed} / ∞"
                else:
                    target = order.get("target", 1)
                    progress_text = f"{completed} / {target}"
                
                progress_surf = self.font_tiny.render(progress_text, True, COLOR_TEXT_DIM)
                surface.blit(progress_surf, (order_rect.x + 6, order_rect.y + 22))
                
                # Progress bar
                bar_x = order_rect.x + 6
                bar_y = order_rect.y + 38
                bar_w = order_rect.width - 50
                bar_h = 10
                
                # Background
                pygame.draw.rect(surface, (20, 25, 30), (bar_x, bar_y, bar_w, bar_h))
                
                # Fill
                if order["quantity_type"] == "infinite":
                    # Show current item progress if in_progress
                    if order.get("in_progress"):
                        progress_pct = ws.get("progress", 0) / recipe.get("work_time", 100)
                        fill_w = int(bar_w * min(1.0, progress_pct))
                        pygame.draw.rect(surface, COLOR_ACCENT_CYAN, (bar_x, bar_y, fill_w, bar_h))
                else:
                    # Show overall completion
                    target = order.get("target", 1)
                    if target > 0:
                        fill_pct = completed / target
                        fill_w = int(bar_w * min(1.0, fill_pct))
                        pygame.draw.rect(surface, COLOR_ACCENT_CYAN, (bar_x, bar_y, fill_w, bar_h))
                
                # Cancel button
                cancel_w = 35
                cancel_h = 20
                cancel_rect = pygame.Rect(
                    order_rect.right - cancel_w - 6,
                    order_rect.y + 6,
                    cancel_w, cancel_h
                )
                self.order_cancel_rects.append(cancel_rect)
                pygame.draw.rect(surface, (80, 40, 40), cancel_rect, border_radius=3)
                pygame.draw.rect(surface, (120, 60, 60), cancel_rect, 1, border_radius=3)
                cancel_text = self.font_tiny.render("X", True, COLOR_TEXT_BRIGHT)
                surface.blit(cancel_text, (cancel_rect.x + 12, cancel_rect.y + 3))
                
                y += 60
    
    def _draw_recipe_select_view(self, surface: pygame.Surface) -> None:
        """Draw the recipe selection view."""
        y = self.panel_rect.y + 45
        
        # Back hint
        back_text = self.font_tiny.render("Click outside to go back", True, COLOR_TEXT_DIM)
        surface.blit(back_text, (self.panel_rect.x + 10, y))
        y += 25
        
        # Recipe list
        self.recipe_rects.clear()
        
        for i, recipe in enumerate(self.recipes):
            if y > self.panel_rect.bottom - 150:
                break  # Leave room for quantity controls
            
            is_selected = (self.selecting_recipe and self.selecting_recipe["id"] == recipe["id"])
            
            # Recipe rect
            recipe_rect = pygame.Rect(self.panel_rect.x + 10, y, self.panel_rect.width - 20, 40)
            self.recipe_rects.append(recipe_rect)
            
            # Background
            bg_color = (50, 60, 70) if is_selected else (35, 40, 50)
            border_color = COLOR_ACCENT_CYAN if is_selected else (60, 70, 80)
            pygame.draw.rect(surface, bg_color, recipe_rect, border_radius=4)
            pygame.draw.rect(surface, border_color, recipe_rect, 2 if is_selected else 1, border_radius=4)
            
            # Recipe name
            name_surf = self.font_small.render(recipe["name"], True, COLOR_TEXT_BRIGHT)
            surface.blit(name_surf, (recipe_rect.x + 6, recipe_rect.y + 4))
            
            # Cost
            inputs = recipe.get("input", {})
            cost_parts = [f"{amt} {res}" for res, amt in inputs.items()]
            cost_text = ", ".join(cost_parts) if cost_parts else "Free"
            cost_surf = self.font_tiny.render(cost_text, True, COLOR_TEXT_DIM)
            surface.blit(cost_surf, (recipe_rect.x + 6, recipe_rect.y + 22))
            
            y += 45
        
        # Quantity controls (only if recipe selected)
        if self.selecting_recipe:
            y = self.panel_rect.bottom - 110
            
            label_surf = self.font_small.render("Quantity:", True, COLOR_TEXT_BRIGHT)
            surface.blit(label_surf, (self.panel_rect.x + 10, y))
            y += 25
            
            self.quantity_button_rects.clear()
            
            btn_w = 80
            btn_h = 24
            spacing = 10
            x_btn = self.panel_rect.x + 10
            
            # Single button
            single_rect = pygame.Rect(x_btn, y, btn_w, btn_h)
            self.quantity_button_rects["single"] = single_rect
            pygame.draw.rect(surface, (50, 60, 70), single_rect, border_radius=4)
            pygame.draw.rect(surface, (80, 90, 100), single_rect, 1, border_radius=4)
            single_text = self.font_small.render("1", True, COLOR_TEXT_BRIGHT)
            surface.blit(single_text, (single_rect.x + 34, single_rect.y + 4))
            
            x_btn += btn_w + spacing
            
            # Infinite button
            inf_rect = pygame.Rect(x_btn, y, btn_w, btn_h)
            self.quantity_button_rects["infinite"] = inf_rect
            pygame.draw.rect(surface, (50, 60, 70), inf_rect, border_radius=4)
            pygame.draw.rect(surface, (80, 90, 100), inf_rect, 1, border_radius=4)
            inf_text = self.font_small.render("∞", True, COLOR_TEXT_BRIGHT)
            surface.blit(inf_text, (inf_rect.x + 32, inf_rect.y + 4))
            
            y += 35
            
            # Target controls
            target_label = self.font_small.render("Target:", True, COLOR_TEXT_BRIGHT)
            surface.blit(target_label, (self.panel_rect.x + 10, y))
            y += 22
            
            # Minus button
            minus_w = 24
            minus_rect = pygame.Rect(self.panel_rect.x + 10, y, minus_w, btn_h)
            self.quantity_button_rects["target_minus"] = minus_rect
            pygame.draw.rect(surface, (50, 60, 70), minus_rect, border_radius=4)
            pygame.draw.rect(surface, (80, 90, 100), minus_rect, 1, border_radius=4)
            minus_text = self.font_small.render("-", True, COLOR_TEXT_BRIGHT)
            surface.blit(minus_text, (minus_rect.x + 8, minus_rect.y + 4))
            
            # Value display
            value_text = str(self.target_value)
            value_surf = self.font_small.render(value_text, True, COLOR_TEXT_BRIGHT)
            value_x = minus_rect.right + 15
            surface.blit(value_surf, (value_x, y + 4))
            
            # Plus button
            plus_rect = pygame.Rect(value_x + 40, y, minus_w, btn_h)
            self.quantity_button_rects["target_plus"] = plus_rect
            pygame.draw.rect(surface, (50, 60, 70), plus_rect, border_radius=4)
            pygame.draw.rect(surface, (80, 90, 100), plus_rect, 1, border_radius=4)
            plus_text = self.font_small.render("+", True, COLOR_TEXT_BRIGHT)
            surface.blit(plus_text, (plus_rect.x + 7, plus_rect.y + 4))
            
            # Confirm button
            confirm_rect = pygame.Rect(plus_rect.right + 15, y, 80, btn_h)
            self.quantity_button_rects["target_confirm"] = confirm_rect
            pygame.draw.rect(surface, COLOR_ACCENT_CYAN_DIM, confirm_rect, border_radius=4)
            pygame.draw.rect(surface, COLOR_ACCENT_CYAN, confirm_rect, 2, border_radius=4)
            confirm_text = self.font_small.render("Add", True, COLOR_TEXT_BRIGHT)
            surface.blit(confirm_text, (confirm_rect.x + 26, confirm_rect.y + 4))


# Global panel instance
_workstation_order_panel: Optional[WorkstationOrderPanel] = None


def get_workstation_order_panel() -> WorkstationOrderPanel:
    """Get or create the global workstation order panel."""
    global _workstation_order_panel
    if _workstation_order_panel is None:
        _workstation_order_panel = WorkstationOrderPanel()
    return _workstation_order_panel
