"""Game entry point and high-level orchestration.

This module wires together the core systems (grid, colonists, buildings) and
hosts the Pygame event loop. All simulation and rendering behavior should live
in dedicated modules so this file stays small and focused on flow control.
"""

import os
import sys
import subprocess
import pygame

from config import (
    SCREEN_W,
    SCREEN_H,
    TILE_SIZE,
    COLONIST_COUNT,
    GRID_W,
    GRID_H,
    COLOR_BG_NORMAL,
    COLOR_BG_ETHER,
    COLOR_DRAG_PREVIEW,
)
from grid import Grid
from colonist import create_colonists, update_colonists, draw_colonists
from buildings import place_wall, place_wall_advanced, place_door, place_floor, place_window, place_fire_escape, process_supply_jobs, update_doors, update_windows
import buildings as buildings_module
import jobs as jobs_module
from resources import spawn_resource_nodes, create_gathering_job_for_node, get_stockpile, update_resource_nodes, get_resource_balance, process_auto_haul_jobs, mark_item_for_hauling, get_all_resource_items
import resources as resources_module
from ui import get_construction_ui
from zones import create_stockpile_zone
import zones as zones_module
from debug_overlay import toggle_debug, draw_debug
import rooms as rooms_module
from rooms import update_rooms


# Drag selection state
_drag_start: tuple[int, int] | None = None
_drag_mode: str | None = None  # "wall", "harvest", or "stockpile"


def get_drag_line(start: tuple[int, int], end: tuple[int, int]) -> list[tuple[int, int]]:
    """Return list of tiles in a 1-tile wide line from start to end.
    
    For walls, we only allow 1-tile wide drags (horizontal or vertical line).
    If dragged diagonally, snaps to the longer axis.
    """
    x1, y1 = start
    x2, y2 = end
    
    dx = abs(x2 - x1)
    dy = abs(y2 - y1)
    
    tiles = []
    
    if dx >= dy:
        # Horizontal line (or single tile)
        min_x, max_x = min(x1, x2), max(x1, x2)
        for x in range(min_x, max_x + 1):
            tiles.append((x, y1))  # Use start y
    else:
        # Vertical line
        min_y, max_y = min(y1, y2), max(y1, y2)
        for y in range(min_y, max_y + 1):
            tiles.append((x1, y))  # Use start x
    
    return tiles


def get_drag_rect(start: tuple[int, int], end: tuple[int, int]) -> list[tuple[int, int]]:
    """Return list of all tiles in a rectangle from start to end."""
    x1, y1 = start
    x2, y2 = end
    
    min_x, max_x = min(x1, x2), max(x1, x2)
    min_y, max_y = min(y1, y2), max(y1, y2)
    
    tiles = []
    for x in range(min_x, max_x + 1):
        for y in range(min_y, max_y + 1):
            tiles.append((x, y))
    
    return tiles


