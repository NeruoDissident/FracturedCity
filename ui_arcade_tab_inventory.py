"""
Logic for the Items/Logistics tab of the Dashboard.
Separated to keep dashboard file clean.
"""

import arcade
from typing import Dict, List, Tuple
from ui_arcade import (
    COLOR_TEXT_BRIGHT, COLOR_TEXT_NORMAL, COLOR_TEXT_DIM,
    UI_FONT, UI_FONT_MONO, COLOR_BG_ELEVATED
)

def draw_inventory_tab(dashboard, rect, game_data):
    """Draw the Inventory/Logistics tab."""
    x, right, bottom, top = rect
    y = top - dashboard.table_scroll_y
    
    # Data aggregation (move this to a data helper later if slow)
    # Ideally this should be calculated once per tick/update, not draw
    # But for now we do it here.
    
    # 1. Gather all resources
    resources = game_data.get("resources", {})
    
    # 2. Gather all stored items (from zones)
    import zones
    stored_items = zones.get_all_stored_equipment() # dict of (x,y,z) -> list[item]
    
    # 3. Gather all world items (from items.py)
    import items
    world_items = items.get_all_world_items() # dict of (x,y,z) -> list[item]
    
    # Aggregate counts
    inventory = {} # id -> {count: int, name: str, stockpile: int, map: int}
    
    # Add raw resources first
    for res_id, count in resources.items():
        inventory[res_id] = {
            "name": res_id.replace("_", " ").title(),
            "count": count,
            "stockpile": count, # Resources are abstractly in stockpiles
            "map": 0, # Don't track loose resource nodes here
            "type": "Resource"
        }
        
    # Process Item Objects
    def process_item_list(item_list, location_key):
        for item in item_list:
            iid = item.get("id", "unknown")
            if iid not in inventory:
                inventory[iid] = {
                    "name": item.get("name", iid).title(),
                    "count": 0,
                    "stockpile": 0,
                    "map": 0,
                    "type": "Item"
                }
            inventory[iid]["count"] += 1
            inventory[iid][location_key] += 1

    for loc, item_list in stored_items.items():
        process_item_list(item_list, "stockpile")
        
    for loc, item_list in world_items.items():
        process_item_list(item_list, "map")
        
    # Sort by count desc
    sorted_inv = sorted(inventory.items(), key=lambda i: i[1]["count"], reverse=True)
    
    # Draw Header
    header_y = top
    curr_x = x
    
    cols = [
        {"label": "ITEM NAME", "w": 250},
        {"label": "TOTAL", "w": 80},
        {"label": "IN STOCKPILE", "w": 100},
        {"label": "ON MAP", "w": 80},
    ]
    
    arcade.draw_lrbt_rectangle_filled(x, right, header_y - 40, header_y, COLOR_BG_ELEVATED)
    for col in cols:
        arcade.draw_text(col["label"], curr_x + 10, header_y - 25, COLOR_TEXT_DIM, font_size=10, font_name=UI_FONT, bold=True)
        curr_x += col["w"]
        
    # Draw Rows
    row_y = header_y - 40 - dashboard.table_scroll_y
    row_h = 35
    
    for i, (iid, data) in enumerate(sorted_inv):
        if row_y < bottom - row_h: break
        if row_y > header_y:
            row_y -= row_h
            continue
            
        is_hovered = (i == dashboard.table_hover_row)
        # Highlight logic here if needed
        
        curr_x = x
        
        # Name
        arcade.draw_text(data["name"], curr_x + 10, row_y - 22, COLOR_TEXT_BRIGHT, font_size=11, font_name=UI_FONT)
        curr_x += cols[0]["w"]
        
        # Total
        arcade.draw_text(str(data["count"]), curr_x + 10, row_y - 22, COLOR_TEXT_NORMAL, font_size=11, font_name=UI_FONT_MONO)
        curr_x += cols[1]["w"]
        
        # Stockpile
        arcade.draw_text(str(data["stockpile"]), curr_x + 10, row_y - 22, COLOR_TEXT_DIM, font_size=11, font_name=UI_FONT_MONO)
        curr_x += cols[2]["w"]
        
        # Map
        map_col = (200, 100, 100) if data["map"] > 0 else COLOR_TEXT_DIM
        arcade.draw_text(str(data["map"]), curr_x + 10, row_y - 22, map_col, font_size=11, font_name=UI_FONT_MONO)
        
        arcade.draw_line(x, row_y, right, row_y, (30, 35, 45), 1)
        row_y -= row_h
