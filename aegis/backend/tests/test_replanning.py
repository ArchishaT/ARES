import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from simulation.environment import Environment
from navigation.planner import plan_route, path_is_blocked


def test_plan_route_success_open_field():
    env = Environment(width_m=20, height_m=20)
    result = plan_route(env, (1, 1), (15, 15))
    assert result.success is True
    assert len(result.waypoints) >= 2
    assert result.path_length_m > 0
    assert result.waypoints[0] == (1, 1)
    assert result.waypoints[-1] == (15, 15)


def test_plan_route_fails_when_goal_surrounded():
    env = Environment(width_m=20, height_m=20, cell_size_m=0.5)
    # Encircle the goal completely with obstacles.
    import math
    gx, gy = 10, 10
    for angle in range(0, 360, 10):
        rad = math.radians(angle)
        env.add_obstacle(gx + 0.9 * math.cos(rad), gy + 0.9 * math.sin(rad), radius=0.4)
    result = plan_route(env, (1, 1), (gx, gy))
    assert result.success is False


def test_path_is_blocked_detects_new_obstacle_on_route():
    env = Environment(width_m=20, height_m=20)
    result = plan_route(env, (1, 1), (15, 1))
    assert result.success is True
    # Place an obstacle directly on the route's straight-line path.
    env.add_obstacle(7, 1, radius=0.8, dynamic=True)
    assert path_is_blocked(env, result.waypoints, 0, lookahead=len(result.waypoints)) is True


def test_path_is_blocked_false_when_clear():
    env = Environment(width_m=20, height_m=20)
    result = plan_route(env, (1, 1), (15, 1))
    assert path_is_blocked(env, result.waypoints, 0, lookahead=len(result.waypoints)) is False


def test_replan_finds_detour_around_new_obstacle():
    env = Environment(width_m=20, height_m=20)
    first = plan_route(env, (1, 1), (15, 1))
    assert first.success is True
    env.add_obstacle(7, 1, radius=1.0, dynamic=True)
    second = plan_route(env, (1, 1), (15, 1))
    assert second.success is True
    # The detour must be longer than the original straight-line path.
    assert second.path_length_m >= first.path_length_m
