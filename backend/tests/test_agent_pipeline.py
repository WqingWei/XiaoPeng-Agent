"""步骤八：意图、编排、输出与七步 Agent 流水线测试。"""

from __future__ import annotations

import json
from typing import Any

import pytest
from langchain_core.messages import AIMessage

from core.agent import Agent
from core.context_manager import ContextManager
from core.intent_engine import IntentEngine, IntentResult
from core.llm_utils import parse_json_object
from core.orchestrator import OrchestrationPlan, Orchestrator
from core.output_formatter import OutputFormatter
from core.safety_engine import SafetyEngine, SafetyResult
from mock.scenario_presets import load_scenario
from models.agent_output import ServiceStep


class QueueLLM:
    def __init__(self, responses: list[str]):
        self.responses = list(responses)
        self.calls: list[Any] = []

    async def ainvoke(self, messages: Any) -> AIMessage:
        self.calls.append(messages)
        if not self.responses:
            raise RuntimeError("没有更多测试响应")
        return AIMessage(content=self.responses.pop(0))


class FailingLLM:
    async def ainvoke(self, messages: Any) -> AIMessage:
        raise RuntimeError("测试中禁用外部 LLM")


def _context(scenario_id: str):
    manager = ContextManager()
    return manager, manager.reset("session", scenario_id)


def test_json_parser_accepts_fence_and_surrounding_text() -> None:
    assert parse_json_object('```json\n{"value": 1}\n```') == {"value": 1}
    assert parse_json_object('结果如下：{"value": 2}，结束') == {"value": 2}


@pytest.mark.asyncio
async def test_intent_engine_parses_llm_json_and_extracts_entities() -> None:
    llm = QueueLLM(
        [
            "分析结果："
            + json.dumps(
                {
                    "detected_intent": "调节空调",
                    "intent_type": "explicit",
                    "confidence": 0.93,
                    "context_factors": ["用户指定温度"],
                },
                ensure_ascii=False,
            )
        ]
    )
    _, context = _context("commute_arrival")

    result = await IntentEngine(llm).analyze("空调调到23度", context)

    assert result.detected_intent == "调节空调"
    assert result.confidence == 0.93
    assert result.entities["temperature"] == 23
    assert llm.calls


@pytest.mark.asyncio
async def test_intent_engine_falls_back_without_network() -> None:
    _, context = _context("fatigue_driving")

    result = await IntentEngine(FailingLLM()).analyze("我有点困", context)

    assert result.detected_intent == "疲劳驾驶干预"
    assert result.intent_type == "implicit"
    assert result.context_factors


@pytest.mark.asyncio
async def test_orchestrator_filters_hallucinated_and_unsafe_steps() -> None:
    planner_json = {
        "summary": "停车前准备",
        "steps": [
            {
                "step_id": 1,
                "action": "播放视频",
                "tool": "media_control",
                "params": {"action": "play", "source": "video", "volume": 30},
                "dependency": None,
                "estimated_duration_s": 2,
            },
            {
                "step_id": 2,
                "action": "调用不存在工具",
                "tool": "invented_tool",
                "params": {},
                "dependency": None,
                "estimated_duration_s": 2,
            },
            {
                "step_id": 3,
                "action": "搜索停车场",
                "tool": "search_parking",
                "params": {"location": "公司", "radius": 3, "filter": "available"},
                "dependency": None,
                "estimated_duration_s": 2,
            },
        ],
        "total_estimated_time_s": 6,
        "tool_selection_reasons": [
            {"tool": "search_parking", "reason": "寻找车位"}
        ],
        "alternatives_considered": [],
        "requires_confirmation": False,
        "confirmation_message": "",
    }
    llm = QueueLLM([json.dumps(planner_json, ensure_ascii=False)])
    _, context = _context("commute_arrival")
    intent = IntentResult(
        detected_intent="通勤停车准备",
        original_message="快到公司了，播放视频并找停车场",
    )
    safety = SafetyEngine().check(
        context.vehicle, context.environment, intent, intent.original_message
    )

    plan = await Orchestrator(llm).plan(intent, safety, context)

    assert [step.tool for step in plan.steps] == ["search_parking"]
    assert plan.total_estimated_time_s == 2


