"""Simple worldgen for testing blob autotiling.

Just concrete base + dirt blob patches. No roads, no buildings, no complexity.
"""

import random
from typing import Tuple


class SimpleWorldGen:
    """Minimal worldgen: concrete base + dirt blobs."""
    
    def __init__(self, grid):
        self.grid = grid
    
    def generate(self) -> Tuple[int, int]:
        """Generate simple world: concrete everywhere + dirt blob patches.
        
        Returns (spawn_x, spawn_y) for colonist placement.
        """
        print("[SimpleWorldGen] Generating test world...")
        
        # Step 1: Fill entire map with concrete base
        print("[SimpleWorldGen] Placing concrete base layer...")
        for x in range(self.grid.width):
            for y in range(self.grid.height):
                self.grid.tiles[0][y][x] = "ground_concrete_0"
        
        # Step 2: Place dirt patches with varied shapes to showcase all variants
        print("[SimpleWorldGen] Placing dirt blob patches...")
        
        # Create overlapping blobs to produce T-shapes, L-shapes, and complex corners
        # Center cluster - overlapping blobs create complex shapes
        center_x, center_y = self.grid.width // 2, self.grid.height // 2
        self._place_dirt_blob(center_x, center_y, 6)
        self._place_dirt_blob(center_x + 5, center_y, 5)
        self._place_dirt_blob(center_x - 5, center_y, 5)
        self._place_dirt_blob(center_x, center_y + 5, 5)
        self._place_dirt_blob(center_x, center_y - 5, 5)
        
        # Scattered individual blobs
        for i in range(15):
            x = random.randint(20, self.grid.width - 20)
            y = random.randint(20, self.grid.height - 20)
            radius = random.randint(3, 6)
            self._place_dirt_blob(x, y, radius)
            
            # 30% chance to add a small overlapping blob nearby
            if random.random() < 0.3:
                offset_x = random.randint(-4, 4)
                offset_y = random.randint(-4, 4)
                self._place_dirt_blob(x + offset_x, y + offset_y, random.randint(2, 4))
        
        print("[SimpleWorldGen] World generation complete!")
        
        # Spawn at center
        spawn_x = self.grid.width // 2
        spawn_y = self.grid.height // 2
        return spawn_x, spawn_y
    
    def _place_dirt_blob(self, center_x: int, center_y: int, radius: int):
        """Place a circular dirt blob at the given position.
        
        Uses overlay system - dirt doesn't replace concrete, it renders on top.
        """
        dirt_count = 0
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                # Circular shape
                if dx*dx + dy*dy > radius*radius:
                    continue
                
                x = center_x + dx
                y = center_y + dy
                
                if not self.grid.in_bounds(x, y, 0):
                    continue
                
                # Place dirt overlay (doesn't replace concrete base)
                self.grid.overlay_tiles[(x, y, 0)] = "ground_dirt_overlay_autotile"
                dirt_count += 1
        
        print(f"[SimpleWorldGen]   Dirt blob at ({center_x},{center_y}) radius={radius}: {dirt_count} tiles")
