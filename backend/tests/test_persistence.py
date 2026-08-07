"""会话与用户画像持久化测试。"""

from __future__ import annotations

import os
from collections.abc import Mapping
from typing import Any
from uuid import uuid4

import pytest

from core.context_manager import ContextManager
from core.persistence import PostgresRedisPersistence
from core.user_profile_manager import UserProfileManager
from models.user_profile import UserProfile


class FakePersistence:
    def __init__(self) -> None:
        self.contexts: dict[str, dict[str, Any]] = {}
        self.profiles: dict[str, dict[str, Any]] = {}

    def load_context(self, session_id: str) -> dict[str, Any] | None:
        return self.contexts.get(session_id)

    def save_context(self, session_id: str, payload: Mapping[str, Any]) -> None:
        self.contexts[session_id] = dict(payload)

    def delete_context(self, session_id: str) -> None:
        self.contexts.pop(session_id, None)

    def load_profile(self, user_id: str) -> dict[str, Any] | None:
        return self.profiles.get(user_id)

    def save_profile(self, user_id: str, payload: Mapping[str, Any]) -> None:
        self.profiles[user_id] = dict(payload)


def test_context_is_restored_by_new_manager_with_response_details() -> None:
    persistence = FakePersistence()
    first = ContextManager(persistence)
    first.add_message("session-a", "user", "打开空调")
    first.add_message(
        "session-a",
        "assistant",
        "已打开空调",
        agent_response={"session_id": "session-a", "turn_id": 1},
    )
    first.get_context("session-a").vehicle.speed = 42
    first.save(first.get_context("session-a"))

    restored = ContextManager(persistence).get_context("session-a")

    assert restored.turn_id == 1
    assert restored.vehicle.speed == 42
    assert [message.content for message in restored.messages] == [
        "打开空调",
        "已打开空调",
    ]
    assert restored.messages[-1].agent_response == {
        "session_id": "session-a",
        "turn_id": 1,
    }


def test_remove_deletes_memory_and_persistent_context() -> None:
    persistence = FakePersistence()
    manager = ContextManager(persistence)
    manager.get_context("session-a")

    assert manager.remove("session-a") is True
    assert "session-a" not in persistence.contexts


def test_profile_is_restored_by_new_manager() -> None:
    persistence = FakePersistence()
    first = UserProfileManager(persistence)
    first.save_profile(
        UserProfile(user_id="U-persisted", name="王女士", role="passenger")
    )

    restored = UserProfileManager(persistence).load_profile("U-persisted")

    assert restored.name == "王女士"
    assert restored.role == "passenger"


def test_unconfigured_persistence_is_safe_noop() -> None:
    persistence = PostgresRedisPersistence()

    persistence.initialize()
    persistence.save_context("session", {"session_id": "session"})

    assert persistence.load_context("session") is None
    assert persistence.status() == {
        "enabled": False,
        "postgres": False,
        "redis": False,
    }


def test_required_persistence_rejects_missing_configuration() -> None:
    with pytest.raises(RuntimeError, match="未配置 PostgreSQL/Redis"):
        PostgresRedisPersistence(required=True).initialize()


@pytest.mark.skipif(
    not os.getenv("TEST_DATABASE_URL") or not os.getenv("TEST_REDIS_URL"),
    reason="需要真实 PostgreSQL 与 Redis 测试地址",
)
def test_real_postgres_and_redis_round_trip() -> None:
    database_url = os.environ["TEST_DATABASE_URL"]
    redis_url = os.environ["TEST_REDIS_URL"]
    session_id = f"integration-{uuid4()}"
    payload = {
        "session_id": session_id,
        "scenario_id": None,
        "turn_id": 1,
        "messages": [],
        "vehicle": {"mode": "owner"},
    }

    combined = PostgresRedisPersistence(
        database_url=database_url,
        redis_url=redis_url,
        required=True,
    )
    combined.initialize()
    combined.save_context(session_id, payload)
    combined.close()

    postgres_only = PostgresRedisPersistence(
        database_url=database_url,
        required=True,
    )
    postgres_only.initialize()
    assert postgres_only.load_context(session_id) == payload
    postgres_only.close()

    redis_only = PostgresRedisPersistence(redis_url=redis_url, required=True)
    redis_only.initialize()
    assert redis_only.load_context(session_id) == payload
    redis_only.delete_context(session_id)
    redis_only.close()

    cleanup = PostgresRedisPersistence(database_url=database_url, required=True)
    cleanup.initialize()
    cleanup.delete_context(session_id)
    cleanup.close()
