# Sprite Renaming Guide

Your sprites are currently organized by **bitmask value** (0-255).
They need to be renamed to **variant numbers** (0-46).

## Bitmask to Variant Mapping

Use this table to rename your sprites:

| Current Name (Bitmask) | New Name (Variant) | Pattern |
|------------------------|-------------------|---------|
| `_0.png` | `_0.png` | Empty |
| `_1.png` | `_1.png` | N edge |
| `_4.png` | `_2.png` | E edge |
| `_5.png` | `_3.png` | N+E |
| `_16.png` | `_4.png` | S edge |
| `_17.png` | `_5.png` | N+S |
| `_20.png` | `_6.png` | E+S |
| `_21.png` | `_7.png` | N+E+S |
| `_64.png` | `_8.png` | W edge |
| `_65.png` | `_9.png` | N+W |
| `_68.png` | `_10.png` | E+W |
| `_69.png` | `_11.png` | N+E+W |
| `_80.png` | `_12.png` | S+W |
| `_81.png` | `_13.png` | N+S+W |
| `_84.png` | `_14.png` | E+S+W |
| `_85.png` | `_15.png` | N+E+S+W |
| `_7.png` | `_16.png` | N+NE+E |
| `_23.png` | `_17.png` | N+NE+E+SE+S |
| `_28.png` | `_18.png` | E+SE+S |
| `_29.png` | `_19.png` | N+E+SE+S |
| `_71.png` | `_20.png` | N+NE+E+W |
| `_87.png` | `_21.png` | N+NE+E+SE+S+W |
| `_92.png` | `_22.png` | E+SE+S+W |
| `_93.png` | `_23.png` | N+E+SE+S+W |
| `_112.png` | `_24.png` | S+W |
| `_113.png` | `_25.png` | N+S+W |
| `_116.png` | `_26.png` | E+S+W |
| `_117.png` | `_27.png` | N+E+S+W |
| `_124.png` | `_28.png` | E+SE+S+SW+W |
| `_125.png` | `_29.png` | N+E+SE+S+SW+W |
| `_209.png` | `_30.png` | N+S+W+NW |
| `_213.png` | `_31.png` | N+E+S+W+NW |
| `_221.png` | `_32.png` | N+E+S+SW+W+NW |
| `_223.png` | `_33.png` | N+NE+E+S+SW+W+NW |
| `_241.png` | `_34.png` | N+S+SW+W+NW |
| `_245.png` | `_35.png` | N+E+S+SW+W+NW |
| `_247.png` | `_36.png` | N+NE+E+S+SW+W+NW |
| `_253.png` | `_37.png` | N+E+SE+S+SW+W+NW |
| `_255.png` | `_38.png` | Full |
| `_31.png` | `_39.png` | N+NE+E+SE+S |
| `_95.png` | `_40.png` | N+NE+E+SE+S+W |
| `_119.png` | `_41.png` | N+NE+E+SE+S+W |
| `_127.png` | `_42.png` | N+NE+E+SE+S+W+NW |
| `_199.png` | `_43.png` | N+NE+E+W+NW |
| `_215.png` | `_44.png` | N+NE+E+S+W+NW |
| `_197.png` | `_45.png` | N+E+W+NW |
| `_193.png` | `_46.png` | N+W+NW |

## How to Rename

1. Look at each sprite in your `assets/tiles/dirt/` folder
2. Identify its current bitmask number
3. Rename it to the corresponding variant number using the table above
4. Keep the prefix: `ground_dirt_overlay_autotile_`

Example:
- `ground_dirt_overlay_autotile_255.png` → `ground_dirt_overlay_autotile_38.png`
- `ground_dirt_overlay_autotile_85.png` → `ground_dirt_overlay_autotile_15.png`

Once renamed, the autotiling will work perfectly!
