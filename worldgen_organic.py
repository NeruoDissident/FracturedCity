"""Organic worldgen using noise-based terrain generation for natural blob shapes."""

from typing import Tuple
from terrain_overlay_generator import TerrainOverlayGenerator


class OrganicWorldGen:
    """Generate organic terrain using the reusable overlay generator."""
    
    def __init__(self, grid):
        self.grid = grid
        self.overlay_gen = TerrainOverlayGenerator(grid)
    
    def generate(self) -> Tuple[int, int]:
        """Generate world with organic dirt patches using noise.
        
        Returns (spawn_x, spawn_y) for colonist placement.
        """
        print("[OrganicWorldGen] Generating organic terrain...")
        
        # Step 1: Fill with concrete base
        print("[OrganicWorldGen] Placing concrete base layer...")
        for x in range(self.grid.width):
            for y in range(self.grid.height):
                self.grid.tiles[0][y][x] = "ground_concrete_0"
        
        # Step 2: Generate organic dirt patches using the overlay generator
        print("[OrganicWorldGen] Generating organic dirt patches...")
        dirt_tiles = self.overlay_gen.generate_overlay(
            overlay_type="ground_dirt_overlay_autotile",
            num_patches=(5, 10),
            radius_range=(10, 25),
            strength_range=(0.6, 1.0),
            threshold_base=0.45,
            threshold_variance=0.25
        )
        
        # Step 3: Place dirt tiles in overlay layer
        for x, y in dirt_tiles:
            self.grid.overlay_tiles[(x, y, 0)] = "ground_dirt_overlay_autotile"
        
        print(f"[OrganicWorldGen] Placed {len(dirt_tiles)} dirt tiles in organic patterns")
        print("[OrganicWorldGen] World generation complete!")
        
        # Spawn at center
        spawn_x = self.grid.width // 2
        spawn_y = self.grid.height // 2
        return spawn_x, spawn_y
