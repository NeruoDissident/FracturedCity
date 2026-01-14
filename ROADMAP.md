# Roadmap - Fractured City

**Timeline:** January 2026 → July 2026 (6 months to Godot port)  
**Goal:** Feature-complete colony sim ready for Godot migration

---

## Phase 1: Core Systems Polish (Jan-Feb 2026)

### Month 1: Survival Loop
**Goal:** Complete food production cycle

- [ ] **Rooftop Farming**
  - Dirt plots (1x1)
  - Planter boxes (2x1)
  - Hydroponic beds (3x1, requires power)
  - Plant → Water → Fertilize → Harvest jobs
  - Crop growth stages (visual progression)

- [ ] **Animal Husbandry**
  - Taming system (feed animals to build trust)
  - Animal pens (room type)
  - Breeding mechanics
  - Egg production (pigeons)
  - Slaughter jobs

- [ ] **Food Chain Complete**
  - Hunt → Butcher → Cook → Eat (DONE)
  - Farm → Harvest → Cook → Eat (NEW)
  - Tame → Breed → Slaughter → Butcher → Cook → Eat (NEW)

### Month 2: UI Polish
**Goal:** Clean, cyberpunk-themed UI

- [ ] **Visual Overhaul**
  - Neon pink/cyan color scheme
  - Digital number fonts
  - Clean, crisp panel borders
  - Animated UI elements

- [ ] **UX Improvements**
  - Colonists clickable in list to snap camera
  - Equipment shown in colonist list
  - Job count panel (total/filled) at bottom of sidebar
  - Drag-place for bridges
  - Consolidate debug info into sidebars

---

## Phase 2: Threats & Pressure (Mar-Apr 2026)

### Month 3: Raiders
**Goal:** External threat system

- [ ] **Raider Factions**
  - 3-5 raider groups with unique behaviors
  - Spawn at map edges
  - Pathfind to colony
  - Steal resources, attack colonists
  - Retreat when outnumbered

- [ ] **Defense**
  - Walls provide cover
  - Colonist combat improvements
  - Weapons (melee, ranged)
  - Guard duty job type
  - Alert system

### Month 4: The Echo
**Goal:** Reality distortion hazard

- [ ] **Echo Mechanics**
  - Echo intensity per tile (0.0-1.0)
  - Visual distortion effects
  - Colonist sanity system
  - Echo-sensitive colonists (trait)
  - Echo storms (periodic events)

- [ ] **Echo Stabilization**
  - Echo dampener workstation
  - Stabilizer structures
  - Echo-resistant materials
  - Safe zones vs corrupted zones

---

## Phase 3: Expansion & Automation (May-Jun 2026)

### Month 5: Vertical Expansion
**Goal:** Multi-level colony management

- [ ] **Z-Level Systems**
  - Fire escapes (vertical access)
  - Ladders (internal access)
  - Rooftop buildings
  - Ground-level ruins
  - Per-level resource distribution

- [ ] **District System**
  - Multiple building capture
  - District designation
  - Resource sharing between buildings
  - Travel jobs between districts

### Month 6: Automation & Polish
**Goal:** Late-game systems + final polish

- [ ] **Automation**
  - Automated hauling (conveyor belts, drones)
  - Auto-crafting queues
  - Supply chain optimization
  - Power grid management

- [ ] **Final Polish**
  - Performance optimization
  - Bug fixes
  - Balance pass (resources, recipes, combat)
  - Tutorial system
  - Save/load improvements

---

## Phase 4: Godot Migration Prep (July 2026)

### Pre-Migration Checklist
- [ ] All systems documented
- [ ] Code architecture clean and modular
- [ ] Asset pipeline established
- [ ] Godot project structure planned
- [ ] Migration guide written

### Migration Strategy
1. **Core Systems First** - Grid, colonists, jobs (1 week)
2. **Rendering** - Sprite system, camera (1 week)
3. **UI** - Rebuild panels in Godot (2 weeks)
4. **Polish** - Performance, bugs (1 week)

