"""小鹏 AI 出行服务管家 Agent — 后端入口

FastAPI 应用 + Socket.IO 挂载 + CORS + 健康检查端点。
"""

import socketio
import uvicorn
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from config.settings import get_settings

# ────────────────────────────────────────────
# Socket.IO 异步服务器
# ────────────────────────────────────────────
sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    logger=False,
    engineio_logger=False,
)

# ────────────────────────────────────────────
# Socket.IO 事件处理（占位，后续步骤九完善）
# ────────────────────────────────────────────

@sio.event
async def connect(sid, environ):
    logger.info(f"Socket.IO client connected: {sid}")


@sio.event
async def disconnect(sid):
    logger.info(f"Socket.IO client disconnected: {sid}")


@sio.event
async def chat_message(sid, data):
    """接收前端聊天消息（占位，后续步骤八实现完整 Agent 逻辑）"""
    logger.info(f"Received message from {sid}: {data}")
    await sio.emit(
        "agent_response",
        {
            "user_response": "你好！我是小鹏 AI 出行服务管家，后端已就绪，Agent 核心引擎正在开发中。",
            "service_plan": {"summary": "占位响应", "steps": [], "total_estimated_time_s": 0},
            "reasoning": {"detected_intent": "待实现", "intent_type": "explicit"},
            "forbidden_actions": [],
            "safety_alerts": [],
        },
        to=sid,
    )


# ────────────────────────────────────────────
# FastAPI 应用
# ────────────────────────────────────────────
settings = get_settings()

logger.remove()
logger.add(
    lambda msg: print(msg, end=""),
    level=settings.log_level,
    format="<green>{time:HH:mm:ss}</green> | <level>{level:<7}</level> | {message}",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：启动 / 关闭时的日志"""
    logger.info("🚀 小鹏 AI 出行服务管家 Agent 后端启动")
    logger.info(f"   模型: {settings.model_name} (主) / {settings.model_name_lite} (轻)")
    logger.info(f"   API:  {settings.openai_base_url}")
    logger.info(f"   端口: {settings.backend_port}")
    yield
    logger.info("🛑 后端服务已关闭")


app = FastAPI(
    title="小鹏 AI 出行服务管家 Agent",
    description="基于 LLM 的出行服务编排 Agent 后端 API",
    version="0.1.0",
    lifespan=lifespan,
)

# ── CORS ──
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── 挂载 Socket.IO ASGI 应用 ──
sio_asgi_app = socketio.ASGIApp(socketio_server=sio, other_asgi_app=app)


# ────────────────────────────────────────────
# REST 端点
# ────────────────────────────────────────────

@app.get("/health", tags=["系统"])
async def health_check():
    """健康检查端点"""
    return {"status": "ok"}


@app.get("/api/config", tags=["系统"])
async def get_config():
    """返回当前模型和模式配置（不暴露 API Key）"""
    return {
        "model_name": settings.model_name,
        "model_name_lite": settings.model_name_lite,
        "base_url": settings.openai_base_url,
    }


# ────────────────────────────────────────────
# 入口
# ────────────────────────────────────────────

if __name__ == "__main__":
    uvicorn.run(
        "main:sio_asgi_app",
        host="0.0.0.0",
        port=settings.backend_port,
        reload=True,
        log_level=settings.log_level.lower(),
    )
