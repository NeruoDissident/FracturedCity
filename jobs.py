"""Global job queue and basic construction job logic.

This module owns the list of active jobs and provides simple helpers for
adding, assigning, and completing jobs. For now only a single job type is
supported: "construction".

The queue is intentionally minimal so it can later be replaced with a more
sophisticated scheduler without changing callers.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Job:
    """Job anchored at a tile.

    Attributes
    -----------
    type:           Job type (e.g. "construction", "gathering", "haul").
    category:       Job category for grouping (e.g. "harvest", "construction", "wall", "haul").
    x, y:           Target grid coordinates (pickup location for haul jobs).
    z:              Z-level of the job (0=ground, 1=rooftop).
    progress:       Current work progress.
    required:       Work required to finish the job.
    assigned:       Whether a colonist has claimed this job.
    dest_x, dest_y, dest_z: Destination coordinates (for haul/supply jobs).
    """

    type: str
    category: str
    x: int
    y: int
    z: int = 0  # Z-level (0=ground, 1=rooftop)
    progress: int = 0
    required: int = 100
    assigned: bool = False
    wait_timer: int = 0  # Ticks to wait before reassigning (e.g., waiting for materials)
    # Optional extra data for specific job types (e.g. gathering).
    resource_type: str | None = None
    # Destination for haul/supply jobs
    dest_x: int | None = None
    dest_y: int | None = None
    dest_z: int = 0  # Destination Z-level
    # Additional metadata (faction, priority, etc.) can be added later via
    # new fields.


# Global job queue for the prototype. In a larger system this could be owned
# by a world or simulation controller object.
JOB_QUEUE: List[Job] = []

# Designation tracking - tiles that are designated for work but may not have active jobs yet
# Key: (x, y, z), Value: {"type": "harvest"|"salvage"|"haul", "category": str}
# This persists until all work in the designation area is complete
_DESIGNATIONS: dict[tuple[int, int, int], dict] = {}


def add_job(
    job_type: str,
    x: int,
    y: int,
    required: int = 100,
    resource_type: str | None = None,
    category: str | None = None,
    dest_x: int | None = None,
    dest_y: int | None = None,
    dest_z: int = 0,
    z: int = 0,
) -> Job:
    """Create and enqueue a new job.

    Returns the created Job instance.
    """
    # Auto-assign category based on job type if not provided
    if category is None:
        if job_type == "gathering":
            category = "harvest"
        elif job_type == "construction":
            category = "construction"
        elif job_type == "haul":
            category = "haul"
        elif job_type == "supply":
            category = "haul"  # Supply jobs are a type of hauling
        elif job_type == "equip":
            category = "equip"  # Equip jobs are personal - any colonist can do
        elif job_type == "install_furniture":
            category = "construction"
        else:
            category = "misc"
    
    job = Job(
        type=job_type, 
        category=category, 
        x=x, 
        y=y, 
        z=z,
        required=required, 
        resource_type=resource_type,
        dest_x=dest_x,
        dest_y=dest_y,
        dest_z=dest_z,
    )
    JOB_QUEUE.append(job)
    return job


def get_next_job() -> Optional[Job]:
    """Return the next *unassigned* job in the queue, without modifying it.

    This is a simple FIFO scan. If all jobs are assigned or the queue is
    empty, returns None.
    """

    for job in JOB_QUEUE:
        if not job.assigned:
            return job
    return None


def get_next_available_job(
    skip_types: list[str] | None = None,
    skip_unready_construction: bool = False
) -> Optional[Job]:
    """Return the next unassigned job, optionally skipping certain job types.
    
    Does NOT mark the job as assigned - caller must do that.
    
    Args:
        skip_types: List of job types to skip (e.g., ["construction"])
        skip_unready_construction: If True, skip construction jobs that don't
            have all materials delivered yet, or are awaiting stockpile clear
    """
    # Import here to avoid circular import
    if skip_unready_construction:
        from buildings import has_required_materials, is_awaiting_stockpile_clear
    
    if skip_types is None:
        skip_types = []
    
    for job in JOB_QUEUE:
        if job.assigned:
            continue
        if job.wait_timer > 0:
            continue  # Skip jobs that are waiting (e.g., for materials)
        if job.type in skip_types:
            continue
        # Skip construction jobs without materials or awaiting stockpile clear
        if skip_unready_construction and job.type == "construction":
            if not has_required_materials(job.x, job.y, job.z):
                continue
            if is_awaiting_stockpile_clear(job.x, job.y, job.z):
                continue
        return job
    return None


def get_all_available_jobs(
    skip_types: list[str] | None = None,
    skip_unready_construction: bool = False
) -> List[Job]:
    """Return all unassigned jobs that are ready to be worked on.
    
    Args:
        skip_types: List of job types to skip (e.g., ["construction"])
        skip_unready_construction: If True, skip construction jobs that don't
            have all materials delivered yet, or are awaiting stockpile clear
    
    Returns:
        List of available Job objects (not assigned, not waiting)
    """
    # Import here to avoid circular import
    if skip_unready_construction:
        from buildings import has_required_materials, is_awaiting_stockpile_clear
    
    if skip_types is None:
        skip_types = []
    
    available = []
    for job in JOB_QUEUE:
        if job.assigned:
            continue
        if job.wait_timer > 0:
            continue
        if job.type in skip_types:
            continue
        if skip_unready_construction and job.type == "construction":
            if not has_required_materials(job.x, job.y, job.z):
                continue
            if is_awaiting_stockpile_clear(job.x, job.y, job.z):
                continue
        available.append(job)
    
    return available


def update_job_timers() -> None:
    """Tick down wait timers on jobs. Call once per game tick."""
    for job in JOB_QUEUE:
        if job.wait_timer > 0:
            job.wait_timer -= 1


def request_job() -> Optional[Job]:
    """Return and mark the next available job as assigned.

    Used by colonists to claim work. If no unassigned jobs exist, returns None.
    """

    job = get_next_job()
    if job is not None:
        job.assigned = True
    return job


def remove_job(job: Job) -> None:
    """Remove a job from the queue if it is present."""

    if job in JOB_QUEUE:
        JOB_QUEUE.remove(job)


def get_job_at(x: int, y: int, z: int = None) -> Optional[Job]:
    """Return the job located at (x, y, z), if any.

    Assumes at most one job per tile for this prototype.
    
    Args:
        x, y: Tile coordinates
        z: Z-level. If None, matches any Z-level (legacy behavior).
    """
    for job in JOB_QUEUE:
        if job.x == x and job.y == y:
            if z is None or job.z == z:
                return job
    return None


def has_job_of_type_at(x: int, y: int, z: int, job_type: str) -> bool:
    """Check if there's a job of a specific type at (x, y, z)."""
    for job in JOB_QUEUE:
        if job.x == x and job.y == y and job.z == z and job.type == job_type:
            return True
    return False


