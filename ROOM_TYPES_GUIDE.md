# FRACTURED CITY - ROOM TYPES & REQUIREMENTS

**System:** Manual room designation (player-driven, no auto-detection)
**Location:** `room_system.py`

---

## 🛏️ BEDROOM

**Purpose:** Private sleeping quarters for colonists

### Requirements:
- **Min Size:** 4 tiles
- **Max Size:** 100 tiles
- **Required Furniture:** 1x crash_bed
- **Max Entrances:** 2 doors/windows
- **Must Be Enclosed:** Yes (walls/doors on all sides)
- **Must Have Roof:** Yes

### Quality Bonuses (per item):
- Cabinet: +5
- Desk: +8
- Statue: +10
- Lamp: +3
- Size: +1 per tile over minimum

### Effects:
- Sleep Quality: 1.0 + (quality × 0.01) = **1.0 to 2.0x**
- Mood Bonus: quality × 0.1 = **0 to +10**

### Can Assign Owner: ✅ Yes

---

## 🍳 KITCHEN

**Purpose:** Food preparation area

### Requirements:
- **Min Size:** 6 tiles
- **Required Furniture:** 1x finished_stove
- **Must Be Enclosed:** Yes
- **Must Have Roof:** Yes

### Quality Bonuses:
- Fridge: +10
- Counter: +5
- Size: +1 per tile over minimum

### Effects:
- Cooking Speed: 1.0 + (quality × 0.002) = **1.0 to 1.2x**
- Food Quality: 1.0 + (quality × 0.001) = **1.0 to 1.1x**

### Can Assign Owner: ✅ Yes (assign cook)

---

## 🔧 WORKSHOP

**Purpose:** Crafting and manufacturing space

### Requirements:
- **Min Size:** 8 tiles
- **Required Furniture (any one):**
  - finished_gutter_forge
  - finished_skinshop_loom
  - finished_cortex_spindle
  - finished_salvagers_bench
- **Must Be Enclosed:** Yes
- **Must Have Roof:** Yes

### Quality Bonuses:
- Workbench: +8
- Storage: +5
- Size: +1 per tile over minimum

### Effects:
- Craft Speed: 1.0 + (quality × 0.0015) = **1.0 to 1.15x**
- Skill Gain: 1.0 + (quality × 0.002) = **1.0 to 1.2x**

### Can Assign Owner: ✅ Yes (assign crafter)

---

## 🎖️ BARRACKS

**Purpose:** Military training and sleeping quarters

### Requirements:
- **Min Size:** 12 tiles
- **Required Furniture:**
  - 2x crash_bed (minimum)
  - 1x finished_barracks (training station)
- **Must Be Enclosed:** Yes
- **Must Have Roof:** Yes
- **Wall Type:** Reinforced (finished_wall_advanced)

### Quality Bonuses:
- Locker: +5
- Weapon Rack: +8
- Size: +1 per tile over minimum

### Effects:
- Sleep Quality: 1.0 + (quality × -0.001) = **0.9x** (worse than bedroom)
- Training Speed: 1.0 + (quality × 0.003) = **1.0 to 1.3x**
- Discipline: 1.0 + (quality × 0.001) = **1.0 to 1.1x**

### Can Assign Owner: ❌ No (shared space)

---

## 🔒 PRISON CELL

**Purpose:** Secure holding cell for prisoners

### Requirements:
- **Min Size:** 4 tiles
- **Max Size:** 20 tiles
- **Required Furniture:** 1x crash_bed
- **Max Entrances:** 1 door only
- **Must Be Enclosed:** Yes
- **Must Have Roof:** Yes
- **Door Type:** Reinforced

### Quality Bonuses:
- Size: -2 per tile (smaller = worse for prisoner)

### Effects:
- Escape Chance: -0.5 at quality 100 (harder to escape)
- Mood Penalty: -10 at quality 100 (prisoners hate it)

### Can Assign Owner: ✅ Yes (assign prisoner)

---

## 🏥 HOSPITAL

**Purpose:** Medical treatment facility

### Requirements:
- **Min Size:** 16 tiles
- **Required Furniture:** 3x crash_bed (minimum)
- **Must Be Enclosed:** Yes
- **Must Have Roof:** Yes

### Quality Bonuses:
- Medicine Cabinet: +15
- Clean Floor: +10
- Size: +2 per tile over minimum

### Effects:
- Healing Rate: 1.0 + (quality × 0.005) = **1.0 to 1.5x**
- Infection Resist: 1.0 + (quality × 0.003) = **1.0 to 1.3x**

### Can Assign Owner: ❌ No (shared medical space)

---

## 🎭 SOCIAL VENUE

**Purpose:** Entertainment and social space (dynamic naming based on furniture)

**Special:** This room type has **dynamic tier naming** based on furniture composition:
- Basic setup → "Social Venue"
- Bar-focused → "Bar" / "Dive Bar" / "Lounge"
- Music-focused → "Music Hall" / "Concert Venue"
- Mixed → "Club" / "Entertainment District"

### Requirements:
- **Min Size:** 10 tiles
- **Must Be Enclosed:** Yes
- **Must Have Roof:** Yes
- **No specific furniture required** (evolves with what you add)

### Quality Bonuses (by furniture category):
- **Bar Furniture:** +15 per item
  - bar_stool, scrap_bar_counter, finished_bar, gutter_still, finished_gutter_still
- **Music Equipment:** +20 per item
  - scrap_guitar_placed, drum_kit_placed, synth_placed, harmonica_placed, amp_placed, stage, finished_stage
