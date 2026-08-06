"""数据模型包

统一导出所有核心数据模型，方便外部引用：
    from models import VehicleState, OrderState, UserProfile, ...
"""

# 车辆相关
from models.vehicle import (
    ACState,
    AmbientLight,
    BatteryInfo,
    CabinState,
    DriverState,
    FuelInfo,
    Location,
    SeatInfo,
    TripInfo,
    VehicleState,
    WindowState,
)

# 订单相关
from models.order import (
    OrderState,
    OrderStatus,
    OrderTimestamps,
    PassengerInfo,
    PricingInfo,
    RouteInfo,
    VehicleInfo,
)

# 用户画像
from models.user_profile import (
    CalendarEvent,
    UserContext,
    UserHistory,
    UserPreferences,
    UserProfile,
)

# 环境上下文
from models.environment import (
    EnvironmentContext,
    NearbyFacilities,
    TimeContext,
    TrafficIncident,
    TrafficInfo,
    WeatherInfo,
)

# 安全规则
from models.safety_rules import (
    EscalationConfig,
    SafetyRule,
    SafetyRuleSet,
)

# Agent 输出
from models.agent_output import (
    AgentResponse,
    AlternativeConsidered,
    FollowUp,
    ForbiddenAction,
    Reasoning,
    SafetyAlert,
    ServicePlan,
    ServiceStep,
    ToolSelectionReason,
)

__all__ = [
    # 车辆
    "ACState", "AmbientLight", "BatteryInfo", "CabinState", "DriverState",
    "FuelInfo", "Location", "SeatInfo", "TripInfo", "VehicleState", "WindowState",
    # 订单
    "OrderState", "OrderStatus", "OrderTimestamps", "PassengerInfo",
    "PricingInfo", "RouteInfo", "VehicleInfo",
    # 用户
    "CalendarEvent", "UserContext", "UserHistory", "UserPreferences", "UserProfile",
    # 环境
    "EnvironmentContext", "NearbyFacilities", "TimeContext",
    "TrafficIncident", "TrafficInfo", "WeatherInfo",
    # 安全
    "EscalationConfig", "SafetyRule", "SafetyRuleSet",
    # Agent 输出
    "AgentResponse", "AlternativeConsidered", "FollowUp", "ForbiddenAction",
    "Reasoning", "SafetyAlert", "ServicePlan", "ServiceStep", "ToolSelectionReason",
]
