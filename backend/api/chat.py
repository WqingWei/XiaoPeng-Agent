"""Socket.IO 聊天事件处理。"""

from __future__ import annotations

from typing import Any, Literal

from loguru import logger
from pydantic import BaseModel, Field, ValidationError

from core.agent import Agent


THINKING_STEPS = (
    "intent_analysis",
    "safety_check",
    "orchestrating",
    "generating",
)


class ChatMessageRequest(BaseModel):
    session_id: str = Field(min_length=1)
    message: str = Field(min_length=1)
    mode: Literal["owner", "robotaxi"]


def register_chat_handlers(sio: Any, agent: Agent) -> dict[str, Any]:
    """在给定 Socket.IO server 上注册连接与聊天事件。"""

    async def connect(sid: str, environ: dict, auth: Any = None) -> bool:
        logger.info(f"Socket.IO client connected: {sid}")
        return True

    async def disconnect(sid: str, *args: Any) -> None:
        logger.info(f"Socket.IO client disconnected: {sid}")

    async def chat_message(sid: str, data: Any) -> None:
        try:
            request = ChatMessageRequest.model_validate(data)
        except ValidationError as exc:
            await sio.emit(
                "agent_error",
                {
                    "code": "invalid_request",
                    "message": "消息格式无效，请提供 session_id、message 和合法 mode。",
                    "details": exc.errors(
                        include_url=False,
                        include_input=False,
                    ),
                },
                to=sid,
            )
            return

        async def emit_step(step: str) -> None:
            await sio.emit(
                "agent_thinking",
                {"session_id": request.session_id, "step": step},
                to=sid,
            )

        try:
            response = await agent.process(
                request.session_id,
                request.message,
                on_step=emit_step,
                mode=request.mode,
            )
            context = agent.context_manager.get_context(request.session_id)
            await sio.emit(
                "vehicle_state_update",
                {
                    "session_id": request.session_id,
                    "vehicle": context.vehicle.model_dump(mode="json"),
                },
                to=sid,
            )
            await sio.emit(
                "agent_response",
                response.model_dump(mode="json"),
                to=sid,
            )
        except Exception:
            logger.exception(
                f"处理聊天消息失败: sid={sid}, session={request.session_id}"
            )
            await sio.emit(
                "agent_error",
                {
                    "code": "processing_failed",
                    "message": "消息处理暂时失败，请稍后重试。",
                    "session_id": request.session_id,
                },
                to=sid,
            )

    sio.on("connect")(connect)
    sio.on("disconnect")(disconnect)
    sio.on("chat_message")(chat_message)
    return {
        "connect": connect,
        "disconnect": disconnect,
        "chat_message": chat_message,
    }


__all__ = [
    "ChatMessageRequest",
    "THINKING_STEPS",
    "register_chat_handlers",
]
