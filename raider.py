"""Raider System - Hostile NPCs that attack the colony.

Raiders are Colonists with hostile faction settings.
They use all existing colonist systems (combat, body, pathfinding).
"""

import random
from colonist import Colonist, generate_colonist_name
from config import GRID_W, GRID_H


class Raider(Colonist):
    """A hostile colonist that attacks the player's colony."""
    
    def __init__(self, x: int, y: int):
        super().__init__(x, y, color=(200, 60, 60))  # Red tint
        self.name = generate_colonist_name()
        self.faction = "raiders"
        self.is_hostile = True


def spawn_raider_at_edge() -> Raider:
    """Spawn a raider at a random map edge."""
    edge = random.choice(["north", "south", "east", "west"])
    
    if edge == "north":
        x, y = random.randint(10, GRID_W - 10), 5
    elif edge == "south":
        x, y = random.randint(10, GRID_W - 10), GRID_H - 5
    elif edge == "east":
        x, y = GRID_W - 5, random.randint(10, GRID_H - 10)
    else:  # west
        x, y = 5, random.randint(10, GRID_H - 10)
    
    raider = Raider(x, y)
    print(f"[Raiders] {raider.name} appeared at ({x}, {y})!")
    return raider
