"""Organic terrain generation for natural-looking ground tiles.

Creates patches of dirt, rock, and grass using noise-like patterns.
"""

import random


def generate_terrain_patches(grid):
    """Generate organic patches of dirt, rock, and grass on empty tiles.
    
    Uses a simple cellular automata-like approach to create natural clusters.
    Only affects tiles that are currently "empty" - preserves streets, buildings, etc.
    """
    print("[TerrainGen] Generating organic terrain patches...")
    
    # Create a temporary terrain map
    terrain_map = {}
    
    # Step 1: Seed random terrain patches
    seed_count = 0
    for _ in range(200):  # Number of seed points
        x = random.randint(0, grid.width - 1)
        y = random.randint(0, grid.height - 1)
        
        # Only seed on empty tiles
        if grid.get_tile(x, y, 0) == "empty":
            # Random terrain type with weighted distribution
            terrain_type = random.choices(
                ["dirt", "grass", "rock", "empty"],
                weights=[40, 30, 15, 15]  # More dirt and grass, less rock
            )[0]
            terrain_map[(x, y)] = terrain_type
            seed_count += 1
    
    # Step 2: Grow patches outward (cellular automata style)
    for growth_iteration in range(3):  # Number of growth iterations
        new_terrain = {}
        
        for (sx, sy), terrain_type in terrain_map.items():
            if terrain_type == "empty":
                continue
                
            # Spread to neighboring tiles
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, 1), (-1, 1), (1, -1)]:
                nx, ny = sx + dx, sy + dy
                
                # Check bounds
                if not (0 <= nx < grid.width and 0 <= ny < grid.height):
                    continue
                
                # Only spread to empty tiles
                if grid.get_tile(nx, ny, 0) != "empty":
                    continue
                
                # Already has terrain assigned
                if (nx, ny) in terrain_map or (nx, ny) in new_terrain:
                    continue
                
                # Chance to spread (creates organic edges)
                if random.random() < 0.4:  # 40% chance to spread
                    new_terrain[(nx, ny)] = terrain_type
        
        # Merge new terrain into main map
        terrain_map.update(new_terrain)
    
    # Step 3: Apply terrain to grid
    dirt_count = 0
    grass_count = 0
    rock_count = 0
    
    for (x, y), terrain_type in terrain_map.items():
        # Double-check tile is still empty (in case worldgen changed it)
        if grid.get_tile(x, y, 0) == "empty":
            grid.set_tile(x, y, terrain_type, z=0)
            
            if terrain_type == "dirt":
                dirt_count += 1
            elif terrain_type == "grass":
                grass_count += 1
            elif terrain_type == "rock":
                rock_count += 1
    
    print(f"[TerrainGen] Created {dirt_count} dirt, {grass_count} grass, {rock_count} rock tiles")
    print(f"[TerrainGen] Total terrain patches: {dirt_count + grass_count + rock_count}")
