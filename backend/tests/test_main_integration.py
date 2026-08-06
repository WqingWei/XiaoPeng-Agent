"""步骤九：FastAPI 与 Socket.IO 挂载集成测试。"""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from main import app, sio, sio_asgi_app


@pytest.mark.asyncio
async def test_main_exposes_health_config_and_step9_routes() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        health = await client.get("/health")
        config = await client.get("/api/config")
        state = await client.get("/api/state/integration")

    assert health.status_code == 200
    assert health.json() == {"status": "ok"}
    assert config.status_code == 200
    assert "model_name" in config.json()
    assert state.status_code == 200
    assert state.json()["session_id"] == "integration"


def test_main_registered_socketio_handlers() -> None:
    assert {"connect", "disconnect", "chat_message"}.issubset(
        sio.handlers["/"]
    )


@pytest.mark.asyncio
async def test_socketio_asgi_polling_handshake() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=sio_asgi_app),
        base_url="http://test",
    ) as client:
        response = await client.get("/socket.io/?EIO=4&transport=polling")

    assert response.status_code == 200
    assert response.text.startswith("0{")
