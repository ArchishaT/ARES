import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from security.models import AttackType, DefenseConfig, ScenarioConfig
from security.engine import run_scenario, run_comparison
from security.defenses import DefenseLayer, sign, sign_message
from security.attacks import Message, attack_unauthorized_command, attack_replay


def test_unsigned_command_rejected_when_auth_enabled():
    layer = DefenseLayer(config=DefenseConfig(authentication_enabled=True))
    outcome = attack_unauthorized_command(nonce=1)
    result = layer.verify(outcome.message, is_actually_malicious=True)
    assert result.accepted is False
    assert result.detected is True


def test_signed_legitimate_message_accepted():
    layer = DefenseLayer(config=DefenseConfig(authentication_enabled=True))
    msg = Message(kind="command", payload={"command": "noop"}, timestamp=__import__("time").time(), nonce=1)
    sign_message(msg)
    result = layer.verify(msg, is_actually_malicious=False)
    assert result.accepted is True
    assert result.false_positive is False


def test_replay_detected_by_integrity_checks():
    layer = DefenseLayer(config=DefenseConfig(integrity_checks_enabled=True))
    outcome = attack_replay(None, nonce=5)
    result = layer.verify(outcome.message, is_actually_malicious=True)
    assert result.accepted is False
    assert result.detected is True


def test_rate_limiting_blocks_flood():
    layer = DefenseLayer(config=DefenseConfig(rate_limiting_enabled=True))
    from security.attacks import attack_dos_flood
    outcome = attack_dos_flood(nonce=1, count=40)
    result = layer.verify(outcome.message, is_actually_malicious=True)
    assert result.accepted is False


def test_secured_scenario_has_lower_degradation_than_unsecured():
    scenario = ScenarioConfig(
        attacks=list(AttackType),
        defenses=DefenseConfig(
            authentication_enabled=True,
            integrity_checks_enabled=True,
            anomaly_detection_enabled=True,
            rate_limiting_enabled=True,
            secure_channel_enabled=True,
        ),
        duration_ticks=300,
        attack_intensity=0.5,
    )
    unsecured, secured, _, _ = run_comparison(scenario)
    assert secured.navigation_degradation_pct <= unsecured.navigation_degradation_pct
    assert secured.detection_rate_pct >= unsecured.detection_rate_pct


def test_metrics_schema_fields_present():
    scenario = ScenarioConfig(attacks=[AttackType.SENSOR_SPOOFING], duration_ticks=50, attack_intensity=0.8)
    metrics, events = run_scenario(scenario, DefenseConfig(anomaly_detection_enabled=True), seed=42, label="secured")
    assert metrics.total_attacks >= 0
    assert 0 <= metrics.detection_rate_pct <= 100
    assert metrics.avg_response_time_ms >= 0
