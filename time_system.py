"""
Day/Night cycle for Fractured City.

Simple time tracking:
- 1 game day = 24000 ticks (~6.7 minutes at 60 FPS)
- 1 hour = 1000 ticks
- Dawn: 5-7, Day: 7-19, Dusk: 19-21, Night: 21-5
"""

from enum import Enum
from typing import Tuple

# Time constants
TICKS_PER_HOUR = 1000
TICKS_PER_DAY = 24000
HOURS_PER_DAY = 24


class TimeOfDay(Enum):
    DAWN = "dawn"
    DAY = "day"
    DUSK = "dusk"
    NIGHT = "night"


# Screen tint colors (RGBA - applied as overlay)
TIME_TINTS = {
    TimeOfDay.DAWN: (255, 200, 150, 30),   # Warm orange
    TimeOfDay.DAY: (255, 255, 255, 0),      # No tint
    TimeOfDay.DUSK: (255, 150, 100, 40),   # Deep orange
    TimeOfDay.NIGHT: (50, 50, 120, 80),    # Blue darkness
}


class GameTime:
    """Tracks game time and day/night cycle."""
    
    def __init__(self):
        self.total_ticks: int = 6000  # Start at 6 AM
        self.day: int = 1
    
    def tick(self) -> None:
        """Advance time by one tick."""
        self.total_ticks += 1
        if self.total_ticks >= TICKS_PER_DAY:
            self.total_ticks -= TICKS_PER_DAY
            self.day += 1
    
    @property
    def hour(self) -> int:
        """Current hour (0-23)."""
        return self.total_ticks // TICKS_PER_HOUR
    
    @property
    def minute(self) -> int:
        """Current minute (0-59)."""
        ticks_into_hour = self.total_ticks % TICKS_PER_HOUR
        return int((ticks_into_hour / TICKS_PER_HOUR) * 60)
    
    @property
    def time_of_day(self) -> TimeOfDay:
        """Get current time of day period."""
        h = self.hour
        if 5 <= h < 7:
            return TimeOfDay.DAWN
        elif 7 <= h < 19:
            return TimeOfDay.DAY
        elif 19 <= h < 21:
            return TimeOfDay.DUSK
        else:
            return TimeOfDay.NIGHT
    
    @property
    def is_night(self) -> bool:
        """Check if it's nighttime (for sleep logic)."""
        return self.time_of_day == TimeOfDay.NIGHT
    
    @property
    def is_sleep_time(self) -> bool:
        """Check if colonists should want to sleep (night or late evening)."""
        h = self.hour
        return h >= 21 or h < 6
    
    def get_time_string(self) -> str:
        """Get formatted time string like '14:30'."""
        return f"{self.hour:02d}:{self.minute:02d}"
    
    def get_display_string(self) -> str:
        """Get full display string like 'Day 3, 14:30'."""
        return f"Day {self.day}, {self.get_time_string()}"
    
    def get_tint(self) -> Tuple[int, int, int, int]:
        """Get current screen tint color (RGBA)."""
        tod = self.time_of_day
        base_tint = TIME_TINTS[tod]
        
        # Smooth transitions
        h = self.hour
        m = self.minute
        progress = m / 60.0
        
        if tod == TimeOfDay.DAWN:
            # Transition from night to day
            if h == 5:
                # Early dawn - still dark
                night = TIME_TINTS[TimeOfDay.NIGHT]
                dawn = TIME_TINTS[TimeOfDay.DAWN]
                return self._lerp_color(night, dawn, progress)
            elif h == 6:
                # Late dawn - getting bright
                dawn = TIME_TINTS[TimeOfDay.DAWN]
                day = TIME_TINTS[TimeOfDay.DAY]
                return self._lerp_color(dawn, day, progress)
        
        elif tod == TimeOfDay.DUSK:
            # Transition from day to night
            if h == 19:
                day = TIME_TINTS[TimeOfDay.DAY]
                dusk = TIME_TINTS[TimeOfDay.DUSK]
                return self._lerp_color(day, dusk, progress)
            elif h == 20:
                dusk = TIME_TINTS[TimeOfDay.DUSK]
                night = TIME_TINTS[TimeOfDay.NIGHT]
                return self._lerp_color(dusk, night, progress)
        
        return base_tint
    
    def _lerp_color(self, c1: Tuple, c2: Tuple, t: float) -> Tuple[int, int, int, int]:
        """Linear interpolate between two colors."""
        return (
            int(c1[0] + (c2[0] - c1[0]) * t),
            int(c1[1] + (c2[1] - c1[1]) * t),
            int(c1[2] + (c2[2] - c1[2]) * t),
            int(c1[3] + (c2[3] - c1[3]) * t),
        )


# Global instance
_game_time: GameTime = None


def get_game_time() -> GameTime:
    """Get or create the global game time instance."""
    global _game_time
    if _game_time is None:
        _game_time = GameTime()
    return _game_time


def tick_time() -> None:
    """Advance game time by one tick."""
    get_game_time().tick()


def is_night() -> bool:
    """Check if it's nighttime."""
    return get_game_time().is_night


def is_sleep_time() -> bool:
    """Check if colonists should want to sleep."""
    return get_game_time().is_sleep_time


def get_time_string() -> str:
    """Get current time as string."""
    return get_game_time().get_time_string()


def get_display_string() -> str:
    """Get full time display string."""
    return get_game_time().get_display_string()


def get_screen_tint() -> Tuple[int, int, int, int]:
    """Get current screen tint for day/night."""
    return get_game_time().get_tint()
