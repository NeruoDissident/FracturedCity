# Sprite Visual Verification Guide

This document describes what each variant (0-46) should visually represent based on its bitmask value.

## Legend:
- **N/S/E/W** = Cardinal directions (North/South/East/West edges)
- **NE/NW/SE/SW** = Diagonal corners
- **Dirt** = Brown dirt texture
- **Concrete** = Gray concrete showing through (transparent areas)

---

## Variant 0 (Bitmask 0)
**Pattern:** Isolated tile, no neighbors
**Visual:** Small dirt blob in center, concrete visible on all sides and corners
**Use:** Single isolated dirt tile

## Variant 1 (Bitmask 1)
**Pattern:** N edge only
**Visual:** Dirt extends to North edge, concrete on S/E/W sides and all corners
**Use:** Southern tip of dirt blob

## Variant 2 (Bitmask 4)
**Pattern:** E edge only
**Visual:** Dirt extends to East edge, concrete on N/S/W sides and all corners
**Use:** Western tip of dirt blob

## Variant 3 (Bitmask 16)
**Pattern:** S edge only
**Visual:** Dirt extends to South edge, concrete on N/E/W sides and all corners
**Use:** Northern tip of dirt blob

## Variant 4 (Bitmask 64)
**Pattern:** W edge only
**Visual:** Dirt extends to West edge, concrete on N/S/E sides and all corners
**Use:** Eastern tip of dirt blob

## Variant 5 (Bitmask 5)
**Pattern:** N+E edges
**Visual:** Dirt extends to North and East edges, concrete on S/W sides, concrete in SW corner
**Use:** Outer corner (SW position) - dirt blob extends to NE

## Variant 6 (Bitmask 20)
**Pattern:** E+S edges
**Visual:** Dirt extends to East and South edges, concrete on N/W sides, concrete in NW corner
**Use:** Outer corner (NW position) - dirt blob extends to SE

## Variant 7 (Bitmask 80)
**Pattern:** S+W edges
**Visual:** Dirt extends to South and West edges, concrete on N/E sides, concrete in NE corner
**Use:** Outer corner (NE position) - dirt blob extends to SW

## Variant 8 (Bitmask 65)
**Pattern:** W+N edges
**Visual:** Dirt extends to West and North edges, concrete on S/E sides, concrete in SE corner
**Use:** Outer corner (SE position) - dirt blob extends to NW

## Variant 9 (Bitmask 7)
**Pattern:** N+NE+E edges/corners
**Visual:** Dirt fills N, NE corner, and E edges. Concrete on S/W sides
**Use:** Smooth curve from N to E

## Variant 10 (Bitmask 28)
**Pattern:** E+SE+S edges/corners
**Visual:** Dirt fills E, SE corner, and S edges. Concrete on N/W sides
**Use:** Smooth curve from E to S

## Variant 11 (Bitmask 112)
**Pattern:** S+SW+W edges/corners
**Visual:** Dirt fills S, SW corner, and W edges. Concrete on N/E sides
**Use:** Smooth curve from S to W

## Variant 12 (Bitmask 193)
**Pattern:** W+NW+N edges/corners
**Visual:** Dirt fills W, NW corner, and N edges. Concrete on S/E sides
**Use:** Smooth curve from W to N

## Variant 13 (Bitmask 17)
**Pattern:** N+S edges (opposite)
**Visual:** Dirt extends to both N and S edges, concrete on E/W sides
**Use:** Vertical strip of dirt

## Variant 14 (Bitmask 68)
**Pattern:** E+W edges (opposite)
**Visual:** Dirt extends to both E and W edges, concrete on N/S sides
**Use:** Horizontal strip of dirt

## Variant 15 (Bitmask 21)
**Pattern:** N+NE+E+S edges
**Visual:** Dirt on N, NE, E, S. Concrete on W side
**Use:** T-junction or edge piece

## Variant 16 (Bitmask 84)
**Pattern:** E+S+SW+W edges
**Visual:** Dirt on E, S, SW, W. Concrete on N side
**Use:** T-junction or edge piece

## Variant 17 (Bitmask 81)
**Pattern:** S+W+NW+N edges
**Visual:** Dirt on S, W, NW, N. Concrete on E side
**Use:** T-junction or edge piece

## Variant 18 (Bitmask 69)
**Pattern:** W+N+NE+E edges
**Visual:** Dirt on W, N, NE, E. Concrete on S side
**Use:** T-junction or edge piece

## Variant 19 (Bitmask 23)
**Pattern:** N+NE+E+SE+S edges
**Visual:** Dirt fills entire N-E-S arc with corners. Concrete on W side
**Use:** Smooth western edge

## Variant 20 (Bitmask 92)
**Pattern:** E+SE+S+SW+W edges
**Visual:** Dirt fills entire E-S-W arc with corners. Concrete on N side
**Use:** Smooth northern edge

## Variant 21 (Bitmask 113)
**Pattern:** S+SW+W+NW+N edges
**Visual:** Dirt fills entire S-W-N arc with corners. Concrete on E side
**Use:** Smooth eastern edge

## Variant 22 (Bitmask 197)
**Pattern:** W+NW+N+NE+E edges
**Visual:** Dirt fills entire W-N-E arc with corners. Concrete on S side
**Use:** Smooth southern edge

## Variant 23 (Bitmask 29)
**Pattern:** N+E+SE+S edges
**Visual:** Dirt on N, E, SE, S. Missing NE corner (inner corner cut)
**Use:** Inner corner at NE position

