# Session Notes - December 18, 2025

## Session Overview
Fixed critical bugs (room detection, workstation UI), implemented audio system with music support, preparing for recreation venues expansion.

---

## Bug Fixes Completed

### 1. Old Room Detection System - CRITICAL FIX
**Problem:** Old auto-room detection system causing infinite unstuck loops and console spam
**Symptoms:**
- Console flooded with `[Room Debug]`, `[Room] Processing`, `[Unstuck]`, `[Recovery]` messages
- Colonists teleporting when standing on "dirty tiles"
- Performance degradation

**Root Cause:** `rooms.py` had old global room detection system running every tick via `process_dirty_rooms()`, scanning tiles and triggering unstuck logic

**Fix:** `rooms.py` line 76-84
```python
def process_dirty_rooms(grid) -> None:
    """DISABLED: Old auto-room detection system.
    
    Manual room system (room_system.py) is now used instead.
    This function is kept as a no-op for compatibility.
    """
    global _DIRTY_TILES
    _DIRTY_TILES.clear()  # Clear any accumulated dirty tiles
    return
```

**Current Room System:** Manual room creation via `room_system.py` - no automatic detection

---

### 2. Workstation UI Buttons Not Working - CRITICAL FIX
**Problem:** +/- buttons on workstation UI randomly not working (salvager's bench only + worked, gutter forge neither worked)

**Root Cause:** Click detection order issue - recipe selection rects (40px tall, full panel width) were checked BEFORE button rects, blocking button clicks

**Investigation Process:**
1. Added debug prints to track clicks
2. Discovered clicks were reaching handler but not buttons
3. Found recipe rects overlapping button positions
4. Recipe list length varied by workstation (4 recipes vs 9 recipes = different overlap amounts)

**Fix:** `ui_workstation_new.py` line 164-204
```python
def _handle_recipe_select_click(self, mouse_pos):
    # Check buttons FIRST (before recipe rects)
    if self.selecting_recipe:
        # Check all quantity buttons
        if "target_minus" in self.quantity_button_rects:
            if self.quantity_button_rects["target_minus"].collidepoint(mouse_pos):
                self.target_value = max(1, self.target_value - 1)
                return True
        # ... other buttons
    
    # THEN check recipe selection (after buttons)
    for i, rect in enumerate(self.recipe_rects):
        if rect.collidepoint(mouse_pos):
            self.selecting_recipe = self.recipes[i]
            return True
```

**Key Insight:** Order matters! Check smaller, higher-priority UI elements before larger background elements.

---

### 3. Workstation Panel Position Issue
**Problem:** Panel spawning at click location caused random button behavior (worked at some screen positions, not others)

**Root Cause:** Panel position changed based on where user clicked workstation. At x=1550, panel was off-screen. Dynamic positioning caused inconsistent button rect calculations.

**Fix:** `ui_workstation_new.py` line 87-90
```python
# Position panel at static location (center of screen, doesn't block sidebars)
self.panel_rect.x = 400  # Center-left area
self.panel_rect.y = 200  # Below top UI bar
```

**Lesson Learned:** User explicitly stated: "everything else in the UI has a static window locations" - follow existing patterns!

---

## New Features Implemented

### Audio System - COMPLETE ✅

**Files Created:**
1. `audio.py` - Audio manager with music/SFX support
2. `procedural_sfx.py` - Numpy-based sound generator (fallback for missing audio files)
3. `assets/AUDIO_README.md` - User guide for adding music/sounds

**Integration:** `main.py` lines 735, 743, 1070-1072
```python
from audio import init_audio, get_audio_manager

# At startup
init_audio()

# In game loop
audio_manager = get_audio_manager()
audio_manager.update()
```

**Music System:**
- Loads all tracks from `assets/music/` (MP3, OGG, WAV)
- Shuffles and auto-plays on startup
- Auto-transitions between tracks
- Volume control (30% default)
- **STATUS:** Working perfectly! User loves it.

**Sound Effects:**
- Procedural generation using numpy (click, notification, success, error, construction)
- Auto-fallback when no sound files present
- **STATUS:** Generated but disabled - user found beeps too jarring. TODO: Add ambient crafting/machine sounds later.

**Pseudocode - Audio System:**
```
ON GAME START:
    - Initialize pygame.mixer
    - Scan assets/music/ for audio files
    - If found: load and shuffle tracks
    - If not found: create folder, print instructions
    - Scan assets/sfx/ for sound files
    - If not found: generate procedural sounds using numpy
    - Start playing first music track

EVERY FRAME:
    - Check if current track finished
    - If finished: load and play next track in shuffle order
    - Loop forever

ON NOTIFICATION:
    - (Currently disabled)
    - TODO: Play subtle ambient sound instead of beep
```

---

## UI Systems Reference

### Active UI System: `ui_workstation_new.py`
**NOT** `ui.py` (old WorkstationPanel exists but unused)

**Main.py Integration:**
```python
# Line 137-139: Click handling
from ui_workstation_new import get_workstation_order_panel
ws_panel = get_workstation_order_panel()
if ws_panel.handle_click((mx, my)):
    return

# Line 373-375: Opening panel
from ui_workstation_new import get_workstation_order_panel
ws_panel = get_workstation_order_panel()
ws_panel.open(gx, gy, current_z, mx, my)

# Line 1190-1192: Drawing
from ui_workstation_new import get_workstation_order_panel
ws_panel = get_workstation_order_panel()
ws_panel.draw(screen)
```

**Panel Features:**
- Two-state system: "orders" view (active orders list) vs "recipe_select" view (recipe picker)
- Order management: single craft, infinite loop, or target quantity
- Static position at (400, 200) - center-left, doesn't block sidebars
- FIFO order processing

---

## Common Pitfalls & Solutions

### 1. "Which UI system is being used?"
**Problem:** Multiple UI files exist (ui.py, ui_workstation_new.py)
**Solution:** Check main.py imports - search for `get_workstation` to see which is active
**Current:** `ui_workstation_new.py` is active

### 2. "Buttons not working randomly"
**Check:**
- Click detection order (smaller elements before larger)
- Panel position (static vs dynamic)
- Rect creation timing (created during draw, used during click)
- Overlapping UI elements

### 3. "Console spam / performance issues"
**Check:**
- Old room detection system (should be disabled in rooms.py)
- Debug print statements (remove after debugging)
- Infinite loops in pathfinding/job processing

### 4. "Audio not working"
**Check:**
- pygame.mixer initialized? (happens in audio.py __init__)
- Files in correct folder? (assets/music/ for tracks)
- Numpy installed? (required for procedural sounds)
- Volume settings? (music 30%, sfx 50% default)

---

## Current Game State

### Working Systems:
- ✅ Room effects (work speed, healing, mood, sleep quality)
- ✅ Manual room creation (room_system.py)
- ✅ Workstation crafting with order queue
- ✅ Recreation jobs (spawn 6pm-10pm at recreation rooms)
- ✅ Training jobs (spawn 6am-8am at barracks)
- ✅ Bed assignment (injured → hospital, fighters → barracks)
- ✅ Audio system (music playing, SFX disabled)

### Known Issues:
- None currently! All major bugs fixed.

### Next Feature: Recreation Venues Expansion
**Goal:** Add 4 new entertainment buildings (Bar, Punk Rock Music Hall, Casino, Race Track)
**Status:** Ready to implement

---

## Recreation Venues - Implementation Plan

### Pseudocode Structure:
```
FOR EACH VENUE TYPE (bar, music_hall, casino, race_track):
    
    1. ADD TO buildings.py:
        - Building definition with materials, construction time
        - Placement rule (indoors, floor_only, etc.)
        - Mark as recreation venue
    
    2. ADD TO recreation.py:
        - Venue-specific job spawning logic
        - Time windows (6pm-10pm for most, maybe 24/7 for bar)
        - Capacity limits (jobs per venue)
    
    3. ADD SPECIAL MECHANICS:
        - Bar: Social interaction, stress relief, drunkenness, fight chance
        - Music Hall: Performance events, mood boost, band formation
        - Casino: Gambling, wealth transfer, addiction tracking
        - Race Track: Betting system, spectator excitement
    
    4. INTEGRATE WITH EXISTING SYSTEMS:
        - Room effects (mood/stress modifiers)
        - Job system (recreation jobs)
        - Colonist preferences (some like gambling, some don't)
        - Relationship system (social venues build relationships)
```

### Implementation Order:
1. **Bar** (simplest - social hub, stress relief)
2. **Music Hall** (events, performances)
3. **Casino** (gambling mechanics)
4. **Race Track** (betting, spectator system)

---

## File Structure Reference

### Core Systems:
- `main.py` - Game loop, event handling
- `colonist.py` - Colonist behavior, jobs, needs
- `buildings.py` - Building definitions, workstations
- `jobs.py` - Job queue management
- `grid.py` - World grid, tiles, pathfinding

### Room Systems:
- `room_system.py` - Manual room creation (ACTIVE)
- `rooms.py` - Old auto-detection (DISABLED)
- `room_effects.py` - Room bonuses (work speed, healing, etc.)

### Recreation:
- `recreation.py` - Recreation job spawning
- `training.py` - Training job spawning (barracks)
- `beds.py` - Bed assignment logic

### UI:
- `ui_workstation_new.py` - Workstation panel (ACTIVE)
- `ui.py` - Old workstation panel + other UI (WorkstationPanel unused)
- `notifications.py` - Pop-up notifications

### Audio:
- `audio.py` - Audio manager
- `procedural_sfx.py` - Sound generator
- `assets/music/` - Music tracks folder
- `assets/sfx/` - Sound effects folder

---

## Debug Commands Reference

### F-Key Debug Commands:
- **F1** - Toggle debug overlay (grid info, colonist states)
- **F3** - Spawn wanderer (triggers notification sound test)
- **F4** - Toggle free build mode (no material requirements)
- **F7** - Equip procedurally generated items on all colonists
- **F8** - Print construction site status

### Console Commands:
- Look for `[Audio]` messages for music/sound status
- Look for `[Workstation UI]` messages for panel debugging
- Look for `[Room Debug]` messages (should NOT appear - old system disabled)

---

## Git Workflow

### Current Status:
- All changes committed and pushed
- Music tracks added to assets/music/
- Audio system working

### Important Files to Track:
- `audio.py` - New file
- `procedural_sfx.py` - New file
- `assets/AUDIO_README.md` - New file
- `main.py` - Modified (audio integration)
- `rooms.py` - Modified (disabled old system)
- `ui_workstation_new.py` - Modified (button fixes, static position)
- `notifications.py` - Modified (sound disabled)

---

## Next Session Checklist

When starting a new session:

1. **Verify Audio System:**
   - Music playing? Check console for `[Audio] Loaded X music tracks`
   - No beeps? Notification sounds should be disabled

2. **Verify Bug Fixes:**
   - No `[Room Debug]` spam in console
   - Workstation UI buttons work at all screen positions
   - Panel appears at (400, 200) consistently

3. **Ready for Recreation Venues:**
   - Start with Bar implementation
   - Reference existing recreation.py for job spawning pattern
   - Add to buildings.py first, then recreation logic

4. **Common Issues to Watch:**
   - Don't re-enable old room detection
   - Keep workstation panel at static position
   - Check click detection order for new UI elements

---

## Technical Notes

### Pygame Audio:
- `pygame.mixer.music` - For background music (one track at a time)
- `pygame.mixer.Sound` - For sound effects (multiple simultaneous)
- Music runs on separate thread (no performance impact)
- Sample rate: 22050 Hz for procedural sounds

### Numpy Sound Generation:
- Sine waves for tones: `np.sin(2 * np.pi * frequency * time_array)`
- 16-bit PCM format: `(wave * 32767).astype(np.int16)`
- Stereo: `np.column_stack((mono, mono))`
- Fade in/out to prevent clicks

### UI Click Detection:
- Check smaller/higher-priority elements first
- Use `rect.collidepoint(mouse_pos)` for hit testing
- Store rects during draw, check during click
- Clear and rebuild rects every frame

---

## User Preferences

- **No dynamic UI positioning** - Everything should have static screen locations
- **Music is great** - Keep it playing
- **Procedural beeps too jarring** - Skip SFX for now, add ambient sounds later
- **Detailed notes preferred** - Keep documentation comprehensive with pseudocode
- **Recreation venues next** - Bar, Music Hall, Casino, Race Track

---

## End of Session Notes

**Time:** 7:47pm, December 18, 2025
**Status:** All bugs fixed, audio working, ready for recreation expansion
**Music:** Playing and awesome! 🎵
**Next:** Implement Bar as first recreation venue
