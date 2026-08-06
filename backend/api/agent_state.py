"""Agent 会话状态查询、更新与模式切换接口。"""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from api.runtime import AppRuntime, get_runtime
from models.environment import EnvironmentContext
from models.order import OrderState
from models.user_profile import UserProfile
from models.vehicle import VehicleState


router = APIRouter(prefix="/api", tags=["Agent 状态"])


class StateUpdateRequest(BaseModel):
    vehicle: VehicleState | None = None
    environment: EnvironmentContext | None = None
    order: OrderState | None = None
    user_profile: UserProfile | None = None


class ModeSwitchRequest(BaseModel):
    session_id: str = Field(min_length=1)
    mode: Literal["owner", "robotaxi"]


@router.get("/state/{session_id}")
async def get_agent_state(
    session_id: str,
    app_runtime: AppRuntime = Depends(get_runtime),
) -> dict:
    """返回会话的车辆、环境、订单、画像和消息历史。"""

    context = app_runtime.agent.context_manager.get_context(session_id)
    return context.prompt_snapshot(history_limit=100)


@router.post("/state/{session_id}")
async def update_agent_state(
    session_id: str,
    request: StateUpdateRequest,
    app_runtime: AppRuntime = Depends(get_runtime),
) -> dict:
    """按字段更新会话状态；显式传入 null 的订单会清空当前订单。"""

    context = app_runtime.agent.context_manager.get_context(session_id)
    if request.vehicle is not None:
        context.vehicle = request.vehicle.model_copy(deep=True)
    if request.environment is not None:
        context.environment = request.environment.model_copy(deep=True)
    if "order" in request.model_fields_set:
        context.order = request.order.model_copy(deep=True) if request.order else None
    if request.user_profile is not None:
        context.user_profile = request.user_profile.model_copy(deep=True)
        app_runtime.agent.user_profile_manager.save_profile(context.user_profile)
    return context.prompt_snapshot(history_limit=100)


@router.post("/mode")
async def switch_mode(
    request: ModeSwitchRequest,
    app_runtime: AppRuntime = Depends(get_runtime),
) -> dict:
    """在不丢失当前会话历史的前提下切换 owner/robotaxi 模式。"""

    context = app_runtime.agent.context_manager.get_context(request.session_id)
    context.vehicle.mode = request.mode
    context.user_profile.role = "owner" if request.mode == "owner" else "passenger"
    app_runtime.agent.user_profile_manager.save_profile(context.user_profile)
    return {
        "session_id": request.session_id,
        "mode": request.mode,
        "state": context.prompt_snapshot(history_limit=100),
    }


__all__ = [
    "ModeSwitchRequest",
    "StateUpdateRequest",
    "get_agent_state",
    "router",
    "switch_mode",
    "update_agent_state",
]
