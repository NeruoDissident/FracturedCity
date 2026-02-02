"""
Logic for the Fauna (Animals) tab of the Dashboard.
"""

import arcade
from ui_arcade import (
    COLOR_TEXT_BRIGHT, COLOR_TEXT_NORMAL, COLOR_TEXT_DIM,
    UI_FONT, UI_FONT_MONO, COLOR_BG_ELEVATED,
    COLOR_GOOD, COLOR_WARNING, COLOR_DANGER
)

def draw_fauna_tab(dashboard, rect, game_data):
    """Draw the Fauna tab showing animal list."""
    from animals import get_all_animals
    
    x, right, bottom, top = rect
    y = top - dashboard.table_scroll_y
    
    animals = get_all_animals()
    # Filter out dead animals
    animals = [a for a in animals if a.is_alive()]
    
    # Store for click handling
    dashboard.current_table_items = animals
    
    cols = [
        {"label": "SPECIES", "w": 150},
        {"label": "NAME/VARIANT", "w": 150},
        {"label": "STATE", "w": 100},
        {"label": "TAME %", "w": 80},
        {"label": "HEALTH", "w": 100},
    ]
    
    # Header
    header_y = top
    curr_x = x
    arcade.draw_lrbt_rectangle_filled(x, right, header_y - 40, header_y, COLOR_BG_ELEVATED)
    for col in cols:
        arcade.draw_text(col["label"], curr_x + 10, header_y - 25, COLOR_TEXT_DIM, font_size=10, font_name=UI_FONT, bold=True)
        curr_x += col["w"]
        
    row_y = header_y - 40 - dashboard.table_scroll_y
    row_h = 40
    
    for i, animal in enumerate(animals):
        if row_y < bottom - row_h: break
        if row_y > header_y:
            row_y -= row_h
            continue
            
        is_hovered = (i == dashboard.table_hover_row)
        is_selected = (dashboard.selected_item == animal)
        
        if is_selected:
            arcade.draw_lrbt_rectangle_filled(x, right, row_y - row_h, row_y, (40, 30, 50))
            arcade.draw_lrbt_rectangle_outline(x, right, row_y - row_h, row_y, (255, 0, 255), 1)
        elif is_hovered:
            arcade.draw_lrbt_rectangle_filled(x, right, row_y - row_h, row_y, (25, 30, 40))
            
        curr_x = x
        
        # Species
        species = animal.species_data["name"].title()
        arcade.draw_text(species, curr_x + 10, row_y - 25, COLOR_TEXT_BRIGHT, font_size=11, font_name=UI_FONT)
        curr_x += cols[0]["w"]
        
        # Variant
        variant = f"#{animal.variant}"
        arcade.draw_text(variant, curr_x + 10, row_y - 25, COLOR_TEXT_DIM, font_size=10, font_name=UI_FONT_MONO)
        curr_x += cols[1]["w"]
        
        # State
        state = animal.state.value.replace("_", " ").title()
        # Color code state
        state_col = COLOR_TEXT_NORMAL
        if "flee" in state.lower(): state_col = COLOR_WARNING
        elif "sleep" in state.lower(): state_col = COLOR_TEXT_DIM
        elif "hunt" in state.lower(): state_col = COLOR_DANGER
        
        arcade.draw_text(state, curr_x + 10, row_y - 25, state_col, font_size=10, font_name=UI_FONT)
        curr_x += cols[2]["w"]
        
        # Tame %
        tame = animal.tame_progress
        tame_col = COLOR_GOOD if tame >= 100 else (COLOR_WARNING if tame > 0 else COLOR_TEXT_DIM)
        arcade.draw_text(f"{tame}%", curr_x + 10, row_y - 25, tame_col, font_size=10, font_name=UI_FONT_MONO)
        curr_x += cols[3]["w"]
        
        # Health
        hp_pct = (animal.health / animal.species_data["health"]) * 100
        hp_col = COLOR_GOOD if hp_pct > 70 else (COLOR_WARNING if hp_pct > 30 else COLOR_DANGER)
        arcade.draw_text(f"{int(hp_pct)}%", curr_x + 10, row_y - 25, hp_col, font_size=10, font_name=UI_FONT_MONO)
        
        arcade.draw_line(x, row_y, right, row_y, (30, 35, 45), 1)
        row_y -= row_h
