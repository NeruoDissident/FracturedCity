# Sprites Needed for Full Coverage

## ✅ Already Have (In assets/)
- `default_north.png` - Colonist facing away
- `default_east.png` - Colonist facing right
- `default_west.png` - Colonist facing left

## 🎨 Priority Sprites to Create

### Ground Tiles (Most Common)
- `empty_0.png` through `empty_7.png` - Dark earth (8 variations)
- `dirt_0.png` through `dirt_3.png` - Brown dirt (4 variations)
- `grass_0.png` through `grass_3.png` - Dark grass (4 variations)

### Floors
- `finished_floor_0.png` through `finished_floor_7.png` - Wood flooring (8 variations)
- `floor_0.png` through `floor_3.png` - Floor under construction (4 variations)

### Walls
- `finished_wall_0.png` through `finished_wall_3.png` - Completed walls (4 variations)
- `wall_0.png` through `wall_1.png` - Walls under construction (2 variations)

### Doors/Windows
- `finished_door.png` - Completed door
- `door.png` - Door under construction
- `finished_window.png` - Window
- `bar_door.png` - Saloon-style door

### Workstations (Finished)
- `finished_spark_bench.png` - Electronics workstation
- `finished_tinker_station.png` - Crafts bench
- `finished_generator.png` - Power generator
- `finished_gutter_forge.png` - Forge
- `finished_salvagers_bench.png` - Salvage bench
- `finished_stove.png` - Kitchen stove
- `finished_gutter_still.png` - Distillery

### Instruments (Placed)
- `scrap_guitar_placed.png` - Guitar on floor
- `drum_kit_placed.png` - Drum set
- `synth_placed.png` - Synthesizer
- `harmonica_placed.png` - Harmonica
- `amp_placed.png` - Amplifier

### Furniture
- `crash_bed.png` - Bed
- `comfort_chair.png` - Chair
- `bar_stool.png` - Stool
- `scrap_bar_counter.png` - Bar counter

## 📁 Folder Structure

You can organize sprites in subfolders or keep them in root `assets/`:

**Option 1: Root (Current - Works Now)**
```
assets/
  default_north.png
  default_east.png
  default_west.png
  finished_floor_0.png
  ...
```

**Option 2: Subfolders (Organized)**
```
assets/
  colonists/
    default_north.png
    default_east.png
    default_west.png
  tiles/
    finished_floor_0.png
    finished_wall_0.png
    ...
  buildings/
    finished_spark_bench.png
    ...
```

Both work! The system checks subfolders first, then falls back to root.

## 🎯 How It Works

1. **Sprite Found** → Displays your art
2. **Sprite Missing** → Falls back to procedural drawing (current colored rectangles)
3. **No code changes needed** → Just drop PNGs in assets folder

## 🚀 Quick Start

1. Create sprites at any resolution (256x256, 512x512, 1024x1024)
2. Save as PNG with transparency (for layered items)
3. Drop in `assets/` folder
4. Run game - sprites load automatically!

## 📊 Current Status

- ✅ Colonist sprites: **3/3** (north, east, west)
- ⏳ Tile sprites: **0/~50** (all use procedural fallback)
- ⏳ Building sprites: **0/~15** (all use procedural fallback)
- ⏳ Furniture sprites: **0/~10** (all use procedural fallback)

**The game works perfectly with or without sprites - add them at your own pace!**
