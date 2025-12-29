"""Autotiling system for seamless tile connections.

Implements 13-tile simplified blob autotiling for roads, walls, and other connectable tiles.
Uses bitmasking to determine which variant to use based on 8-directional neighbors.
"""

from typing import Tuple, Set, Optional


def get_autotile_variant(grid, x: int, y: int, z: int, tile_type: str, connect_to: Optional[Set[str]] = None) -> int:
    """Calculate autotile variant (0-16) based on neighbors.
    
    Extended system supports both OUTER corners (paths) and INNER corners (patches).
    
    Args:
        grid: Grid object with get_tile() method
        x, y, z: Tile coordinates
        tile_type: Current tile type (e.g., "street", "wall", "ground_dirt_overlay_autotile")
        connect_to: Set of tile types that count as connections. If None, only connects to same type.
    
    Returns:
        Variant index (0-16):
            0: Isolated (no connections)
            1: Straight horizontal ─
            2: Straight vertical │
            
            3-6: OUTER corners (for paths/roads/walls):
            3: Outer corner NW (connects S+E, path extends to NW)
            4: Outer corner NE (connects S+W, path extends to NE)
            5: Outer corner SW (connects N+E, path extends to SW)
            6: Outer corner SE (connects N+W, path extends to SE)
            
            7: T-junction N (connects S+E+W) ┬
            8: T-junction S (connects N+E+W) ┴
            9: T-junction E (connects N+S+W) ├
            10: T-junction W (connects N+S+E) ┤
            11: 4-way cross (all directions) ┼
            12: End cap (single connection) - currently unused
            
            13-16: INNER corners (for patches/blobs):
            13: Inner corner NW (dirt at S+E, concrete cuts from NW)
            14: Inner corner NE (dirt at S+W, concrete cuts from NE)
            15: Inner corner SW (dirt at N+E, concrete cuts from SW)
            16: Inner corner SE (dirt at N+W, concrete cuts from SE)
    """
    # Determine which tile types count as connections
    if connect_to is None:
        connect_to = {tile_type}
    
    # Determine if this is a patch (blob) or path (line)
    is_patch = "overlay_autotile" in tile_type
    
    # Check 4 cardinal directions
    n = _is_connected(grid, x, y - 1, z, connect_to)  # North
    s = _is_connected(grid, x, y + 1, z, connect_to)  # South
    e = _is_connected(grid, x + 1, y, z, connect_to)  # East
    w = _is_connected(grid, x - 1, y, z, connect_to)  # West
    
    # For patches, also check diagonals (needed for inner corners)
    if is_patch:
        ne = _is_connected(grid, x + 1, y - 1, z, connect_to)  # Northeast
        nw = _is_connected(grid, x - 1, y - 1, z, connect_to)  # Northwest
        se = _is_connected(grid, x + 1, y + 1, z, connect_to)  # Southeast
        sw = _is_connected(grid, x - 1, y + 1, z, connect_to)  # Southwest
    
    # Count connections
    connections = sum([n, s, e, w])
    
    # No connections - isolated tile
    if connections == 0:
        return 0
    
    # Single connection - use appropriate straight tile instead of end cap
    # This avoids needing 4 directional end cap variants
    if connections == 1:
        if n or s:
            return 2  # Vertical straight
        if e or w:
            return 1  # Horizontal straight
    
    # Two connections - straight or corner
    if connections == 2:
        if n and s:
            return 2  # Vertical straight │
        if e and w:
            return 1  # Horizontal straight ─
        
        # CORNER LOGIC - Different for patches vs paths
        if is_patch:
            # PATCHES: Proper blob autotiling with 8-directional checking
            # The key: check if the corner is FILLED (outer corner) or EMPTY (inner corner)
            
            # For a 2-connection corner, check the diagonal between them
            if s and e:
                # South + East connection
                if se:
                    # Diagonal is FILLED = this is part of a blob, use outer corner
                    return 3  # Outer corner NW (blob extends to SE, curves at NW)
                else:
                    # Diagonal is EMPTY = concave cut, use inner corner
                    return 13  # Inner corner NW (concrete cuts from NW)
            
            elif s and w:
                # South + West connection
                if sw:
                    return 4  # Outer corner NE (blob extends to SW, curves at NE)
                else:
                    return 14  # Inner corner NE (concrete cuts from NE)
            
            elif n and e:
                # North + East connection
                if ne:
                    return 5  # Outer corner SW (blob extends to NE, curves at SW)
                else:
                    return 15  # Inner corner SW (concrete cuts from SW)
            
            elif n and w:
                # North + West connection
                if nw:
                    return 6  # Outer corner SE (blob extends to NW, curves at SE)
                else:
                    return 16  # Inner corner SE (concrete cuts from SE)
        else:
            # PATHS: Outer corners (variants 3-6) - path curves outward
            if s and e:
                return 6  # Outer corner SE └ (connects from south, exits east)
            if s and w:
                return 5  # Outer corner SW ┘ (connects from south, exits west)
            if n and e:
                return 4  # Outer corner NE ┌ (connects from north, exits east)
            if n and w:
                return 3  # Outer corner NW ┐ (connects from north, exits west)
    
    # Three connections - T-junction
    if connections == 3:
        if not s:
            return 7  # T-junction N ┬ (opening to north, connects S+E+W)
        if not n:
            return 8  # T-junction S ┴ (opening to south, connects N+E+W)
        if not w:
            return 9  # T-junction E ├ (opening to east, connects N+S+W)
        if not e:
            return 10  # T-junction W ┤ (opening to west, connects N+S+E)
    
    # Four connections - cross
    if connections == 4:
        return 11  # 4-way cross ┼
    
    # Fallback (shouldn't reach here)
    return 0


