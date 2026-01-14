# Architecture - Fractured City

**Last Updated:** January 10, 2026  
**Renderer:** Python Arcade (GPU-accelerated)

---

## High-Level Overview

Fractured City is a **colony simulation game** built with Python Arcade. The architecture separates **game logic** (simulation) from **rendering** (presentation), allowing for clean code and future portability to Godot.

```
┌─────────────────────────────────────────────────┐
│              main.py (Entry Point)              │
│  - Arcade window initialization                 │
│  - Game loop (60 FPS)                           │
│  - Event handling (input, UI clicks)            │
└─────────────────────────────────────────────────┘
                        │
        ┌───────────────┴───────────────┐
        │                               │
┌───────▼────────┐             ┌────────▼────────┐
│  SIMULATION    │             │   RENDERING     │
│  (Game Logic)  │             │   (Arcade GPU)  │
└────────────────┘             └─────────────────┘
```

---

## Core Architecture

### 1. Entry Point

**`main.py`** (formerly `main_arcade.py`)
- Initializes Arcade window
- Creates `FracturedCityWindow` class
- Runs game loop at 60 FPS
- Handles all input events

**Key Methods:**
- `__init__()` - Setup world, colonists, UI
- `on_update(delta_time)` - Simulation tick (60 Hz)
- `on_draw()` - Render frame
- `on_mouse_press()`, `on_key_press()` - Input handling

---

### 2. World State (Simulation Core)

**`grid.py`** - World Data
- 3D tile grid (X, Y, Z)
- Tile types, walkability, overlays
- Environment parameters (interference, echo, pressure)
- Camera position and zoom

**Global Registries:**
- `JOB_QUEUE` (jobs.py) - All active jobs
- `_RESOURCE_NODES` (resources.py) - Resource locations
- `_STOCKPILE` (resources.py) - Stockpile contents
- `_ZONES` (zones.py) - Stockpile zones
- `WORLD_ITEMS` (items.py) - Dropped items
- `COLONISTS` (main.py) - All colonists
- `ANIMALS` (animals.py) - All animals

---

### 3. Simulation Systems

#### Colonist AI (`colonist.py`)
**State Machine:**
- `idle` - No task, may wander/chat
- `moving_to_job` - Walking to job location
- `performing_job` - Working on task
- `eating` - Consuming food
- `recovery` - Brief pause after interruption

**Job Selection:**
1. Check hunger (eating takes priority)
2. Scan `JOB_QUEUE` for available jobs
3. Score jobs by priority + distance
4. Claim highest-scoring job
5. Pathfind to job location
6. Execute job

#### Job System (`jobs.py`)
**Job Structure:**
```python
{
    "type": "build",
    "category": "construction",
    "priority": 5,
    "x": 45, "y": 78, "z": 0,
    "metadata": {...}
}
```

**Job Types:**
- `build` - Construction
- `haul` - Move items
- `craft` - Workstation crafting
- `harvest` - Gather resources
- `salvage` - Scrap collection
- `hunt` - Chase and kill animals
- `equip` - Pick up equipment

#### Resource System (`resources.py`)
**Resource Nodes:**
- Trees (wood)
- Mineral deposits
- Scrap piles

**Stockpile System:**
- Per-tile storage (max 100 per tile)
- Resource filters (allow/deny by type)
- Auto-relocation when filters change

#### Building System (`buildings.py`)
**Building Types:**
- Walls, floors, doors, windows
- Workstations (11 types)
- Furniture (beds, tables, chairs)

**Construction Flow:**
1. Player designates construction
2. Blueprint placed (ghost tile)
3. Job created in `JOB_QUEUE`
4. Colonist claims job
5. Colonist gathers materials
6. Colonist works at site
7. Structure completes

---

### 4. Rendering System (Arcade)

#### Grid Renderer (`grid_arcade.py`)
**Rendering Pipeline:**
1. Calculate viewport (visible tiles)
2. Render ground layer (concrete, dirt)
3. Render dirt overlays (additive autotiles)
4. Render structures (walls, floors)
5. Render resources (trees, minerals)
6. Render furniture (beds, workstations)
7. Render items (dropped world items)

**Sprite Caching:**
```python
sprite_cache = {
    "wall_0": Texture,
    "finished_wall_0": Texture,
    # ... thousands of cached sprites
}
```

#### Colonist Renderer (`colonist_arcade.py`)
- Renders colonist sprites (8 directions × 2 states)
- Animation (walking bob, combat shake)
- Equipment overlay (future)

#### UI System (Arcade Native)
**UI Files:**
- `ui_arcade.py` - Top bar, action bar
- `ui_arcade_panels.py` - Left sidebar
- `ui_arcade_colonist_popup.py` - Colonist detail
- `ui_arcade_bed.py` - Bed assignment
- `ui_arcade_workstation.py` - Workstation orders
- `ui_arcade_trader.py` - Trader interface
- `ui_arcade_visitor.py` - Visitor panel
- `ui_arcade_stockpile.py` - Stockpile filters
- `ui_arcade_notifications.py` - Notifications
- `ui_arcade_tile_info.py` - Tile hover info

**UI Rendering:**
- Drawn after world rendering
- Uses screen coordinates (not world coordinates)
- Click handling in `main.py::on_mouse_press()`

---

### 5. Data Flow

#### Simulation Tick (60 Hz)
```
main.py::on_update()
  ├─ Update time (game clock)
  ├─ Update colonists (AI, movement, jobs)
  ├─ Update resources (node depletion)
  ├─ Update animals (movement, flee)
  ├─ Update doors/windows (open/close)
  ├─ Process jobs (timeouts, cleanup)
  ├─ Process hauling (auto-haul items)
  ├─ Process crafting (workstation recipes)
  ├─ Process equipment (auto-equip)
  ├─ Process relocation (stockpile filters)
  └─ Update audio (music, SFX)
```

