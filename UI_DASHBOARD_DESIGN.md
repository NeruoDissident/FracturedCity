# UI Mega-Dashboard Design & Data Catalog

## 1. Design Goals
- **Information Density:** "Dwarf Fortress" style - show everything, filterable and sortable.
- **Cyberpunk Aesthetic:** Use existing neon palette (Cyan/Magenta/Pink on Dark).
- **Centralized Management:** One screen (or modal) to manage the entire colony.
- **Expandability:** Tab-based architecture to easily add new systems (Factions, Research, etc.).

## 2. Proposed Architecture
**The "Net-Log" (Network Logistics Interface)**
A full-screen (or near full-screen) modal dashboard triggered by a hotkey (e.g., `Tab` or `F1`).

- **Header:** Global status (Time, Wealth, Population, Alert Level).
- **Navigation Rail (Left or Top):** Icons + Text for major categories.
- **Main Content Area:** Dynamic content based on selected category.
- **Detail Panel (Right, Collapsible):** Context-sensitive details for selected item in Main Area.

## 3. Data Catalog (Available Information)

### A. Colonists (`colonist.py`)
| Field | Data Type | Display Strategy |
|-------|-----------|------------------|
| **Identity** | `name`, `age`, `role` | Name column, color-coded by role |
| **Status** | `state` (idle/working), `current_job` | Status text, Job icon |
| **Vitals** | `health`, `hunger`, `tiredness`, `stress` | Mini-bars or colored text (Green/Yellow/Red) |
| **Mood** | `mood_state`, `comfort`, `thoughts` | Mood word + tooltip with breakdown |
| **Stats** | `melee_skill`, `work_speed` | Numeric values in "Skills" view |
| **Equipment** | `equipment` (dict of slots) | Paper-doll icons or list |
| **Personality** | `traits`, `bio`, `preferences` | Detail panel text |
| **Social** | `relationships`, `faction` | Relationship web or list |

### B. Inventory & Items (`items.py`, `zones.py`)
| Field | Data Type | Display Strategy |
|-------|-----------|------------------|
| **Item Def** | `id`, `name`, `type`, `tags` | Item Name, Icon |
| **Count** | Aggregate from stockpiles + map | Total Count column |
| **Location** | Stockpile, Map, Equipped | "Where is it?" breakdown |
| **Stats** | `quality`, `condition` (future), `material` | Quality color coding |
| **Details** | `description`, `stats` (armor/damage) | Detail panel stats block |

### C. Production & Workstations (`buildings.py`)
| Field | Data Type | Display Strategy |
|-------|-----------|------------------|
| **Station** | `type`, `location` | Station Name, Z-Level |
| **Status** | `reserved`, `working`, `progress` | Progress Bar, "In Use by [Name]" |
| **Recipe** | `active_recipe`, `queue` | Current Output Icon |
| **Input** | `input_items` | "Waiting for Materials" warning |

### D. Jobs (`jobs.py`)
| Field | Data Type | Display Strategy |
|-------|-----------|------------------|
| **Job** | `type`, `category`, `subtype` | Job Name (e.g., "Build Wall") |
| **Priority** | `pressure`, `priority_score` | Priority Number (Editable?) |
| **Assignee** | `assigned` (Colonist Ref) | Colonist Face/Name or "Unassigned" |
| **Location** | `x, y, z` | "Go to" button |
| **Progress** | `progress` / `required` | Progress % |

### E. Animals (`animals.py`)
| Field | Data Type | Display Strategy |
|-------|-----------|------------------|
| **Identity** | `species`, `name`, `variant` | Species Icon, Custom Name |
| **State** | `state` (wild/tame), `owner` | "Wild", "Tame", or Owner Name |
| **Stats** | `health`, `hunger`, `age` | Vitals bars |
| **Products** | `meat_yield`, `materials` | "Butcher Yield" preview |

### F. Rooms (`rooms.py`)
| Field | Data Type | Display Strategy |
|-------|-----------|------------------|
| **Room** | `id`, `room_type` | Room Name (Auto-generated or Custom) |
| **Quality** | `score` (future), `contents` | Quality Rating, List of Furniture |
| **Owners** | `owners` (future) | Assigned Colonists |

## 4. Proposed Tabs & Layouts

### Tab 1: **OVERVIEW** (Dashboard)
- **Population Pyramid:** Age/Role distribution.
- **Resource Tickers:** Rolling graph of key resources (Food, Power, Scrap).
- **Alerts:** Recent critical notifications.
- **Map Preview:** Mini-map showing colonist positions.

### Tab 2: **COLONISTS** (The "Roster")
- **View:** Sortable Data Table.
- **Columns:** Name, Role, Current Action, Mood, Health, Hunger, Sleep.
- **Actions:** "Draft" (Combat), "Locate".
- **Detail Panel:** Complete character sheet (Bio, Gear, Health, Thoughts).

### Tab 3: **LOGISTICS** (Items & Stockpiles)
- **View:** Categorized Tree (Resources > Food > Raw / Cooked).
- **Columns:** Total Count, In Stockpile, On Map, Equipped.
- **Actions:** "Forbid", "Mark for Trade".

### Tab 4: **PRODUCTION** (Work)
- **View:** Split View (Workstations | Global Queue).
- **Workstations:** List of all benches, their status, and active crafter.
- **Bills:** (Future) Manager interface to set "Make X" orders.

### Tab 5: **JOBS** (Task Management)
- **View:** List of active jobs.
- **Columns:** Priority, Type, Description, Assigned To, Progress.
- **Actions:** Cancel, Boost Priority.

### Tab 6: **FAUNA** (Animals)
- **View:** Two lists (Wild / Tame).
- **Wild:** List of animals on map (Hunt/Tame buttons).
- **Tame:** List of pets/livestock (Master, Training, Slaughter buttons).

## 5. Visual Specs (Referencing `ui_arcade.py`)
- **Background:** `COLOR_BG_DARKEST` (0, 0, 0, 240) - Semi-transparent overlay.
- **Panels:** `COLOR_BG_PANEL` with `COLOR_BORDER_BRIGHT` outlines.
- **Text:**
  - Headers: `COLOR_NEON_CYAN` (Bahnschrift, Bold).
  - Data: `COLOR_TEXT_BRIGHT` (Cascadia Mono).
  - Labels: `COLOR_TEXT_DIM`.
- **Accents:**
  - Selection: `COLOR_NEON_MAGENTA` glow.
  - Good/Bad: `COLOR_GOOD` / `COLOR_DANGER`.

## 6. Implementation Plan
1.  **Dashboard Framework:** Create `ui_arcade_dashboard.py` to handle the main modal and tab switching.
2.  **Reuse Strategy:** 
    - The **Detail Panel** (Right side) will wrap the existing `ColonistPopup` tabs (`ui_arcade_colonist_popup.py`).
    - We will refactor `ColonistPopup` slightly to allow rendering into a specific screen region (the Detail Panel) instead of just as a centered popup.
3.  **Colonist Tab:** Implement the data table for colonists (Roster View).
4.  **Integration:** Hook up `Tab` key in `main_arcade.py` to toggle dashboard.
