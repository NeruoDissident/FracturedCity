"""Automatic road tile extraction from topdown_itch.png.

This script analyzes the sprite sheet and extracts road tiles based on visual patterns.
It identifies corners, straights, intersections, etc. and saves them as autotile variants.
"""

from PIL import Image
import os
import numpy as np


def analyze_tile_connectivity(tile_array):
    """Analyze which edges of a tile have road connections.
    
    Returns (north, south, east, west) as booleans.
    """
    height, width = tile_array.shape[:2]
    
    # Check edges for dark pixels (roads are dark)
    # We'll sample the middle of each edge
    
    # North edge (top)
    north_sample = tile_array[2:5, width//2-2:width//2+2]
    north_dark = np.mean(north_sample) < 100
    
    # South edge (bottom)
    south_sample = tile_array[height-5:height-2, width//2-2:width//2+2]
    south_dark = np.mean(south_sample) < 100
    
    # East edge (right)
    east_sample = tile_array[height//2-2:height//2+2, width-5:width-2]
    east_dark = np.mean(east_sample) < 100
    
    # West edge (left)
    west_sample = tile_array[height//2-2:height//2+2, 2:5]
    west_dark = np.mean(west_sample) < 100
    
    return north_dark, south_dark, east_dark, west_dark


def classify_tile(north, south, east, west):
    """Classify tile type based on connectivity.
    
    Returns autotile variant index (0-12) or None if not a valid road tile.
    """
    connections = sum([north, south, east, west])
    
    # No connections - isolated
    if connections == 0:
        return 0
    
    # Single connection - end cap
    if connections == 1:
        return 12
    
    # Two connections
    if connections == 2:
        if north and south:
            return 2  # Vertical straight
        if east and west:
            return 1  # Horizontal straight
        if south and east:
            return 3  # Corner NW
        if south and west:
            return 4  # Corner NE
        if north and east:
            return 5  # Corner SW
        if north and west:
            return 6  # Corner SE
    
    # Three connections - T-junctions
    if connections == 3:
        if not north:
            return 7  # T-junction N
        if not south:
            return 8  # T-junction S
        if not west:
            return 9  # T-junction E
        if not east:
            return 10  # T-junction W
    
    # Four connections - cross
    if connections == 4:
        return 11
    
    return None


def extract_road_tiles_auto():
    """Automatically extract road tiles from sprite sheet."""
    
    sheet_path = "assets/topdown_itch.png"
    output_dir = "assets/tiles"
    tile_size = 64
    
    if not os.path.exists(sheet_path):
        print(f"ERROR: {sheet_path} not found!")
        return
    
    print("Loading sprite sheet...")
    sheet = Image.open(sheet_path)
    sheet_array = np.array(sheet)
    
    print(f"Sprite sheet: {sheet.width}x{sheet.height}")
    print(f"Analyzing tiles (64x64)...")
    
    # Track which variants we've found
    found_variants = {}
    
    # Scan the sprite sheet in a grid
    rows = sheet.height // tile_size
    cols = sheet.width // tile_size
    
    print(f"Scanning {rows}x{cols} grid of tiles...")
    
    for row in range(rows):
        for col in range(cols):
            x = col * tile_size
            y = row * tile_size
            
            # Extract tile
            tile_array = sheet_array[y:y+tile_size, x:x+tile_size]
            
            # Skip if tile is mostly empty/transparent
            if tile_array.shape[0] < tile_size or tile_array.shape[1] < tile_size:
                continue
            
            # Convert to grayscale for analysis
            if len(tile_array.shape) == 3:
                gray_tile = np.mean(tile_array[:, :, :3], axis=2)
            else:
                gray_tile = tile_array
            
            # Check if this looks like a road tile (has dark pixels)
            dark_ratio = np.sum(gray_tile < 100) / (tile_size * tile_size)
            
            # Skip if less than 20% dark (probably not a road)
            if dark_ratio < 0.2:
                continue
            
            # Analyze connectivity
            north, south, east, west = analyze_tile_connectivity(gray_tile)
            
            # Classify tile
            variant = classify_tile(north, south, east, west)
            
            if variant is not None and variant not in found_variants:
                # Save this tile
                tile_img = sheet.crop((x, y, x + tile_size, y + tile_size))
                output_path = os.path.join(output_dir, f"street_autotile_{variant}.png")
                tile_img.save(output_path)
                
                found_variants[variant] = (x, y)
                
                # Variant names for logging
                variant_names = {
                    0: "Isolated",
                    1: "Horizontal straight",
                    2: "Vertical straight",
                    3: "Corner NW",
                    4: "Corner NE",
                    5: "Corner SW",
                    6: "Corner SE",
                    7: "T-junction N",
                    8: "T-junction S",
                    9: "T-junction E",
                    10: "T-junction W",
                    11: "4-way cross",
                    12: "End cap"
                }
                
                print(f"  ✓ Found variant {variant:2d} ({variant_names[variant]:20s}) at ({x:4d}, {y:4d})")
    
    print("\n" + "="*60)
    print(f"EXTRACTION COMPLETE: {len(found_variants)}/13 variants found")
    print("="*60)
    
    if len(found_variants) >= 4:
        print("\n✅ Enough tiles extracted! Restart the game to see autotiling.")
    else:
        print("\n⚠️  Only found", len(found_variants), "variants. May need manual extraction.")
    
    # List missing variants
    missing = [i for i in range(13) if i not in found_variants]
    if missing:
        print(f"\nMissing variants: {missing}")
        print("These will fall back to old street sprites.")
    
    return found_variants


if __name__ == "__main__":
    print("="*60)
    print("AUTOMATIC ROAD TILE EXTRACTOR")
    print("="*60)
    print("\nThis script will:")
    print("  1. Scan topdown_itch.png")
    print("  2. Identify road patterns automatically")
    print("  3. Extract and save autotile variants")
    print("\nPress Enter to start...")
    input()
    
    try:
        found = extract_road_tiles_auto()
        
        if found and len(found) > 0:
            print("\n" + "="*60)
            print("SUCCESS!")
            print("="*60)
            print(f"\nExtracted {len(found)} road tile variants to assets/tiles/")
            print("\nNext steps:")
            print("  1. Restart main_arcade.py")
            print("  2. Streets should now have clean corners and intersections!")
        else:
            print("\n" + "="*60)
            print("NO TILES FOUND")
            print("="*60)
            print("\nThe automatic detection didn't find road tiles.")
            print("You may need to use manual extraction (extract_tiles.py)")
    
    except Exception as e:
        print(f"\nERROR: {e}")
        print("\nTry manual extraction instead: python extract_tiles.py")
