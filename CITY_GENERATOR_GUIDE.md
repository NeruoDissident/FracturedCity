# New Procedural City Generator

## What Changed

You now have a **complete city generation rewrite** that creates proper urban structure instead of just drawing straight lines.

### Old System (What You Had)
- Drew straight horizontal and vertical lines
- Called them "streets"
- No intersections, no curves, no urban logic
- Just a grid of lines

### New System (What You Have Now)
- **Road Network:** Arterial roads + local streets with real intersections
- **City Blocks:** Organic blocks bounded by roads
- **Buildings:** Varied placement (dense, sparse, large) with realistic damage states
- **Landmarks:** Plazas, parks, ruins for variety
- **Proper Structure:** Actual city layout with districts

---

## How It Works

### 1. Road Network Generation (`city_generator.py`)

**Arterial Roads:**
- Major roads that divide city into districts
- Run full length of map
- Create primary intersections

**Local Streets:**
- Secondary roads within districts
- Create city blocks (12-20 tiles apart)
- Varied spacing for organic feel

**Result:** Proper road network with intersections that autotiling can handle

### 2. Building Placement

**Three Fill Types:**
- **Dense:** Multiple small buildings (3-5 tiles)
- **Sparse:** Few medium buildings with gaps
- **Single Large:** One building filling block

**Three Damage States:**
- **Intact:** Complete walls with entrance (15%)
- **Partial:** Walls with gaps (35%)
- **Ruined:** Heavily damaged, mostly salvage (50%)

### 3. Landmarks

Random blocks converted to:
- **Plazas:** Open paved areas
- **Parks:** Green spaces (TODO: add vegetation)
- **Ruins:** Debris-filled areas

---

## Integration

The new system is **already integrated** into your game:

### `resources.py::spawn_resource_nodes()`
Now calls `CityGenerator` instead of old line-drawing code.

### What's Preserved
- All resource spawning (wood, scrap, minerals, food)
- Starter stockpile creation
- Colonist spawn location
- All game systems (jobs, pathfinding, etc.)

---

## Testing the New City

Run the game and you should see:

✅ **Roads with intersections** (autotiling will make them look clean)  
✅ **Varied city blocks** (not uniform rectangles)  
✅ **Buildings of different sizes** (3-7 tiles)  
✅ **Organic city layout** (feels like a real ruined city)  
✅ **Proper urban density** (tight cyberpunk megacity)

---

## Next Steps

### 1. Test Basic Generation
```bash
python main_arcade.py
```

Check:
- Roads form proper intersections
- Buildings fit in blocks
- City looks organic, not grid-locked
- Colonists can pathfind

### 2. Extract Autotile Sprites
```bash
python auto_extract_roads.py
```

This will make intersections look clean with proper corners.

### 3. Tune Parameters (Optional)

Edit `city_generator.py::generate_city()`:

```python
# More/fewer arterial roads
self.road_network.generate_arterial_roads(num_horizontal=4, num_vertical=4)

# Tighter/looser blocks
self.road_network.generate_local_streets(block_size_range=(10, 16))
```

### 4. Add Features (Future)

**Alleys:**
- Narrow 1-tile paths between buildings
- Add in `RoadNetwork::add_alleys()`

**Curves:**
- Diagonal roads
- Curved intersections
- Requires more autotile variants

**Districts:**
- Residential, commercial, industrial zones
- Different building densities per district
- Different damage levels per district

**Vertical Structures:**
- Multi-story buildings (Z-levels)
- Rooftop access
- Fire escapes between levels

---

## File Structure

### New Files
- **`city_generator.py`** - Main city generation system
  - `RoadNetwork` class - Manages roads and intersections
  - `CityGenerator` class - Coordinates city creation

### Modified Files
- **`resources.py`** - Now uses `CityGenerator`
  - `spawn_resource_nodes()` - Calls new system
  - `_spawn_resources_in_city()` - Adds resources to generated city

### Preserved Files
- All game logic files unchanged
- Grid system unchanged
- Autotiling system ready to use

---

## Architecture

```
CityGenerator
├── RoadNetwork
│   ├── generate_arterial_roads() → Main roads
│   ├── generate_local_streets() → City blocks
│   └── get_city_blocks() → Block identification
│
├── Building Placement
│   ├── _place_dense_buildings() → Multiple small
│   ├── _place_sparse_buildings() → Few medium
│   └── _place_large_building() → Single large
│
└── Landmarks
    ├── Plazas
    ├── Parks
    └── Ruins
```

---

## Comparison

### Before (Old Worldgen)
```
[Empty] [Empty] [Empty] [Empty] [Empty]
[Empty] [Street][Street][Street][Empty]
[Empty] [Empty] [Empty] [Empty] [Empty]
[Empty] [Street][Street][Street][Empty]
[Empty] [Empty] [Empty] [Empty] [Empty]
```

### After (New City Generator)
```
[Build] [Build] [Street][Build] [Build]
[Build] [Empty] [Street][Empty] [Build]
[Street][Street][Street][Street][Street]
[Build] [Empty] [Street][Build] [Build]
[Build] [Build] [Street][Build] [Empty]
```

Real intersections, varied blocks, organic structure!

---

## Status

✅ **Complete city generation system implemented**  
✅ **Integrated with existing game**  
✅ **Ready to test**  
⏳ **Autotile sprites needed for clean corners**  
⏳ **Tuning and polish**

Run the game and see your new procedural cyberpunk city!
