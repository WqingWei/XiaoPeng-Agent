"""步骤七：SafetyEngine 的规则级与聚合测试。"""

from __future__ import annotations

from collections.abc import Callable

import pytest

from core.safety_engine import SafetyEngine, UnsafeConditionError
from mock.scenario_presets import load_scenario
from models.environment import EnvironmentContext, TimeContext
from models.vehicle import (
    ACState,
    BatteryInfo,
    CabinState,
    DriverState,
    SeatInfo,
    VehicleState,
)


@pytest.fixture(scope="module")
def engine() -> SafetyEngine:
    return SafetyEngine()


def _safe_state() -> VehicleState:
    return VehicleState(
        driving_status="parked",
        speed=0,
        battery=BatteryInfo(level=80, range_km=400, charging=False),
        cabin=CabinState(
            ac=ACState(
                zone_temp={"driver": 24, "passenger": 24, "rear": 24},
                fan_speed=3,
                mode="auto",
            ),
            seats=[
                SeatInfo(id="driver", occupied=True),
                SeatInfo(id="passenger", occupied=False),
                SeatInfo(id="rear_left", occupied=False),
                SeatInfo(id="rear_right", occupied=False),
            ],
        ),
        driver=DriverState(fatigue_level=0, driving_duration_min=30),
    )


def _safe_environment() -> EnvironmentContext:
    return EnvironmentContext(time=TimeContext(period="morning"))


def _rule_ids(result: object) -> set[str]:
    return {rule.rule_id for rule in result.triggered_rules}


TriggerSetup = Callable[[VehicleState, EnvironmentContext], dict]


def _s01(vehicle: VehicleState, _: EnvironmentContext) -> dict:
    vehicle.driver.driving_duration_min = 121
    return {}


def _s02(vehicle: VehicleState, _: EnvironmentContext) -> dict:
    vehicle.cabin.seats[2].occupied = True
    vehicle.cabin.seats[2].child_seat = True
    return {}


def _s03(vehicle: VehicleState, _: EnvironmentContext) -> dict:
    vehicle.cabin.seats[0].occupied = False
    vehicle.cabin.seats[2].occupied = True
    vehicle.cabin.seats[2].child_seat = True
    return {}


def _s04(_: VehicleState, __: EnvironmentContext) -> dict:
    return {"user_message": "我身体不舒服，需要求助"}


def _s05(vehicle: VehicleState, _: EnvironmentContext) -> dict:
    vehicle.speed = 1
    return {}


def _s06(vehicle: VehicleState, _: EnvironmentContext) -> dict:
    vehicle.speed = 81
    return {}


def _s07(vehicle: VehicleState, _: EnvironmentContext) -> dict:
    vehicle.battery.charging = True
    return {}


def _s08(_: VehicleState, __: EnvironmentContext) -> dict:
    return {"intent": {"order": {"pickup_in_danger_zone": True}}}


def _s09(_: VehicleState, __: EnvironmentContext) -> dict:
    return {"intent": {"safety_event": {"level": 3}}}


def _s10(vehicle: VehicleState, _: EnvironmentContext) -> dict:
    vehicle.battery.range_km = 100
    return {"intent": {"remaining_distance_km": 100}}


def _s11(_: VehicleState, environment: EnvironmentContext) -> dict:
    environment.time.period = "night"
    return {"intent": {"media": {"volume": 41}}}


def _s12(_: VehicleState, __: EnvironmentContext) -> dict:
    return {"intent": {"cabin": {"ac": {"target_temp": 17}}}}


@pytest.mark.parametrize(
    ("rule_id", "expected_level", "setup"),
    [
        ("S01", "L2", _s01),
        ("S02", "L2", _s02),
        ("S03", "L3", _s03),
        ("S04", "L4", _s04),
        ("S05", "L1", _s05),
        ("S06", "L1", _s06),
        ("S07", "L1", _s07),
        ("S08", "L2", _s08),
        ("S09", "L4", _s09),
        ("S10", "L1", _s10),
        ("S11", "L1", _s11),
        ("S12", "L1", _s12),
    ],
)
def test_each_rule_triggers(
    engine: SafetyEngine,
    rule_id: str,
    expected_level: str,
    setup: TriggerSetup,
) -> None:
    vehicle = _safe_state()
    environment = _safe_environment()
    arguments = setup(vehicle, environment)

    result = engine.check(vehicle, environment, **arguments)

    assert rule_id in _rule_ids(result)
    assert int(result.safety_level[1:]) >= int(expected_level[1:])
    assert result.required_actions


