"""
Logic for the Production/Work tab of the Dashboard.
"""

import arcade
from ui_arcade import (
    COLOR_TEXT_BRIGHT, COLOR_TEXT_NORMAL, COLOR_TEXT_DIM,
    UI_FONT, UI_FONT_MONO, COLOR_BG_ELEVATED,
    COLOR_GOOD, COLOR_WARNING, COLOR_DANGER,
    COLOR_NEON_MAGENTA
)

def draw_production_tab(dashboard, rect, game_data):
    """Draw the Production tab showing workstations."""
    import buildings
    
    x, right, bottom, top = rect
    y = top - dashboard.table_scroll_y
    
    workstations = buildings.get_all_workstations()
    
    # Columns
    cols = [
        {"label": "STATION", "w": 200},
        {"label": "LOCATION", "w": 100},
        {"label": "STATUS", "w": 150},
        {"label": "PROGRESS", "w": 150},
    ]
    
    # Header
    header_y = top
    curr_x = x
    arcade.draw_lrbt_rectangle_filled(x, right, header_y - 40, header_y, COLOR_BG_ELEVATED)
    for col in cols:
        arcade.draw_text(col["label"], curr_x + 10, header_y - 25, COLOR_TEXT_DIM, font_size=10, font_name=UI_FONT, bold=True)
        curr_x += col["w"]
        
    row_y = header_y - 40 - dashboard.table_scroll_y
    row_h = 45
    
    for (wx, wy, wz), data in workstations.items():
        if row_y < bottom - row_h: break
        if row_y > header_y:
            row_y -= row_h
            continue
            
        curr_x = x
        
        # Name
        name = data.get("type", "Unknown Station").replace("_", " ").title()
        arcade.draw_text(name, curr_x + 10, row_y - 28, COLOR_TEXT_BRIGHT, font_size=11, font_name=UI_FONT)
        curr_x += cols[0]["w"]
        
        # Location
        loc_str = f"{wx}, {wy} (Z{wz})"
        arcade.draw_text(loc_str, curr_x + 10, row_y - 28, COLOR_TEXT_DIM, font_size=11, font_name=UI_FONT_MONO)
        curr_x += cols[1]["w"]
        
        # Status
        is_reserved = data.get("reserved", False)
        is_working = data.get("working", False)
        
        if is_working:
            status = "WORKING"
            col = COLOR_GOOD
        elif is_reserved:
            status = "RESERVED"
            col = COLOR_WARNING
        else:
            status = "IDLE"
            col = COLOR_TEXT_DIM
            
        arcade.draw_text(status, curr_x + 10, row_y - 28, col, font_size=10, font_name=UI_FONT, bold=True)
        curr_x += cols[2]["w"]
        
        # Progress
        if is_working:
            progress = data.get("progress", 0)
            # Need max progress (work_time) from recipe... usually stored? 
            # If not stored, just show raw ticks or simple bar
            # Simplified bar:
            bar_w = 100
            bar_h = 8
            arcade.draw_lrbt_rectangle_filled(curr_x + 10, curr_x + 10 + bar_w, row_y - 28, row_y - 20, (40, 40, 50))
            # Just visualizing activity, exact percentage might be tricky without looking up recipe
            # Assuming ~100 ticks avg
            fill_w = min(progress, 100) # Cap for visual
            arcade.draw_lrbt_rectangle_filled(curr_x + 10, curr_x + 10 + fill_w, row_y - 28, row_y - 20, COLOR_NEON_MAGENTA)
        else:
            arcade.draw_text("-", curr_x + 10, row_y - 28, COLOR_TEXT_DIM, font_size=11)
            
        arcade.draw_line(x, row_y, right, row_y, (30, 35, 45), 1)
        row_y -= row_h
