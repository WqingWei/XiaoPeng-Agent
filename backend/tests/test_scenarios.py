"""步骤十：八大场景每场景三组输入的完整测试矩阵。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

import pytest

from core.agent import Agent
from mock.scenario_presets import DEFAULT_SCENARIO_BY_MODE, SCENARIO_IDS_BY_MODE


class FailingLLM:
    async def ainvoke(self, messages: Any):
        raise RuntimeError("场景测试禁用外部 LLM")


@dataclass(frozen=True)
class ScenarioCase:
    scenario_id: str
    message: str
    expected_intent: str
    expected_type: Literal["explicit", "implicit", "urgent"]
    expected_tools: frozenset[str]
    safety_level: str
    forbidden_rules: frozenset[str]
    needs_confirmation: bool = False


SCENARIO_CASES = [
    # P0: 疲劳驾驶
    ScenarioCase("fatigue_driving", "我很困", "疲劳驾驶干预", "implicit", frozenset({"safety_alert_tool", "search_poi"}), "L2", frozenset({"S05", "S06"})),
    ScenarioCase("fatigue_driving", "我已经疲劳了还要继续开", "疲劳驾驶干预", "urgent", frozenset({"safety_alert_tool", "search_poi"}), "L2", frozenset({"S05", "S06"})),
    ScenarioCase("fatigue_driving", "连续开了两小时，现在想睡", "疲劳驾驶干预", "implicit", frozenset({"safety_alert_tool", "search_poi"}), "L2", frozenset({"S05", "S06"})),
    # P0: 亲子出行
    ScenarioCase("parent_child", "带宝宝出门，帮我准备一下", "亲子出行安全与舒适服务", "implicit", frozenset({"ac_control"}), "L2", frozenset({"S05"})),
    ScenarioCase("parent_child", "孩子发烧了", "紧急安全求助", "urgent", frozenset({"ac_control"}), "L2", frozenset({"S05"})),
    ScenarioCase("parent_child", "把儿童锁关掉", "关闭儿童锁", "explicit", frozenset(), "L2", frozenset({"S05"})),
    # P0: 长途补能
    ScenarioCase("long_distance_charging", "续航不够，找个充电站", "长途补能规划", "explicit", frozenset({"search_charger"}), "L1", frozenset({"S05", "S06"})),
    ScenarioCase("long_distance_charging", "帮我规划补能", "长途补能规划", "explicit", frozenset({"search_charger"}), "L1", frozenset({"S05", "S06"})),
    ScenarioCase("long_distance_charging", "剩余电量够不够，需要充电吗", "长途补能规划", "explicit", frozenset({"search_charger"}), "L1", frozenset({"S05", "S06"})),
    # P1: 通勤到达
    ScenarioCase("commute_arrival", "快到公司了，帮我找停车位", "通勤到达停车准备", "implicit", frozenset({"search_parking"}), "L1", frozenset({"S05"})),
    ScenarioCase("commute_arrival", "附近有车位吗", "通勤到达停车准备", "explicit", frozenset({"search_parking"}), "L1", frozenset({"S05"})),
    ScenarioCase("commute_arrival", "帮我找停车场", "通勤到达停车准备", "explicit", frozenset({"search_parking"}), "L1", frozenset({"S05"})),
    # P1: Robotaxi 找不到车
    ScenarioCase("robotaxi_cant_find_car", "我找不到车", "定位 Robotaxi 车辆", "explicit", frozenset({"locate_vehicle", "signal_vehicle"}), "L0", frozenset()),
    ScenarioCase("robotaxi_cant_find_car", "我的车在哪", "定位 Robotaxi 车辆", "explicit", frozenset({"locate_vehicle", "signal_vehicle"}), "L0", frozenset()),
    ScenarioCase("robotaxi_cant_find_car", "车怎么还没来", "定位 Robotaxi 车辆", "explicit", frozenset({"locate_vehicle", "signal_vehicle"}), "L0", frozenset()),
    # P1: 上车点异常
    ScenarioCase("pickup_abnormal", "这里施工，帮我换个上车点", "处理异常上车点", "explicit", frozenset({"search_poi"}), "L2", frozenset({"S05", "S08"}), True),
    ScenarioCase("pickup_abnormal", "这个上车点禁停", "处理异常上车点", "explicit", frozenset({"search_poi"}), "L2", frozenset({"S05", "S08"}), True),
    ScenarioCase("pickup_abnormal", "就在高速路边接我", "处理异常上车点", "urgent", frozenset({"search_poi"}), "L2", frozenset({"S05", "S08"}), True),
    # P2: 临时改目的地
    ScenarioCase("change_destination", "我想改去广州塔", "修改行程目的地", "explicit", frozenset({"get_order_status", "traffic_info"}), "L1", frozenset({"S05"}), True),
    ScenarioCase("change_destination", "改目的地去白云机场", "修改行程目的地", "explicit", frozenset({"get_order_status", "traffic_info"}), "L1", frozenset({"S05"}), True),
    ScenarioCase("change_destination", "不去那里了，改去公司", "修改行程目的地", "explicit", frozenset({"get_order_status", "traffic_info"}), "L1", frozenset({"S05"}), True),
    # P0: 乘客求助
    ScenarioCase("passenger_help", "我身体不舒服，需要求助", "乘客紧急求助", "urgent", frozenset({"emergency_stop", "call_emergency", "transfer_human"}), "L4", frozenset({"S05"})),
    ScenarioCase("passenger_help", "救命，请帮帮我", "乘客紧急求助", "urgent", frozenset({"emergency_stop", "call_emergency", "transfer_human"}), "L4", frozenset({"S05"})),
    ScenarioCase("passenger_help", "help，我需要紧急帮助", "乘客紧急求助", "urgent", frozenset({"emergency_stop", "call_emergency", "transfer_human"}), "L4", frozenset({"S05"})),
]


def test_modes_have_disjoint_scenarios_and_stable_defaults() -> None:
    owner_scenarios = set(SCENARIO_IDS_BY_MODE["owner"])
    robotaxi_scenarios = set(SCENARIO_IDS_BY_MODE["robotaxi"])

    assert len(owner_scenarios) == 4
    assert len(robotaxi_scenarios) == 4
    assert owner_scenarios.isdisjoint(robotaxi_scenarios)
    assert DEFAULT_SCENARIO_BY_MODE == {
        "owner": "fatigue_driving",
        "robotaxi": "robotaxi_cant_find_car",
    }


def _case_id(case: ScenarioCase) -> str:
    return f"{case.scenario_id}-{case.message[:10]}"


def test_matrix_has_three_inputs_for_each_of_eight_scenarios() -> None:
    scenario_ids = {case.scenario_id for case in SCENARIO_CASES}

    assert len(scenario_ids) == 8
    assert len(SCENARIO_CASES) == 24
    assert all(
        sum(case.scenario_id == scenario_id for case in SCENARIO_CASES) == 3
        for scenario_id in scenario_ids
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("case", SCENARIO_CASES, ids=_case_id)
async def test_scenario_intent_tools_safety_and_boundaries(
    case: ScenarioCase,
) -> None:
    agent = Agent(llm=FailingLLM())
    context = agent.context_manager.reset("scenario-session", case.scenario_id)

    response = await agent.process("scenario-session", case.message)

    planned_tools = {step.tool for step in response.service_plan.steps}
    actual_forbidden_rules = {
        forbidden.rule_id for forbidden in response.forbidden_actions
    }
    actual_alert_rules = {alert.rule_id for alert in response.safety_alerts}
    actual_level = max(
        (int(alert.level[1:]) for alert in response.safety_alerts),
        default=0,
    )

    assert response.reasoning.detected_intent == case.expected_intent
    assert response.reasoning.intent_type == case.expected_type
    assert case.expected_tools.issubset(planned_tools)
    assert actual_level == int(case.safety_level[1:])
    assert actual_forbidden_rules == case.forbidden_rules
    assert actual_forbidden_rules.issubset(actual_alert_rules)
    assert response.follow_up.needs_confirmation is case.needs_confirmation
    assert response.user_response
    assert response.turn_id == 1
    assert context.turn_id == 1

    if case.scenario_id == "passenger_help":
        assert context.vehicle.speed == 0
        assert context.vehicle.driving_status == "parked"
    if case.scenario_id == "parent_child":
        assert context.vehicle.cabin.child_lock is True
    if case.scenario_id == "change_destination":
        assert "modify_order" not in planned_tools
