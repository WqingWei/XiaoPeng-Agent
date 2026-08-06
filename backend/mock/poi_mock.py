"""POI 模拟数据

定义广州/深圳区域的充电站、停车场、服务区、医院、餐厅数据。
坐标使用真实经纬度近似值。
"""

from __future__ import annotations


# ── 充电站 ──────────────────────────────────

CHARGING_STATIONS = [
    {
        "id": "CS-001", "name": "小鹏超充站（天河体育中心）",
        "address": "广州市天河区体育西路191号",
        "lat": 23.1356, "lng": 113.3287,
        "power_kw": 480, "price_per_kwh": 1.2,
        "available_chargers": 4, "total_chargers": 8,
        "is_xpeng": True, "distance_km": 1.2,
    },
    {
        "id": "CS-002", "name": "小鹏超充站（珠江新城）",
        "address": "广州市天河区华夏路16号",
        "lat": 23.1191, "lng": 113.3218,
        "power_kw": 360, "price_per_kwh": 1.3,
        "available_chargers": 2, "total_chargers": 6,
        "is_xpeng": True, "distance_km": 3.5,
    },
    {
        "id": "CS-003", "name": "南方电网充电站（番禺万达）",
        "address": "广州市番禺区南村镇万博中心",
        "lat": 23.0056, "lng": 113.3364,
        "power_kw": 120, "price_per_kwh": 0.9,
        "available_chargers": 6, "total_chargers": 10,
        "is_xpeng": False, "distance_km": 12.8,
    },
    {
        "id": "CS-004", "name": "特来电充电站（白云机场T2）",
        "address": "广州市花都区白云国际机场T2航站楼",
        "lat": 23.3924, "lng": 113.3036,
        "power_kw": 240, "price_per_kwh": 1.5,
        "available_chargers": 8, "total_chargers": 12,
        "is_xpeng": False, "distance_km": 35.2,
    },
    {
        "id": "CS-005", "name": "小鹏超充站（深圳湾万象城）",
        "address": "深圳市南山区深圳湾万象城B1层",
        "lat": 22.5175, "lng": 113.9386,
        "power_kw": 480, "price_per_kwh": 1.4,
        "available_chargers": 3, "total_chargers": 6,
        "is_xpeng": True, "distance_km": 120.0,
    },
    {
        "id": "CS-006", "name": "星星充电站（广州南站）",
        "address": "广州市番禺区石壁街道广州南站P3停车场",
        "lat": 22.9876, "lng": 113.2688,
        "power_kw": 180, "price_per_kwh": 1.1,
        "available_chargers": 5, "total_chargers": 8,
        "is_xpeng": False, "distance_km": 18.5,
    },
]


# ── 停车场 ──────────────────────────────────

PARKING_LOTS = [
    {
        "id": "PK-001", "name": "天河城地下停车场",
        "address": "广州市天河区天河路208号",
        "lat": 23.1330, "lng": 113.3290,
        "price_per_hour": 12, "available_spots": 120, "total_spots": 800,
        "distance_km": 0.5,
    },
    {
        "id": "PK-002", "name": "珠江新城花城广场停车场",
        "address": "广州市天河区花城大道",
        "lat": 23.1170, "lng": 113.3210,
        "price_per_hour": 16, "available_spots": 45, "total_spots": 500,
        "distance_km": 2.1,
    },
    {
        "id": "PK-003", "name": "广州塔停车场",
        "address": "广州市海珠区阅江西路222号",
        "lat": 23.1066, "lng": 113.3245,
        "price_per_hour": 10, "available_spots": 200, "total_spots": 400,
        "distance_km": 4.0,
    },
    {
        "id": "PK-004", "name": "正佳广场停车场",
        "address": "广州市天河区天河路228号",
        "lat": 23.1339, "lng": 113.3263,
        "price_per_hour": 15, "available_spots": 80, "total_spots": 1200,
        "distance_km": 0.8,
    },
    {
        "id": "PK-005", "name": "广州国际金融中心（IFC）停车场",
        "address": "广州市天河区珠江西路5号",
        "lat": 23.1182, "lng": 113.3231,
        "price_per_hour": 20, "available_spots": 30, "total_spots": 300,
        "distance_km": 2.5,
    },
]


# ── 服务区 ──────────────────────────────────

