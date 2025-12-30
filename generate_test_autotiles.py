"""
Generate numbered test sprites for autotiling debugging.

Creates 47 tiles (64x64) with large numbers for easy identification in screenshots.
Can be used for walls, floors, roads, bridges - any autotile system.

Usage:
    python generate_test_autotiles.py walls
    python generate_test_autotiles.py floors
    python generate_test_autotiles.py roads
"""

from PIL import Image, ImageDraw, ImageFont
import os
import sys


def generate_test_autotiles(output_folder: str, tile_name: str, tile_size: int = 64, count: int = 47):
    """Generate numbered test sprites for autotiling.
    
    Args:
        output_folder: Where to save the sprites (e.g., "assets/tiles/walls")
        tile_name: Base name for sprites (e.g., "finished_wall_autotile")
        tile_size: Size of each tile in pixels (default 64x64)
        count: Number of variants to generate (default 47 for blob autotiling)
    """
    # Create output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)
    
    # Colors for different tile types (easy to distinguish)
    colors = {
        "wall": (100, 100, 150),      # Blue-gray
        "floor": (120, 100, 80),       # Brown
        "road": (80, 80, 80),          # Dark gray
        "bridge": (100, 120, 100),     # Green-gray
        "dirt": (139, 90, 43),         # Brown
    }
    
    # Determine base color
    base_color = (100, 100, 100)  # Default gray
    for key, color in colors.items():
        if key in tile_name.lower():
            base_color = color
            break
    
    print(f"Generating {count} test sprites for '{tile_name}'...")
    print(f"Output folder: {output_folder}")
    print(f"Base color: RGB{base_color}")
    
    for i in range(count):
        # Create image
        img = Image.new('RGB', (tile_size, tile_size), base_color)
        draw = ImageDraw.Draw(img)
        
        # Draw border for visibility
        border_color = tuple(max(0, c - 30) for c in base_color)
        draw.rectangle([0, 0, tile_size-1, tile_size-1], outline=border_color, width=2)
        
        # Draw number in center
        text = str(i)
        
        # Try to use a large font, fall back to default if not available
        try:
            font = ImageFont.truetype("arial.ttf", 36)
        except:
            try:
                font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 36)
            except:
                font = ImageFont.load_default()
        
        # Get text bounding box for centering
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Center the text
        x = (tile_size - text_width) // 2
        y = (tile_size - text_height) // 2
        
        # Draw text with outline for visibility
        outline_color = (255, 255, 255) if sum(base_color) < 384 else (0, 0, 0)
        text_color = (0, 0, 0) if sum(base_color) > 384 else (255, 255, 255)
        
        # Draw outline
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx != 0 or dy != 0:
                    draw.text((x + dx, y + dy), text, font=font, fill=outline_color)
        
        # Draw main text
        draw.text((x, y), text, font=font, fill=text_color)
        
        # Save image
        filename = f"{tile_name}_{i}.png"
        filepath = os.path.join(output_folder, filename)
        img.save(filepath)
        
        if i % 10 == 0:
            print(f"  Generated {i}/{count}...")
    
    print(f"✓ Generated {count} test sprites in {output_folder}")
    print(f"  Files: {tile_name}_0.png through {tile_name}_{count-1}.png")


def main():
    """Main entry point for command-line usage."""
    if len(sys.argv) < 2:
        print("Usage: python generate_test_autotiles.py <type>")
        print("Types: walls, floors, roads, bridges, dirt")
        print("\nExamples:")
        print("  python generate_test_autotiles.py walls")
        print("  python generate_test_autotiles.py floors")
        print("  python generate_test_autotiles.py roads")
        return
    
    tile_type = sys.argv[1].lower()
    
    # Configuration for different tile types
    configs = {
        "walls": {
            "folder": "assets/tiles/walls",
            "name": "finished_wall_autotile",
            "count": 13  # 13-tile path system
        },
        "floors": {
            "folder": "assets/tiles",
            "name": "finished_floor",
            "count": 8  # Simple variations
        },
        "roads": {
            "folder": "assets/tiles/roads",
            "name": "street_autotile",
            "count": 13  # 13-tile path system
        },
        "bridges": {
            "folder": "assets/tiles",
            "name": "finished_bridge",
            "count": 13  # 13-tile path system
        },
        "dirt": {
            "folder": "assets/tiles/dirt",
            "name": "ground_dirt_overlay_autotile",
            "count": 47  # 47-tile blob system
        },
    }
    
    if tile_type not in configs:
        print(f"Unknown type: {tile_type}")
        print(f"Available types: {', '.join(configs.keys())}")
        return
    
    config = configs[tile_type]
    generate_test_autotiles(
        output_folder=config["folder"],
        tile_name=config["name"],
        count=config["count"]
    )
    
    print("\n" + "="*60)
    print("TEST SPRITES READY!")
    print("="*60)
    print(f"Now run the game and place {tile_type}.")
    print("In screenshots, you'll see the variant numbers clearly.")
    print("This makes it easy to verify autotiling logic!")


if __name__ == "__main__":
    main()
