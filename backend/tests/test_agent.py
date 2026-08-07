"""步骤十：Agent 最小闭环与核心契约测试。"""

from __future__ import annotations

from typing import Any

import pytest

from core.agent import Agent
from models.agent_output import AgentResponse


class FailingLLM:
    """强制走生产代码的本地降级链，测试不访问外部模型。"""

    async def ainvoke(self, messages: Any):
        raise RuntimeError("Agent 测试禁用外部 LLM")


@pytest.mark.asyncio
async def test_agent_minimum_ac_control_loop() -> None:
    agent = Agent(llm=FailingLLM())

    response = await agent.process("agent-minimal", "帮我打开空调")

    AgentResponse.model_validate(response.model_dump())
    assert response.user_response
    assert "ac_control" in {step.tool for step in response.service_plan.steps}
    assert response.reasoning.detected_intent == "调节座舱空调"
    assert response.reasoning.tool_selection_reasons
    assert response.session_id == "agent-minimal"
    assert response.turn_id == 1
    context = agent.context_manager.get_context("agent-minimal")
    assert context.vehicle.cabin.ac.zone_temp["driver"] == 24
    assert [message.role for message in context.messages] == ["user", "assistant"]


@pytest.mark.asyncio
async def test_agent_rejects_empty_message() -> None:
    agent = Agent(llm=FailingLLM())

    with pytest.raises(ValueError, match="user_message 不能为空"):
        await agent.process("agent-empty", "   ")


@pytest.mark.asyncio
async def test_agent_tracks_multiple_turns() -> None:
    agent = Agent(llm=FailingLLM())

    first = await agent.process("agent-turns", "查询车辆状态")
    second = await agent.process("agent-turns", "空调调到23度")

    context = agent.context_manager.get_context("agent-turns")
    assert first.turn_id == 1
    assert second.turn_id == 2
    assert context.turn_id == 2
    assert len(context.messages) == 4
    assert context.vehicle.cabin.ac.zone_temp["driver"] == 23


@pytest.mark.asyncio
async def test_agent_safety_blocks_video_while_driving() -> None:
    agent = Agent(llm=FailingLLM())
    agent.context_manager.reset("agent-video", "commute_arrival")

    response = await agent.process("agent-video", "给我播放视频")

    assert "media_control" not in {
        step.tool for step in response.service_plan.steps
    }
    assert "S05" in {item.rule_id for item in response.forbidden_actions}
    assert "S05" in {item.rule_id for item in response.safety_alerts}
    assert response.user_response
