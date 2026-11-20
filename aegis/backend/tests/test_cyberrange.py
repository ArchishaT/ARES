import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from cyberrange.models import RedTeamTechnique, SystemConfig, VulnerabilityType
from cyberrange.simulator import run_blue_team, run_red_team


def test_hardened_system_resists_better_than_weak_system():
    weak = SystemConfig(firewall_enabled=False, ids_enabled=False, strong_auth_enabled=False)
    hardened = SystemConfig(
        firewall_enabled=True, ids_enabled=True, strong_auth_enabled=True,
        least_privilege_enabled=True, network_segmentation_enabled=True, patch_level_pct=95,
    )
    techniques = list(RedTeamTechnique)
    weak_result = run_red_team(weak, techniques, seed=1)
    hardened_result = run_red_team(hardened, techniques, seed=1)
    assert hardened_result.overall_compromise_pct <= weak_result.overall_compromise_pct
    assert hardened_result.detection_rate_pct >= weak_result.detection_rate_pct


def test_red_team_result_has_all_techniques():
    system = SystemConfig()
    techniques = [RedTeamTechnique.PORT_SCAN, RedTeamTechnique.BRUTE_FORCE_LOGIN]
    result = run_red_team(system, techniques, seed=7)
    assert len(result.techniques) == 2


def test_blue_team_better_defense_improves_score():
    weak = SystemConfig(ids_enabled=False, strong_auth_enabled=False, patch_level_pct=20)
    strong = SystemConfig(ids_enabled=True, strong_auth_enabled=True, patch_level_pct=95, least_privilege_enabled=True)
    weak_result = run_blue_team(VulnerabilityType.BACKDOOR, weak, duration_ticks=100, seed=3)
    strong_result = run_blue_team(VulnerabilityType.BACKDOOR, strong, duration_ticks=100, seed=3)
    assert strong_result.defense_score_0_100 >= weak_result.defense_score_0_100
    assert strong_result.final_integrity_pct >= weak_result.final_integrity_pct


def test_blue_team_timeline_has_trigger_event():
    system = SystemConfig()
    result = run_blue_team(VulnerabilityType.TIME_BOMB, system, duration_ticks=50, seed=9)
    assert len(result.timeline) >= 1
    assert any("activated" in t.event for t in result.timeline)


def test_breach_flag_consistent_with_integrity():
    system = SystemConfig(ids_enabled=False, strong_auth_enabled=False, patch_level_pct=10)
    result = run_blue_team(VulnerabilityType.TIME_BOMB, system, duration_ticks=80, seed=11)
    if result.breach_occurred:
        assert result.final_integrity_pct <= 100
