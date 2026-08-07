"""API 层共享的 Agent 运行时。"""

from __future__ import annotations

from config.settings import get_settings
from core.agent import Agent
from core.context_manager import ContextManager
from core.persistence import PostgresRedisPersistence
from core.user_profile_manager import UserProfileManager


class AppRuntime:
    """保证 REST 与 Socket.IO 使用同一个 Agent 和会话状态。"""

    def __init__(
        self,
        agent: Agent | None = None,
        persistence: PostgresRedisPersistence | None = None,
    ) -> None:
        if agent is not None:
            self.persistence = persistence
            self.agent = agent
            return

        settings = get_settings()
        self.persistence = persistence or PostgresRedisPersistence(
            database_url=settings.database_url,
            redis_url=settings.redis_url,
            redis_ttl_seconds=settings.redis_cache_ttl_seconds,
            required=settings.persistence_required,
        )
        self.agent = Agent(
            context_manager=ContextManager(self.persistence),
            user_profile_manager=UserProfileManager(self.persistence),
        )

    def initialize(self) -> None:
        if self.persistence:
            self.persistence.initialize()

    def close(self) -> None:
        if self.persistence:
            self.persistence.close()


runtime = AppRuntime()


def get_runtime() -> AppRuntime:
    """FastAPI 依赖入口，测试时可覆盖。"""

    return runtime


__all__ = ["AppRuntime", "get_runtime", "runtime"]
