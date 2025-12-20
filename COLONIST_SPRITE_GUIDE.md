# Colonist Sprite System Guide

## How to Add Multiple Colonist Styles

The game supports multiple colonist sprite styles. Each colonist can have their own unique look!

## File Naming Convention

For each colonist style, create **3 sprites** (one for each direction):

```
assets/colonists/STYLE_NAME_north.png
assets/colonists/STYLE_NAME_east.png
assets/colonists/STYLE_NAME_west.png
```

OR place them directly in assets folder:

```
assets/STYLE_NAME_north.png
assets/STYLE_NAME_east.png
assets/STYLE_NAME_west.png
```

## Current Styles

### default (already exists)
- `default_north.png` - Facing up
- `default_east.png` - Facing right
- `default_west.png` - Facing left

## Adding New Styles

Just drop 3 new sprites with a new style name:

### Example: "punk" style
- `punk_north.png`
- `punk_east.png`
- `punk_west.png`

### Example: "scavenger" style
- `scavenger_north.png`
- `scavenger_east.png`
- `scavenger_west.png`

### Example: "medic" style
- `medic_north.png`
- `medic_east.png`
- `medic_west.png`

## Testing Your Sprites

1. Drop the 3 sprites in `assets/` or `assets/colonists/`
2. Run the game
3. The game will automatically load them
4. You can test different styles by changing the colonist_id in the code

## Sprite Specifications

- **Format**: PNG with transparency
- **Size**: Any size (auto-scales to match tile size)
- **Aspect Ratio**: Preserved automatically
- **Recommended**: Square or portrait orientation works best
- **Directions**: 
  - North = facing up/away from camera
  - East = facing right
  - West = facing left
  - South = uses east sprite (or alternates east/west for walking animation)

## Notes

- The game will fall back to "default" style if a style isn't found
- You can have as many styles as you want
- Each colonist can potentially use a different style
- Sprites are cached and scaled automatically for zoom levels
