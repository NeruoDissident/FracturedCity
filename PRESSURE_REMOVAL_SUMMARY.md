# Environmental Pressure Removal - Complete

## What Was Removed

**Environmental "pressure" preference system** - a non-functional atmospheric preference that was never implemented in gameplay.

### Files Modified:

1. **colonist.py**
   - Removed `affinity_pressure` attribute
   - Removed `likes_pressure` from preferences dict
   - Removed pressure from all drift/update systems
   - Removed pressure from environment sampling
   - Removed pressure thoughts/flavor text
   - Removed pressure from bio generation templates
   - Updated hazard calculation (removed pressure component)

2. **ui.py**
   - Removed "Pressure" from Status tab preferences display
   - Removed "Pressure" from Visitor panel preferences display
   - Removed "Prs" from debug affinity display
   - Updated environment display to show Integrity instead

3. **traits.py**
   - Removed "pressure" from combined affinities dict
   - Traits that had pressure affinities still exist but those values are now ignored

4. **grid.py**
   - NO CHANGES - pressure still tracked in env_data but always 0.0 (harmless)

## What Remains

**Job pressure system** - fully functional, renamed to "Needs of the Many":
- `job.pressure` (1-10) = job urgency
- `colonist.needs_of_the_many` (1-10) = colonist's collectivism
- Dynamic pressure for cooking jobs based on food availability
- All working as intended

## Traits That Had Pressure Affinities

These traits previously gave "pressure" affinity bonuses. The affinity values are now ignored, but the traits still exist with their other benefits:

- **deep_shelters** (Origin): Had pressure +0.2
- **fringe_settlements** (Origin): Had pressure +0.3
- **former_mercenary** (Experience): Had pressure +0.3
- **collapsed_block_escapee** (Experience): Had pressure +0.2
- **heatline_runner** (Experience): Had pressure +0.4
- **silent_commune_raised** (Experience): Had pressure -0.2
- **mild_paranoia** (Quirk): Had pressure +0.1
- **pressure_blind** (Major Trait): Had pressure -0.5
- **last_light_disciple** (Major Trait): Had pressure +0.2

**Note:** These traits should eventually be updated to provide `needs_of_the_many` modifiers instead, but that's a separate task for trait system expansion.

## Testing Checklist

- [x] Colonist initialization (no errors)
- [ ] Status tab displays correctly (no "Pressure" shown)
- [ ] Preferences drift without errors
- [ ] Comfort/stress calculation works
- [ ] Environment thoughts generate correctly
- [ ] Bio generation works
- [ ] Visitor panel displays correctly

## Next Steps

1. Test in-game to confirm no errors
2. Consider mapping old pressure-related traits to needs_of_the_many modifiers
3. Initialize preferences from affinities at colonist creation (separate task)