def handle_mouse_down(grid: Grid, event: pygame.event.Event, colonists: list) -> None:
    """Handle mouse button press."""
    global _drag_start, _drag_mode
    
    mx, my = pygame.mouse.get_pos()
    ui = get_construction_ui()
    
    # Check new UI layout first (sidebar clicks)
    from ui_layout import get_ui_layout
    ui_layout = get_ui_layout()
    sidebar_action = ui_layout.handle_click((mx, my))
    if sidebar_action:
        # Direct tool selection - set the tool directly
        ui.action_bar.current_tool = sidebar_action
        ui.action_bar._close_all_menus()
        return
    
    # Check colonist management panel first (only if visible)
    from ui import get_colonist_management_panel
    mgmt_panel = get_colonist_management_panel()
    if mgmt_panel.visible and mgmt_panel.handle_click((mx, my)):
        return
    
    # Check if click was in sidebar or bottom bar area (consumed but no action)
    if ui_layout.left_sidebar.rect.collidepoint(mx, my):
        return
    if ui_layout.bottom_bar.rect.collidepoint(mx, my):
        return
    
    # If click is in UI panels, don't process as map click
    if ui_layout.is_point_in_ui(mx, my):
        # Still let existing UI handle it for bottom bar
        if ui.handle_click((mx, my), event.button):
            return
        return
    
    # Check colonist panel
    from ui import get_colonist_panel
    colonist_panel = get_colonist_panel()
    if colonist_panel.handle_click((mx, my)):
        return
    
    # Check stockpile filter panel
    from ui import get_stockpile_filter_panel
    filter_panel = get_stockpile_filter_panel()
    if filter_panel.handle_click((mx, my)):
        return
    
    # Check workstation panel
    from ui import get_workstation_panel
    ws_panel = get_workstation_panel()
    if ws_panel.handle_click((mx, my)):
        return
    
    # Check bed assignment panel
    from ui import get_bed_assignment_panel
    bed_panel = get_bed_assignment_panel()
    if bed_panel.handle_click((mx, my), colonists):
        return
    
    # Check fixer trade panel
    from ui import get_fixer_trade_panel
    trade_panel = get_fixer_trade_panel()
    if trade_panel.handle_click((mx, my), zones_module):
        return
    
    # Check visitor panel
    from ui import get_visitor_panel
    visitor_panel = get_visitor_panel()
    if visitor_panel.handle_click((mx, my)):
        return
    
    # Check notification clicks (jump camera to location)
    from notifications import handle_notification_click
    click_loc = handle_notification_click((mx, my))
    if click_loc:
        grid.center_camera_on(click_loc[0], click_loc[1])
        return
    
    # Let UI handle click first
    if ui.handle_click((mx, my), event.button):
        return
    
    # Convert screen coordinates to world tile coordinates
    gx, gy = grid.screen_to_world(mx, my)
    
    if not (0 <= gx < GRID_W and 0 <= gy < GRID_H):
        return

    if event.button == 1:  # left click
        build_mode = ui.get_build_mode()
        current_z = grid.current_z
        
        # Handle "allow" mode - start drag for roof access on any Z > 0
        if build_mode == "allow":
            if current_z == 0:
                print(f"[Allow] Cannot use Allow on ground level - only on rooftops (Z > 0)")
                return
            _drag_start = (gx, gy)
            _drag_mode = "allow"
            return
        
        # Building modes - allow on both Z levels (individual tile checks happen on placement)
        if build_mode in ("wall", "wall_advanced", "door", "window"):
            # Start drag for structure construction (line)
            _drag_start = (gx, gy)
            _drag_mode = build_mode
        elif build_mode == "floor":
            # Start drag for floor construction (rectangle)
            _drag_start = (gx, gy)
            _drag_mode = "floor"
        elif build_mode == "roof":
            # Start drag for roof placement (rectangle) - requires 4 corner walls
            _drag_start = (gx, gy)
            _drag_mode = "roof"
        elif build_mode == "fire_escape":
            # Fire escape - single click placement on finished walls (any Z level)
            if place_fire_escape(grid, gx, gy, current_z):
                z_info = f" on Z={current_z}" if current_z > 0 else ""
                print(f"[Build] Fire escape placed at ({gx}, {gy}){z_info}")
            else:
                print(f"[Build] Cannot place fire escape at ({gx}, {gy}) - needs finished wall with exterior space")
        elif build_mode == "bridge":
            # Bridge - single click placement, must be adjacent to fire escape platform or another bridge
            from buildings import place_bridge
            if place_bridge(grid, gx, gy, current_z):
                pass  # Success message printed by place_bridge
            else:
                print(f"[Build] Cannot place bridge at ({gx}, {gy}) - must be adjacent to fire escape platform or bridge")
        elif build_mode == "salvagers_bench":
            # Salvager's Bench - single click placement on floor inside room
            from buildings import place_salvagers_bench
            if place_salvagers_bench(grid, gx, gy, current_z):
                print(f"[Build] Salvager's Bench placed at ({gx}, {gy})")
            else:
                print(f"[Build] Cannot place Salvager's Bench at ({gx}, {gy}) - needs floor inside room")
        elif build_mode == "generator":
            # Generator - single click placement on floor inside room
            from buildings import place_generator
            if place_generator(grid, gx, gy, current_z):
                print(f"[Build] Generator placed at ({gx}, {gy})")
            else:
                print(f"[Build] Cannot place Generator at ({gx}, {gy}) - needs floor inside room")
        elif build_mode == "stove":
            # Stove - single click placement on floor inside room
            from buildings import place_stove
            if place_stove(grid, gx, gy, current_z):
                print(f"[Build] Stove placed at ({gx}, {gy})")
            else:
                print(f"[Build] Cannot place Stove at ({gx}, {gy}) - needs floor inside room")
        elif build_mode == "gutter_forge":
            # Gutter Forge - single click placement on floor inside room
            from buildings import place_gutter_forge
            if place_gutter_forge(grid, gx, gy, current_z):
                print(f"[Build] Gutter Forge placed at ({gx}, {gy})")
            else:
                print(f"[Build] Cannot place Gutter Forge at ({gx}, {gy}) - needs floor inside room")
        elif build_mode == "skinshop_loom":
            # Skinshop Loom - single click placement on floor inside room
            from buildings import place_skinshop_loom
            if place_skinshop_loom(grid, gx, gy, current_z):
                print(f"[Build] Skinshop Loom placed at ({gx}, {gy})")
            else:
                print(f"[Build] Cannot place Skinshop Loom at ({gx}, {gy}) - needs floor inside room")
        elif build_mode == "cortex_spindle":
            # Cortex Spindle - single click placement on floor inside room
            from buildings import place_cortex_spindle
            if place_cortex_spindle(grid, gx, gy, current_z):
                print(f"[Build] Cortex Spindle placed at ({gx}, {gy})")
            else:
                print(f"[Build] Cannot place Cortex Spindle at ({gx}, {gy}) - needs floor inside room")
        elif build_mode in buildings_module.BUILDING_TYPES and buildings_module.BUILDING_TYPES[build_mode].get("workstation"):
            # Generic workstation placement using shared rules (floor + roofed room)
            from buildings import place_workstation_generic
            ws_def = buildings_module.BUILDING_TYPES[build_mode]
            ws_name = ws_def.get("name", build_mode).replace("_", " ")
            if place_workstation_generic(grid, gx, gy, build_mode, current_z):
                print(f"[Build] {ws_name} placed at ({gx}, {gy})")
            else:
                print(f"[Build] Cannot place {ws_name} at ({gx}, {gy}) - needs floor inside room")
        elif build_mode and build_mode.startswith("furn_"):
            # Generic furniture placement - install crafted furniture from stockpiles
            from buildings import request_furniture_install
            item_id = build_mode[len("furn_"):]
            if request_furniture_install(grid, gx, gy, current_z, item_id):
                print(f"[Build] Furniture install requested: {item_id} at ({gx}, {gy}, z={current_z})")
            else:
                print(f"[Build] Cannot install {item_id} at ({gx}, {gy}, z={current_z})")
        elif build_mode == "stockpile":
            # Start drag for stockpile zone (rectangle) - works on both Z levels
            _drag_start = (gx, gy)
            _drag_mode = "stockpile"
        elif build_mode == "harvest":
            # Combined harvest + haul tool - ground level only
            if current_z != 0:
                return
            _drag_start = (gx, gy)
            _drag_mode = "harvest"
        elif build_mode == "demolish":
            # Demolish tool - drag to select area
            _drag_start = (gx, gy)
            _drag_mode = "demolish"
        elif build_mode == "salvage":
            # Salvage tool - drag to designate salvage objects
            _drag_start = (gx, gy)
            _drag_mode = "salvage"
        elif build_mode is None:
            # No tool selected - check for wanderer, colonist, or stockpile zone
            
            # Check for fixer first (trader)
            from wanderers import get_fixer_at
            fixer = get_fixer_at(gx, gy, current_z)
            if fixer is not None:
                # Open trade panel
                from ui import get_fixer_trade_panel
                trade_panel = get_fixer_trade_panel()
                trade_panel.open(fixer)
                return
            
            # Check for wanderer (potential recruit) - open visitor panel
            from wanderers import get_wanderer_at, recruit_wanderer, reject_wanderer
            wanderer = get_wanderer_at(gx, gy, current_z)
            if wanderer is not None:
                # Open visitor panel instead of auto-recruiting
                from ui import get_visitor_panel
                visitor_panel = get_visitor_panel()
                
                def accept_visitor(w, cols=colonists):
                    new_colonist = recruit_wanderer(w)
                    if new_colonist:
                        cols.append(new_colonist)
                        from notifications import add_notification, NotificationType
                        add_notification(NotificationType.ARRIVAL,
                                       "// LINK ESTABLISHED //",
                                       f"{new_colonist.name} has jacked in",
                                       duration=360)
                
                def deny_visitor(w):
                    reject_wanderer(w)
                    from notifications import add_notification, NotificationType
                    add_notification(NotificationType.INFO,
                                   "// CONNECTION TERMINATED //",
                                   f"{w['name']} flatlined",
                                   duration=240)
                
                visitor_panel.on_accept = accept_visitor
                visitor_panel.on_deny = deny_visitor
                visitor_panel.open(wanderer)
                return
            
            # Check if clicking on a colonist (within 1 tile radius)
            clicked_colonist = None
            for colonist in colonists:
                if colonist.z == current_z:  # Same Z-level
                    dx = abs(colonist.x - gx)
                    dy = abs(colonist.y - gy)
                    if dx <= 0 and dy <= 0:  # Exact tile
                        clicked_colonist = colonist
                        break
            
            if clicked_colonist is not None:
                # Open colonist management panel (includes job tags)
                from ui import get_colonist_management_panel
                mgmt_panel = get_colonist_management_panel()
                mgmt_panel.open_for_colonist(colonists, clicked_colonist)
            else:
                # Check if clicking on a workstation (open recipe panel)
                tile = grid.get_tile(gx, gy, current_z)
                
                # Check for bed first
                if tile == "crash_bed":
                    from beds import get_bed_at
                    from ui import get_bed_assignment_panel
                    bed = get_bed_at(gx, gy, current_z)
                    if bed is not None:
                        bed_panel = get_bed_assignment_panel()
                        bed_panel.open(gx, gy, current_z, mx, my)
                elif tile and tile.startswith("finished_"):
                    ws = buildings_module.get_workstation(gx, gy, current_z)
                    if ws is not None:
                        # Open workstation panel
                        from ui import get_workstation_panel
                        ws_panel = get_workstation_panel()
                        ws_panel.open(gx, gy, current_z, mx, my)
                    else:
                        # Check if clicking on stockpile zone for filter UI
                        from ui import get_stockpile_filter_panel
                        zone_id = zones_module.get_zone_id_at(gx, gy, current_z)
                        if zone_id is not None:
                            panel = get_stockpile_filter_panel()
                            panel.open(zone_id, mx, my)
                else:
                    # Check if clicking on stockpile zone for filter UI
                    from ui import get_stockpile_filter_panel
                    zone_id = zones_module.get_zone_id_at(gx, gy, current_z)
                    if zone_id is not None:
                        panel = get_stockpile_filter_panel()
                        panel.open(zone_id, mx, my)


