# Fractured City - Implementation Plan

## Current Architecture Status

### ✅ Already Implemented
- **Carry System**: Colonists have `carrying` dict with `type`/`amount`, visible in UI
- **Item System**: `items.py` with `ItemDef` registry, 6 equipment slots, world items
- **Crafting Stations**: Gutter Forge, Skinshop Loom, Cortex Spindle (multi-recipe)
- **Equipment UI**: Slots display equipped items with icon colors
- **Stockpile Filters**: Including "equipment" type for crafted items
- **Haul System**: Auto-haul for both resources and equipment items

### 🔧 Needs Verification/Polish
- [ ] Crafting completion spawns items correctly
- [ ] Equipment haul jobs work end-to-end
- [ ] Recipe cycling UI feedback

---

## Milestone Mapping to Current State

| Milestone | Status | Notes |
|-----------|--------|-------|
| 1. Carry System | ✅ DONE | `colonist.carrying`, UI display works |
| 2. Item System | ✅ DONE | `items.py`, equipment slots, world items |
| 3. Crafting Stations | ✅ DONE | 3 stations, multi-recipe, job queue |
| 4. Equipment Effects | 🔲 TODO | Stats defined but not applied |
| 5. Hazards System | 🔲 TODO | No hazard tiles yet |
| 6. Personality/Traits | 🔲 TODO | Affinities exist, traits don't |
| 7. Colony Pressures | 🔲 TODO | No pressure metrics |
| 8. AI Task Selection | 🔲 TODO | Flat job selection currently |
| 9. District World Gen | 🔲 TODO | Dense city gen exists, no districts |
| 10. Lighting/Z-Trans | 🔲 TODO | Basic Z-levels, no lighting |

---

## Implementation Order (Recommended)

### Phase A: Verify & Polish Existing (Current Session)
```
[ ] A1. Test crafting end-to-end (forge → item → haul → stockpile)
[ ] A2. Fix any remaining multi-recipe bugs
[ ] A3. Add visual feedback for recipe selection on stations
```

### Phase B: Equipment Effects (Milestone 4)
```
[ ] B1. Add stat calculation in colonist update loop
[ ] B2. Speed bonuses from tools (hands slot)
[ ] B3. Comfort/protection from clothing (body/feet)
[ ] B4. Affinity modifiers from implants/charms
[ ] B5. UI display of active bonuses
```

### Phase C: Hazards System (Milestone 5)
```
[ ] C1. Add hazard flags to tile system (bio, shards, echo)
[ ] C2. Hazard effects on colonist stress/comfort
[ ] C3. Equipment mitigation (boots vs shards, etc.)
[ ] C4. Hazard tile rendering (tints/overlays)
[ ] C5. World gen: sprinkle hazards in appropriate areas
```

### Phase D: Traits & Personality (Milestone 6)
```
[ ] D1. Trait data definitions (Rustborn, Echo-Touched, etc.)
[ ] D2. Trait → affinity modifiers
[ ] D3. Trait → job preference modifiers
[ ] D4. Trait UI in colonist panel
[ ] D5. Spawn colonists with random traits
```

### Phase E: Colony Pressures (Milestone 7)
```
[ ] E1. Calculate food pressure (meals per colonist)
[ ] E2. Calculate shelter pressure (rooms vs colonists)
[ ] E3. Calculate security pressure (walls/hazards)
[ ] E4. Pressure display in UI
[ ] E5. Periodic update loop
```

### Phase F: Smart Job Selection (Milestone 8)
```
[ ] F1. Job scoring system (base priority)
[ ] F2. Trait/affinity modifiers to job scores
[ ] F3. Pressure multipliers (high food pressure → cooking)
[ ] F4. Fatigue/variety factor (avoid same job forever)
[ ] F5. Fallback logic (critical jobs always get done)
```

### Phase G: District World Gen (Milestone 9)
```
[ ] G1. District type definitions (residential, industrial, etc.)
[ ] G2. District placement algorithm
[ ] G3. Resource distribution by district
[ ] G4. Hazard distribution by district
[ ] G5. Visual distinction (tile palettes per district)
```

