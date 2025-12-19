"""
Procedural sound effects generator using Pygame and numpy.

Creates basic placeholder sounds until real audio files are available.
"""

import pygame
import numpy as np


def generate_tone(frequency: float, duration: float, sample_rate: int = 22050) -> pygame.mixer.Sound:
    """Generate a simple sine wave tone."""
    samples = int(duration * sample_rate)
    wave = np.sin(2 * np.pi * frequency * np.linspace(0, duration, samples))
    
    # Apply fade in/out to prevent clicks
    fade_samples = int(0.01 * sample_rate)
    fade_in = np.linspace(0, 1, fade_samples)
    fade_out = np.linspace(1, 0, fade_samples)
    wave[:fade_samples] *= fade_in
    wave[-fade_samples:] *= fade_out
    
    # Convert to 16-bit PCM
    wave = (wave * 32767).astype(np.int16)
    
    # Create stereo sound
    stereo_wave = np.column_stack((wave, wave))
    
    return pygame.mixer.Sound(buffer=stereo_wave)


def generate_click() -> pygame.mixer.Sound:
    """Generate a UI click sound."""
    return generate_tone(1200, 0.05)


def generate_notification() -> pygame.mixer.Sound:
    """Generate a notification sound - two-tone beep."""
    sample_rate = 22050
    duration = 0.15
    
    # First tone
    samples1 = int(duration * sample_rate)
    wave1 = np.sin(2 * np.pi * 800 * np.linspace(0, duration, samples1))
    
    # Second tone
    samples2 = int(duration * sample_rate)
    wave2 = np.sin(2 * np.pi * 600 * np.linspace(0, duration, samples2))
    
    # Combine
    wave = np.concatenate([wave1, wave2])
    
    # Fade
    fade_samples = int(0.01 * sample_rate)
    fade_in = np.linspace(0, 1, fade_samples)
    fade_out = np.linspace(1, 0, fade_samples)
    wave[:fade_samples] *= fade_in
    wave[-fade_samples:] *= fade_out
    
    # Convert to 16-bit PCM
    wave = (wave * 32767).astype(np.int16)
    stereo_wave = np.column_stack((wave, wave))
    
    return pygame.mixer.Sound(buffer=stereo_wave)


def generate_success() -> pygame.mixer.Sound:
    """Generate a success sound - ascending tones."""
    sample_rate = 22050
    duration = 0.1
    
    # Three ascending tones
    freqs = [400, 500, 600]
    waves = []
    
    for freq in freqs:
        samples = int(duration * sample_rate)
        wave = np.sin(2 * np.pi * freq * np.linspace(0, duration, samples))
        waves.append(wave)
    
    wave = np.concatenate(waves)
    
    # Fade
    fade_samples = int(0.01 * sample_rate)
    fade_out = np.linspace(1, 0, fade_samples)
    wave[-fade_samples:] *= fade_out
    
    # Convert to 16-bit PCM
    wave = (wave * 32767).astype(np.int16)
    stereo_wave = np.column_stack((wave, wave))
    
    return pygame.mixer.Sound(buffer=stereo_wave)


def generate_error() -> pygame.mixer.Sound:
    """Generate an error sound - low buzz."""
    sample_rate = 22050
    duration = 0.2
    
    samples = int(duration * sample_rate)
    wave = np.sin(2 * np.pi * 200 * np.linspace(0, duration, samples))
    
    # Add some noise for harshness
    noise = np.random.uniform(-0.1, 0.1, samples)
    wave = wave + noise
    
    # Fade
    fade_samples = int(0.01 * sample_rate)
    fade_in = np.linspace(0, 1, fade_samples)
    fade_out = np.linspace(1, 0, fade_samples)
    wave[:fade_samples] *= fade_in
    wave[-fade_samples:] *= fade_out
    
    # Convert to 16-bit PCM
    wave = np.clip(wave, -1, 1)
    wave = (wave * 32767).astype(np.int16)
    stereo_wave = np.column_stack((wave, wave))
    
    return pygame.mixer.Sound(buffer=stereo_wave)


def generate_construction() -> pygame.mixer.Sound:
    """Generate a construction complete sound."""
    sample_rate = 22050
    duration = 0.3
    
    samples = int(duration * sample_rate)
    
    # Metallic clang - mix of frequencies
    wave = (np.sin(2 * np.pi * 800 * np.linspace(0, duration, samples)) * 0.5 +
            np.sin(2 * np.pi * 1200 * np.linspace(0, duration, samples)) * 0.3 +
            np.sin(2 * np.pi * 1600 * np.linspace(0, duration, samples)) * 0.2)
    
    # Decay envelope
    decay = np.exp(-5 * np.linspace(0, 1, samples))
    wave *= decay
    
    # Convert to 16-bit PCM
    wave = np.clip(wave, -1, 1)
    wave = (wave * 32767).astype(np.int16)
    stereo_wave = np.column_stack((wave, wave))
    
    return pygame.mixer.Sound(buffer=stereo_wave)


def init_procedural_sounds() -> dict:
    """Generate all procedural sounds and return as dictionary."""
    sounds = {}
    
    try:
        print("[Procedural SFX] Generating sounds...")
        sounds['click'] = generate_click()
        print("[Procedural SFX] - click generated")
        sounds['notification'] = generate_notification()
        print("[Procedural SFX] - notification generated")
        sounds['success'] = generate_success()
        print("[Procedural SFX] - success generated")
        sounds['error'] = generate_error()
        print("[Procedural SFX] - error generated")
        sounds['construction'] = generate_construction()
        print("[Procedural SFX] - construction generated")
        
        print("[Procedural SFX] Generated 5 placeholder sounds successfully")
    except Exception as e:
        print(f"[Procedural SFX] Error generating sounds: {e}")
        import traceback
        traceback.print_exc()
    
    return sounds
