"""
Quick script to check for missing sprites in the game.
Scans code for sprite references and compares against assets folder.
"""

import os
from pathlib import Path
from collections import defaultdict

# Scan assets folder for existing sprites
def get_existing_sprites():
    assets_dir = Path('assets')
    existing = defaultdict(list)
    
    for root, dirs, files in os.walk(assets_dir):
        for f in files:
            if f.endswith('.png'):
                rel_path = os.path.relpath(os.path.join(root, f), assets_dir)
                category = rel_path.split(os.sep)[0]
                existing[category].append(f.replace('.png', ''))
    
    return existing

# Get all building/workstation tile types from buildings.py
def get_building_sprites():
    from buildings import BUILDING_TYPES
    
    sprites_needed = []
    for key, data in BUILDING_TYPES.items():
        tile_type = data.get('tile_type', key)
        
        # Construction sprite
        sprites_needed.append(f"{tile_type}.png")
        
        # Finished sprite
        sprites_needed.append(f"finished_{tile_type}.png")
        
        # Multi-tile sprites
        size = data.get('size', (1, 1))
        if size != (1, 1):
            width, height = size
            # 3x3 multi-tile
            if width == 3 and height == 3:
                for suffix in ['_sw', '_s', '_se', '_w', '_center', '_e', '_nw', '_n', '_ne']:
                    sprites_needed.append(f"{tile_type}{suffix}.png")
                    sprites_needed.append(f"finished_{tile_type}{suffix}.png")
            # 2x2 multi-tile
            elif width == 2 and height == 2:
                for suffix in ['_sw', '_se', '_nw', '_ne']:
                    sprites_needed.append(f"{tile_type}{suffix}.png")
                    sprites_needed.append(f"finished_{tile_type}{suffix}.png")
            # 2x1 horizontal
            elif width == 2 and height == 1:
                for suffix in ['', '_e']:
                    sprites_needed.append(f"{tile_type}{suffix}.png")
                    sprites_needed.append(f"finished_{tile_type}{suffix}.png")
            # 1x2 vertical
            elif width == 1 and height == 2:
                for suffix in ['', '_top']:
                    sprites_needed.append(f"{tile_type}{suffix}.png")
                    sprites_needed.append(f"finished_{tile_type}{suffix}.png")
    
    return sprites_needed

# Get furniture sprites
def get_furniture_sprites():
    from furniture import FURNITURE_TILE_MAPPING, FURNITURE_SIZES
    
    sprites_needed = []
    for item_id, tile_type in FURNITURE_TILE_MAPPING.items():
        size = FURNITURE_SIZES.get(item_id, (1, 1))
        
        if size == (1, 1):
            sprites_needed.append(f"{tile_type}.png")
        else:
            width, height = size
            # 1x2 vertical (like crash_bed)
            if width == 1 and height == 2:
                sprites_needed.append(f"{tile_type}.png")
                sprites_needed.append(f"{tile_type}_top.png")
    
    return sprites_needed

# Main check
if __name__ == "__main__":
    print("=" * 60)
    print("MISSING SPRITES CHECK")
    print("=" * 60)
    
    existing = get_existing_sprites()
    
    print("\n📁 EXISTING SPRITES:")
    for category, sprites in sorted(existing.items()):
        print(f"\n  {category.upper()}/ ({len(sprites)} files)")
        for sprite in sorted(sprites)[:10]:  # Show first 10
            print(f"    ✓ {sprite}.png")
        if len(sprites) > 10:
            print(f"    ... and {len(sprites) - 10} more")
    
    print("\n" + "=" * 60)
    print("CHECKING BUILDINGS & WORKSTATIONS...")
    print("=" * 60)
    
    building_sprites = get_building_sprites()
    missing_buildings = []
    
    tiles_existing = existing.get('tiles', [])
    for sprite in building_sprites:
        sprite_name = sprite.replace('.png', '')
        if sprite_name not in tiles_existing:
            missing_buildings.append(sprite)
    
    if missing_buildings:
        print(f"\n❌ MISSING ({len(missing_buildings)} sprites):")
        for sprite in sorted(missing_buildings):
            print(f"  - assets/tiles/{sprite}")
    else:
        print("\n✅ All building sprites present!")
    
    print("\n" + "=" * 60)
    print("CHECKING FURNITURE...")
    print("=" * 60)
    
    furniture_sprites = get_furniture_sprites()
    missing_furniture = []
    
    furniture_existing = existing.get('furniture', [])
    for sprite in furniture_sprites:
        sprite_name = sprite.replace('.png', '')
        if sprite_name not in furniture_existing:
            missing_furniture.append(sprite)
    
    if missing_furniture:
        print(f"\n❌ MISSING ({len(missing_furniture)} sprites):")
        for sprite in sorted(missing_furniture):
            print(f"  - assets/furniture/{sprite}")
    else:
        print("\n✅ All furniture sprites present!")
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total missing sprites: {len(missing_buildings) + len(missing_furniture)}")
    print(f"  Buildings/Workstations: {len(missing_buildings)}")
    print(f"  Furniture: {len(missing_furniture)}")
    print("=" * 60)