- **Seating:** +5 per item
  - comfort_chair, bar_stool, crash_bed (lounge)
- **Tables:** +5 per item
  - dining_table, workshop_table, gutter_slab
- **Luxury:** +30 per item (future: pool, chandelier, fountain)
- **Size:** +2 per tile over minimum

### Effects:
- Recreation Gain: 1.0 + (quality × 0.004) = **1.0 to 1.4x**
- Mood Bonus: quality × 0.08 = **0 to +8**
- Social Interaction: 1.0 + (quality × 0.002) = **1.0 to 1.2x**

### Can Assign Owner: ❌ No (public space)

---

## 🍽️ DINING HALL

**Purpose:** Communal eating area

### Requirements:
- **Min Size:** 12 tiles
- **Required Furniture:** 2x table (minimum)
- **Must Be Enclosed:** Yes
- **Must Have Roof:** Yes

### Quality Bonuses:
- Chair: +2 per item
- Table: +5 per item
- Decoration: +8 per item
- Size: +1 per tile over minimum

### Effects:
- Meal Mood: 1.0 + (quality × 0.002) = **1.0 to 1.2x** (better meals = better mood)
- Social Interaction: 1.0 + (quality × 0.001) = **1.0 to 1.1x**

### Can Assign Owner: ❌ No (communal space)

---

## 🎨 FUTURE ROOM TYPES (Not Yet Implemented)

### Planned for Farming/Animal Systems:
- **Greenhouse** - Indoor farming with climate control
- **Animal Pen** - Livestock housing and breeding
- **Slaughterhouse** - Animal processing facility
- **Smokehouse** - Food preservation
- **Hydroponics Bay** - Advanced vertical farming

### Planned for Industrial:
- **Power Plant** - Generator room with efficiency bonuses
- **Storage Warehouse** - Mass storage with organization bonuses
- **Laboratory** - Research and experimentation
- **Armory** - Weapon/armor storage and maintenance

### Planned for Luxury/Late Game:
- **Throne Room** - Leadership and diplomacy
- **Library** - Knowledge and skill training
- **Spa/Bath House** - Luxury recreation
- **Observatory** - Echo research and astronomy

---

## 📋 SPRITE REQUIREMENTS FOR ROOMS

### Core Furniture (Already Implemented):
- ✅ crash_bed.png + crash_bed_top.png
- ✅ finished_stove.png
- ✅ finished_gutter_forge.png (3x3 multi-tile)
- ✅ finished_barracks.png
- ✅ bar_stool.png
- ✅ comfort_chair.png
- ✅ dining_table.png

### Furniture Needed for Full Room Support:
- ❌ cabinet.png (bedroom quality)
- ❌ desk.png (bedroom quality)
- ❌ statue.png (bedroom quality)
- ❌ wall_lamp.png (bedroom quality)
- ❌ fridge.png (kitchen quality)
- ❌ counter.png (kitchen quality)
- ❌ workbench.png (workshop quality)
- ❌ storage_locker.png (workshop quality)
- ❌ weapon_rack.png (barracks quality)
- ❌ medicine_cabinet.png (hospital quality)
- ❌ scrap_bar_counter.png (social venue)
- ❌ finished_bar.png (social venue)

### Multi-Tile Workstations (Already Defined):
- ✅ finished_gutter_still.png (3x3 - brewing)
- ✅ finished_skinshop_loom.png (1x1)
- ✅ finished_cortex_spindle.png (1x1)
- ✅ finished_salvagers_bench.png (1x1)

---

## 🔧 TECHNICAL NOTES

### Room Creation Flow:
1. Player clicks "Create Room" button in UI
2. Selects room type from menu
3. Drags rectangle on grid to define area
4. Game validates requirements (size, furniture, enclosure, roof)
5. If valid: Room created with quality score and effects applied
6. If invalid: Error messages shown to player

### Quality Score System:
- Base: 0 points
- Add bonuses from furniture (per item type)
- Add size bonus (tiles over minimum × size_bonus)
- Cap at 100 points
- Effects scale with quality (see each room type)

### Enclosure Detection:
- Checks all tiles in room
- For each tile, checks 4 cardinal neighbors
- If neighbor is outside room, must be wall/door/window
- Valid barriers: finished_wall, finished_wall_autotile, finished_wall_advanced, door, finished_window, window_tile

### Roof Detection:
- Checks Z+1 level above each room tile
- All tiles must have "roof" tile above them
- Roofs are placed manually by player or auto-generated when room forms

---

## 🎯 PRIORITY FOR SPRITE CREATION

### High Priority (Core Gameplay):
1. **Bedroom furniture** - cabinet, desk, lamp (sleep quality affects everything)
2. **Kitchen furniture** - fridge, counter (food is critical)
3. **Workshop storage** - storage_locker, workbench (crafting efficiency)

### Medium Priority (Quality of Life):
4. **Barracks furniture** - weapon_rack (military gameplay)
5. **Hospital furniture** - medicine_cabinet (healing system)
6. **Social venue furniture** - bar_counter, finished_bar (morale system)

### Low Priority (Polish):
7. **Decorations** - statue, paintings, plants
8. **Luxury items** - chandelier, fountain, pool (late game)

---

**Last Updated:** Dec 30, 2025
**System Status:** Manual room designation implemented, auto-detection disabled
**Next Steps:** Create sprites for quality furniture, test room effects, add farming/animal room types