def handle_mouse_up(grid: Grid, event: pygame.event.Event) -> None:
    """Handle mouse button release."""
    global _drag_start, _drag_mode
    
    ui = get_construction_ui()
    
    if event.button == 1:  # left release
        if _drag_start is not None:
            mx, my = pygame.mouse.get_pos()
            # Convert screen coordinates to world tile coordinates
            gx, gy = grid.screen_to_world(mx, my)
            gx = max(0, min(GRID_W - 1, gx))
            gy = max(0, min(GRID_H - 1, gy))
            current_z = grid.current_z
            
            if _drag_mode in ("wall", "wall_advanced", "door", "window"):
                # Get all tiles in the line (structures are 1-tile wide)
                tiles = get_drag_line(_drag_start, (gx, gy))
                
                # Place structures on all tiles in line
                structures_placed = 0
                for tx, ty in tiles:
                    if _drag_mode == "wall":
                        if place_wall(grid, tx, ty, current_z):
                            structures_placed += 1
                    elif _drag_mode == "wall_advanced":
                        if place_wall_advanced(grid, tx, ty, current_z):
                            structures_placed += 1
                    elif _drag_mode == "door":
                        if place_door(grid, tx, ty, current_z):
                            structures_placed += 1
                    elif _drag_mode == "window":
                        if place_window(grid, tx, ty, current_z):
                            structures_placed += 1
                
                if structures_placed > 0:
                    name = {"wall": "wall", "wall_advanced": "reinforced wall", "door": "door", "window": "window"}[_drag_mode]
                    z_info = f" on z={current_z}" if current_z > 0 else ""
                    print(f"Designated {structures_placed} {name}(s) for construction{z_info}")
            
            elif _drag_mode == "floor":
                # Get all tiles in rectangle
                tiles = get_drag_rect(_drag_start, (gx, gy))
                
                # Place floors on all empty tiles in rectangle
                floors_placed = 0
                for tx, ty in tiles:
                    if place_floor(grid, tx, ty, current_z):
                        floors_placed += 1
                
                if floors_placed > 0:
                    z_info = f" on z={current_z}" if current_z > 0 else ""
                    print(f"Designated {floors_placed} floor(s) for construction{z_info}")
            
            elif _drag_mode == "roof":
                # Place roof over rectangular area - requires 4 corner walls
                start_x, start_y = _drag_start
                end_x, end_y = gx, gy
                
                try:
                    from rooms import place_roof_area, can_place_roof_area
                    can_place, reason = can_place_roof_area(grid, start_x, start_y, end_x, end_y, current_z)
                    if can_place:
                        if place_roof_area(grid, start_x, start_y, end_x, end_y, current_z):
                            pass  # Success message printed by place_roof_area
                    else:
                        print(f"[Roof] Cannot place roof: {reason}")
                except Exception as e:
                    import traceback
                    print(f"[Roof] ERROR: {e}")
                    traceback.print_exc()
            
            elif _drag_mode == "stockpile":
                # Get all tiles in rectangle
                tiles = get_drag_rect(_drag_start, (gx, gy))
                
                # create_stockpile_zone handles validation internally based on Z-level
                # It will automatically trim invalid tiles
                tiles_3d = [(tx, ty, current_z) for tx, ty in tiles]
                zone_id = create_stockpile_zone(tiles_3d, grid, z=current_z)
                if zone_id > 0:
                    zone_info = zones_module.get_zone_info(zone_id)
                    tile_count = zone_info["tile_count"] if zone_info else len(tiles)
                    z_info = f" on z={current_z}" if current_z > 0 else ""
                    print(f"Created stockpile zone with {tile_count} tile(s){z_info}")
            
            elif _drag_mode == "harvest":
                # Combined harvest + haul tool
                # Get all tiles in rectangle
                tiles = get_drag_rect(_drag_start, (gx, gy))
                
                # Create gathering jobs for all resource nodes in selection
                # Also add designations for persistent highlighting
                jobs_created = 0
                streets_designated = 0
                items_marked = 0
                resource_items = get_all_resource_items()
                
                for tx, ty in tiles:
                    tile = grid.get_tile(tx, ty, current_z)
                    # Harvest resource nodes (only on ground level)
                    if current_z == 0 and tile == "resource_node":
                        if create_gathering_job_for_node(jobs_module, grid, tx, ty):
                            jobs_created += 1
                            # Add designation for persistent highlighting
                            jobs_module.add_designation(tx, ty, current_z, "harvest", "harvest")
                    # Harvest streets (converts to scorched, yields mineral)
                    elif current_z == 0 and tile in ("street", "street_cracked", "street_scar", "street_ripped"):
                        if resources_module.designate_street_for_harvest(grid, tx, ty, jobs_module):
                            streets_designated += 1
                            jobs_module.add_designation(tx, ty, current_z, "harvest", "harvest")
                    # Harvest sidewalks (converts to scorched, yields mineral)
                    elif current_z == 0 and tile == "sidewalk":
                        if resources_module.designate_sidewalk_for_harvest(grid, tx, ty, jobs_module):
                            streets_designated += 1  # Count with streets
                            jobs_module.add_designation(tx, ty, current_z, "harvest", "harvest")
                    # Also mark any loose items for hauling (on current Z level)
                    if (tx, ty, current_z) in resource_items:
                        if mark_item_for_hauling(tx, ty, current_z):
                            items_marked += 1
                            # Add designation for persistent highlighting
                            jobs_module.add_designation(tx, ty, current_z, "haul", "haul")
                
                if jobs_created > 0 or streets_designated > 0 or items_marked > 0:
                    parts = []
                    if jobs_created > 0:
                        parts.append(f"{jobs_created} resource(s) for harvesting")
                    if streets_designated > 0:
                        parts.append(f"{streets_designated} street(s) for mining")
                    if items_marked > 0:
                        parts.append(f"{items_marked} item(s) for hauling")
                    print(f"Designated {' and '.join(parts)}")
            
            elif _drag_mode == "allow":
                # Allow tool - convert roof tiles to walkable/buildable roof_access
                # Works on any Z > 0
                tiles = get_drag_rect(_drag_start, (gx, gy))
                
                allowed_count = 0
                disallowed_count = 0
                
                for tx, ty in tiles:
                    current_tile = grid.get_tile(tx, ty, z=current_z)
                    if current_tile == "roof":
                        # Convert roof to roof_access (walkable/buildable)
                        grid.set_tile(tx, ty, "roof_access", z=current_z)
                        allowed_count += 1
                    elif current_tile == "roof_access":
                        # Convert back to roof (non-walkable)
                        grid.set_tile(tx, ty, "roof", z=current_z)
                        disallowed_count += 1
                
                if allowed_count > 0 or disallowed_count > 0:
                    parts = []
                    if allowed_count > 0:
                        parts.append(f"allowed {allowed_count} tile(s)")
                    if disallowed_count > 0:
                        parts.append(f"disallowed {disallowed_count} tile(s)")
                    print(f"[Allow] {' and '.join(parts)} on Z={current_z}")
            
            elif _drag_mode == "demolish":
                # Demolish tool - remove structures in selection
                from buildings import demolish_tile
                tiles = get_drag_rect(_drag_start, (gx, gy))
                
                demolished_count = 0
                for tx, ty in tiles:
                    if demolish_tile(grid, tx, ty, current_z):
                        demolished_count += 1
                
                if demolished_count > 0:
                    z_info = f" on Z={current_z}" if current_z > 0 else ""
                    print(f"[Demolish] Removed {demolished_count} structure(s){z_info}")
            
            elif _drag_mode == "salvage":
                # Salvage tool - designate salvage objects for dismantling
                from resources import designate_salvage, get_salvage_object_at, get_salvage_work_time
                tiles = get_drag_rect(_drag_start, (gx, gy))
                
                designated_count = 0
                for tx, ty in tiles:
                    tile = grid.get_tile(tx, ty, 0)
                    if tile == "salvage_object":
                        if designate_salvage(tx, ty):
                            # Create salvage job
                            work_time = get_salvage_work_time(tx, ty)
                            jobs_module.add_job(
                                "salvage",
                                tx, ty,
                                required=work_time,
                                category="salvage",
                                z=0,
                            )
                            # Add designation for persistent highlighting
                            jobs_module.add_designation(tx, ty, 0, "salvage", "salvage")
                            designated_count += 1
                
                if designated_count > 0:
                    print(f"[Salvage] Designated {designated_count} object(s) for salvage")
            
            _drag_start = None
            _drag_mode = None


