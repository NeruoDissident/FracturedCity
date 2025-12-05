"""Global environmental statistics tracking.

Maintains rolling averages of environmental parameters across all sampled tiles.
Used by the colonist affinity system to determine relative preferences.
"""

from collections import deque
from typing import Dict


class EnvironmentStats:
    """Tracks global averages of environmental parameters."""
    
    def __init__(self, max_samples: int = 100):
        """Initialize with a maximum number of samples to track."""
        self.max_samples = max_samples
        
        # Rolling buffers for each parameter
        self._interference_samples = deque(maxlen=max_samples)
        self._echo_samples = deque(maxlen=max_samples)
        self._pressure_samples = deque(maxlen=max_samples)
        self._integrity_samples = deque(maxlen=max_samples)
        self._outside_samples = deque(maxlen=max_samples)  # 0 or 1
        self._crowding_samples = deque(maxlen=max_samples)
        
        # Cached averages (updated when samples are added)
        self._avg_interference = 0.0
        self._avg_echo = 0.0
        self._avg_pressure = 0.0
        self._avg_integrity = 1.0
        self._avg_outside = 0.5
        self._avg_crowding = 0.0
    
    def add_sample(self, sample: Dict) -> None:
        """Add a new environment sample and update averages.
        
        Args:
            sample: Dictionary containing environmental parameters
        """
        # Add to buffers
        self._interference_samples.append(sample.get('interference', 0.0))
        self._echo_samples.append(sample.get('echo', 0.0))
        self._pressure_samples.append(sample.get('pressure', 0.0))
        self._integrity_samples.append(sample.get('integrity', 1.0))
        
        # Convert boolean to float for outside
        is_outside = 1.0 if sample.get('is_outside', True) else 0.0
        self._outside_samples.append(is_outside)
        
        # Crowding is based on nearby colonists
        nearby = sample.get('nearby_colonists', 0)
        self._crowding_samples.append(float(nearby))
        
        # Update cached averages
        self._update_averages()
    
    def _update_averages(self) -> None:
        """Recalculate all averages from current samples."""
        if len(self._interference_samples) > 0:
            self._avg_interference = sum(self._interference_samples) / len(self._interference_samples)
        if len(self._echo_samples) > 0:
            self._avg_echo = sum(self._echo_samples) / len(self._echo_samples)
        if len(self._pressure_samples) > 0:
            self._avg_pressure = sum(self._pressure_samples) / len(self._pressure_samples)
        if len(self._integrity_samples) > 0:
            self._avg_integrity = sum(self._integrity_samples) / len(self._integrity_samples)
        if len(self._outside_samples) > 0:
            self._avg_outside = sum(self._outside_samples) / len(self._outside_samples)
        if len(self._crowding_samples) > 0:
            self._avg_crowding = sum(self._crowding_samples) / len(self._crowding_samples)
    
    def get_averages(self) -> Dict[str, float]:
        """Get current global averages for all parameters.
        
        Returns:
            Dictionary mapping parameter names to their global averages
        """
        return {
            'interference': self._avg_interference,
            'echo': self._avg_echo,
            'pressure': self._avg_pressure,
            'integrity': self._avg_integrity,
            'outside': self._avg_outside,
            'crowding': self._avg_crowding,
        }
    
    def get_sample_count(self) -> int:
        """Get the number of samples currently tracked."""
        return len(self._interference_samples)


# Global instance
_global_env_stats = EnvironmentStats(max_samples=100)


def get_environment_stats() -> EnvironmentStats:
    """Get the global environment statistics tracker."""
    return _global_env_stats


def add_environment_sample(sample: Dict) -> None:
    """Add a sample to the global environment statistics.
    
    Args:
        sample: Environment sample dictionary
    """
    _global_env_stats.add_sample(sample)


def get_global_averages() -> Dict[str, float]:
    """Get current global averages for all environmental parameters.
    
    Returns:
        Dictionary mapping parameter names to their global averages
    """
    return _global_env_stats.get_averages()
