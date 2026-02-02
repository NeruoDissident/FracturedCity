"""
Logic for the Jobs/Tasks tab of the Dashboard.
"""

import arcade
from ui_arcade import (
    COLOR_TEXT_BRIGHT, COLOR_TEXT_NORMAL, COLOR_TEXT_DIM,
    UI_FONT, UI_FONT_MONO, COLOR_BG_ELEVATED
)

def draw_jobs_tab(dashboard, rect, game_data):
    """Draw the Jobs tab."""
    import jobs
    
    x, right, bottom, top = rect
    y = top - dashboard.table_scroll_y
    
    job_list = jobs.JOB_QUEUE
    
    cols = [
        {"label": "ID", "w": 50},
        {"label": "TYPE", "w": 150},
        {"label": "PRIORITY", "w": 80},
        {"label": "LOCATION", "w": 120},
        {"label": "ASSIGNED TO", "w": 150},
    ]
    
    # Header
    header_y = top
    curr_x = x
    arcade.draw_lrbt_rectangle_filled(x, right, header_y - 40, header_y, COLOR_BG_ELEVATED)
    for col in cols:
        arcade.draw_text(col["label"], curr_x + 10, header_y - 25, COLOR_TEXT_DIM, font_size=10, font_name=UI_FONT, bold=True)
        curr_x += col["w"]
        
    row_y = header_y - 40 - dashboard.table_scroll_y
    row_h = 35
    
    for i, job in enumerate(job_list):
        if row_y < bottom - row_h: break
        if row_y > header_y:
            row_y -= row_h
            continue
            
        curr_x = x
        
        # ID (Index)
        arcade.draw_text(str(i), curr_x + 10, row_y - 22, COLOR_TEXT_DIM, font_size=10, font_name=UI_FONT_MONO)
        curr_x += cols[0]["w"]
        
        # Type
        jtype = job.type.replace("_", " ").title()
        cat = job.category.title() if job.category else ""
        text = f"{jtype} ({cat})"
        arcade.draw_text(text, curr_x + 10, row_y - 22, COLOR_TEXT_BRIGHT, font_size=11, font_name=UI_FONT)
        curr_x += cols[1]["w"]
        
        # Priority
        prio = jobs.get_job_priority(job)
        arcade.draw_text(str(prio), curr_x + 10, row_y - 22, COLOR_TEXT_NORMAL, font_size=11, font_name=UI_FONT_MONO)
        curr_x += cols[2]["w"]
        
        # Location
        loc = f"{job.x}, {job.y} (Z{job.z})"
        arcade.draw_text(loc, curr_x + 10, row_y - 22, COLOR_TEXT_DIM, font_size=11, font_name=UI_FONT_MONO)
        curr_x += cols[3]["w"]
        
        # Assigned
        assignee = "Unassigned"
        color = COLOR_TEXT_DIM
        if job.assigned:
            # Find who has it
            # This is slow (O(N) search per job), but fine for prototype
            # In real system, job should point to colonist or vice versa
            assignee = "Assigned" # Placeholder since we don't have easy back-ref here without searching colonists
            color = (100, 255, 100)
            
        arcade.draw_text(assignee, curr_x + 10, row_y - 22, color, font_size=11, font_name=UI_FONT)
        
        arcade.draw_line(x, row_y, right, row_y, (30, 35, 45), 1)
        row_y -= row_h
