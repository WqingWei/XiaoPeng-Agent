"""工具箱基础架构

提供 ToolContext（共享状态管理器）和 ToolRegistry（工具注册器）。
所有工具通过 ToolContext 共享车辆/环境/订单等状态。
"""

from __future__ import annotations

from typing import Any

from loguru import logger

from models.vehicle import VehicleState
from models.environment import EnvironmentContext
from models.order import OrderState
from models.user_profile import UserProfile


class ToolContext:
    """工具共享上下文（单例）

    所有工具通过此对象访问和修改当前状态。
    在加载场景时调用 init_from_scenario() 初始化。
    """

    _instance: ToolContext | None = None

    def __new__(cls) -> ToolContext:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._initialized = True
        self.vehicle: VehicleState = VehicleState()
        self.environment: EnvironmentContext = EnvironmentContext()
        self.order: OrderState | None = None
        self.user: UserProfile = UserProfile()
        self.media_volume: int = 30
        self.media_playing: bool = False
        logger.debug("ToolContext 初始化完成")

    @classmethod
    def reset(cls) -> None:
        """重置单例（测试用）"""
        cls._instance = None

    def init_from_scenario(
        self,
        vehicle: VehicleState,
        environment: EnvironmentContext,
        order: OrderState | None,
        user: UserProfile,
    ) -> None:
        """从场景预设加载初始状态"""
        self.vehicle = vehicle
        self.environment = environment
        self.order = order
        self.user = user
        self.media_volume = 30
        self.media_playing = False
        logger.info(f"ToolContext 已从场景加载: mode={vehicle.mode}, status={vehicle.driving_status}")

    def vehicle_dict(self) -> dict[str, Any]:
        return self.vehicle.model_dump()

    def environment_dict(self) -> dict[str, Any]:
        return self.environment.model_dump()

    def order_dict(self) -> dict[str, Any] | None:
        return self.order.model_dump() if self.order else None

    def user_dict(self) -> dict[str, Any]:
        return self.user.model_dump()


def get_context() -> ToolContext:
    """获取全局 ToolContext 单例"""
    return ToolContext()


class ToolRegistry:
    """工具注册器

    收集所有 @tool 装饰的工具函数，供 LangChain Agent 使用。
    """

    def __init__(self) -> None:
        self._tools: list = []
        self._loaded = False

    def load_all(self) -> None:
        """加载所有工具模块并收集 @tool 函数"""
        if self._loaded:
            return

        from tools.cabin_tools import (
            ac_control, seat_control, window_control,
            light_control, media_control, child_lock_control,
        )
        from tools.navigation_tools import (
            navigate_to, search_poi, search_parking,
            search_charger, traffic_info,
        )
        from tools.vehicle_tools import (
            get_vehicle_status, get_driver_status,
            get_location, get_environment_info,
        )
        from tools.order_tools import (
            create_order, modify_order, cancel_order,
            get_order_status, locate_vehicle, signal_vehicle,
        )
        from tools.safety_tools import (
            emergency_stop, call_rescue, call_emergency,
            transfer_human, safety_alert_tool,
        )

        self._tools = [
            # 座舱 (6)
            ac_control, seat_control, window_control,
            light_control, media_control, child_lock_control,
            # 导航 (5)
            navigate_to, search_poi, search_parking,
            search_charger, traffic_info,
            # 车辆状态 (4)
            get_vehicle_status, get_driver_status,
            get_location, get_environment_info,
            # 订单 (6)
            create_order, modify_order, cancel_order,
            get_order_status, locate_vehicle, signal_vehicle,
            # 安全 (5)
            emergency_stop, call_rescue, call_emergency,
            transfer_human, safety_alert_tool,
        ]
        self._loaded = True
        logger.info(f"ToolRegistry 已加载 {len(self._tools)} 个工具")

    def get_all_tools(self) -> list:
        """返回所有已注册的工具列表"""
        if not self._loaded:
            self.load_all()
        return self._tools

    @property
    def tool_count(self) -> int:
        return len(self._tools)
