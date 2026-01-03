"""Tile Info Panel - Bottom-right panel showing detailed info about hovered tile.

Displays:
- Tile coordinates and type
- Indoor/outdoor status
- Items on tile
- Colonists on tile
- Animals on tile
- Buildings/furniture
- Resources
"""

import arcade
from typing import Optional, List, Tuple
from config import SCREEN_W, SCREEN_H, TILE_SIZE
from ui_arcade import (
    BOTTOM_BAR_HEIGHT,
    PADDING,
    COLOR_BG_PANEL,
    COLOR_BG_ELEVATED,
    COLOR_TEXT_BRIGHT,
    COLOR_TEXT_NORMAL,
    COLOR_TEXT_DIM,
    COLOR_NEON_CYAN,
    COLOR_BORDER_BRIGHT,
    UI_FONT,
    UI_FONT_MONO,
)


class TileInfoPanel:
    """Bottom-right panel showing detailed tile information on mouse hover."""
    
    def __init__(self, screen_width=SCREEN_W, screen_height=SCREEN_H):
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        # Panel dimensions
        self.width = 320
        self.height = 200
        self.x = screen_width - self.width - 10
        self.y = BOTTOM_BAR_HEIGHT + 10
        
        # Current hover tile
        self.hover_x: Optional[int] = None
        self.hover_y: Optional[int] = None
        self.hover_z: int = 0
    
    def on_resize(self, width: int, height: int):
        """Update dimensions on window resize."""
        self.screen_width = width
        self.screen_height = height
        self.x = width - self.width - 10
    
    def set_hover_tile(self, tile_x: Optional[int], tile_y: Optional[int], z: int):
        """Update the hovered tile coordinates."""
        self.hover_x = tile_x
        self.hover_y = tile_y
        self.hover_z = z
    
    def draw(self, grid, colonists: List, camera_x: int, camera_y: int, camera_z: int):
        """Draw the tile info panel.
        
        Args:
            grid: Game grid
            colonists: List of all colonists
            camera_x: Camera X position
            camera_y: Camera Y position
            camera_z: Current Z-level
        """
        if self.hover_x is None or self.hover_y is None:
            return
        
        # Panel background
        arcade.draw_lrbt_rectangle_filled(
            left=self.x,
            right=self.x + self.width,
            bottom=self.y,
            top=self.y + self.height,
            color=COLOR_BG_PANEL
        )
        
        # Border with cyan glow
        arcade.draw_lrbt_rectangle_outline(
            left=self.x,
            right=self.x + self.width,
            bottom=self.y,
            top=self.y + self.height,
            color=COLOR_NEON_CYAN,
            border_width=2
        )
        
        # Subtle glow
        for i in range(4):
            alpha = 15 - i * 3
            arcade.draw_lrbt_rectangle_outline(
                left=self.x - i,
                right=self.x + self.width + i,
                bottom=self.y - i,
                top=self.y + self.height + i,
                color=(*COLOR_NEON_CYAN, alpha),
                border_width=1
            )
        
        # Header
        arcade.draw_text(
            "TILE INFO",
            self.x + 10,
            self.y + self.height - 20,
            COLOR_NEON_CYAN,
            font_size=11,
            bold=True,
            font_name=UI_FONT
        )
        
        # Content area
        content_y = self.y + self.height - 45
        line_height = 14
        
        # Coordinates
        coord_text = f"({self.hover_x}, {self.hover_y}, Z={self.hover_z})"
        arcade.draw_text(
            coord_text,
            self.x + 10,
            content_y,
            COLOR_TEXT_NORMAL,
            font_size=10,
            font_name=UI_FONT_MONO
        )
        content_y -= line_height
        
        # Tile type
        tile_type = grid.get_tile(self.hover_x, self.hover_y, self.hover_z)
        if tile_type:
            tile_display = tile_type.replace("_", " ").title()
            arcade.draw_text(
                f"Type: {tile_display}",
                self.x + 10,
                content_y,
                COLOR_TEXT_NORMAL,
                font_size=9,
                font_name=UI_FONT
            )
            content_y -= line_height
        
        # Indoor/Outdoor status
        from rooms import get_room_at
        room = get_room_at(self.hover_x, self.hover_y, self.hover_z)
        if room:
            arcade.draw_text(
                "Status: Indoor (Room)",
                self.x + 10,
                content_y,
                COLOR_TEXT_NORMAL,
                font_size=9,
                font_name=UI_FONT
            )
        else:
            arcade.draw_text(
                "Status: Outdoor",
                self.x + 10,
                content_y,
                COLOR_TEXT_DIM,
                font_size=9,
                font_name=UI_FONT
            )
        content_y -= line_height
        
        # Separator
        content_y -= 5
        arcade.draw_line(
            self.x + 10,
            content_y,
            self.x + self.width - 10,
            content_y,
            COLOR_BORDER_BRIGHT,
            1
        )
        content_y -= 10
        
        # Items on tile (including corpses, equipment, and stockpile items)
        from resources import _RESOURCE_ITEMS
        from items import get_world_items_at
        import zones as zones_module
        
        items_here = []
        coord_key = (self.hover_x, self.hover_y, self.hover_z)
        
        # Check resource items (wood, scrap, etc. - dropped on ground)
        if coord_key in _RESOURCE_ITEMS:
            items_here.append(_RESOURCE_ITEMS[coord_key])
        
        # Check world items (corpses, equipment, etc.)
        world_items = get_world_items_at(self.hover_x, self.hover_y, self.hover_z)
        items_here.extend(world_items)
        
        # Check stockpile storage (raw resources like wood, scrap)
        stockpile_item = zones_module.get_tile_storage(self.hover_x, self.hover_y, self.hover_z)
        if stockpile_item:
            items_here.append(stockpile_item)
        
        # Check equipment storage (corpses, equipment, crafted items)
        equipment_items = zones_module.get_equipment_at_tile(self.hover_x, self.hover_y, self.hover_z)
        if equipment_items:
            items_here.extend(equipment_items)
        
        if items_here:
            arcade.draw_text(
                f"Items: ({len(items_here)})",
                self.x + 10,
                content_y,
                COLOR_TEXT_BRIGHT,
                font_size=9,
                bold=True,
                font_name=UI_FONT
            )
            content_y -= line_height
            
            for item in items_here[:3]:  # Show max 3 items
                # Handle both resource items and world items
                if "type" in item:
                    # Resource item (wood, scrap, etc.)
                    item_name = item.get("type", "unknown")
                    amount = item.get("amount", 1)
                    if amount > 1:
                        item_display = f"  • {item_name} x{amount}"
                    else:
                        item_display = f"  • {item_name}"
                else:
                    # World item (corpse, equipment, etc.) - show metadata if available
                    from items import get_item_display_name
                    # Get current game tick for age calculation
                    game_tick = getattr(self, 'game_tick', 0)
                    item_display_name = get_item_display_name(item, game_tick)
                    item_display = f"  • {item_display_name}"
                
                arcade.draw_text(
                    item_display,
                    self.x + 15,
                    content_y,
                    COLOR_TEXT_NORMAL,
                    font_size=8,
                    font_name=UI_FONT
                )
                content_y -= line_height
            
            if len(items_here) > 3:
                arcade.draw_text(
                    f"  ... and {len(items_here) - 3} more",
                    self.x + 15,
                    content_y,
                    COLOR_TEXT_DIM,
                    font_size=8,
                    font_name=UI_FONT
                )
                content_y -= line_height
        
        # Colonists on tile
        colonists_here = [c for c in colonists 
                         if c.x == self.hover_x 
                         and c.y == self.hover_y 
                         and c.z == self.hover_z
                         and not c.is_dead]
        
        if colonists_here:
            arcade.draw_text(
                f"Colonists: ({len(colonists_here)})",
                self.x + 10,
                content_y,
                COLOR_TEXT_BRIGHT,
                font_size=9,
                bold=True,
                font_name=UI_FONT
            )
            content_y -= line_height
            
            for colonist in colonists_here[:2]:  # Show max 2
                arcade.draw_text(
                    f"  • {colonist.name}",
                    self.x + 15,
                    content_y,
                    COLOR_TEXT_NORMAL,
                    font_size=8,
                    font_name=UI_FONT
                )
                content_y -= line_height
        
        # Animals on tile
        from animals import get_all_animals
        animals_here = [a for a in get_all_animals() 
                       if a.x == self.hover_x 
                       and a.y == self.hover_y 
                       and a.z == self.hover_z
                       and a.is_alive()]
        
        if animals_here:
            arcade.draw_text(
                f"Animals: ({len(animals_here)})",
                self.x + 10,
                content_y,
                COLOR_TEXT_BRIGHT,
                font_size=9,
                bold=True,
                font_name=UI_FONT
            )
            content_y -= line_height
            
            for animal in animals_here[:2]:  # Show max 2
                species_name = animal.species_data.get("name", animal.species)
                arcade.draw_text(
                    f"  • {species_name}",
                    self.x + 15,
                    content_y,
                    COLOR_TEXT_NORMAL,
                    font_size=8,
                    font_name=UI_FONT
                )
                content_y -= line_height
        
        # Check for workstations/furniture via grid tile type
        # These show up as special tile types in the grid
        if tile_type and tile_type not in ("floor", "dirt", "street", "void", "resource_node"):
            # It's some kind of structure
            structure_name = tile_type.replace("_", " ").title()
            arcade.draw_text(
                f"Structure: {structure_name}",
                self.x + 10,
                content_y,
                COLOR_TEXT_NORMAL,
                font_size=9,
                font_name=UI_FONT
            )
            content_y -= line_height


# Singleton instance
_tile_info_panel: Optional[TileInfoPanel] = None


def get_tile_info_panel() -> TileInfoPanel:
    """Get or create the tile info panel singleton."""
    global _tile_info_panel
    if _tile_info_panel is None:
        _tile_info_panel = TileInfoPanel()
    return _tile_info_panel
