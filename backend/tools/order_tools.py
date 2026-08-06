"""Robotaxi 订单工具（6个）

create_order, modify_order, cancel_order, get_order_status, locate_vehicle, signal_vehicle
"""

from __future__ import annotations

from datetime import datetime

from langchain_core.tools import tool
from loguru import logger

from tools.base import get_context
from models.order import OrderState, PassengerInfo, VehicleInfo, RouteInfo, PricingInfo, OrderTimestamps
from models.vehicle import Location


@tool
def create_order(
    pickup: str, dropoff: str, vehicle_type: str = "standard",
    pickup_lat: float = 23.1291, pickup_lng: float = 113.2644,
    dropoff_lat: float = 23.1091, dropoff_lng: float = 113.2944,
) -> dict:
    """创建 Robotaxi 订单。

    Args:
        pickup: 上车点地址
        dropoff: 下车点地址
        vehicle_type: 车型 (standard/premium)
        pickup_lat: 上车点纬度
        pickup_lng: 上车点经度
        dropoff_lat: 下车点纬度
        dropoff_lng: 下车点经度
    """
    ctx = get_context()
    now = datetime.now()
    order = OrderState(
        order_id=f"ORD-{int(now.timestamp()) % 10000}",
        status="pending",
        passenger=PassengerInfo(
            user_id=ctx.user.user_id, name=ctx.user.name,
            location=Location(lat=pickup_lat, lng=pickup_lng, address=pickup),
        ),
        route=RouteInfo(
            pickup=Location(lat=pickup_lat, lng=pickup_lng, address=pickup),
            dropoff=Location(lat=dropoff_lat, lng=dropoff_lng, address=dropoff),
            estimated_distance_km=8.0, estimated_duration_min=20,
        ),
        pricing=PricingInfo(base_fee=13),
        timestamps=OrderTimestamps(created_at=now),
    )
    ctx.order = order
    logger.info(f"订单已创建: {order.order_id}, {pickup} → {dropoff}")
    return {
        "success": True,
        "order_id": order.order_id,
        "message": f"订单已创建，从{pickup}到{dropoff}，预估20分钟",
    }


@tool
def modify_order(order_id: str = "", changes: str = "") -> dict:
    """修改订单信息（目的地、途经点等）。

    Args:
        order_id: 订单ID（空=当前订单）
        changes: 修改内容描述
    """
    ctx = get_context()
    order = ctx.order
    if not order:
        return {"success": False, "message": "当前没有活跃订单"}

    logger.info(f"订单{order.order_id}修改: {changes}")
    return {
        "success": True,
        "order_id": order.order_id,
        "message": f"订单已更新: {changes}",
    }


@tool
def cancel_order(order_id: str = "", reason: str = "用户主动取消") -> dict:
    """取消订单。

    Args:
        order_id: 订单ID（空=当前订单）
        reason: 取消原因
    """
    ctx = get_context()
    order = ctx.order
    if not order:
        return {"success": False, "message": "当前没有活跃订单"}

    # 行程中取消需注意安全
    if order.status == "in_trip":
        speed = ctx.vehicle.speed
        if speed > 0:
            return {
                "success": False,
                "message": f"当前车速{speed}km/h，取消行程需要先安全停车。",
            }

    old_id = order.order_id
    order.status = "cancelled"
    ctx.order = None  # 取消后清除活跃订单
    logger.info(f"订单{old_id}已取消: {reason}")
    return {
        "success": True,
        "order_id": old_id,
        "message": f"订单{old_id}已取消，原因: {reason}",
    }


@tool
def get_order_status(order_id: str = "") -> dict:
    """查询订单当前状态。

    Args:
        order_id: 订单ID（空=当前订单）
    """
    ctx = get_context()
    order = ctx.order
    if not order:
        return {"success": False, "message": "当前没有活跃订单"}

    return {
        "success": True,
        "order_id": order.order_id,
        "status": order.status,
        "passenger": order.passenger.name,
        "pickup": order.route.pickup.address,
        "dropoff": order.route.dropoff.address,
        "pricing": {
            "base_fee": order.pricing.base_fee,
            "total": order.pricing.total,
        },
    }


@tool
def locate_vehicle(order_id: str = "") -> dict:
    """定位订单车辆当前位置。

    Args:
        order_id: 订单ID（空=当前订单）
    """
    ctx = get_context()
    order = ctx.order
    if not order:
        return {"success": False, "message": "当前没有活跃订单"}

    v_loc = ctx.vehicle.location
    p_loc = order.passenger.location
    # 简单估算距离（度 → km 近似）
    dist_km = ((v_loc.lat - p_loc.lat) ** 2 + (v_loc.lng - p_loc.lng) ** 2) ** 0.5 * 111

    return {
        "success": True,
        "vehicle_id": order.vehicle.vehicle_id if order.vehicle else ctx.vehicle.vehicle_id,
        "vehicle_location": {"lat": v_loc.lat, "lng": v_loc.lng, "address": v_loc.address},
        "passenger_location": {"lat": p_loc.lat, "lng": p_loc.lng, "address": p_loc.address},
        "distance_km": round(dist_km, 2),
        "message": f"车辆位于{v_loc.address}，距您约{dist_km:.1f}km",
    }


@tool
def signal_vehicle(order_id: str = "", action: str = "flash_and_honk") -> dict:
    """向车辆发送信号（闪灯/鸣笛）。

    Args:
        order_id: 订单ID（空=当前订单）
        action: 动作 (flash/honk/flash_and_honk)
    """
    ctx = get_context()
    order = ctx.order
    if not order:
        return {"success": False, "message": "当前没有活跃订单"}

    action_desc = {"flash": "闪灯", "honk": "鸣笛", "flash_and_honk": "闪灯并鸣笛"}
    desc = action_desc.get(action, action)
    vid = order.vehicle.vehicle_id if order.vehicle else ctx.vehicle.vehicle_id
    logger.info(f"车辆信号: {vid} → {desc}")
    return {
        "success": True,
        "vehicle_id": vid,
        "message": f"已向{vid}发送{desc}信号，请留意车辆位置",
    }
