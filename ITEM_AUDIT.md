# Item Audit - Purpose & Usage

**Goal:** Every item must have a clear purpose. Remove items that don't contribute to gameplay loops.

---

## ✅ ORGANIC ITEMS (Hunting/Butchery Loop)

### Corpses
- **rat_corpse** → Butcher → rat_meat + rat_pelt ✓
- **bird_corpse** → Butcher → bird_meat + feathers ✓

### Meat (Food Loop)
- **rat_meat** → Cook at stove → cooked_meal ✓
- **bird_meat** → Cook at stove → cooked_meal ✓

### Materials (Crafting Loop)
- **rat_pelt** → **NEEDS USE** - Should tan → leather → clothing
- **feathers** → **NEEDS USE** - Should craft → stuffing, fletching, quills

**Status:** Core loop works, but pelts/feathers are dead ends. Need processing recipes.

---

## ✅ EQUIPMENT (Auto-Equip Loop)

### Head Slot
- **hard_hat** → Hazard protection ✓
- **scavenger_hood** → Comfort ✓
- **signal_visor** → Work bonus ✓

### Body Slot
- **work_vest** → Work bonus ✓
- **padded_jacket** → Comfort + hazard ✓
- **scrap_armor** → High hazard, slow speed ✓
- **armor_plate** → Heavy armor ✓

### Hands Slot
- **work_gloves** → Work bonus ✓
- **salvage_tool** → High work bonus ✓
- **signal_gauntlet** → Tech work bonus ✓
- **pipe_weapon** → Melee weapon ✓
- **scrap_blade** → Melee weapon ✓

### Feet Slot
- **work_boots** → Speed bonus ✓
- **runner_shoes** → High speed + comfort ✓

### Implant Slot
- **focus_chip** → Work bonus ✓
- **endurance_mod** → Speed + hazard ✓
- **echo_dampener** → Comfort ✓
- **medical_scanner** → Work bonus (medical) ✓
- **stim_injector** → Speed boost, hazard penalty ✓
- **neural_interface** → High work, low comfort ✓

### Charm Slot
- **lucky_coin** → Comfort ✓
- **memory_locket** → Comfort ✓
- **signal_stone** → Hazard resist ✓
- **data_slate** → Work bonus ✓

**Status:** All equipment has stats and fits auto-equip system. ✓

---

## ✅ FURNITURE (Room Quality Loop)

### Sleeping
- **crash_bed** → Sleep quality ✓

### Comfort
- **comfort_chair** → Relaxation ✓
- **storage_locker** → Personal storage ✓

### Dining
- **dining_table** → Meal quality bonus ✓
- **bar_stool** → Bar seating ✓

### Social/Recreation
- **vending_machine** → Convenience, morale ✓

### Utility
- **gutter_slab** → Work surface ✓
- **wall_lamp** → Lighting ✓
- **weapon_rack** → Weapon storage ✓

**Status:** All furniture has room purpose. ✓

---

## ✅ INSTRUMENTS (Recreation Loop)

- **scrap_guitar** → Music, morale ✓
- **drum_kit** → Music, morale ✓
- **synth** → Electronic music, morale ✓
- **harmonica** → Portable music ✓
- **amp** → Amplifies instruments ✓

**Status:** All instruments support recreation system. ✓

---

## ✅ CONSUMABLES (Social/Morale Loop)

- **swill** → Low-quality alcohol, comfort ✓
- **guttershine** → High-quality alcohol, comfort ✓

**Status:** Fits bar/social system. ✓

---

## ✅ COMPONENTS (Electronics Crafting Chain)

- **wire** → Basic component ✓
- **resistor** → Basic component ✓
- **capacitor** → Basic component ✓
- **chip** → Advanced component (requires wire) ✓
- **led** → Lighting component ✓

**Status:** Multi-step crafting chain works. ✓

---

## ⚠️ QUESTIONABLE ITEMS (Unclear Purpose)

### Non-Equippable Items
- **rusty_key** → **NO USE** - No locks/doors that need keys
- **data_chip** → **NO USE** - No data system, no trading value
- **acorn** → **NO USE** - No planting system yet

### Building Components
- **reinforced_door** → **UNCLEAR** - Can it be placed? Is it just a crafted item?

**Recommendation:** 
- **REMOVE:** rusty_key, data_chip (no systems for them)
- **KEEP:** acorn (future farming system)
- **CLARIFY:** reinforced_door (is it placeable or just inventory item?)

---

## 🔴 MISSING ITEMS (Gaps in Loops)

### Material Processing (CRITICAL)
- **leather** - Tanned hide, used for clothing
- **bone** - From butchery, used for tools/fertilizer
- **fat/tallow** - From butchery, used for candles/soap/grease
- **offal/organs** - From butchery, used for bait/compost

### Processed Foods
- **preserved_meat** - Smoked/cured, doesn't spoil
- **bone_meal** - Fertilizer for farming

### Crafting Intermediates
- **leather_straps** - Used in many recipes
- **bone_needle** - Enables sewing without metal
- **grease** - Machine maintenance

### Chemicals/Reagents
- **tannins** - Required to tan hides
- **salt** - Preserve food
- **soap** - Hygiene system

---

## 📊 SUMMARY

**Total Items:** ~60
**Fully Functional:** ~50 (83%)
**Dead Ends:** 2 (pelts, feathers - need processing)
**No Purpose:** 3 (rusty_key, data_chip, reinforced_door?)
**Missing Critical:** ~10 (material processing items)

---

## 🎯 NEXT ACTIONS

### Phase 1: Fix Dead Ends (This Session)
1. Add **leather** item (tanned hide)
2. Add **bone** item (from butchery)
3. Add **tannins** reagent (for tanning)
4. Create tanning recipes at **Skinshop Loom**
5. Create bone processing at **Salvagers Bench**
6. Add feather uses (stuffing, fletching)

### Phase 2: Remove Useless Items
1. Delete **rusty_key** (no lock system)
2. Delete **data_chip** (no data system)
3. Clarify **reinforced_door** purpose

### Phase 3: Expand Material Processing
1. Add fat/tallow/grease loop
2. Add organ/offal processing
3. Add preservation recipes (smoking, curing)
4. Add chemical reagents (salt, soap, etc.)

---

**Philosophy:** Every item should either:
1. Be part of a crafting chain (input → process → output)
2. Provide a stat bonus (equipment)
3. Enable an activity (instruments, furniture)
4. Solve a pressure (food spoilage, machine maintenance, hygiene)

If an item doesn't do one of these, **remove it**.
