"""
Audio system for background music and sound effects.

Handles music playback, sound effects, and volume controls.
"""

import pygame
import os
import random
from typing import Optional, List


class AudioManager:
    """Manages background music and sound effects."""
    
    def __init__(self):
        self.music_enabled = True
        self.sfx_enabled = True
        self.music_volume = 0.3  # 30% default
        self.sfx_volume = 0.5    # 50% default
        
        self.music_tracks: List[str] = []
        self.current_track_index = 0
        self.shuffle = True
        
        self.sfx_cache = {}  # Cache loaded sound effects
        
        # Initialize pygame mixer if not already done
        if not pygame.mixer.get_init():
            pygame.mixer.init()
    
    def load_music_tracks(self, music_folder: str = "assets/music") -> None:
        """Load all music tracks from the music folder."""
        if not os.path.exists(music_folder):
            os.makedirs(music_folder)
            print(f"[Audio] Created music folder: {music_folder}")
            print(f"[Audio] Place your music files (.mp3, .ogg, .wav) in this folder")
            return
        
        # Find all audio files
        valid_extensions = ('.mp3', '.ogg', '.wav')
        self.music_tracks = [
            os.path.join(music_folder, f)
            for f in os.listdir(music_folder)
            if f.lower().endswith(valid_extensions)
        ]
        
        if self.music_tracks:
            if self.shuffle:
                random.shuffle(self.music_tracks)
            print(f"[Audio] Loaded {len(self.music_tracks)} music tracks")
        else:
            print(f"[Audio] No music files found in {music_folder}")
    
    def play_music(self) -> None:
        """Start playing background music."""
        if not self.music_enabled or not self.music_tracks:
            return
        
        try:
            track = self.music_tracks[self.current_track_index]
            pygame.mixer.music.load(track)
            pygame.mixer.music.set_volume(self.music_volume)
            pygame.mixer.music.play()
            
            track_name = os.path.basename(track)
            print(f"[Audio] Now playing: {track_name}")
        except Exception as e:
            print(f"[Audio] Error playing music: {e}")
    
    def next_track(self) -> None:
        """Skip to the next track."""
        if not self.music_tracks:
            return
        
        self.current_track_index = (self.current_track_index + 1) % len(self.music_tracks)
        self.play_music()
    
    def update(self) -> None:
        """Update music state. Call this every frame."""
        if not self.music_enabled or not self.music_tracks:
            return
        
        # Check if current track finished, play next
        if not pygame.mixer.music.get_busy():
            self.next_track()
    
    def set_music_volume(self, volume: float) -> None:
        """Set music volume (0.0 to 1.0)."""
        self.music_volume = max(0.0, min(1.0, volume))
        pygame.mixer.music.set_volume(self.music_volume)
    
    def set_sfx_volume(self, volume: float) -> None:
        """Set sound effects volume (0.0 to 1.0)."""
        self.sfx_volume = max(0.0, min(1.0, volume))
        # Update volume for all cached sounds
        for sound in self.sfx_cache.values():
            sound.set_volume(self.sfx_volume)
    
    def toggle_music(self) -> bool:
        """Toggle music on/off. Returns new state."""
        self.music_enabled = not self.music_enabled
        if self.music_enabled:
            self.play_music()
        else:
            pygame.mixer.music.stop()
        return self.music_enabled
    
    def toggle_sfx(self) -> bool:
        """Toggle sound effects on/off. Returns new state."""
        self.sfx_enabled = not self.sfx_enabled
        return self.sfx_enabled
    
    def load_sound(self, sound_name: str, filepath: str) -> None:
        """Load a sound effect into cache."""
        try:
            sound = pygame.mixer.Sound(filepath)
            sound.set_volume(self.sfx_volume)
            self.sfx_cache[sound_name] = sound
        except Exception as e:
            print(f"[Audio] Error loading sound '{sound_name}': {e}")
    
    def play_sound(self, sound_name: str) -> None:
        """Play a cached sound effect."""
        if not self.sfx_enabled:
            return
        
        sound = self.sfx_cache.get(sound_name)
        if sound:
            sound.play()
    
    def load_sfx_folder(self, sfx_folder: str = "assets/sfx") -> None:
        """Load all sound effects from the sfx folder."""
        if not os.path.exists(sfx_folder):
            os.makedirs(sfx_folder)
            print(f"[Audio] Created SFX folder: {sfx_folder}")
            # Generate procedural sounds as fallback
            self._load_procedural_sounds()
            return
        
        valid_extensions = ('.wav', '.ogg')  # WAV and OGG work best for SFX
        count = 0
        
        for filename in os.listdir(sfx_folder):
            if filename.lower().endswith(valid_extensions):
                name = os.path.splitext(filename)[0]
                filepath = os.path.join(sfx_folder, filename)
                self.load_sound(name, filepath)
                count += 1
        
        if count > 0:
            print(f"[Audio] Loaded {count} sound effects")
        else:
            # No files found, use procedural sounds
            print(f"[Audio] No sound files found, generating procedural sounds")
            self._load_procedural_sounds()
    
    def _load_procedural_sounds(self) -> None:
        """Generate and load procedural placeholder sounds."""
        try:
            from procedural_sfx import init_procedural_sounds
            procedural_sounds = init_procedural_sounds()
            
            for name, sound in procedural_sounds.items():
                sound.set_volume(self.sfx_volume)
                self.sfx_cache[name] = sound
        except ImportError:
            print("[Audio] procedural_sfx.py not found, skipping procedural sounds")
        except Exception as e:
            print(f"[Audio] Error loading procedural sounds: {e}")


# Global audio manager instance
_audio_manager: Optional[AudioManager] = None


def get_audio_manager() -> AudioManager:
    """Get or create the global audio manager."""
    global _audio_manager
    if _audio_manager is None:
        _audio_manager = AudioManager()
    return _audio_manager


def init_audio() -> None:
    """Initialize the audio system. Call this at game startup."""
    audio = get_audio_manager()
    audio.load_music_tracks()
    audio.load_sfx_folder()
    audio.play_music()


def play_sound(sound_name: str) -> None:
    """Convenience function to play a sound effect."""
    get_audio_manager().play_sound(sound_name)
