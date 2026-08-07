"""Agent 流水线使用的安全规则引擎。

该模块负责把车辆、环境和当前意图转换为规则上下文，使用 AST 白名单
求值器执行 ``safety/rules.json`` 中的条件，并聚合成单个 ``SafetyResult``。
"""

from __future__ import annotations

import ast
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Literal

from loguru import logger
from pydantic import BaseModel, Field

from models.agent_output import ForbiddenAction, SafetyAlert
from models.environment import EnvironmentContext
from models.safety_rules import SafetyRule, SafetyRuleSet
from models.vehicle import VehicleState


RULES_FILE = Path(__file__).parents[1] / "safety" / "rules.json"
SafetyLevel = Literal["L0", "L1", "L2", "L3", "L4"]


class SafetyResult(BaseModel):
    """一次安全检查的聚合结果。"""

    safety_level: SafetyLevel = "L0"
    triggered_rules: list[SafetyRule] = Field(default_factory=list)
    required_actions: list[str] = Field(default_factory=list)
    forbidden_actions: list[ForbiddenAction] = Field(default_factory=list)
    safety_alerts: list[SafetyAlert] = Field(default_factory=list)


class UnsafeConditionError(ValueError):
    """规则表达式包含白名单之外的语法。"""


class _Missing:
    """表示规则上下文中不存在的字段。"""


MISSING = _Missing()


class _ConditionEvaluator(ast.NodeVisitor):
    """仅支持安全规则所需语法的 AST 求值器。"""

    def __init__(self, context: Mapping[str, Any]):
        self.context = context

    def evaluate(self, condition: str) -> bool:
        try:
            tree = ast.parse(condition, mode="eval")
        except SyntaxError as exc:
            raise UnsafeConditionError(f"无效的规则表达式: {condition}") from exc
        return bool(self.visit(tree))

    def generic_visit(self, node: ast.AST) -> Any:
        raise UnsafeConditionError(f"不支持的规则语法: {type(node).__name__}")

    def visit_Expression(self, node: ast.Expression) -> Any:  # noqa: N802
        return self.visit(node.body)

    def visit_Constant(self, node: ast.Constant) -> Any:  # noqa: N802
        if isinstance(node.value, (str, int, float, bool)) or node.value is None:
            return node.value
        raise UnsafeConditionError(f"不支持的常量类型: {type(node.value).__name__}")

    def visit_Name(self, node: ast.Name) -> Any:  # noqa: N802
        aliases = {"true": True, "false": False, "null": None}
        if node.id in aliases:
            return aliases[node.id]
        if node.id.startswith("_"):
            raise UnsafeConditionError("规则字段不能以下划线开头")
        return self.context.get(node.id, MISSING)

    def visit_Attribute(self, node: ast.Attribute) -> Any:  # noqa: N802
        if node.attr.startswith("_"):
            raise UnsafeConditionError("规则字段不能以下划线开头")
        value = self.visit(node.value)
        if value is MISSING:
            return MISSING
        if isinstance(value, Mapping):
            return value.get(node.attr, MISSING)
        return MISSING

    def visit_BoolOp(self, node: ast.BoolOp) -> bool:  # noqa: N802
        if isinstance(node.op, ast.And):
            return all(bool(self.visit(value)) for value in node.values)
        if isinstance(node.op, ast.Or):
            return any(bool(self.visit(value)) for value in node.values)
        raise UnsafeConditionError(f"不支持的布尔运算: {type(node.op).__name__}")

    def visit_UnaryOp(self, node: ast.UnaryOp) -> bool:  # noqa: N802
        if isinstance(node.op, ast.Not):
            return not bool(self.visit(node.operand))
        raise UnsafeConditionError(f"不支持的一元运算: {type(node.op).__name__}")

    def visit_BinOp(self, node: ast.BinOp) -> Any:  # noqa: N802
        left = self.visit(node.left)
        right = self.visit(node.right)
        if left is MISSING or right is MISSING:
            return MISSING
        operations = {
            ast.Add: lambda: left + right,
            ast.Sub: lambda: left - right,
            ast.Mult: lambda: left * right,
            ast.Div: lambda: left / right,
        }
        operation = operations.get(type(node.op))
        if operation is None:
            raise UnsafeConditionError(f"不支持的算术运算: {type(node.op).__name__}")
        try:
            return operation()
        except (TypeError, ValueError, ZeroDivisionError):
            return MISSING

    def visit_Compare(self, node: ast.Compare) -> bool:  # noqa: N802
        left = self.visit(node.left)
        operations = {
            ast.Gt: lambda a, b: a > b,
            ast.GtE: lambda a, b: a >= b,
            ast.Lt: lambda a, b: a < b,
            ast.LtE: lambda a, b: a <= b,
            ast.Eq: lambda a, b: a == b,
            ast.NotEq: lambda a, b: a != b,
        }

        for operator, comparator in zip(node.ops, node.comparators):
            right = self.visit(comparator)
            if left is MISSING or right is MISSING:
                return False
            compare = operations.get(type(operator))
            if compare is None:
                raise UnsafeConditionError(
                    f"不支持的比较运算: {type(operator).__name__}"
                )
            try:
                if not compare(left, right):
                    return False
            except (TypeError, ValueError):
                return False
            left = right
        return True


