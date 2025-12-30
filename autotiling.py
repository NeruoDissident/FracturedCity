"""Autotiling system for Fractured City.

Handles automatic tile variant selection based on neighboring tiles.
Supports both path-style (roads, walls) and blob-style (dirt, grass) autotiling.
"""

from typing import Optional, Set


def get_autotile_variant(grid, x: int, y: int, z: int, tile_type: str, connect_to: Optional[Set[str]] = None) -> int:
    """Calculate autotile variant (0-16) based on 8-neighbor blob autotiling.
    
    Uses standard blob autotiling algorithm:
    - Checks all 8 neighbors (N, S, E, W, NE, NW, SE, SW)
    - Selects tile variant based on neighbor pattern
    - Supports both blob-style (patches) and path-style (roads) autotiling
    
    Args:
        grid: Grid object with get_tile() method
        x, y, z: Tile coordinates
        tile_type: Current tile type
        connect_to: Set of tile types that count as connections
    
    Returns:
        Variant index (0-16)
    """
    # If no connection set specified, only connect to same tile type
    if connect_to is None:
        connect_to = {tile_type}
    
    # Determine if this is a patch (blob) or path (line)
    is_patch = "overlay_autotile" in tile_type
    
    # Check all 8 neighbors
    n = _is_connected(grid, x, y - 1, z, connect_to)
    s = _is_connected(grid, x, y + 1, z, connect_to)
    e = _is_connected(grid, x + 1, y, z, connect_to)
    w = _is_connected(grid, x - 1, y, z, connect_to)
    ne = _is_connected(grid, x + 1, y - 1, z, connect_to)
    nw = _is_connected(grid, x - 1, y - 1, z, connect_to)
    se = _is_connected(grid, x + 1, y + 1, z, connect_to)
    sw = _is_connected(grid, x - 1, y + 1, z, connect_to)
    
    # For blobs, use proper blob autotiling
    if is_patch:
        return _get_blob_variant(n, s, e, w, ne, nw, se, sw)
    else:
        # For paths, use simpler path autotiling
        return _get_path_variant(n, s, e, w)


