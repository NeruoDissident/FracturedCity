"""Procedural city generation for Fractured City.

Generates a realistic ruined cyberpunk city with:
- Proper road networks with intersections
- Varied city blocks
- Buildings with architectural logic
- Alleys, plazas, and landmarks
- Organic urban structure
"""

import random
from typing import List, Tuple, Set, Dict, Optional
from config import GRID_W, GRID_H


class RoadNetwork:
    """Manages the city's road network."""
    
    def __init__(self, grid_width: int, grid_height: int):
        self.width = grid_width
        self.height = grid_height
        self.roads: Set[Tuple[int, int]] = set()
        self.intersections: List[Tuple[int, int]] = []
        self.main_streets: List[Dict] = []  # Major roads
        self.side_streets: List[Dict] = []  # Minor roads
        
    def generate_arterial_roads(self, num_horizontal: int = 2, num_vertical: int = 2):
        """Generate main arterial roads that divide the city into districts.
        
        These are the primary roads - wider spacing, run full length.
        Reduced to 2x2 grid for larger districts and longer road stretches.
        """
        # Horizontal arterials
        h_spacing = self.height // (num_horizontal + 1)
        for i in range(1, num_horizontal + 1):
            y = i * h_spacing
            road = {
                "type": "arterial_horizontal",
                "y": y,
                "x_start": 0,
                "x_end": self.width,
            }
            self.main_streets.append(road)
            
            # Place road tiles
            for x in range(self.width):
                self.roads.add((x, y))
        
        # Vertical arterials
        v_spacing = self.width // (num_vertical + 1)
        for i in range(1, num_vertical + 1):
            x = i * v_spacing
            road = {
                "type": "arterial_vertical",
                "x": x,
                "y_start": 0,
                "y_end": self.height,
            }
            self.main_streets.append(road)
            
            # Place road tiles
            for y in range(self.height):
                self.roads.add((x, y))
        
        # Find intersections (where arterials cross)
        for h_road in [r for r in self.main_streets if "horizontal" in r["type"]]:
            for v_road in [r for r in self.main_streets if "vertical" in r["type"]]:
                intersection = (v_road["x"], h_road["y"])
                self.intersections.append(intersection)
    
    def generate_local_streets(self, block_size_range: Tuple[int, int] = (20, 35)):
        """Generate local streets within districts created by arterials.
        
        These create the actual city blocks where buildings sit.
        Increased block size for longer road stretches and bigger buildings.
        """
        min_block, max_block = block_size_range
        
        # For each district (area between arterials), add local streets
        h_arterials = sorted([r["y"] for r in self.main_streets if "horizontal" in r["type"]])
        v_arterials = sorted([r["x"] for r in self.main_streets if "vertical" in r["type"]])
        
        # Add boundaries
        h_arterials = [0] + h_arterials + [self.height]
        v_arterials = [0] + v_arterials + [self.width]
        
        # For each district
        for i in range(len(h_arterials) - 1):
            for j in range(len(v_arterials) - 1):
                y_start = h_arterials[i] + 1
                y_end = h_arterials[i + 1] - 1
                x_start = v_arterials[j] + 1
                x_end = v_arterials[j + 1] - 1
                
                district_width = x_end - x_start
                district_height = y_end - y_start
                
                if district_width < 10 or district_height < 10:
                    continue
                
                # Add horizontal local streets
                y = y_start
                while y < y_end:
                    block_size = random.randint(min_block, max_block)
                    y += block_size
                    
                    if y < y_end - 3:  # Leave margin
                        road = {
                            "type": "local_horizontal",
                            "y": y,
                            "x_start": x_start,
                            "x_end": x_end,
                        }
                        self.side_streets.append(road)
                        
                        for x in range(x_start, x_end):
                            self.roads.add((x, y))
                
                # Add vertical local streets
                x = x_start
                while x < x_end:
                    block_size = random.randint(min_block, max_block)
                    x += block_size
                    
                    if x < x_end - 3:  # Leave margin
                        road = {
                            "type": "local_vertical",
                            "x": x,
                            "y_start": y_start,
                            "y_end": y_end,
                        }
                        self.side_streets.append(road)
                        
                        for y in range(y_start, y_end):
                            self.roads.add((x, y))
    
    def add_alleys(self, probability: float = 0.4):
        """Add narrow alleys between some buildings for variety.
        
        Alleys are 1-tile paths that cut through blocks, creating shortcuts
        and adding visual interest. Uses same autotiling as roads.
        """
        # Get all city blocks
        blocks = self.get_city_blocks()
        
        for block in blocks:
            # Skip small blocks
            if block["width"] < 8 or block["height"] < 8:
                continue
            
            # Random chance to add an alley
            if random.random() > probability:
                continue
            
            # Decide alley type
            alley_type = random.choice(["horizontal_cut", "vertical_cut", "cross", "L_shape"])
            
            if alley_type == "horizontal_cut":
                # Horizontal alley cutting through block
                alley_y = block["y"] + random.randint(2, block["height"] - 3)
                for x in range(block["x"], block["x"] + block["width"]):
                    self.roads.add((x, alley_y))
            
            elif alley_type == "vertical_cut":
                # Vertical alley cutting through block
                alley_x = block["x"] + random.randint(2, block["width"] - 3)
                for y in range(block["y"], block["y"] + block["height"]):
                    self.roads.add((alley_x, y))
            
            elif alley_type == "cross":
                # Cross-shaped alleys
                mid_x = block["x"] + block["width"] // 2
                mid_y = block["y"] + block["height"] // 2
                
                # Horizontal
                for x in range(block["x"], block["x"] + block["width"]):
                    self.roads.add((x, mid_y))
                
                # Vertical
                for y in range(block["y"], block["y"] + block["height"]):
                    self.roads.add((mid_x, y))
            
            elif alley_type == "L_shape":
                # L-shaped alley for corner access
                corner_x = block["x"] + random.randint(2, block["width"] - 3)
                corner_y = block["y"] + random.randint(2, block["height"] - 3)
                
                # Horizontal arm
                for x in range(block["x"], corner_x + 1):
                    self.roads.add((x, corner_y))
                
                # Vertical arm
                for y in range(block["y"], corner_y + 1):
                    self.roads.add((corner_x, y))
    
    def add_curved_roads(self, num_curves: int = 5):
        """Add curved connector roads between districts for organic feel.
        
        Creates diagonal and curved paths that connect different areas,
        breaking up the grid pattern.
        """
        # Get district centers
        h_arterials = sorted([r["y"] for r in self.main_streets if "horizontal" in r["type"]])
        v_arterials = sorted([r["x"] for r in self.main_streets if "vertical" in r["type"]])
        
        if len(h_arterials) < 2 or len(v_arterials) < 2:
            return
        
        for _ in range(num_curves):
            # Pick two random points to connect
            start_x = random.choice(v_arterials)
            start_y = random.choice(h_arterials)
            end_x = random.choice(v_arterials)
            end_y = random.choice(h_arterials)
            
            # Don't connect same point
            if start_x == end_x and start_y == end_y:
                continue
            
            # Create curved path using simple interpolation
            self._create_curved_path(start_x, start_y, end_x, end_y)
    
    def _create_curved_path(self, x1: int, y1: int, x2: int, y2: int):
        """Create a curved road path between two points.
        
        Uses simple stepped diagonal movement to create organic curves.
        The autotiling system will handle corner smoothing.
        """
        current_x = x1
        current_y = y1
        
        # Calculate direction
        dx = 1 if x2 > x1 else -1 if x2 < x1 else 0
        dy = 1 if y2 > y1 else -1 if y2 < y1 else 0
        
        # Create path with occasional direction changes for curves
        while current_x != x2 or current_y != y2:
            # Add current position to roads
            self.roads.add((current_x, current_y))
            
            # Decide whether to move horizontally or vertically
            # Bias toward whichever direction has more distance to cover
            x_dist = abs(x2 - current_x)
            y_dist = abs(y2 - current_y)
            
            if x_dist == 0:
                current_y += dy
            elif y_dist == 0:
                current_x += dx
            else:
                # Random choice weighted by remaining distance
                if random.random() < x_dist / (x_dist + y_dist):
                    current_x += dx
                else:
                    current_y += dy
            
            # Safety check
            if not (0 <= current_x < self.width and 0 <= current_y < self.height):
                break
    
    def get_city_blocks(self) -> List[Dict]:
        """Identify rectangular city blocks bounded by roads.
        
        Returns list of blocks with x, y, width, height, zone type.
        """
        blocks = []
        
        # Get all horizontal and vertical roads sorted
        h_roads = sorted(set(y for x, y in self.roads if self._is_horizontal_road(x, y)))
        v_roads = sorted(set(x for x, y in self.roads if self._is_vertical_road(x, y)))
        
        # Find blocks between roads
        for i in range(len(h_roads) - 1):
            for j in range(len(v_roads) - 1):
                x = v_roads[j] + 1
                y = h_roads[i] + 1
                width = v_roads[j + 1] - v_roads[j] - 1
                height = h_roads[i + 1] - h_roads[i] - 1
                
                if width >= 3 and height >= 3:  # Minimum block size
                    # Assign zone type based on location and randomness
                    zone_type = self._determine_zone_type(x, y, width, height)
                    
                    blocks.append({
                        "x": x,
                        "y": y,
                        "width": width,
                        "height": height,
                        "zone_type": zone_type
                    })
        
        return blocks
    
    def _determine_zone_type(self, x: int, y: int, width: int, height: int) -> str:
        """Determine zone type for a city block.
        
        Returns: "residential", "commercial", "industrial", "abandoned", "suburban", or "rural"
        
        Creates natural urban sprawl:
        - Core: Dense commercial/residential
        - Mid: Residential/industrial
        - Outer: Suburban (fewer buildings, more nature)
        - Edge: Rural (mostly nature, few intact buildings)
        """
        # Distance from center influences zone type
        center_x = self.width // 2
        center_y = self.height // 2
        dist_from_center = ((x - center_x) ** 2 + (y - center_y) ** 2) ** 0.5
        max_dist = (center_x ** 2 + center_y ** 2) ** 0.5
        
        # Normalize distance (0 = center, 1 = edge)
        normalized_dist = dist_from_center / max_dist
        
        # Zone distribution based on distance from center
        # Creates natural urban -> suburban -> rural gradient
        
        if normalized_dist < 0.25:
            # Urban core - dense commercial/residential
            return random.choices(
                ["commercial", "residential", "abandoned"],
                weights=[0.6, 0.3, 0.1]
            )[0]
        elif normalized_dist < 0.45:
            # Inner city - residential/industrial
            return random.choices(
                ["residential", "commercial", "industrial", "abandoned"],
                weights=[0.5, 0.2, 0.2, 0.1]
            )[0]
        elif normalized_dist < 0.65:
            # Suburban transition - fewer buildings, more nature
            return random.choices(
                ["suburban", "residential", "abandoned"],
                weights=[0.6, 0.3, 0.1]
            )[0]
        elif normalized_dist < 0.85:
            # Outer suburbs - sparse buildings
            return random.choices(
                ["suburban", "rural", "abandoned"],
                weights=[0.5, 0.4, 0.1]
            )[0]
        else:
            # Rural outskirts - mostly nature
            return random.choices(
                ["rural", "suburban"],
                weights=[0.8, 0.2]
            )[0]
    
    def _is_horizontal_road(self, x: int, y: int) -> bool:
        """Check if a road tile is part of a horizontal road."""
        # Check if there are road tiles to the left and right
        return (x - 1, y) in self.roads or (x + 1, y) in self.roads
    
    def _is_vertical_road(self, x: int, y: int) -> bool:
        """Check if a road tile is part of a vertical road."""
        # Check if there are road tiles above and below
        return (x, y - 1) in self.roads or (x, y + 1) in self.roads


