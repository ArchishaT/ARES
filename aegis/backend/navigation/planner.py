"""
High-level path planner: converts world coordinates to the occupancy
grid, runs A*, simplifies the result, and packages metrics for the UI.
"""
from __future__ import annotations

import math
import time
from dataclasses import dataclass
from typing import List, Optional, Tuple

from navigation.astar import astar, simplify_path
from simulation.environment import Environment

AVERAGE_TRAVEL_SPEED_MPS = 1.4


@dataclass
class PlanResult:
    success: bool
    waypoints: List[Tuple[float, float]]
    path_length_m: float
    estimated_time_s: float
    planning_time_ms: float
    reason: Optional[str] = None


def plan_route(env: Environment, start: Tuple[float, float], goal: Tuple[float, float]) -> PlanResult:
    t0 = time.perf_counter()

    start_cell = env.world_to_cell(*start)
    goal_cell = env.world_to_cell(*goal)

    grid = env.grid()
    cell_path = astar(grid, start_cell, goal_cell)
    planning_time_ms = (time.perf_counter() - t0) * 1000.0

    if cell_path is None:
        return PlanResult(
            success=False,
            waypoints=[],
            path_length_m=0.0,
            estimated_time_s=0.0,
            planning_time_ms=round(planning_time_ms, 2),
            reason="No traversable path to destination.",
        )

    simplified = simplify_path(cell_path)
    world_points = [env.cell_to_world(cx, cy) for cx, cy in simplified]
    # Always terminate exactly at the requested goal, not the cell center.
    world_points[-1] = goal
    world_points[0] = start

    length = 0.0
    for i in range(1, len(world_points)):
        length += math.dist(world_points[i - 1], world_points[i])

    return PlanResult(
        success=True,
        waypoints=world_points,
        path_length_m=round(length, 2),
        estimated_time_s=round(length / AVERAGE_TRAVEL_SPEED_MPS, 1),
        planning_time_ms=round(planning_time_ms, 2),
    )


def path_is_blocked(env: Environment, waypoints: List[Tuple[float, float]], from_index: int, lookahead: int = 6) -> bool:
    """Checks whether the remaining route (from the robot's current
    waypoint onward) intersects any obstacle. Used to decide whether a
    newly-placed obstacle actually invalidates the active route, rather
    than replanning on every obstacle addition regardless of relevance."""
    remaining = waypoints[from_index: from_index + lookahead + 1]
    for i in range(len(remaining) - 1):
        if _segment_hits_obstacle(env, remaining[i], remaining[i + 1]):
            return True
    return False


def _segment_hits_obstacle(env: Environment, a: Tuple[float, float], b: Tuple[float, float], step: float = 0.2) -> bool:
    dist = math.dist(a, b)
    steps = max(1, int(dist / step))
    for i in range(steps + 1):
        t = i / steps
        x = a[0] + (b[0] - a[0]) * t
        y = a[1] + (b[1] - a[1]) * t
        for obs in env.obstacles:
            if (x - obs.x) ** 2 + (y - obs.y) ** 2 <= (obs.radius + 0.35) ** 2:
                return True
    return False
