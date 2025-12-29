"""
Batch resize all sprite assets to 64x64 for optimal performance.

This script will:
1. Backup original sprites to assets_backup/
2. Resize all PNG files in assets/ to 64x64
3. Preserve aspect ratio (fit within 64x64)
4. Use high-quality Lanczos resampling

Run from project root: python resize_sprites.py
"""

import os
import shutil
from pathlib import Path
from PIL import Image

# Configuration
TARGET_SIZE = 64
BACKUP_FOLDER = "assets_backup"
ASSETS_FOLDER = "assets"

def backup_assets():
    """Create backup of original assets."""
    if os.path.exists(BACKUP_FOLDER):
        print(f"[WARNING] Backup folder '{BACKUP_FOLDER}' already exists.")
        response = input("Overwrite existing backup? (y/n): ")
        if response.lower() != 'y':
            print("Backup cancelled. Exiting.")
            return False
        shutil.rmtree(BACKUP_FOLDER)
    
    print(f"Creating backup: {BACKUP_FOLDER}/")
    shutil.copytree(ASSETS_FOLDER, BACKUP_FOLDER)
    print(f"✓ Backup complete!")
    return True

def resize_image(image_path, target_size=64):
    """Resize image to fit within target_size x target_size, preserving aspect ratio."""
    try:
        img = Image.open(image_path)
        original_size = img.size
        
        # Calculate new size preserving aspect ratio
        width, height = img.size
        if width > height:
            new_width = target_size
            new_height = int((height / width) * target_size)
        else:
            new_height = target_size
            new_width = int((width / height) * target_size)
        
        # Resize with high-quality Lanczos resampling
        resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Save back to original path
        resized.save(image_path, 'PNG', optimize=True)
        
        return original_size, (new_width, new_height)
    except Exception as e:
        print(f"  [ERROR] Failed to resize {image_path}: {e}")
        return None, None

def resize_all_sprites():
    """Resize all PNG files in assets folder."""
    assets_path = Path(ASSETS_FOLDER)
    
    if not assets_path.exists():
        print(f"[ERROR] Assets folder not found: {ASSETS_FOLDER}")
        return
    
    # Find all PNG files recursively
    png_files = list(assets_path.rglob("*.png"))
    
    if not png_files:
        print(f"[WARNING] No PNG files found in {ASSETS_FOLDER}")
        return
    
    print(f"\nFound {len(png_files)} PNG files to resize...")
    print(f"Target size: {TARGET_SIZE}x{TARGET_SIZE} (preserving aspect ratio)\n")
    
    resized_count = 0
    skipped_count = 0
    total_savings = 0
    
    for png_file in png_files:
        relative_path = png_file.relative_to(assets_path)
        original_size, new_size = resize_image(png_file, TARGET_SIZE)
        
        if original_size and new_size:
            original_pixels = original_size[0] * original_size[1]
            new_pixels = new_size[0] * new_size[1]
            savings = ((original_pixels - new_pixels) / original_pixels) * 100
            total_savings += savings
            
            print(f"✓ {relative_path}")
            print(f"  {original_size[0]}x{original_size[1]} → {new_size[0]}x{new_size[1]} ({savings:.1f}% reduction)")
            resized_count += 1
        else:
            print(f"✗ {relative_path} (skipped)")
            skipped_count += 1
    
    print(f"\n{'='*60}")
    print(f"Resize complete!")
    print(f"  Resized: {resized_count} files")
    print(f"  Skipped: {skipped_count} files")
    if resized_count > 0:
        print(f"  Average pixel reduction: {total_savings/resized_count:.1f}%")
    print(f"{'='*60}\n")

def main():
    print("="*60)
    print("SPRITE RESIZE TOOL - Optimize for Performance")
    print("="*60)
    print(f"\nThis will resize all sprites in '{ASSETS_FOLDER}/' to {TARGET_SIZE}x{TARGET_SIZE}")
    print(f"Original sprites will be backed up to '{BACKUP_FOLDER}/'\n")
    
    response = input("Continue? (y/n): ")
    if response.lower() != 'y':
        print("Cancelled.")
        return
    
    # Step 1: Backup
    if not backup_assets():
        return
    
    # Step 2: Resize
    resize_all_sprites()
    
    print("\n✓ All done! Your sprites are now optimized.")
    print(f"  Original sprites backed up to: {BACKUP_FOLDER}/")
    print(f"  If anything looks wrong, restore from backup and adjust TARGET_SIZE\n")

if __name__ == "__main__":
    main()
