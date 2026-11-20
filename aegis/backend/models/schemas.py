"""
Shared Pydantic models for AEGIS backend.

These describe the wire format between the FastAPI backend and the React
frontend (both REST responses and WebSocket telemetry frames).
"""
from __future__ import annotations

from enum import Enum
from typing import List, Optional, Tuple

from pydantic import BaseModel, Field


# --------------------------------------------------------------------------
# Enums
# --------------------------------------------------------------------------

class RobotState(str, Enum):
    IDLE = "IDLE"
    PLANNING = "PLANNING"
    NAVIGATING = "NAVIGATING"
    OBSTACLE_DETECTED = "OBSTACLE_DETECTED"
    REPLANNING = "REPLANNING"
    PAUSED = "PAUSED"
    MISSION_COMPLETE = "MISSION_COMPLETE"
    EMERGENCY_STOP = "EMERGENCY_STOP"
    FAULT = "FAULT"


class LogSeverity(str, Enum):
    INFO = "INFO"
    SUCCESS = "SUCCESS"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class EnvironmentPreset(str, Enum):
    OPEN_FIELD = "open_field"
    WAREHOUSE = "warehouse"
    MAZE = "maze"
    URBAN_GRID = "urban_grid"


# --------------------------------------------------------------------------
# Simple geometry / grid types
# --------------------------------------------------------------------------

class GridCell(BaseModel):
    x: int
    y: int


class WorldPoint(BaseModel):
    x: float
    y: float


# --------------------------------------------------------------------------
# Requests
# --------------------------------------------------------------------------

class SetDestinationRequest(BaseModel):
    x: float
    y: float


class AddObstacleRequest(BaseModel):
    x: float
    y: float
    radius: float = Field(default=0.6, ge=0.1, le=5.0)


class ManualControlRequest(BaseModel):
    """Direction is a semantic command, not raw motor values, so the
    frontend never has to know about the controller internals."""
    command: str  # forward | reverse | left | right | stop


class SetEnvironmentRequest(BaseModel):
    preset: EnvironmentPreset


class SetSpeedRequest(BaseModel):
    multiplier: float = Field(ge=0.1, le=10.0)


class LidarConfigRequest(BaseModel):
    range_m: float = Field(ge=1.0, le=30.0)
    num_rays: int = Field(ge=8, le=180)
    noise_std: float = Field(ge=0.0, le=1.0)


# --------------------------------------------------------------------------
# Responses
# --------------------------------------------------------------------------

class PathPlanResult(BaseModel):
    status: str
    algorithm: str = "A*"
    waypoints: List[WorldPoint]
    path_length_m: float
    estimated_time_s: float
    planning_time_ms: float


class SensorFrame(BaseModel):
    lidar_ranges: List[float]
    lidar_angles: List[float]
    ultrasonic_front: float
    ultrasonic_left: float
    ultrasonic_right: float
    ultrasonic_rear: float
    gps_x: float
    gps_y: float
    gps_accuracy_m: float
    imu_heading_deg: float
    imu_angular_velocity_dps: float
    imu_acceleration_mps2: float


class RobotTelemetry(BaseModel):
    x: float
    y: float
    heading_deg: float
    velocity_mps: float
    acceleration_mps2: float
    battery_pct: float
    state: RobotState
    current_waypoint_index: int
    total_waypoints: int
    obstacle_count: int


class LogEntry(BaseModel):
    timestamp: str
    severity: LogSeverity
    source: str
    message: str


class DetectionBox(BaseModel):
    label: str
    confidence: float
    x: int
    y: int
    width: int
    height: int


class VisionResult(BaseModel):
    model: str
    objects: List[DetectionBox]
    inference_time_ms: float
    frame_width: int
    frame_height: int


class SystemHealth(BaseModel):
    simulation_engine: str
    navigation: str
    sensor_system: str
    vision: str
    websocket: str
    backend_api: str
    backend_latency_ms: float
    ws_latency_ms: float
    simulation_tick_rate_hz: float
    active_connections: int