class CityGenerator:
    """Main city generation coordinator."""
    
    def __init__(self, grid):
        self.grid = grid
        self.road_network = RoadNetwork(GRID_W, GRID_H)
        self.buildings: List[Dict] = []
        self.landmarks: List[Dict] = []
        
    def generate_city(self) -> Tuple[int, int]:
        """Generate a complete city with curves and alleys.
        
        Returns (spawn_x, spawn_y) for colonist placement.
        """
        print("[CityGen] Generating procedural city...")
        
        # Step 1: Generate road network (FEWER roads = BIGGER blocks = BIGGER buildings)
        print("[CityGen] Creating road network...")
        self.road_network.generate_arterial_roads(num_horizontal=2, num_vertical=2)
        self.road_network.generate_local_streets(block_size_range=(20, 35))
        
        # Step 2: Add curved connector roads for organic feel (FEWER for bigger blocks)
        print("[CityGen] Adding curved roads...")
        self.road_network.add_curved_roads(num_curves=2)
        
        # Step 3: Add alleys through blocks (MINIMAL for bigger blocks)
        print("[CityGen] Adding alleys...")
        self.road_network.add_alleys(probability=0.05)
        
        # Step 4: Identify city blocks (before placing roads, so we know zones)
        blocks = self.road_network.get_city_blocks()
        print(f"[CityGen] Identified {len(blocks)} city blocks")
        
        # Step 5: Fill empty spaces with ground tiles based on zone
        print("[CityGen] Placing base layer ground tiles...")
        ground_tiles_placed = self._place_ground_layer(blocks)
        
        # Step 6: Place roads on grid (autotiling will handle corners/curves)
        # Roads go OVER ground tiles
        print(f"[CityGen] Placing {len(self.road_network.roads)} road tiles...")
        for x, y in self.road_network.roads:
            if self.grid.in_bounds(x, y, 0):
                self.grid.set_tile(x, y, "street", z=0)
        
        # Step 6: Place buildings in blocks - dense placement with new tile system
        print("[CityGen] Placing buildings...")
        building_count = 0
        
        for block in blocks:
            if block["zone_type"] == "road":
                continue
            
            # Skip only TINY blocks (need at least 3x3)
            if block["width"] < 3 or block["height"] < 3:
                continue
            
            # MAXIMUM DENSITY: Fill each block with building(s) sized to fit
            # Calculate building size based on block size
            # 2-tile margin for 2-tile-wide roads (1 tile padding on each side)
            margin = 2
            available_width = block["width"] - margin * 2
            available_height = block["height"] - margin * 2
            
            # Place one LARGE building filling most of block (5-20 tiles)
            bldg_width = max(5, min(20, available_width))
            bldg_height = max(5, min(20, available_height))
            
            bx = block["x"] + margin
            by = block["y"] + margin
            
            if self._place_building_new_system(bx, by, bldg_width, bldg_height):
                building_count += 1
        
        # Step 7: Add landmarks (plazas, parks, major structures)
        print("[CityGen] Adding landmarks...")
        self._add_landmarks(blocks)
        
        # Step 8: Spawn resources throughout city (zone-based intelligent placement)
        print("[CityGen] Spawning resources (zone-based)...")
        wood_count, mineral_count, food_count, scrap_count = self._spawn_resources_intelligent(blocks)
        
        # Step 9: Find spawn location (near center, on a road)
        spawn_x, spawn_y = self._find_spawn_location()
        
        print(f"[CityGen] City generation complete!")
        print(f"[CityGen]   Roads: {len(self.road_network.roads)} tiles")
        print(f"[CityGen]   Blocks: {len(blocks)}")
        print(f"[CityGen]   Buildings: {building_count}")
        print(f"[CityGen]   Curves & Alleys: Added for organic layout")
        print(f"[CityGen]   Resources: {wood_count} wood, {mineral_count} mineral, {food_count} food, {scrap_count} scrap")
        print(f"[CityGen]   Spawn: ({spawn_x}, {spawn_y})")
        
        return spawn_x, spawn_y
    
    def _place_ground_layer(self, blocks: List[Dict]) -> int:
        """Fill empty spaces with ground tiles based on zone type.
        
        Returns number of ground tiles placed.
        """
        tiles_placed = 0
        
        for block in blocks:
            zone_type = block["zone_type"]
            
            # Determine ground tile type based on zone
            # NOTE: Concrete base is always rendered, these are OVERLAY tiles
            # Use base tile name without variant - autotiling system will calculate correct variant
            if zone_type == "commercial":
                # Commercial: mostly just concrete base (no overlay)
                ground_tiles = ["ground_concrete_0"]
                weights = [1.0]
            elif zone_type == "residential":
                # Residential: occasional grass patches (10%)
                ground_tiles = ["ground_concrete_0", "ground_overgrown_overlay_autotile"]
                weights = [0.9, 0.1]
            elif zone_type == "industrial":
                # Industrial: scattered dirt patches (15%)
                ground_tiles = ["ground_concrete_0", "ground_dirt_overlay_autotile"]
                weights = [0.85, 0.15]
            else:  # abandoned
                # Abandoned: mix of dirt (20%) and rubble (15%), rest concrete
                ground_tiles = ["ground_concrete_0", "ground_dirt_overlay_autotile", "ground_rubble_overlay_autotile"]
                weights = [0.65, 0.20, 0.15]
            
            # Fill block with ground tiles - ALL CONCRETE (no dirt for now)
            for dx in range(block["width"]):
                for dy in range(block["height"]):
                    x = block["x"] + dx
                    y = block["y"] + dy
                    
                    if not self.grid.in_bounds(x, y, 0):
                        continue
                    
                    if (x, y) in self.road_network.roads:
                        continue
                    
                    self.grid.set_tile(x, y, "ground_concrete_0", z=0)
                    tiles_placed += 1
        
        # Fill any remaining empty tiles outside blocks
        for x in range(self.grid.width):
            for y in range(self.grid.height):
                if not self.grid.in_bounds(x, y, 0):
                    continue
                
                tile = self.grid.get_tile(x, y, 0)
                if tile == "empty" and (x, y) not in self.road_network.roads:
                    # Fill with concrete base
                    self.grid.set_tile(x, y, "ground_concrete_0", z=0)
                    tiles_placed += 1
        
        # Generate zone-aware organic dirt patches
        print("[CityGen] Generating zone-aware dirt patches...")
        dirt_count = self._place_dirt_intelligent(blocks)
        
        print(f"[CityGen] Placed {dirt_count} dirt overlay tiles (zone-aware)")
        
        return tiles_placed
    
    def _OLD_place_buildings_in_blocks(self, blocks: List[Dict]) -> int:
        """Place buildings within city blocks.
        
        Returns number of buildings placed.
        """
        building_count = 0
        
        for block in blocks:
            zone_type = block["zone_type"]
            
            # Adjust building density based on zone type
            if zone_type == "rural":
                # Rural: Very few buildings (10% chance)
                if random.random() < 0.1:
                    fill_type = random.choices(
                        ["sparse", "single_large", "empty"],
                        weights=[0.5, 0.3, 0.2]
                    )[0]
                else:
                    fill_type = "empty"
            elif zone_type == "suburban":
                # Suburban: Sparse buildings (40% chance)
                if random.random() < 0.4:
                    fill_type = random.choices(
                        ["sparse", "single_large", "empty"],
                        weights=[0.6, 0.2, 0.2]
                    )[0]
                else:
                    fill_type = "empty"
            else:
                # Urban zones: Normal density
                fill_type = random.choices(
                    ["dense", "sparse", "single_large", "empty"],
                    weights=[0.4, 0.3, 0.2, 0.1]
                )[0]
            
            if fill_type == "dense":
                # Multiple small buildings
                building_count += self._place_dense_buildings(block)
            elif fill_type == "sparse":
                # Few medium buildings with gaps
                building_count += self._place_sparse_buildings(block)
            elif fill_type == "single_large":
                # One large building filling most of block
                building_count += self._place_large_building(block)
            # "empty" = leave as open space
        
        return building_count
    
    def _place_dense_buildings(self, block: Dict) -> int:
        """Fill block with multiple small buildings."""
        count = 0
        margin = 1
        zone_type = block.get("zone_type")
        
        # Try to fit multiple buildings
        x = block["x"] + margin
        while x < block["x"] + block["width"] - margin - 2:
            y = block["y"] + margin
            while y < block["y"] + block["height"] - margin - 2:
                # Random small building size
                bldg_width = random.randint(3, 5)
                bldg_height = random.randint(3, 5)
                
                # Check if it fits
                if x + bldg_width <= block["x"] + block["width"] - margin:
                    if y + bldg_height <= block["y"] + block["height"] - margin:
                        self._place_single_building(x, y, bldg_width, bldg_height, zone_type)
                        count += 1
                
                y += bldg_height + 1  # Gap between buildings
            
            x += random.randint(3, 5) + 1
        
        return count
    
    def _place_sparse_buildings(self, block: Dict) -> int:
        """Place a few medium-sized buildings with gaps."""
        count = 0
        num_buildings = random.randint(2, 4)
        zone_type = block.get("zone_type")
        
        for _ in range(num_buildings):
            # Random position in block
            bldg_width = random.randint(4, 7)
            bldg_height = random.randint(4, 7)
            
            if bldg_width >= block["width"] - 2 or bldg_height >= block["height"] - 2:
                continue
            
            x = block["x"] + random.randint(1, max(1, block["width"] - bldg_width - 1))
            y = block["y"] + random.randint(1, max(1, block["height"] - bldg_height - 1))
            
            if self._place_single_building(x, y, bldg_width, bldg_height, zone_type):
                count += 1
        
        return count
    
    def _place_large_building(self, block: Dict) -> int:
        """Place one large building filling most of the block."""
        margin = 1
        bldg_width = block["width"] - margin * 2
        bldg_height = block["height"] - margin * 2
        zone_type = block.get("zone_type")
        
        if bldg_width < 3 or bldg_height < 3:
            return 0
        
        x = block["x"] + margin
        y = block["y"] + margin
        
        if self._place_single_building(x, y, bldg_width, bldg_height, zone_type):
            return 1
        return 0
    
    def _place_single_building(self, x: int, y: int, width: int, height: int, zone_type: str = None) -> bool:
        """Place a single building structure.
        
        Args:
            zone_type: Optional zone type to adjust building condition
        
        Returns True if successful.
        """
        # Check if area is clear
        for dx in range(width):
            for dy in range(height):
                if not self.grid.in_bounds(x + dx, y + dy, 0):
                    return False
                tile = self.grid.get_tile(x + dx, y + dy, 0)
                if tile != "empty":
                    return False
        
        # Determine building condition based on zone
        if zone_type == "rural":
            # Rural buildings are mostly intact (survivors' homes)
            condition = random.choices(
                ["intact", "partial", "ruined"],
                weights=[0.7, 0.2, 0.1]
            )[0]
        elif zone_type == "suburban":
            # Suburban buildings are moderately intact
            condition = random.choices(
                ["intact", "partial", "ruined"],
                weights=[0.5, 0.3, 0.2]
            )[0]
        else:
            # Urban buildings are mostly damaged
            condition = random.choices(
                ["intact", "partial", "ruined"],
                weights=[0.15, 0.35, 0.5]
            )[0]
        
        # Place floor
        for dx in range(1, width - 1):
            for dy in range(1, height - 1):
                self.grid.set_tile(x + dx, y + dy, "finished_floor", z=0)
        
        # Place walls based on condition
        if condition == "intact":
            self._place_intact_walls(x, y, width, height)
        elif condition == "partial":
            self._place_partial_walls(x, y, width, height)
        else:  # ruined
            self._place_ruined_walls(x, y, width, height)
        
        # Add interior details (scrap, food, etc.)
        self._add_building_interior(x, y, width, height)
        
        return True
    
    def _place_intact_walls(self, x: int, y: int, width: int, height: int):
        """Place complete walls with entrance."""
        entrance_side = random.choice(["north", "south", "east", "west"])
        entrance_pos = random.randint(2, max(2, min(width, height) - 3))
        
        for dx in range(width):
            for dy in range(height):
                is_edge = (dx == 0 or dx == width - 1 or dy == 0 or dy == height - 1)
                if not is_edge:
                    continue
                
                # Skip entrance
                if entrance_side == "north" and dy == 0 and dx == entrance_pos:
                    continue
                if entrance_side == "south" and dy == height - 1 and dx == entrance_pos:
                    continue
                if entrance_side == "east" and dx == width - 1 and dy == entrance_pos:
                    continue
                if entrance_side == "west" and dx == 0 and dy == entrance_pos:
                    continue
                
                self.grid.set_tile(x + dx, y + dy, "finished_wall_autotile", z=0)
    
    def _place_partial_walls(self, x: int, y: int, width: int, height: int):
        """Place walls with gaps (damaged building)."""
        for dx in range(width):
            for dy in range(height):
                is_edge = (dx == 0 or dx == width - 1 or dy == 0 or dy == height - 1)
                if not is_edge:
                    continue
                
                # 40% chance of gap
                if random.random() < 0.4:
                    continue
                
                self.grid.set_tile(x + dx, y + dy, "finished_wall_autotile", z=0)
    
    def _place_ruined_walls(self, x: int, y: int, width: int, height: int):
        """Place heavily damaged walls (mostly salvage objects)."""
        for dx in range(width):
            for dy in range(height):
                is_edge = (dx == 0 or dx == width - 1 or dy == 0 or dy == height - 1)
                if not is_edge:
                    continue
                
                # 60% chance of gap
                if random.random() < 0.6:
                    continue
                
                # Mix of walls and salvage
                if random.random() < 0.5:
                    self.grid.set_tile(x + dx, y + dy, "finished_wall_autotile", z=0)
                else:
                    self.grid.set_tile(x + dx, y + dy, "salvage_object", z=0)
    
    def _add_building_interior(self, x: int, y: int, width: int, height: int):
        """Add resources and objects inside building."""
        # Add scrap piles
        num_scrap = random.randint(1, 3)
        for _ in range(num_scrap):
            sx = x + random.randint(1, max(1, width - 2))
            sy = y + random.randint(1, max(1, height - 2))
            if self.grid.get_tile(sx, sy, 0) == "finished_floor":
                self.grid.set_tile(sx, sy, "salvage_object", z=0)
        
        # Add food (rare)
        if random.random() < 0.3:
            fx = x + random.randint(1, max(1, width - 2))
            fy = y + random.randint(1, max(1, height - 2))
            if self.grid.get_tile(fx, fy, 0) == "finished_floor":
                # TODO: Place food node (requires resources.py integration)
                pass
    
    def _add_landmarks(self, blocks: List[Dict]):
        """Add special landmarks like plazas, parks, major structures."""
        # Pick a few random blocks to convert to landmarks
        if len(blocks) < 5:
            return
        
        landmark_blocks = random.sample(blocks, min(3, len(blocks) // 10))
        
        for block in landmark_blocks:
            landmark_type = random.choice(["plaza", "park", "ruins"])
            
            if landmark_type == "plaza":
                # Open paved area
                for dx in range(block["width"]):
                    for dy in range(block["height"]):
                        x = block["x"] + dx
                        y = block["y"] + dy
                        if self.grid.in_bounds(x, y, 0):
                            self.grid.set_tile(x, y, "finished_floor", z=0)
            
            elif landmark_type == "park":
                # Green space with trees
                # TODO: Add vegetation
                pass
            
            elif landmark_type == "ruins":
                # Heavily damaged area with debris
                for dx in range(block["width"]):
                    for dy in range(block["height"]):
                        x = block["x"] + dx
                        y = block["y"] + dy
                        if self.grid.in_bounds(x, y, 0) and random.random() < 0.3:
                            self.grid.set_tile(x, y, "debris", z=0)
    
    def _OLD_spawn_resources(self, blocks: List[Dict]) -> Dict[str, int]:
        """Spawn harvestable resources throughout the city.
        
        Returns dict with counts of each resource type spawned.
        """
        from resources import _place_node, spawn_salvage_object
        
        wood_count = 0
        mineral_count = 0
        food_count = 0
        scrap_count = 0
        
        # Debug: Check first few blocks
        debug_count = 0
        
        for block in blocks:
            # Skip roads
            if block["zone_type"] == "road":
                continue
            
            # Wood patches - ABUNDANT in all blocks (this is a colony sim, need resources to build!)
            # Place 15-25 tree nodes per block
            num_trees = random.randint(15, 25)
            for _ in range(num_trees):
                tx = block["x"] + random.randint(1, max(1, block["width"] - 2))
                ty = block["y"] + random.randint(1, max(1, block["height"] - 2))
                if self.grid.in_bounds(tx, ty, 0):
                    if _place_node(self.grid, tx, ty, "tree"):
                        wood_count += 1
            
            # Mineral nodes - ABUNDANT rubble piles everywhere
            # Place 10-20 mineral nodes per block
            num_minerals = random.randint(10, 20)
            for _ in range(num_minerals):
                mx = block["x"] + random.randint(1, max(1, block["width"] - 2))
                my = block["y"] + random.randint(1, max(1, block["height"] - 2))
                if self.grid.in_bounds(mx, my, 0):
                    if _place_node(self.grid, mx, my, "mineral_node"):
                        mineral_count += 1
            
            # Food plants - scattered throughout
            # Place 8-15 food plants per block
            num_food = random.randint(8, 15)
            for _ in range(num_food):
                fx = block["x"] + random.randint(1, max(1, block["width"] - 2))
                fy = block["y"] + random.randint(1, max(1, block["height"] - 2))
                if self.grid.in_bounds(fx, fy, 0):
                    if _place_node(self.grid, fx, fy, "food_plant"):
                        food_count += 1
            
            # Scrap/salvage - EVERYWHERE in a ruined city
            # Place 12-20 salvage objects per block
            num_scrap = random.randint(12, 20)
            for _ in range(num_scrap):
                sx = block["x"] + random.randint(1, max(1, block["width"] - 2))
                sy = block["y"] + random.randint(1, max(1, block["height"] - 2))
                if self.grid.in_bounds(sx, sy, 0):
                    if spawn_salvage_object(sx, sy, "salvage_pile"):
                        self.grid.set_tile(sx, sy, "salvage_object", z=0)
                        scrap_count += 1
        
        return {
            "wood": wood_count,
            "mineral": mineral_count,
            "food": food_count,
            "scrap": scrap_count
        }
    
    def _place_building_new_system(self, x: int, y: int, width: int, height: int) -> bool:
        """Place a building using NEW tile system (autotiling, layering).
        
        Returns True if building was placed.
        """
        # Check if area is clear
        for dx in range(width):
            for dy in range(height):
                if not self.grid.in_bounds(x + dx, y + dy, 0):
                    return False
                tile = self.grid.get_tile(x + dx, y + dy, 0)
                # Allow placement on ground tiles
                if tile not in ["empty", "ground_concrete_0", "ground_dirt_overlay"]:
                    return False
        
        # Place floor tiles (interior)
        for dx in range(1, width - 1):
            for dy in range(1, height - 1):
                self.grid.set_tile(x + dx, y + dy, "finished_floor", z=0)
        
        # Place walls (edges) - use finished_wall_autotile for proper autotiling
        # Determine building condition (will be overridden by _place_single_building if zone is passed)
        condition = random.choices(
            ["intact", "partial", "ruined"],
            weights=[0.3, 0.4, 0.3]
        )[0]
        
        if condition == "intact":
            # Full walls with entrance
            entrance_side = random.choice(["north", "south", "east", "west"])
            entrance_pos = random.randint(2, max(2, min(width, height) - 3))
            
            for dx in range(width):
                for dy in range(height):
                    is_edge = (dx == 0 or dx == width - 1 or dy == 0 or dy == height - 1)
                    if not is_edge:
                        continue
                    
                    # Skip entrance
                    if entrance_side == "north" and dy == 0 and dx == entrance_pos:
                        continue
                    if entrance_side == "south" and dy == height - 1 and dx == entrance_pos:
                        continue
                    if entrance_side == "east" and dx == width - 1 and dy == entrance_pos:
                        continue
                    if entrance_side == "west" and dx == 0 and dy == entrance_pos:
                        continue
                    
                    self.grid.set_tile(x + dx, y + dy, "finished_wall_autotile", z=0)
        
        elif condition == "partial":
            # Partial walls (50% coverage)
            for dx in range(width):
                for dy in range(height):
                    is_edge = (dx == 0 or dx == width - 1 or dy == 0 or dy == height - 1)
                    if is_edge and random.random() < 0.5:
                        self.grid.set_tile(x + dx, y + dy, "finished_wall_autotile", z=0)
        
        else:  # ruined
            # Minimal walls (25% coverage)
            for dx in range(width):
                for dy in range(height):
                    is_edge = (dx == 0 or dx == width - 1 or dy == 0 or dy == height - 1)
                    if is_edge and random.random() < 0.25:
                        self.grid.set_tile(x + dx, y + dy, "finished_wall_autotile", z=0)
        
        return True
    
    def _find_spawn_location(self) -> Tuple[int, int]:
        """Find a good spawn location near center on a road."""
        center_x = GRID_W // 2
        center_y = GRID_H // 2
        
        # Find nearest road to center
        best_dist = float('inf')
        best_pos = (center_x, center_y)
        
        for x, y in self.road_network.roads:
            dx = x - center_x
            dy = y - center_y
            dist = dx * dx + dy * dy
            if dist < best_dist:
                best_dist = dist
                best_pos = (x, y)
        
        return best_pos
    
    def _spawn_resources_intelligent(self, blocks: List[Dict]) -> Tuple[int, int, int, int]:
        """Spawn resources based on zone types and building conditions.
        
        Returns: (wood_count, mineral_count, food_count, scrap_count)
        """
        from resources import _place_node, spawn_salvage_object
        
        wood_count = 0
        mineral_count = 0
        food_count = 0
        scrap_count = 0
        
        # Process each block based on zone type
        for block in blocks:
            zone_type = block["zone_type"]
            x_start = block["x"]
            y_start = block["y"]
            width = block["width"]
            height = block["height"]
            
            # Determine resource spawn rates based on zone
            if zone_type == "rural":
                # Rural: Mostly trees, minimal other resources
                tree_rate = 0.35  # Heavy tree coverage
                mineral_rate = 0.03  # Very few minerals
                food_rate = 0.02  # Minimal canned food (reduced from 0.05)
                scrap_rate = 0.015  # Very little scrap (reduced from 0.04)
            elif zone_type == "suburban":
                # Suburban: Heavy trees, moderate resources
                tree_rate = 0.25  # Lots of trees
                mineral_rate = 0.08  # Some minerals
                food_rate = 0.04  # Moderate canned food (reduced from 0.12)
                scrap_rate = 0.03  # Some scrap (reduced from 0.10)
            elif zone_type == "abandoned":
                # Abandoned: Heavy resources, lots of scrap and minerals
                tree_rate = 0.15  # Trees growing through ruins
                mineral_rate = 0.20  # Rubble piles
                food_rate = 0.06  # Canned food in ruins (reduced from 0.18)
                scrap_rate = 0.08  # Salvage everywhere (reduced from 0.25)
            elif zone_type == "industrial":
                # Industrial: Minerals and scrap, few trees
                tree_rate = 0.05
                mineral_rate = 0.18
                food_rate = 0.025  # Some canned food in warehouses (reduced from 0.08)
                scrap_rate = 0.07  # (reduced from 0.22)
            elif zone_type == "residential":
                # Residential: Trees, food, moderate scrap
                tree_rate = 0.12
                mineral_rate = 0.08
                food_rate = 0.05  # Canned food in homes (reduced from 0.15)
                scrap_rate = 0.04  # (reduced from 0.12)
            else:  # commercial
                # Commercial: Least resources, some food/scrap
                tree_rate = 0.03
                mineral_rate = 0.05
                food_rate = 0.03  # Canned food in stores (reduced from 0.10)
                scrap_rate = 0.03  # (reduced from 0.10)
            
            # Spawn resources in this block
            for dy in range(height):
                for dx in range(width):
                    x = x_start + dx
                    y = y_start + dy
                    
                    if not self.grid.in_bounds(x, y, 0):
                        continue
                    
                    tile = self.grid.get_tile(x, y, 0)
                    
                    # Trees - cluster in open areas (not on floors)
                    if tile in ["ground_concrete_0", "ground_dirt_overlay_autotile"] and random.random() < tree_rate:
                        if _place_node(self.grid, x, y, "tree"):
                            wood_count += 1
                    
                    # Minerals - near walls and on open ground
                    elif tile in ["ground_concrete_0", "ground_dirt_overlay_autotile"] and random.random() < mineral_rate:
                        # Check if near a wall (more likely near ruins)
                        near_wall = False
                        for check_dx in [-1, 0, 1]:
                            for check_dy in [-1, 0, 1]:
                                if check_dx == 0 and check_dy == 0:
                                    continue
                                check_tile = self.grid.get_tile(x + check_dx, y + check_dy, 0)
                                if check_tile and "wall" in check_tile:
                                    near_wall = True
                                    break
                            if near_wall:
                                break
                        
                        # Higher chance near walls
                        if near_wall or random.random() < 0.5:
                            if _place_node(self.grid, x, y, "mineral_node"):
                                mineral_count += 1
                    
                    # Food (canned) - INSIDE and AROUND ruined buildings
                    elif tile == "finished_floor" and random.random() < food_rate:
                        if _place_node(self.grid, x, y, "food_plant"):
                            food_count += 1
                    # Also spawn food on ground near buildings
                    elif tile in ["ground_concrete_0", "ground_dirt_overlay_autotile"] and random.random() < (food_rate * 0.3):
                        # Check if near a floor tile (near building)
                        near_building = False
                        for check_dx in [-1, 0, 1]:
                            for check_dy in [-1, 0, 1]:
                                if check_dx == 0 and check_dy == 0:
                                    continue
                                check_tile = self.grid.get_tile(x + check_dx, y + check_dy, 0)
                                if check_tile == "finished_floor":
                                    near_building = True
                                    break
                            if near_building:
                                break
                        
                        if near_building:
                            if _place_node(self.grid, x, y, "food_plant"):
                                food_count += 1
                    
                    # Scrap - everywhere, but concentrated in industrial/abandoned
                    if random.random() < scrap_rate:
                        # Can spawn on floors or ground
                        if tile in ["finished_floor", "ground_concrete_0", "ground_dirt_overlay_autotile"]:
                            if spawn_salvage_object(x, y, "salvage_pile"):
                                self.grid.set_tile(x, y, "salvage_object", z=0)
                                scrap_count += 1
        
        return wood_count, mineral_count, food_count, scrap_count
    
    def _place_dirt_intelligent(self, blocks: List[Dict]) -> int:
        """Place dirt overlays based on zone types and building conditions.
        
        Returns: Number of dirt tiles placed
        """
        from terrain_overlay_generator import TerrainOverlayGenerator
        overlay_gen = TerrainOverlayGenerator(self.grid)
        
        total_dirt_count = 0
        
        # Process each block based on zone type
        for block in blocks:
            zone_type = block["zone_type"]
            x_start = block["x"]
            y_start = block["y"]
            width = block["width"]
            height = block["height"]
            
            # Determine dirt density based on zone
            if zone_type == "rural":
                # Very heavy dirt coverage in rural areas (natural ground)
                num_patches = random.randint(3, 6)
                radius_range = (10, 18)
                strength_range = (0.7, 0.95)
            elif zone_type == "suburban":
                # Heavy dirt in suburban areas
                num_patches = random.randint(2, 4)
                radius_range = (8, 14)
                strength_range = (0.6, 0.85)
            elif zone_type == "abandoned":
                # Heavy dirt coverage in abandoned areas
                num_patches = random.randint(2, 4)
                radius_range = (6, 12)
                strength_range = (0.6, 0.9)
            elif zone_type == "industrial":
                # Medium dirt in industrial zones
                num_patches = random.randint(1, 3)
                radius_range = (5, 10)
                strength_range = (0.5, 0.8)
            elif zone_type == "residential":
                # Light dirt in residential
                num_patches = random.randint(1, 2)
                radius_range = (4, 8)
                strength_range = (0.4, 0.7)
            else:  # commercial
                # Minimal dirt in commercial areas
                num_patches = random.randint(0, 1)
                radius_range = (3, 6)
                strength_range = (0.3, 0.6)
            
            # Generate dirt patches for this block
            for _ in range(num_patches):
                # Pick a random center point in the block
                center_x = x_start + random.randint(2, max(2, width - 3))
                center_y = y_start + random.randint(2, max(2, height - 3))
                
                # Generate patch around this center
                radius = random.randint(*radius_range)
                strength = random.uniform(*strength_range)
                
                # Place dirt in a circular pattern
                for dy in range(-radius, radius + 1):
                    for dx in range(-radius, radius + 1):
                        x = center_x + dx
                        y = center_y + dy
                        
                        if not self.grid.in_bounds(x, y, 0):
                            continue
                        
                        # Calculate distance from center
                        dist = (dx * dx + dy * dy) ** 0.5
                        if dist > radius:
                            continue
                        
                        # Falloff based on distance
                        falloff = 1.0 - (dist / radius)
                        if random.random() > (falloff * strength):
                            continue
                        
                        # Check tile type - only place on concrete base, avoid roads and floors
                        tile = self.grid.get_tile(x, y, 0)
                        if tile == "ground_concrete_0":
                            # Don't place on roads
                            if (x, y) not in self.road_network.roads:
                                self.grid.overlay_tiles[(x, y, 0)] = "ground_dirt_overlay_autotile"
                                total_dirt_count += 1
                        # Also place dirt near ruined buildings (on floors)
                        elif tile == "finished_floor" and zone_type in ["abandoned", "industrial"]:
                            # 30% chance to place dirt on floors in ruined areas
                            if random.random() < 0.3:
                                self.grid.overlay_tiles[(x, y, 0)] = "ground_dirt_overlay_autotile"
                                total_dirt_count += 1
        
        return total_dirt_count