def remove_job_at(x: int, y: int, z: int = None) -> bool:
    """Remove any job at (x, y, z).
    
    Args:
        x, y: Tile coordinates
        z: Z-level. If None, removes job at any Z-level (legacy behavior).
    
    Returns True if a job was removed.
    """
    job = get_job_at(x, y, z)
    if job is not None:
        # Unassign colonist if assigned
        job.assigned = False
        JOB_QUEUE.remove(job)
        return True
    return False


# --- Save/Load ---

def get_save_state() -> dict:
    """Get jobs state for saving.
    
    Note: We don't save jobs - they're regenerated from world state on load.
    This is simpler and avoids orphaned jobs.
    """
    return {"job_count": len(JOB_QUEUE)}


def load_save_state(state: dict):
    """Restore jobs state from save.
    
    Jobs are cleared on load - they'll be regenerated by the game systems.
    """
    global JOB_QUEUE, _DESIGNATIONS
    JOB_QUEUE.clear()
    _DESIGNATIONS.clear()


# --- Designation System ---

def add_designation(x: int, y: int, z: int, designation_type: str, category: str) -> None:
    """Add a tile to the designation tracking.
    
    Args:
        x, y, z: Tile coordinates
        designation_type: Type of designation (harvest, salvage, haul)
        category: Job category for visual highlighting
    """
    _DESIGNATIONS[(x, y, z)] = {"type": designation_type, "category": category}


def remove_designation(x: int, y: int, z: int) -> bool:
    """Remove a designation from a tile.
    
    Returns True if a designation was removed.
    """
    if (x, y, z) in _DESIGNATIONS:
        del _DESIGNATIONS[(x, y, z)]
        return True
    return False


def has_designation(x: int, y: int, z: int) -> bool:
    """Check if a tile has a designation."""
    return (x, y, z) in _DESIGNATIONS


def get_designation(x: int, y: int, z: int) -> Optional[dict]:
    """Get designation info for a tile, or None if not designated."""
    return _DESIGNATIONS.get((x, y, z))


def get_designation_category(x: int, y: int, z: int) -> Optional[str]:
    """Get the category of a designation at a tile, for visual highlighting."""
    designation = _DESIGNATIONS.get((x, y, z))
    if designation:
        return designation.get("category")
    return None


def clear_all_designations() -> None:
    """Clear all designations (used on game reset/load)."""
    _DESIGNATIONS.clear()
