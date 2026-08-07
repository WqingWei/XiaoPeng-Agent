"""Agent 系统 Prompt 构建器。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from models.agent_output import AgentResponse
from models.environment import EnvironmentContext
from models.order import OrderState
from models.user_profile import UserProfile
from models.vehicle import VehicleState
from tools.base import ToolRegistry


RULES_FILE = Path(__file__).parents[1] / "safety" / "rules.json"


def _tool_descriptions(registry: ToolRegistry) -> list[dict]:
    return [
        {
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.args,
        }
        for tool in registry.get_all_tools()
    ]


def _safety_rule_summary() -> list[dict]:
    with RULES_FILE.open("r", encoding="utf-8") as file:
        rules = json.load(file)["rules"]
    return [
        {
            "rule_id": rule["rule_id"],
            "name": rule["name"],
            "type": rule["type"],
            "action": rule["action"],
            "level": rule["escalation"]["level"],
        }
        for rule in rules
    ]


def build_system_prompt(
    mode: Literal["owner", "robotaxi"],
    vehicle_state: VehicleState,
    environment: EnvironmentContext,
    order: OrderState | None,
    user_profile: UserProfile,
    tool_registry: ToolRegistry | None = None,
) -> str:
    """拼接角色、工具、安全规则、输出约束及实时状态。"""

    registry = tool_registry or ToolRegistry()
    role_name = "车主自驾服务" if mode == "owner" else "Robotaxi 乘客服务"
    payload = {
        "tools": _tool_descriptions(registry),
        "safety_rules": _safety_rule_summary(),
        "output_json_schema": AgentResponse.model_json_schema(),
        "state": {
            "vehicle": vehicle_state.model_dump(mode="json"),
            "environment": environment.model_dump(mode="json"),
            "order": order.model_dump(mode="json") if order else None,
            "user_profile": user_profile.model_dump(mode="json"),
        },
    }

    return (
        "你是小鹏 AI 出行服务管家，是座舱、出行与 Robotaxi 服务之上的智能编排中枢。\n"
        f"当前模式：{mode}（{role_name}）。\n\n"
        "工作原则：\n"
        "1. 先理解显性、隐性或紧急意图，再选择最小且完整的工具组合。\n"
        "2. 安全优先；硬规则不可绕过，危险操作必须拒绝并给出安全替代方案。\n"
        "3. 不编造工具、状态或执行结果；修改订单等需要确认的动作先说明影响。\n"
        "4. 回复温暖、专业、简洁，车辆行驶时尤其精炼，并清楚说明做了什么。\n"
        "5. 结构化输出必须严格符合提供的 JSON Schema，不要输出 Markdown 代码围栏。\n\n"
        "以下是可用工具、安全规则、输出 Schema 和当前状态快照：\n"
        + json.dumps(payload, ensure_ascii=False, indent=2)
    )


def build_intent_system_prompt(mode: Literal["owner", "robotaxi"]) -> str:
    """构建意图分类专用的轻量系统 Prompt，避免注入工具与最终响应 Schema。"""

    role_name = "车主自驾服务" if mode == "owner" else "Robotaxi 乘客服务"
    return (
        "你是小鹏 AI 出行服务管家的意图分类器。"
        f"当前模式是 {mode}（{role_name}）。"
        "只判断用户此刻的主意图、意图类型、置信度和关键上下文；"
        "不要规划工具、生成用户回复或输出分析过程。"
        "安全冲突和乘客求助必须优先识别，输出必须严格符合用户消息中的 JSON 格式。"
    )


__all__ = ["build_intent_system_prompt", "build_system_prompt"]
