# Colonist Stat Audit - Trait vs Hardcoded

## Current State Analysis

### ✅ ALREADY FROM TRAITS
These stats are correctly generated from traits:

1. **Affinities** (starting biases)
   - `affinity_interference` - from traits
   - `affinity_echo` - from traits
   - `affinity_pressure` - from traits
   - `affinity_integrity` - from traits
   - `affinity_outside` - from traits
   - `affinity_crowding` - from traits

2. **Job Speed Modifiers**
   - `trait_job_mods` - from traits (build, haul, craft, scavenge)

3. **Stat Modifiers**
   - `trait_stat_mods` - from traits (stress_resist, echo_sense, etc.)

4. **Needs of the Many**
   - `needs_of_the_many` - generated from bio/traits (1-10)

---

## ❌ HARDCODED DEFAULTS (Should be from traits?)

### Movement & Physical
- **`move_speed = 8`** - HARDCODED
  - Should vary by origin/experience?
  - Topside runners vs deep shelter dwellers?

- **`hunger_rate = 0.003`** - HARDCODED
  - Should vary by physiology/experience?
  - Some colonists burn energy faster?

### Personality Drift
- **`preference_drift_rate = 0.00005`** - HARDCODED
  - Should vary by personality?
  - Stubborn vs adaptable colonists?

### Starting States
- **`comfort = 0.0`** - HARDCODED (neutral start)
  - OK - should start neutral

- **`stress = 0.0`** - HARDCODED (neutral start)
  - OK - should start neutral

- **`preferences = all 0.0`** - HARDCODED (neutral start)
  - ⚠️ ISSUE: Preferences start at 0, but affinities are set from traits
  - Should preferences START with trait-based values?

---

## 🔍 RECOMMENDATIONS

### Priority 1: Preferences Should Start Non-Zero
**Current:** Preferences start at 0.0, affinities set from traits
**Problem:** Colonists with strong trait affinities (e.g., "likes outside") start with neutral preferences
**Solution:** Initialize preferences based on affinities

```python
# After setting affinities from traits:
self.preferences = {
    "likes_interference": self.affinity_interference * 2.0,  # Scale to preference range
    "likes_echo": self.affinity_echo * 2.0,
    "likes_pressure": self.affinity_pressure * 2.0,
    "likes_integrity": self.affinity_integrity * 2.0,
    "likes_outside": self.affinity_outside * 2.0,
    "likes_crowding": self.affinity_crowding * 2.0,
}
```

### Priority 2: Movement Speed from Traits
**Add to trait system:**
- Topside runners: `move_speed = 6` (faster)
- Deep shelter dwellers: `move_speed = 10` (slower, cautious)
- Default: `move_speed = 8`

### Priority 3: Personality Drift Rate from Traits
**Add to trait system:**
- Stubborn/rigid traits: `drift_rate = 0.00002` (slow to change)
- Adaptable/flexible traits: `drift_rate = 0.0001` (quick to adapt)
- Default: `drift_rate = 0.00005`

### Priority 4: Hunger Rate (Optional)
**Add to trait system:**
- High metabolism: `hunger_rate = 0.004`
- Low metabolism: `hunger_rate = 0.002`
- Default: `hunger_rate = 0.003`

---

## 📋 IMPLEMENTATION ORDER

1. **Fix preferences initialization** - High impact, easy fix
2. **Add move_speed to traits** - Medium impact, easy to add
3. **Add drift_rate to traits** - Low impact, adds personality depth
4. **Add hunger_rate to traits** (optional) - Low impact, minor gameplay effect