### Phase H: Lighting & Z-Transparency (Milestone 10)
```
[ ] H1. Light source system (colonists, buildings)
[ ] H2. Tile darkness based on light distance
[ ] H3. Room brightness (enclosed + powered)
[ ] H4. Z-level transparency (dim lower levels)
[ ] H5. Performance optimization
```

---

## Dependencies & Risks

### Critical Path
```
Crafting (done) → Equipment Effects → Hazards → Traits → Pressures → Smart AI
```

### Parallel Work Possible
- District World Gen (G) can happen alongside D-F
- Lighting (H) can happen anytime after C

### Risk Areas
1. **Performance**: Lighting + hazard checks every frame could lag
2. **Balance**: Equipment effects need tuning passes
3. **Complexity**: Smart AI job selection could get messy

---

## Quick Reference: Key Files

| System | Primary File(s) |
|--------|-----------------|
| Items/Equipment | `items.py` |
| Crafting | `buildings.py`, `colonist.py` |
| Jobs | `jobs.py`, `colonist.py` |
| Zones/Stockpiles | `zones.py` |
| UI | `ui.py` |
| World Gen | `worldgen.py` (if exists) or `main.py` |
| Grid/Rendering | `grid.py` |
| Resources | `resources.py` |

---

## Session Log

### 2024-12-05
- Fixed multi-recipe support in `workstation_has_inputs()` and `consume_workstation_inputs()`
- Added world item rendering (diamond icons)
- Added equipment storage in zones
- Added equipment haul job processing
- Added equipment rendering in stockpile tiles
- Added equipment/items to tile hover tooltip (debug mode)
- Added recipe indicator on workstation tiles (2-letter code in corner)
- Added debug keys: F10 (spawn test item), F11 (show workstations)
- Verified: crafting produces items, haul jobs work, items stored in stockpiles

### Milestone 3 Status: ✅ COMPLETE
- [x] Build stations from menu
- [x] Colonists craft items
- [x] Items spawn and render
- [x] Items hauled to stockpiles
- [x] Recipe cycling via click
- [x] Visual recipe indicator on stations

### Milestone 4 Status: ✅ COMPLETE (Equipment Effects)
- [x] Equipment stats calculated from ItemDef (comfort, speed_bonus, hazard_resist, work_bonus)
- [x] Speed bonus affects movement (lower move_cooldown = faster)
- [x] Work bonus affects job progress (faster construction, gathering, crafting)
- [x] Comfort bonus affects mood calculation (added to comfort before mood state)
- [x] Hazard resist ready for environmental damage (not yet implemented)
- [x] F7 debug key shows equipment stats

### World Improvements (Bonus)
- [x] Streets harvestable → yields mineral, converts to scorched earth
- [x] Sidewalks harvestable → yields mineral, converts to scorched earth
- [x] Mineral nodes no longer respawn (finite resource)
- [x] Empty tiles render with earth tones instead of black
- [x] New tile types: dirt, grass, rock, scorched

### Procedural Item System (Milestone 4b) ✅ COMPLETE
- [x] `item_generator.py` - procedural item generation from components
- [x] Prefix + Base + Suffix naming (e.g., "Wind's Scarf of the Fallen Squirrel")
- [x] Conditional stat triggers (near_fire, in_cold, while_working, etc.)
- [x] Stats tab in colonist panel (D&D-style wall of text)
- [x] F7 debug key equips procedural items
- [x] Console logging for work speed verification

### Crafting Loop (Milestone 4c) ✅ COMPLETE
- [x] Crafting checks stockpile space before producing items
- [x] Crafted items hauled to stockpile automatically
- [x] Workstation UI panel - click workstation to see recipes
- [x] Recipe selection with costs and effects displayed
- [x] Auto-equip system - colonists claim items matching preferences
- [x] Preference-to-stat mapping (outdoor lovers want hazard resist, etc.)
- [x] "equip" job type for colonists to pick up and equip items

### Future Verification Checklist
- [ ] Verify walk speed equipment bonus actually changes movement
- [ ] Verify work speed bonus actually changes job completion time
- [ ] Verify comfort bonus affects mood calculation
- [ ] Verify conditional triggers fire correctly (near_fire, in_cold, etc.)
- [ ] Add unit tests for stat calculations

### Next Session
- Milestone 5: Colonist Needs (shelter, rest, social)
