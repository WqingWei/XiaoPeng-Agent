"""用户画像数据模型

定义用户偏好、历史、上下文信息，用于个性化服务。
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


# ── 子模型 ──────────────────────────────────

class UserPreferences(BaseModel):
    """用户偏好"""
    ac_temp_default: float = Field(default=24.0, description="默认空调温度")
    seat_position: dict[str, float] = Field(default_factory=dict, description="座椅位置记忆")
    music_genre: str = Field(default="pop", description="偏好音乐类型")
    language: Literal["zh", "en"] = Field(default="zh", description="语言偏好")
    notifications: bool = Field(default=True, description="是否开启通知")


class UserHistory(BaseModel):
    """用户历史数据"""
    frequent_destinations: list[dict] = Field(default_factory=list, description="常用目的地")
    recent_trips: list[dict] = Field(default_factory=list, description="近期行程")
    charging_stations_used: list[dict] = Field(default_factory=list, description="使用过的充电站")


class CalendarEvent(BaseModel):
    """日历事件"""
    title: str = ""
    start_time: datetime | None = None
    end_time: datetime | None = None
    location: str = ""


class UserContext(BaseModel):
    """用户上下文"""
    has_child: bool = Field(default=False, description="是否有儿童同行")
    child_age: int | None = Field(default=None, description="儿童年龄")
    calendar_events: list[CalendarEvent] = Field(default_factory=list, description="今日日程")


# ── 主模型 ──────────────────────────────────

class UserProfile(BaseModel):
    """用户画像"""
    user_id: str = Field(default="U-001")
    name: str = Field(default="李先生")
    role: Literal["owner", "passenger"] = Field(default="owner")
    preferences: UserPreferences = Field(default_factory=UserPreferences)
    history: UserHistory = Field(default_factory=UserHistory)
    context: UserContext = Field(default_factory=UserContext)