@pytest.mark.asyncio
async def test_orchestrator_executes_dependencies_and_syncs_state() -> None:
    _, context = _context("commute_arrival")
    orchestrator = Orchestrator(FailingLLM())
    plan = OrchestrationPlan(
        summary="调节座舱",
        steps=[
            ServiceStep(
                step_id=1,
                action="调空调",
                tool="ac_control",
                params={"zone": "driver", "temp": 23, "fan_speed": 2, "mode": "auto"},
                estimated_duration_s=1,
            ),
            ServiceStep(
                step_id=2,
                action="开座椅通风",
                tool="seat_control",
                params={"seat_id": "driver", "cooling": True},
                dependency=1,
                estimated_duration_s=1,
            ),
        ],
        total_estimated_time_s=2,
    )

    results = await orchestrator.execute(plan, context)

    assert [result.success for result in results] == [True, True]
    assert context.vehicle.cabin.ac.zone_temp["driver"] == 23


@pytest.mark.asyncio
async def test_failed_dependency_skips_downstream_step() -> None:
    _, context = _context("commute_arrival")
    orchestrator = Orchestrator(FailingLLM())
    plan = OrchestrationPlan(
        summary="失败依赖",
        steps=[
            ServiceStep(step_id=1, action="失败", tool="missing_tool", params={}),
            ServiceStep(
                step_id=2,
                action="不应执行",
                tool="ac_control",
                params={"zone": "driver", "temp": 20},
                dependency=1,
            ),
        ],
    )

    results = await orchestrator.execute(plan, context)

    assert not results[0].success
    assert results[1].skipped
    assert context.vehicle.cabin.ac.zone_temp["driver"] != 20


@pytest.mark.asyncio
async def test_output_formatter_builds_complete_agent_response() -> None:
    llm = QueueLLM(['{"user_response":"已为您找到附近停车场。"}'])
    _, context = _context("commute_arrival")
    intent = IntentResult(
        detected_intent="通勤停车准备",
        intent_type="implicit",
        confidence=0.9,
        context_factors=["接近公司"],
    )
    plan = OrchestrationPlan(
        summary="搜索停车场",
        steps=[],
        requires_confirmation=True,
        confirmation_message="是否导航到推荐停车场？",
    )

    response = await OutputFormatter(llm).format(
        intent, plan, [], SafetyResult(), context
    )

    assert response.user_response == "已为您找到附近停车场。"
    assert response.reasoning.detected_intent == "通勤停车准备"
    assert response.follow_up.needs_confirmation
    assert response.session_id == "session"


SCENARIOS = [
    ("fatigue_driving", "我有点困", "safety_alert_tool", "S01"),
    ("parent_child", "带宝宝出门，帮我准备一下", "ac_control", "S02"),
    ("long_distance_charging", "续航不够，找个充电站", "search_charger", None),
    ("commute_arrival", "快到公司了，帮我找停车位", "search_parking", None),
    ("robotaxi_cant_find_car", "我找不到车，车在哪", "locate_vehicle", None),
    ("pickup_abnormal", "这里施工，帮我换个上车点", "search_poi", "S08"),
    ("change_destination", "我想改去广州塔", "get_order_status", None),
    ("passenger_help", "我身体不舒服，需要求助", "emergency_stop", "S04"),
]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("scenario_id", "message", "expected_tool", "expected_rule"),
    SCENARIOS,
)
async def test_all_eight_scenarios_run_end_to_end_offline(
    scenario_id: str,
    message: str,
    expected_tool: str,
    expected_rule: str | None,
) -> None:
    agent = Agent(llm=FailingLLM())
    context = agent.context_manager.reset("session", scenario_id)

    response = await agent.process("session", message)

    assert expected_tool in {step.tool for step in response.service_plan.steps}
    if expected_rule:
        assert expected_rule in {alert.rule_id for alert in response.safety_alerts}
    assert response.session_id == "session"
    assert response.turn_id == 1
    assert context.messages[-2].role == "user"
    assert context.messages[-1].role == "assistant"
    assert response.user_response
    if scenario_id == "passenger_help":
        assert context.vehicle.speed == 0
        assert context.vehicle.driving_status == "parked"


@pytest.mark.asyncio
async def test_destination_change_requires_confirmation_without_mutation() -> None:
    agent = Agent(llm=FailingLLM())
    context = agent.context_manager.reset("session", "change_destination")
    original_destination = context.order.route.dropoff.address

    response = await agent.process("session", "我想改去广州塔")

    assert response.follow_up.needs_confirmation
    assert "广州塔" in response.follow_up.confirmation_message
    assert context.order.route.dropoff.address == original_destination
    assert "modify_order" not in {step.tool for step in response.service_plan.steps}