def get_hovered_tile(grid: Grid) -> tuple[int, int] | None:
    """Return grid coords of tile under mouse, or None if out of bounds.
    
    Args:
        grid: Grid object for screen-to-world coordinate conversion
    """
    mx, my = pygame.mouse.get_pos()
    gx, gy = grid.screen_to_world(mx, my)
    if 0 <= gx < GRID_W and 0 <= gy < GRID_H:
        return (gx, gy)
    return None


def get_drag_preview_tiles(grid: Grid) -> list[tuple[int, int]]:
    """Return list of tiles in current drag selection, or empty if not dragging.
    
    Args:
        grid: Grid object for screen-to-world coordinate conversion
    """
    if _drag_start is None:
        return []
    
    hovered = get_hovered_tile(grid)
    if hovered is None:
        return [_drag_start]
    
    # Use line for walls/doors, rectangle for floors/harvest/stockpile/haul
    if _drag_mode in ("wall", "wall_advanced", "door"):
        return get_drag_line(_drag_start, hovered)
    else:
        return get_drag_rect(_drag_start, hovered)


def draw_drag_preview(surface: pygame.Surface, grid: Grid, camera_x: int = 0, camera_y: int = 0) -> None:
    """Draw semi-transparent preview of drag selection.
    
    Args:
        surface: Pygame surface to draw on
        grid: Grid object for coordinate conversion
        camera_x, camera_y: Camera offset for viewport rendering
    """
    tiles = get_drag_preview_tiles(grid)
    if not tiles:
        return
    
    # Create a semi-transparent surface for the preview
    for tx, ty in tiles:
        # World position in pixels
        world_x = tx * TILE_SIZE
        world_y = ty * TILE_SIZE
        
        # Screen position (apply camera offset)
        screen_x = world_x - camera_x
        screen_y = world_y - camera_y
        
        rect = pygame.Rect(screen_x, screen_y, TILE_SIZE, TILE_SIZE)
        # Draw filled rectangle with alpha
        preview_surface = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        preview_surface.fill(COLOR_DRAG_PREVIEW)
        surface.blit(preview_surface, rect.topleft)


