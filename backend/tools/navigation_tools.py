"""导航与出行工具（5个）

navigate_to, search_poi, search_parking, search_charger, traffic_info
"""

from __future__ import annotations

from langchain_core.tools import tool
from loguru import logger

from tools.base import get_context
from mock.poi_mock import (
    CHARGING_STATIONS, PARKING_LOTS, SERVICE_AREAS,
    get_pois_by_category, search_pois,
)


@tool
def navigate_to(destination: str, waypoints: str = "", preference: str = "fastest") -> dict:
    """设置导航目的地。

    Args:
        destination: 目的地地址
        waypoints: 途经点（逗号分隔）
        preference: 路线偏好 (fastest/shortest/avoid_toll/avoid_highway)
    """
    ctx = get_context()
    wp_list = [w.strip() for w in waypoints.split(",") if w.strip()] if waypoints else []
    logger.info(f"导航设置: 目的地={destination}, 途经点={wp_list}, 偏好={preference}")
    return {
        "success": True,
        "message": f"已设置导航到{destination}",
        "route": {
            "destination": destination,
            "waypoints": wp_list,
            "preference": preference,
            "estimated_distance_km": 15.0,
            "estimated_duration_min": 25,
        },
    }


@tool
def search_poi(category: str = "restaurant", keyword: str = "", radius: float = 10.0, sort_by: str = "distance") -> dict:
    """搜索附近兴趣点（POI）。

    Args:
        category: 类别 (charging_station/parking_lot/service_area/hospital/restaurant)
        keyword: 关键词搜索
        radius: 搜索半径 (km)
        sort_by: 排序 (distance/price/rating)
    """
    if keyword:
        results = search_pois(keyword, radius_km=radius)
    else:
        results = get_pois_by_category(category)
        results = [r for r in results if r.get("distance_km", 999) <= radius]

    if sort_by == "distance":
        results = sorted(results, key=lambda x: x.get("distance_km", 999))
    elif sort_by == "rating":
        results = sorted(results, key=lambda x: x.get("rating", 0), reverse=True)

    logger.info(f"POI搜索: category={category}, keyword={keyword}, 找到{len(results)}条")
    return {
        "success": True,
        "count": len(results),
        "pois": results[:10],
        "message": f"找到{len(results)}个{category}",
    }


@tool
def search_parking(location: str = "当前位置", radius: float = 5.0, filter: str = "") -> dict:
    """搜索附近停车场。

    Args:
        location: 搜索位置
        radius: 搜索半径 (km)
        filter: 过滤条件 (price/available)
    """
    results = [p for p in PARKING_LOTS if p.get("distance_km", 999) <= radius]
    results = sorted(results, key=lambda x: x.get("distance_km", 999))
    logger.info(f"停车场搜索: location={location}, 找到{len(results)}个")
    return {
        "success": True,
        "count": len(results),
        "parking_lots": results,
        "message": f"找到{len(results)}个停车场",
    }


@tool
def search_charger(location: str = "当前位置", radius: float = 20.0, power_type: str = "", sort_by: str = "distance") -> dict:
    """搜索附近充电站。

    Args:
        location: 搜索位置
        radius: 搜索半径 (km)
        power_type: 功率类型 (fast/slow/any)
        sort_by: 排序 (distance/price/available)
    """
    results = [c for c in CHARGING_STATIONS if c.get("distance_km", 999) <= radius]
    if power_type == "fast":
        results = [c for c in results if c.get("power_kw", 0) >= 200]
    if sort_by == "distance":
        results = sorted(results, key=lambda x: x.get("distance_km", 999))
    elif sort_by == "price":
        results = sorted(results, key=lambda x: x.get("price_per_kwh", 999))

    xpeng_count = sum(1 for c in results if c.get("is_xpeng"))
    logger.info(f"充电站搜索: 找到{len(results)}个（小鹏自营{xpeng_count}家）")
    return {
        "success": True,
        "count": len(results),
        "chargers": results,
        "message": f"找到{len(results)}个充电站，其中小鹏自营{xpeng_count}家",
    }


@tool
def traffic_info(route_id: str = "current") -> dict:
    """查询当前路况信息。

    Args:
        route_id: 路线ID (current=当前路线)
    """
    ctx = get_context()
    traffic = ctx.environment.traffic
    incidents = [
        {"type": inc.type, "description": inc.description, "location": inc.location.address}
        for inc in traffic.incidents
    ]
    return {
        "success": True,
        "congestion_level": traffic.congestion_level,
        "incidents": incidents,
        "message": f"当前路况: {traffic.congestion_level}，{len(incidents)}个事件",
    }
