"""
Runs one security scenario (a fixed sequence of attack opportunities over
N ticks) through a DefenseLayer configuration and computes the resulting
metrics. Running the same scenario (same random seed) once with all
defenses off and once with the requested defenses on is what produces
the "unsecured vs secured" comparison.
"""
from __future__ import annotations

import random
import time
from dataclasses import dataclass, field
from typing import List, Optional

from security.attacks import (
    Message,
    attack_compromised_channel,
    attack_dos_flood,
    attack_malicious_nav_injection,
    attack_replay,
    attack_sensor_spoofing,
    attack_unauthorized_command,
)
from security.defenses import DefenseLayer, sign_message
from security.models import (
    AttackType,
    DefenseConfig,
    ScenarioConfig,
    SecurityEventRecord,
    SecurityMetrics,
)

ROUTE_LENGTH_M = 50.0

_SEVERITY = {
    AttackType.SENSOR_SPOOFING: 1.2,
    AttackType.UNAUTHORIZED_COMMAND: 1.6,
    AttackType.REPLAY_ATTACK: 0.6,
    AttackType.COMPROMISED_CHANNEL: 1.3,
    AttackType.MALICIOUS_NAV_INJECTION: 2.2,
    AttackType.DOS_FLOOD: 1.0,
}

_ATTACK_BUILDERS = {
    AttackType.SENSOR_SPOOFING: lambda ctx: attack_sensor_spoofing(ctx["x"], ctx["y"], ctx["heading"], ctx["nonce"]),
    AttackType.UNAUTHORIZED_COMMAND: lambda ctx: attack_unauthorized_command(ctx["nonce"]),
    AttackType.REPLAY_ATTACK: lambda ctx: attack_replay(ctx["last_legit"], ctx["nonce"]),
    AttackType.COMPROMISED_CHANNEL: lambda ctx: attack_compromised_channel(ctx["last_legit_signed"]),
    AttackType.MALICIOUS_NAV_INJECTION: lambda ctx: attack_malicious_nav_injection(ctx["nonce"]),
    AttackType.DOS_FLOOD: lambda ctx: attack_dos_flood(ctx["nonce"]),
}


def run_scenario(scenario: ScenarioConfig, defense_config: DefenseConfig, seed: int, label: str):
    rng = random.Random(seed)
    layer = DefenseLayer(config=defense_config)

    drift_m = 0.0
    nonce_counter = 0
    commands_accepted = 0
    commands_rejected = 0
    false_positives = 0
    events: List[SecurityEventRecord] = []
    response_times: List[float] = []

    true_x, true_y, true_heading = 0.0, 0.0, 0.0
    last_legit: Optional[Message] = None
    last_legit_signed: Optional[Message] = None

    attacks_available = scenario.attacks or list(AttackType)

    for tick in range(scenario.duration_ticks):
        layer.reset_tick()

        # -- nominal forward progress (ideal path) ---------------------------
        true_x += ROUTE_LENGTH_M / scenario.duration_ticks
        nonce_counter += 1

        # -- legitimate telemetry each tick (tests false-positive rate) -------
        legit_telemetry = Message(
            kind="telemetry",
            payload={"x": true_x, "y": true_y, "heading_deg": true_heading},
            timestamp=time.time(),
            nonce=nonce_counter,
        )
        if defense_config.authentication_enabled or defense_config.secure_channel_enabled:
            sign_message(legit_telemetry)
        result = layer.verify(legit_telemetry, is_actually_malicious=False)
        response_times.append(result.response_time_ms)
        if result.false_positive:
            false_positives += 1
            drift_m += 0.05  # minor degradation: a good reading was discarded
        last_legit = legit_telemetry
        last_legit_signed = legit_telemetry

        # -- maybe inject an attack this tick ---------------------------------
        if attacks_available and rng.random() < scenario.attack_intensity:
            attack_type = rng.choice(attacks_available)
            nonce_counter += 1
            ctx = {
                "x": true_x, "y": true_y, "heading": true_heading,
                "nonce": nonce_counter, "last_legit": last_legit, "last_legit_signed": last_legit_signed,
            }
            outcome = _ATTACK_BUILDERS[attack_type](ctx)
            msg = outcome.message
            verdict = layer.verify(msg, is_actually_malicious=True)
            response_times.append(verdict.response_time_ms)

            if verdict.accepted:
                commands_accepted += 1
                drift_m += _SEVERITY[attack_type] * (0.5 + rng.random())
            else:
                commands_rejected += 1

            events.append(
                SecurityEventRecord(
                    tick=tick,
                    attack_type=attack_type,
                    detected=verdict.detected,
                    blocked=not verdict.accepted,
                    response_time_ms=verdict.response_time_ms,
                    description=f"{outcome.description} -> {verdict.reason}",
                )
            )
        else:
            commands_accepted += 1  # the legitimate telemetry/command tick itself

    total_attacks = len(events)
    detected = sum(1 for e in events if e.detected)
    blocked = sum(1 for e in events if e.blocked)

    metrics = SecurityMetrics(
        label=label,
        total_attacks=total_attacks,
        detected_attacks=detected,
        blocked_attacks=blocked,
        detection_rate_pct=round(100.0 * detected / total_attacks, 1) if total_attacks else 0.0,
        false_positive_count=false_positives,
        false_positive_rate_pct=round(100.0 * false_positives / scenario.duration_ticks, 2),
        avg_response_time_ms=round(sum(response_times) / len(response_times), 4) if response_times else 0.0,
        navigation_degradation_pct=round(min(100.0, 100.0 * drift_m / ROUTE_LENGTH_M), 1),
        final_position_error_m=round(drift_m, 2),
        commands_accepted=commands_accepted,
        commands_rejected=commands_rejected,
    )
    return metrics, events


def run_comparison(scenario: ScenarioConfig):
    seed = random.randint(0, 1_000_000)
    unsecured_metrics, unsecured_events = run_scenario(scenario, DefenseConfig(), seed, "unsecured")
    secured_metrics, secured_events = run_scenario(scenario, scenario.defenses, seed, "secured")
    return unsecured_metrics, secured_metrics, unsecured_events, secured_events