def draw_stockpile_ui(surface: pygame.Surface) -> None:
    """Draw stockpiled resources in the top-left corner.
    
    Shows resources actually stored in stockpile zones (usable for construction).
    """
    font = pygame.font.Font(None, 24)
    
    y_offset = 10
    x_offset = 10
    line_height = 20
    
    # Resource colors matching node types
    resource_colors = {
        "wood": (139, 90, 43),    # brown
        "scrap": (120, 120, 120), # gray
        "metal": (180, 180, 200), # silver-blue
        "mineral": (80, 200, 200), # teal
        "power": (255, 220, 80),  # yellow
        "raw_food": (180, 220, 100),  # light green
        "cooked_meal": (220, 160, 80),  # orange
    }
    
    # Display names for resources
    display_names = {
        "raw_food": "Raw Food",
        "cooked_meal": "Meals",
    }
    
    # Show stockpiled amounts from zones
    for resource_type in ["wood", "mineral", "scrap", "metal", "power", "raw_food", "cooked_meal"]:
        stored = zones_module.get_total_stored(resource_type)
        color = resource_colors.get(resource_type, (200, 200, 200))
        name = display_names.get(resource_type, resource_type.capitalize())
        text = f"{name}: {stored}"
        text_surface = font.render(text, True, color)
        surface.blit(text_surface, (x_offset, y_offset))
        y_offset += line_height


