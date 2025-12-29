"""Tool to extract individual tiles from sprite sheets.

Usage:
    python extract_tiles.py

This will help you extract road tiles from topdown_itch.png and save them
as individual autotile variants.
"""

from PIL import Image
import os


def extract_tile(sheet_path, x, y, tile_size, output_path):
    """Extract a single tile from a sprite sheet.
    
    Args:
        sheet_path: Path to sprite sheet
        x, y: Top-left corner of tile in pixels
        tile_size: Size of tile (assumes square)
        output_path: Where to save extracted tile
    """
    sheet = Image.open(sheet_path)
    tile = sheet.crop((x, y, x + tile_size, y + tile_size))
    tile.save(output_path)
    print(f"Extracted tile to {output_path}")


def extract_road_tiles_interactive():
    """Interactive tool to extract road tiles from topdown_itch.png.
    
    Opens the sprite sheet and lets you click to extract tiles.
    """
    sheet_path = "assets/topdown_itch.png"
    
    if not os.path.exists(sheet_path):
        print(f"ERROR: {sheet_path} not found!")
        return
    
    sheet = Image.open(sheet_path)
    print(f"Sprite sheet loaded: {sheet.width}x{sheet.height}")
    print(f"Assuming 64x64 tiles")
    
    # Show the sprite sheet so you can identify tiles
    sheet.show()
    
    print("\n" + "="*60)
    print("ROAD TILE EXTRACTION GUIDE")
    print("="*60)
    print("\nLook at the sprite sheet and identify these road patterns:")
    print("  0. Isolated (single tile, no connections)")
    print("  1. Straight horizontal ─")
    print("  2. Straight vertical │")
    print("  3. Corner NW (connects S+E) ┐")
    print("  4. Corner NE (connects S+W) ┌")
    print("  5. Corner SW (connects N+E) ┘")
    print("  6. Corner SE (connects N+W) └")
    print("  7. T-junction N (connects S+E+W) ┬")
    print("  8. T-junction S (connects N+E+W) ┴")
    print("  9. T-junction E (connects N+S+W) ├")
    print(" 10. T-junction W (connects N+S+E) ┤")
    print(" 11. 4-way cross (all directions) ┼")
    print(" 12. End cap (single connection)")
    print("\nFor each variant, enter the pixel coordinates (x, y)")
    print("Coordinates are for the TOP-LEFT corner of the tile.")
    print("Press Enter to skip a variant.\n")
    
    tile_size = 64
    output_dir = "assets/tiles"
    
    # Autotile variant names
    variants = [
        ("isolated", "Isolated tile (no connections)"),
        ("straight_h", "Straight horizontal ─"),
        ("straight_v", "Straight vertical │"),
        ("corner_nw", "Corner NW ┐"),
        ("corner_ne", "Corner NE ┌"),
        ("corner_sw", "Corner SW ┘"),
        ("corner_se", "Corner SE └"),
        ("t_north", "T-junction N ┬"),
        ("t_south", "T-junction S ┴"),
        ("t_east", "T-junction E ├"),
        ("t_west", "T-junction W ┤"),
        ("cross", "4-way cross ┼"),
        ("end_cap", "End cap (dead end)")
    ]
    
    extracted = []
    
    for idx, (variant_name, description) in enumerate(variants):
        print(f"\n[{idx}] {description}")
        coords = input(f"    Enter coordinates (x,y) or press Enter to skip: ").strip()
        
        if not coords:
            print(f"    Skipped variant {idx}")
            continue
        
        try:
            x, y = map(int, coords.split(','))
            output_path = os.path.join(output_dir, f"street_autotile_{idx}.png")
            extract_tile(sheet_path, x, y, tile_size, output_path)
            extracted.append((idx, variant_name, x, y))
        except Exception as e:
            print(f"    ERROR: {e}")
            continue
    
    print("\n" + "="*60)
    print(f"EXTRACTION COMPLETE: {len(extracted)} tiles extracted")
    print("="*60)
    
    if extracted:
        print("\nExtracted tiles:")
        for idx, name, x, y in extracted:
            print(f"  street_autotile_{idx}.png ({name}) from ({x}, {y})")
        
        print("\n✅ Autotile sprites created! Restart the game to see them.")
    else:
        print("\n⚠️  No tiles extracted. Try again.")


def extract_road_tiles_batch():
    """Batch extract road tiles if you know the coordinates.
    
    Edit this function with the correct coordinates from your sprite sheet.
    """
    sheet_path = "assets/topdown_itch.png"
    tile_size = 64
    output_dir = "assets/tiles"
    
    # TODO: Measure these coordinates from topdown_itch.png
    # Format: (variant_index, x, y)
    # These are PLACEHOLDER coordinates - you need to measure the actual positions!
    tile_coords = [
        # (0, 0, 0),      # Isolated
        # (1, 64, 0),     # Straight horizontal
        # (2, 128, 0),    # Straight vertical
        # (3, 192, 0),    # Corner NW
        # (4, 256, 0),    # Corner NE
        # (5, 320, 0),    # Corner SW
        # (6, 384, 0),    # Corner SE
        # (7, 0, 64),     # T-junction N
        # (8, 64, 64),    # T-junction S
        # (9, 128, 64),   # T-junction E
        # (10, 192, 64),  # T-junction W
        # (11, 256, 64),  # 4-way cross
        # (12, 320, 64),  # End cap
    ]
    
    if not tile_coords:
        print("ERROR: No coordinates defined!")
        print("Edit extract_tiles.py::extract_road_tiles_batch() with actual coordinates.")
        return
    
    for idx, x, y in tile_coords:
        output_path = os.path.join(output_dir, f"street_autotile_{idx}.png")
        extract_tile(sheet_path, x, y, tile_size, output_path)
    
    print(f"\n✅ Extracted {len(tile_coords)} road tiles!")


if __name__ == "__main__":
    print("Road Tile Extractor")
    print("="*60)
    print("1. Interactive mode (click and extract)")
    print("2. Batch mode (if you know coordinates)")
    print("="*60)
    
    choice = input("Choose mode (1 or 2): ").strip()
    
    if choice == "1":
        extract_road_tiles_interactive()
    elif choice == "2":
        extract_road_tiles_batch()
    else:
        print("Invalid choice!")