**Target:** Godot version feature-parity by end of July 2026

---

## Content Roadmap

### Workstations (Expand Recipes)
- [ ] Salvager's Bench - 10+ recipes
- [ ] Tinker Station - Advanced tech
- [ ] Spark Bench - Electronics
- [ ] Gutter Forge - Weapons, armor
- [ ] Gutter Still - Alcohol, chemicals
- [ ] Skinshop Loom - Clothing, bags
- [ ] Cortex Spindle - Implants, charms
- [ ] Bio-Matter Station - Butchering, processing

### New Workstations
- [ ] Medical Bay - Surgery, medicine
- [ ] Research Station - Tech tree
- [ ] Hydroponics Lab - Advanced farming
- [ ] Recycler - Material conversion
- [ ] Armory - Weapon storage, maintenance

### Equipment Expansion
- [ ] Weapons (10+ types)
- [ ] Armor (light, medium, heavy)
- [ ] Tools (specialized work tools)
- [ ] Cybernetics (advanced implants)
- [ ] Clothing (fashion, utility)

### Animals
- [ ] More urban critters (squirrels, crows, dogs)
- [ ] Mutant variants (Echo-touched)
- [ ] Aggressive animals (attack colonists)
- [ ] Exotic animals (rare, valuable)

---

## System Priorities

### High Priority (Must-Have)
1. Farming system
2. Animal husbandry
3. Raiders
4. Echo system
5. UI polish

### Medium Priority (Should-Have)
1. Vertical expansion
2. Automation
3. Research tree
4. Temperature system
5. Weather

### Low Priority (Nice-to-Have)
1. Factions (traders, allies)
2. Events (random occurrences)
3. Seasons
4. Procedural history generation
5. Multiplayer (distant future)

---

## Performance Targets

### Current (Jan 2026)
- 60 FPS at 1920x1080
- 20 colonists, 2000+ sprites
- ~200MB memory

### Target (July 2026)
- 60 FPS at 1920x1080
- 50 colonists, 5000+ sprites
- ~300MB memory
- No frame drops during combat/events

---

## Milestones

### ✅ Milestone 1: Arcade Migration (Dec 2025)
- Pygame removed
- Arcade rendering stable
- 60 FPS achieved

### 🎯 Milestone 2: Survival Complete (Feb 2026)
- Farming system
- Animal husbandry
- Food chain complete

### 🎯 Milestone 3: Threats Active (Apr 2026)
- Raiders functional
- Echo system implemented
- Combat balanced

### 🎯 Milestone 4: Expansion Ready (Jun 2026)
- Vertical expansion
- Automation systems
- Late-game content

### 🎯 Milestone 5: Godot Ready (Jul 2026)
- All systems documented
- Codebase clean
- Migration plan complete

---

## Risk Mitigation

### Technical Risks
- **Performance degradation** - Monitor FPS, optimize early
- **Scope creep** - Stick to roadmap, defer nice-to-haves
- **Godot migration complexity** - Document everything, plan carefully

### Design Risks
- **Balance issues** - Playtest frequently, iterate
- **Feature bloat** - Focus on core loop, cut ruthlessly
- **UI complexity** - Keep it simple, test with users

---

## Success Criteria

By July 2026, Fractured City should:
- ✅ Run at 60 FPS with 50 colonists
- ✅ Have complete survival loop (food, shelter, defense)
- ✅ Feature meaningful threats (raiders, Echo)
- ✅ Support vertical expansion (Z-levels, districts)
- ✅ Have polished, cyberpunk UI
- ✅ Be ready for Godot migration

---

## Post-Godot Plans (Aug 2026+)

### Steam Early Access
- Marketing materials
- Trailer
- Store page
- Community building

### Content Updates
- New workstations
- More animals
- Additional threats
- Expanded Echo system

### Long-Term Vision
- Procedural faction history
- District-scale conflicts
- PMC threats
- Full city simulation
- Emergent storytelling (DF-style)
