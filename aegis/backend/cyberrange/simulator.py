"""
Abstracted red-team / blue-team simulation logic.

Every "attack technique" and "vulnerability" here is a lookup-table entry
with numeric parameters (base success probability, which hardening flags
mitigate it, how fast it's detected). Running a session evaluates those
probabilities against a chosen SystemConfig -- there is no real scanning,
no real exploitation, no real malware. This models the *outcomes* of a
penetration test / incident-response exercise so the scoring and
reporting layer is meaningful without any actual attack tooling existing.
"""
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import List, Optional

from cyberrange.models import (
    BlueTeamResult,
    BlueTeamTick,
    RedTeamResult,
    RedTeamTechnique,
    SystemConfig,
    TechniqueResult,
    VulnerabilityType,
)

# -- Red team technique definitions -------------------------------------------
# Each technique: (base_success_prob, base_detect_prob, mitigating flags (list of
# SystemConfig attribute names, each present mitigation reduces success and/or
# raises detection), base_time_s range)
_TECHNIQUES = {
    RedTeamTechnique.PORT_SCAN: dict(
        base_success=0.9, base_detect=0.15, time_range=(2, 8),
        success_mitigators=["firewall_enabled"], detect_boosters=["ids_enabled", "firewall_enabled"],
    ),
    RedTeamTechnique.BRUTE_FORCE_LOGIN: dict(
        base_success=0.55, base_detect=0.2, time_range=(10, 60),
        success_mitigators=["strong_auth_enabled"], detect_boosters=["ids_enabled", "strong_auth_enabled"],
    ),
    RedTeamTechnique.PHISHING_FOOTHOLD: dict(
        base_success=0.65, base_detect=0.1, time_range=(5, 30),
        success_mitigators=["least_privilege_enabled"], detect_boosters=["ids_enabled"],
    ),
    RedTeamTechnique.PRIVILEGE_ESCALATION: dict(
        base_success=0.5, base_detect=0.2, time_range=(5, 40),
        success_mitigators=["least_privilege_enabled", "patch_level_pct"], detect_boosters=["ids_enabled"],
    ),
    RedTeamTechnique.LATERAL_MOVEMENT: dict(
        base_success=0.6, base_detect=0.25, time_range=(5, 25),
        success_mitigators=["network_segmentation_enabled"], detect_boosters=["ids_enabled", "network_segmentation_enabled"],
    ),
    RedTeamTechnique.DATA_EXFILTRATION: dict(
        base_success=0.5, base_detect=0.3, time_range=(3, 20),
        success_mitigators=["firewall_enabled"], detect_boosters=["ids_enabled", "firewall_enabled"],
    ),
}

# -- Blue team vulnerability definitions --------------------------------------
_VULNERABILITIES = {
    VulnerabilityType.TROJAN: dict(
        trigger_frac=0.2, detect_boosters=["ids_enabled"], mitigate_needs=["ids_enabled"],
        degrade_per_tick=2.5, base_detect_latency_ticks=8,
    ),
    VulnerabilityType.BACKDOOR: dict(
        trigger_frac=0.1, detect_boosters=["ids_enabled", "strong_auth_enabled"], mitigate_needs=["strong_auth_enabled"],
        degrade_per_tick=1.2, base_detect_latency_ticks=14,
    ),
    VulnerabilityType.TIME_BOMB: dict(
        trigger_frac=0.6, detect_boosters=["ids_enabled"], mitigate_needs=["patch_level_pct"],
        degrade_per_tick=8.0, base_detect_latency_ticks=4,
    ),
    VulnerabilityType.WORM: dict(
        trigger_frac=0.15, detect_boosters=["ids_enabled", "network_segmentation_enabled"],
        mitigate_needs=["network_segmentation_enabled"], degrade_per_tick=4.0, base_detect_latency_ticks=6,
    ),
    VulnerabilityType.ROOTKIT: dict(
        trigger_frac=0.25, detect_boosters=["ids_enabled", "least_privilege_enabled"],
        mitigate_needs=["least_privilege_enabled", "patch_level_pct"], degrade_per_tick=1.8,
        base_detect_latency_ticks=16,
    ),
}


def _flag_value(system: SystemConfig, name: str) -> float:
    val = getattr(system, name)
    if isinstance(val, bool):
        return 1.0 if val else 0.0
    if name == "patch_level_pct":
        return val / 100.0
    return float(val)


