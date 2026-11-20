"""
Waypoint-following controller.

A lightweight PID-style controller that steers the robot's heading toward
the current waypoint and modulates forward speed based on heading error
and proximity to the target. This is intentionally simple (P-dominant
with a small D term on heading error) rather than a full PID with integral
windup handling, which would be overkill for a kinematic point-robot in a
simulated environment.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

WAYPOINT_ARRIVAL_RADIUS_M = 0.45


@dataclass
class ControlOutput:
    target_speed_mps: float
    target_heading_deg: float
    arrived: bool


class WaypointController:
    def __init__(self, kp_heading: float = 2.2, kd_heading: float = 0.4):
        self.kp_heading = kp_heading
        self.kd_heading = kd_heading
        self._prev_heading_error = 0.0

    def compute(
        self,
        x: float,
        y: float,
        heading_deg: float,
        target: tuple[float, float],
        max_speed_mps: float,
    ) -> ControlOutput:
        dx = target[0] - x
        dy = target[1] - y
        distance = math.hypot(dx, dy)

        if distance <= WAYPOINT_ARRIVAL_RADIUS_M:
            return ControlOutput(target_speed_mps=0.0, target_heading_deg=heading_deg, arrived=True)

        target_heading = math.degrees(math.atan2(dy, dx)) % 360
        heading_error = (target_heading - heading_deg + 540) % 360 - 180

        # Slow down sharply when a big turn is needed; this is the fix for
        # the controller-overshoot contribution to the oscillation bug
        # described in the README (the robot used to barrel through
        # waypoints too fast to correct heading, overshoot the waypoint
        # radius, and immediately re-trigger a "missed waypoint" replan).
        turn_penalty = max(0.15, 1.0 - abs(heading_error) / 90.0)
        distance_penalty = min(1.0, distance / 2.0)
        target_speed = max_speed_mps * turn_penalty * distance_penalty
        target_speed = max(target_speed, 0.3 * max_speed_mps * turn_penalty)

        self._prev_heading_error = heading_error
        return ControlOutput(
            target_speed_mps=target_speed,
            target_heading_deg=target_heading,
            arrived=False,
        )
