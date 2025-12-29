# Audio Setup Guide

## Music Tracks

Place your music files in the `music/` folder:
- Supported formats: **MP3**, **OGG**, **WAV**
- Recommended: **OGG** (best quality/size ratio for games)
- The game will automatically load and play all tracks in this folder
- Tracks play in shuffled order and loop continuously

### How to Add Music:

1. Download your tracks from Suno (or any source)
2. Convert to MP3 or OGG if needed
3. Place files in `assets/music/`
4. Restart the game - music will start automatically!

**Example:**
```
assets/
  music/
    cyberpunk_night.ogg
    neon_dreams.mp3
    fractured_city_theme.ogg
```

---

## Sound Effects (Optional)

Place sound effect files in the `sfx/` folder:
- Supported formats: **WAV**, **OGG** (WAV recommended for short sounds)
- Name files descriptively (e.g., `click.wav`, `notification.wav`)
- The game will automatically load all sound effects

**Example:**
```
assets/
  sfx/
    click.wav
    notification.wav
    construction_complete.wav
    job_done.wav
```

---

## Volume Controls

**In-game controls** (to be added):
- Music volume: 0-100%
- SFX volume: 0-100%
- Toggle music on/off
- Toggle SFX on/off

**Current defaults:**
- Music: 30% volume
- SFX: 50% volume

---

## Converting Audio Files

If your files are in MP4 or other formats, use FFmpeg to convert:

### Install FFmpeg:
- Download from: https://ffmpeg.org/download.html
- Or use online converter: https://cloudconvert.com/

### Convert to OGG (recommended):
```bash
ffmpeg -i input.mp4 -vn -acodec libvorbis -q:a 5 output.ogg
```

### Convert to MP3:
```bash
ffmpeg -i input.mp4 -vn -acodec libmp3lame -q:a 2 output.mp3
```

---

## Troubleshooting

**No music playing?**
- Check console for `[Audio] Loaded X music tracks` message
- Make sure files are in `assets/music/` folder
- Verify file formats are MP3, OGG, or WAV
- Check that files aren't corrupted

**Music skipping or stuttering?**
- Try converting to OGG format (better performance)
- Reduce file size/bitrate if files are very large

**Want to skip to next track?**
- Press `M` key (to be implemented)
- Or wait for current track to finish

---

## Technical Details

- Music plays on a separate thread (no performance impact)
- Tracks automatically transition when finished
- Shuffle mode enabled by default
- Audio system initializes at game startup
- Volume settings will be saved to config file (future feature)
