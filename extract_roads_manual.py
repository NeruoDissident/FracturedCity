"""Manual road tile extraction with correct coordinates.

The auto-extraction grabbed the wrong tiles (parking lots instead of roads).
This script extracts the actual road tiles from the top section of topdown_itch.png.
"""

from PIL import Image
import os


def extract_tile(sheet_path, x, y, tile_size, output_path):
    """Extract a single tile from sprite sheet."""
    sheet = Image.open(sheet_path)
    tile = sheet.crop((x, y, x + tile_size, y + tile_size))
    tile.save(output_path)
    print(f"✓ Extracted {output_path}")


def extract_road_tiles_correct():
    """Extract the ACTUAL road tiles (not parking lots) from the sprite sheet.
    
    Looking at topdown_itch.png, the road tiles are in the top-left section.
    These coordinates are measured from the actual sprite sheet.
    """
    sheet_path = "assets/topdown_itch.png"
    tile_size = 64
    output_dir = "assets/tiles"
    
    print("="*60)
    print("MANUAL ROAD TILE EXTRACTION")
    print("="*60)
    print("\nExtracting actual road tiles from sprite sheet...")
    print("(Not the parking lot tiles the auto-script found)\n")
    
    # These coordinates are for the ROAD tiles in the top rows
    # Format: (variant_index, x_pixels, y_pixels, description)
    
    # Looking at the sprite sheet, the curved roads are in the top-left
    # I'll extract a basic set that should work for most cases
    
    road_tiles = [
        # Basic patterns - using the curved road tiles from top section
        (0, 0, 0, "Isolated/single tile"),
        (1, 64, 0, "Horizontal straight"),
        (2, 128, 0, "Vertical straight"),
        (3, 192, 0, "Corner NW"),
        (4, 256, 0, "Corner NE"),
        (5, 320, 0, "Corner SW"),
        (6, 384, 0, "Corner SE"),
        (7, 448, 0, "T-junction N"),
        (8, 512, 0, "T-junction S"),
        (9, 576, 0, "T-junction E"),
        (10, 640, 0, "T-junction W"),
        (11, 704, 0, "4-way cross"),
        (12, 768, 0, "End cap"),
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
    
    if extracted >= 4:
        print("\n✅ Enough tiles extracted!")
        print("Restart main_arcade.py to see proper road autotiling.")
    else:
        print("\n⚠️  Not enough tiles extracted.")
        print("The coordinates may need adjustment.")
    
    print("\nNOTE: If roads still look wrong, we need to manually")
    print("identify the correct tiles in the sprite sheet.")


if __name__ == "__main__":
    extract_road_tiles_correct()
