"""安全与应急工具（5个）

emergency_stop, call_rescue, call_emergency, transfer_human, safety_alert_tool
"""

from __future__ import annotations

from langchain_core.tools import tool
from loguru import logger

from tools.base import get_context


@tool
def emergency_stop() -> dict:
    """紧急停车。在L3/L4安全事件中触发，寻找安全位置停车。"""
    ctx = get_context()
    ctx.vehicle.speed = 0
    ctx.vehicle.driving_status = "parked"
    logger.warning("⚠️ 紧急停车已触发")
    return {
        "success": True,
        "message": "已执行紧急停车，车辆已安全停靠。请保持冷静，救援正在赶来。",
        "action": "emergency_stop",
    }


@tool
def call_rescue(rescue_type: str = "road", location: str = "当前位置") -> dict:
    """呼叫道路救援或车辆故障救援。

    Args:
        rescue_type: 救援类型 (road/accident/breakdown)
        location: 位置描述
    """
    ctx = get_context()
    loc = location if location != "当前位置" else ctx.vehicle.location.address
    type_desc = {"road": "道路救援", "accident": "事故救援", "breakdown": "故障救援"}
    desc = type_desc.get(rescue_type, rescue_type)
    logger.warning(f"呼叫{desc}: location={loc}")
    return {
        "success": True,
        "message": f"已呼叫{desc}，救援团队正在前往{loc}。预计到达时间15-30分钟。",
        "rescue_type": rescue_type,
        "location": loc,
        "eta_min": 20,
    }


@tool
def call_emergency(service: str = "120") -> dict:
    """呼叫紧急服务（110报警/120急救/119消防）。

    Args:
        service: 紧急服务号码 (110/120/119)
    """
    ctx = get_context()
    loc = ctx.vehicle.location.address
    service_names = {"110": "报警", "120": "急救", "119": "消防"}
    name = service_names.get(service, service)
    logger.warning(f"⚠️ 紧急呼叫: {service}({name}), location={loc}")
    return {
        "success": True,
        "message": f"已拨打{service}({name})，已向接警员提供位置信息: {loc}。请保持通话。",
        "service": service,
        "service_name": name,
        "location": loc,
    }


@tool
def transfer_human(priority: str = "normal", context: str = "") -> dict:
    """转接人工客服。

    Args:
        priority: 优先级 (normal/high/urgent)
        context: 转接上下文描述
    """
    ctx = get_context()
    priority_desc = {"normal": "普通", "high": "高", "urgent": "紧急"}
    p = priority_desc.get(priority, priority)
    logger.info(f"转人工客服: priority={p}, context={context}")
    return {
        "success": True,
        "message": f"正在为您转接人工客服（{p}优先级）{'，原因: ' + context if context else ''}。请稍候。",
        "priority": priority,
        "estimated_wait_s": 10 if priority == "urgent" else 30,
    }


@tool
def safety_alert_tool(level: str = "L1", message: str = "") -> dict:
    """生成安全告警信息。

    Args:
        level: 安全等级 (L0/L1/L2/L3/L4)
        message: 告警信息
    """
    logger.warning(f"安全告警 [{level}]: {message}")
    return {
        "success": True,
        "level": level,
        "message": message,
        "action": "safety_alert",
    }
