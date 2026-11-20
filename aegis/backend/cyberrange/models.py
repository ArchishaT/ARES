"""
Schemas for the abstracted red-team/blue-team cyber range.

Everything is a scored simulation over data: a "target system" is a
dataclass of hardening parameters, a "technique" is a named entry in a
lookup table with a difficulty score, and the "virtual machine" is an
in-memory process/file list. Nothing here executes code, opens a socket,
or could function as a real tool against a real system.
"""
from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class VulnerabilityType(str, Enum):
    TROJAN = "trojan"
    BACKDOOR = "backdoor"
    TIME_BOMB = "time_bomb"
    WORM = "worm"
    ROOTKIT = "rootkit"


class RedTeamTechnique(str, Enum):
    PORT_SCAN = "port_scan"
    BRUTE_FORCE_LOGIN = "brute_force_login"
    PHISHING_FOOTHOLD = "phishing_foothold"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    LATERAL_MOVEMENT = "lateral_movement"
    DATA_EXFILTRATION = "data_exfiltration"


class SystemConfig(BaseModel):
    os_type: str = "linux"
    patch_level_pct: int = Field(default=70, ge=0, le=100)
    open_ports: List[int] = Field(default_factory=lambda: [22, 80, 443])
    firewall_enabled: bool = False
    ids_enabled: bool = False
    strong_auth_enabled: bool = False
    least_privilege_enabled: bool = False
    network_segmentation_enabled: bool = False


class RedTeamRunRequest(BaseModel):
    system: SystemConfig
    techniques: List[RedTeamTechnique]
    seed: Optional[int] = None


class BlueTeamRunRequest(BaseModel):
    vulnerability: VulnerabilityType
    system: SystemConfig
    defense_budget: int = Field(default=3, ge=1, le=6)  # how many hardening choices they can enable
    duration_ticks: int = Field(default=60, ge=10, le=300)
    seed: Optional[int] = None


class TechniqueResult(BaseModel):
    technique: RedTeamTechnique
    success: bool
    detected: bool
    time_to_outcome_s: float
    stealth_score: float  # 0-100, higher = stealthier
    notes: str


class RedTeamResult(BaseModel):
    system: SystemConfig
    techniques: List[TechniqueResult]
    overall_compromise_pct: float
    mean_time_to_compromise_s: float
    detection_rate_pct: float
    overall_stealth_score: float


class BlueTeamTick(BaseModel):
    tick: int
    event: str
    detected: bool
    mitigated: bool


class BlueTeamResult(BaseModel):
    vulnerability: VulnerabilityType
    system: SystemConfig
    timeline: List[BlueTeamTick]
    mean_time_to_detect_s: Optional[float]
    mean_time_to_mitigate_s: Optional[float]
    breach_occurred: bool
    final_integrity_pct: float
    defense_score_0_100: float


class SessionSummary(BaseModel):
    red: Optional[RedTeamResult] = None
    blue: Optional[BlueTeamResult] = None
