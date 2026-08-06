"""车辆状态数据模型

定义车辆完整状态快照，包括位置、电量、座舱、驾驶员、行程等。
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


# ── 子模型 ──────────────────────────────────

class Location(BaseModel):
    """地理位置"""
    lat: float = Field(default=0.0, description="纬度")
    lng: float = Field(default=0.0, description="经度")
    address: str = Field(default="", description="地址文本")


class BatteryInfo(BaseModel):
    """电池状态"""
    level: float = Field(ge=0, le=100, description="电量百分比 (0-100)")
    range_km: float = Field(ge=0, description="剩余续航 (km)")
    charging: bool = Field(default=False, description="是否正在充电")
    temperature: float = Field(default=25.0, description="电池温度 (°C)")


class FuelInfo(BaseModel):
    """燃油状态（混动车型）"""
    level: float = Field(default=0, ge=0, le=100, description="油量百分比 (0-100)")
    range_km: float = Field(default=0, ge=0, description="燃油续航 (km)")


class SeatInfo(BaseModel):
    """单个座椅状态"""
    id: Literal["driver", "passenger", "rear_left", "rear_right"]
    occupied: bool = Field(default=False, description="是否有人")
    child_seat: bool = Field(default=False, description="是否为儿童座椅")


class ACState(BaseModel):
    """空调状态"""
    zone_temp: dict[str, float] = Field(
        default_factory=lambda: {"driver": 24.0, "passenger": 24.0, "rear": 24.0},
        description="各区域目标温度",
    )
    fan_speed: int = Field(default=3, ge=0, le=7, description="风量 (0-7)")
    mode: Literal["auto", "cool", "heat", "vent"] = Field(default="auto")


class WindowState(BaseModel):
    """车窗状态（开合度 0-100%）"""
    front_left: int = Field(default=0, ge=0, le=100)
    front_right: int = Field(default=0, ge=0, le=100)
    rear_left: int = Field(default=0, ge=0, le=100)
    rear_right: int = Field(default=0, ge=0, le=100)


class AmbientLight(BaseModel):
    """氛围灯"""
    color: str = Field(default="#FFFFFF", description="颜色 (hex)")
    brightness: int = Field(default=50, ge=0, le=100, description="亮度 (0-100)")


class CabinState(BaseModel):
    """座舱整体状态"""
    ac: ACState = Field(default_factory=ACState)
    seats: list[SeatInfo] = Field(default_factory=lambda: [
        SeatInfo(id="driver"),
        SeatInfo(id="passenger"),
        SeatInfo(id="rear_left"),
        SeatInfo(id="rear_right"),
    ])
    windows: WindowState = Field(default_factory=WindowState)
    child_lock: bool = Field(default=False, description="儿童安全锁是否启用")
    ambient_light: AmbientLight = Field(default_factory=AmbientLight)


class DriverState(BaseModel):
    """驾驶员状态"""
    fatigue_level: int = Field(default=0, ge=0, le=3, description="疲劳等级 (0=清醒, 3=重度疲劳)")
    driving_duration_min: float = Field(default=0, ge=0, description="连续驾驶时长 (分钟)")
    lane_departure_count: int = Field(default=0, ge=0, description="车道偏离次数")
    eyes_detected: bool = Field(default=True, description="是否检测到驾驶员注视前方")


class TripInfo(BaseModel):
    """本次行程信息"""
    start_time: datetime | None = Field(default=None, description="行程开始时间")
    distance_km: float = Field(default=0, ge=0, description="已行驶距离 (km)")
    avg_speed: float = Field(default=0, ge=0, description="平均速度 (km/h)")


# ── 主模型 ──────────────────────────────────

class VehicleState(BaseModel):
    """车辆完整状态快照"""
    vehicle_id: str = Field(default="XP-001")
    mode: Literal["owner", "robotaxi"] = Field(default="owner")
    driving_status: Literal["parked", "driving", "charging"] = Field(default="parked")
    speed: float = Field(default=0, ge=0, description="当前速度 (km/h)")
    location: Location = Field(default_factory=lambda: Location(lat=23.1291, lng=113.2644, address="广州市天河区"))
    battery: BatteryInfo = Field(default_factory=lambda: BatteryInfo(level=85, range_km=420))
    fuel: FuelInfo = Field(default_factory=FuelInfo)
    cabin: CabinState = Field(default_factory=CabinState)
    driver: DriverState = Field(default_factory=DriverState)
    trip: TripInfo = Field(default_factory=TripInfo)
