"""
MissionEngine: the single source of truth for one simulation session.

Ties together the environment, robot, sensors, planner, and controller
into a fixed-timestep tick loop, and owns the robot state machine and
event log. Both the REST API and the WebSocket stream operate on the
same MissionEngine instance so there is exactly one place where
simulation truth lives.
"""
from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Tuple

from models.schemas import EnvironmentPreset, LogSeverity, RobotState
from navigation.controller import WaypointController
from navigation.planner import PlanResult, path_is_blocked, plan_route
from simulation.environment import Environment, build_preset
from simulation.physics import step_kinematics
from simulation.robot import Robot
from simulation.sensors import LidarConfig, simulate_gps, simulate_imu, simulate_lidar, simulate_ultrasonic

TICK_HZ = 20.0
TICK_DT = 1.0 / TICK_HZ
OBSTACLE_CHECK_LOOKAHEAD = 6
REPLAN_COOLDOWN_S = 0.75  # minimum time between consecutive replans


@dataclass
class LogRecord:
    timestamp: str
    severity: LogSeverity
    source: str
    message: str


class MissionEngine:
    def __init__(self) -> None:
        self.env: Environment = build_preset(EnvironmentPreset.OPEN_FIELD)
        self.robot = Robot(x=2.5, y=2.5)
        self.controller = WaypointController()
        self.lidar_cfg = LidarConfig()
        self.destination: Optional[Tuple[float, float]] = None
        self.last_plan: Optional[PlanResult] = None
        self.speed_multiplier: float = 1.0
        self.paused: bool = False
        self.logs: List[LogRecord] = []
        self.sim_time_s: float = 0.0
        self._last_replan_time: float = -999.0
        self._last_tick_wall: float = time.perf_counter()
        self.tick_count: int = 0
        self.mission_count: int = 0

        self.log(LogSeverity.INFO, "SYSTEM", "Mission engine initialized.")

    # -- logging -------------------------------------------------------
    def log(self, severity: LogSeverity, source: str, message: str) -> None:
        self.logs.append(
            LogRecord(
                timestamp=datetime.now().strftime("%H:%M:%S"),
                severity=severity,
                source=source,
                message=message,
            )
        )
        self.logs = self.logs[-300:]

    # -- environment -----------------------------------------------------
    def set_environment(self, preset: EnvironmentPreset) -> None:
        self.env = build_preset(preset)
        self.robot.reset(2.5, 2.5)
        self.destination = None
        self.last_plan = None
        self.log(LogSeverity.INFO, "SIMULATION", f"Environment set to {preset.value}.")

    def add_obstacle(self, x: float, y: float, radius: float = 0.6) -> None:
        self.env.add_obstacle(x, y, radius=radius, dynamic=True)
        self.log(LogSeverity.WARNING, "SENSOR", f"Obstacle detected at ({x:.1f}, {y:.1f}).")
        self._maybe_trigger_replan(reason="obstacle placed on map")

    def reset_simulation(self) -> None:
        self.env.clear_dynamic_obstacles()
        self.robot.reset(2.5, 2.5)
        self.destination = None
        self.last_plan = None
        self.paused = False
        self.sim_time_s = 0.0
        self.log(LogSeverity.INFO, "SYSTEM", "Simulation reset.")

    # -- mission lifecycle -------------------------------------------------
    def set_destination(self, x: float, y: float) -> None:
        self.destination = (x, y)
        self.log(LogSeverity.INFO, "NAVIGATION", f"Destination set to ({x:.1f}, {y:.1f}).")

    def plan_route(self) -> PlanResult:
        if self.destination is None:
            raise ValueError("No destination set.")
        self.robot.transition_to(RobotState.PLANNING)
        result = plan_route(self.env, (self.robot.x, self.robot.y), self.destination)
        self.last_plan = result
        if result.success:
            self.log(
                LogSeverity.SUCCESS,
                "PLANNER",
                f"A* path generated ({result.path_length_m} m, {len(result.waypoints)} waypoints, {result.planning_time_ms} ms).",
            )
            self.robot.set_route(result.waypoints)
        else:
            self.log(LogSeverity.ERROR, "PLANNER", result.reason or "Planning failed.")
            self.robot.transition_to(RobotState.IDLE)
        return result

    def start_mission(self) -> bool:
        if not self.last_plan or not self.last_plan.success:
            self.log(LogSeverity.ERROR, "NAVIGATION", "Cannot start: no valid plan.")
            return False
        if not self.robot.transition_to(RobotState.NAVIGATING):
            self.log(LogSeverity.ERROR, "NAVIGATION", f"Cannot start mission from state {self.robot.state}.")
            return False
        self.paused = False
        self.mission_count += 1
        self.log(LogSeverity.SUCCESS, "ROBOT", "Autonomous navigation started.")
        return True

    def pause_mission(self) -> bool:
        if self.robot.transition_to(RobotState.PAUSED):
            self.paused = True
            self.log(LogSeverity.INFO, "ROBOT", "Mission paused.")
            return True
        return False

    def resume_mission(self) -> bool:
        if self.robot.state == RobotState.PAUSED and self.robot.transition_to(RobotState.NAVIGATING):
            self.paused = False
            self.log(LogSeverity.INFO, "ROBOT", "Mission resumed.")
            return True
        return False

    def abort_mission(self) -> bool:
        if self.robot.transition_to(RobotState.IDLE):
            self.robot.velocity_mps = 0.0
            self.robot.waypoints = []
            self.paused = False
            self.log(LogSeverity.WARNING, "ROBOT", "Mission aborted by operator.")
            return True
        return False

    def emergency_stop(self) -> None:
        self.robot.transition_to(RobotState.EMERGENCY_STOP)
        self.robot.velocity_mps = 0.0
        self.robot.waypoints = []
        self.log(LogSeverity.CRITICAL, "SAFETY", "EMERGENCY STOP triggered.")

    def clear_emergency(self) -> bool:
        if self.robot.state == RobotState.EMERGENCY_STOP and self.robot.transition_to(RobotState.IDLE):
            self.log(LogSeverity.INFO, "SAFETY", "Emergency stop cleared. System reset to IDLE.")
            return True
        return False

    # -- manual control -------------------------------------------------
    def manual_control(self, command: str) -> None:
        if self.robot.state == RobotState.EMERGENCY_STOP:
            return
        if self.robot.state in (RobotState.NAVIGATING, RobotState.REPLANNING, RobotState.PLANNING):
            # manual override cancels the active autonomous mission
            self.robot.transition_to(RobotState.IDLE)
            self.robot.waypoints = []

        step_heading = 8.0
        step_speed = 0.6
        if command == "forward":
            self.robot.velocity_mps = min(self.robot.max_speed_mps, self.robot.velocity_mps + step_speed)
        elif command == "reverse":
            self.robot.velocity_mps = max(-self.robot.max_speed_mps / 2, self.robot.velocity_mps - step_speed)
        elif command == "left":
            self.robot.heading_deg = (self.robot.heading_deg - step_heading) % 360
        elif command == "right":
            self.robot.heading_deg = (self.robot.heading_deg + step_heading) % 360
        elif command == "stop":
            self.robot.velocity_mps = 0.0

    # -- tick loop -------------------------------------------------------
    def tick(self) -> None:
        dt = TICK_DT * self.speed_multiplier
        self.sim_time_s += dt
        self.tick_count += 1

        if self.robot.state in (RobotState.NAVIGATING,) and not self.paused:
            target = self.robot.current_target()
            if target is None:
                self.robot.transition_to(RobotState.MISSION_COMPLETE)
                self.robot.velocity_mps = 0.0
                self.log(LogSeverity.SUCCESS, "NAVIGATION", "Mission complete. Destination reached.")
            else:
                if path_is_blocked(self.env, self.robot.waypoints, self.robot.current_waypoint_index, OBSTACLE_CHECK_LOOKAHEAD):
                    self._maybe_trigger_replan(reason="obstacle intersects active route")
                else:
                    out = self.controller.compute(
                        self.robot.x, self.robot.y, self.robot.heading_deg, target, self.robot.max_speed_mps
                    )
                    step_kinematics(self.robot, self.env, dt, out.target_speed_mps, out.target_heading_deg)
                    if out.arrived:
                        finished = self.robot.advance_waypoint()
                        if finished:
                            self.robot.transition_to(RobotState.MISSION_COMPLETE)
                            self.robot.velocity_mps = 0.0
                            self.log(LogSeverity.SUCCESS, "NAVIGATION", "Mission complete. Destination reached.")
        elif self.robot.state == RobotState.IDLE:
            # IDLE also covers manual-drive mode: integrate whatever
            # velocity/heading manual_control() last set, so W/A/S/D drives
            # actually move the rover instead of only rotating in place.
            step_kinematics(self.robot, self.env, dt, self.robot.velocity_mps, self.robot.heading_deg)
        # PAUSED / MISSION_COMPLETE / EMERGENCY_STOP / FAULT: no movement.

    def _maybe_trigger_replan(self, reason: str) -> None:
        if self.robot.state != RobotState.NAVIGATING:
            return
        if self.sim_time_s - self._last_replan_time < REPLAN_COOLDOWN_S:
            return
        self._last_replan_time = self.sim_time_s

        self.robot.transition_to(RobotState.OBSTACLE_DETECTED)
        self.log(LogSeverity.WARNING, "SENSOR", f"Obstacle detected ({reason}).")
        self.log(LogSeverity.WARNING, "NAVIGATION", "Current path invalidated.")

        self.robot.transition_to(RobotState.REPLANNING)
        self.log(LogSeverity.INFO, "PLANNER", "Replanning route...")
        result = plan_route(self.env, (self.robot.x, self.robot.y), self.destination)
        self.last_plan = result

        if result.success:
            self.robot.set_route(result.waypoints)
            self.robot.transition_to(RobotState.NAVIGATING)
            self.log(
                LogSeverity.SUCCESS,
                "NAVIGATION",
                f"New route confirmed ({result.path_length_m} m, {len(result.waypoints)} waypoints).",
            )
        else:
            self.robot.transition_to(RobotState.FAULT)
            self.log(LogSeverity.ERROR, "PLANNER", "Replanning failed: no valid route to destination.")

    # -- sensor / telemetry snapshots -------------------------------------
    def sensor_frame(self) -> dict:
        ranges, angles = simulate_lidar(self.env, self.robot, self.lidar_cfg)
        ultrasonic = simulate_ultrasonic(self.env, self.robot)
        gx, gy, gacc = simulate_gps(self.robot)
        heading, ang_vel, accel = simulate_imu(self.robot, TICK_DT)
        return {
            "lidar_ranges": ranges,
            "lidar_angles": angles,
            "ultrasonic_front": ultrasonic["front"],
            "ultrasonic_left": ultrasonic["left"],
            "ultrasonic_right": ultrasonic["right"],
            "ultrasonic_rear": ultrasonic["rear"],
            "gps_x": gx,
            "gps_y": gy,
            "gps_accuracy_m": gacc,
            "imu_heading_deg": heading,
            "imu_angular_velocity_dps": ang_vel,
            "imu_acceleration_mps2": accel,
        }

    def telemetry(self) -> dict:
        return {
            "x": round(self.robot.x, 3),
            "y": round(self.robot.y, 3),
            "heading_deg": round(self.robot.heading_deg, 1),
            "velocity_mps": round(self.robot.velocity_mps, 3),
            "acceleration_mps2": round(self.robot.acceleration_mps2, 3),
            "battery_pct": round(self.robot.battery_pct, 1),
            "state": self.robot.state.value,
            "current_waypoint_index": self.robot.current_waypoint_index,
            "total_waypoints": len(self.robot.waypoints),
            "obstacle_count": len(self.env.obstacles),
        }

    def recent_logs(self, limit: int = 50) -> List[dict]:
        return [
            {"timestamp": r.timestamp, "severity": r.severity.value, "source": r.source, "message": r.message}
            for r in self.logs[-limit:]
        ]
