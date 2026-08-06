"""环境信息数据模型

定义天气、时间、交通、周边设施等环境上下文。
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from models.vehicle import Location


# ── 子模型 ──────────────────────────────────

class WeatherInfo(BaseModel):
    """天气信息"""
    condition: Literal["sunny", "cloudy", "rainy", "snowy", "foggy"] = Field(default="sunny")
    temperature: float = Field(default=28.0, description="室外温度 (°C)")
    humidity: float = Field(default=60, ge=0, le=100, description="湿度 (%)")
    visibility_km: float = Field(default=10, ge=0, description="能见度 (km)")


class TimeContext(BaseModel):
    """时间上下文"""
    current: datetime = Field(default_factory=datetime.now)
    period: Literal["morning", "afternoon", "evening", "night"] = Field(default="morning")
    is_holiday: bool = Field(default=False)


class TrafficIncident(BaseModel):
    """交通事件"""
    type: Literal["construction", "accident", "closure"]
    location: Location = Field(default_factory=Location)
    description: str = ""


class TrafficInfo(BaseModel):
    """交通信息"""
    congestion_level: Literal["low", "medium", "high", "severe"] = Field(default="low")
    incidents: list[TrafficIncident] = Field(default_factory=list)


class NearbyFacilities(BaseModel):
    """周边设施"""
    charging_stations: list[dict] = Field(default_factory=list)
    service_areas: list[dict] = Field(default_factory=list)
    hospitals: list[dict] = Field(default_factory=list)
    parking_lots: list[dict] = Field(default_factory=list)
    restaurants: list[dict] = Field(default_factory=list)


# ── 主模型 ──────────────────────────────────

class EnvironmentContext(BaseModel):
    """环境上下文"""
    weather: WeatherInfo = Field(default_factory=WeatherInfo)
    time: TimeContext = Field(default_factory=TimeContext)
    traffic: TrafficInfo = Field(default_factory=TrafficInfo)
    nearby: NearbyFacilities = Field(default_factory=NearbyFacilities)