def run_red_team(system: SystemConfig, techniques: List[RedTeamTechnique], seed: Optional[int] = None) -> RedTeamResult:
    rng = random.Random(seed)
    results: List[TechniqueResult] = []

    for tech in techniques:
        spec = _TECHNIQUES[tech]
        success_p = spec["base_success"]
        for flag in spec["success_mitigators"]:
            success_p *= (1.0 - 0.5 * _flag_value(system, flag))
        success_p = max(0.03, min(0.98, success_p))

        detect_p = spec["base_detect"]
        for flag in spec["detect_boosters"]:
            detect_p += 0.25 * _flag_value(system, flag)
        detect_p = max(0.02, min(0.97, detect_p))

        success = rng.random() < success_p
        detected = rng.random() < detect_p
        t_lo, t_hi = spec["time_range"]
        time_s = rng.uniform(t_lo, t_hi) * (1.4 if not success else 1.0)
        stealth = max(0.0, 100.0 * (1.0 - detect_p) - (0 if success else 15))

        notes = (
            f"{'Succeeded' if success else 'Failed'}; {'detected' if detected else 'went unnoticed'} by defenses."
        )
        results.append(TechniqueResult(
            technique=tech, success=success, detected=detected,
            time_to_outcome_s=round(time_s, 1), stealth_score=round(stealth, 1), notes=notes,
        ))

    successes = [r for r in results if r.success]
    compromise_pct = 100.0 * len(successes) / len(results) if results else 0.0
    mttc = sum(r.time_to_outcome_s for r in successes) / len(successes) if successes else 0.0
    detection_rate = 100.0 * sum(1 for r in results if r.detected) / len(results) if results else 0.0
    stealth = sum(r.stealth_score for r in results) / len(results) if results else 0.0

    return RedTeamResult(
        system=system,
        techniques=results,
        overall_compromise_pct=round(compromise_pct, 1),
        mean_time_to_compromise_s=round(mttc, 1),
        detection_rate_pct=round(detection_rate, 1),
        overall_stealth_score=round(stealth, 1),
    )


def run_blue_team(
    vulnerability: VulnerabilityType,
    system: SystemConfig,
    duration_ticks: int,
    seed: Optional[int] = None,
) -> BlueTeamResult:
    rng = random.Random(seed)
    spec = _VULNERABILITIES[vulnerability]
    trigger_tick = max(1, int(duration_ticks * spec["trigger_frac"]))

    detect_boost = sum(_flag_value(system, f) for f in spec["detect_boosters"])
    mitigate_strength = sum(_flag_value(system, f) for f in spec["mitigate_needs"]) / max(1, len(spec["mitigate_needs"]))

    detect_latency = max(1, int(spec["base_detect_latency_ticks"] / (1 + detect_boost)))
    mitigate_latency = max(1, int(6 / (0.3 + mitigate_strength)))

    timeline: List[BlueTeamTick] = []
    integrity = 100.0
    detected_at: Optional[int] = None
    mitigated_at: Optional[int] = None
    breach_occurred = False

    for tick in range(duration_ticks):
        if tick == trigger_tick:
            timeline.append(BlueTeamTick(tick=tick, event=f"{vulnerability.value} activated.", detected=False, mitigated=False))

        active = tick >= trigger_tick and mitigated_at is None
        if active:
            integrity -= spec["degrade_per_tick"] * (0.4 if detected_at is not None else 1.0)
            integrity = max(0.0, integrity)
            if integrity < 50:
                breach_occurred = True

            if detected_at is None and tick >= trigger_tick + detect_latency:
                detected_at = tick
                timeline.append(BlueTeamTick(tick=tick, event="Threat detected by monitoring.", detected=True, mitigated=False))

            if detected_at is not None and mitigated_at is None and tick >= detected_at + mitigate_latency:
                mitigated_at = tick
                timeline.append(BlueTeamTick(tick=tick, event="Threat successfully mitigated.", detected=True, mitigated=True))

    mttd = float(detected_at - trigger_tick) if detected_at is not None else None
    mttm = float(mitigated_at - detected_at) if (mitigated_at is not None and detected_at is not None) else None

    score = 40.0
    score += 25.0 if detected_at is not None else 0.0
    score += 25.0 if mitigated_at is not None else 0.0
    score += 0.10 * integrity
    score -= 15.0 if breach_occurred else 0.0
    score = max(0.0, min(100.0, score))

    return BlueTeamResult(
        vulnerability=vulnerability,
        system=system,
        timeline=timeline,
        mean_time_to_detect_s=mttd,
        mean_time_to_mitigate_s=mttm,
        breach_occurred=breach_occurred,
        final_integrity_pct=round(integrity, 1),
        defense_score_0_100=round(score, 1),
    )
