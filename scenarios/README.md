# 场景与模拟数据说明

`scenarios/` 文档与 `backend/mock/` 的 8 个可重置场景一一对应。每次调用
`POST /api/scenario` 会重新创建车辆、环境、订单和用户画像，并清空当前会话历史。

## 文档索引

1. [疲劳驾驶](fatigue_driving.md)
2. [亲子出行](parent_child.md)
3. [长途补能](long_distance_charging.md)
4. [通勤到达](commute_arrival.md)
5. [Robotaxi 找不到车](robotaxi_cant_find_car.md)
6. [上车点异常](pickup_abnormal.md)
7. [临时改目的地](change_destination.md)
8. [乘客求助](passenger_help.md)

## 数据组成

| 数据 | 源码 | 内容 |
|------|------|------|
| 车辆状态 | `backend/mock/vehicle_mock.py` | 模式、位置、车速、电量/续航、座舱、驾驶员和行程 |
| 环境上下文 | `backend/mock/environment_mock.py` | 时间、天气、能见度、拥堵、交通事件和附近设施 |
| Robotaxi 订单 | `backend/mock/order_mock.py` | 乘客、车辆、路线、计价与时间戳；仅场景 5–8 存在 |
| 用户画像 | `backend/mock/scenario_presets.py` | 车主/乘客角色、偏好、儿童上下文和场景系统消息 |
| POI / 服务结果 | `backend/mock/poi_mock.py` | 充电站、停车场、服务区等模拟查询结果 |
| 安全规则 | `backend/safety/rules.json` | S01–S12 触发条件、动作、话术与 L0–L4 升级 |

## 运行时语义

- 场景数据是确定性初始值；时间戳使用当前日期叠加预设时分。
- Agent 工具会修改当前会话状态并写入 PostgreSQL，例如紧急停车把车速置为 0；Redis
  保存同一快照的读缓存。
- 重新切换场景会恢复预设，不会持久化到数据库或外部车端。
- 真实 LLM 不可用时，意图、编排和回复会使用与测试同源的本地 Fallback。

## 隐私与边界

- 人名、手机号、车牌、订单号与坐标都是 Demo 数据；手机号已脱敏。
- 地名使用广州市演示地标，距离、价格、车位和充电功率不代表实时信息。
- `call_emergency`、`transfer_human`、车控和订单工具仅返回模拟结果。
- 本项目不应用于真实医疗、紧急决策或车辆控制。