def main() -> None:
    """Run the main game loop."""
    from save_system import quicksave, quickload

    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("Colony Prototype")
    clock = pygame.time.Clock()

    grid = Grid()
    # Generate world (streets, lots, ruins) and get colonist spawn location
    spawn_x, spawn_y = spawn_resource_nodes(grid)
    
    # Create colonists at the spawn location
    colonists = create_colonists(COLONIST_COUNT, spawn_x, spawn_y)
    
    # Center camera on colonist spawn location
    spawn_center_x = spawn_x * TILE_SIZE
    spawn_center_y = spawn_y * TILE_SIZE
    # Initialize camera position
    grid.camera_x = spawn_center_x - SCREEN_W // 2
    grid.camera_y = spawn_center_y - SCREEN_H // 2
    # Clamp to valid range
    grid.pan_camera(0, 0)
    
    ether_mode = False
    paused = False
    game_speed = 1  # 1-5, controls simulation speed
    tick_count = 0

    running = True
    while running:
        tick_count += 1
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                # Let lists panel handle keys first
                from lists_ui import get_lists_panel
                lists_panel = get_lists_panel()
                if lists_panel.handle_event(event):
                    continue  # Lists panel consumed the event
                
                # Let management panel handle keys first (for arrow navigation)
                from ui import get_colonist_management_panel
                mgmt_panel = get_colonist_management_panel()
                if mgmt_panel.handle_key(event.key):
                    pass  # Management panel consumed the key
                # Let UI handle keybinds
                elif get_construction_ui().handle_key(event.key):
                    pass  # UI consumed the key
                elif event.key == pygame.K_e:
                    ether_mode = not ether_mode
                elif event.key == pygame.K_i:
                    toggle_debug()
                elif event.key == pygame.K_SPACE:
                    # Toggle pause
                    paused = not paused
                    print(f"[Game] {'PAUSED' if paused else 'RESUMED'}")
                elif event.key == pygame.K_1:
                    game_speed = 1
                    print(f"[Game] Speed: 1x (Normal)")
                elif event.key == pygame.K_2:
                    game_speed = 2
                    print(f"[Game] Speed: 2x")
                elif event.key == pygame.K_3:
                    game_speed = 3
                    print(f"[Game] Speed: 3x")
                elif event.key == pygame.K_4:
                    game_speed = 4
                    print(f"[Game] Speed: 4x")
                elif event.key == pygame.K_5:
                    game_speed = 5
                    print(f"[Game] Speed: 5x (Max)")
                elif event.key == pygame.K_F6:
                    # Quick save
                    quicksave(grid, colonists, zones_module, buildings_module, resources_module, jobs_module)
                elif event.key == pygame.K_F9:
                    # Quick load
                    if quickload(grid, colonists, zones_module, buildings_module, resources_module, jobs_module):
                        print("[Load] Game state restored")
                # Z-level switching with PageUp/PageDown or +/-
                elif event.key in (pygame.K_PAGEUP, pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS):
                    new_z = min(grid.current_z + 1, grid.depth - 1)
                    if new_z != grid.current_z:
                        grid.set_current_z(new_z)
                        print(f"[View] Switched to Z-level {new_z}")
                elif event.key in (pygame.K_PAGEDOWN, pygame.K_MINUS, pygame.K_KP_MINUS):
                    new_z = max(grid.current_z - 1, 0)
                    if new_z != grid.current_z:
                        grid.set_current_z(new_z)
                        print(f"[View] Switched to Z-level {new_z}")
                elif event.key == pygame.K_F5:
                    # Hard restart - re-run the game
                    print("[Restart] Restarting game...")
                    pygame.quit()
                    script_path = os.path.abspath(__file__)
                    subprocess.Popen([sys.executable, script_path])
                    sys.exit(0)
                elif event.key == pygame.K_F7:
                    # Debug: Spawn wanderers (refugees) and fixer (trader)
                    from wanderers import _pick_group_spawn_location, _create_wanderer_at, _wanderers, _create_fixer, _fixers
                    from resources import get_colonist_spawn_location
                    from notifications import add_notification, NotificationType
                    import random
                    
                    colony_center = get_colonist_spawn_location()
                    
                    # Pick ONE spawn location for the group
                    group_spawn = _pick_group_spawn_location(grid)
                    if group_spawn:
                        # Spawn 1-3 wanderers around that point
                        num_wanderers = random.randint(1, 3)
                        spawned_names = []
                        for i in range(num_wanderers):
                            offset_x = (i % 3) - 1
                            offset_y = (i // 3) - 1
                            spawn_x = group_spawn[0] + offset_x
                            spawn_y = group_spawn[1] + offset_y
                            if not grid.is_walkable(spawn_x, spawn_y, 0):
                                spawn_x, spawn_y = group_spawn
                            
                            wanderer = _create_wanderer_at(spawn_x, spawn_y, colony_center, grid)
                            if wanderer:
                                _wanderers.append(wanderer)
                                spawned_names.append(wanderer["name"])
                        
                        if spawned_names:
                            print(f"[Debug] Spawned {len(spawned_names)} wanderer(s): {', '.join(spawned_names)}")
                            add_notification(NotificationType.ARRIVAL,
                                           f"// {len(spawned_names)} SIGNAL(S) DETECTED //",
                                           ", ".join(spawned_names),
                                           duration=480,
                                           click_location=group_spawn)
                            # Jump camera to them
                            grid.center_camera_on(group_spawn[0], group_spawn[1])
                    
                    # Also spawn a fixer if none exists
                    if len(_fixers) == 0:
                        fixer = _create_fixer(colony_center, grid)
                        if fixer:
                            _fixers.append(fixer)
                            print(f"[Debug] Spawned fixer: {fixer['name']} from {fixer['origin'].name}")
                            fixer_loc = (fixer["x"], fixer["y"])
                            add_notification(NotificationType.INFO,
                                           "// FIXER INBOUND //",
                                           f"{fixer['name']} wants to trade",
                                           duration=480,
                                           click_location=fixer_loc)
                    else:
                        print("[Debug] Fixer already present, skipping")
                elif event.key == pygame.K_F8:
                    # Debug: Print construction site status
                    from buildings import get_all_construction_sites, get_missing_materials
                    sites = get_all_construction_sites()
                    print(f"[Debug] Construction sites: {len(sites)}")
                    for (x, y, z), site in sites.items():
                        missing = get_missing_materials(x, y, z)
                        print(f"  ({x},{y},z={z}) type={site.get('type')} needed={site.get('materials_needed')} delivered={site.get('materials_delivered')} missing={missing}")
                    # Also print stockpile contents
                    print("[Debug] Stockpile contents:")
                    for res_type in ["wood", "scrap", "metal", "mineral", "power"]:
                        total = zones_module.get_total_stored(res_type)
                        print(f"  {res_type}: {total}")
                elif event.key == pygame.K_F10:
                    # Debug: Spawn test item at first colonist's location
                    from items import spawn_world_item, get_all_world_items
                    if colonists:
                        c = colonists[0]
                        spawn_world_item(c.x, c.y, c.z, "work_gloves")
                        print(f"[Debug] Spawned work_gloves at ({c.x},{c.y},z={c.z})")
                        print(f"[Debug] World items: {get_all_world_items()}")
                elif event.key == pygame.K_F11:
                    # Debug: Print workstation status
                    from buildings import _WORKSTATIONS, get_workstation_recipe
                    print(f"[Debug] Registered workstations: {len(_WORKSTATIONS)}")
                    for (x, y, z), ws in _WORKSTATIONS.items():
                        recipe = get_workstation_recipe(x, y, z)
                        recipe_name = recipe.get("name", "?") if recipe else "None"
                        print(f"  ({x},{y},z={z}) type={ws.get('type')} recipe={recipe_name} reserved={ws.get('reserved')} working={ws.get('working')}")
                elif event.key == pygame.K_F12:
                    # Debug: Toggle BERSERK MODE - everyone fights everyone
                    from combat import CombatStance
                    alive = [c for c in colonists if not c.is_dead]
                    if alive:
                        # Check if already berserk (toggle off)
                        if getattr(alive[0], '_debug_berserk', False):
                            # Turn off berserk
                            for c in alive:
                                c._debug_berserk = False
                                c.is_hostile = False
                                c.in_combat = False
                                c.combat_target = None
                            print("[Debug] BERSERK MODE OFF - peace restored")
                            from notifications import add_notification, NotificationType
                            add_notification(NotificationType.INFO,
                                           "// PEACE PROTOCOL //",
                                           "Combat systems disengaged",
                                           duration=180)
                        else:
                            # UNLEASH HELL
                            for c in alive:
                                c._debug_berserk = True
                                c.is_hostile = True
                                c.state = "idle"
                                c.current_job = None
                            print(f"[Debug] BERSERK MODE ON - {len(alive)} colonists going wild!")
                            from notifications import add_notification, NotificationType
                            add_notification(NotificationType.FIGHT_START,
                                           "// BERSERK PROTOCOL //",
                                           f"All {len(alive)} colonists hostile!",
                                           duration=300)
                elif event.key == pygame.K_TAB:
                    # TAB cycles to next colonist in right panel
                    from ui import get_colonist_management_panel
                    mgmt_panel = get_colonist_management_panel()
                    mgmt_panel._next_colonist()
                elif event.key == pygame.K_l:
                    # L key switches to COLONISTS tab in sidebar
                    ui_layout.left_sidebar.current_tab = 0  # COLONISTS is now tab 0
                # ESC keybinding removed - use window close button to quit

            if event.type == pygame.MOUSEBUTTONDOWN:
                # Ignore scroll wheel (4, 5) and middle mouse (2) - not used
                if event.button in (2, 4, 5):
                    continue
                
                # Check top bar speed controls first
                from ui_layout import get_ui_layout
                ui_layout = get_ui_layout()
                mx, my = pygame.mouse.get_pos()
                consumed, speed_val = ui_layout.top_bar.handle_click((mx, my), {"paused": paused, "game_speed": game_speed})
                if consumed:
                    if speed_val == -1:  # Toggle pause
                        paused = not paused
                        print(f"[Game] {'PAUSED' if paused else 'RESUMED'}")
                    elif speed_val > 0:  # Set speed
                        game_speed = speed_val
                        print(f"[Game] Speed: {game_speed}x")
                    continue
                
                handle_mouse_down(grid, event, colonists)
            
            if event.type == pygame.MOUSEBUTTONUP:
                # Ignore scroll wheel and middle mouse
                if event.button in (2, 4, 5):
                    continue
                handle_mouse_up(grid, event)
            
        # Camera controls (WASD or Arrow keys)
        keys = pygame.key.get_pressed()
        camera_speed = 20  # pixels per frame
        if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
            camera_speed = 40  # Faster with Shift
        
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            grid.pan_camera(0, -camera_speed)
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            grid.pan_camera(0, camera_speed)
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            grid.pan_camera(-camera_speed, 0)
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            grid.pan_camera(camera_speed, 0)

        # Update notifications (even when paused so they fade)
        from notifications import update_notifications
        update_notifications()
        
        # Only update simulation when not paused
        if not paused:
          for _ in range(game_speed):  # Run multiple ticks based on speed
            # Advance game time
            from time_system import tick_time
            tick_time()
            
            update_colonists(colonists, grid, tick_count)
            update_resource_nodes(grid)
            update_doors()  # Auto-close doors after delay
            update_windows()  # Auto-close windows after delay
            tick_count += 1  # Increment game tick
            
            # Process batched room updates (dirty tiles from construction)
            rooms_module.process_dirty_rooms(grid)
            
            jobs_module.update_job_timers()  # Tick down job wait timers
            
            # Process auto-haul jobs for harvested resources
            process_auto_haul_jobs(jobs_module, zones_module)
            
            # Process supply jobs for construction sites
            process_supply_jobs(jobs_module, zones_module)
            
            # Process crafting jobs for workstations
            from buildings import process_crafting_jobs
            process_crafting_jobs(jobs_module, zones_module)
            
            # Process equipment haul jobs (crafted items on ground)
            from items import process_equipment_haul_jobs, process_auto_equip
            process_equipment_haul_jobs(jobs_module, zones_module)
            
            # Process auto-equip (colonists claim items matching preferences)
            process_auto_equip(colonists, zones_module, jobs_module)
            
            # Process stockpile relocation (items from zones being removed)
            zones_module.process_stockpile_relocation(jobs_module)
            
            # Process filter mismatch relocation (resources on stockpiles that no longer allow them)
            zones_module.process_filter_mismatch_relocation(jobs_module)
            
            # Update wanderers (potential recruits) and fixers (traders)
            from wanderers import spawn_wanderer_check, update_wanderers, spawn_fixer_check, update_fixers
            from time_system import get_game_time
            from resources import get_colonist_spawn_location
            colony_center = get_colonist_spawn_location()
            current_day = get_game_time().day
            new_wanderers = spawn_wanderer_check(current_day, colony_center, grid)
            
            # Notify player of new visitors (clickable to jump camera)
            if new_wanderers:
                from notifications import add_notification, NotificationType
                count = len(new_wanderers)
                group_spawn = new_wanderers[0].get("group_spawn")
                
                if count == 1:
                    name = new_wanderers[0]["name"]
                    add_notification(NotificationType.ARRIVAL, 
                                   f"// SIGNAL DETECTED //",
                                   f"{name} approaches the colony",
                                   duration=480,
                                   click_location=group_spawn)
                else:
                    names = ", ".join(w["name"] for w in new_wanderers[:3])
                    if count > 3:
                        names += f" +{count - 3} more"
                    add_notification(NotificationType.ARRIVAL,
                                   f"// {count} SIGNALS DETECTED //",
                                   names,
                                   duration=480,
                                   click_location=group_spawn)
                
                # Auto-jump camera to group spawn location
                if group_spawn:
                    grid.center_camera_on(group_spawn[0], group_spawn[1])
            
            update_wanderers(grid, colony_center, tick_count)
            spawn_fixer_check(current_day, colony_center, grid)
            update_fixers(grid, colony_center, tick_count)
            
            # Process trade jobs (colonists physically exchange goods with fixers)
            from wanderers import process_trade_jobs
            process_trade_jobs(jobs_module, zones_module)
        
        # Update UI
        ui = get_construction_ui()
        ui.update(pygame.mouse.get_pos())

        if ether_mode:
            screen.fill(COLOR_BG_ETHER)
        else:
            screen.fill(COLOR_BG_NORMAL)

        grid.draw(screen, hovered_tile=None)
        
        # Draw drag preview on top of grid (left-click drag in build mode)
        if _drag_start is not None and pygame.mouse.get_pressed()[0]:
            draw_drag_preview(screen, grid, camera_x=grid.camera_x, camera_y=grid.camera_y)
        
        draw_colonists(screen, colonists, ether_mode=ether_mode, current_z=grid.current_z, camera_x=grid.camera_x, camera_y=grid.camera_y)
        
        # Draw wanderers (potential recruits)
        from wanderers import draw_wanderers
        draw_wanderers(screen, current_z=grid.current_z, camera_x=grid.camera_x, camera_y=grid.camera_y)
        
        # Draw day/night tint overlay
        from time_system import get_screen_tint, get_display_string
        tint = get_screen_tint()
        if tint[3] > 0:  # Only draw if alpha > 0
            tint_overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            tint_overlay.fill(tint)
            screen.blit(tint_overlay, (0, 0))
        
        # Draw new UI layout (top bar, left sidebar, bottom bar)
        from ui_layout import get_ui_layout, LEFT_SIDEBAR_WIDTH, TOP_BAR_HEIGHT, BOTTOM_BAR_HEIGHT
        ui_layout = get_ui_layout()
        
        # Gather game data for UI
        game_data = {
            "time_str": get_display_string(),
            "z_level": grid.current_z,
            "paused": paused,
            "game_speed": game_speed,
            "resources": {
                "wood": zones_module.get_total_stored("wood"),
                "scrap": zones_module.get_total_stored("scrap"),
                "metal": zones_module.get_total_stored("metal"),
                "mineral": zones_module.get_total_stored("mineral"),
                "power": zones_module.get_total_stored("power"),
                "raw_food": zones_module.get_total_stored("raw_food"),
                "cooked_meal": zones_module.get_total_stored("cooked_meal"),
            },
            "colonists": [{"name": c.name, "status": c.current_job.type if c.current_job else "Idle"} 
                         for c in colonists if not c.is_dead],
            "colonist_objects": [c for c in colonists if not c.is_dead],  # Actual colonist objects
            "current_tool": ui.get_build_mode(),
            "job_count": len(jobs_module.get_all_available_jobs()),
            "jobs_module": jobs_module,
        }
        
        # Wire up sidebar callbacks for colonist clicks
        from ui import get_colonist_management_panel
        _mgmt_panel = get_colonist_management_panel()
        ui_layout.left_sidebar.on_colonist_locate = lambda x, y, z: grid.center_camera_on(x, y)
        ui_layout.left_sidebar.on_colonist_click = lambda c: _mgmt_panel.open_for_colonist(colonists, c)
        
        # Wire up colonist panel prev/next to center camera
        _mgmt_panel.on_colonist_changed = lambda c: grid.center_camera_on(c.x, c.y) if hasattr(c, 'x') else None
        
        ui_layout.update(pygame.mouse.get_pos())
        ui_layout.draw(screen, game_data)
        
        # Draw notifications (adjusted position for new layout - offset for sidebar)
        from notifications import draw_notifications
        draw_notifications(screen, x_offset=LEFT_SIDEBAR_WIDTH + 10, y_offset=TOP_BAR_HEIGHT + 10)
        
        # Old bottom bar removed - now using sidebar UI
        # ui.draw(screen)
        
        # Draw stockpile filter panel (if open)
        from ui import get_stockpile_filter_panel
        filter_panel = get_stockpile_filter_panel()
        filter_panel.draw(screen)
        
        # Draw workstation panel (if open)
        from ui import get_workstation_panel
        ws_panel = get_workstation_panel()
        ws_panel.draw(screen)
        
        # Draw bed assignment panel (if open)
        from ui import get_bed_assignment_panel
        bed_panel = get_bed_assignment_panel()
        bed_panel.draw(screen, colonists)
        
        # Draw fixer trade panel (if open)
        from ui import get_fixer_trade_panel
        trade_panel = get_fixer_trade_panel()
        trade_panel.draw(screen, zones_module)
        
        # Draw visitor panel (if open)
        from ui import get_visitor_panel
        visitor_panel = get_visitor_panel()
        visitor_panel.draw(screen)
        
        # Draw colonist job tags panel (if open)
        from ui import get_colonist_panel
        colonist_panel = get_colonist_panel()
        colonist_panel.draw(screen)
        
        # Draw colonist management panel (always visible in right panel)
        from ui import get_colonist_management_panel
        mgmt_panel = get_colonist_management_panel()
        # Always keep colonists list updated and panel visible
        if not mgmt_panel.visible or not mgmt_panel.colonists:
            mgmt_panel.open(colonists, 0)
        mgmt_panel.update(pygame.mouse.get_pos())  # Update tooltip
        mgmt_panel.draw(screen)
        
        # Draw lists panel (if open)
        from lists_ui import get_lists_panel
        lists_panel = get_lists_panel()
        if lists_panel.visible:
            try:
                lists_panel.update_data(colonists, grid)
                lists_panel.draw(screen)
            except Exception as e:
                print(f"[Lists] Error: {e}")
                lists_panel.visible = False
        
        # Draw debug overlay (toggle with 'I' key)
        draw_debug(screen, grid, colonists, jobs_module, resources_module, zones_module, buildings_module, rooms_module)
        
        # Draw pause indicator (centered in viewport area)
        if paused:
            font_pause = pygame.font.Font(None, 48)
            pause_text = font_pause.render("PAUSED", True, (255, 255, 100))
            # Center in viewport area (accounting for sidebars and bars)
            from ui_layout import RIGHT_PANEL_WIDTH, BOTTOM_BAR_HEIGHT
            viewport_center_x = LEFT_SIDEBAR_WIDTH + (SCREEN_W - LEFT_SIDEBAR_WIDTH - RIGHT_PANEL_WIDTH) // 2
            pause_x = viewport_center_x
            pause_y = TOP_BAR_HEIGHT + 40
            pause_rect = pause_text.get_rect(center=(pause_x, pause_y))
            # Draw background for visibility
            bg_rect = pause_rect.inflate(20, 10)
            pygame.draw.rect(screen, (40, 40, 40), bg_rect)
            pygame.draw.rect(screen, (255, 255, 100), bg_rect, 2)
            screen.blit(pause_text, pause_rect)
        
        # Check for colony lost (all colonists dead)
        alive_colonists = [c for c in colonists if not c.is_dead]
        if len(alive_colonists) == 0:
            # Draw "Colony Lost" overlay
            overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))
            
            font_large = pygame.font.Font(None, 72)
            font_small = pygame.font.Font(None, 32)
            
            lost_text = font_large.render("COLONY LOST", True, (255, 80, 80))
            lost_rect = lost_text.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2 - 30))
            screen.blit(lost_text, lost_rect)
            
            reason_text = font_small.render("All colonists have perished.", True, (200, 200, 200))
            reason_rect = reason_text.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2 + 20))
            screen.blit(reason_text, reason_rect)
            
            hint_text = font_small.render("Press ESC to quit", True, (150, 150, 150))
            hint_rect = hint_text.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2 + 60))
            screen.blit(hint_text, hint_rect)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()
