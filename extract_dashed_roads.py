"""Extract the dashed-line road tiles (the correct ones).

Looking at the sprite sheet, the roads with white dashed center lines
are in the middle-right section. These match the vertical road that's
already working correctly.
"""

from PIL import Image
import os


def extract_tile(sheet_path, x, y, tile_size, output_path):
    """Extract a single tile from sprite sheet."""
    sheet = Image.open(sheet_path)
    tile = sheet.crop((x, y, x + tile_size, y + tile_size))
    tile.save(output_path)
    print(f"✓ Extracted {os.path.basename(output_path)}")


def extract_dashed_roads():
    """Extract the dashed-line road tiles from the sprite sheet.
    
    These are the roads with white dashed center lines that match
    the vertical road (variant 2) that's already working.
    """
    sheet_path = "assets/topdown_itch.png"
    tile_size = 64
    output_dir = "assets/tiles"
    
    print("="*60)
    print("EXTRACTING DASHED-LINE ROADS")
    print("="*60)
    print("\nThese roads have white dashed center lines.")
    print("Looking at middle-right section of sprite sheet...\n")
    
    # Based on visual inspection of the sprite sheet:
    # - Vertical roads with dashed lines are around x=448-512, y=0-128
    # - Horizontal roads with dashed lines are around x=640-704, y=0-128
    # - Intersections are around x=576-640, y=0-128
    
    # I'll extract the tiles that match the style of variant 2 (vertical)
    # which is already working correctly
    
    road_tiles = [
        # Row 1 (y=0) - Basic straights and corners
        (1, 640, 0, "Horizontal straight - dashed line"),
        (2, 448, 0, "Vertical straight - dashed line (already correct)"),
        (11, 576, 0, "4-way cross - dashed lines"),
        
        # Row 2 (y=64) - More patterns
        (7, 576, 64, "T-junction N"),
        (8, 576, 128, "T-junction S"),
        (9, 512, 64, "T-junction E"),
        (10, 640, 64, "T-junction W"),
        
        # Corners - these might be in different locations
        (3, 512, 0, "Corner NW"),
        (4, 704, 0, "Corner NE"),
        (5, 512, 128, "Corner SW"),
        (6, 704, 128, "Corner SE"),
        
        # Special cases
        (0, 448, 128, "Isolated tile"),
        (12, 448, 64, "End cap"),
    ]
    
    extracted = 0
    
    for variant, x, y, description in road_tiles:
        output_path = os.path.join(output_dir, f"street_autotile_{variant}.png")
        
        try:
            extract_tile(sheet_path, x, y, tile_size, output_path)
            extracted += 1
        except Exception as e:
            print(f"✗ Failed variant {variant} ({description}): {e}")
    
    print("\n" + "="*60)
    print(f"EXTRACTION COMPLETE: {extracted}/13 tiles")
    print("="*60)
    print("\n✅ Restart main_arcade.py to test!")
    print("\nIf some tiles still look wrong, we may need to adjust")
    print("coordinates or use a mix of tiles from different sections.")


if __name__ == "__main__":
    extract_dashed_roads()
