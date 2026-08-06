"""Robotaxi 订单数据模型

定义订单完整生命周期状态，包括乘客、车辆、路线、计价、时间戳。
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from models.vehicle import Location


# ── 子模型 ──────────────────────────────────

class PassengerInfo(BaseModel):
    """乘客信息"""
    user_id: str = Field(default="P-001")
    name: str = Field(default="张先生")
    phone: str = Field(default="138****1234")
    location: Location = Field(default_factory=Location)


class VehicleInfo(BaseModel):
    """订单关联车辆信息"""
    vehicle_id: str = Field(default="XP-001")
    model: str = Field(default="小鹏G6")
    color: str = Field(default="白色")
    plate: str = Field(default="粤A·12345")
    location: Location = Field(default_factory=Location)


class RouteInfo(BaseModel):
    """路线信息"""
    pickup: Location = Field(description="上车点")
    dropoff: Location = Field(description="下车点")
    waypoints: list[Location] = Field(default_factory=list, description="途经点")
    estimated_distance_km: float = Field(default=0, ge=0)
    estimated_duration_min: float = Field(default=0, ge=0)


class PricingInfo(BaseModel):
    """计价信息"""
    base_fee: float = Field(default=0, ge=0, description="起步价")
    distance_fee: float = Field(default=0, ge=0, description="里程费")
    time_fee: float = Field(default=0, ge=0, description="时长费")
    total: float = Field(default=0, ge=0, description="总费用")


class OrderTimestamps(BaseModel):
    """订单时间戳"""
    created_at: datetime | None = None
    driver_assigned_at: datetime | None = None
    arrived_at: datetime | None = None
    trip_started_at: datetime | None = None
    trip_ended_at: datetime | None = None


# ── 主模型 ──────────────────────────────────

OrderStatus = Literal[
    "pending",
    "driver_assigned",
    "arriving",
    "waiting",
    "in_trip",
    "completed",
    "cancelled",
]


class OrderState(BaseModel):
    """Robotaxi 订单完整状态"""
    order_id: str = Field(default="ORD-001")
    status: OrderStatus = Field(default="pending")
    passenger: PassengerInfo = Field(default_factory=PassengerInfo)
    vehicle: VehicleInfo = Field(default_factory=VehicleInfo)
    route: RouteInfo = Field(
        default_factory=lambda: RouteInfo(
            pickup=Location(lat=23.1291, lng=113.2644, address="天河城"),
            dropoff=Location(lat=23.1091, lng=113.2944, address="珠江新城"),
            estimated_distance_km=5.2,
            estimated_duration_min=15,
        )
    )
    pricing: PricingInfo = Field(default_factory=PricingInfo)
    timestamps: OrderTimestamps = Field(default_factory=OrderTimestamps)
