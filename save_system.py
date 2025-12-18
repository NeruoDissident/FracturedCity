"""Save and load game state.

Serializes all game state to JSON for persistence.
"""

import json
import os
from datetime import datetime
from typing import Any

SAVE_DIR = "saves"
QUICKSAVE_FILE = "quicksave.json"


def ensure_save_dir():
    """Create saves directory if it doesn't exist."""
    if not os.path.exists(SAVE_DIR):
        os.makedirs(SAVE_DIR)


def get_game_state(grid, colonists, zones_module, buildings_module, resources_module, jobs_module) -> dict:
    """Capture entire game state as a serializable dictionary."""
    
    # Grid state
    depth = getattr(grid, "depth", getattr(grid, "z_levels", 1))
    current_z = getattr(grid, "current_z", 0)
    grid_state = {
        "width": grid.width,
        "height": grid.height,
        "depth": depth,
        "z_levels": depth,
        "current_z": current_z,
        "tiles": {}
    }
    
    # Save non-empty tiles
    for z in range(depth):
        for y in range(grid.height):
            for x in range(grid.width):
                tile = grid.get_tile(x, y, z)
                if tile != "empty":
                    key = f"{x},{y},{z}"
                    grid_state["tiles"][key] = tile
    
    # Colonist state
    colonist_state = []
    for c in colonists:
        colonist_state.append({
            "uid": getattr(c, "uid", None),
            "x": c.x,
            "y": c.y,
            "z": c.z,
            "hunger": c.hunger,
            "health": c.health,
            "is_dead": c.is_dead,
            "state": c.state,
            "capabilities": c.capabilities,
        })
    
    # Zones state
    zones_state = zones_module.get_save_state() if hasattr(zones_module, 'get_save_state') else {}
    
    # Buildings state (construction sites, workstations)
    buildings_state = buildings_module.get_save_state() if hasattr(buildings_module, 'get_save_state') else {}
    
    # Resources state (nodes, items)
    resources_state = resources_module.get_save_state() if hasattr(resources_module, 'get_save_state') else {}
    
    # Jobs state
    jobs_state = jobs_module.get_save_state() if hasattr(jobs_module, 'get_save_state') else {}
    
    # Social state (relationships, conversations)
    # We need to import these modules dynamically or pass them in
    # For now, we'll import them here since they are singletons essentially
    import relationships as relationships_module
    import conversations as conversations_module
    
    relationships_state = relationships_module.get_save_state(colonists)
    conversations_state = conversations_module.get_save_state(colonists)
    
    return {
        "version": 1,
        "timestamp": datetime.now().isoformat(),
        "grid": grid_state,
        "colonists": colonist_state,
        "zones": zones_state,
        "buildings": buildings_state,
        "resources": resources_state,
        "jobs": jobs_state,
        "relationships": relationships_state,
        "conversations": conversations_state,
    }


def save_game(grid, colonists, zones_module, buildings_module, resources_module, jobs_module, filename: str = None) -> str:
    """Save game state to file. Returns the filename used."""
    ensure_save_dir()
    
    if filename is None:
        filename = QUICKSAVE_FILE
    
    filepath = os.path.join(SAVE_DIR, filename)
    
    state = get_game_state(grid, colonists, zones_module, buildings_module, resources_module, jobs_module)
    
    with open(filepath, 'w') as f:
        json.dump(state, f, indent=2)
    
    print(f"[Save] Game saved to {filepath}")
    return filepath


def load_game(grid, colonists, zones_module, buildings_module, resources_module, jobs_module, filename: str = None) -> bool:
    """Load game state from file. Returns True if successful."""
    if filename is None:
        filename = QUICKSAVE_FILE
    
    filepath = os.path.join(SAVE_DIR, filename)
    
    if not os.path.exists(filepath):
        print(f"[Load] No save file found: {filepath}")
        return False
    
    try:
        with open(filepath, 'r') as f:
            state = json.load(f)
        
        # Restore grid
        grid_state = state.get("grid", {})
        depth = getattr(grid, "depth", getattr(grid, "z_levels", 1))
        
        # Clear existing tiles
        for z in range(depth):
            for y in range(grid.height):
                for x in range(grid.width):
                    grid.set_tile(x, y, "empty", z)
        
        # Restore tiles
        for key, tile in grid_state.get("tiles", {}).items():
            parts = key.split(",")
            x, y, z = int(parts[0]), int(parts[1]), int(parts[2])
            if 0 <= z < depth:
                grid.set_tile(x, y, tile, z)
        
        saved_z = grid_state.get("current_z", 0)
        try:
            if hasattr(grid, "set_current_z"):
                grid.set_current_z(saved_z)
            else:
                grid.current_z = saved_z
        except Exception:
            pass
        
        # Restore colonists
        colonist_state = state.get("colonists", [])
        max_uid = 0
        for i, c_state in enumerate(colonist_state):
            if i < len(colonists):
                c = colonists[i]
                if "uid" in c_state and c_state["uid"] is not None:
                    c.uid = c_state["uid"]
                    try:
                        max_uid = max(max_uid, int(c.uid))
                    except Exception:
                        pass
                c.x = c_state.get("x", c.x)
                c.y = c_state.get("y", c.y)
                c.z = c_state.get("z", 0)
                c.hunger = c_state.get("hunger", 0)
                c.health = c_state.get("health", 100)
                c.is_dead = c_state.get("is_dead", False)
                c.state = "idle"  # Reset to idle on load
                c.current_job = None
                c.current_path = []
                c.carrying = None
                if "capabilities" in c_state:
                    c.capabilities = c_state["capabilities"]

        # Advance uid counter to avoid collisions for newly spawned colonists
        try:
            from colonist import Colonist
            if max_uid > 0:
                Colonist._uid_counter = max(Colonist._uid_counter, max_uid + 1)
        except Exception:
            pass
        
        # Restore zones
        if hasattr(zones_module, 'load_save_state'):
            zones_module.load_save_state(state.get("zones", {}))
        
        # Restore buildings
        if hasattr(buildings_module, 'load_save_state'):
            buildings_module.load_save_state(state.get("buildings", {}))
        
        # Restore resources
        if hasattr(resources_module, 'load_save_state'):
            resources_module.load_save_state(state.get("resources", {}))
        
        # Restore jobs
        if hasattr(jobs_module, 'load_save_state'):
            jobs_module.load_save_state(state.get("jobs", {}))
        
        # Restore social state
        import relationships as relationships_module
        import conversations as conversations_module
        
        if hasattr(relationships_module, 'load_save_state'):
            relationships_module.load_save_state(state.get("relationships", {}), colonists)
            
        if hasattr(conversations_module, 'load_save_state'):
            conversations_module.load_save_state(state.get("conversations", {}), colonists)
        
        print(f"[Load] Game loaded from {filepath}")
        return True
        
    except Exception as e:
        print(f"[Load] Error loading save: {e}")
        return False


def quicksave(grid, colonists, zones_module, buildings_module, resources_module, jobs_module):
    """Quick save to default slot."""
    return save_game(grid, colonists, zones_module, buildings_module, resources_module, jobs_module, QUICKSAVE_FILE)


def quickload(grid, colonists, zones_module, buildings_module, resources_module, jobs_module) -> bool:
    """Quick load from default slot."""
    return load_game(grid, colonists, zones_module, buildings_module, resources_module, jobs_module, QUICKSAVE_FILE)
