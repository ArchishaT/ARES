import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from simulation.environment import Environment
from simulation.robot import Robot
from simulation.physics import step_kinematics


def test_no_collision_in_open_space():
    env = Environment(width_m=10, height_m=10)
    assert env.collides(5, 5, robot_radius=0.3) is False


def test_collision_with_obstacle():
    env = Environment(width_m=10, height_m=10)
    env.add_obstacle(5, 5, radius=0.5)
    assert env.collides(5.2, 5.2, robot_radius=0.3) is True


def test_collision_with_out_of_bounds():
    env = Environment(width_m=10, height_m=10)
    assert env.collides(-1, 5, robot_radius=0.3) is True
    assert env.collides(11, 5, robot_radius=0.3) is True


def test_obstacle_rasterized_onto_grid():
    env = Environment(width_m=10, height_m=10, cell_size_m=0.5)
    env.add_obstacle(5, 5, radius=0.6)
    cx, cy = env.world_to_cell(5, 5)
    assert env.is_free_cell(cx, cy) is False


def test_step_kinematics_stops_on_collision():
    env = Environment(width_m=10, height_m=10)
    env.add_obstacle(3.0, 2.0, radius=0.5)
    robot = Robot(x=1.0, y=2.0, heading_deg=0.0)
    robot.velocity_mps = 2.0
    result = None
    for _ in range(200):
        result = step_kinematics(robot, env, dt=0.05, target_speed_mps=2.0, target_heading_deg=0.0)
        if result.collided:
            break
    assert result is not None
    assert result.collided is True


def test_clear_dynamic_obstacles_keeps_static():
    env = Environment(width_m=10, height_m=10)
    env.add_obstacle(2, 2, dynamic=False)
    env.add_obstacle(4, 4, dynamic=True)
    env.clear_dynamic_obstacles()
    assert len(env.obstacles) == 1
    assert env.obstacles[0].dynamic is False
