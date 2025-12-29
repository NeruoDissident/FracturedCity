"""Upscale 32x32 sprites to 64x64 using nearest-neighbor (pixel-perfect).

This script finds all PNG files in assets/tiles/ and upscales any that are 32x32
to 64x64 pixels, preserving the pixel art style.
"""

from PIL import Image
import os
from pathlib import Path


def upscale_sprite(input_path: str, output_path: str = None):
    """Upscale a 32x32 sprite to 64x64 using nearest-neighbor.
    
    Args:
        input_path: Path to input PNG file
        output_path: Path to save upscaled PNG (defaults to overwriting input)
    """
    if output_path is None:
        output_path = input_path
    
    # Open image
    img = Image.open(input_path)
    
    # Check if it's 32x32
    if img.size != (32, 32):
        print(f"  Skipping {os.path.basename(input_path)} - size is {img.size}, not 32x32")
        return False
    
    # Upscale to 64x64 using nearest-neighbor (no smoothing, pixel-perfect)
    upscaled = img.resize((64, 64), Image.NEAREST)
    
    # Save
    upscaled.save(output_path, 'PNG')
    print(f"  ✓ Upscaled {os.path.basename(input_path)} from 32x32 to 64x64")
    return True


def upscale_all_sprites(directory: str = "assets/tiles"):
    """Upscale all 32x32 PNG files in a directory to 64x64.
    
    Args:
        directory: Directory to search for PNG files
    """
    print(f"Scanning {directory} for 32x32 sprites...")
    print("=" * 60)
    
    # Find all PNG files
    png_files = list(Path(directory).glob("*.png"))
    
    if not png_files:
        print(f"No PNG files found in {directory}")
        return
    
    print(f"Found {len(png_files)} PNG files")
    print()
    
    upscaled_count = 0
    skipped_count = 0
    
    for png_path in sorted(png_files):
        try:
            if upscale_sprite(str(png_path)):
                upscaled_count += 1
            else:
                skipped_count += 1
        except Exception as e:
            print(f"  ✗ Error processing {png_path.name}: {e}")
            skipped_count += 1
    
    print()
    print("=" * 60)
    print(f"COMPLETE: Upscaled {upscaled_count} sprites, skipped {skipped_count}")
    print("=" * 60)


if __name__ == "__main__":
    # Upscale all sprites in assets/tiles/
    upscale_all_sprites("assets/tiles")
    
    print()
    print("You can now run the game:")
    print("  python main_arcade.py")
