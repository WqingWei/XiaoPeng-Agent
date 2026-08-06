"""步骤八：上下文与用户画像管理测试。"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from core.context_manager import ContextManager
from core.user_profile_manager import UserProfileManager
from mock.vehicle_mock import create_fatigue_driving_state
from models.user_profile import UserProfile


def test_context_is_created_and_isolated_by_session() -> None:
    manager = ContextManager()

    first = manager.get_context("session-a")
    second = manager.get_context("session-b")
    first.vehicle.speed = 42

    assert first.session_id == "session-a"
    assert second.session_id == "session-b"
    assert second.vehicle.speed == 0
    assert manager.session_count == 2


def test_add_message_tracks_history_and_turns() -> None:
    manager = ContextManager()

    manager.add_message("session", "user", "打开空调")
    manager.add_message("session", "assistant", "已为您打开空调")

    context = manager.get_context("session")
    assert [message.role for message in context.messages] == ["user", "assistant"]
    assert context.turn_id == 1


def test_reset_loads_complete_scenario_and_clears_old_history() -> None:
    manager = ContextManager()
    manager.add_message("session", "user", "旧消息")

    context = manager.reset("session", "passenger_help")

    assert context.scenario_id == "passenger_help"
    assert context.vehicle.mode == "robotaxi"
    assert context.order is not None
    assert context.user_profile.role == "passenger"
    assert context.turn_id == 0
    assert len(context.messages) == 1
    assert context.messages[0].role == "system"


def test_update_vehicle_state_uses_deep_copy() -> None:
    manager = ContextManager()
    state = create_fatigue_driving_state()

    context = manager.update_vehicle_state("session", state)
    state.speed = 0

    assert context.vehicle.speed == 100


def test_prompt_snapshot_is_json_serializable_shape() -> None:
    manager = ContextManager()
    context = manager.reset("session", "fatigue_driving")
    manager.add_message("session", "user", "我有点困")

    snapshot = context.prompt_snapshot()

    assert snapshot["scenario_id"] == "fatigue_driving"
    assert snapshot["vehicle"]["driver"]["fatigue_level"] == 2
    assert snapshot["messages"][-1]["content"] == "我有点困"


@pytest.mark.parametrize("value", ["", "   "])
def test_context_rejects_empty_session_id(value: str) -> None:
    with pytest.raises(ValueError):
        ContextManager().get_context(value)


def test_profile_load_save_and_copy_isolation() -> None:
    manager = UserProfileManager()
    saved = manager.save_profile(UserProfile(user_id="U-9", name="王女士"))
    saved.name = "外部修改"

    loaded = manager.load_profile("U-9")

    assert loaded.name == "王女士"


def test_profile_updates_preferences_and_history() -> None:
    manager = UserProfileManager()

    updated = manager.update_preferences(
        "U-1", {"ac_temp_default": 25.5, "music_genre": "jazz"}
    )
    with_trip = manager.add_recent_trip("U-1", {"destination": "公司"})

    assert updated.preferences.ac_temp_default == 25.5
    assert updated.preferences.music_genre == "jazz"
    assert with_trip.history.recent_trips == [{"destination": "公司"}]


def test_profile_rejects_unknown_or_invalid_preference() -> None:
    manager = UserProfileManager()

    with pytest.raises(ValueError, match="未知偏好字段"):
        manager.update_preferences("U-1", {"unknown": True})
    with pytest.raises(ValidationError):
        manager.update_preferences("U-1", {"language": "fr"})
