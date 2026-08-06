"""场景预设加载器

提供 load_scenario() 函数，根据场景ID返回完整的初始状态包：
(vehicle_state, environment, order_state_or_none, user_profile, initial_system_message)
"""

from __future__ import annotations

from models.vehicle import VehicleState
from models.environment import EnvironmentContext
from models.order import OrderState
from models.user_profile import UserProfile, UserPreferences, UserContext

from mock.vehicle_mock import VEHICLE_FACTORIES
from mock.environment_mock import ENVIRONMENT_FACTORIES
from mock.order_mock import ORDER_FACTORIES


# ── 场景系统消息 ────────────────────────────

SYSTEM_MESSAGES: dict[str, str] = {
    "fatigue_driving": (
        "您正在长途高速行驶中。系统检测到您的驾驶时间较长，"
        "请关注驾驶员状态，必要时主动提醒休息。"
    ),
    "parent_child": (
        "车主带着孩子出行，后排有儿童座椅。"
        "请确保儿童安全措施到位，关注后排温度和舒适度。"
    ),
    "long_distance_charging": (
        "长途行驶中，电量较低。请评估续航是否足够到达目的地，"
        "如不够请搜索并推荐沿途充电站。"
    ),
    "commute_arrival": (
        "日常通勤，即将到达目的地。请搜索附近停车场，"
        "并提醒用户携带随身物品。"
    ),
    "robotaxi_cant_find_car": (
        "Robotaxi乘客已下单，车辆已到达上车点但乘客找不到车。"
        "请提供车辆精确位置描述，必要时触发闪灯鸣笛。"
    ),
    "pickup_abnormal": (
        "Robotaxi乘客的上车点存在异常（施工/禁停）。"
        "请检测异常类型并推荐替代上车点。"
    ),
    "change_destination": (
        "乘客在行程中想要修改目的地。"
        "请评估新路线的费用和时间变化，确认后更新导航。"
    ),
    "passenger_help": (
        "Robotaxi乘客在行程中发出求助信号。"
        "这是最高优先级事件，请立即响应并评估紧急程度。"
    ),
}


# ── 场景用户画像 ────────────────────────────

def _create_owner_profile() -> UserProfile:
    """车主用户画像"""
    return UserProfile(
        user_id="U-001",
        name="李先生",
        role="owner",
        preferences=UserPreferences(
            ac_temp_default=24.0,
            music_genre="pop",
            language="zh",
        ),
    )


def _create_parent_profile() -> UserProfile:
    """带儿童的车主画像"""
    return UserProfile(
        user_id="U-002",
        name="陈女士",
        role="owner",
        preferences=UserPreferences(ac_temp_default=25.0, music_genre="children"),
        context=UserContext(has_child=True, child_age=4),
    )


def _create_passenger_profile() -> UserProfile:
    """Robotaxi乘客画像"""
    return UserProfile(
        user_id="U-003",
        name="张先生",
        role="passenger",
        preferences=UserPreferences(ac_temp_default=23.0, language="zh"),
    )


# ── 场景元数据 ────────────────────────────

SCENARIO_META: dict[str, dict] = {
    "fatigue_driving": {
        "title": "场景一：疲劳驾驶提醒",
        "mode": "owner",
        "description": "长途高速驾驶，系统检测到疲劳信号",
    },
    "parent_child": {
        "title": "场景二：亲子出行",
        "mode": "owner",
        "description": "车主带着孩子出行，需关注儿童安全",
    },
    "long_distance_charging": {
        "title": "场景三：长途补能",
        "mode": "owner",
        "description": "长途行驶中电量不足，需寻找充电站",
    },
    "commute_arrival": {
        "title": "场景四：通勤到达",
        "mode": "owner",
        "description": "日常通勤接近目的地，需找停车场",
    },
    "robotaxi_cant_find_car": {
        "title": "场景五：找不到车",
        "mode": "robotaxi",
        "description": "Robotaxi乘客在上车点找不到车辆",
    },
    "pickup_abnormal": {
        "title": "场景六：上车点异常",
        "mode": "robotaxi",
        "description": "上车点存在施工/禁停等异常",
    },
    "change_destination": {
        "title": "场景七：临时改目的地",
        "mode": "robotaxi",
        "description": "乘客在行程中想修改目的地",
    },
    "passenger_help": {
        "title": "场景八：乘客求助",
        "mode": "robotaxi",
        "description": "乘客身体不适或需要紧急帮助",
    },
}

# 所有可用的场景ID列表
SCENARIO_IDS: list[str] = list(SCENARIO_META.keys())


# ── 场景加载器 ────────────────────────────

def load_scenario(
    scenario_id: str,
) -> tuple[VehicleState, EnvironmentContext, OrderState | None, UserProfile, str]:
    """加载指定场景的完整初始状态。

    Parameters
    ----------
    scenario_id : str
        场景ID，可选值见 SCENARIO_IDS

    Returns
    -------
    tuple
        (vehicle_state, environment, order_state_or_none, user_profile, system_message)

    Raises
    ------
    ValueError
        如果 scenario_id 不存在
    """
    if scenario_id not in SCENARIO_META:
        raise ValueError(
            f"未知场景ID: '{scenario_id}'，"
            f"可选: {', '.join(SCENARIO_IDS)}"
        )

    # 车辆状态
    vehicle = VEHICLE_FACTORIES[scenario_id]()

    # 环境上下文
    environment = ENVIRONMENT_FACTORIES[scenario_id]()

    # 订单（仅 Robotaxi 场景有）
    order = ORDER_FACTORIES.get(scenario_id, lambda: None)()

    # 用户画像
    meta = SCENARIO_META[scenario_id]
    if scenario_id == "parent_child":
        user = _create_parent_profile()
    elif meta["mode"] == "robotaxi":
        user = _create_passenger_profile()
    else:
        user = _create_owner_profile()

    # 系统消息
    system_message = SYSTEM_MESSAGES.get(scenario_id, "")

    return vehicle, environment, order, user, system_message


def get_scenario_meta(scenario_id: str) -> dict:
    """获取场景元数据"""
    return SCENARIO_META.get(scenario_id, {})
