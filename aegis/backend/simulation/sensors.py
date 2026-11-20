"""
Simulated sensor suite.

All sensors read from the same ground-truth Environment/Robot state, but
each applies its own noise model and field of view so the frontend gets
realistically imperfect data rather than omniscient ground truth.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import List, Tuple

from simulation.environment import Environment
from simulation.robot import Robot


@dataclass
class LidarConfig:
    range_m: float = 8.0
    num_rays: int = 36
    noise_std: float = 0.03


def raycast(env: Environment, x: float, y: float, angle_deg: float, max_range: float, step: float = 0.05) -> float:
    """March a ray outward from (x, y) until it hits an obstacle, the
    world boundary, or exceeds max_range."""
    rad = math.radians(angle_deg)
    dx, dy = math.cos(rad), math.sin(rad)
    dist = 0.0
    while dist < max_range:
        px, py = x + dx * dist, y + dy * dist
        if not env.in_bounds(px, py):
            return round(dist, 3)
        for obs in env.obstacles:
            if (px - obs.x) ** 2 + (py - obs.y) ** 2 <= obs.radius ** 2:
                return round(dist, 3)
        dist += step
    return round(max_range, 3)


def simulate_lidar(env: Environment, robot: Robot, cfg: LidarConfig) -> Tuple[List[float], List[float]]:
    angles = [i * (360.0 / cfg.num_rays) for i in range(cfg.num_rays)]
    ranges = []
    for a in angles:
        world_angle = (robot.heading_deg + a) % 360
        r = raycast(env, robot.x, robot.y, world_angle, cfg.range_m)
        if cfg.noise_std > 0:
            r = max(0.0, r + random.gauss(0, cfg.noise_std))
        ranges.append(round(r, 3))
    return ranges, angles


def simulate_ultrasonic(env: Environment, robot: Robot, max_range: float = 10.0) -> dict:
    directions = {"front": 0, "left": 90, "right": -90, "rear": 180}
    result = {}
    for name, offset in directions.items():
        world_angle = (robot.heading_deg + offset) % 360
        r = raycast(env, robot.x, robot.y, world_angle, max_range)
        result[name] = round(max(0.0, r + random.gauss(0, 0.05)), 2)
    return result


def simulate_gps(robot: Robot, accuracy_m: float = 0.15) -> Tuple[float, float, float]:
    noisy_x = robot.x + random.gauss(0, accuracy_m / 3)
    noisy_y = robot.y + random.gauss(0, accuracy_m / 3)
    return round(noisy_x, 3), round(noisy_y, 3), accuracy_m


def simulate_imu(robot: Robot, dt: float) -> Tuple[float, float, float]:
    heading = round(robot.heading_deg + random.gauss(0, 0.2), 2)
    angular_velocity = round(robot.angular_velocity_dps(dt) + random.gauss(0, 0.5), 2)
    acceleration = round(robot.acceleration_mps2 + random.gauss(0, 0.05), 3)
    return heading, angular_velocity, acceleration
