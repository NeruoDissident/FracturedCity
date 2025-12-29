"""Reusable organic terrain overlay generator for dirt, grass, and rubble.

This is the FINAL autotiling system template used throughout the entire game.
Creates large organic blobs with natural gaps and highly irregular edges.
"""

import random
import math
from typing import Set, Tuple


class TerrainOverlayGenerator:
    """Generate organic terrain overlays using noise and cellular automata.
    
    This system creates natural-looking terrain patches with:
    - Large organic blobs with substantial areas
    - Natural gaps and holes within formations
    - Highly irregular edges from multi-scale noise
    - No grid-like patterns
    - Perfect for city boroughs and terrain divisions
    """
    
    def __init__(self, grid):
        self.grid = grid
    
    def generate_overlay(
        self,
        overlay_type: str,
        num_patches: Tuple[int, int] = (5, 10),
        radius_range: Tuple[int, int] = (10, 25),
        strength_range: Tuple[float, float] = (0.6, 1.0),
        threshold_base: float = 0.45,
        threshold_variance: float = 0.25
    ) -> Set[Tuple[int, int]]:
        """Generate organic overlay tiles using noise-based terrain generation.
        
        Args:
            overlay_type: Tile type (e.g., "ground_dirt_overlay_autotile")
            num_patches: (min, max) number of patch centers
            radius_range: (min, max) influence radius for each patch
            strength_range: (min, max) strength of each patch
            threshold_base: Base threshold for tile placement
            threshold_variance: Random variance added to threshold
            
        Returns:
            Set of (x, y) coordinates where overlay tiles should be placed
        """
        overlay_tiles = set()
        
        # Create seed points for patches
        num = random.randint(*num_patches)
        patch_centers = []
        for _ in range(num):
            x = random.randint(15, self.grid.width - 15)
            y = random.randint(15, self.grid.height - 15)
            strength = random.uniform(*strength_range)
            radius = random.randint(*radius_range)
            patch_centers.append((x, y, strength, radius))
        
        # For each tile, calculate influence from all patch centers
        for gx in range(self.grid.width):
            for gy in range(self.grid.height):
                total_influence = 0.0
                
                for cx, cy, strength, radius in patch_centers:
                    # Distance to patch center
                    dx = gx - cx
                    dy = gy - cy
                    dist = math.sqrt(dx*dx + dy*dy)
                    
                    # Influence falls off with distance
                    if dist < radius:
                        # Multi-scale noise creates:
                        # - Organic irregular edges
                        # - Natural gaps/holes within blobs
                        # - Varied texture throughout
                        noise = self._noise(gx * 0.12, gy * 0.12)  # Medium-scale organic edges
                        noise += self._noise(gx * 0.35, gy * 0.35) * 0.7  # High-freq detail
                        noise += self._noise(gx * 0.04, gy * 0.04) * 0.4  # Large-scale gaps
                        
                        # Calculate influence with strong noise component
                        falloff = 1.0 - (dist / radius)
                        influence = strength * falloff + noise * 0.6
                        total_influence += influence
                
                # Threshold: if influence is high enough, place tile
                threshold = threshold_base + random.random() * threshold_variance
                if total_influence > threshold:
                    overlay_tiles.add((gx, gy))
        
        # Apply cellular automata to smooth and create more organic shapes
        overlay_tiles = self._cellular_automata_pass(overlay_tiles, iterations=2)
        
        # Remove thin single-tile runs (they look too grid-like)
        overlay_tiles = self._remove_thin_runs(overlay_tiles)
        
        # Add a few small scattered patches for variety
        for _ in range(random.randint(3, 8)):
            x = random.randint(10, self.grid.width - 10)
            y = random.randint(10, self.grid.height - 10)
            size = random.randint(2, 5)
            
            # Small irregular cluster
            for dx in range(-size, size + 1):
                for dy in range(-size, size + 1):
                    if random.random() < 0.5:
                        px, py = x + dx, y + dy
                        if 0 <= px < self.grid.width and 0 <= py < self.grid.height:
                            overlay_tiles.add((px, py))
        
        return overlay_tiles
    
    def _cellular_automata_pass(self, tiles: Set[Tuple[int, int]], iterations: int = 1) -> Set[Tuple[int, int]]:
        """Apply cellular automata rules to create more organic shapes.
        
        Rules favor thicker, clustered formations and remove thin single-tile runs.
        """
        current = tiles.copy()
        
        for _ in range(iterations):
            next_gen = set()
            
            # Check all tiles and their neighbors
            check_tiles = set()
            for x, y in current:
                for dx in range(-1, 2):
                    for dy in range(-1, 2):
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < self.grid.width and 0 <= ny < self.grid.height:
                            check_tiles.add((nx, ny))
            
            for x, y in check_tiles:
                # Count dirt neighbors (all 8 directions)
                dirt_neighbors = 0
                cardinal_neighbors = 0  # N, S, E, W only
                
                for dx in range(-1, 2):
                    for dy in range(-1, 2):
                        if dx == 0 and dy == 0:
                            continue
                        nx, ny = x + dx, y + dy
                        if (nx, ny) in current:
                            dirt_neighbors += 1
                            if (dx == 0 or dy == 0):  # Cardinal direction
                                cardinal_neighbors += 1
                
                # Apply rules that favor thick blobs and remove thin runs
                if dirt_neighbors >= 5:
                    # Strong cluster - always keep
                    next_gen.add((x, y))
                elif dirt_neighbors >= 4 and (x, y) in current:
                    # Medium cluster - keep if already present
                    next_gen.add((x, y))
                elif dirt_neighbors >= 3 and cardinal_neighbors >= 2:
                    # Has good cardinal support - keep to avoid thin lines
                    next_gen.add((x, y))
                elif (x, y) in current and cardinal_neighbors >= 3:
                    # Existing tile with strong cardinal support
                    next_gen.add((x, y))
            
            current = next_gen
        
        return current
    
    def _remove_thin_runs(self, tiles: Set[Tuple[int, int]]) -> Set[Tuple[int, int]]:
        """Remove single-tile runs that look too grid-like.
        
        A tile is removed if it only has neighbors in one cardinal direction
        (creating a straight line) and has no diagonal support.
        """
        filtered = set()
        
        for x, y in tiles:
            # Count neighbors in each direction
            has_north = (x, y - 1) in tiles
            has_south = (x, y + 1) in tiles
            has_east = (x + 1, y) in tiles
            has_west = (x - 1, y) in tiles
            
            # Count diagonal neighbors
            diagonal_count = 0
            for dx, dy in [(-1, -1), (1, -1), (-1, 1), (1, 1)]:
                if (x + dx, y + dy) in tiles:
                    diagonal_count += 1
            
            # Count cardinal neighbors
            cardinal_count = sum([has_north, has_south, has_east, has_west])
            
            # Remove if it's a thin run (only 1-2 cardinal neighbors and no diagonal support)
            if cardinal_count <= 1:
                # Single isolated tile or dead-end - keep it (will become variant 0)
                filtered.add((x, y))
            elif cardinal_count == 2:
                # Check if it's a straight line (opposite cardinals)
                is_horizontal_line = has_east and has_west and not has_north and not has_south
                is_vertical_line = has_north and has_south and not has_east and not has_west
                
                if (is_horizontal_line or is_vertical_line) and diagonal_count == 0:
                    # Thin straight run with no diagonal support - remove it
                    continue
                else:
                    # L-shape or has diagonal support - keep it
                    filtered.add((x, y))
            else:
                # 3+ cardinal neighbors - definitely keep
                filtered.add((x, y))
        
        return filtered
    
    def _noise(self, x: float, y: float) -> float:
        """Simple pseudo-random noise function.
        
        Returns value between -1 and 1.
        """
        # Simple hash-based noise
        n = int(x * 12.9898 + y * 78.233)
        n = (n << 13) ^ n
        n = (n * (n * n * 15731 + 789221) + 1376312589) & 0x7fffffff
        return (n / 1073741824.0) - 1.0
