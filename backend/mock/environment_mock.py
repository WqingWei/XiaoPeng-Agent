"""环境上下文模拟数据

为8个标准场景提供环境配置工厂函数。
每个函数返回一个 EnvironmentContext 实例。
"""

from __future__ import annotations

from datetime import datetime, timedelta

from models.environment import (
    EnvironmentContext, WeatherInfo, TimeContext, TrafficInfo,
    TrafficIncident, NearbyFacilities,
)
from models.vehicle import Location


# ── 场景1: 疲劳驾驶（深夜高速）─────────────

def create_fatigue_driving_env() -> EnvironmentContext:
    """深夜23:30、高速公路、天气晴朗"""
    now = datetime.now().replace(hour=23, minute=30, second=0, microsecond=0)
    return EnvironmentContext(
        weather=WeatherInfo(condition="sunny", temperature=26, humidity=65, visibility_km=10),
        time=TimeContext(current=now, period="night", is_holiday=False),
        traffic=TrafficInfo(congestion_level="low", incidents=[]),
        nearby=NearbyFacilities(
            service_areas=[{"name": "沙贝服务区", "distance_km": 3.0}],
            charging_stations=[{"name": "小鹏超充（沙贝）", "distance_km": 3.2}],
        ),
    )


# ── 场景2: 亲子出行（周末上午）─────────────

def create_parent_child_env() -> EnvironmentContext:
    """周六上午10:00、城市道路、天气多云"""
    now = datetime.now().replace(hour=10, minute=0, second=0, microsecond=0)
    return EnvironmentContext(
        weather=WeatherInfo(condition="cloudy", temperature=30, humidity=70, visibility_km=8),
        time=TimeContext(current=now, period="morning", is_holiday=True),
        traffic=TrafficInfo(congestion_level="medium", incidents=[]),
        nearby=NearbyFacilities(
            hospitals=[{"name": "广州市妇女儿童医疗中心", "distance_km": 2.0}],
        ),
    )


# ── 场景3: 长途补能（下午高速）─────────────

def create_long_distance_charging_env() -> EnvironmentContext:
    """下午14:00、高速公路、炎热"""
    now = datetime.now().replace(hour=14, minute=0, second=0, microsecond=0)
    return EnvironmentContext(
        weather=WeatherInfo(condition="sunny", temperature=36, humidity=55, visibility_km=12),
        time=TimeContext(current=now, period="afternoon", is_holiday=False),
        traffic=TrafficInfo(congestion_level="low", incidents=[]),
        nearby=NearbyFacilities(
            charging_stations=[
                {"name": "小鹏超充（南沙）", "distance_km": 15.0, "power_kw": 480},
                {"name": "南方电网（番禺）", "distance_km": 25.0, "power_kw": 120},
            ],
            service_areas=[{"name": "南沙服务区", "distance_km": 12.0}],
            restaurants=[{"name": "南沙服务区餐厅", "distance_km": 12.5}],
        ),
    )


# ── 场景4: 通勤到达（工作日早晨）─────────────

def create_commute_arrival_env() -> EnvironmentContext:
    """工作日8:45、城市道路、轻微拥堵"""
    now = datetime.now().replace(hour=8, minute=45, second=0, microsecond=0)
    return EnvironmentContext(
        weather=WeatherInfo(condition="cloudy", temperature=28, humidity=75, visibility_km=8),
        time=TimeContext(current=now, period="morning", is_holiday=False),
        traffic=TrafficInfo(
            congestion_level="medium",
            incidents=[TrafficIncident(
                type="construction",
                location=Location(lat=23.1350, lng=113.3280, address="体育西路施工"),
                description="体育西路地铁施工，部分车道封闭",
            )],
        ),
        nearby=NearbyFacilities(
            parking_lots=[
                {"name": "天河城停车场", "distance_km": 0.3, "price_per_hour": 12, "available": 120},
                {"name": "正佳广场停车场", "distance_km": 0.5, "price_per_hour": 15, "available": 80},
            ],
        ),
    )


# ── 场景5: Robotaxi 找不到车 ─────────────────

def create_robotaxi_cant_find_car_env() -> EnvironmentContext:
    """下午16:30、商圈、人流密集"""
    now = datetime.now().replace(hour=16, minute=30, second=0, microsecond=0)
    return EnvironmentContext(
        weather=WeatherInfo(condition="sunny", temperature=32, humidity=60, visibility_km=10),
        time=TimeContext(current=now, period="afternoon", is_holiday=False),
        traffic=TrafficInfo(congestion_level="high", incidents=[]),
    )


# ── 场景6: 上车点异常（施工路段）─────────────

def create_pickup_abnormal_env() -> EnvironmentContext:
    """工作日上午9:15、上车点有施工"""
    now = datetime.now().replace(hour=9, minute=15, second=0, microsecond=0)
    return EnvironmentContext(
        weather=WeatherInfo(condition="rainy", temperature=25, humidity=85, visibility_km=5),
        time=TimeContext(current=now, period="morning", is_holiday=False),
        traffic=TrafficInfo(
            congestion_level="high",
            incidents=[TrafficIncident(
                type="construction",
                location=Location(lat=23.1200, lng=113.2500, address="黄埔大道施工段"),
                description="黄埔大道地铁施工，双向封闭",
            )],
        ),
    )


# ── 场景7: 临时改目的地 ─────────────────────

def create_change_destination_env() -> EnvironmentContext:
    """下午18:00、晚高峰、城市道路"""
    now = datetime.now().replace(hour=18, minute=0, second=0, microsecond=0)
    return EnvironmentContext(
        weather=WeatherInfo(condition="cloudy", temperature=29, humidity=68, visibility_km=9),
        time=TimeContext(current=now, period="evening", is_holiday=False),
        traffic=TrafficInfo(congestion_level="high", incidents=[]),
    )


# ── 场景8: 乘客求助 ─────────────────────────

def create_passenger_help_env() -> EnvironmentContext:
    """晚上20:00、城市道路"""
    now = datetime.now().replace(hour=20, minute=0, second=0, microsecond=0)
    return EnvironmentContext(
        weather=WeatherInfo(condition="sunny", temperature=27, humidity=62, visibility_km=10),
        time=TimeContext(current=now, period="evening", is_holiday=False),
        traffic=TrafficInfo(congestion_level="medium", incidents=[]),
        nearby=NearbyFacilities(
            hospitals=[
                {"name": "中山大学附属第一医院", "distance_km": 3.2, "level": "三甲"},
                {"name": "广州市第一人民医院", "distance_km": 5.0, "level": "三甲"},
            ],
        ),
    )


# ── 工厂映射 ──────────────────────────────────

ENVIRONMENT_FACTORIES: dict[str, callable] = {
    "fatigue_driving": create_fatigue_driving_env,
    "parent_child": create_parent_child_env,
    "long_distance_charging": create_long_distance_charging_env,
    "commute_arrival": create_commute_arrival_env,
    "robotaxi_cant_find_car": create_robotaxi_cant_find_car_env,
    "pickup_abnormal": create_pickup_abnormal_env,
    "change_destination": create_change_destination_env,
    "passenger_help": create_passenger_help_env,
}
