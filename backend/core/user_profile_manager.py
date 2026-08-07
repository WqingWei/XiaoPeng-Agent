"""用户画像的内存加载与更新管理。"""

from __future__ import annotations

from collections.abc import Mapping
from threading import RLock
from typing import Any, Literal

from core.persistence import PersistenceBackend
from models.user_profile import UserProfile, UserPreferences


class UserProfileManager:
    """按用户 ID 管理画像，并通过 Pydantic 保证更新后的类型安全。"""

    def __init__(self, persistence: PersistenceBackend | None = None) -> None:
        self._profiles: dict[str, UserProfile] = {}
        self._lock = RLock()
        self._persistence = persistence

    def load_profile(
        self,
        user_id: str,
        role: Literal["owner", "passenger"] = "owner",
    ) -> UserProfile:
        """读取画像；首次读取时创建默认画像。"""

        if not user_id or not user_id.strip():
            raise ValueError("user_id 不能为空")
        with self._lock:
            if user_id not in self._profiles:
                restored = (
                    self._persistence.load_profile(user_id)
                    if self._persistence
                    else None
                )
                self._profiles[user_id] = (
                    UserProfile.model_validate(restored)
                    if restored is not None
                    else UserProfile(user_id=user_id, role=role)
                )
            return self._profiles[user_id].model_copy(deep=True)

    def save_profile(self, profile: UserProfile) -> UserProfile:
        """保存完整画像并返回独立副本。"""

        with self._lock:
            self._profiles[profile.user_id] = profile.model_copy(deep=True)
            if self._persistence:
                self._persistence.save_profile(
                    profile.user_id,
                    profile.model_dump(mode="json"),
                )
            return self._profiles[profile.user_id].model_copy(deep=True)

    def update_preferences(
        self,
        user_id: str,
        updates: Mapping[str, Any],
    ) -> UserProfile:
        """局部更新用户偏好，未知字段会被拒绝。"""

        allowed = set(UserPreferences.model_fields)
        unknown = set(updates) - allowed
        if unknown:
            raise ValueError(f"未知偏好字段: {', '.join(sorted(unknown))}")

        with self._lock:
            profile = self.load_profile(user_id)
            preferences = profile.preferences.model_copy(update=dict(updates))
            # model_copy 不会重新验证 update，因此显式校验完整结果。
            profile.preferences = UserPreferences.model_validate(
                preferences.model_dump()
            )
            self._profiles[user_id] = profile.model_copy(deep=True)
            if self._persistence:
                self._persistence.save_profile(
                    user_id,
                    profile.model_dump(mode="json"),
                )
            return profile.model_copy(deep=True)

    def add_recent_trip(self, user_id: str, trip: Mapping[str, Any]) -> UserProfile:
        """追加近期行程记录。"""

        with self._lock:
            profile = self.load_profile(user_id)
            profile.history.recent_trips.append(dict(trip))
            self._profiles[user_id] = profile.model_copy(deep=True)
            if self._persistence:
                self._persistence.save_profile(
                    user_id,
                    profile.model_dump(mode="json"),
                )
            return profile.model_copy(deep=True)


__all__ = ["UserProfileManager"]
