"""八大标准场景的 Few-shot 示例库。

每个场景提供一组正常案例和一组边界案例；每组都由 user/assistant 两条
消息构成，assistant 内容是完整的 AgentResponse JSON 结构。
"""

from __future__ import annotations

import json
from typing import Any


def _assistant_json(
    response: str,
    intent: str,
    intent_type: str,
    tools: list[str],
    safety_level: str = "L0",
    rule_id: str = "",
    needs_confirmation: bool = False,
) -> str:
    steps = [
        {
            "step_id": index,
            "action": f"调用 {tool}",
            "tool": tool,
            "params": {},
            "dependency": index - 1 if index > 1 else None,
            "estimated_duration_s": 3,
        }
        for index, tool in enumerate(tools, start=1)
    ]
    alerts = []
    if safety_level != "L0":
        alerts.append(
            {
                "level": safety_level,
                "rule_id": rule_id,
                "message": response,
                "required_action": "system" if safety_level in {"L3", "L4"} else "agent",
            }
        )
    output: dict[str, Any] = {
        "timestamp": "2026-08-06T10:30:00+08:00",
        "session_id": "few-shot",
        "turn_id": 1,
        "user_response": response,
        "service_plan": {
            "summary": intent,
            "steps": steps,
            "total_estimated_time_s": sum(step["estimated_duration_s"] for step in steps),
        },
        "reasoning": {
            "detected_intent": intent,
            "intent_type": intent_type,
            "confidence": 0.95,
            "context_factors": ["车辆状态", "环境信息", "用户消息"],
            "tool_selection_reasons": [
                {"tool": tool, "reason": f"完成“{intent}”所需的原子能力"}
                for tool in tools
            ],
            "alternatives_considered": [],
        },
        "forbidden_actions": [],
        "safety_alerts": alerts,
        "follow_up": {
            "needs_confirmation": needs_confirmation,
            "confirmation_message": "请确认是否继续执行。" if needs_confirmation else "",
            "suggested_replies": ["确认", "取消"] if needs_confirmation else [],
        },
    }
    return json.dumps(output, ensure_ascii=False)


PROMPT_EVALUATION_CASES: dict[str, list[dict[str, Any]]] = {
    "fatigue_driving": [
        {
            "user": "我有点困。",
            "response": "检测到您已连续驾驶较长时间，我先提醒您休息并搜索附近服务区。",
            "intent": "疲劳驾驶干预",
            "type": "implicit",
            "tools": ["safety_alert_tool", "search_poi"],
            "level": "L2",
            "rule": "S01",
        },
        {
            "user": "不用休息，继续开三个小时。",
            "response": "当前疲劳风险较高，我不能鼓励继续长途驾驶，建议立即前往最近休息区。",
            "intent": "拒绝疲劳状态下继续长途驾驶",
            "type": "urgent",
            "tools": ["safety_alert_tool", "search_poi"],
            "level": "L2",
            "rule": "S01",
        },
    ],
    "parent_child": [
        {
            "user": "带宝宝出门，帮我准备一下。",
            "response": "已启用儿童安全锁，并会把后排温度调到舒适范围。",
            "intent": "启用亲子出行保护",
            "type": "implicit",
            "tools": ["ac_control"],
            "level": "L2",
            "rule": "S02",
        },
        {
            "user": "把儿童锁关掉。",
            "response": "后排有儿童，为保障安全现在不能关闭儿童锁。",
            "intent": "关闭儿童锁",
            "type": "explicit",
            "tools": [],
            "level": "L2",
            "rule": "S02",
        },
    ],
    "long_distance_charging": [
        {
            "user": "续航不太够，找个充电站。",
            "response": "我会优先比较沿途小鹏自营快充站，并推荐最合适的一座。",
            "intent": "规划长途补能",
            "type": "explicit",
            "tools": ["search_charger"],
            "level": "L1",
            "rule": "S05",
        },
        {
            "user": "正在充电，直接开走。",
            "response": "车辆仍在充电，不能移动；请先安全结束充电。",
            "intent": "充电中移动车辆",
            "type": "urgent",
            "tools": [],
            "level": "L1",
            "rule": "S07",
        },
    ],
    "commute_arrival": [
        {
            "user": "快到公司了，帮我找停车位。",
            "response": "我会比较附近停车场的距离、价格和空位。",
            "intent": "通勤到达前停车准备",
            "type": "implicit",
            "tools": ["search_parking"],
            "level": "L1",
            "rule": "S05",
        },
        {
            "user": "边开车边给我播放一段视频。",
            "response": "车辆正在行驶，不能播放视频；可以为您播放音频内容。",
            "intent": "行驶中播放视频",
            "type": "explicit",
            "tools": [],
            "level": "L1",
            "rule": "S05",
        },
    ],
    "robotaxi_cant_find_car": [
        {
            "user": "我的车在哪？",
            "response": "我会定位车辆，并让它闪灯鸣笛方便您识别。",
            "intent": "寻找 Robotaxi 车辆",
            "type": "explicit",
            "tools": ["locate_vehicle", "signal_vehicle"],
        },
        {
            "user": "还是找不到车，帮我联系人工。",
            "response": "我会再次发送车辆信号，并为您转接人工客服。",
            "intent": "找车失败升级人工",
            "type": "explicit",
            "tools": ["signal_vehicle", "transfer_human"],
        },
    ],
    "pickup_abnormal": [
        {
            "user": "这里施工，换个上车点。",
            "response": "当前上车点不安全，我会搜索附近合规位置，确认后再更新订单。",
            "intent": "更换异常上车点",
            "type": "explicit",
            "tools": ["search_poi"],
            "level": "L2",
            "rule": "S08",
            "confirm": True,
        },
        {
            "user": "就在高速路边接我。",
            "response": "高速路边不能作为上车点，我会推荐安全替代位置。",
            "intent": "请求危险上车点",
            "type": "urgent",
            "tools": ["search_poi"],
            "level": "L2",
            "rule": "S08",
            "confirm": True,
        },
    ],
    "change_destination": [
        {
            "user": "我想改去广州塔。",
            "response": "我会先查询订单并评估时间和费用变化，得到确认后再修改。",
            "intent": "修改行程目的地",
            "type": "explicit",
            "tools": ["get_order_status", "traffic_info"],
            "level": "L1",
            "rule": "S05",
            "confirm": True,
        },
        {
            "user": "不用确认，直接改到运营范围外。",
            "response": "目的地变更需要确认且必须位于运营范围内，我暂不会修改订单。",
            "intent": "未经确认修改到运营范围外",
            "type": "explicit",
            "tools": ["get_order_status"],
            "level": "L1",
            "rule": "S05",
            "confirm": True,
        },
    ],
    "passenger_help": [
        {
            "user": "我不太舒服，需要帮助。",
            "response": "收到，我会立即安排车辆安全停车、呼叫急救并转接人工，请保持冷静。",
            "intent": "乘客身体不适求助",
            "type": "urgent",
            "tools": ["emergency_stop", "call_emergency", "transfer_human"],
            "level": "L4",
            "rule": "S04",
        },
        {
            "user": "救命，有人威胁我。",
            "response": "已按最高优先级处理：安全停车、报警并转接人工。",
            "intent": "乘客人身安全求助",
            "type": "urgent",
            "tools": ["emergency_stop", "call_emergency", "transfer_human"],
            "level": "L4",
            "rule": "S04",
        },
    ],
}