def _is_connected(grid, x: int, y: int, z: int, connect_to: Set[str]) -> bool:
    """Check if a neighboring tile should connect.
    
    Args:
        grid: Grid object
        x, y, z: Neighbor coordinates
        connect_to: Set of tile types that count as connections
    
    Returns:
        True if neighbor exists and is in connect_to set
    """
    if not grid.in_bounds(x, y, z):
        return False
    
    neighbor_tile = grid.get_tile(x, y, z)
    return neighbor_tile in connect_to


# Tile type connection rules
# Defines which tile types connect to each other for autotiling
AUTOTILE_GROUPS = {
    # Roads connect to other roads
    "street": {"street", "street_cracked", "street_scar", "street_ripped"},
    "street_cracked": {"street", "street_cracked", "street_scar", "street_ripped"},
    "street_scar": {"street", "street_cracked", "street_scar", "street_ripped"},
    "street_ripped": {"street", "street_cracked", "street_scar", "street_ripped"},
    
    # Walls connect to walls and doors
    "wall": {"wall", "finished_wall", "door", "finished_door"},
    "finished_wall": {"wall", "finished_wall", "door", "finished_door"},
    
    # Floors connect to floors
    "floor": {"floor", "finished_floor"},
    "finished_floor": {"floor", "finished_floor"},
    
    # Bridges connect to bridges
    "bridge": {"bridge", "finished_bridge"},
    "finished_bridge": {"bridge", "finished_bridge"},
    
    # Ground overlays connect to same material type
    "ground_dirt_overlay_autotile": {"ground_dirt_overlay_autotile"},
    "ground_rubble_overlay_autotile": {"ground_rubble_overlay_autotile"},
    "ground_overgrown_overlay_autotile": {"ground_overgrown_overlay_autotile"},
}


def get_connection_set(tile_type: str) -> Set[str]:
    """Get the set of tile types that a given tile should connect to.
    
    Args:
        tile_type: The tile type to look up
    
    Returns:
        Set of tile types to connect to. Defaults to {tile_type} if not in AUTOTILE_GROUPS.
    """
    return AUTOTILE_GROUPS.get(tile_type, {tile_type})


def should_autotile(tile_type: str) -> bool:
    """Check if a tile type should use autotiling.
    
    Args:
        tile_type: The tile type to check
    
    Returns:
        True if tile should use autotiling system
    """
    # Autotile roads, walls, bridges, floors, and ground overlays
    autotile_keywords = ["street", "road", "wall", "bridge", "floor", "path", "overlay_autotile"]
    return any(keyword in tile_type for keyword in autotile_keywords)
