import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from navigation.astar import astar, simplify_path


def make_grid(w, h):
    return [[0 for _ in range(w)] for _ in range(h)]


def test_straight_line_path_open_grid():
    grid = make_grid(10, 10)
    path = astar(grid, (0, 0), (5, 0))
    assert path is not None
    assert path[0] == (0, 0)
    assert path[-1] == (5, 0)


def test_no_path_when_goal_is_obstacle():
    grid = make_grid(5, 5)
    grid[2][2] = 1
    path = astar(grid, (0, 0), (2, 2))
    assert path is None


def test_path_avoids_wall():
    grid = make_grid(7, 7)
    for y in range(6):
        grid[y][3] = 1  # vertical wall with a gap at the bottom row
    path = astar(grid, (0, 0), (6, 0))
    assert path is not None
    for (x, y) in path:
        assert grid[y][x] == 0


def test_start_equals_goal():
    grid = make_grid(3, 3)
    path = astar(grid, (1, 1), (1, 1))
    assert path == [(1, 1)]


def test_diagonal_move_blocked_by_corner_obstacles():
    grid = make_grid(3, 3)
    grid[0][1] = 1
    grid[1][0] = 1
    path = astar(grid, (0, 0), (1, 1))
    # Direct diagonal cut across two blocked corners must not be allowed;
    # a valid path must exist but not be the 1-step diagonal.
    assert path is None or len(path) > 2


def test_simplify_path_collapses_straight_run():
    path = [(0, 0), (1, 0), (2, 0), (3, 0), (3, 1), (3, 2)]
    simplified = simplify_path(path)
    assert simplified[0] == (0, 0)
    assert simplified[-1] == (3, 2)
    assert len(simplified) < len(path)
