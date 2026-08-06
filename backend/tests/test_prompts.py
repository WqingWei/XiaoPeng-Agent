"""步骤八：系统 Prompt、Few-shot 与 Jinja 模板测试。"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from jinja2 import Environment, FileSystemLoader, StrictUndefined

from mock.scenario_presets import SCENARIO_IDS, load_scenario
from models.agent_output import AgentResponse
from prompts.few_shot_examples import (
    SCENARIO_FEW_SHOT_EXAMPLES,
    get_few_shot_examples,
)
from prompts.system_prompt import build_system_prompt


TEMPLATE_DIR = Path(__file__).parents[1] / "prompts" / "templates"


def test_system_prompt_contains_role_tools_rules_schema_and_state() -> None:
    vehicle, environment, order, user, _ = load_scenario("passenger_help")

    prompt = build_system_prompt(
        vehicle.mode, vehicle, environment, order, user
    )

    assert "小鹏 AI 出行服务管家" in prompt
    assert "Robotaxi 乘客服务" in prompt
    assert '"name": "emergency_stop"' in prompt
    assert '"rule_id": "S04"' in prompt
    assert '"user_response"' in prompt
    assert vehicle.vehicle_id in prompt


def test_each_scenario_has_two_complete_examples() -> None:
    assert set(SCENARIO_FEW_SHOT_EXAMPLES) == set(SCENARIO_IDS)

    for groups in SCENARIO_FEW_SHOT_EXAMPLES.values():
        assert len(groups) == 2
        for messages in groups:
            assert [message["role"] for message in messages] == ["user", "assistant"]
            AgentResponse.model_validate_json(messages[1]["content"])


def test_all_examples_flatten_to_32_messages() -> None:
    messages = get_few_shot_examples()

    assert len(messages) == 32
    assert sum(message["role"] == "user" for message in messages) == 16
    assert sum(message["role"] == "assistant" for message in messages) == 16


def test_unknown_few_shot_scenario_is_rejected() -> None:
    with pytest.raises(ValueError, match="未知场景"):
        get_few_shot_examples("missing")


@pytest.mark.parametrize(
    ("template_name", "variables", "expected"),
    [
        (
            "intent_analysis.j2",
            {
                "user_message": "我有点困",
                "mode": "owner",
                "vehicle": {"speed": 100},
                "environment": {"time": {"period": "night"}},
                "order": None,
                "user_profile": {"role": "owner"},
                "conversation_history": [],
            },
            '"detected_intent"',
        ),
        (
            "service_planning.j2",
            {
                "intent": {"detected_intent": "找充电站"},
                "safety": {"safety_level": "L1"},
                "context": {"vehicle": {"battery": 18}},
                "tools": [{"name": "search_charger"}],
            },
            '"steps"',
        ),
        (
            "response_generation.j2",
            {
                "intent": {"detected_intent": "找充电站"},
                "plan": {"steps": []},
                "tool_results": [],
                "safety": {"safety_level": "L0"},
                "mode": "owner",
                "is_driving": True,
            },
            '"user_response"',
        ),
    ],
)
def test_templates_render_with_strict_variables(
    template_name: str,
    variables: dict,
    expected: str,
) -> None:
    environment = Environment(
        loader=FileSystemLoader(TEMPLATE_DIR),
        undefined=StrictUndefined,
        autoescape=False,
    )

    rendered = environment.get_template(template_name).render(**variables)

    assert expected in rendered
    assert json.dumps(variables, ensure_ascii=False).startswith("{")
