"""Test to showcase ALL 47 blob autotile variants by creating specific patterns."""

import sys
sys.path.insert(0, 'c:\\Users\\thoma\\Fractured City')

from grid import Grid
from autotiling import get_autotile_variant, get_connection_set

# Create test grid
grid = Grid(width=50, height=50, depth=1)

# Fill with concrete
for x in range(50):
    for y in range(50):
        grid.tiles[0][y][x] = "ground_concrete_0"

print("Creating test patterns to showcase all 47 variants...")

# Pattern 1: Single isolated tile (variant 0)
grid.overlay_tiles[(5, 5, 0)] = "ground_dirt_overlay_autotile"

# Pattern 2: Straight line (variants 1-4, 13-14)
for x in range(10, 20):
    grid.overlay_tiles[(x, 10, 0)] = "ground_dirt_overlay_autotile"

# Pattern 3: L-shape (variants 5-8)
for x in range(10, 15):
    grid.overlay_tiles[(x, 15, 0)] = "ground_dirt_overlay_autotile"
for y in range(15, 20):
    grid.overlay_tiles[(10, y, 0)] = "ground_dirt_overlay_autotile"

# Pattern 4: T-shape (variants 15-18)
for x in range(20, 25):
    grid.overlay_tiles[(x, 20, 0)] = "ground_dirt_overlay_autotile"
for y in range(18, 23):
    grid.overlay_tiles[(22, y, 0)] = "ground_dirt_overlay_autotile"

# Pattern 5: Cross/+ shape (variants with 4 cardinals)
for x in range(30, 35):
    grid.overlay_tiles[(x, 25, 0)] = "ground_dirt_overlay_autotile"
for y in range(23, 28):
    grid.overlay_tiles[(32, y, 0)] = "ground_dirt_overlay_autotile"

# Pattern 6: Filled square (all interior = variant 46)
for x in range(10, 15):
    for y in range(30, 35):
        grid.overlay_tiles[(x, y, 0)] = "ground_dirt_overlay_autotile"

# Pattern 7: Diagonal connection
for i in range(5):
    grid.overlay_tiles[(20 + i, 30 + i, 0)] = "ground_dirt_overlay_autotile"

# Calculate variants for all placed tiles
print("\nCalculating variants...")
variant_counts = {}
for (x, y, z), tile_type in grid.overlay_tiles.items():
    variant = get_autotile_variant(
        grid, x, y, z,
        tile_type,
        connect_to=get_connection_set(tile_type)
    )
    variant_counts[variant] = variant_counts.get(variant, 0) + 1

print(f"\nTotal dirt tiles placed: {len(grid.overlay_tiles)}")
print(f"Unique variants used: {len(variant_counts)}")
print("\nVariant distribution:")
for v in sorted(variant_counts.keys()):
    count = variant_counts[v]
    print(f"  Variant {v:2d}: {count:3d} tiles")

# Check which variants are missing
all_variants = set(range(47))
used_variants = set(variant_counts.keys())
missing_variants = all_variants - used_variants

if missing_variants:
    print(f"\nMissing variants ({len(missing_variants)}): {sorted(missing_variants)}")
else:
    print("\n✓ ALL 47 VARIANTS USED!")

print("\nTest complete!")