def _get_blob_variant(n: bool, s: bool, e: bool, w: bool, ne: bool, nw: bool, se: bool, sw: bool) -> int:
    """Calculate blob autotile variant using bitmask.
    
    Uses standard blob tileset bitmask system (47 tiles from 256 combinations).
    Bitmask values: N=1, NE=2, E=4, SE=8, S=16, SW=32, W=64, NW=128
    
    IMPORTANT: Diagonal neighbors only count if their adjacent cardinals are present.
    """
    # Calculate bitmask from neighbors
    bitmask = 0
    if n:  bitmask += 1
    if ne and n and e: bitmask += 2  # NE only counts if both N and E present
    if e:  bitmask += 4
    if se and s and e: bitmask += 8  # SE only counts if both S and E present
    if s:  bitmask += 16
    if sw and s and w: bitmask += 32  # SW only counts if both S and W present
    if w:  bitmask += 64
    if nw and n and w: bitmask += 128  # NW only counts if both N and W present
    
    # Map bitmask to 47-tile blob tileset variant
    # Corrected mapping from user template:
    # 0 = 0 (isolated, no edges touching)
    # 1,2,3,4 = 1,4,16,64
    # 5,6,7,8 = 5,20,80,65
    # 9,10,11,12 = 7,28,112,193 (variant 10 corrected to bitmask 28)
    # 13,14 = 17,68
    # 15,16,17,18 = 21,84,81,69
    # 19,20,21,22 = 23,92,113,197
    # 23,24,25,26 = 29,116,209,71 (variant 23 is bitmask 29)
    # 27,28,29,30 = 31,124,241,199
    # 31 = 85
    # 32,33,34,35 = 87,93,117,213
    # 36,37,38,39 = 95,125,245,215
    # 40,41 = 119,221
    # 42,43,44,45 = 127,253,247,223
    # 46 = 255 (full, all sides touching)
    BITMASK_TO_VARIANT = {
        0: 0,      # Isolated (no neighbors)
        1: 1,
        4: 2,
        16: 3,
        64: 4,
        5: 5,
        20: 6,
        80: 7,
        65: 8,
        7: 9,
        28: 10,    # Corrected from 29
        112: 11,
        193: 12,
        17: 13,
        68: 14,
        21: 15,
        84: 16,
        81: 17,
        69: 18,
        23: 19,
        92: 20,
        113: 21,
        197: 22,
        29: 23,    # Variant 23
        116: 24,
        209: 25,
        71: 26,
        31: 27,
        124: 28,
        241: 29,
        199: 30,
        85: 31,
        87: 32,
        93: 33,
        117: 34,
        213: 35,
        95: 36,
        125: 37,
        245: 38,
        215: 39,
        119: 40,
        221: 41,
        127: 42,
        253: 43,
        247: 44,
        223: 45,
        255: 46,   # Full tile (all 8 neighbors)
    }
    
    # Debug: Track variant usage
    if not hasattr(_get_blob_variant, '_variant_counts'):
        _get_blob_variant._variant_counts = {}
        _get_blob_variant._bitmask_counts = {}
    
    variant = BITMASK_TO_VARIANT.get(bitmask, 0)
    
    # Count this variant
    _get_blob_variant._variant_counts[variant] = _get_blob_variant._variant_counts.get(variant, 0) + 1
    _get_blob_variant._bitmask_counts[bitmask] = _get_blob_variant._bitmask_counts.get(bitmask, 0) + 1
    
    # Print summary after processing many tiles
    if sum(_get_blob_variant._variant_counts.values()) == 100:
        print("\n[AUTOTILE ANALYSIS] First 100 dirt tiles:")
        print("  Variant usage:")
        for v in sorted(_get_blob_variant._variant_counts.keys()):
            count = _get_blob_variant._variant_counts[v]
            print(f"    Variant {v:2d}: {count:3d} tiles")
        print("  Bitmask usage (top 10):")
        sorted_bitmasks = sorted(_get_blob_variant._bitmask_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        for bitmask, count in sorted_bitmasks:
            v = BITMASK_TO_VARIANT.get(bitmask, 0)
            print(f"    Bitmask {bitmask:3d} -> Variant {v:2d}: {count:3d} tiles")
    
    # Return mapped variant, or 0 if not in blob tileset
    return variant


def _get_path_variant(n: bool, s: bool, e: bool, w: bool) -> int:
    """Calculate path autotile variant using 4-neighbor checking."""
    cardinal_count = sum([n, s, e, w])
    
    if cardinal_count == 0:
        return 0
    
    if cardinal_count == 1:
        if n or s:
            return 2
        else:
            return 1
    
    if cardinal_count == 2:
        if n and s:
            return 2
        if e and w:
            return 1
        if n and e:
            return 4  # Corner NE
        if n and w:
            return 3  # Corner NW
        if s and e:
            return 6  # Corner SE
        if s and w:
            return 5  # Corner SW
    
    if cardinal_count == 3:
        if not n:
            return 8
        if not s:
            return 7
        if not e:
            return 10
        if not w:
            return 9
    
    if cardinal_count == 4:
        return 11
    
    return 0


def _is_connected(grid, x: int, y: int, z: int, connect_to: Set[str]) -> bool:
    """Check if tile at position connects to the given tile types."""
    if not grid.in_bounds(x, y, z):
        return False
    
    # For overlay tiles, check the overlay layer
    # For regular tiles, check the base tile layer
    is_checking_overlay = any("overlay_autotile" in ct for ct in connect_to)
    
    if is_checking_overlay:
        # Check overlay layer
        tile = grid.get_overlay_tile(x, y, z)
        if tile is None:
            return False  # No overlay at this position
    else:
        # Check base tile layer
        tile = grid.get_tile(x, y, z)
    
    # Check if tile matches any in the connection set
    for connect_type in connect_to:
        if connect_type in tile:
            return True
    
    return False


# Autotile connection groups - defines which tile types connect to each other
AUTOTILE_GROUPS = {
    # Roads connect to all road types
    "street": {"street", "road", "street_autotile"},
    "road": {"street", "road", "street_autotile"},
    
    # Walls connect to walls (autotiled)
    "finished_wall": {"finished_wall", "finished_wall_autotile"},
    "wall": {"wall", "finished_wall", "finished_wall_autotile"},
    "finished_wall_autotile": {"finished_wall", "finished_wall_autotile"},
    
    # Bridges connect to bridges
    "finished_bridge": {"finished_bridge"},
    
    # Floors connect to floors
    "finished_floor": {"finished_floor"},
    
    # Ground overlays connect to same material type
    "ground_dirt_overlay_autotile": {"ground_dirt_overlay_autotile"},
    "ground_rubble_overlay_autotile": {"ground_rubble_overlay_autotile"},
    "ground_overgrown_overlay_autotile": {"ground_overgrown_overlay_autotile"},
}


def get_connection_set(tile_type: str) -> Set[str]:
    """Get the set of tile types that this tile connects to for autotiling."""
    # Check each group
    for key, group in AUTOTILE_GROUPS.items():
        if key in tile_type:
            return group
    
    # Default: only connect to same type
    return {tile_type}


def should_autotile(tile_type: str) -> bool:
    """Check if this tile type should use autotiling."""
    # Autotile roads, walls, bridges, floors, and ground overlays
    # Walls use autotiling when they have _autotile suffix
    autotile_keywords = ["street", "road", "bridge", "path", "overlay_autotile", "_autotile"]
    return any(keyword in tile_type for keyword in autotile_keywords)
