"""API 路由聚合。"""

from fastapi import APIRouter

from api.agent_state import router as agent_state_router
from api.scenario import router as scenario_router


router = APIRouter()
router.include_router(scenario_router)
router.include_router(agent_state_router)


__all__ = ["router"]
