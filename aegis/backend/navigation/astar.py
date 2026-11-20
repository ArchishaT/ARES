"""
A* pathfinding over the environment's occupancy grid.

Standard 8-connected grid search with an octile-distance heuristic, which
is admissible and consistent for 8-connected movement and therefore
guarantees an optimal path on the grid.
"""
from __future__ import annotations

import heapq
import math
from typing import List, Optional, Tuple

Cell = Tuple[int, int]

_NEIGHBORS = [
    (1, 0, 1.0), (-1, 0, 1.0), (0, 1, 1.0), (0, -1, 1.0),
    (1, 1, math.sqrt(2)), (1, -1, math.sqrt(2)),
    (-1, 1, math.sqrt(2)), (-1, -1, math.sqrt(2)),
]


def octile(a: Cell, b: Cell) -> float:
    dx = abs(a[0] - b[0])
    dy = abs(a[1] - b[1])
    return (dx + dy) + (math.sqrt(2) - 2) * min(dx, dy)


def astar(
    grid: List[List[int]],
    start: Cell,
    goal: Cell,
) -> Optional[List[Cell]]:
    """Returns a list of grid cells from start to goal inclusive, or None
    if no path exists."""
    h = len(grid)
    w = len(grid[0]) if h else 0

    def free(c: Cell) -> bool:
        x, y = c
        return 0 <= x < w and 0 <= y < h and grid[y][x] == 0

    if not free(start) or not free(goal):
        return None
    if start == goal:
        return [start]

    open_heap: List[Tuple[float, int, Cell]] = []
    counter = 0
    heapq.heappush(open_heap, (0.0, counter, start))

    came_from: dict[Cell, Cell] = {}
    g_score: dict[Cell, float] = {start: 0.0}
    closed: set[Cell] = set()

    while open_heap:
        _, _, current = heapq.heappop(open_heap)
        if current in closed:
            continue
        if current == goal:
            return _reconstruct(came_from, current)
        closed.add(current)

        for dx, dy, cost in _NEIGHBORS:
            neighbor = (current[0] + dx, current[1] + dy)
            if not free(neighbor) or neighbor in closed:
                continue
            # prevent cutting across obstacle corners on diagonal moves
            if dx != 0 and dy != 0:
                if not free((current[0] + dx, current[1])) or not free((current[0], current[1] + dy)):
                    continue

            tentative_g = g_score[current] + cost
            if tentative_g < g_score.get(neighbor, math.inf):
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                f = tentative_g + octile(neighbor, goal)
                counter += 1
                heapq.heappush(open_heap, (f, counter, neighbor))

    return None


def _reconstruct(came_from: dict, current: Cell) -> List[Cell]:
    path = [current]
    while current in came_from:
        current = came_from[current]
        path.append(current)
    path.reverse()
    return path


def simplify_path(path: List[Cell]) -> List[Cell]:
    """Collapse collinear runs of cells into corner waypoints only, so the
    controller doesn't need to stop-and-check at every single grid cell."""
    if len(path) <= 2:
        return path
    simplified = [path[0]]
    for i in range(1, len(path) - 1):
        prev, cur, nxt = path[i - 1], path[i], path[i + 1]
        d1 = (cur[0] - prev[0], cur[1] - prev[1])
        d2 = (nxt[0] - cur[0], nxt[1] - cur[1])
        if d1 != d2:
            simplified.append(cur)
    simplified.append(path[-1])
    return simplified
