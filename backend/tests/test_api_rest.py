"""步骤九：场景、状态与模式 REST API 测试。"""

from __future__ import annotations

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from api.router import router
from api.runtime import AppRuntime, get_runtime
from core.agent import Agent


@pytest.fixture
def runtime() -> AppRuntime:
    return AppRuntime(agent=Agent(llm=_FailingLLM()))


@pytest.fixture
def app(runtime: AppRuntime) -> FastAPI:
    application = FastAPI()
    application.include_router(router)
    application.dependency_overrides[get_runtime] = lambda: runtime
    return application


class _FailingLLM:
    async def ainvoke(self, messages):
        raise RuntimeError("REST 测试不访问外部 LLM")


@pytest_asyncio.fixture
async def client(app: FastAPI):
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as api_client:
        yield api_client


@pytest.mark.asyncio
async def test_switch_scenario_returns_complete_initial_state(client: AsyncClient) -> None:
    response = await client.post(
        "/api/scenario",
        json={"session_id": "s-1", "scenario_id": "passenger_help"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["scenario_id"] == "passenger_help"
    assert payload["state"]["vehicle"]["mode"] == "robotaxi"
    assert payload["state"]["order"]["status"] == "in_trip"
    assert payload["state"]["messages"][0]["role"] == "system"


@pytest.mark.asyncio
async def test_switch_scenario_preserves_existing_conversation(
    client: AsyncClient,
    runtime: AppRuntime,
) -> None:
    await client.post(
        "/api/scenario",
        json={"session_id": "s-history", "scenario_id": "fatigue_driving"},
    )
    runtime.agent.context_manager.add_message("s-history", "user", "记住这条消息")
    runtime.agent.context_manager.add_message("s-history", "assistant", "我会记住")

    response = await client.post(
        "/api/scenario",
        json={"session_id": "s-history", "scenario_id": "commute_arrival"},
    )

    assert response.status_code == 200
    state = response.json()["state"]
    assert state["turn_id"] == 1
    assert [message["content"] for message in state["messages"][-3:-1]] == [
        "记住这条消息",
        "我会记住",
    ]
    assert "通勤到达" in state["messages"][-1]["content"]


@pytest.mark.asyncio
async def test_unknown_scenario_returns_404_with_available_ids(client: AsyncClient) -> None:
    response = await client.post(
        "/api/scenario",
        json={"session_id": "s-1", "scenario_id": "missing"},
    )

    assert response.status_code == 404
    assert "fatigue_driving" in response.json()["detail"]["available_scenarios"]


@pytest.mark.asyncio
async def test_state_get_creates_and_returns_session(client: AsyncClient) -> None:
    response = await client.get("/api/state/new-session")

    assert response.status_code == 200
    assert response.json()["session_id"] == "new-session"
    assert response.json()["vehicle"]["speed"] == 0


@pytest.mark.asyncio
async def test_state_post_updates_vehicle_and_can_clear_order(
    client: AsyncClient,
) -> None:
    await client.post(
        "/api/scenario",
        json={"session_id": "s-1", "scenario_id": "change_destination"},
    )
    current = (await client.get("/api/state/s-1")).json()
    current["vehicle"]["speed"] = 12

    response = await client.post(
        "/api/state/s-1",
        json={"vehicle": current["vehicle"], "order": None},
    )

    assert response.status_code == 200
    assert response.json()["vehicle"]["speed"] == 12
    assert response.json()["order"] is None


@pytest.mark.asyncio
async def test_state_post_rejects_invalid_vehicle(client: AsyncClient) -> None:
    response = await client.post(
        "/api/state/s-1",
        json={"vehicle": {"speed": -1}},
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_mode_switch_updates_vehicle_and_user_role(client: AsyncClient) -> None:
    response = await client.post(
        "/api/mode",
        json={"session_id": "s-1", "mode": "robotaxi"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["mode"] == "robotaxi"
    assert payload["scenario_id"] == "robotaxi_cant_find_car"
    assert payload["state"]["vehicle"]["mode"] == "robotaxi"
    assert payload["state"]["user_profile"]["role"] == "passenger"
    assert payload["state"]["order"] is not None


@pytest.mark.asyncio
async def test_mode_switch_replaces_incompatible_scenario(
    client: AsyncClient,
    runtime: AppRuntime,
) -> None:
    await client.post(
        "/api/scenario",
        json={"session_id": "s-1", "scenario_id": "passenger_help"},
    )
    runtime.agent.context_manager.add_message("s-1", "user", "我想切换模式")
    runtime.agent.context_manager.add_message("s-1", "assistant", "好的")

    response = await client.post(
        "/api/mode",
        json={"session_id": "s-1", "mode": "owner"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["scenario_id"] == "fatigue_driving"
    assert payload["state"]["scenario_id"] == "fatigue_driving"
    assert payload["state"]["vehicle"]["mode"] == "owner"
    assert payload["state"]["order"] is None
    assert payload["state"]["turn_id"] == 1
    assert not any(
        message["content"] == "我想切换模式"
        for message in payload["state"]["messages"]
    )

    restored = await client.post(
        "/api/mode",
        json={"session_id": "s-1", "mode": "robotaxi"},
    )

    assert restored.status_code == 200
    restored_messages = restored.json()["state"]["messages"]
    assert any(
        message["content"] == "我想切换模式"
        for message in restored_messages
    )
    assert not any(
        message["mode"] == "owner"
        for message in restored_messages
    )


@pytest.mark.asyncio
async def test_clear_scenario_keeps_mode_and_removes_scenario_state(
    client: AsyncClient,
    runtime: AppRuntime,
) -> None:
    await client.post(
        "/api/scenario",
        json={"session_id": "s-1", "scenario_id": "passenger_help"},
    )
    runtime.agent.context_manager.add_message("s-1", "user", "保留这条历史")
    runtime.agent.context_manager.add_message("s-1", "assistant", "历史会保留")

    response = await client.delete("/api/scenario/s-1")

    assert response.status_code == 200
    payload = response.json()
    assert payload["scenario_id"] is None
    assert payload["mode"] == "robotaxi"
    assert payload["state"]["scenario_id"] is None
    assert payload["state"]["vehicle"]["mode"] == "robotaxi"
    assert payload["state"]["vehicle"]["speed"] == 0
    assert payload["state"]["order"] is None
    assert payload["state"]["turn_id"] == 1
    assert [
        message["content"] for message in payload["state"]["messages"][-3:]
    ] == [
        "保留这条历史",
        "历史会保留",
        "已取消场景选择，当前为Robotaxi自由对话模式。",
    ]


@pytest.mark.asyncio
async def test_mode_switch_rejects_unknown_mode(client: AsyncClient) -> None:
    response = await client.post(
        "/api/mode",
        json={"session_id": "s-1", "mode": "airplane"},
    )

    assert response.status_code == 422
