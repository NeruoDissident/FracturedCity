"""Debug overlay for visualizing game state.

Toggle with 'I' key. Shows:
- Resource node amounts
- Stockpile tile contents
- Construction site material requirements
- Job queue status
- Colonist states
"""

import pygame
from typing import Optional, Dict, Tuple

from config import TILE_SIZE, GRID_W, GRID_H

# Colors for debug overlay
COLOR_DEBUG_BG = (20, 20, 30, 200)  # Semi-transparent dark
COLOR_DEBUG_TEXT = (220, 220, 220)
COLOR_DEBUG_HEADER = (100, 200, 255)
COLOR_DEBUG_GOOD = (100, 255, 100)
COLOR_DEBUG_BAD = (255, 100, 100)
COLOR_DEBUG_NEUTRAL = (255, 220, 100)

# Tile overlay colors (semi-transparent)
COLOR_OVERLAY_NODE = (50, 200, 50, 150)
COLOR_OVERLAY_STOCKPILE = (50, 50, 200, 150)
COLOR_OVERLAY_CONSTRUCTION = (200, 150, 50, 150)
COLOR_OVERLAY_ROOM = (150, 100, 200, 180)  # Default room outline color

# Per-room-type neon outline colors for detail/debug view
ROOM_TYPE_OVERLAY_COLORS = {
    "Kitchen": (0, 255, 180, 230),       # Aqua green
    "Salvage Bay": (255, 220, 80, 230),  # Gold
    "Forge Den": (255, 90, 90, 230),     # Hot red
    "Skin Shop": (255, 0, 255, 230),     # Magenta
    "Cortex Cell": (0, 200, 255, 230),   # Cyan
    "Crash Pad": (180, 120, 255, 230),   # Violet-blue shared dorm glow
    "Coffin Nook": (255, 120, 200, 230), # Pink coffin-hotel vibe
}


