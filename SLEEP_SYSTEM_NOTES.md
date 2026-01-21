# Sleep System - Predictable Testing Version

## Current Status: SIMPLIFIED (Fixed Schedule with Bed Logic)
The sleep system has been simplified to a predictable, testable version for development.

**Current Implementation:**
- **Sleep time:** 02:00-06:00 (4 hours)
- **Recreation time:** 01:00-02:00 (1 hour before bed)
- **Wake time:** 06:00 (unconditional - everyone wakes, no exceptions)

**Bedtime Logic (02:00-06:00):**
1. If colonist has assigned bed → Always go to sleep
2. If no bed AND tiredness >= 80 → Sleep on ground (mood penalty)
3. If no bed AND tiredness < 80 → Stay awake (skip sleep that night)

**Emergency Pass-Out:**
- Tiredness >= 100 → Pass out on ground (anytime, anywhere)
- Still wakes at 06:00 next morning

**Tiredness System:**
- Still accumulates normally (affects mood, causes pass-out)
- Creates pressure to build beds (or suffer ground sleep penalties)

## What Tiredness Affects
1. **Mood Penalties:**
   - Tiredness > 80: -10.0 mood ("Exhausted")
   - Tiredness > 60: -5.0 mood ("Very Tired")
   - Tiredness > 40: -2.0 mood ("Tired")

2. **Thoughts:**
   - Tiredness >= 90: "I can barely keep my eyes open..." (-0.2 mood)
   - Tiredness >= 70: "Getting tired..." (-0.1 mood)

3. **Emergency Pass-Out:**
   - Tiredness >= 100: Colonist passes out on floor (no bed required)

## Previous Complex System (Disabled)
The previous system used personality-driven sleep/wake thresholds based on `needs_of_the_many`:

**Wake Thresholds:**
- Fully rested: tiredness <= 10 (always wake)
- During work hours: tiredness <= (35-65 based on personality)
  - Collectivists wake at 35 (get up for work even if tired)
  - Individualists wake at 65 (sleep in until well-rested)

**Sleep Thresholds:**
- During sleep hours (18:00-06:00): tiredness > (35-65 based on personality)
  - Collectivists sleep at 35 (follow schedule)
  - Individualists sleep at 65 (resist bedtime)
- During work hours: tiredness > (70-90 based on personality)
  - Collectivists resist at 90 (stay awake for work)
  - Individualists give in at 70 (nap when tired)

**Issues with Complex System:**
- Narrow gap between wake/sleep thresholds for individualists (5 points)
- Potential for wake-sleep loops in edge cases
- Made testing other features difficult
- Unclear if personality-driven sleep is the desired behavior

## Future Considerations
- Should sleep be personality-driven or schedule-driven?
- Should colonists be able to nap during the day?
- Should there be a "night owl" vs "early bird" trait?
- Should sleep quality affect wake time?
- Should colonists wake up for emergencies (raids, fires)?
- Should exhausted colonists sleep longer?

## Files Involved
- `colonist.py`: `_update_tiredness()` - Main sleep logic
- `beds.py`: Sleep quality calculation, bed assignment
- `time_system.py`: `is_sleep_time()` - Defines sleep hours
