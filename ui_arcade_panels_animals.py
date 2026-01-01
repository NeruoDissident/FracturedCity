"""Animal list drawing for LeftSidebar.

Separated to keep ui_arcade_panels.py clean.
"""

import arcade
from typing import List

from ui_arcade import (
    COLOR_NEON_CYAN,
    COLOR_NEON_MAGENTA,
    COLOR_TEXT_BRIGHT,
    COLOR_TEXT_NORMAL,
    COLOR_TEXT_DIM,
    COLOR_GOOD,
    COLOR_WARNING,
    COLOR_DANGER,
    UI_FONT,
    UI_FONT_MONO,
)


def draw_animals_tab(sidebar, animals: List, content_y: int) -> None:
    """Draw the ANIMALS tab content for LeftSidebar.
    
    Args:
        sidebar: LeftSidebar instance
        animals: List of Animal objects
        content_y: Y position to start drawing
    """
    # Header
    arcade.draw_text(
        text=f"Animals ({len(animals)})",
        x=sidebar.x + 10,
        y=content_y,
        color=COLOR_NEON_MAGENTA,
        font_size=11,
        bold=True,
        font_name=UI_FONT
    )
    
    content_y += 20
    
    if not animals:
        # No animals message
        arcade.draw_text(
            text="No animals",
            x=sidebar.x + 10,
            y=content_y,
            color=COLOR_TEXT_DIM,
            font_size=10,
            font_name=UI_FONT
        )
        return
    
    # Draw animal list
    for i, animal in enumerate(animals):
        item_y = content_y + i * sidebar.animal_item_height - sidebar.animal_scroll
        
        # Skip if not visible
        if item_y < content_y or item_y > sidebar.y + sidebar.height:
            continue
        
        # Highlight if hovered
        is_hovered = (i == sidebar.hovered_animal_index)
        if is_hovered:
            arcade.draw_lrbt_rectangle_filled(
                left=sidebar.x + 2,
                right=sidebar.x + sidebar.width - 2,
                bottom=item_y,
                top=item_y + sidebar.animal_item_height - 2,
                color=(40, 45, 55)
            )
        
        # Animal species + variant
        species_name = animal.species_data["name"]
        arcade.draw_text(
            text=f"{species_name} #{animal.variant}",
            x=sidebar.x + 10,
            y=item_y + 30,
            color=COLOR_TEXT_BRIGHT,
            font_size=11,
            bold=True,
            font_name=UI_FONT
        )
        
        # State
        state_text = animal.state.value.replace("_", " ").title()
        state_color = _get_animal_state_color(animal.state.value)
        
        arcade.draw_text(
            text=state_text,
            x=sidebar.x + 10,
            y=item_y + 15,
            color=state_color,
            font_size=9,
            font_name=UI_FONT
        )
        
        # Tame progress bar (small)
        bar_x = sidebar.x + 10
        bar_y = item_y + 3
        bar_width = sidebar.width - 40
        bar_height = 6
        
        # Background
        arcade.draw_lrbt_rectangle_filled(
            left=bar_x,
            right=bar_x + bar_width,
            bottom=bar_y,
            top=bar_y + bar_height,
            color=(20, 20, 30)
        )
        
        # Fill
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
            bottom=bar_y,
            top=bar_y + bar_height,
            color=fill_color
        )
        
        # Tame percentage text
        arcade.draw_text(
            text=f"{animal.tame_progress}%",
            x=sidebar.x + sidebar.width - 15,
            y=item_y + 2,
            color=COLOR_TEXT_DIM,
            font_size=8,
            anchor_x="right",
            font_name=UI_FONT_MONO
        )


def _get_animal_state_color(state: str) -> tuple:
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