class DebugOverlay:
    """Manages debug visualization overlay."""
    
    def __init__(self):
        self.enabled = False
        self.font_small: Optional[pygame.font.Font] = None
        self.font_medium: Optional[pygame.font.Font] = None
        self.font_large: Optional[pygame.font.Font] = None
        self._initialized = False
    
    def _init_fonts(self):
        """Initialize fonts (must be called after pygame.init)."""
        if self._initialized:
            return
        pygame.font.init()
        self.font_small = pygame.font.SysFont("Consolas", 12)
        self.font_medium = pygame.font.SysFont("Consolas", 14)
        self.font_large = pygame.font.SysFont("Consolas", 16, bold=True)
        self._initialized = True
    
    def toggle(self):
        """Toggle debug overlay on/off."""
        self.enabled = not self.enabled
        print(f"[DEBUG] Overlay {'enabled' if self.enabled else 'disabled'}")
    
    def draw(self, screen: pygame.Surface, grid, colonists, jobs_module, resources_module, zones_module, buildings_module, rooms_module=None):
        """Draw the complete debug overlay."""
        if not self.enabled:
            return
        
        self._init_fonts()
        
        # Draw tile overlays first (under everything) - pass camera offset
        self._draw_tile_overlays(screen, grid, resources_module, zones_module, buildings_module, rooms_module)
        
        # Draw info panels (reduced - colonist/jobs/rooms now in sidebar)
        self._draw_resource_panel(screen, resources_module, zones_module)
        self._draw_construction_panel(screen, buildings_module)
        # Removed: _draw_jobs_panel, _draw_colonist_panel, _draw_rooms_panel (now in sidebar)
        
        # Draw tile hover tooltip with environmental data
        self._draw_tile_hover_tooltip(screen, grid)
    
    def _draw_tile_overlays(self, screen, grid, resources_module, zones_module, buildings_module, rooms_module=None):
        """Draw numbers on tiles showing their contents."""
        camera_x = grid.camera_x
        camera_y = grid.camera_y
        
        # Draw room overlays first (under other info)
        if rooms_module:
            current_z = grid.current_z
            for room_id, room_data in rooms_module.get_all_rooms().items():
                room_z = room_data.get("z", 0)
                if room_z != current_z:
                    continue  # Only show rooms on current Z-level

                room_type = room_data.get("room_type")
                color = ROOM_TYPE_OVERLAY_COLORS.get(room_type, COLOR_OVERLAY_ROOM)

                # Outline-only overlay per tile for this room, using neon room-type color
                overlay_surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
                pygame.draw.rect(overlay_surf, color, overlay_surf.get_rect(), 2)

                tiles = room_data.get("tiles", [])
                for (x, y) in tiles:
                    screen_x = x * TILE_SIZE - camera_x
                    screen_y = y * TILE_SIZE - camera_y
                    rect = pygame.Rect(screen_x, screen_y, TILE_SIZE, TILE_SIZE)
                    screen.blit(overlay_surf, rect)
        
        # Get dropped items for reference
        dropped_items = resources_module.get_all_resource_items()
        
        # Resource nodes - show remaining amount (or dropped count if depleted)
        # Nodes are always on z=0
        current_z = grid.current_z
        for (x, y), node in resources_module.get_all_nodes().items():
            if current_z != 0:
                continue  # Only show nodes on ground level view
            amount = node.get("amount", 0)
            node_type = node.get("type", "")
            is_replenishable = resources_module.is_node_replenishable(node_type)
            
            if amount > 0:
                # Node has resources - green for replenishable, cyan for non-replenishable
                color = COLOR_DEBUG_GOOD if is_replenishable else (100, 200, 200)
                self._draw_tile_number(screen, x, y, f"{amount}", color, camera_x=camera_x, camera_y=camera_y)
            elif (x, y, 0) in dropped_items:
                # Depleted but has dropped item - show dropped amount
                item = dropped_items[(x, y, 0)]
                dropped_amt = item.get("amount", 1)
                self._draw_tile_number(screen, x, y, f"{dropped_amt}", COLOR_DEBUG_NEUTRAL, camera_x=camera_x, camera_y=camera_y)
            else:
                # Depleted and no dropped item - show 0 in red (will respawn) or nothing (removed)
                if is_replenishable:
                    self._draw_tile_number(screen, x, y, "0", COLOR_DEBUG_BAD, camera_x=camera_x, camera_y=camera_y)
        
        # Dropped resource items - show type indicator below the number (on current Z level)
        for (x, y, z), item in dropped_items.items():
            if z != current_z:
                continue  # Only show items on current Z level
            res_type = item.get("type", "?")
            short_type = res_type[0].upper() if res_type else "?"
            haul_req = item.get("haul_requested", False)
            # Yellow if waiting to haul, cyan if being hauled
            color = COLOR_DEBUG_NEUTRAL if haul_req else (100, 200, 200)
            self._draw_tile_number(screen, x, y, f"[{short_type}]", color, offset_y=8, camera_x=camera_x, camera_y=camera_y)
        
        # Stockpile zone tiles - show blue overlay for ALL stockpile tiles (on current Z level)
        stockpile_overlay = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        stockpile_overlay.fill(COLOR_OVERLAY_STOCKPILE)
        
        for (x, y, z) in zones_module.get_all_stockpile_tiles():
            if z != current_z:
                continue
            screen_x = x * TILE_SIZE - camera_x
            screen_y = y * TILE_SIZE - camera_y
            rect = pygame.Rect(screen_x, screen_y, TILE_SIZE, TILE_SIZE)
            screen.blit(stockpile_overlay, rect)
            # Draw border to make it more visible
            pygame.draw.rect(screen, (80, 80, 255), rect, 1)
        
        # Stockpile tiles with contents - show stored amount (on current Z level)
        for (x, y, z), storage in zones_module.get_all_tile_storage().items():
            if z != current_z:
                continue  # Only show storage on current Z level
            res_type = storage.get("type", "?")
            amount = storage.get("amount", 0)
            short_type = res_type[0].upper() if res_type else "?"
            self._draw_tile_number(screen, x, y, f"{short_type}:{amount}", COLOR_DEBUG_NEUTRAL, offset_y=-8, camera_x=camera_x, camera_y=camera_y)
        
        # Construction sites - show delivered/needed
        for (x, y, z), site in buildings_module.get_all_construction_sites().items():
            needed = site.get("materials_needed", {})
            delivered = site.get("materials_delivered", {})
            
            # Build compact string like "W:1/1 M:0/1"
            parts = []
            for res_type in needed.keys():
                short = res_type[0].upper()
                d = delivered.get(res_type, 0)
                n = needed.get(res_type, 0)
                color = COLOR_DEBUG_GOOD if d >= n else COLOR_DEBUG_BAD
                parts.append((f"{short}:{d}/{n}", color))
            
            # Draw each part
            offset_y = -10
            for text, color in parts:
                self._draw_tile_number(screen, x, y, text, color, offset_y=offset_y, camera_x=camera_x, camera_y=camera_y)
                offset_y += 10
    
    def _draw_tile_number(self, screen, tile_x: int, tile_y: int, text: str, color, offset_y: int = 0, camera_x: int = 0, camera_y: int = 0):
        """Draw a small number on a tile.
        
        Args:
            screen: Pygame surface to draw on
            tile_x, tile_y: Tile coordinates in world space
            text: Text to display
            color: Text color
            offset_y: Vertical offset from tile center
            camera_x, camera_y: Camera offset for viewport rendering
        """
        # World position in pixels
        world_px = tile_x * TILE_SIZE + TILE_SIZE // 2
        world_py = tile_y * TILE_SIZE + TILE_SIZE // 2 + offset_y
        
        # Screen position (apply camera offset)
        px = world_px - camera_x
        py = world_py - camera_y
        
        text_surf = self.font_small.render(text, True, color)
        text_rect = text_surf.get_rect(center=(px, py))
        
        # Draw background for readability
        bg_rect = text_rect.inflate(4, 2)
        bg_surf = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
        bg_surf.fill((0, 0, 0, 180))
        screen.blit(bg_surf, bg_rect)
        screen.blit(text_surf, text_rect)
    
    def _draw_panel(self, screen, x: int, y: int, width: int, height: int, title: str) -> int:
        """Draw a panel background and title. Returns y position for content."""
        # Semi-transparent background
        panel_surf = pygame.Surface((width, height), pygame.SRCALPHA)
        panel_surf.fill(COLOR_DEBUG_BG)
        screen.blit(panel_surf, (x, y))
        
        # Border
        pygame.draw.rect(screen, COLOR_DEBUG_HEADER, (x, y, width, height), 1)
        
        # Title bar
        pygame.draw.rect(screen, (*COLOR_DEBUG_HEADER[:3], 100), (x, y, width, 20))
        title_surf = self.font_medium.render(title, True, COLOR_DEBUG_TEXT)
        screen.blit(title_surf, (x + 5, y + 2))
        
        return y + 24
    
    def _draw_resource_panel(self, screen, resources_module, zones_module):
        """Draw panel showing global resource counts."""
        x, y = 10, 10
        width, height = 180, 160
        
        content_y = self._draw_panel(screen, x, y, width, height, "📦 Resources")
        
        stockpile = resources_module.get_stockpile()
        
        # Header row
        header = "Type     Inv  Stored"
        header_surf = self.font_small.render(header, True, COLOR_DEBUG_HEADER)
        screen.blit(header_surf, (x + 8, content_y))
        content_y += 14
        
        for i, (res_type, amount) in enumerate(stockpile.items()):
            stored = zones_module.get_total_stored(res_type)
            
            # Color: green if inventory matches stored, yellow if mismatch
            if amount == stored:
                color = COLOR_DEBUG_GOOD
            else:
                color = COLOR_DEBUG_NEUTRAL
            
            # Format: "Wood      5     3"
            name = res_type.capitalize()[:8].ljust(8)
            inv_str = str(amount).rjust(3)
            stored_str = str(stored).rjust(5)
            text = f"{name} {inv_str}  {stored_str}"
            text_surf = self.font_small.render(text, True, color)
            screen.blit(text_surf, (x + 8, content_y + i * 14))
        
        # Show dropped items waiting for stockpile
        dropped_items = resources_module.get_all_resource_items()
        row = len(stockpile)
        waiting = len([i for i in dropped_items.values() if i.get("haul_requested")])
        being_hauled = len(dropped_items) - waiting
        
        content_y += row * 14 + 6
        
        # Dropped items line
        text = f"On ground: {len(dropped_items)}"
        color = COLOR_DEBUG_NEUTRAL if len(dropped_items) > 0 else COLOR_DEBUG_TEXT
        text_surf = self.font_small.render(text, True, color)
        screen.blit(text_surf, (x + 8, content_y))
        
        if len(dropped_items) > 0:
            # Detail: waiting vs being hauled
            detail = f"  ({waiting} wait, {being_hauled} haul)"
            detail_surf = self.font_small.render(detail, True, COLOR_DEBUG_TEXT)
            screen.blit(detail_surf, (x + 8, content_y + 12))
    
    def _draw_jobs_panel(self, screen, jobs_module):
        """Draw panel showing job queue status."""
        x, y = 10, 180
        width, height = 180, 100
        
        content_y = self._draw_panel(screen, x, y, width, height, "📋 Jobs")
        
        # Count jobs by type
        job_counts: Dict[str, Tuple[int, int]] = {}  # type -> (total, assigned)
        for job in jobs_module.JOB_QUEUE:
            jtype = job.type
            total, assigned = job_counts.get(jtype, (0, 0))
            job_counts[jtype] = (total + 1, assigned + (1 if job.assigned else 0))
        
        if not job_counts:
            text_surf = self.font_small.render("No jobs", True, COLOR_DEBUG_NEUTRAL)
            screen.blit(text_surf, (x + 8, content_y))
        else:
            for i, (jtype, (total, assigned)) in enumerate(job_counts.items()):
                pending = total - assigned
                color = COLOR_DEBUG_GOOD if pending == 0 else COLOR_DEBUG_NEUTRAL
                text = f"{jtype}: {assigned}/{total}"
                text_surf = self.font_small.render(text, True, color)
                screen.blit(text_surf, (x + 8, content_y + i * 14))
    
    def _draw_construction_panel(self, screen, buildings_module):
        """Draw panel showing construction site status."""
        x, y = 10, 290
        width, height = 180, 120
        
        sites = buildings_module.get_all_construction_sites()
        if not sites:
            return
        
        content_y = self._draw_panel(screen, x, y, width, height, "🔨 Construction")
        
        # Show summary
        ready = 0
        waiting = 0
        for (sx, sy, sz), site in sites.items():
            if buildings_module.has_required_materials(sx, sy, sz):
                ready += 1
            else:
                waiting += 1
        
        text = f"Ready: {ready}  Waiting: {waiting}"
        color = COLOR_DEBUG_GOOD if waiting == 0 else COLOR_DEBUG_NEUTRAL
        text_surf = self.font_small.render(text, True, color)
        screen.blit(text_surf, (x + 8, content_y))
        
        # Show pending supply jobs
        pending = len(buildings_module._PENDING_SUPPLY_JOBS)
        text = f"Pending supplies: {pending}"
        color = COLOR_DEBUG_NEUTRAL if pending > 0 else COLOR_DEBUG_TEXT
        text_surf = self.font_small.render(text, True, color)
        screen.blit(text_surf, (x + 8, content_y + 16))
        
        # List first few sites
        content_y += 36
        for i, ((sx, sy, sz), site) in enumerate(list(sites.items())[:3]):
            needed = site.get("materials_needed", {})
            delivered = site.get("materials_delivered", {})
            
            parts = []
            all_done = True
            for res_type in needed.keys():
                d = delivered.get(res_type, 0)
                n = needed.get(res_type, 0)
                if d < n:
                    all_done = False
                parts.append(f"{res_type[0].upper()}:{d}/{n}")
            
            status = " ".join(parts)
            color = COLOR_DEBUG_GOOD if all_done else COLOR_DEBUG_BAD
            z_str = f"z{sz}" if sz > 0 else ""
            text = f"({sx},{sy}{z_str}): {status}"
            text_surf = self.font_small.render(text, True, color)
            screen.blit(text_surf, (x + 8, content_y + i * 14))
    
    def _draw_colonist_panel(self, screen, colonists):
        """Draw panel showing colonist states, mood, and hunger."""
        screen_w = screen.get_width()
        x, y = screen_w - 220, 10
        width = 210
        
        # Calculate height based on colonist count (more space per colonist)
        height = 50 + len(colonists) * 38
        
        content_y = self._draw_panel(screen, x, y, width, height, "Colonists")
        
        # Show each colonist
        for i, c in enumerate(colonists):
            row_y = content_y + i * 38
            
            # Get colonist name (fallback to index if no name)
            name = getattr(c, 'name', f'Colonist {i+1}')
            # Truncate long names
            if len(name) > 18:
                name = name[:16] + ".."
            
            if c.is_dead:
                # Dead colonist - show in red, strikethrough effect
                text_surf = self.font_small.render(f"{name}: DEAD", True, COLOR_DEBUG_BAD)
                screen.blit(text_surf, (x + 8, row_y))
            else:
                # Row 1: Name and mood
                from colonist import Colonist
                mood = getattr(c, 'mood_state', 'Focused')
                mood_color = Colonist.get_mood_color(mood)
                
                name_surf = self.font_small.render(name, True, (220, 210, 180))
                screen.blit(name_surf, (x + 8, row_y))
                
                # Mood indicator (right-aligned)
                mood_surf = self.font_small.render(mood, True, mood_color)
                mood_x = x + width - 8 - mood_surf.get_width()
                screen.blit(mood_surf, (mood_x, row_y))
                
                # Row 2: State and stats
                row2_y = row_y + 13
                state_short = c.state[:10] if len(c.state) > 10 else c.state
                state_surf = self.font_small.render(state_short, True, (140, 140, 150))
                screen.blit(state_surf, (x + 8, row2_y))
                
                # Hunger bar (compact)
                bar_x = x + 80
                bar_y = row2_y + 2
                bar_width = 50
                bar_height = 5
                
                pygame.draw.rect(screen, (40, 40, 40), (bar_x, bar_y, bar_width, bar_height))
                
                hunger_ratio = c.hunger / 100.0
                if hunger_ratio < 0.5:
                    bar_color = COLOR_DEBUG_GOOD
                elif hunger_ratio < 0.7:
                    bar_color = COLOR_DEBUG_NEUTRAL
                else:
                    bar_color = COLOR_DEBUG_BAD
                
                fill_width = int(bar_width * hunger_ratio)
                if fill_width > 0:
                    pygame.draw.rect(screen, bar_color, (bar_x, bar_y, fill_width, bar_height))
                
                # Hunger value
                hunger_surf = self.font_small.render(f"{c.hunger:.0f}", True, bar_color)
                screen.blit(hunger_surf, (bar_x + bar_width + 4, row2_y))
                
                # Health if damaged (right side)
                if c.health < 100:
                    health_surf = self.font_small.render(f"HP:{c.health:.0f}", True, COLOR_DEBUG_BAD)
                    screen.blit(health_surf, (x + width - 8 - health_surf.get_width(), row2_y))
                
                # Separator line between colonists
                if i < len(colonists) - 1:
                    sep_y = row_y + 34
                    pygame.draw.line(screen, (50, 50, 55), (x + 8, sep_y), (x + width - 8, sep_y), 1)
    
    def _draw_rooms_panel(self, screen, rooms_module, colonist_count: int = 3):
        """Draw panel showing room status."""
        if rooms_module is None:
            return
        
        screen_w = screen.get_width()
        # Position below colonist panel (which varies in height)
        colonist_panel_height = 50 + colonist_count * 38
        # Make panel wider so text doesn't clip
        width = 210
        x, y = screen_w - width - 10, 20 + colonist_panel_height
        height = 110
        
        content_y = self._draw_panel(screen, x, y, width, height, "🏠 Rooms")
        
        rooms = rooms_module.get_all_rooms()
        
        if not rooms:
            text_surf = self.font_small.render("No rooms", True, COLOR_DEBUG_NEUTRAL)
            screen.blit(text_surf, (x + 8, content_y))
        else:
            roof_tiles = rooms_module.get_all_roof_tiles()
            kitchen_count = 0
            for data in rooms.values():
                if data.get("room_type") == "Kitchen":
                    kitchen_count += 1
            if kitchen_count > 0:
                header = f"Rooms: {len(rooms)}   Kitchens: {kitchen_count}   Roofs: {len(roof_tiles)}"
            else:
                header = f"Rooms: {len(rooms)}   Roofs: {len(roof_tiles)}"
            text_surf = self.font_small.render(header, True, COLOR_DEBUG_GOOD)
            screen.blit(text_surf, (x + 8, content_y))
            
            # List a few rooms with very clear type label
            for i, (room_id, room_data) in enumerate(list(rooms.items())[:4]):
                tiles = room_data.get("tiles", [])
                exits = len(room_data.get("entrances", []))
                room_type = room_data.get("room_type")
                if room_type:
                    label = f"R{room_id}: {len(tiles)} tiles, {exits} exits  [ {room_type} ]"
                    if room_type == "Kitchen":
                        color = COLOR_DEBUG_GOOD
                    else:
                        color = (200, 200, 255)
                else:
                    label = f"R{room_id}: {len(tiles)} tiles, {exits} exits"
                    color = (200, 150, 255)
                text_surf = self.font_small.render(label, True, color)
                screen.blit(text_surf, (x + 8, content_y + 14 + i * 14))
    
    def _draw_tile_hover_tooltip(self, screen, grid):
        """Draw tooltip showing environmental data for hovered tile."""
        # Get mouse position
        mx, my = pygame.mouse.get_pos()
        
        # Convert to world coordinates
        world_x = mx + grid.camera_x
        world_y = my + grid.camera_y
        
        # Convert to tile coordinates
        tile_x = world_x // TILE_SIZE
        tile_y = world_y // TILE_SIZE
        tile_z = grid.current_z
        
        # Check if in bounds
        if not grid.in_bounds(tile_x, tile_y, tile_z):
            return
        
        # Get tile data
        tile_type = grid.get_tile(tile_x, tile_y, tile_z)
        env_data = grid.get_env_data(tile_x, tile_y, tile_z)
        
        # Get storage data
        import zones
        from items import get_world_items_at
        tile_storage = zones.get_tile_storage(tile_x, tile_y, tile_z)
        equipment_storage = zones.get_equipment_at_tile(tile_x, tile_y, tile_z)
        world_items = get_world_items_at(tile_x, tile_y, tile_z)
        
        # Create tooltip
        tooltip_lines = [
            f"Tile: ({tile_x}, {tile_y}, {tile_z})",
            f"Type: {tile_type}",
        ]
        
        # Add storage info if present
        if tile_storage:
            res_type = tile_storage.get("type", "?")
            amount = tile_storage.get("amount", 0)
            tooltip_lines.append(f"Storage: {res_type} x{amount}")
        
        if equipment_storage:
            for item in equipment_storage[:3]:  # Show up to 3
                tooltip_lines.append(f"Equipment: {item.get('name', '?')}")
            if len(equipment_storage) > 3:
                tooltip_lines.append(f"  +{len(equipment_storage) - 3} more...")
        
        if world_items:
            for item in world_items[:3]:  # Show up to 3
                tooltip_lines.append(f"Item: {item.get('name', '?')}")
            if len(world_items) > 3:
                tooltip_lines.append(f"  +{len(world_items) - 3} more...")
        
        # Check registered room first, then fall back to env_data
        room_id = None
        room_type_text = None
        room_exits = 0
        room_enclosure = None
        
        try:
            import rooms as rooms_module
            # Check if tile is in a registered room
            room_id = rooms_module._TILE_TO_ROOM.get((gx, gy, current_z))
            if room_id is not None:
                room = rooms_module.get_all_rooms().get(room_id)
                if room is not None:
                    # Get room classification (Kitchen, Salvage Bay, etc.)
                    rt = room.get("room_type")
                    if rt:
                        room_type_text = f"Room Type: {rt}"
                    
                    # Get room enclosure type (COVERED/ENCLOSED)
                    room_type_enum = room.get("room_type_enum")
                    if room_type_enum is not None:
                        room_enclosure = room_type_enum.value  # "covered" or "enclosed"
                    
                    # Get room exits (number of entrances/doors)
                    entrances = room.get("entrances", [])
                    room_exits = len(entrances)
        except Exception:
            pass
        
        # Fall back to env_data room_id if not found in registered rooms
        if room_id is None:
            room_id = env_data.get("room_id")
        
        if room_id is None:
            room_text = "Room: None"
        else:
            room_text = f"Room: R{room_id}"
            if room_enclosure:
                room_text += f" ({room_enclosure})"

        tooltip_lines.extend([
            f"─────────────────",
            f"Interference: {env_data.get('interference', 0.0):.2f}",
            f"Pressure: {env_data.get('pressure', 0.0):.2f}",
            f"Echo: {env_data.get('echo', 0.0):.2f}",
            f"Integrity: {env_data.get('integrity', 1.0):.2f}",
            f"Outside: {env_data.get('is_outside', True)}",
            room_text,
        ])
        if room_type_text is not None:
            tooltip_lines.append(room_type_text)
        tooltip_lines.append(f"Exits (room): {room_exits}")
        
        # Calculate tooltip size
        line_height = 14
        padding = 8
        tooltip_width = 200
        tooltip_height = len(tooltip_lines) * line_height + padding * 2
        
        # Position tooltip near mouse (offset to avoid cursor)
        tooltip_x = mx + 15
        tooltip_y = my + 15
        
        # Keep tooltip on screen
        from config import SCREEN_W, SCREEN_H
        if tooltip_x + tooltip_width > SCREEN_W:
            tooltip_x = mx - tooltip_width - 5
        if tooltip_y + tooltip_height > SCREEN_H:
            tooltip_y = SCREEN_H - tooltip_height - 5
        
        # Draw tooltip background
        tooltip_rect = pygame.Rect(tooltip_x, tooltip_y, tooltip_width, tooltip_height)
        pygame.draw.rect(screen, (30, 30, 40, 240), tooltip_rect)
        pygame.draw.rect(screen, (100, 150, 200), tooltip_rect, 2)
        
        # Draw tooltip text
        y_offset = tooltip_y + padding
        for line in tooltip_lines:
            if line.startswith("─"):
                # Separator line
                y_offset += 7
                pygame.draw.line(screen, (80, 80, 90), 
                               (tooltip_x + padding, y_offset), 
                               (tooltip_x + tooltip_width - padding, y_offset))
                y_offset += 7
            else:
                text_surf = self.font_small.render(line, True, (220, 220, 230))
                screen.blit(text_surf, (tooltip_x + padding, y_offset))
                y_offset += line_height


# Global instance
_debug_overlay = DebugOverlay()


def get_debug_overlay() -> DebugOverlay:
    """Get the global debug overlay instance."""
    return _debug_overlay


def toggle_debug():
    """Toggle debug overlay."""
    _debug_overlay.toggle()


def draw_debug(screen, grid, colonists, jobs_module, resources_module, zones_module, buildings_module, rooms_module=None):
    """Draw debug overlay if enabled."""
    _debug_overlay.draw(screen, grid, colonists, jobs_module, resources_module, zones_module, buildings_module, rooms_module)
