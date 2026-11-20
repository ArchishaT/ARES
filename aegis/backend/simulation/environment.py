"""
Grid-based environment representation.

The world is modelled as a continuous metric space (metres) that is
rasterised onto a discrete occupancy grid for path planning. Each cell is
either free (0) or occupied (1). Obstacles are stored both as grid cells
(for A*) and as circles in world space (for continuous collision checks
against the rover and sensors), so the two representations never drift
apart.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import List, Tuple

from models.schemas import EnvironmentPreset

FREE = 0
OBSTACLE = 1


@dataclass
class Obstacle:
    x: float
    y: float
    radius: float = 0.6
    dynamic: bool = True  # user/runtime-placed obstacles vs. preset walls


@dataclass
class Environment:
    width_m: float = 30.0
    height_m: float = 20.0
    cell_size_m: float = 0.5
    obstacles: List[Obstacle] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.grid_w = int(self.width_m / self.cell_size_m)
        self.grid_h = int(self.height_m / self.cell_size_m)
        self._grid = [[FREE for _ in range(self.grid_w)] for _ in range(self.grid_h)]

    # -- coordinate conversions ------------------------------------------------
    def world_to_cell(self, x: float, y: float) -> Tuple[int, int]:
        cx = int(max(0, min(self.grid_w - 1, x / self.cell_size_m)))
        cy = int(max(0, min(self.grid_h - 1, y / self.cell_size_m)))
        return cx, cy

    def cell_to_world(self, cx: int, cy: int) -> Tuple[float, float]:
        return (cx + 0.5) * self.cell_size_m, (cy + 0.5) * self.cell_size_m

    def in_bounds(self, x: float, y: float) -> bool:
        return 0 <= x <= self.width_m and 0 <= y <= self.height_m

    # -- obstacle management -----------------------------------------------
    def add_obstacle(self, x: float, y: float, radius: float = 0.6, dynamic: bool = True) -> Obstacle:
        obs = Obstacle(x=x, y=y, radius=radius, dynamic=dynamic)
        self.obstacles.append(obs)
        self._rasterize_obstacle(obs)
        return obs

    def clear_dynamic_obstacles(self) -> None:
        self.obstacles = [o for o in self.obstacles if not o.dynamic]
        self._rebuild_grid()

    def clear_all(self) -> None:
        self.obstacles = []
        self._rebuild_grid()

    def _rebuild_grid(self) -> None:
        self._grid = [[FREE for _ in range(self.grid_w)] for _ in range(self.grid_h)]
        for obs in self.obstacles:
            self._rasterize_obstacle(obs)

    def _rasterize_obstacle(self, obs: Obstacle, inflation_m: float = 0.35) -> None:
        """Mark grid cells covered by the obstacle as occupied.

        `inflation_m` grows the obstacle footprint slightly beyond its
        physical radius. This is the fix for the oscillating-replan failure
        documented in the README: without inflation the planner would find
        paths that grazed the obstacle boundary, sensors would then flag
        those cells as unsafe mid-transit, and the robot would bounce
        between two razor-thin "valid" routes.
        """
        r_cells = int((obs.radius + inflation_m) / self.cell_size_m) + 1
        cx, cy = self.world_to_cell(obs.x, obs.y)
        for dy in range(-r_cells, r_cells + 1):
            for dx in range(-r_cells, r_cells + 1):
                gx, gy = cx + dx, cy + dy
                if 0 <= gx < self.grid_w and 0 <= gy < self.grid_h:
                    wx, wy = self.cell_to_world(gx, gy)
                    if (wx - obs.x) ** 2 + (wy - obs.y) ** 2 <= (obs.radius + inflation_m) ** 2:
                        self._grid[gy][gx] = OBSTACLE

    def grid(self) -> List[List[int]]:
        return self._grid

    def is_free_cell(self, cx: int, cy: int) -> bool:
        if not (0 <= cx < self.grid_w and 0 <= cy < self.grid_h):
            return False
        return self._grid[cy][cx] == FREE

    def collides(self, x: float, y: float, robot_radius: float = 0.3) -> bool:
        """Continuous-space collision check used by the physics step."""
        if not self.in_bounds(x, y):
            return True
        for obs in self.obstacles:
            dist2 = (x - obs.x) ** 2 + (y - obs.y) ** 2
            if dist2 <= (obs.radius + robot_radius) ** 2:
                return True
        return False

    def nearest_obstacle_distance(self, x: float, y: float) -> float:
        if not self.obstacles:
            return float("inf")
        return min(
            ((x - o.x) ** 2 + (y - o.y) ** 2) ** 0.5 - o.radius for o in self.obstacles
        )


def build_preset(preset: EnvironmentPreset) -> Environment:
    """Factory for the four environment presets requested in the spec."""
    if preset == EnvironmentPreset.OPEN_FIELD:
        env = Environment(width_m=30, height_m=20)
        rng = random.Random(7)
        for _ in range(4):
            env.add_obstacle(rng.uniform(6, 24), rng.uniform(4, 16), radius=0.8, dynamic=False)
        return env

    if preset == EnvironmentPreset.WAREHOUSE:
        env = Environment(width_m=30, height_m=20)
        # Shelving rows made of chained circular obstacles.
        for row_y in (4, 8, 12, 16):
            for x in range(4, 26, 2):
                if 12 <= x <= 14:  # aisle gap
                    continue
                env.add_obstacle(x, row_y, radius=0.55, dynamic=False)
        return env

    if preset == EnvironmentPreset.MAZE:
        env = Environment(width_m=30, height_m=20)
        # A simple hand-authored maze of wall segments.
        walls = [
            (6, y) for y in range(2, 16)
        ] + [
            (12, y) for y in range(4, 20)
        ] + [
            (18, y) for y in range(0, 14)
        ] + [
            (24, y) for y in range(4, 18)
        ]
        for x, y in walls:
            env.add_obstacle(x, y, radius=0.5, dynamic=False)
        return env

    if preset == EnvironmentPreset.URBAN_GRID:
        env = Environment(width_m=30, height_m=20)
        for bx in range(4, 27, 6):
            for by in range(3, 18, 6):
                for x in range(bx, bx + 3):
                    for y in range(by, by + 3):
                        env.add_obstacle(x, y, radius=0.5, dynamic=False)
        return env

    return Environment()
