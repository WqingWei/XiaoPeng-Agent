"""步骤九：Socket.IO 聊天事件测试。"""

from __future__ import annotations

from typing import Any

import pytest

from api.chat import THINKING_STEPS, register_chat_handlers
from core.context_manager import ContextManager
from core.user_profile_manager import UserProfileManager
from models.agent_output import AgentResponse, Reasoning


class FakeSio:
    def __init__(self) -> None:
        self.handlers: dict[str, Any] = {}
        self.emitted: list[tuple[str, dict, str | None]] = []

    def on(self, event: str):
        def decorator(handler):
            self.handlers[event] = handler
            return handler

        return decorator

    async def emit(self, event: str, data: dict, to: str | None = None) -> None:
        self.emitted.append((event, data, to))


class FakeAgent:
    def __init__(self, fail: bool = False) -> None:
        self.context_manager = ContextManager()
        self.user_profile_manager = UserProfileManager()
        self.fail = fail
        self.calls: list[tuple[str, str]] = []

    async def process(
        self,
        session_id: str,
        message: str,
        on_step=None,
        mode=None,
    ):
        self.calls.append((session_id, message))
        context = self.context_manager.get_context(session_id)
        if mode:
            context.vehicle.mode = mode
            context.user_profile.role = "owner" if mode == "owner" else "passenger"
        if self.fail:
            raise RuntimeError("模拟处理失败")
        for step in THINKING_STEPS:
            await on_step(step)
        return AgentResponse(
            session_id=session_id,
            turn_id=1,
            user_response="已完成处理。",
            reasoning=Reasoning(detected_intent="测试意图"),
        )


@pytest.mark.asyncio
async def test_chat_emits_four_thinking_steps_and_response() -> None:
    sio = FakeSio()
    agent = FakeAgent()
    handlers = register_chat_handlers(sio, agent)

    await handlers["chat_message"](
        "socket-1",
        {"session_id": "session-1", "message": "打开空调", "mode": "owner"},
    )

    assert [event for event, _, _ in sio.emitted] == [
        "agent_thinking",
        "agent_thinking",
        "agent_thinking",
        "agent_thinking",
        "vehicle_state_update",
        "agent_response",
    ]
    assert [data["step"] for event, data, _ in sio.emitted if event == "agent_thinking"] == list(THINKING_STEPS)
    assert sio.emitted[-1][1]["user_response"] == "已完成处理。"
    vehicle_event = next(
        data for event, data, _ in sio.emitted if event == "vehicle_state_update"
    )
    assert vehicle_event["session_id"] == "session-1"
    assert vehicle_event["vehicle"]["mode"] == "owner"
    assert all(target == "socket-1" for _, _, target in sio.emitted)
    assert agent.calls == [("session-1", "打开空调")]


@pytest.mark.asyncio
async def test_chat_applies_requested_mode_to_shared_context() -> None:
    sio = FakeSio()
    agent = FakeAgent()
    handlers = register_chat_handlers(sio, agent)

    await handlers["chat_message"](
        "socket-1",
        {"session_id": "session-1", "message": "车在哪", "mode": "robotaxi"},
    )

    context = agent.context_manager.get_context("session-1")
    assert context.vehicle.mode == "robotaxi"
    assert context.user_profile.role == "passenger"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "data",
    [
        None,
        {},
        {"session_id": "s", "message": "", "mode": "owner"},
        {"session_id": "s", "message": "你好", "mode": "airplane"},
    ],
)
async def test_chat_rejects_invalid_request(data: Any) -> None:
    sio = FakeSio()
    agent = FakeAgent()
    handlers = register_chat_handlers(sio, agent)

    await handlers["chat_message"]("socket-1", data)

    assert len(sio.emitted) == 1
    event, payload, target = sio.emitted[0]
    assert event == "agent_error"
    assert payload["code"] == "invalid_request"
    assert target == "socket-1"
    assert agent.calls == []


@pytest.mark.asyncio
async def test_chat_hides_internal_processing_error() -> None:
    sio = FakeSio()
    handlers = register_chat_handlers(sio, FakeAgent(fail=True))

    await handlers["chat_message"](
        "socket-1",
        {"session_id": "session-1", "message": "你好", "mode": "owner"},
    )

    event, payload, _ = sio.emitted[-1]
    assert event == "agent_error"
    assert payload == {
        "code": "processing_failed",
        "message": "消息处理暂时失败，请稍后重试。",
        "session_id": "session-1",
    }


@pytest.mark.asyncio
async def test_connect_and_disconnect_handlers() -> None:
    sio = FakeSio()
    handlers = register_chat_handlers(sio, FakeAgent())

    assert await handlers["connect"]("socket-1", {}, None) is True
    assert await handlers["disconnect"]("socket-1") is None
