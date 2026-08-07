"""PostgreSQL 持久化与 Redis 会话缓存。"""

from __future__ import annotations

import json
from collections.abc import Mapping
from threading import RLock
from typing import Any, Protocol

from loguru import logger
from psycopg.types.json import Jsonb
from psycopg_pool import ConnectionPool
from redis import Redis


class PersistenceBackend(Protocol):
    """上下文与画像持久化所需的最小接口。"""

    def load_context(self, session_id: str) -> dict[str, Any] | None: ...

    def save_context(self, session_id: str, payload: Mapping[str, Any]) -> None: ...

    def delete_context(self, session_id: str) -> None: ...

    def load_profile(self, user_id: str) -> dict[str, Any] | None: ...

    def save_profile(self, user_id: str, payload: Mapping[str, Any]) -> None: ...


class PostgresRedisPersistence:
    """以 PostgreSQL 为真源、Redis 为读缓存的同步持久化实现。"""

    def __init__(
        self,
        *,
        database_url: str = "",
        redis_url: str = "",
        redis_ttl_seconds: int = 86_400,
        required: bool = False,
    ) -> None:
        self.database_url = database_url.strip()
        self.redis_url = redis_url.strip()
        self.redis_ttl_seconds = redis_ttl_seconds
        self.required = required
        self._pool: ConnectionPool | None = None
        self._redis: Redis | None = None
        self._initialized = False
        self._lock = RLock()

    @property
    def enabled(self) -> bool:
        return bool(self.database_url or self.redis_url)

    def initialize(self) -> None:
        """连接已配置的存储，并创建 PostgreSQL 表。"""

        with self._lock:
            if self._initialized:
                return
            if not self.enabled:
                if self.required:
                    raise RuntimeError("持久化被设为必需，但未配置 PostgreSQL/Redis")
                self._initialized = True
                return

            if self.database_url:
                pool: ConnectionPool | None = None
                try:
                    pool = ConnectionPool(
                        conninfo=self.database_url,
                        min_size=1,
                        max_size=5,
                        open=False,
                    )
                    pool.open(wait=True, timeout=10)
                    with pool.connection() as connection:
                        connection.execute(
                            """
                            CREATE TABLE IF NOT EXISTS agent_sessions (
                                session_id TEXT PRIMARY KEY,
                                context JSONB NOT NULL,
                                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                            )
                            """
                        )
                        connection.execute(
                            """
                            CREATE TABLE IF NOT EXISTS user_profiles (
                                user_id TEXT PRIMARY KEY,
                                profile JSONB NOT NULL,
                                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                            )
                            """
                        )
                    self._pool = pool
                    logger.info("PostgreSQL 会话持久化已连接")
                except Exception as exc:
                    if pool is not None:
                        pool.close()
                    self._handle_error("连接 PostgreSQL", exc)

            if self.redis_url:
                try:
                    redis_client = Redis.from_url(
                        self.redis_url,
                        decode_responses=True,
                        socket_connect_timeout=5,
                        socket_timeout=5,
                    )
                    redis_client.ping()
                    self._redis = redis_client
                    logger.info("Redis 会话缓存已连接")
                except Exception as exc:
                    self._handle_error("连接 Redis", exc)

            if self.required and not (self._pool or self._redis):
                raise RuntimeError("持久化被设为必需，但 PostgreSQL/Redis 均不可用")
            self._initialized = True

    def close(self) -> None:
        with self._lock:
            if self._redis is not None:
                self._redis.close()
                self._redis = None
            if self._pool is not None:
                self._pool.close()
                self._pool = None
            self._initialized = False

    def load_context(self, session_id: str) -> dict[str, Any] | None:
        self._ensure_initialized()
        key = self._context_key(session_id)
        cached = self._cache_get(key)
        if cached is not None:
            return cached

        payload = self._postgres_load(
            "SELECT context FROM agent_sessions WHERE session_id = %s",
            session_id,
            action="读取会话",
        )
        if payload is not None:
            self._cache_set(key, payload)
        return payload

    def save_context(self, session_id: str, payload: Mapping[str, Any]) -> None:
        self._ensure_initialized()
        normalized = dict(payload)
        self._postgres_save(
            """
            INSERT INTO agent_sessions (session_id, context, updated_at)
            VALUES (%s, %s, NOW())
            ON CONFLICT (session_id) DO UPDATE
            SET context = EXCLUDED.context, updated_at = NOW()
            """,
            session_id,
            normalized,
            action="保存会话",
        )
        self._cache_set(self._context_key(session_id), normalized)

    def delete_context(self, session_id: str) -> None:
        self._ensure_initialized()
        if self._pool is not None:
            try:
                with self._pool.connection() as connection:
                    connection.execute(
                        "DELETE FROM agent_sessions WHERE session_id = %s",
                        (session_id,),
                    )
            except Exception as exc:
                self._handle_error("删除会话", exc)
        if self._redis is not None:
            try:
                self._redis.delete(self._context_key(session_id))
            except Exception as exc:
                self._handle_error("删除 Redis 会话缓存", exc)

    def load_profile(self, user_id: str) -> dict[str, Any] | None:
        self._ensure_initialized()
        key = self._profile_key(user_id)
        cached = self._cache_get(key)
        if cached is not None:
            return cached
        payload = self._postgres_load(
            "SELECT profile FROM user_profiles WHERE user_id = %s",
            user_id,
            action="读取用户画像",
        )
        if payload is not None:
            self._cache_set(key, payload)
        return payload

    def save_profile(self, user_id: str, payload: Mapping[str, Any]) -> None:
        self._ensure_initialized()
        normalized = dict(payload)
        self._postgres_save(
            """
            INSERT INTO user_profiles (user_id, profile, updated_at)
            VALUES (%s, %s, NOW())
            ON CONFLICT (user_id) DO UPDATE
            SET profile = EXCLUDED.profile, updated_at = NOW()
            """,
            user_id,
            normalized,
            action="保存用户画像",
        )
        self._cache_set(self._profile_key(user_id), normalized)

    def status(self) -> dict[str, bool]:
        return {
            "enabled": self.enabled,
            "postgres": self._pool is not None,
            "redis": self._redis is not None,
        }

    def _ensure_initialized(self) -> None:
        if not self._initialized:
            self.initialize()

    def _postgres_load(
        self,
        query: str,
        identifier: str,
        *,
        action: str,
    ) -> dict[str, Any] | None:
        if self._pool is None:
            return None
        try:
            with self._pool.connection() as connection:
                row = connection.execute(query, (identifier,)).fetchone()
            if row is None:
                return None
            value = row[0]
            return value if isinstance(value, dict) else json.loads(value)
        except Exception as exc:
            self._handle_error(action, exc)
            return None

    def _postgres_save(
        self,
        query: str,
        identifier: str,
        payload: Mapping[str, Any],
        *,
        action: str,
    ) -> None:
        if self._pool is None:
            return
        try:
            with self._pool.connection() as connection:
                connection.execute(query, (identifier, Jsonb(dict(payload))))
        except Exception as exc:
            self._handle_error(action, exc)

    def _cache_get(self, key: str) -> dict[str, Any] | None:
        if self._redis is None:
            return None
        try:
            value = self._redis.get(key)
            return json.loads(value) if value else None
        except Exception as exc:
            self._handle_error("读取 Redis 缓存", exc)
            return None

    def _cache_set(self, key: str, payload: Mapping[str, Any]) -> None:
        if self._redis is None:
            return
        try:
            value = json.dumps(payload, ensure_ascii=False)
            if self.redis_ttl_seconds > 0:
                self._redis.set(key, value, ex=self.redis_ttl_seconds)
            else:
                self._redis.set(key, value)
        except Exception as exc:
            self._handle_error("写入 Redis 缓存", exc)

    def _handle_error(self, action: str, exc: Exception) -> None:
        if self.required:
            raise RuntimeError(f"{action}失败: {exc}") from exc
        logger.warning(f"{action}失败，继续使用可用存储或进程内状态: {exc}")

    @staticmethod
    def _context_key(session_id: str) -> str:
        return f"xiaopeng:session:{session_id}"

    @staticmethod
    def _profile_key(user_id: str) -> str:
        return f"xiaopeng:profile:{user_id}"


__all__ = ["PersistenceBackend", "PostgresRedisPersistence"]
