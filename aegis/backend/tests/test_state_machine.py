import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from models.schemas import RobotState
from simulation.robot import Robot


def test_valid_transition_idle_to_planning():
    r = Robot()
    assert r.transition_to(RobotState.PLANNING) is True
    assert r.state == RobotState.PLANNING


def test_invalid_transition_idle_to_navigating():
    r = Robot()
    assert r.transition_to(RobotState.NAVIGATING) is False
    assert r.state == RobotState.IDLE


def test_full_happy_path_sequence():
    r = Robot()
    sequence = [
        RobotState.PLANNING,
        RobotState.NAVIGATING,
        RobotState.OBSTACLE_DETECTED,
        RobotState.REPLANNING,
        RobotState.NAVIGATING,
        RobotState.MISSION_COMPLETE,
    ]
    for state in sequence:
        assert r.transition_to(state) is True, f"failed transitioning to {state}"


def test_emergency_stop_requires_explicit_reset():
    r = Robot()
    r.transition_to(RobotState.PLANNING)
    r.transition_to(RobotState.NAVIGATING)
    assert r.transition_to(RobotState.EMERGENCY_STOP) is True
    # cannot jump straight back into navigating from emergency stop
    assert r.transition_to(RobotState.NAVIGATING) is False
    assert r.transition_to(RobotState.IDLE) is True


def test_self_transition_is_allowed():
    r = Robot()
    assert r.transition_to(RobotState.IDLE) is True