def _model_to_dict(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, BaseModel):
        return value.model_dump(mode="python")
    if isinstance(value, Mapping):
        return dict(value)
    raise TypeError(f"安全上下文只接受 Pydantic 模型或映射，收到: {type(value).__name__}")


def _deep_merge(target: dict[str, Any], source: Mapping[str, Any]) -> None:
    """将调用方提供的意图上下文覆盖到派生上下文中。"""

    for key, value in source.items():
        if isinstance(value, Mapping) and isinstance(target.get(key), dict):
            _deep_merge(target[key], value)
        else:
            target[key] = dict(value) if isinstance(value, Mapping) else value


def _flatten_context(value: Any, output: dict[str, Any]) -> None:
    if not isinstance(value, Mapping):
        return
    for key, child in value.items():
        if isinstance(child, Mapping):
            _flatten_context(child, output)
        elif child is not MISSING:
            output.setdefault(key, child)


class SafetyEngine:
    """加载并执行 12 条安全规则。"""

    def __init__(self, rules_file: Path | str | None = None):
        self._rules_file = Path(rules_file) if rules_file else RULES_FILE
        self.rules = self._load_rules()

    def _load_rules(self) -> list[SafetyRule]:
        try:
            with self._rules_file.open("r", encoding="utf-8") as file:
                data = json.load(file)
        except (OSError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"无法加载安全规则: {self._rules_file}") from exc

        rule_set = SafetyRuleSet.model_validate(data)
        logger.info(f"安全引擎已加载 {len(rule_set.rules)} 条规则")
        return rule_set.rules

    @staticmethod
    def evaluate_condition(condition: str, context: Mapping[str, Any]) -> bool:
        """公开的条件求值入口，方便规则校验和单元测试。"""

        return _ConditionEvaluator(context).evaluate(condition)

    def _build_context(
        self,
        vehicle_state: VehicleState | Mapping[str, Any],
        environment: EnvironmentContext | Mapping[str, Any] | None,
        intent: str | Mapping[str, Any] | BaseModel | None,
        user_message: str,
    ) -> dict[str, Any]:
        vehicle = _model_to_dict(vehicle_state)
        environment_data = _model_to_dict(environment)
        intent_data = (
            _model_to_dict(intent)
            if isinstance(intent, (Mapping, BaseModel))
            else {}
        )

        cabin = vehicle.setdefault("cabin", {})
        driver = vehicle.setdefault("driver", {})
        trip = vehicle.setdefault("trip", {})
        seats = cabin.get("seats") or []
        driver_seat = next((seat for seat in seats if seat.get("id") == "driver"), {})
        rear_seats = [seat for seat in seats if str(seat.get("id", "")).startswith("rear_")]

        cabin["child_seat_detected"] = any(
            seat.get("child_seat", False) and seat.get("occupied", False)
            for seat in rear_seats
        )
        cabin["rear_child_present"] = cabin["child_seat_detected"]
        driver["seat_occupied"] = driver_seat.get("occupied", True)

        ac = cabin.setdefault("ac", {})
        zone_temp = ac.get("zone_temp") or {}
        ac.setdefault("target_temp", zone_temp.get("driver", 24))

        nearby = environment_data.get("nearby") or {}
        service_areas = nearby.get("service_areas") or []
        chargers = nearby.get("charging_stations") or []
        first_service_area = service_areas[0] if service_areas else {}
        first_charger = chargers[0] if chargers else {}

        normalized_message = user_message.strip().lower()
        intent_text = " ".join(
            str(intent_data.get(key, ""))
            for key in ("detected_intent", "original_message", "name")
        ).lower()
        help_signal = any(
            keyword in normalized_message
            for keyword in (
                "求助", "救命", "身体不适", "不舒服", "不太舒服",
                "要吐", "威胁", "紧急帮助", "help",
            )
        )
        traffic_incidents = (environment_data.get("traffic") or {}).get("incidents") or []
        pickup_request = any(
            keyword in f"{normalized_message} {intent_text}"
            for keyword in ("上车点", "接我", "pickup")
        )
        explicit_danger = any(
            keyword in normalized_message
            for keyword in ("高速路边", "施工", "禁停", "危险")
        )
        relevant_incident = next(
            (
                incident
                for incident in traffic_incidents
                if incident.get("type") in {"construction", "closure"}
            ),
            None,
        )
        pickup_in_danger_zone = pickup_request and (
            explicit_danger or relevant_incident is not None
        )
        danger_zone_type = (
            relevant_incident.get("type", "危险区域")
            if relevant_incident
            else "危险区域"
        )

        context: dict[str, Any] = {
            "vehicle": vehicle,
            "driver": driver,
            "cabin": cabin,
            "battery": vehicle.get("battery", {}),
            "trip": {
                **trip,
                "remaining_distance_km": intent_data.get(
                    "remaining_distance_km",
                    intent_data.get("destination_distance_km", 0),
                ),
            },
            "time": environment_data.get("time", {}),
            "weather": environment_data.get("weather", {}),
            "traffic": environment_data.get("traffic", {}),
            "passenger": {"help_signal": help_signal},
            "order": {
                "pickup_in_danger_zone": pickup_in_danger_zone,
                "danger_zone_type": danger_zone_type,
            },
            "safety_event": {"level": 0},
            "media": {"volume": 30, "playing": False},
            "intent": intent if isinstance(intent, str) else intent_data.get("name", ""),
            "user_message": user_message,
            "rest_area_distance_km": first_service_area.get("distance_km", "未知"),
            "nearest_charger_name": first_charger.get("name", "附近充电站"),
        }

        # intent 可承载订单、媒体、安全事件等尚未进入基础状态模型的运行时字段。
        _deep_merge(context, intent_data)
        return context

    @staticmethod
    def _render_message(template: str, context: Mapping[str, Any]) -> str:
        flat: dict[str, Any] = {}
        _flatten_context(context, flat)

        class _SafeFormatDict(dict[str, Any]):
            def __missing__(self, key: str) -> str:
                return f"{{{key}}}"

        return template.format_map(_SafeFormatDict(flat))

    @staticmethod
    def _required_actions(rule: SafetyRule) -> list[str]:
        action_labels = {
            "reject": f"拒绝执行：{rule.name}",
            "warn": f"发出安全警告：{rule.name}",
            "force": f"强制执行安全措施：{rule.name}",
            "alert": f"立即触发安全告警：{rule.name}",
        }
        actions = [action_labels[rule.action]]
        if rule.escalation.transfer_to_human:
            actions.append("转接人工服务")
        if rule.escalation.call_emergency:
            actions.append(f"呼叫紧急服务：{rule.escalation.call_emergency}")
        return actions

    def check(
        self,
        vehicle_state: VehicleState | Mapping[str, Any],
        environment: EnvironmentContext | Mapping[str, Any] | None = None,
        intent: str | Mapping[str, Any] | BaseModel | None = None,
        user_message: str = "",
    ) -> SafetyResult:
        """检查当前状态并返回最高等级及所有触发结果。"""

        context = self._build_context(vehicle_state, environment, intent, user_message)
        triggered_rules: list[SafetyRule] = []
        required_actions: list[str] = []
        forbidden_actions: list[ForbiddenAction] = []
        safety_alerts: list[SafetyAlert] = []

        for rule in self.rules:
            try:
                triggered = self.evaluate_condition(rule.trigger_condition, context)
            except UnsafeConditionError as exc:
                logger.error(f"规则 {rule.rule_id} 条件非法: {exc}")
                continue
            if not triggered:
                continue

            triggered_rules.append(rule)
            message = self._render_message(rule.message_template, context)
            for action in self._required_actions(rule):
                if action not in required_actions:
                    required_actions.append(action)

            if rule.action == "reject":
                required_by = "user"
            elif rule.action == "alert" and rule.escalation.level >= 3:
                required_by = "system"
            else:
                required_by = "agent"
            safety_alerts.append(
                SafetyAlert(
                    level=f"L{rule.escalation.level}",
                    rule_id=rule.rule_id,
                    message=message,
                    required_action=required_by,
                )
            )

            if rule.action == "reject":
                forbidden_actions.append(
                    ForbiddenAction(
                        action=rule.name,
                        rule_id=rule.rule_id,
                        reason=message,
                    )
                )

        highest_level = max(
            (rule.escalation.level for rule in triggered_rules),
            default=0,
        )
        return SafetyResult(
            safety_level=f"L{highest_level}",
            triggered_rules=triggered_rules,
            required_actions=required_actions,
            forbidden_actions=forbidden_actions,
            safety_alerts=safety_alerts,
        )


__all__ = ["SafetyEngine", "SafetyResult", "UnsafeConditionError"]
