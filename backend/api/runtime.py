"""API 层共享的 Agent 运行时。"""

from __future__ import annotations

from core.agent import Agent


class AppRuntime:
    """保证 REST 与 Socket.IO 使用同一个 Agent 和会话状态。"""

    def __init__(self, agent: Agent | None = None) -> None:
        self.agent = agent or Agent()


runtime = AppRuntime()


def get_runtime() -> AppRuntime:
    """FastAPI 依赖入口，测试时可覆盖。"""

    return runtime


__all__ = ["AppRuntime", "get_runtime", "runtime"]
