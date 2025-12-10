"""Configuration values and global settings for the colony prototype.

This module centralizes tuning parameters (sizes, counts, and colors) so
simulation systems and rendering can share a single source of truth.
"""

# --- GRID / SCREEN ------------------------------------------------------------

TILE_SIZE = 32
# Grid dimensions (tiles) - LARGE MAP
GRID_W = 200
GRID_H = 200
GRID_Z = 3  # Number of Z-levels (0 = ground, 1 = first floor, 2 = second floor)

# Screen dimensions - FULL HD (increase for 4K monitors)
SCREEN_W = 1920
SCREEN_H = 1080

# --- SIMULATION ---------------------------------------------------------------

COLONIST_COUNT = 10

COLOR_BG_NORMAL = (20, 20, 20)
COLOR_BG_ETHER = (15, 0, 25)

COLOR_GRID_LINES = (40, 70, 80)  # Teal-tinted grid lines to match UI
COLOR_TILE_SELECTED = (80, 120, 255)
COLOR_TILE_BUILDING = (200, 180, 60)
COLOR_TILE_FINISHED_BUILDING = (170, 150, 40)
COLOR_TILE_WALL = (100, 100, 110)           # planned wall (under construction)
COLOR_TILE_FINISHED_WALL = (80, 80, 90)     # completed wall
COLOR_TILE_STREET = (50, 52, 58)            # medium cool gray for city streets
COLOR_TILE_STREET_DESIGNATED = (58, 55, 50) # slightly warmer for designated streets
COLOR_TILE_STREET_CRACKED = (45, 47, 52)   # slightly darker cracked asphalt
COLOR_TILE_STREET_SCAR = (40, 40, 46)      # scarred pavement tone
COLOR_TILE_STREET_RIPPED = (32, 32, 38)    # exposed sub-layer for ripped streets
COLOR_TILE_SIDEWALK = (72, 70, 68)          # lighter warm gray for sidewalks (contrast)
COLOR_TILE_SIDEWALK_DESIGNATED = (78, 72, 65) # warmer for designated sidewalks
COLOR_TILE_SCORCHED = (25, 22, 20)          # dark scorched earth from demolished pavement
COLOR_TILE_DEBRIS = (65, 60, 55)            # brownish gray for debris/rubble
COLOR_TILE_WEEDS = (35, 45, 30)             # dark greenish for overgrowth
COLOR_TILE_PROP_BARREL = (70, 50, 40)       # rusty barrel
COLOR_TILE_PROP_SIGN = (60, 65, 70)         # broken sign post
COLOR_TILE_PROP_SCRAP = (75, 70, 65)        # scrap heap
# Natural ground tiles (earth tones)
COLOR_TILE_DIRT = (55, 45, 35)              # brown dirt
COLOR_TILE_GRASS = (40, 55, 35)             # dark grass
COLOR_TILE_ROCK = (50, 50, 55)              # gray rock
COLOR_TILE_EMPTY = (35, 32, 30)             # dark earth tone for empty tiles
COLOR_DRAG_PREVIEW = (100, 150, 255, 100)   # semi-transparent blue for drag rectangle

# Color used for small progress indicators on construction tiles.
COLOR_CONSTRUCTION_PROGRESS = (60, 220, 120)

# Resource node colors by type
COLOR_RESOURCE_NODE_WOOD = (101, 67, 33)     # brown for trees
COLOR_RESOURCE_NODE_SCRAP = (120, 120, 120)  # gray for scrap piles
COLOR_RESOURCE_NODE_MINERAL = (64, 164, 164) # teal for minerals
COLOR_RESOURCE_NODE_METAL = (180, 180, 200)  # silver-blue for refined metal
COLOR_RESOURCE_NODE_POWER = (255, 220, 80)   # yellow for power units
COLOR_RESOURCE_NODE_RAW_FOOD = (180, 220, 100)  # light green for raw food
COLOR_RESOURCE_NODE_COOKED_MEAL = (220, 160, 80)  # orange-brown for cooked meals
COLOR_RESOURCE_NODE_DEFAULT = (120, 100, 80) # fallback

# Resource node state overlay colors (applied as tint)
COLOR_NODE_RESERVED = (255, 200, 100)        # yellow-ish highlight when reserved
COLOR_NODE_IN_PROGRESS = (100, 255, 150)     # green highlight when being harvested
COLOR_NODE_DEPLETED = (50, 50, 50)           # dark gray when depleted

COLOR_RESOURCE_PILE = (140, 160, 180)

# Job category debug border colors
COLOR_JOB_CATEGORY_WALL = (255, 220, 50)       # yellow
COLOR_JOB_CATEGORY_HARVEST = (50, 220, 80)     # green
COLOR_JOB_CATEGORY_CONSTRUCTION = (80, 150, 255)  # blue
COLOR_JOB_CATEGORY_HAUL = (180, 80, 255)       # purple

COLOR_COLONIST_DEFAULT = (200, 80, 255)
COLOR_COLONIST_ETHER = (255, 40, 255)

# Zone colors
COLOR_ZONE_STOCKPILE = (60, 120, 60, 100)  # Semi-transparent green
COLOR_ZONE_STOCKPILE_BORDER = (80, 180, 80)

# UI colors
COLOR_UI_BUTTON = (55, 58, 68)
COLOR_UI_BUTTON_HOVER = (75, 80, 95)
COLOR_UI_BUTTON_ACTIVE = (90, 115, 150)
COLOR_UI_TEXT = (230, 230, 235)
COLOR_UI_PANEL = (35, 38, 48)
