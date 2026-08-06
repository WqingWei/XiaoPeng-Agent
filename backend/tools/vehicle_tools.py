"""车辆状态查询工具（4个）

get_vehicle_status, get_driver_status, get_location, get_environment_info
"""

from __future__ import annotations

from langchain_core.tools import tool
from loguru import logger

from tools.base import get_context


@tool
def get_vehicle_status() -> dict:
    """获取车辆完整状态信息，包括电量、续航、车速、座舱状态等。"""
    ctx = get_context()
    v = ctx.vehicle
    return {
        "success": True,
        "vehicle_id": v.vehicle_id,
        "mode": v.mode,
        "driving_status": v.driving_status,
        "speed_kmh": v.speed,
        "battery": {
            "level_percent": v.battery.level,
            "range_km": v.battery.range_km,
            "charging": v.battery.charging,
            "temperature": v.battery.temperature,
        },
        "cabin": {
            "ac_temp": v.cabin.ac.zone_temp,
            "fan_speed": v.cabin.ac.fan_speed,
            "child_lock": v.cabin.child_lock,
            "windows": {
                "front_left": v.cabin.windows.front_left,
                "front_right": v.cabin.windows.front_right,
                "rear_left": v.cabin.windows.rear_left,
                "rear_right": v.cabin.windows.rear_right,
            },
        },
    }


@tool
def get_driver_status() -> dict:
    """获取驾驶员状态信息，包括疲劳等级、驾驶时长、车道偏离等。"""
    ctx = get_context()
    d = ctx.vehicle.driver
    return {
        "success": True,
        "fatigue_level": d.fatigue_level,
        "fatigue_description": ["清醒", "轻度疲劳", "中度疲劳", "重度疲劳"][d.fatigue_level],
        "driving_duration_min": d.driving_duration_min,
        "lane_departure_count": d.lane_departure_count,
        "eyes_detected": d.eyes_detected,
    }


@tool
def get_location() -> dict:
    """获取车辆当前GPS位置和地址。"""
    ctx = get_context()
    loc = ctx.vehicle.location
    return {
        "success": True,
        "lat": loc.lat,
        "lng": loc.lng,
        "address": loc.address,
    }


@tool
def get_environment_info() -> dict:
    """获取当前环境信息，包括天气、时间、交通状况。"""
    ctx = get_context()
    e = ctx.environment
    return {
        "success": True,
        "weather": {
            "condition": e.weather.condition,
            "temperature": e.weather.temperature,
            "humidity": e.weather.humidity,
            "visibility_km": e.weather.visibility_km,
        },
        "time": {
            "period": e.time.period,
            "is_holiday": e.time.is_holiday,
        },
        "traffic": {
            "congestion_level": e.traffic.congestion_level,
            "incident_count": len(e.traffic.incidents),
        },
    }
