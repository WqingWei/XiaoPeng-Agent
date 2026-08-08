"""场景切换 REST 接口。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from api.runtime import AppRuntime, get_runtime
from mock.scenario_presets import SCENARIO_IDS, get_scenario_meta


router = APIRouter(prefix="/api", tags=["场景"])


class ScenarioSwitchRequest(BaseModel):
    scenario_id: str = Field(min_length=1)
    session_id: str = Field(min_length=1)


@router.post("/scenario")
async def switch_scenario(
    request: ScenarioSwitchRequest,
    app_runtime: AppRuntime = Depends(get_runtime),
) -> dict:
    """切换指定会话的场景状态，同时保留消息历史。"""

    if request.scenario_id not in SCENARIO_IDS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "message": f"未知场景 ID: {request.scenario_id}",
                "available_scenarios": SCENARIO_IDS,
            },
        )

    context = app_runtime.agent.context_manager.switch_scenario(
        request.session_id, request.scenario_id
    )
    app_runtime.agent.user_profile_manager.save_profile(context.user_profile)
    return {
        "session_id": request.session_id,
        "scenario_id": request.scenario_id,
        "scenario": get_scenario_meta(request.scenario_id),
        "state": context.prompt_snapshot(history_limit=100),
    }


@router.delete("/scenario/{session_id}")
async def clear_scenario(
    session_id: str,
    app_runtime: AppRuntime = Depends(get_runtime),
) -> dict:
    """取消当前场景，保留模式、消息历史并恢复中性默认状态。"""

    context = app_runtime.agent.context_manager.clear_scenario(session_id)
    mode = context.vehicle.mode
    app_runtime.agent.user_profile_manager.save_profile(context.user_profile)
    return {
        "session_id": session_id,
        "scenario_id": None,
        "mode": mode,
        "state": context.prompt_snapshot(history_limit=100),
    }


__all__ = [
    "ScenarioSwitchRequest",
    "clear_scenario",
    "router",
    "switch_scenario",
]
