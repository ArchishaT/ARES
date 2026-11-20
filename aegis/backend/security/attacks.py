"""
Simulated attack models.

IMPORTANT: these are abstract behavioral models, not real exploit code.
An "attack" here is a Python function that perturbs an in-memory
dataclass (SimRobotState) -- there is no network I/O, no code execution,
no interaction with any real system. The goal is to model the *effect*
an attack class would have on a robot's command/telemetry pipeline so
that defensive countermeasures can be meaningfully evaluated.
"""
from __future__ import annotations

import random
import time
from dataclasses import dataclass, field
from typing import Optional

from security.models import AttackType


@dataclass
class Message:
    """A single simulated command or telemetry message traveling over the
    robot's (simulated) communication channel."""
    kind: str  # "command" | "telemetry"
    payload: dict
    timestamp: float
    nonce: int
    signature: Optional[str] = None  # present only if authentication is enabled
    tampered: bool = False
    replayed: bool = False
    forged: bool = False


@dataclass
class AttackOutcome:
    attack_type: AttackType
    message: Message
    description: str


_SEEN_NONCES: set[int] = set()


def attack_sensor_spoofing(true_x: float, true_y: float, true_heading: float, nonce: int) -> AttackOutcome:
    """Falsifies a telemetry reading with an implausible jump in position
    or heading -- modeling a spoofed GPS/IMU feed."""
    spoofed_x = true_x + random.uniform(-15, 15)
    spoofed_y = true_y + random.uniform(-15, 15)
    spoofed_heading = (true_heading + random.uniform(90, 270)) % 360
    msg = Message(
        kind="telemetry",
        payload={"x": spoofed_x, "y": spoofed_y, "heading_deg": spoofed_heading},
        timestamp=time.time(),
        nonce=nonce,
        forged=True,
    )
    return AttackOutcome(AttackType.SENSOR_SPOOFING, msg, "Falsified telemetry injected (spoofed position/heading).")


def attack_unauthorized_command(nonce: int) -> AttackOutcome:
    """Injects a navigation command with no valid credentials at all."""
    msg = Message(
        kind="command",
        payload={"command": "set_heading", "value": random.uniform(0, 360)},
        timestamp=time.time(),
        nonce=nonce,
        signature=None,
        forged=True,
    )
    return AttackOutcome(AttackType.UNAUTHORIZED_COMMAND, msg, "Unauthenticated command injected onto control channel.")


def attack_replay(last_legitimate: Optional[Message], nonce: int) -> AttackOutcome:
    """Resends a previously-valid message with a stale nonce/timestamp."""
    if last_legitimate is None:
        base_payload = {"command": "set_heading", "value": 0.0}
        base_sig = "sig-stale"
    else:
        base_payload = dict(last_legitimate.payload)
        base_sig = last_legitimate.signature
    msg = Message(
        kind="command",
        payload=base_payload,
        timestamp=time.time() - 30.0,  # deliberately stale
        nonce=nonce - 1000 if nonce > 1000 else 0,  # reused/old nonce
        signature=base_sig,
        replayed=True,
    )
    return AttackOutcome(AttackType.REPLAY_ATTACK, msg, "Previously valid command replayed with a stale nonce.")


def attack_compromised_channel(legit: Message) -> AttackOutcome:
    """Simulates a man-in-the-middle tampering with an in-flight message:
    the payload is altered after signing, so the signature (if any) no
    longer matches the content."""
    tampered_payload = dict(legit.payload)
    for k, v in tampered_payload.items():
        if isinstance(v, (int, float)):
            tampered_payload[k] = v + random.uniform(50, 150)
    msg = Message(
        kind=legit.kind,
        payload=tampered_payload,
        timestamp=legit.timestamp,
        nonce=legit.nonce,
        signature=legit.signature,  # stale signature over the ORIGINAL payload
        tampered=True,
    )
    return AttackOutcome(AttackType.COMPROMISED_CHANNEL, msg, "In-flight message tampered (MITM) after signing.")


def attack_malicious_nav_injection(nonce: int) -> AttackOutcome:
    """Directly overwrites the active waypoint/destination with an
    attacker-chosen location far from the planned route."""
    msg = Message(
        kind="command",
        payload={"command": "override_waypoint", "x": random.uniform(-50, 50), "y": random.uniform(-50, 50)},
        timestamp=time.time(),
        nonce=nonce,
        forged=True,
    )
    return AttackOutcome(AttackType.MALICIOUS_NAV_INJECTION, msg, "Navigation waypoint maliciously overwritten.")


def attack_dos_flood(nonce: int, count: int = 40) -> AttackOutcome:
    """Floods the command channel with junk commands intended to exhaust
    the controller's processing budget for one tick."""
    msg = Message(
        kind="command",
        payload={"command": "noop_flood", "count": count},
        timestamp=time.time(),
        nonce=nonce,
        forged=True,
    )
    return AttackOutcome(AttackType.DOS_FLOOD, msg, f"Command flood ({count} junk messages) sent in a single tick.")