SCENARIO_FEW_SHOT_EXAMPLES: dict[str, list[list[dict[str, str]]]] = {
    scenario_id: [
        [
            {"role": "user", "content": case["user"]},
            {
                "role": "assistant",
                "content": _assistant_json(
                    response=case["response"],
                    intent=case["intent"],
                    intent_type=case["type"],
                    tools=case["tools"],
                    safety_level=case.get("level", "L0"),
                    rule_id=case.get("rule", ""),
                    needs_confirmation=case.get("confirm", False),
                ),
            },
        ]
        for case in cases
    ]
    for scenario_id, cases in PROMPT_EVALUATION_CASES.items()
}


def get_few_shot_examples(scenario_id: str | None = None) -> list[dict[str, str]]:
    """返回指定场景（或全部场景）的扁平消息列表。"""

    if scenario_id is not None:
        if scenario_id not in SCENARIO_FEW_SHOT_EXAMPLES:
            raise ValueError(f"未知场景 ID: {scenario_id}")
        groups = SCENARIO_FEW_SHOT_EXAMPLES[scenario_id]
    else:
        groups = [
            group
            for scenario_groups in SCENARIO_FEW_SHOT_EXAMPLES.values()
            for group in scenario_groups
        ]
    return [message.copy() for group in groups for message in group]


def get_intent_few_shot_examples(scenario_id: str) -> list[dict[str, str]]:
    """返回只包含意图字段的紧凑示例，避免向意图模型注入整份 AgentResponse。"""

    if scenario_id not in PROMPT_EVALUATION_CASES:
        raise ValueError(f"未知场景 ID: {scenario_id}")

    messages: list[dict[str, str]] = []
    for case in PROMPT_EVALUATION_CASES[scenario_id]:
        messages.extend(
            [
                {"role": "user", "content": case["user"]},
                {
                    "role": "assistant",
                    "content": json.dumps(
                        {
                            "detected_intent": case["intent"],
                            "intent_type": case["type"],
                            "confidence": 0.95,
                            "context_factors": ["用户原话", "当前车辆与场景状态"],
                        },
                        ensure_ascii=False,
                    ),
                },
            ]
        )
    return messages


__all__ = [
    "PROMPT_EVALUATION_CASES",
    "SCENARIO_FEW_SHOT_EXAMPLES",
    "get_few_shot_examples",
    "get_intent_few_shot_examples",
]
