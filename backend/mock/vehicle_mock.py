"""车辆状态模拟数据

为8个标准场景提供车辆初始状态工厂函数。
每个函数返回一个 VehicleState 实例。
"""

from __future__ import annotations

from datetime import datetime, timedelta

from models.vehicle import (
    VehicleState, Location, BatteryInfo, FuelInfo, CabinState,
    ACState, SeatInfo, WindowState, AmbientLight, DriverState, TripInfo,
)


# ── 场景1: 疲劳驾驶 ─────────────────────────

def create_fatigue_driving_state() -> VehicleState:
    """长途高速驾驶，连续驾驶135分钟，疲劳等级2"""
    now = datetime.now()
    return VehicleState(
        vehicle_id="XP-001",
        mode="owner",
        driving_status="driving",
        speed=100,
        location=Location(lat=23.2891, lng=113.4544, address="广河高速 距河源50km"),
        battery=BatteryInfo(level=75, range_km=370, charging=False, temperature=38),
        fuel=FuelInfo(level=0, range_km=0),
        cabin=CabinState(
            ac=ACState(zone_temp={"driver": 24, "passenger": 24, "rear": 24}, fan_speed=3, mode="auto"),
            seats=[
                SeatInfo(id="driver", occupied=True),
                SeatInfo(id="passenger", occupied=False),
                SeatInfo(id="rear_left", occupied=False),
                SeatInfo(id="rear_right", occupied=False),
            ],
            windows=WindowState(),
            child_lock=False,
            ambient_light=AmbientLight(color="#FFFFFF", brightness=50),
        ),
        driver=DriverState(
            fatigue_level=2,
            driving_duration_min=135,
            lane_departure_count=3,
            eyes_detected=True,
        ),
        trip=TripInfo(
            start_time=now - timedelta(minutes=135),
            distance_km=180,
            avg_speed=80,
        ),
    )


# ── 场景2: 亲子出行 ─────────────────────────

def create_parent_child_state() -> VehicleState:
    """后排有儿童座椅，儿童锁已启用"""
    return VehicleState(
        vehicle_id="XP-002",
        mode="owner",
        driving_status="driving",
        speed=60,
        location=Location(lat=23.1291, lng=113.3044, address="广州市天河区 珠江公园附近"),
        battery=BatteryInfo(level=90, range_km=450, charging=False, temperature=32),
        cabin=CabinState(
            ac=ACState(zone_temp={"driver": 24, "passenger": 24, "rear": 25}, fan_speed=2, mode="auto"),
            seats=[
                SeatInfo(id="driver", occupied=True),
                SeatInfo(id="passenger", occupied=False),
                SeatInfo(id="rear_left", occupied=True, child_seat=True),
                SeatInfo(id="rear_right", occupied=False),
            ],
            windows=WindowState(),
            child_lock=True,
            ambient_light=AmbientLight(color="#FFE4B5", brightness=30),
        ),
        driver=DriverState(fatigue_level=0, driving_duration_min=20, lane_departure_count=0),
        trip=TripInfo(start_time=datetime.now() - timedelta(minutes=20), distance_km=12, avg_speed=36),
    )


# ── 场景3: 长途补能 ─────────────────────────

def create_long_distance_charging_state() -> VehicleState:
    """电量低，续航不足以到达目的地"""
    return VehicleState(
        vehicle_id="XP-003",
        mode="owner",
        driving_status="driving",
        speed=90,
        location=Location(lat=23.0567, lng=113.3567, address="广澳高速 距南沙30km"),
        battery=BatteryInfo(level=18, range_km=85, charging=False, temperature=42),
        cabin=CabinState(
            ac=ACState(zone_temp={"driver": 22, "passenger": 22, "rear": 24}, fan_speed=4, mode="cool"),
        ),
        driver=DriverState(fatigue_level=1, driving_duration_min=90, lane_departure_count=1),
        trip=TripInfo(
            start_time=datetime.now() - timedelta(minutes=90),
            distance_km=120,
            avg_speed=80,
        ),
    )