@pytest.mark.parametrize(
    ("rule_id", "mutate", "intent", "message"),
    [
        ("S01", lambda v, e: setattr(v.driver, "driving_duration_min", 120), {}, ""),
        ("S02", lambda v, e: None, {}, ""),
        ("S03", lambda v, e: setattr(v.cabin.seats[0], "occupied", False), {}, ""),
        ("S04", lambda v, e: None, {}, "普通行程咨询"),
        ("S05", lambda v, e: setattr(v, "speed", 0), {}, ""),
        ("S06", lambda v, e: setattr(v, "speed", 80), {}, ""),
        ("S07", lambda v, e: setattr(v.battery, "charging", False), {}, ""),
        ("S08", lambda v, e: None, {"order": {"pickup_in_danger_zone": False}}, ""),
        ("S09", lambda v, e: None, {"safety_event": {"level": 2}}, ""),
        ("S10", lambda v, e: setattr(v.battery, "range_km", 120), {"remaining_distance_km": 100}, ""),
        ("S11", lambda v, e: setattr(e.time, "period", "night"), {"media": {"volume": 40}}, ""),
        ("S12", lambda v, e: None, {"cabin": {"ac": {"target_temp": 18}}}, ""),
    ],
)
def test_each_rule_has_non_triggering_boundary(
    engine: SafetyEngine,
    rule_id: str,
    mutate: Callable[[VehicleState, EnvironmentContext], None],
    intent: dict,
    message: str,
) -> None:
    vehicle = _safe_state()
    environment = _safe_environment()
    mutate(vehicle, environment)

    result = engine.check(vehicle, environment, intent=intent, user_message=message)

    assert rule_id not in _rule_ids(result)


def test_loads_all_rules_and_types(engine: SafetyEngine) -> None:
    assert [rule.rule_id for rule in engine.rules] == [f"S{number:02d}" for number in range(1, 13)]
    assert sum(rule.type == "hard" for rule in engine.rules) == 9
    assert sum(rule.type == "soft" for rule in engine.rules) == 3


def test_safe_state_returns_l0(engine: SafetyEngine) -> None:
    result = engine.check(_safe_state(), _safe_environment())

    assert result.safety_level == "L0"
    assert result.triggered_rules == []
    assert result.required_actions == []
    assert result.forbidden_actions == []


def test_highest_level_and_escalation_actions(engine: SafetyEngine) -> None:
    result = engine.check(
        _safe_state(),
        _safe_environment(),
        intent={"safety_event": {"level": 3}},
        user_message="救命，我身体不舒服",
    )

    assert result.safety_level == "L4"
    assert {"S04", "S09"}.issubset(_rule_ids(result))
    assert "转接人工服务" in result.required_actions
    assert "呼叫紧急服务：110" in result.required_actions
    assert "呼叫紧急服务：120" in result.required_actions


def test_reject_rule_builds_forbidden_action(engine: SafetyEngine) -> None:
    vehicle = _safe_state()
    vehicle.speed = 81

    result = engine.check(vehicle, _safe_environment())

    assert {action.rule_id for action in result.forbidden_actions} == {"S05", "S06"}
    assert "81" in next(
        action.reason for action in result.forbidden_actions if action.rule_id == "S06"
    )


def test_real_scenarios_map_to_expected_rules(engine: SafetyEngine) -> None:
    fatigue_vehicle, fatigue_env, *_ = load_scenario("fatigue_driving")
    parent_vehicle, parent_env, *_ = load_scenario("parent_child")
    help_vehicle, help_env, *_ = load_scenario("passenger_help")

    assert "S01" in _rule_ids(engine.check(fatigue_vehicle, fatigue_env))
    assert "S02" in _rule_ids(engine.check(parent_vehicle, parent_env))
    assert "S04" in _rule_ids(
        engine.check(help_vehicle, help_env, user_message="我身体不舒服，需要帮助")
    )


def test_condition_evaluator_supports_planned_operators(engine: SafetyEngine) -> None:
    context = {"driver": {"fatigue_level": 2, "duration": 121}, "speed": 80}

    assert engine.evaluate_condition(
        "driver.duration > 120 and (driver.fatigue_level >= 2 or speed < 20)",
        context,
    )
    assert engine.evaluate_condition("speed == 80", context)


@pytest.mark.parametrize(
    "condition",
    [
        "__import__('os').getcwd()",
        "driver['fatigue_level'] >= 2",
        "(lambda: true)()",
    ],
)
def test_condition_evaluator_rejects_unsafe_syntax(
    engine: SafetyEngine,
    condition: str,
) -> None:
    with pytest.raises(UnsafeConditionError):
        engine.evaluate_condition(condition, {"driver": {"fatigue_level": 2}})


def test_missing_condition_field_is_non_triggering(engine: SafetyEngine) -> None:
    assert not engine.evaluate_condition("missing.value > 0", {})