SERVICE_AREAS = [
    {
        "id": "SA-001", "name": "沙贝服务区",
        "address": "广佛高速沙贝段",
        "lat": 23.1628, "lng": 113.1876,
        "distance_km": 8.5,
        "facilities": ["加油站", "充电桩", "餐厅", "洗手间", "便利店"],
    },
    {
        "id": "SA-002", "name": "南沙服务区",
        "address": "广澳高速南沙段",
        "lat": 22.8345, "lng": 113.5278,
        "distance_km": 35.0,
        "facilities": ["加油站", "充电桩", "餐厅", "洗手间"],
    },
    {
        "id": "SA-003", "name": "北兴服务区",
        "address": "机场高速北兴段",
        "lat": 23.4256, "lng": 113.3789,
        "distance_km": 42.0,
        "facilities": ["加油站", "充电桩", "洗手间", "便利店"],
    },
    {
        "id": "SA-004", "name": "九龙服务区",
        "address": "广河高速九龙段",
        "lat": 23.2890, "lng": 113.6543,
        "distance_km": 55.0,
        "facilities": ["加油站", "充电桩", "餐厅", "洗手间", "汽修"],
    },
    {
        "id": "SA-005", "name": "大雁山服务区",
        "address": "广珠西线大雁山段",
        "lat": 22.7156, "lng": 113.3567,
        "distance_km": 60.0,
        "facilities": ["加油站", "充电桩", "餐厅", "洗手间", "便利店"],
    },
]


# ── 医院 ──────────────────────────────────

HOSPITALS = [
    {
        "id": "HP-001", "name": "中山大学附属第一医院",
        "address": "广州市越秀区中山二路58号",
        "lat": 23.1295, "lng": 113.2865,
        "distance_km": 3.2, "level": "三甲",
        "emergency_phone": "020-28823388",
    },
    {
        "id": "HP-002", "name": "广州市妇女儿童医疗中心",
        "address": "广州市天河区金穗路9号",
        "lat": 23.1230, "lng": 113.3210,
        "distance_km": 2.0, "level": "三甲",
        "emergency_phone": "020-38076666",
    },
    {
        "id": "HP-003", "name": "广东省人民医院",
        "address": "广州市越秀区中山二路106号",
        "lat": 23.1285, "lng": 113.2895,
        "distance_km": 3.5, "level": "三甲",
        "emergency_phone": "020-83827812",
    },
    {
        "id": "HP-004", "name": "南方医科大学南方医院",
        "address": "广州市白云区广州大道北1838号",
        "lat": 23.2042, "lng": 113.3321,
        "distance_km": 8.0, "level": "三甲",
        "emergency_phone": "020-61641888",
    },
    {
        "id": "HP-005", "name": "广州市第一人民医院",
        "address": "广州市越秀区盘福路1号",
        "lat": 23.1390, "lng": 113.2678,
        "distance_km": 5.0, "level": "三甲",
        "emergency_phone": "020-81048888",
    },
]


# ── 餐厅 ──────────────────────────────────

RESTAURANTS = [
    {
        "id": "RS-001", "name": "广州酒家（文昌总店）",
        "address": "广州市荔湾区文昌南路2号",
        "lat": 23.1215, "lng": 113.2478,
        "distance_km": 4.5, "cuisine": "粤菜",
        "price_range": "¥120-200/人", "rating": 4.6,
    },
    {
        "id": "RS-002", "name": "点都德（花城汇店）",
        "address": "广州市天河区花城大道花城汇北区",
        "lat": 23.1200, "lng": 113.3200,
        "distance_km": 1.8, "cuisine": "茶点",
        "price_range": "¥80-120/人", "rating": 4.5,
    },
    {
        "id": "RS-003", "name": "海底捞（正佳广场店）",
        "address": "广州市天河区天河路228号正佳广场6楼",
        "lat": 23.1340, "lng": 113.3270,
        "distance_km": 0.9, "cuisine": "火锅",
        "price_range": "¥130-160/人", "rating": 4.4,
    },
    {
        "id": "RS-004", "name": "陶陶居（太古汇店）",
        "address": "广州市天河区天河路383号太古汇M层",
        "lat": 23.1345, "lng": 113.3315,
        "distance_km": 1.0, "cuisine": "粤菜",
        "price_range": "¥150-250/人", "rating": 4.7,
    },
    {
        "id": "RS-005", "name": "九毛九（天河城店）",
        "address": "广州市天河区天河路208号天河城4楼",
        "lat": 23.1328, "lng": 113.3285,
        "distance_km": 0.6, "cuisine": "西北菜",
        "price_range": "¥60-90/人", "rating": 4.3,
    },
]


# ── 查询函数 ──────────────────────────────────

def get_pois_by_category(category: str) -> list[dict]:
    """按类别获取 POI 列表"""
    mapping = {
        "charging_station": CHARGING_STATIONS,
        "parking_lot": PARKING_LOTS,
        "service_area": SERVICE_AREAS,
        "hospital": HOSPITALS,
        "restaurant": RESTAURANTS,
    }
    return mapping.get(category, [])


def search_pois(keyword: str, radius_km: float = 10.0) -> list[dict]:
    """按关键词和距离搜索所有 POI"""
    all_pois = (
        CHARGING_STATIONS + PARKING_LOTS + SERVICE_AREAS
        + HOSPITALS + RESTAURANTS
    )
    results = []
    for poi in all_pois:
        if keyword.lower() in poi["name"].lower():
            if poi.get("distance_km", 999) <= radius_km:
                results.append(poi)
    return results
