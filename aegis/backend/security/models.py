"""
Schemas for the ARES security layer.

Everything here models SIMULATED attacks against the simulated robot: no
real network traffic, no real exploit code, no code that could run
against anything outside this process. Attacks are data-driven behaviors
applied to the in-memory MissionEngine state, exactly like the rest of
the AEGIS simulation.
"""
from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class AttackType(str, Enum):
    SENSOR_SPOOFING = "sensor_spoofing"           # falsified telemetry/sensor values
    UNAUTHORIZED_COMMAND = "unauthorized_command"  # command injected without valid auth
    REPLAY_ATTACK = "replay_attack"                # a previously valid command resent later
    COMPROMISED_CHANNEL = "compromised_channel"     # simulated MITM tampering with messages in transit
    MALICIOUS_NAV_INJECTION = "malicious_nav_injection"  # tampered waypoints/destination
    DOS_FLOOD = "dos_flood"                        # command flood intended to exhaust the controller


class DefenseConfig(BaseModel):
    authentication_enabled: bool = False
    integrity_checks_enabled: bool = False
    anomaly_detection_enabled: bool = False
    rate_limiting_enabled: bool = False
    secure_channel_enabled: bool = False


class ScenarioConfig(BaseModel):
    attacks: List[AttackType] = Field(default_factory=list)
    defenses: DefenseConfig = Field(default_factory=DefenseConfig)
    duration_ticks: int = Field(default=200, ge=20, le=2000)
    attack_intensity: float = Field(default=0.3, ge=0.01, le=1.0)  # probability per tick an active attack fires


class SecurityEventRecord(BaseModel):
    tick: int
    attack_type: Optional[AttackType]
    detected: bool
    blocked: bool
    response_time_ms: float
    description: str


class SecurityMetrics(BaseModel):
    label: str  # "unsecured" | "secured"
    total_attacks: int
    detected_attacks: int
    blocked_attacks: int
    detection_rate_pct: float
    false_positive_count: int
    false_positive_rate_pct: float
    avg_response_time_ms: float
    navigation_degradation_pct: float
    final_position_error_m: float
    commands_accepted: int
    commands_rejected: int


class ComparisonResult(BaseModel):
    scenario: ScenarioConfig
    unsecured: SecurityMetrics
    secured: SecurityMetrics
    events_unsecured: List[SecurityEventRecord]
    events_secured: List[SecurityEventRecord]
