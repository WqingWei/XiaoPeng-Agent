"""Robotaxi 订单模拟数据

为4个 Robotaxi 场景创建订单数据。
"""

from __future__ import annotations

from datetime import datetime, timedelta

from models.order import (
    OrderState, PassengerInfo, VehicleInfo, RouteInfo,
    PricingInfo, OrderTimestamps,
)
from models.vehicle import Location


# ── 场景5: 找不到车（车辆已到达等待中）─────────

def create_cant_find_car_order() -> OrderState:
    """订单状态: waiting，车辆已到达上车点"""
    now = datetime.now()
    return OrderState(
        order_id="ORD-501",
        status="waiting",
        passenger=PassengerInfo(
            user_id="P-001", name="张先生", phone="138****1234",
            location=Location(lat=23.1295, lng=113.2650, address="天河城南门西侧50m"),
        ),
        vehicle=VehicleInfo(
            vehicle_id="RP-001", model="小鹏G6", color="白色", plate="粤A·D8888",
            location=Location(lat=23.1291, lng=113.2644, address="天河城南门"),
        ),
        route=RouteInfo(
            pickup=Location(lat=23.1291, lng=113.2644, address="天河城南门"),
            dropoff=Location(lat=23.1191, lng=113.3218, address="珠江新城花城广场"),
            estimated_distance_km=6.5,
            estimated_duration_min=20,
        ),
        pricing=PricingInfo(base_fee=13, distance_fee=0, time_fee=0, total=13),
        timestamps=OrderTimestamps(
            created_at=now - timedelta(minutes=15),
            driver_assigned_at=now - timedelta(minutes=12),
            arrived_at=now - timedelta(minutes=3),
        ),
    )


# ── 场景6: 上车点异常（订单刚创建，上车点施工）───

def create_pickup_abnormal_order() -> OrderState:
    """订单状态: pending，上车点在施工区域"""
    now = datetime.now()
    return OrderState(
        order_id="ORD-601",
        status="pending",
        passenger=PassengerInfo(
            user_id="P-002", name="李女士", phone="139****5678",
            location=Location(lat=23.1200, lng=113.2500, address="黄埔大道施工段"),
        ),
        route=RouteInfo(
            pickup=Location(lat=23.1200, lng=113.2500, address="黄埔大道中段"),
            dropoff=Location(lat=23.1091, lng=113.2944, address="广州塔"),
            estimated_distance_km=8.0,
            estimated_duration_min=25,
        ),
        pricing=PricingInfo(base_fee=13, distance_fee=0, time_fee=0, total=13),
        timestamps=OrderTimestamps(created_at=now - timedelta(minutes=2)),
    )


# ── 场景7: 临时改目的地（行程中）─────────────

def create_change_destination_order() -> OrderState:
    """订单状态: in_trip，乘客想改目的地"""
    now = datetime.now()
    return OrderState(
        order_id="ORD-701",
        status="in_trip",
        passenger=PassengerInfo(
            user_id="P-003", name="王先生", phone="137****9012",
            location=Location(lat=23.1150, lng=113.2800, address="猎德大桥上"),
        ),
        vehicle=VehicleInfo(
            vehicle_id="RP-003", model="小鹏G9", color="黑色", plate="粤A·G6666",
            location=Location(lat=23.1150, lng=113.2800, address="猎德大桥上"),
        ),
        route=RouteInfo(
            pickup=Location(lat=23.1291, lng=113.2644, address="天河城"),
            dropoff=Location(lat=23.1091, lng=113.2944, address="珠江新城"),
            estimated_distance_km=5.0,
            estimated_duration_min=15,
        ),
        pricing=PricingInfo(base_fee=13, distance_fee=8, time_fee=3, total=24),
        timestamps=OrderTimestamps(
            created_at=now - timedelta(minutes=20),
            driver_assigned_at=now - timedelta(minutes=18),
            arrived_at=now - timedelta(minutes=12),
            trip_started_at=now - timedelta(minutes=10),
        ),
    )


# ── 场景8: 乘客求助（行程中身体不适）─────────

def create_passenger_help_order() -> OrderState:
    """订单状态: in_trip，乘客身体不适"""
    now = datetime.now()
    return OrderState(
        order_id="ORD-801",
        status="in_trip",
        passenger=PassengerInfo(
            user_id="P-004", name="赵女士", phone="136****3456",
            location=Location(lat=23.1080, lng=113.2950, address="临江大道"),
        ),
        vehicle=VehicleInfo(
            vehicle_id="RP-004", model="小鹏G6", color="银色", plate="粤A·H9999",
            location=Location(lat=23.1080, lng=113.2950, address="临江大道"),
        ),
        route=RouteInfo(
            pickup=Location(lat=23.1291, lng=113.2644, address="天河城"),
            dropoff=Location(lat=23.1000, lng=113.3100, address="琶洲会展中心"),
            estimated_distance_km=10.0,
            estimated_duration_min=30,
        ),
        pricing=PricingInfo(base_fee=13, distance_fee=12, time_fee=5, total=30),
        timestamps=OrderTimestamps(
            created_at=now - timedelta(minutes=25),
            driver_assigned_at=now - timedelta(minutes=22),
            arrived_at=now - timedelta(minutes=15),
            trip_started_at=now - timedelta(minutes=8),
        ),
    )


# ── 工厂映射 ──────────────────────────────────

ORDER_FACTORIES: dict[str, callable] = {
    "robotaxi_cant_find_car": create_cant_find_car_order,
    "pickup_abnormal": create_pickup_abnormal_order,
    "change_destination": create_change_destination_order,
    "passenger_help": create_passenger_help_order,
}
