"""座舱控制工具（6个）

ac_control, seat_control, window_control, light_control, media_control, child_lock_control
"""

from __future__ import annotations

from langchain_core.tools import tool
from loguru import logger

from tools.base import get_context


@tool
def ac_control(zone: str = "driver", temp: float = 24.0, fan_speed: int = 3, mode: str = "auto") -> dict:
    """控制车辆空调系统。

    Args:
        zone: 控制区域 (driver/passenger/rear/all)
        temp: 目标温度 16-32°C
        fan_speed: 风量 0-7
        mode: 模式 (auto/cool/heat/vent)
    """
    ctx = get_context()
    if temp < 16 or temp > 32:
        return {"success": False, "message": f"温度 {temp}°C 超出范围（16-32°C）"}
    if fan_speed < 0 or fan_speed > 7:
        return {"success": False, "message": f"风量 {fan_speed} 超出范围（0-7）"}

    ac = ctx.vehicle.cabin.ac
    if zone == "all":
        for k in ac.zone_temp:
            ac.zone_temp[k] = temp
    elif zone in ac.zone_temp:
        ac.zone_temp[zone] = temp
    else:
        return {"success": False, "message": f"未知区域: {zone}"}
    ac.fan_speed = fan_speed
    ac.mode = mode
    logger.info(f"空调已调整: zone={zone}, temp={temp}°C, fan={fan_speed}, mode={mode}")
    return {"success": True, "message": f"已将{zone}空调调至{temp}°C，风量{fan_speed}，模式{mode}"}


@tool
def seat_control(
    seat_id: str = "driver", position: str = "normal",
    heating: bool = False, cooling: bool = False, massage: bool = False,
) -> dict:
    """调节车辆座椅。

    Args:
        seat_id: 座椅ID (driver/passenger/rear_left/rear_right)
        position: 位置预设 (normal/recline/upright/flat)
        heating: 开启加热
        cooling: 开启通风
        massage: 开启按摩
    """
    ctx = get_context()
    valid_ids = ["driver", "passenger", "rear_left", "rear_right"]
    if seat_id not in valid_ids:
        return {"success": False, "message": f"无效座椅ID: {seat_id}，可选: {valid_ids}"}

    features = []
    if heating:
        features.append("加热")
    if cooling:
        features.append("通风")
    if massage:
        features.append("按摩")
    feat_str = "、".join(features) if features else "无"
    logger.info(f"座椅{seat_id}已调节: position={position}, features={feat_str}")
    return {
        "success": True,
        "message": f"已将{seat_id}座椅调至{position}模式，功能: {feat_str}",
    }


@tool
def window_control(window_id: str = "front_left", action: str = "set", level: int = 0) -> dict:
    """控制车辆车窗开合度。

    Args:
        window_id: 车窗ID (front_left/front_right/rear_left/rear_right/all)
        action: 动作 (open/close/set)
        level: 开合度 0-100%
    """
    ctx = get_context()
    speed = ctx.vehicle.speed

    # 安全约束：高速行驶限制开窗
    if speed > 80 and (action == "open" or level > 30):
        return {
            "success": False,
            "message": f"当前车速{speed}km/h，为保障安全，车窗开合度已限制在30%以内。",
        }

    windows = ctx.vehicle.cabin.windows
    if window_id == "all":
        targets = ["front_left", "front_right", "rear_left", "rear_right"]
    elif hasattr(windows, window_id):
        targets = [window_id]
    else:
        return {"success": False, "message": f"无效车窗ID: {window_id}"}

    final_level = 0 if action == "close" else (100 if action == "open" else level)
    for wid in targets:
        setattr(windows, wid, final_level)

    logger.info(f"车窗已调整: {window_id} → {final_level}%")
    return {"success": True, "message": f"已将{window_id}车窗设为{final_level}%"}


@tool
def light_control(light_type: str = "ambient", color: str = "#FFFFFF", brightness: int = 50) -> dict:
    """控制车辆灯光。

    Args:
        light_type: 灯光类型 (ambient/cabin/headlight)
        color: 颜色 (hex格式)
        brightness: 亮度 0-100%
    """
    ctx = get_context()
    if brightness < 0 or brightness > 100:
        return {"success": False, "message": f"亮度 {brightness} 超出范围（0-100）"}

    if light_type == "ambient":
        ctx.vehicle.cabin.ambient_light.color = color
        ctx.vehicle.cabin.ambient_light.brightness = brightness
    logger.info(f"灯光已调整: type={light_type}, color={color}, brightness={brightness}")
    return {"success": True, "message": f"已将{light_type}灯光设为{color}，亮度{brightness}%"}


@tool
def media_control(action: str = "play", source: str = "music", volume: int = 30, content_id: str = "") -> dict:
    """控制车载媒体播放。

    Args:
        action: 动作 (play/pause/next/prev/volume/stop)
        source: 来源 (music/radio/podcast/video)
        volume: 音量 0-100
        content_id: 内容ID
    """
    ctx = get_context()
    speed = ctx.vehicle.speed

    # 安全约束：行驶中禁止播放视频
    if speed > 0 and source == "video":
        return {
            "success": False,
            "message": "车辆正在行驶中，为确保驾驶安全，无法播放视频。",
        }

    if action == "volume":
        ctx.media_volume = max(0, min(100, volume))
        msg = f"音量已调至{ctx.media_volume}%"
    elif action == "play":
        ctx.media_playing = True
        msg = f"正在播放{source}，音量{ctx.media_volume}%"
    elif action == "pause":
        ctx.media_playing = False
        msg = "媒体已暂停"
    elif action == "stop":
        ctx.media_playing = False
        ctx.media_volume = 0
        msg = "媒体已停止"
    else:
        msg = f"已执行{action}操作"

    logger.info(f"媒体控制: action={action}, source={source}")
    return {"success": True, "message": msg}


@tool
def child_lock_control(action: str = "enable") -> dict:
    """控制儿童安全锁。

    Args:
        action: 动作 (enable/disable)
    """
    ctx = get_context()

    if action == "disable":
        # 检查后排是否有人
        rear_occupied = any(
            s.occupied for s in ctx.vehicle.cabin.seats
            if s.id in ("rear_left", "rear_right")
        )
        if rear_occupied:
            return {
                "success": False,
                "message": "后排有乘客，为保障安全，无法关闭儿童安全锁。",
            }

    ctx.vehicle.cabin.child_lock = (action == "enable")
    status = "已启用" if action == "enable" else "已关闭"
    logger.info(f"儿童安全锁{status}")
    return {"success": True, "message": f"儿童安全锁{status}"}
