# Hunting System Implementation Plan

## ✅ Completed
1. Bio-Matter Salvage Station added to buildings.py
   - 2x2 workstation
   - Recipes: rat_corpse → raw_food + scrap, bird_corpse → raw_food
   - Description: "Cuts up cats and birds and shit"

2. Corpse items added to items.py
   - rat_corpse
   - bird_corpse

3. Animal hunting designation system
   - `marked_for_hunt` flag on animals
   - `hunter_uid` to track who's hunting
   - `mark_for_hunt()`, `unmark_for_hunt()`, `get_huntable_animals()` functions

## 🔄 In Progress
4. Hunt job implementation in colonist.py
   - Add "hunt" job type
   - Colonist behavior: approach animal, attack when in range
   - On kill: create corpse item, remove animal

5. Animal fleeing behavior
   - When hunter approaches, animal enters FLEEING state
   - Runs away from hunter
   - Returns to normal behavior if hunter gives up

6. UI integration
   - Click animal in detail panel → "Hunt" button
   - Click animal sprite → context menu with "Hunt" option
   - Visual indicator on hunted animals (red outline?)

## 📋 TODO
7. Hunt job spawning
   - Check for huntable animals each tick
   - Create hunt job if colonist available
   - Assign hunter_uid to animal

8. Corpse hauling
   - Corpse spawns as world item when animal dies
   - Auto-haul to stockpile (existing system)
   - Butcher at bio-matter salvage station (existing crafting system)

## 🎮 Testing Checklist
- [ ] Build bio-matter salvage station
- [ ] Mark animal for hunt via UI
- [ ] Colonist picks up hunt job
- [ ] Colonist chases animal
- [ ] Animal flees from hunter
- [ ] Colonist kills animal
- [ ] Corpse spawns on ground
- [ ] Corpse hauled to stockpile
- [ ] Butcher job created at station
- [ ] Corpse processed into food + materials

## 🔧 Technical Notes
- Hunt job similar to combat job but target is animal UID
- Use existing combat system (`perform_attack`) for killing
- Corpse creation handled by `kill_animal()` in animals.py
- Fleeing uses existing FLEEING state, just needs hunter tracking
