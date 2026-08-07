"""步骤十：26 个 LangChain 工具的逐项与边界测试。"""

from __future__ import annotations

from typing import Any

import pytest
from pydantic import ValidationError

from mock.scenario_presets import load_scenario
from tools.base import ToolContext, ToolRegistry


VALID_TOOL_CASES: list[tuple[str, str, dict[str, Any]]] = [
    # 座舱控制 6
    ("ac_control", "commute_arrival", {"zone": "driver", "temp": 23, "fan_speed": 2, "mode": "auto"}),
    ("seat_control", "commute_arrival", {"seat_id": "driver", "position": "upright", "cooling": True}),
    ("window_control", "commute_arrival", {"window_id": "front_left", "action": "set", "level": 20}),
    ("light_control", "commute_arrival", {"light_type": "ambient", "color": "#00C15D", "brightness": 60}),
    ("media_control", "commute_arrival", {"action": "play", "source": "music", "volume": 30}),
    ("child_lock_control", "parent_child", {"action": "enable"}),
    # 导航出行 5
    ("navigate_to", "commute_arrival", {"destination": "广州塔", "waypoints": "珠江新城", "preference": "fastest"}),
    ("search_poi", "commute_arrival", {"category": "restaurant", "radius": 10, "sort_by": "rating"}),
    ("search_parking", "commute_arrival", {"location": "公司", "radius": 5, "filter": "available"}),
    ("search_charger", "long_distance_charging", {"location": "当前位置", "radius": 20, "power_type": "fast", "sort_by": "distance"}),
    ("traffic_info", "pickup_abnormal", {"route_id": "current"}),
    # 车辆查询 4
    ("get_vehicle_status", "fatigue_driving", {}),
    ("get_driver_status", "fatigue_driving", {}),
    ("get_location", "fatigue_driving", {}),
    ("get_environment_info", "fatigue_driving", {}),
    # Robotaxi 订单 6
    ("create_order", "robotaxi_cant_find_car", {"pickup": "天河城", "dropoff": "广州塔", "vehicle_type": "standard"}),
    ("modify_order", "change_destination", {"order_id": "ORD-701", "changes": "目的地改为广州塔"}),
    ("cancel_order", "robotaxi_cant_find_car", {"order_id": "ORD-501", "reason": "行程有变"}),
    ("get_order_status", "change_destination", {"order_id": "ORD-701"}),
    ("locate_vehicle", "robotaxi_cant_find_car", {"order_id": "ORD-501"}),
    ("signal_vehicle", "robotaxi_cant_find_car", {"order_id": "ORD-501", "action": "flash_and_honk"}),
    # 安全应急 5
    ("emergency_stop", "passenger_help", {}),
    ("call_rescue", "commute_arrival", {"rescue_type": "road", "location": "当前位置"}),
    ("call_emergency", "passenger_help", {"service": "120"}),
    ("transfer_human", "passenger_help", {"priority": "urgent", "context": "乘客身体不适"}),
    ("safety_alert_tool", "fatigue_driving", {"level": "L2", "message": "请尽快休息"}),
]


def _initialize(scenario_id: str) -> ToolContext:
    ToolContext.reset()
    vehicle, environment, order, user, _ = load_scenario(scenario_id)
    context = ToolContext()
    context.init_from_scenario(vehicle, environment, order, user)
    return context


@pytest.fixture(scope="module")
def tools() -> dict[str, Any]:
    registry = ToolRegistry()
    return {tool.name: tool for tool in registry.get_all_tools()}


def test_registry_contains_exactly_26_unique_tools(tools: dict[str, Any]) -> None:
    assert len(tools) == 26
    assert set(tools) == {name for name, _, _ in VALID_TOOL_CASES}


@pytest.mark.parametrize(
    ("tool_name", "scenario_id", "arguments"),
    VALID_TOOL_CASES,
    ids=[case[0] for case in VALID_TOOL_CASES],
)
def test_each_tool_accepts_valid_input(
    tools: dict[str, Any],
    tool_name: str,
    scenario_id: str,
    arguments: dict[str, Any],
) -> None:
    _initialize(scenario_id)

    result = tools[tool_name].invoke(arguments)

    assert isinstance(result, dict)
    assert result["success"] is True


@pytest.mark.parametrize(
    ("tool_name", "scenario_id", "arguments", "message_fragment"),
    [
        ("ac_control", "commute_arrival", {"temp": 50}, "超出范围"),
        ("ac_control", "commute_arrival", {"fan_speed": 8}, "超出范围"),
        ("ac_control", "commute_arrival", {"zone": "trunk"}, "未知区域"),
        ("seat_control", "commute_arrival", {"seat_id": "roof"}, "无效座椅"),
        ("window_control", "fatigue_driving", {"action": "open"}, "限制在30%"),
        ("window_control", "commute_arrival", {"window_id": "roof"}, "无效车窗"),
        ("light_control", "commute_arrival", {"brightness": 101}, "超出范围"),
        ("media_control", "commute_arrival", {"action": "play", "source": "video"}, "无法播放视频"),
        ("child_lock_control", "parent_child", {"action": "disable"}, "无法关闭"),
        ("modify_order", "commute_arrival", {"changes": "改目的地"}, "没有活跃订单"),
        ("cancel_order", "change_destination", {"reason": "用户取消"}, "需要先安全停车"),
        ("get_order_status", "commute_arrival", {}, "没有活跃订单"),
        ("locate_vehicle", "commute_arrival", {}, "没有活跃订单"),
        ("signal_vehicle", "commute_arrival", {"action": "honk"}, "没有活跃订单"),
    ],
)
def test_tools_reject_invalid_or_unsafe_input(
    tools: dict[str, Any],
    tool_name: str,
    scenario_id: str,
    arguments: dict[str, Any],
    message_fragment: str,
) -> None:
    _initialize(scenario_id)

    result = tools[tool_name].invoke(arguments)

    assert result["success"] is False
    assert message_fragment in result["message"]


def test_required_tool_arguments_are_schema_validated(tools: dict[str, Any]) -> None:
    _initialize("commute_arrival")

    with pytest.raises(ValidationError):
        tools["navigate_to"].invoke({})
    with pytest.raises(ValidationError):
        tools["create_order"].invoke({"pickup": "天河城"})


def test_successful_controls_mutate_shared_state(tools: dict[str, Any]) -> None:
    context = _initialize("commute_arrival")

    tools["ac_control"].invoke({"zone": "driver", "temp": 22, "fan_speed": 2})
    tools["window_control"].invoke({"window_id": "front_left", "action": "set", "level": 15})
    tools["media_control"].invoke({"action": "volume", "volume": 45})

    assert context.vehicle.cabin.ac.zone_temp["driver"] == 22
    assert context.vehicle.cabin.windows.front_left == 15
    assert context.media_volume == 45


def test_emergency_stop_and_cancel_order_mutate_lifecycle(
    tools: dict[str, Any],
) -> None:
    emergency_context = _initialize("passenger_help")
    stop_result = tools["emergency_stop"].invoke({})

    assert stop_result["success"]
    assert emergency_context.vehicle.speed == 0
    assert emergency_context.vehicle.driving_status == "parked"

    order_context = _initialize("robotaxi_cant_find_car")
    cancel_result = tools["cancel_order"].invoke({"reason": "测试取消"})

    assert cancel_result["success"]
    assert order_context.order is None
