# Colonist UI Systems Audit

## Current State (Jan 1, 2026)

### PYGAME Systems (OLD - TO BE REMOVED)
1. **`ui.py`** - Popup panels for clicking on game objects
   - `ColonistManagementPanel` - Opens when clicking colonist
   - Uses pygame rendering
   - **STATUS: LEGACY - Should be replaced**

2. **`ui_layout.py`** - Structural UI (sidebars, top bar)
   - `_draw_colonists_content()` - Draws colonist list
   - Uses pygame rendering
   - Has colonist click handling
   - **STATUS: LEGACY - Being replaced by arcade**

3. **`ui_workstation_new.py`** - Workstation panel
   - Uses pygame rendering
   - **STATUS: LEGACY - Already has arcade replacement**

### ARCADE Systems (NEW - CURRENT)
1. **`ui_arcade_panels.py`** - Main UI panels
   - `LeftSidebar` - 5 tabs (COLONISTS, ANIMALS, JOBS, ITEMS, ROOMS)
     - Shows colonist list with name, job, hunger, tiredness
     - Click to locate colonist
     - Scroll support
   - `ColonistDetailPanel` - Right panel with 9 tabs
     - Status, Bio, Body, Links, Stats, Drives, Mind, Chat, Help
     - Full colonist information display
   - **STATUS: ACTIVE - Main colonist UI**

2. **`ui_arcade.py`** - UI constants and basic panels
   - `ColonistListPanel` - Simple colonist list (may be redundant)
   - **STATUS: ACTIVE - But may have redundancy**

3. **`ui_arcade_tile_info.py`** - Tile hover info
   - Shows item metadata when hovering
   - **STATUS: ACTIVE - Working well**

4. **`ui_arcade_visitor.py`** - Visitor/wanderer panel
   - Shows colonist stats when accepting visitors
   - **STATUS: ACTIVE - Working**

5. **`ui_arcade_bed.py`** - Bed assignment panel
   - Shows colonist list for bed assignment
   - **STATUS: ACTIVE - Working**

## Issues Identified

### 1. **Pygame/Arcade Duplication**
- `ui.py` and `ui_layout.py` still use pygame
- `ui_arcade_panels.py` has arcade replacements
- Need to verify which system is actually being used in `main_arcade.py`

### 2. **Confirmed Redundancy**
- `ColonistListPanel` in `ui_arcade.py` exists but is NOT used
- `LeftSidebar` in `ui_arcade_panels.py` is the active system
- Can remove `ColonistListPanel` safely

### 3. **Missing Features**
- Colonist equipment display (from UI wishlist)
- Click colonist in list to move camera (from UI wishlist)

## Consolidation Plan

### Phase 1: Audit Current Usage
- [ ] Check `main_arcade.py` to see which UI systems are active
- [ ] Identify which pygame files are still being imported
- [ ] Document what each system does

### Phase 2: Remove Pygame Code
- [ ] Remove or deprecate `ui.py` pygame panels
- [ ] Remove or deprecate `ui_layout.py` pygame rendering
- [ ] Remove `ui_workstation_new.py` (already replaced)

### Phase 3: Consolidate Arcade Systems
- [ ] Merge redundant colonist list panels
- [ ] Ensure single source of truth for colonist display
- [ ] Add missing features (equipment, camera movement)

### Phase 4: Enhance Colonist UI
- [ ] Add equipment display to colonist list
- [ ] Add click-to-locate functionality
- [ ] Improve colonist detail panel layout
- [ ] Add cyberpunk styling improvements

## Findings from main_arcade.py

### ✅ ACTIVE SYSTEMS (Currently Used)
- `ui_arcade_panels.py` - LeftSidebar + ColonistDetailPanel
- `ui_arcade_workstation.py` - Workstation panel
- `ui_arcade_bed.py` - Bed assignment
- `ui_arcade_visitor.py` - Visitor/wanderer panel
- `ui_arcade_trader.py` - Trader panel
- `ui_arcade_tile_info.py` - Tile hover info
- `ui_arcade_notifications.py` - Notification system
- `ui_arcade.py` - ArcadeUI (base system)

### ❌ INACTIVE SYSTEMS (Can Be Removed)
- `ui.py` - NOT imported in main_arcade.py
- `ui_layout.py` - NOT imported in main_arcade.py
- `ui_workstation_new.py` - Replaced by ui_arcade_workstation.py
- `ui_drawing.py` - Unknown status

### ⚠️ EXCEPTION
- `ui.py` - `get_stockpile_filter_panel()` is still used (line 1363)
  - This is the ONLY pygame UI still active
  - Should be replaced with arcade version

## Colonist UI Current State

### Left Sidebar (ui_arcade_panels.py - LeftSidebar)
**Shows:**
- Colonist name
- Current job
- Hunger bar
- Tiredness bar
- Click to locate colonist on map

**Missing:**
- Equipment display
- Click to move camera (callback exists but may not work)
- Health/mood indicators
- Status icons (sleeping, fighting, etc.)

### Right Panel (ui_arcade_panels.py - ColonistDetailPanel)
**9 Tabs:**
1. Status - Health, hunger, tiredness, mood
2. Bio - Name, age, background
3. Body - Body parts, injuries
4. Links - Relationships
5. Stats - Skills, traits
6. Drives - Needs, desires
7. Mind - Thoughts, memories
8. Chat - Conversation history
9. Help - Tutorial info

**Issues:**
- Very detailed but may be overwhelming
- Some tabs may be empty/unused
- Could benefit from better visual hierarchy

## Consolidation Plan

### Phase 1: Safe Removal ✅
- [x] Confirmed pygame UI not used (except stockpile filter)
- [ ] Remove `ui_layout.py` (not imported)
- [ ] Remove `ui_workstation_new.py` (replaced)
- [ ] Archive `ui.py` or mark as deprecated

### Phase 2: Replace Stockpile Filter
- [ ] Create `ui_arcade_stockpile.py` to replace pygame stockpile filter
- [ ] Remove last pygame dependency

### Phase 3: Enhance Colonist List
- [ ] Add equipment icons to colonist list
- [ ] Add health/mood indicators
- [ ] Add status icons (sleeping, fighting, etc.)
- [ ] Improve click-to-locate (ensure camera moves)
- [ ] Add right-click context menu?

### Phase 4: Improve Detail Panel
- [ ] Consolidate tabs (9 tabs may be too many)
- [ ] Add visual hierarchy (important info first)
- [ ] Add equipment display with icons
- [ ] Improve cyberpunk styling

## Recommended First Steps

1. **Remove dead code** - Delete unused pygame files
2. **Fix colonist list** - Add equipment display
3. **Test camera movement** - Ensure click-to-locate works
4. **Improve visual clarity** - Better status indicators