## Variant 24 (Bitmask 116)
**Pattern:** E+S+W edges
**Visual:** Dirt on E, S, W. Concrete on N side
**Use:** T-junction opening north

## Variant 25 (Bitmask 209)
**Pattern:** S+W+N edges
**Visual:** Dirt on S, W, N. Concrete on E side
**Use:** T-junction opening east

## Variant 26 (Bitmask 71)
**Pattern:** W+N+E edges
**Visual:** Dirt on W, N, E. Concrete on S side
**Use:** T-junction opening south

## Variant 27 (Bitmask 31)
**Pattern:** N+NE+E+SE+S edges
**Visual:** Dirt fills N-E-S with both corners. Concrete on W
**Use:** Smooth western edge with corners

## Variant 28 (Bitmask 124)
**Pattern:** E+SE+S+SW+W edges
**Visual:** Dirt fills E-S-W with both corners. Concrete on N
**Use:** Smooth northern edge with corners

## Variant 29 (Bitmask 241)
**Pattern:** S+SW+W+NW+N edges
**Visual:** Dirt fills S-W-N with both corners. Concrete on E
**Use:** Smooth eastern edge with corners

## Variant 30 (Bitmask 199)
**Pattern:** W+NW+N+NE+E edges
**Visual:** Dirt fills W-N-E with both corners. Concrete on S
**Use:** Smooth southern edge with corners

## Variant 31 (Bitmask 85)
**Pattern:** N+E+S+W (all cardinals, no diagonals)
**Visual:** Dirt extends to all 4 edges, concrete cuts in all 4 corners
**Use:** Cross/plus shape with inner corners at all 4 diagonals

## Variant 32 (Bitmask 87)
**Pattern:** N+NE+E+S+W
**Visual:** Dirt on all cardinals + NE corner. Concrete cuts at NW, SE, SW
**Use:** Complex junction with 3 inner corners

## Variant 33 (Bitmask 93)
**Pattern:** E+SE+S+W+N
**Visual:** Dirt on all cardinals + SE corner. Concrete cuts at NE, NW, SW
**Use:** Complex junction with 3 inner corners

## Variant 34 (Bitmask 117)
**Pattern:** S+SW+W+N+E
**Visual:** Dirt on all cardinals + SW corner. Concrete cuts at NW, NE, SE
**Use:** Complex junction with 3 inner corners

## Variant 35 (Bitmask 213)
**Pattern:** W+NW+N+E+S
**Visual:** Dirt on all cardinals + NW corner. Concrete cuts at NE, SE, SW
**Use:** Complex junction with 3 inner corners

## Variant 36 (Bitmask 95)
**Pattern:** N+NE+E+SE+S+W
**Visual:** Dirt on all cardinals + NE and SE corners. Concrete cuts at NW, SW
**Use:** Two inner corners on west side

## Variant 37 (Bitmask 125)
**Pattern:** E+SE+S+SW+W+N
**Visual:** Dirt on all cardinals + SE and SW corners. Concrete cuts at NE, NW
**Use:** Two inner corners on north side

## Variant 38 (Bitmask 245)
**Pattern:** S+SW+W+NW+N+E
**Visual:** Dirt on all cardinals + SW and NW corners. Concrete cuts at NE, SE
**Use:** Two inner corners on east side

## Variant 39 (Bitmask 215)
**Pattern:** W+NW+N+NE+E+S
**Visual:** Dirt on all cardinals + NW and NE corners. Concrete cuts at SE, SW
**Use:** Two inner corners on south side

## Variant 40 (Bitmask 119)
**Pattern:** N+NE+E+SE+S+W (missing SW, NW)
**Visual:** Dirt on all cardinals + NE and SE. Concrete cuts at NW, SW
**Use:** Two opposite inner corners (diagonal)

## Variant 41 (Bitmask 221)
**Pattern:** W+NW+N+E+SE+S+SW
**Visual:** Dirt on all cardinals + NW, SE, SW. Concrete cut at NE only
**Use:** Single inner corner at NE

## Variant 42 (Bitmask 127)
**Pattern:** N+NE+E+SE+S+SW+W
**Visual:** Dirt on all cardinals + NE, SE, SW. Concrete cut at NW only
**Use:** Single inner corner at NW

## Variant 43 (Bitmask 253)
**Pattern:** E+SE+S+SW+W+NW+N
**Visual:** Dirt on all cardinals + SE, SW, NW. Concrete cut at NE only
**Use:** Single inner corner at NE

## Variant 44 (Bitmask 247)
**Pattern:** S+SW+W+NW+N+NE+E
**Visual:** Dirt on all cardinals + SW, NW, NE. Concrete cut at SE only
**Use:** Single inner corner at SE

## Variant 45 (Bitmask 223)
**Pattern:** W+NW+N+NE+E+SE+S
**Visual:** Dirt on all cardinals + NW, NE, SE. Concrete cut at SW only
**Use:** Single inner corner at SW

## Variant 46 (Bitmask 255)
**Pattern:** All 8 neighbors filled
**Visual:** Completely filled with dirt, no concrete visible
**Use:** Center of large dirt blob

---

## How to Verify:

For each variant number (0-46), check that your sprite matches the description above. The key things to verify:

1. **Which edges have dirt extending to them** (N/S/E/W)
2. **Which corners have dirt** (NE/NW/SE/SW)
3. **Where concrete shows through** (cuts/gaps)

If any sprite doesn't match its description, let me know the variant number and I'll help identify the issue.
