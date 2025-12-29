"""
UI Drawing Utilities - Premium Cyberpunk Effects

Helper functions for drawing beautiful UI elements with gradients, glows, and shadows.
"""

import arcade
from typing import Tuple

def draw_gradient_rect(left: float, right: float, bottom: float, top: float, 
                       color_start: Tuple[int, int, int], color_end: Tuple[int, int, int]):
    """Draw a vertical gradient rectangle."""
    # Create color list for gradient
    colors = [
        (*color_start, 255),  # Bottom-left
        (*color_start, 255),  # Bottom-right
        (*color_end, 255),    # Top-right
        (*color_end, 255),    # Top-left
    ]
    
    arcade.draw_lrtb_rectangle_filled(left, right, top, bottom, color_start)
    # Note: Arcade doesn't have native gradient support, so we'll use solid colors
    # with layered semi-transparent overlays for depth

def draw_glowing_border(left: float, right: float, bottom: float, top: float,
                       border_color: Tuple[int, int, int], glow_color: Tuple[int, int, int, int],
                       border_width: int = 2, glow_width: int = 4):
    """Draw a border with outer glow effect."""
    # Outer glow (semi-transparent)
    if len(glow_color) == 4:
        arcade.draw_lrtb_rectangle_outline(
            left - glow_width, right + glow_width, 
            top + glow_width, bottom - glow_width,
            (*glow_color[:3], glow_color[3]), 
            border_width=glow_width
        )
    
    # Main border
    arcade.draw_lrtb_rectangle_outline(
        left, right, top, bottom,
        border_color, 
        border_width=border_width
    )

def draw_panel_background(left: float, right: float, bottom: float, top: float,
                         bg_color: Tuple[int, int, int], 
                         border_color: Tuple[int, int, int],
                         glow_color: Tuple[int, int, int, int] = None):
    """Draw a premium panel with background, border, and optional glow."""
    # Background
    arcade.draw_lrtb_rectangle_filled(left, right, top, bottom, bg_color)
    
    # Subtle inner shadow (darker overlay at top)
    shadow_color = (bg_color[0] - 5, bg_color[1] - 5, bg_color[2] - 5)
    arcade.draw_lrtb_rectangle_filled(left, right, top, top - 20, shadow_color)
    
    # Border with glow
    if glow_color:
        draw_glowing_border(left, right, bottom, top, border_color, glow_color)
    else:
        arcade.draw_lrtb_rectangle_outline(left, right, top, bottom, border_color, 2)

def draw_button(left: float, right: float, bottom: float, top: float,
               text: str, font_size: int = 10,
               bg_color: Tuple[int, int, int] = (30, 35, 50),
               text_color: Tuple[int, int, int] = (240, 250, 255),
               border_color: Tuple[int, int, int] = (60, 80, 120),
               is_hovered: bool = False,
               is_active: bool = False):
    """Draw a premium button with hover and active states."""
    # Adjust colors for state
    if is_active:
        bg_color = (50, 60, 90)
        border_color = (0, 255, 255)
        text_color = (0, 255, 255)
    elif is_hovered:
        bg_color = (40, 45, 65)
        border_color = (80, 100, 140)
    
    # Background with subtle gradient effect
    arcade.draw_lrtb_rectangle_filled(left, right, top, bottom, bg_color)
    
    # Highlight at top
    highlight_color = (bg_color[0] + 10, bg_color[1] + 10, bg_color[2] + 15)
    arcade.draw_lrtb_rectangle_filled(left, right, top, top - 3, highlight_color)
    
    # Border
    arcade.draw_lrtb_rectangle_outline(left, right, top, bottom, border_color, 2)
    
    # Text centered
    center_x = (left + right) / 2
    center_y = (bottom + top) / 2
    arcade.draw_text(
        text=text,
        start_x=center_x,
        start_y=center_y,
        color=text_color,
        font_size=font_size,
        anchor_x="center",
        anchor_y="center",
        bold=True
    )

def draw_stat_bar(left: float, right: float, bottom: float, top: float,
                 value: float, max_value: float = 100.0,
                 bar_color: Tuple[int, int, int] = (0, 255, 150),
                 bg_color: Tuple[int, int, int] = (20, 25, 30),
                 border_color: Tuple[int, int, int] = (40, 50, 60)):
    """Draw a stat bar with value fill."""
    # Background
    arcade.draw_lrtb_rectangle_filled(left, right, top, bottom, bg_color)
    
    # Fill based on value
    if value > 0:
        fill_width = (right - left) * (value / max_value)
        arcade.draw_lrtb_rectangle_filled(left, left + fill_width, top, bottom, bar_color)
    
    # Border
    arcade.draw_lrtb_rectangle_outline(left, right, top, bottom, border_color, 1)