# ── 场景4: 通勤到达 ─────────────────────────

def create_commute_arrival_state() -> VehicleState:
    """日常通勤，接近目的地（公司）"""
    return VehicleState(
        vehicle_id="XP-004",
        mode="owner",
        driving_status="driving",
        speed=30,
        location=Location(lat=23.1330, lng=113.3290, address="广州市天河区 体育西路"),
        battery=BatteryInfo(level=82, range_km=410, charging=False, temperature=30),
        cabin=CabinState(
            ac=ACState(zone_temp={"driver": 23, "passenger": 23, "rear": 24}, fan_speed=3, mode="auto"),
        ),
        driver=DriverState(fatigue_level=0, driving_duration_min=35, lane_departure_count=0),
        trip=TripInfo(
            start_time=datetime.now() - timedelta(minutes=35),
            distance_km=15,
            avg_speed=26,
        ),
    )


# ── 场景5: Robotaxi 找不到车 ─────────────────

def create_robotaxi_cant_find_car_state() -> VehicleState:
    """车辆已到达上车点等待中，乘客找不到"""
    return VehicleState(
        vehicle_id="RP-001",
        mode="robotaxi",
        driving_status="parked",
        speed=0,
        location=Location(lat=23.1291, lng=113.2644, address="广州市天河区 天河城南门"),
        battery=BatteryInfo(level=88, range_km=440, charging=False, temperature=28),
        cabin=CabinState(
            ac=ACState(zone_temp={"driver": 24, "passenger": 24, "rear": 24}, fan_speed=2, mode="auto"),
        ),
    )


# ── 场景6: 上车点异常 ─────────────────────

def create_pickup_abnormal_state() -> VehicleState:
    """上车点位于施工区域"""
    return VehicleState(
        vehicle_id="RP-002",
        mode="robotaxi",
        driving_status="driving",
        speed=40,
        location=Location(lat=23.1200, lng=113.2500, address="广州市天河区 黄埔大道中段"),
        battery=BatteryInfo(level=78, range_km=390, charging=False, temperature=30),
    )


# ── 场景7: 临时改目的地 ─────────────────────

def create_change_destination_state() -> VehicleState:
    """行程中，乘客想改目的地"""
    return VehicleState(
        vehicle_id="RP-003",
        mode="robotaxi",
        driving_status="driving",
        speed=60,
        location=Location(lat=23.1150, lng=113.2800, address="广州市天河区 猎德大桥上"),
        battery=BatteryInfo(level=72, range_km=360, charging=False, temperature=33),
        trip=TripInfo(
            start_time=datetime.now() - timedelta(minutes=10),
            distance_km=5,
            avg_speed=30,
        ),
    )


# ── 场景8: 乘客求助 ─────────────────────────

def create_passenger_help_state() -> VehicleState:
    """乘客在行程中身体不适"""
    return VehicleState(
        vehicle_id="RP-004",
        mode="robotaxi",
        driving_status="driving",
        speed=50,
        location=Location(lat=23.1080, lng=113.2950, address="广州市天河区 临江大道"),
        battery=BatteryInfo(level=80, range_km=400, charging=False, temperature=31),
        cabin=CabinState(
            ac=ACState(zone_temp={"driver": 24, "passenger": 24, "rear": 24}, fan_speed=3, mode="auto"),
        ),
        trip=TripInfo(
            start_time=datetime.now() - timedelta(minutes=8),
            distance_km=4,
            avg_speed=30,
        ),
    )


# ── 工厂映射 ──────────────────────────────────

VEHICLE_FACTORIES: dict[str, callable] = {
    "fatigue_driving": create_fatigue_driving_state,
    "parent_child": create_parent_child_state,
    "long_distance_charging": create_long_distance_charging_state,
    "commute_arrival": create_commute_arrival_state,
    "robotaxi_cant_find_car": create_robotaxi_cant_find_car_state,
    "pickup_abnormal": create_pickup_abnormal_state,
    "change_destination": create_change_destination_state,
    "passenger_help": create_passenger_help_state,
}
