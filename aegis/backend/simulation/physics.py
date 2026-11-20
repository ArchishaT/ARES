"""
Kinematic integration for the rover.

Simple bicycle-free point-robot kinematics: heading turns at a bounded
rate toward a target heading, speed accelerates/decelerates at a bounded
rate toward a target speed, and position integrates via Euler steps. This
is sufficient fidelity for the mission-control simulation without needing
a full dynamics engine.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from simulation.environment import Environment
from simulation.robot import Robot


@dataclass
class StepResult:
    collided: bool
    distance_traveled_m: float


def step_kinematics(
    robot: Robot,
    env: Environment,
    dt: float,
    target_speed_mps: float,
    target_heading_deg: float,
) -> StepResult:
    robot._last_heading_deg = robot.heading_deg

    # Bounded turn rate toward target heading.
    heading_error = (target_heading_deg - robot.heading_deg + 540) % 360 - 180
    max_turn = robot.max_turn_rate_dps * dt
    turn = max(-max_turn, min(max_turn, heading_error))
    robot.heading_deg = (robot.heading_deg + turn) % 360

    # Bounded acceleration toward target speed.
    speed_error = target_speed_mps - robot.velocity_mps
    max_dv = robot.max_accel_mps2 * dt
    dv = max(-max_dv, min(max_dv, speed_error))
    robot.acceleration_mps2 = dv / dt if dt > 0 else 0.0
    robot.velocity_mps = max(0.0, min(robot.max_speed_mps, robot.velocity_mps + dv))

    heading_rad = math.radians(robot.heading_deg)
    dx = math.cos(heading_rad) * robot.velocity_mps * dt
    dy = math.sin(heading_rad) * robot.velocity_mps * dt

    new_x = robot.x + dx
    new_y = robot.y + dy

    if env.collides(new_x, new_y, robot.radius_m):
        # Hard stop on collision rather than clipping through the obstacle.
        robot.velocity_mps = 0.0
        return StepResult(collided=True, distance_traveled_m=0.0)

    robot.x = new_x
    robot.y = new_y
    robot.drain_battery(dt)
    return StepResult(collided=False, distance_traveled_m=math.hypot(dx, dy))
