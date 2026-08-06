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
    assert payload["state"]["vehicle"]["mode"] == "robotaxi"
    assert payload["state"]["user_profile"]["role"] == "passenger"


@pytest.mark.asyncio
async def test_mode_switch_rejects_unknown_mode(client: AsyncClient) -> None:
    response = await client.post(
        "/api/mode",
        json={"session_id": "s-1", "mode": "airplane"},
    )

    assert response.status_code == 422
