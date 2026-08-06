"""模拟数据包

提供 POI 数据、车辆/环境/订单工厂函数和场景加载器。
"""

from mock.poi_mock import (
    CHARGING_STATIONS,
    PARKING_LOTS,
    SERVICE_AREAS,
    HOSPITALS,
    RESTAURANTS,
    get_pois_by_category,
    search_pois,
)
from mock.vehicle_mock import VEHICLE_FACTORIES
from mock.environment_mock import ENVIRONMENT_FACTORIES
from mock.order_mock import ORDER_FACTORIES
from mock.scenario_presets import (
    SCENARIO_IDS,
    SCENARIO_META,
    load_scenario,
    get_scenario_meta,
)
