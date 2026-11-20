"""
REST API routes for the ARES security layer (attack/defense simulation
and comparison scoring). Mounted at /api/security.
"""
from __future__ import annotations

from fastapi import APIRouter

from security.engine import run_comparison
from security.models import ComparisonResult, ScenarioConfig

router = APIRouter()


@router.post("/security/run-comparison", response_model=ComparisonResult)
def run_security_comparison(scenario: ScenarioConfig) -> ComparisonResult:
    unsecured, secured, ev_u, ev_s = run_comparison(scenario)
    return ComparisonResult(
        scenario=scenario,
        unsecured=unsecured,
        secured=secured,
        events_unsecured=ev_u,
        events_secured=ev_s,
    )


@router.get("/security/attack-types")
def list_attack_types() -> dict:
    from security.models import AttackType
    return {
        "attacks": [
            {"id": "sensor_spoofing", "label": "Sensor / Telemetry Spoofing",
             "description": "Falsified GPS/IMU readings injected into the telemetry stream."},
            {"id": "unauthorized_command", "label": "Unauthorized Command",
             "description": "A navigation command injected with no valid credentials."},
            {"id": "replay_attack", "label": "Replayed Command",
             "description": "A previously valid command resent later with a stale nonce/timestamp."},
            {"id": "compromised_channel", "label": "Compromised Communication Channel",
             "description": "Man-in-the-middle tampering with an in-flight message after signing."},
            {"id": "malicious_nav_injection", "label": "Malicious Navigation Injection",
             "description": "Direct overwrite of the active waypoint/destination."},
            {"id": "dos_flood", "label": "Denial of Service Flood",
             "description": "A burst of junk commands intended to exhaust the control channel."},
        ]
    }
