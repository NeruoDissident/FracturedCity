"""Test blob autotiling in isolation to verify the algorithm works correctly."""

import sys
sys.path.insert(0, 'c:\\Users\\thoma\\Fractured City')

from grid import Grid
from autotiling import get_autotile_variant, get_connection_set

# Create a small test grid
grid = Grid(width=20, height=20, depth=1)

# Fill with concrete base
for x in range(20):
    for y in range(20):
        grid.tiles[0][y][x] = "ground_concrete_0"

# Place a circular dirt patch at center (10, 10) with radius 5
print("Placing circular dirt patch at (10, 10) with radius 5...")
dirt_positions = []
for dx in range(-5, 6):
    for dy in range(-5, 6):
        if dx*dx + dy*dy <= 25:  # radius 5
            x, y = 10 + dx, 10 + dy
            if 0 <= x < 20 and 0 <= y < 20:
                grid.overlay_tiles[(x, y, 0)] = "ground_dirt_overlay_autotile"
                dirt_positions.append((x, y))

print(f"Placed {len(dirt_positions)} dirt tiles")
print(f"Positions: {dirt_positions}")

# Now calculate autotile variants for each dirt tile
print("\nCalculating autotile variants...")
variants = {}
for x, y in dirt_positions:
    variant = get_autotile_variant(
        grid, x, y, 0, 
        "ground_dirt_overlay_autotile",
        connect_to=get_connection_set("ground_dirt_overlay_autotile")
    )
    variants[(x, y)] = variant
    
# Print a visual map
print("\nDirt blob with variants:")
for y in range(20):
    row = ""
    for x in range(20):
        if (x, y) in variants:
            v = variants[(x, y)]
            if v < 10:
                row += f" {v} "
            else:
                row += f"{v} "
        else:
            row += " . "
    print(row)

# Check specific edge cases
print("\nEdge tile analysis:")
edge_tiles = [(5, 10), (15, 10), (10, 5), (10, 15)]  # N, S, E, W edges
for x, y in edge_tiles:
    if (x, y) in variants:
        v = variants[(x, y)]
        print(f"  ({x},{y}): variant {v}")

# Check corner tiles
print("\nCorner tile analysis:")
corner_tiles = [(7, 7), (13, 7), (7, 13), (13, 13)]  # NW, NE, SW, SE corners
for x, y in corner_tiles:
    if (x, y) in variants:
        v = variants[(x, y)]
        print(f"  ({x},{y}): variant {v}")

# Check center tile
print("\nCenter tile:")
if (10, 10) in variants:
    print(f"  (10,10): variant {variants[(10, 10)]} (should be 46 for full tile)")

print("\nTest complete!")
