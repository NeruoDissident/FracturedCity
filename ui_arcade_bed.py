"""Native Arcade UI for bed assignment panel."""
import arcade
from typing import Optional, List, Tuple

# Screen dimensions
SCREEN_W = 1920
SCREEN_H = 1080


class BedAssignmentPanel:
    """Native Arcade UI panel for assigning colonists to beds."""
    
    def __init__(self):
        self.visible = False
        self.bed_pos: Optional[Tuple[int, int, int]] = None
        self.panel_x = 0
        self.panel_y = 0
        self.panel_width = 280
        self.panel_height = 400
        self.colonist_rects: List[Tuple[float, float, float, float]] = []  # (left, right, bottom, top)
        self.unassign_rects: List[Tuple[float, float, float, float]] = []
        self.scroll_offset = 0
        self.hovered_colonist_idx = -1
        self.max_visible_colonists = 5  # Show 5 colonists at a time
        self.scroll_area_y = 0  # Y position where scrollable area starts
        self.scroll_area_height = 0  # Height of scrollable area
    
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
        # Center the panel on screen for now to debug
        self.panel_x = (SCREEN_W - self.panel_width) / 2
        self.panel_y = (SCREEN_H - self.panel_height) / 2
        
        print(f"[BedPanel] Opened at screen pos ({screen_x}, {screen_y})")
        print(f"[BedPanel] Panel positioned at: X({self.panel_x:.1f} to {self.panel_x + self.panel_width:.1f}), Y({self.panel_y:.1f} to {self.panel_y + self.panel_height:.1f})")
    
    def close(self) -> None:
        """Close the panel."""
        self.visible = False
        self.bed_pos = None
    
    def handle_click(self, mouse_x: int, mouse_y: int, colonists: List) -> bool:
        """Handle click. Returns True if consumed."""
        if not self.visible:
            return False
        
        # Click outside panel closes it
        if not (self.panel_x <= mouse_x <= self.panel_x + self.panel_width and
                self.panel_y <= mouse_y <= self.panel_y + self.panel_height):
            self.close()
            return True
        
        from beds import assign_colonist_to_bed, unassign_colonist, get_bed_occupants
        
        # Check unassign buttons first
        for i, (left, right, bottom, top) in enumerate(self.unassign_rects):
            if left <= mouse_x <= right and bottom <= mouse_y <= top:
                occupants = get_bed_occupants(*self.bed_pos)
                if i < len(occupants):
                    unassign_colonist(occupants[i])
                return True
        
        # Check colonist assignment clicks (accounting for scroll offset)
        for i, (left, right, bottom, top) in enumerate(self.colonist_rects):
            if left <= mouse_x <= right and bottom <= mouse_y <= top:
                unassigned = self._get_unassigned_colonists(colonists)
                actual_index = i + self.scroll_offset
                if actual_index < len(unassigned):
                    colonist = unassigned[actual_index]
                    assign_colonist_to_bed(id(colonist), *self.bed_pos)
                return True
        
        return True  # Consume click on panel
    
    def handle_scroll(self, mouse_x: int, mouse_y: int, scroll_y: float, colonists: List) -> bool:
        """Handle mouse wheel scroll. Returns True if consumed.
        
        Note: mouse_x, mouse_y are already in Arcade coordinates (bottom-left origin).
        """
        if not self.visible:
            return False
        
        # ALWAYS consume scroll when panel is visible and mouse is anywhere on screen
        # This prevents map zoom when the panel is open
        # The panel is modal - if it's open, it should handle all scroll events
        
        # Calculate max scroll based on number of unassigned colonists
        unassigned = self._get_unassigned_colonists(colonists)
        max_scroll = max(0, len(unassigned) - self.max_visible_colonists)
        
        if max_scroll == 0:
            print(f"[BedPanel] No scrolling needed (only {len(unassigned)} colonists)")
            return True  # No scrolling needed, but consume the event
        
        # Update scroll offset (scroll_y is positive for scroll up, negative for scroll down)
        # We want scroll up to decrease offset (show earlier items), scroll down to increase
        old_offset = self.scroll_offset
        self.scroll_offset = max(0, min(max_scroll, self.scroll_offset - int(scroll_y)))
        
        # Debug output
        print(f"[BedPanel] Scrolled from {old_offset} to {self.scroll_offset} (max: {max_scroll}, scroll_y: {scroll_y})")
        
        return True
    
    def _get_unassigned_colonists(self, colonists: List) -> List:
        """Get colonists not assigned to any bed."""
        from beds import get_colonist_bed
        return [c for c in colonists if not c.is_dead and get_colonist_bed(id(c)) is None]
    
    def _get_colonist_by_id(self, colonist_id: int, colonists: List):
        """Find colonist by id()."""
        for c in colonists:
            if id(c) == colonist_id:
                return c
        return None
    
    def draw(self, colonists: List, mouse_x: int, mouse_y: int) -> None:
        """Draw the bed assignment panel.
        
        Args:
            colonists: List of all colonists
            mouse_x: Current mouse X coordinate (Arcade coordinates)
            mouse_y: Current mouse Y coordinate (Arcade coordinates)
        """
        if not self.visible or self.bed_pos is None:
            return
        
        from beds import get_bed_at, get_bed_occupants
        
        bed = get_bed_at(*self.bed_pos)
        if bed is None:
            self.close()
            return
        
        # Store mouse position for hover detection
        self._current_mouse_x = mouse_x
        self._current_mouse_y = mouse_y
        
        # Panel background with gradient effect (darker at edges)
        arcade.draw_lrbt_rectangle_filled(
            self.panel_x, self.panel_x + self.panel_width,
            self.panel_y, self.panel_y + self.panel_height,
            (25, 28, 35)
        )
        
        # Cyberpunk neon border (cyan)
        arcade.draw_lrbt_rectangle_outline(
            self.panel_x, self.panel_x + self.panel_width,
            self.panel_y, self.panel_y + self.panel_height,
            (0, 220, 220), 3
        )
        
        # Inner glow effect
        arcade.draw_lrbt_rectangle_outline(
            self.panel_x + 2, self.panel_x + self.panel_width - 2,
            self.panel_y + 2, self.panel_y + self.panel_height - 2,
            (0, 180, 180, 100), 1
        )
        
        # Title bar background
        arcade.draw_lrbt_rectangle_filled(
            self.panel_x, self.panel_x + self.panel_width,
            self.panel_y + self.panel_height - 50, self.panel_y + self.panel_height,
            (35, 40, 50)
        )
        
        # Title with cyberpunk styling
        arcade.draw_text(
            "CRASH BED",
            self.panel_x + 15,
            self.panel_y + self.panel_height - 32,
            (0, 255, 255),
            font_size=20,
            bold=True,
            font_name="Arial"
        )
        
        # Quality indicator (stars)
        quality = bed.get("quality", 1)
        quality_text = "★" * quality + "☆" * (3 - quality)
        arcade.draw_text(
            quality_text,
            self.panel_x + self.panel_width - 70,
            self.panel_y + self.panel_height - 30,
            (255, 220, 100),
            font_size=16,
            font_name="Arial"
        )
        
        y = self.panel_y + self.panel_height - 70
        
        # Current occupants section
        occupants = get_bed_occupants(*self.bed_pos)
        
        # Section header with neon pink accent
        arcade.draw_text(
            f"ASSIGNED ({len(occupants)}/2)",
            self.panel_x + 15,
            y,
            (255, 50, 130),
            font_size=14,
            bold=True,
            font_name="Arial"
        )
        y -= 30
        
        self.unassign_rects.clear()
        
        if not occupants:
            arcade.draw_text(
                "— No colonists assigned —",
                self.panel_x + 20,
                y,
                (100, 100, 120),
                font_size=13,
                font_name="Arial"
            )
            y -= 30
        else:
            for occ_id in occupants:
                colonist = self._get_colonist_by_id(occ_id, colonists)
                name = colonist.name if colonist else f"#{occ_id}"
                
                # Background for assigned colonist
                arcade.draw_lrbt_rectangle_filled(
                    self.panel_x + 12, self.panel_x + self.panel_width - 12,
                    y - 5, y + 25,
                    (40, 50, 60)
                )
                arcade.draw_lrbt_rectangle_outline(
                    self.panel_x + 12, self.panel_x + self.panel_width - 12,
                    y - 5, y + 25,
                    (0, 180, 180), 1
                )
                
                # Name
                arcade.draw_text(
                    name,
                    self.panel_x + 20,
                    y + 5,
                    (220, 240, 255),
                    font_size=14,
                    font_name="Arial"
                )
                
                # Unassign button (X) - larger and more visible
                x_left = self.panel_x + self.panel_width - 45
                x_right = x_left + 30
                x_bottom = y
                x_top = y + 20
                self.unassign_rects.append((x_left, x_right, x_bottom, x_top))
                
                arcade.draw_lrbt_rectangle_filled(
                    x_left, x_right, x_bottom, x_top,
                    (150, 40, 40)
                )
                arcade.draw_lrbt_rectangle_outline(
                    x_left, x_right, x_bottom, x_top,
                    (255, 80, 80), 2
                )
                arcade.draw_text(
                    "✗",
                    x_left + 8,
                    y + 3,
                    (255, 200, 200),
                    font_size=14,
                    bold=True,
                    font_name="Arial"
                )
                
                y -= 35
        
        y -= 15
        
        # Separator with neon glow
        arcade.draw_line(
            self.panel_x + 15, y,
            self.panel_x + self.panel_width - 15, y,
            (0, 220, 220), 2
        )
        y -= 20
        
        # Available colonists section
        unassigned = self._get_unassigned_colonists(colonists)
        
        # Section header
        arcade.draw_text(
            f"AVAILABLE ({len(unassigned)})",
            self.panel_x + 15,
            y,
            (255, 50, 130),
            font_size=14,
            bold=True,
            font_name="Arial"
        )
        y -= 30
        
        # Store scroll area position for scroll handling
        self.scroll_area_y = y
        self.scroll_area_height = self.max_visible_colonists * 35
        
        self.colonist_rects.clear()
        
        # Can only assign if bed has space
        can_assign = len(occupants) < 2
        
        if not unassigned:
            arcade.draw_text(
                "— All colonists assigned —",
                self.panel_x + 20,
                y,
                (100, 100, 120),
                font_size=13,
                font_name="Arial"
            )
        else:
            # Calculate visible range based on scroll offset
            start_idx = self.scroll_offset
            end_idx = min(start_idx + self.max_visible_colonists, len(unassigned))
            
            # Draw visible colonists
            for list_idx, actual_idx in enumerate(range(start_idx, end_idx)):
                colonist = unassigned[actual_idx]
                
                rect_left = self.panel_x + 12
                rect_right = rect_left + self.panel_width - 24
                rect_bottom = y - 5
                rect_top = y + 25
                self.colonist_rects.append((rect_left, rect_right, rect_bottom, rect_top))
                
                # Check if mouse is hovering
                is_hovered = (rect_left <= mouse_x <= rect_right and 
                             rect_bottom <= mouse_y <= rect_top)
                
                # Background with hover effect
                if can_assign:
                    if is_hovered:
                        # Bright hover state
                        arcade.draw_lrbt_rectangle_filled(
                            rect_left, rect_right, rect_bottom, rect_top,
                            (50, 80, 90)
                        )
                        arcade.draw_lrbt_rectangle_outline(
                            rect_left, rect_right, rect_bottom, rect_top,
                            (0, 255, 255), 2
                        )
                    else:
                        # Normal state
                        arcade.draw_lrbt_rectangle_filled(
                            rect_left, rect_right, rect_bottom, rect_top,
                            (35, 45, 55)
                        )
                        arcade.draw_lrbt_rectangle_outline(
                            rect_left, rect_right, rect_bottom, rect_top,
                            (0, 150, 150), 1
                        )
                else:
                    # Disabled state
                    arcade.draw_lrbt_rectangle_filled(
                        rect_left, rect_right, rect_bottom, rect_top,
                        (30, 30, 35)
                    )
                    arcade.draw_lrbt_rectangle_outline(
                        rect_left, rect_right, rect_bottom, rect_top,
                        (60, 60, 70), 1
                    )
                
                # Name
                text_color = (220, 240, 255) if can_assign else (80, 80, 90)
                arcade.draw_text(
                    colonist.name,
                    rect_left + 10,
                    y + 5,
                    text_color,
                    font_size=14,
                    font_name="Arial"
                )
                
                y -= 35
            
            # Draw scroll indicators if there are more colonists
            if len(unassigned) > self.max_visible_colonists:
                # Scroll position indicator on the right
                scroll_bar_x = self.panel_x + self.panel_width - 8
                scroll_bar_top = self.scroll_area_y
                scroll_bar_bottom = scroll_bar_top - self.scroll_area_height
                
                # Background track
                arcade.draw_line(
                    scroll_bar_x, scroll_bar_bottom,
                    scroll_bar_x, scroll_bar_top,
                    (60, 70, 80), 3
                )
                
                # Calculate thumb position and size
                total_items = len(unassigned)
                visible_ratio = self.max_visible_colonists / total_items
                thumb_height = max(20, self.scroll_area_height * visible_ratio)
                
                scroll_ratio = self.scroll_offset / (total_items - self.max_visible_colonists)
                thumb_travel = self.scroll_area_height - thumb_height
                thumb_top = scroll_bar_top - (scroll_ratio * thumb_travel)
                thumb_bottom = thumb_top - thumb_height
                
                # Draw thumb
                arcade.draw_line(
                    scroll_bar_x, thumb_bottom,
                    scroll_bar_x, thumb_top,
                    (0, 220, 220), 5
                )
                
                # Scroll hints
                if self.scroll_offset > 0:
                    # Up arrow
                    arcade.draw_text(
                        "▲",
                        self.panel_x + self.panel_width - 20,
                        scroll_bar_top + 5,
                        (0, 220, 220),
                        font_size=10,
                        font_name="Arial"
                    )
                
                if self.scroll_offset < total_items - self.max_visible_colonists:
                    # Down arrow
                    arcade.draw_text(
                        "▼",
                        self.panel_x + self.panel_width - 20,
                        scroll_bar_bottom - 15,
                        (0, 220, 220),
                        font_size=10,
                        font_name="Arial"
                    )
        
        # Hint at bottom with cyberpunk styling
        if not can_assign:
            arcade.draw_lrbt_rectangle_filled(
                self.panel_x + 10, self.panel_x + self.panel_width - 10,
                self.panel_y + 10, self.panel_y + 35,
                (60, 40, 40)
            )
            arcade.draw_text(
                "⚠ BED AT CAPACITY",
                self.panel_x + self.panel_width // 2,
                self.panel_y + 18,
                (255, 180, 100),
                font_size=13,
                bold=True,
                anchor_x="center",
                font_name="Arial"
            )


# Global bed assignment panel
_bed_assignment_panel: Optional[BedAssignmentPanel] = None


def get_bed_assignment_panel() -> BedAssignmentPanel:
    """Get or create the global bed assignment panel."""
    global _bed_assignment_panel
    if _bed_assignment_panel is None:
        _bed_assignment_panel = BedAssignmentPanel()
    return _bed_assignment_panel
