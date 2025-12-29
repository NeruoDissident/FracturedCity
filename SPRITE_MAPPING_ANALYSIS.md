# Sprite Mapping Analysis

Examining user's actual sprites to determine correct variant mapping.

## Observed Sprites:

**Variant 0**: Full tile (all dirt) ✓
**Variant 1**: North edge (dirt fades at top) ✓
**Variant 2**: South edge (dirt fades at bottom)
**Variant 3**: West edge (dirt fades at left)
**Variant 4**: East edge (dirt fades at right)
**Variant 5**: Outer corner NW (small dirt bottom-right)
**Variant 6**: Outer corner SW (small dirt top-right)
**Variant 7**: Outer corner SE (small dirt top-left)
**Variant 8**: Outer corner NE (small dirt bottom-left)
**Variant 9**: Inner corner NW (concave cut from top-left)
**Variant 10**: Inner corner NE (concave cut from top-right)
**Variant 11**: Inner corner SE (concave cut from bottom-right)
**Variant 12**: Inner corner SW (concave cut from bottom-left)

## Issue Identified:

User's sprite numbering follows RPG Maker / Terraria standard:
- Variants 5-8: Outer corners (convex)
- Variants 9-12: Inner corners (concave)

My algorithm expects:
- Variants 5-8: Outer corners (CORRECT)
- Variants 9-12: Inner corners (CORRECT)

BUT the corner orientations are different!

## Standard Blob Autotiling Convention:

Looking at Terraria/RPG Maker, the standard is:
- Variant 5: Outer NW (dirt extends to SE)
- Variant 6: Outer NE (dirt extends to SW)
- Variant 7: Outer SW (dirt extends to NE)
- Variant 8: Outer SE (dirt extends to NW)

User's sprites appear to follow this standard.
