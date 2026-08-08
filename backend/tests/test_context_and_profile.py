"""步骤八：上下文与用户画像管理测试。"""

from __future__ import annotations

from typing import Literal

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
    assert [message.mode for message in context.messages] == ["owner", "owner"]
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


def test_switch_scenario_preserves_history_turn_and_adds_transition() -> None:
    manager = ContextManager()
    manager.add_message("session", "user", "先帮我打开空调")
    manager.add_message("session", "assistant", "空调已打开")

    context = manager.switch_scenario("session", "passenger_help")

    assert context.scenario_id == "passenger_help"
    assert context.vehicle.mode == "robotaxi"
    assert context.turn_id == 1
    assert [message.role for message in context.messages] == [
        "user",
        "assistant",
        "system",
    ]
    assert context.messages[0].content == "先帮我打开空调"
    assert "乘客求助" in context.messages[-1].content


def test_clear_scenario_preserves_history_and_creates_neutral_state() -> None:
    manager = ContextManager()
    manager.switch_scenario("session", "passenger_help")
    manager.add_message("session", "user", "我现在没事了")

    context = manager.clear_scenario("session")

    assert context.scenario_id is None
    assert context.vehicle.mode == "robotaxi"
    assert context.vehicle.speed == 0
    assert context.order is None
    assert context.turn_id == 1
    assert context.messages[-2].content == "我现在没事了"
    assert "已取消场景选择" in context.messages[-1].content


def test_messages_and_snapshot_are_isolated_by_mode() -> None:
    manager = ContextManager()
    manager.switch_scenario("session", "fatigue_driving")
    manager.add_message("session", "user", "车主模式消息")
    manager.switch_scenario("session", "passenger_help")
    manager.add_message("session", "user", "Robotaxi模式消息")

    context = manager.get_context("session")

    assert [message.content for message in context.messages_for_mode("owner")] == [
        context.messages[0].content,
        "车主模式消息",
    ]
    assert [
        message.content for message in context.messages_for_mode("robotaxi")
    ] == [
        context.messages[2].content,
        "Robotaxi模式消息",
    ]
    assert all(
        message["mode"] == "robotaxi"
        for message in context.prompt_snapshot()["messages"]
    )


@pytest.mark.parametrize(
    ("mode", "role"),
    [("owner", "owner"), ("robotaxi", "passenger")],
)
def test_reset_to_mode_clears_scenario_and_creates_neutral_state(
    mode: Literal["owner", "robotaxi"],
    role: Literal["owner", "passenger"],
) -> None:
    manager = ContextManager()
    manager.reset("session", "passenger_help")

    context = manager.reset_to_mode("session", mode)

    assert context.scenario_id is None
    assert context.vehicle.mode == mode
    assert context.vehicle.speed == 0
    assert context.order is None
    assert context.messages == []
    assert context.user_profile.role == role


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
