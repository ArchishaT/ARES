"""
Robot model: pose, velocity, battery, and the mission state machine.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, Tuple

from models.schemas import RobotState

# Legal state transitions. Anything not listed here is rejected by
# `Robot.transition_to`, which keeps the state machine from drifting into
# nonsensical states under bugs elsewhere in the system.
_TRANSITIONS = {
    RobotState.IDLE: {RobotState.PLANNING, RobotState.FAULT},
    RobotState.PLANNING: {RobotState.NAVIGATING, RobotState.IDLE, RobotState.FAULT},
    RobotState.NAVIGATING: {
        RobotState.OBSTACLE_DETECTED,
        RobotState.PAUSED,
        RobotState.MISSION_COMPLETE,
        RobotState.EMERGENCY_STOP,
        RobotState.FAULT,
        RobotState.IDLE,
    },
    RobotState.OBSTACLE_DETECTED: {RobotState.REPLANNING, RobotState.EMERGENCY_STOP, RobotState.FAULT},
    RobotState.REPLANNING: {RobotState.NAVIGATING, RobotState.IDLE, RobotState.EMERGENCY_STOP, RobotState.FAULT},
    RobotState.PAUSED: {RobotState.NAVIGATING, RobotState.IDLE, RobotState.EMERGENCY_STOP},
    RobotState.MISSION_COMPLETE: {RobotState.IDLE, RobotState.PLANNING},
    RobotState.EMERGENCY_STOP: {RobotState.IDLE},
    RobotState.FAULT: {RobotState.IDLE},
}


@dataclass
class Robot:
    x: float = 3.0
    y: float = 3.0
    heading_deg: float = 0.0
    velocity_mps: float = 0.0
    acceleration_mps2: float = 0.0
    battery_pct: float = 100.0
    radius_m: float = 0.3
    max_speed_mps: float = 2.5
    max_accel_mps2: float = 1.5
    max_turn_rate_dps: float = 120.0

    state: RobotState = RobotState.IDLE
    waypoints: List[Tuple[float, float]] = field(default_factory=list)
    current_waypoint_index: int = 0

    # bookkeeping for angular velocity telemetry
    _last_heading_deg: float = 0.0

    def transition_to(self, new_state: RobotState) -> bool:
        allowed = _TRANSITIONS.get(self.state, set())
        if new_state == self.state or new_state in allowed:
            self.state = new_state
            return True
        return False

    def reset(self, x: float = 3.0, y: float = 3.0) -> None:
        self.x = x
        self.y = y
        self.heading_deg = 0.0
        self.velocity_mps = 0.0
        self.acceleration_mps2 = 0.0
        self.battery_pct = 100.0
        self.state = RobotState.IDLE
        self.waypoints = []
        self.current_waypoint_index = 0

    def set_route(self, waypoints: List[Tuple[float, float]]) -> None:
        self.waypoints = waypoints
        self.current_waypoint_index = 0

    def current_target(self) -> Tuple[float, float] | None:
        if not self.waypoints or self.current_waypoint_index >= len(self.waypoints):
            return None
        return self.waypoints[self.current_waypoint_index]

    def advance_waypoint(self) -> bool:
        """Returns True if the mission's final waypoint has been consumed."""
        self.current_waypoint_index += 1
        return self.current_waypoint_index >= len(self.waypoints)

    def angular_velocity_dps(self, dt: float) -> float:
        if dt <= 0:
            return 0.0
        diff = (self.heading_deg - self._last_heading_deg + 540) % 360 - 180
        return diff / dt

    def drain_battery(self, dt: float) -> None:
        # Rough model: idle drain + motion-proportional drain.
        idle_drain = 0.02 * dt
        motion_drain = 0.15 * abs(self.velocity_mps) * dt
        self.battery_pct = max(0.0, self.battery_pct - idle_drain - motion_drain)
