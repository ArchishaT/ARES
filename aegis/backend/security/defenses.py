"""
Defensive countermeasures evaluated against the simulated attacks in
attacks.py. These are real, working implementations of the underlying
techniques (HMAC signing, timestamp/nonce freshness, statistical anomaly
detection, token-bucket rate limiting) -- just applied to the simulated
message objects rather than real network sockets.
"""
from __future__ import annotations

import hashlib
import hmac
import time
from dataclasses import dataclass, field
from typing import Optional

from security.attacks import Message
from security.models import DefenseConfig

SECRET_KEY = b"ares-demo-shared-key-not-for-production"
MAX_CLOCK_SKEW_S = 5.0
ANOMALY_POSITION_JUMP_M = 3.0       # max plausible per-tick position jump
ANOMALY_HEADING_JUMP_DEG = 60.0     # max plausible per-tick heading jump
RATE_LIMIT_PER_TICK = 5             # legitimate commands allowed per tick


def sign(payload: dict, nonce: int, timestamp: float) -> str:
    """HMAC-SHA256 over a canonical representation of the message. Any
    change to payload/nonce/timestamp after signing invalidates it."""
    canonical = f"{sorted(payload.items())}|{nonce}|{timestamp:.3f}".encode()
    return hmac.new(SECRET_KEY, canonical, hashlib.sha256).hexdigest()


def sign_message(msg: Message) -> Message:
    msg.signature = sign(msg.payload, msg.nonce, msg.timestamp)
    return msg


@dataclass
class TokenBucket:
    capacity: int = RATE_LIMIT_PER_TICK
    tokens: float = RATE_LIMIT_PER_TICK

    def allow(self, cost: int = 1) -> bool:
        if self.tokens >= cost:
            self.tokens -= cost
            return True
        return False

    def refill(self) -> None:
        self.tokens = min(self.capacity, self.tokens + self.capacity)


@dataclass
class VerificationResult:
    accepted: bool
    detected: bool          # was this correctly flagged as anomalous/invalid?
    false_positive: bool    # legitimate message incorrectly rejected
    reason: str
    response_time_ms: float


@dataclass
class DefenseLayer:
    config: DefenseConfig
    seen_nonces: set = field(default_factory=set)
    bucket: TokenBucket = field(default_factory=TokenBucket)
    last_trusted_x: float = 0.0
    last_trusted_y: float = 0.0
    last_trusted_heading: float = 0.0

    def reset_tick(self) -> None:
        self.bucket.refill()

    def verify(self, msg: Message, is_actually_malicious: bool) -> VerificationResult:
        t0 = time.perf_counter()

        # -- rate limiting (applies to all command messages) -----------------
        if self.config.rate_limiting_enabled and msg.kind == "command":
            cost = msg.payload.get("count", 1) if msg.payload.get("command") == "noop_flood" else 1
            if not self.bucket.allow(cost):
                elapsed = (time.perf_counter() - t0) * 1000.0
                return VerificationResult(
                    accepted=False,
                    detected=is_actually_malicious,
                    false_positive=not is_actually_malicious,
                    reason="Rejected: rate limit exceeded.",
                    response_time_ms=round(elapsed, 3),
                )

        # -- authentication (signature presence + validity) -------------------
        if self.config.authentication_enabled:
            expected = sign(msg.payload, msg.nonce, msg.timestamp)
            if msg.signature != expected:
                elapsed = (time.perf_counter() - t0) * 1000.0
                return VerificationResult(
                    accepted=False,
                    detected=is_actually_malicious,
                    false_positive=not is_actually_malicious,
                    reason="Rejected: missing or invalid authentication signature.",
                    response_time_ms=round(elapsed, 3),
                )

        # -- integrity / freshness checks (catches tamper + replay) -----------
        if self.config.integrity_checks_enabled:
            if abs(time.time() - msg.timestamp) > MAX_CLOCK_SKEW_S:
                elapsed = (time.perf_counter() - t0) * 1000.0
                return VerificationResult(
                    accepted=False,
                    detected=is_actually_malicious,
                    false_positive=not is_actually_malicious,
                    reason="Rejected: stale timestamp (possible replay).",
                    response_time_ms=round(elapsed, 3),
                )
            if msg.nonce in self.seen_nonces:
                elapsed = (time.perf_counter() - t0) * 1000.0
                return VerificationResult(
                    accepted=False,
                    detected=is_actually_malicious,
                    false_positive=not is_actually_malicious,
                    reason="Rejected: nonce already used (replay detected).",
                    response_time_ms=round(elapsed, 3),
                )

        # -- secure channel (detects post-signing tampering) -------------------
        if self.config.secure_channel_enabled and msg.signature is not None:
            expected = sign(msg.payload, msg.nonce, msg.timestamp)
            if msg.signature != expected:
                elapsed = (time.perf_counter() - t0) * 1000.0
                return VerificationResult(
                    accepted=False,
                    detected=is_actually_malicious,
                    false_positive=not is_actually_malicious,
                    reason="Rejected: integrity mismatch over secure channel (tampering detected).",
                    response_time_ms=round(elapsed, 3),
                )

        # -- anomaly detection (telemetry only: implausible physical jumps) ---
        if self.config.anomaly_detection_enabled and msg.kind == "telemetry":
            dx = abs(msg.payload.get("x", self.last_trusted_x) - self.last_trusted_x)
            dy = abs(msg.payload.get("y", self.last_trusted_y) - self.last_trusted_y)
            dh = abs(((msg.payload.get("heading_deg", self.last_trusted_heading) - self.last_trusted_heading) + 540) % 360 - 180)
            if dx > ANOMALY_POSITION_JUMP_M or dy > ANOMALY_POSITION_JUMP_M or dh > ANOMALY_HEADING_JUMP_DEG:
                elapsed = (time.perf_counter() - t0) * 1000.0
                return VerificationResult(
                    accepted=False,
                    detected=is_actually_malicious,
                    false_positive=not is_actually_malicious,
                    reason="Rejected: telemetry anomaly (implausible state jump).",
                    response_time_ms=round(elapsed, 3),
                )

        self.seen_nonces.add(msg.nonce)
        if msg.kind == "telemetry":
            self.last_trusted_x = msg.payload.get("x", self.last_trusted_x)
            self.last_trusted_y = msg.payload.get("y", self.last_trusted_y)
            self.last_trusted_heading = msg.payload.get("heading_deg", self.last_trusted_heading)

        elapsed = (time.perf_counter() - t0) * 1000.0
        return VerificationResult(
            accepted=True,
            detected=False,
            false_positive=False,
            reason="Accepted.",
            response_time_ms=round(elapsed, 3),
        )