#### Rendering Frame (60 FPS)
```
main.py::on_draw()
  ├─ Clear screen
  ├─ Set camera position
  ├─ grid_renderer.draw() - World tiles
  ├─ colonist_renderer.draw() - Colonists
  ├─ animal_renderer.draw() - Animals
  ├─ ui_panels.draw() - UI elements
  └─ Present frame
```

---

## File Organization

### Core Runtime
```
main.py                 # Entry point, game loop
config.py               # Constants, settings
```

### World State
```
grid.py                 # 3D tile grid
resources.py            # Resource nodes, stockpiles
buildings.py            # Building definitions
zones.py                # Stockpile zones
rooms.py                # Room detection (legacy)
room_system.py          # Room designation (current)
```

### Simulation
```
colonist.py             # Colonist AI
jobs.py                 # Job queue
pathfinding.py          # A* pathfinding
items.py                # Item definitions
animals.py              # Animal entities
hunting.py              # Hunt jobs
combat.py               # Combat system
body.py                 # Body part tracking
relationships.py        # Relationship system
conversations.py        # Dialogue system
traits.py               # Personality traits
```

### Rendering (Arcade)
```
grid_arcade.py          # Tile renderer
colonist_arcade.py      # Colonist renderer
animals_arcade.py       # Animal renderer
tileset_loader.py       # Sprite loading
autotiling.py           # Autotiling logic
```

### UI (Arcade)
```
ui_arcade.py            # Top/bottom bars
ui_arcade_panels.py     # Left sidebar
ui_arcade_colonist_popup.py
ui_arcade_bed.py
ui_arcade_workstation.py
ui_arcade_trader.py
ui_arcade_visitor.py
ui_arcade_stockpile.py
ui_arcade_notifications.py
ui_arcade_tile_info.py
ui_drawing.py           # UI utilities
ui_config.py            # UI constants
```

### Worldgen
```
city_generator.py       # Procedural city generation
worldgen_organic.py     # Organic terrain
worldgen_simple.py      # Simple test worldgen
```

### Utilities
```
save_system.py          # Save/load
audio.py                # Music, SFX
procedural_sfx.py       # Procedural sound generation
```

---

## Design Patterns

### 1. Global Registries
**Why:** Simple, fast access for simulation systems  
**Tradeoff:** Harder to test, potential coupling

**Example:**
```python
# jobs.py
JOB_QUEUE = []

# colonist.py
from jobs import JOB_QUEUE
job = JOB_QUEUE[0]
```

### 2. State Machines
**Where:** Colonist AI, animal AI  
**Why:** Clear state transitions, easy to debug

**Example:**
```python
if self.state == "idle":
    self.select_job()
elif self.state == "moving_to_job":
    self.move_toward_job()
elif self.state == "performing_job":
    self.work_on_job()
```

### 3. Event-Driven Updates
**Where:** Room detection, stockpile relocation  
**Why:** Avoid expensive per-frame scans

**Example:**
```python
# Only check room formation when wall completes
if wall_completed:
    try_form_room_at(x, y, z)
```

### 4. Sprite Caching
**Where:** All rendering  
**Why:** Load once, reuse forever (60 FPS)

**Example:**
```python
if sprite_name not in cache:
    cache[sprite_name] = load_texture(sprite_name)
return cache[sprite_name]
```

---

## Performance Considerations

### Optimizations
- **Sprite caching** - No disk I/O during gameplay
- **Viewport culling** - Only render visible tiles
- **Batch rendering** - 1 GPU call per sprite list
- **Throttled systems** - Some updates every 10/60 ticks
- **Early exits** - Skip work if conditions not met

### Bottlenecks (Current)
- **Pathfinding** - A* can be expensive for long paths
- **Colonist updates** - 50+ colonists may slow down
- **Job scanning** - Large job queues need optimization

### Future Optimizations
- Spatial hashing for colonist/animal lookups
- Job queue indexing by category
- Pathfinding caching
- Texture atlases for GPU batching

---

## Extensibility

### Adding a New System
1. Create new Python file (e.g., `farming.py`)
2. Define data structures (crops, growth stages)
3. Add job types to `jobs.py`
4. Integrate into colonist AI (`colonist.py`)
5. Add UI panel (`ui_arcade_farming.py`)
6. Wire into main loop (`main.py::on_update()`)

### Adding a New Workstation
1. Define in `buildings.py::BUILDING_TYPES`
2. Add recipes to `buildings.py::WORKSTATION_RECIPES`
3. Create sprites in `assets/workstations/`
4. Test placement and crafting

### Adding a New UI Panel
1. Create `ui_arcade_newpanel.py`
2. Implement `draw()` and `handle_click()` methods
3. Wire into `main.py::on_draw()` and `on_mouse_press()`

---

## Migration Path to Godot

### Arcade → Godot Mapping

| Arcade | Godot |
|--------|-------|
| `arcade.Sprite` | `Sprite2D` |
| `arcade.SpriteList` | `Node2D` with children |
| `arcade.Camera2D` | `Camera2D` |
| `arcade.draw_*` | `CanvasItem.draw_*` |
| UI panels | `Control` nodes |

### Migration Strategy
1. **Core logic stays Python** - Godot supports GDScript + Python
2. **Rendering rewrite** - Use Godot's scene system
3. **UI rebuild** - Use Godot's Control nodes
4. **Asset pipeline** - Same sprites, different loader

**Timeline:** 1 month for feature parity

---

## See Also

- `CURRENT_STATE.md` - What works now
- `ROADMAP.md` - Next 6 months
- `RENDERING_SYSTEM.md` - Arcade rendering details
- `SPRITE_SYSTEM.md` - Sprite organization
