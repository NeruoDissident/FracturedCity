"""
Quick script to create 13 placeholder wall sprites for testing autotiling.
Creates simple colored squares with variant numbers.
"""

from PIL import Image, ImageDraw, ImageFont
import os

# Create walls folder if it doesn't exist
os.makedirs("assets/tiles/walls", exist_ok=True)

# Create 13 wall sprites (variants 0-12)
for i in range(13):
    # Create 64x64 image
    img = Image.new('RGB', (64, 64), (100, 100, 150))  # Blue-gray
    draw = ImageDraw.Draw(img)
    
    # Draw border
    draw.rectangle([0, 0, 63, 63], outline=(70, 70, 120), width=2)
    
    # Draw number
    text = str(i)
    try:
        font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 36)
    except:
        font = ImageFont.load_default()
    
    # Center text
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (64 - text_width) // 2
    y = (64 - text_height) // 2
    
    # Draw text
    draw.text((x, y), text, font=font, fill=(255, 255, 255))
    
    # Save
    filename = f"assets/tiles/walls/finished_wall_autotile_{i}.png"
    img.save(filename)
    print(f"Created {filename}")

print("\n✓ Created 13 wall placeholder sprites")
print("Run the game and test wall autotiling!")
