"""
Native Arcade workstation panel UI.

Replaces Pygame workstation panel with native Arcade implementation.
Two-state system:
1. Orders view: Active orders list + "New Order" button
2. Recipe selection view: Recipe list with quantity options (1x / Infinite / Target)
"""

import arcade
from typing import Optional, List, Dict, Tuple
from ui_arcade import (
    COLOR_BG_PANEL, COLOR_BG_ELEVATED, COLOR_BG_DARK,
    COLOR_NEON_CYAN, COLOR_NEON_PINK, COLOR_NEON_MAGENTA,
    COLOR_TEXT_BRIGHT, COLOR_TEXT_NORMAL, COLOR_TEXT_DIM,
    COLOR_BORDER_BRIGHT, COLOR_BORDER_DIM,
    UI_FONT, UI_FONT_MONO,
    SCREEN_W, SCREEN_H
)


class WorkstationPanel:
    """Native Arcade workstation panel with order management."""
    
    def __init__(self):
        self.visible = False
        self.workstation_pos: Optional[Tuple[int, int, int]] = None
        self.workstation_data: Optional[dict] = None
        self.recipes: List[dict] = []
        
        # UI state
        self.view_mode = "orders"  # "orders" or "recipe_select"
        self.selecting_recipe: Optional[dict] = None
        
        # Panel dimensions
        self.panel_x = 400
        self.panel_y = 150
        self.panel_width = 380
        self.panel_height = 600
        
        # Clickable areas (rebuilt each frame)
        self.new_order_button_rect: Optional[Tuple[float, float, float, float]] = None  # (left, right, bottom, top)
        self.recipe_rects: List[Tuple[float, float, float, float]] = []
        self.order_cancel_rects: List[Tuple[float, float, float, float]] = []
        self.quantity_button_rects: Dict[str, Tuple[float, float, float, float]] = {}
        self.target_value = 5
        
        # Tooltip tracking
        self.hovered_recipe_idx = -1
        self.hovered_order_idx = -1
    
    def open(self, x: int, y: int, z: int) -> None:
        """Open the workstation panel."""
        import buildings
        
        self.workstation_pos = (x, y, z)
        self.workstation_data = buildings.get_workstation(x, y, z)
        if self.workstation_data is None:
            return
        
        # Migrate old data if needed
        self._migrate_old_data()
        
        self.recipes = buildings.get_workstation_recipes(x, y, z)
        self.visible = True
        self.view_mode = "orders"
        self.selecting_recipe = None
    
    def _migrate_old_data(self) -> None:
        """Migrate old craft_queue to orders system."""
        ws = self.workstation_data
        if ws is None:
            return
        
        if "orders" not in ws:
            ws["orders"] = []
        
        old_queue = ws.get("craft_queue", 0)
        if old_queue > 0 and len(ws["orders"]) == 0:
            selected_recipe = ws.get("selected_recipe")
            if selected_recipe:
                ws["orders"].append({
                    "recipe_id": selected_recipe,
                    "quantity_type": "target",
                    "target": old_queue,
                    "completed": 0,
                    "in_progress": False
                })
            ws["craft_queue"] = 0
    
    def close(self) -> None:
        """Close the panel."""
        self.visible = False
        self.workstation_pos = None
        self.workstation_data = None
        self.recipes = []
        self.view_mode = "orders"
        self.selecting_recipe = None
    
    def handle_click(self, x: int, y: int) -> bool:
        """Handle mouse click. Returns True if consumed."""
        if not self.visible:
            return False
        
        # Check if click is inside panel
        if not (self.panel_x <= x <= self.panel_x + self.panel_width and
                self.panel_y <= y <= self.panel_y + self.panel_height):
            self.close()
            return True
        
        if self.view_mode == "orders":
            return self._handle_orders_click(x, y)
        elif self.view_mode == "recipe_select":
            return self._handle_recipe_select_click(x, y)
        
        return True
    
    def _handle_orders_click(self, x: int, y: int) -> bool:
        """Handle clicks in orders view."""
        # Check "New Order" button
        if self.new_order_button_rect:
            left, right, bottom, top = self.new_order_button_rect
            if left <= x <= right and bottom <= y <= top:
                self.view_mode = "recipe_select"
                self.target_value = 5
                return True
        
        # Check cancel buttons
        ws = self.workstation_data
        if ws and "orders" in ws:
            for i, rect in enumerate(self.order_cancel_rects):
                if i < len(ws["orders"]):
                    left, right, bottom, top = rect
                    if left <= x <= right and bottom <= y <= top:
                        cancelled = ws["orders"].pop(i)
                        print(f"[Workstation] Cancelled order: {cancelled['recipe_id']}")
                        return True
        
        return True
    
    def _handle_recipe_select_click(self, x: int, y: int) -> bool:
        """Handle clicks in recipe selection view."""
        # Check quantity buttons if recipe selected
        if self.selecting_recipe:
            for btn_name, rect in self.quantity_button_rects.items():
                left, right, bottom, top = rect
                if left <= x <= right and bottom <= y <= top:
                    if btn_name == "single":
                        self._add_order("single", 1)
                    elif btn_name == "infinite":
                        self._add_order("infinite", 0)
                    elif btn_name == "target_minus":
                        self.target_value = max(1, self.target_value - 1)
                    elif btn_name == "target_plus":
                        self.target_value = min(999, self.target_value + 1)
                    elif btn_name == "target_confirm":
                        self._add_order("target", self.target_value)
                    return True
        
        # Check recipe selection
        for i, rect in enumerate(self.recipe_rects):
            if i < len(self.recipes):
                left, right, bottom, top = rect
                if left <= x <= right and bottom <= y <= top:
                    self.selecting_recipe = self.recipes[i]
                    return True
        
        return True
    
    def _add_order(self, quantity_type: str, target: int) -> None:
        """Add new order to workstation."""
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
        
        recipe_name = self.selecting_recipe["name"]
        if quantity_type == "single":
            print(f"[Workstation] Added order: {recipe_name} x1")
        elif quantity_type == "infinite":
            print(f"[Workstation] Added order: {recipe_name} (infinite)")
        else:
            print(f"[Workstation] Added order: {recipe_name} x{target}")
        
        self.view_mode = "orders"
        self.selecting_recipe = None
    
    def draw(self, mouse_x: int, mouse_y: int) -> None:
        """Draw the workstation panel.
        
        Args:
            mouse_x: Current mouse X coordinate (Arcade coordinates)
            mouse_y: Current mouse Y coordinate (Arcade coordinates)
        """
        if not self.visible:
            return
        
        # Panel background
        arcade.draw_lrbt_rectangle_filled(
            self.panel_x, self.panel_x + self.panel_width,
            self.panel_y, self.panel_y + self.panel_height,
            COLOR_BG_PANEL
        )
        
        # Panel border
        arcade.draw_lrbt_rectangle_outline(
            self.panel_x, self.panel_x + self.panel_width,
            self.panel_y, self.panel_y + self.panel_height,
            COLOR_NEON_CYAN, 2
        )
        
        # Title
        import buildings
        ws_type = self.workstation_data.get("type", "Workstation")
        building_def = buildings.BUILDING_TYPES.get(ws_type, {})
        title = building_def.get("name", ws_type.replace("_", " ").title())
        
        arcade.draw_text(
            title,
            self.panel_x + 12,
            self.panel_y + self.panel_height - 30,
            COLOR_NEON_CYAN,
            font_size=16,
            bold=True,
            font_name=UI_FONT
        )
        
        # Draw appropriate view
        if self.view_mode == "orders":
            self._draw_orders_view(mouse_x, mouse_y)
        elif self.view_mode == "recipe_select":
            self._draw_recipe_select_view(mouse_x, mouse_y)
        
        # Draw tooltip on top of everything
        self._draw_tooltip(mouse_x, mouse_y)
    
    def _draw_orders_view(self, mouse_x: int, mouse_y: int) -> None:
        """Draw active orders list."""
        ws = self.workstation_data
        orders = ws.get("orders", [])
        
        self.hovered_order_idx = -1
        
        y = self.panel_y + self.panel_height - 60
        
        # "New Order" button
        btn_w = 130
        btn_h = 32
        btn_x = self.panel_x + 12
        btn_y = y - btn_h
        
        self.new_order_button_rect = (btn_x, btn_x + btn_w, btn_y, btn_y + btn_h)
        
        arcade.draw_lrbt_rectangle_filled(
            btn_x, btn_x + btn_w, btn_y, btn_y + btn_h,
            COLOR_BG_ELEVATED
        )
        arcade.draw_lrbt_rectangle_outline(
            btn_x, btn_x + btn_w, btn_y, btn_y + btn_h,
            COLOR_NEON_CYAN, 2
        )
        arcade.draw_text(
            "+ New Order",
            btn_x + btn_w / 2,
            btn_y + btn_h / 2,
            COLOR_TEXT_BRIGHT,
            font_size=12,
            bold=True,
            anchor_x="center",
            anchor_y="center",
            font_name=UI_FONT
        )
        
        y -= 50
        
        # Orders list
        self.order_cancel_rects.clear()
        
        if not orders:
            arcade.draw_text(
                "No active orders",
                self.panel_x + 12,
                y,
                COLOR_TEXT_DIM,
                font_size=11,
                font_name=UI_FONT
            )
        else:
            for i, order in enumerate(orders):
                if y < self.panel_y + 20:
                    break
                
                # Get recipe info
                recipe = None
                for r in self.recipes:
                    if r["id"] == order["recipe_id"]:
                        recipe = r
                        break
                
                if not recipe:
                    continue
                
                # Order background
                order_h = 70
                
                # Check if mouse is hovering over this order
                is_hovered = (self.panel_x + 8 <= mouse_x <= self.panel_x + self.panel_width - 8 and
                             y - order_h <= mouse_y <= y)
                if is_hovered:
                    self.hovered_order_idx = i
                bg_color = (45, 50, 60) if is_hovered else COLOR_BG_ELEVATED
                arcade.draw_lrbt_rectangle_filled(
                    self.panel_x + 8, self.panel_x + self.panel_width - 8,
                    y - order_h, y,
                    bg_color
                )
                arcade.draw_lrbt_rectangle_outline(
                    self.panel_x + 8, self.panel_x + self.panel_width - 8,
                    y - order_h, y,
                    COLOR_NEON_CYAN if is_hovered else COLOR_BORDER_DIM, 2 if is_hovered else 1
                )
                
                # Recipe name
                arcade.draw_text(
                    recipe["name"],
                    self.panel_x + 14,
                    y - 18,
                    COLOR_TEXT_BRIGHT,
                    font_size=11,
                    bold=True,
                    font_name=UI_FONT
                )
                
                # Quantity info
                qty_type = order["quantity_type"]
                if qty_type == "single":
                    qty_text = "1x"
                elif qty_type == "infinite":
                    qty_text = f"∞ ({order['completed']} done)"
                else:
                    qty_text = f"{order['completed']}/{order['target']}"
                
                arcade.draw_text(
                    qty_text,
                    self.panel_x + 14,
                    y - 36,
                    COLOR_TEXT_NORMAL,
                    font_size=10,
                    font_name=UI_FONT_MONO
                )
                
                # Progress bar (if target type)
                if qty_type == "target" and order["target"] > 0:
                    bar_x = self.panel_x + 14
                    bar_y = y - 52
                    bar_w = self.panel_width - 100
                    bar_h = 8
                    
                    # Background
                    arcade.draw_lrbt_rectangle_filled(
                        bar_x, bar_x + bar_w, bar_y, bar_y + bar_h,
                        COLOR_BG_DARK
                    )
                    
                    # Fill
                    progress = order["completed"] / order["target"]
                    fill_w = bar_w * progress
                    arcade.draw_lrbt_rectangle_filled(
                        bar_x, bar_x + fill_w, bar_y, bar_y + bar_h,
                        COLOR_NEON_CYAN
                    )
                
                # Cancel button
                cancel_w = 60
                cancel_h = 24
                cancel_x = self.panel_x + self.panel_width - cancel_w - 14
                cancel_y = y - 50
                
                self.order_cancel_rects.append((cancel_x, cancel_x + cancel_w, cancel_y, cancel_y + cancel_h))
                
                arcade.draw_lrbt_rectangle_filled(
                    cancel_x, cancel_x + cancel_w, cancel_y, cancel_y + cancel_h,
                    COLOR_BG_DARK
                )
                arcade.draw_lrbt_rectangle_outline(
                    cancel_x, cancel_x + cancel_w, cancel_y, cancel_y + cancel_h,
                    (200, 80, 80), 1
                )
                arcade.draw_text(
                    "Cancel",
                    cancel_x + cancel_w / 2,
                    cancel_y + cancel_h / 2,
                    (255, 100, 100),
                    font_size=9,
                    anchor_x="center",
                    anchor_y="center",
                    font_name=UI_FONT
                )
                
                y -= order_h + 6
    
    def _draw_recipe_select_view(self, mouse_x: int, mouse_y: int) -> None:
        """Draw recipe selection view."""
        y = self.panel_y + self.panel_height - 60
        
        self.hovered_recipe_idx = -1
        
        # Recipe list
        self.recipe_rects.clear()
        
        for i, recipe in enumerate(self.recipes):
            if y < self.panel_y + 150:
                break
            
            recipe_h = 50
            is_selected = (self.selecting_recipe and self.selecting_recipe["id"] == recipe["id"])
            
            # Check if mouse is hovering
            rect_left = self.panel_x + 8
            rect_right = self.panel_x + self.panel_width - 8
            rect_bottom = y - recipe_h
            rect_top = y
            is_hovered = (rect_left <= mouse_x <= rect_right and rect_bottom <= mouse_y <= rect_top)
            if is_hovered:
                self.hovered_recipe_idx = i
                print(f"[Workstation] Hovering over recipe {i}: {recipe['name']}, rect: ({rect_left}, {rect_right}, {rect_bottom}, {rect_top})")
            
            # Recipe background
            bg_color = (50, 30, 60) if is_selected else ((45, 50, 60) if is_hovered else COLOR_BG_ELEVATED)
            border_color = COLOR_NEON_MAGENTA if is_selected else (COLOR_NEON_CYAN if is_hovered else COLOR_BORDER_DIM)
            
            self.recipe_rects.append((rect_left, rect_right, rect_bottom, rect_top))
            
            arcade.draw_lrbt_rectangle_filled(
                rect_left, rect_right, rect_bottom, rect_top,
                bg_color
            )
            arcade.draw_lrbt_rectangle_outline(
                rect_left, rect_right, rect_bottom, rect_top,
                border_color, 2 if (is_selected or is_hovered) else 1
            )
            
            # Recipe name
            arcade.draw_text(
                recipe["name"],
                self.panel_x + 14,
                y - 18,
                COLOR_NEON_MAGENTA if is_selected else COLOR_TEXT_BRIGHT,
                font_size=11,
                bold=is_selected,
                font_name=UI_FONT
            )
            
            # Inputs - check both "input" and "inputs" keys
            inputs = recipe.get("inputs", recipe.get("input", {}))
            if inputs:
                input_text = ", ".join(f"{amt} {res}" for res, amt in inputs.items())
                arcade.draw_text(
                    f"→ {input_text}",
                    self.panel_x + 14,
                    y - 36,
                    COLOR_TEXT_DIM,
                    font_size=9,
                    font_name=UI_FONT
                )
            
            y -= recipe_h + 4
        
        # Quantity selection (if recipe selected)
        if self.selecting_recipe:
            y = self.panel_y + 80
            
            self.quantity_button_rects.clear()
            
            # Title
            arcade.draw_text(
                "Select Quantity:",
                self.panel_x + 12,
                y + 50,
                COLOR_TEXT_BRIGHT,
                font_size=12,
                bold=True,
                font_name=UI_FONT
            )
            
            # 1x button
            btn_w = 80
            btn_h = 32
            btn_x = self.panel_x + 12
            
            self.quantity_button_rects["single"] = (btn_x, btn_x + btn_w, y, y + btn_h)
            arcade.draw_lrbt_rectangle_filled(btn_x, btn_x + btn_w, y, y + btn_h, COLOR_BG_ELEVATED)
            arcade.draw_lrbt_rectangle_outline(btn_x, btn_x + btn_w, y, y + btn_h, COLOR_NEON_CYAN, 2)
            arcade.draw_text("1x", btn_x + btn_w / 2, y + btn_h / 2, COLOR_TEXT_BRIGHT, 11, anchor_x="center", anchor_y="center", font_name=UI_FONT)
            
            # Infinite button
            btn_x += btn_w + 8
            self.quantity_button_rects["infinite"] = (btn_x, btn_x + btn_w, y, y + btn_h)
            arcade.draw_lrbt_rectangle_filled(btn_x, btn_x + btn_w, y, y + btn_h, COLOR_BG_ELEVATED)
            arcade.draw_lrbt_rectangle_outline(btn_x, btn_x + btn_w, y, y + btn_h, COLOR_NEON_CYAN, 2)
            arcade.draw_text("∞", btn_x + btn_w / 2, y + btn_h / 2, COLOR_TEXT_BRIGHT, 11, anchor_x="center", anchor_y="center", font_name=UI_FONT)
            
            # Target quantity
            y -= 50
            arcade.draw_text("Target:", self.panel_x + 12, y + 8, COLOR_TEXT_NORMAL, 10, font_name=UI_FONT)
            
            # Minus button
            btn_w = 32
            btn_x = self.panel_x + 80
            self.quantity_button_rects["target_minus"] = (btn_x, btn_x + btn_w, y, y + btn_h)
            arcade.draw_lrbt_rectangle_filled(btn_x, btn_x + btn_w, y, y + btn_h, COLOR_BG_ELEVATED)
            arcade.draw_lrbt_rectangle_outline(btn_x, btn_x + btn_w, y, y + btn_h, COLOR_BORDER_DIM, 1)
            arcade.draw_text("-", btn_x + btn_w / 2, y + btn_h / 2, COLOR_TEXT_BRIGHT, 14, anchor_x="center", anchor_y="center", font_name=UI_FONT)
            
            # Value display
            btn_x += btn_w + 4
            btn_w = 50
            arcade.draw_lrbt_rectangle_filled(btn_x, btn_x + btn_w, y, y + btn_h, COLOR_BG_DARK)
            arcade.draw_text(str(self.target_value), btn_x + btn_w / 2, y + btn_h / 2, COLOR_NEON_CYAN, 12, anchor_x="center", anchor_y="center", font_name=UI_FONT_MONO)
            
            # Plus button
            btn_x += btn_w + 4
            btn_w = 32
            self.quantity_button_rects["target_plus"] = (btn_x, btn_x + btn_w, y, y + btn_h)
            arcade.draw_lrbt_rectangle_filled(btn_x, btn_x + btn_w, y, y + btn_h, COLOR_BG_ELEVATED)
            arcade.draw_lrbt_rectangle_outline(btn_x, btn_x + btn_w, y, y + btn_h, COLOR_BORDER_DIM, 1)
            arcade.draw_text("+", btn_x + btn_w / 2, y + btn_h / 2, COLOR_TEXT_BRIGHT, 14, anchor_x="center", anchor_y="center", font_name=UI_FONT)
            
            # Confirm button
            btn_x += btn_w + 8
            btn_w = 80
            self.quantity_button_rects["target_confirm"] = (btn_x, btn_x + btn_w, y, y + btn_h)
            arcade.draw_lrbt_rectangle_filled(btn_x, btn_x + btn_w, y, y + btn_h, (40, 80, 40))
            arcade.draw_lrbt_rectangle_outline(btn_x, btn_x + btn_w, y, y + btn_h, (80, 200, 80), 2)
            arcade.draw_text("Add", btn_x + btn_w / 2, y + btn_h / 2, (150, 255, 150), 11, bold=True, anchor_x="center", anchor_y="center", font_name=UI_FONT)
    
    def _draw_tooltip(self, mouse_x: int, mouse_y: int) -> None:
        """Draw tooltip showing recipe details on hover - full Pygame-style implementation."""
        recipe = None
        
        # Check if hovering over a recipe in recipe select view
        if self.view_mode == "recipe_select" and self.hovered_recipe_idx >= 0:
            if self.hovered_recipe_idx < len(self.recipes):
                recipe = self.recipes[self.hovered_recipe_idx]
                print(f"[Tooltip] Showing tooltip for recipe: {recipe.get('name', 'Unknown')}")
                print(f"[Tooltip] Recipe data: {recipe}")
        
        # Check if hovering over an order in orders view
        elif self.view_mode == "orders" and self.hovered_order_idx >= 0:
            ws = self.workstation_data
            orders = ws.get("orders", [])
            if self.hovered_order_idx < len(orders):
                order = orders[self.hovered_order_idx]
                # Find the recipe for this order
                for r in self.recipes:
                    if r["id"] == order["recipe_id"]:
                        recipe = r
                        break
        
        if not recipe:
            return
        
        # Build tooltip content with proper formatting
        title = recipe.get("name", "Unknown Recipe")
        desc_lines = []
        
        print(f"[Tooltip] Full recipe data: {recipe}")
        
        # Required materials section - check both "input" and "inputs" keys
        inputs = recipe.get("inputs", recipe.get("input", {}))
        print(f"[Tooltip] Recipe inputs: {inputs}, type: {type(inputs)}")
        
        if inputs and isinstance(inputs, dict):
            desc_lines.append("REQUIRED MATERIALS:")
            for resource, amount in inputs.items():
                # Check if we have enough in stockpile
                try:
                    from resources import get_stockpile_amount
                    available = get_stockpile_amount(resource)
                except:
                    available = 0
                status = "✓" if available >= amount else "✗"
                resource_name = resource.replace('_', ' ').title()
                desc_lines.append(f"  {status} {amount}x {resource_name}")
                desc_lines.append(f"     (Have: {available})")
        else:
            print(f"[Tooltip] No valid inputs found or inputs is not a dict")
        
        # Output section - check both "output" and "output_item"
        output_item = recipe.get("output_item")
        output_dict = recipe.get("output", {})
        
        if output_dict and isinstance(output_dict, dict):
            if desc_lines:
                desc_lines.append("")
            desc_lines.append("PRODUCES:")
            for item, amount in output_dict.items():
                desc_lines.append(f"  {amount}x {item.replace('_', ' ').title()}")
        elif output_item:
            if desc_lines:
                desc_lines.append("")
            desc_lines.append("PRODUCES:")
            desc_lines.append(f"  {output_item.replace('_', ' ').title()}")
        
        # Craft time if available - check both "time" and "work_time"
        craft_time = recipe.get("time", recipe.get("work_time", 0))
        if craft_time > 0:
            if desc_lines:
                desc_lines.append("")
            desc_lines.append(f"Time: {craft_time} ticks")
        
        print(f"[Tooltip] desc_lines count: {len(desc_lines)}")
        if len(desc_lines) > 0:
            print(f"[Tooltip] First few lines: {desc_lines[:5]}")
        else:
            print("[Tooltip] WARNING: No description lines generated!")
        
        # Calculate tooltip size with proper padding
        padding = 16
        line_spacing = 18
        title_font_size = 16
        desc_font_size = 12
        
        # Measure text to get proper width
        max_width = 250  # Minimum width
        
        # Title width
        title_width = len(title) * (title_font_size * 0.6)  # Rough estimate
        max_width = max(max_width, title_width + padding * 2)
        
        # Description lines width
        for line in desc_lines:
            line_width = len(line) * (desc_font_size * 0.6)
            max_width = max(max_width, line_width + padding * 2)
        
        tooltip_width = min(max_width, 400)  # Cap at 400px
        tooltip_height = padding * 2 + title_font_size + line_spacing
        tooltip_height += len(desc_lines) * (desc_font_size + 4)
        
        print(f"[Tooltip] Calculated dimensions: {tooltip_width}x{tooltip_height}")
        
        # Position tooltip near mouse, but keep on screen
        # Try to the right first
        tooltip_x = mouse_x + 15
        tooltip_y = mouse_y - tooltip_height // 2
        
        # Keep on screen horizontally
        if tooltip_x + tooltip_width > SCREEN_W - 10:
            tooltip_x = mouse_x - tooltip_width - 15
        if tooltip_x < 10:
            tooltip_x = 10
        
        # Keep on screen vertically
        if tooltip_y + tooltip_height > SCREEN_H - 10:
            tooltip_y = SCREEN_H - tooltip_height - 10
        if tooltip_y < 10:
            tooltip_y = 10
        
        # Draw shadow
        shadow_offset = 4
        arcade.draw_lrbt_rectangle_filled(
            tooltip_x + shadow_offset, tooltip_x + tooltip_width + shadow_offset,
            tooltip_y - shadow_offset, tooltip_y + tooltip_height - shadow_offset,
            (15, 15, 20, 180)
        )
        
        # Draw tooltip background (darker, more opaque)
        arcade.draw_lrbt_rectangle_filled(
            tooltip_x, tooltip_x + tooltip_width,
            tooltip_y, tooltip_y + tooltip_height,
            (45, 45, 55, 250)
        )
        
        # Draw tooltip border (thicker, brighter)
        arcade.draw_lrbt_rectangle_outline(
            tooltip_x, tooltip_x + tooltip_width,
            tooltip_y, tooltip_y + tooltip_height,
            (70, 70, 90), 2
        )
        
        # Draw title
        text_y = tooltip_y + tooltip_height - padding - title_font_size
        arcade.draw_text(
            title,
            tooltip_x + padding,
            text_y,
            (255, 220, 150),  # Gold color for title
            font_size=title_font_size,
            bold=True,
            font_name=UI_FONT
        )
        text_y -= line_spacing
        
        # Draw separator line
        arcade.draw_line(
            tooltip_x + padding, text_y + 6,
            tooltip_x + tooltip_width - padding, text_y + 6,
            (80, 80, 100), 1
        )
        text_y -= 6
        
        # Draw description lines
        for line in desc_lines:
            if not line:  # Empty line for spacing
                text_y -= desc_font_size // 2
                continue
            
            # Color based on content
            if line.endswith(":"):
                # Section headers
                color = (150, 180, 220)  # Light blue
                bold = True
            elif "✓" in line:
                # Available items
                color = (100, 220, 100)  # Green
                bold = False
            elif "✗" in line:
                # Missing items
                color = (220, 100, 100)  # Red
                bold = False
            elif line.startswith("     "):
                # Sub-info (Have: X)
                color = (140, 140, 150)  # Gray
                bold = False
            else:
                # Regular text
                color = (220, 220, 220)  # White
                bold = False
            
            arcade.draw_text(
                line,
                tooltip_x + padding,
                text_y,
                color,
                font_size=desc_font_size,
                bold=bold,
                font_name=UI_FONT
            )
            text_y -= desc_font_size + 4


# Singleton instance
_workstation_panel: Optional[WorkstationPanel] = None


def get_workstation_panel() -> WorkstationPanel:
    """Get the singleton workstation panel instance."""
    global _workstation_panel
    if _workstation_panel is None:
        _workstation_panel = WorkstationPanel()
    return _workstation_panel
