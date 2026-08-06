"""安全规则引擎

从 rules.json 加载安全规则，在 Agent 流水线中执行规则检查。
将触发结果转换为 SafetyAlert / ForbiddenAction 结构化输出。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from loguru import logger

from models.safety_rules import SafetyRule, SafetyRuleSet
from models.agent_output import ForbiddenAction, SafetyAlert

# ── 规则文件路径 ──
RULES_FILE = Path(__file__).parent / "rules.json"


# ── DotDict：支持属性访问的嵌套字典 ────────

class _DotDict:
    """将嵌套 dict 包装为支持 dot.notation 访问的对象。

    用于在 eval() 中安全地评估形如 ``driver.fatigue_level >= 2`` 的条件表达式。
    """

    def __init__(self, data: dict[str, Any]):
        for key, value in data.items():
            if isinstance(value, dict):
                setattr(self, key, _DotDict(value))
            else:
                setattr(self, key, value)

    def __repr__(self) -> str:
        return f"DotDict({self.__dict__})"

    def __getattr__(self, name: str) -> Any:
        # 访问不存在的属性时返回 None 而不是抛异常，
        # 避免规则条件因缺少字段而崩溃
        return None


# ── 上下文构建器 ────────────────────────────

def build_context(
    vehicle: dict[str, Any] | None = None,
    environment: dict[str, Any] | None = None,
    order: dict[str, Any] | None = None,
    user: dict[str, Any] | None = None,
    action: dict[str, Any] | None = None,
) -> dict[str, _DotDict]:
    """将各数据模型 dict 组装为规则评估用的上下文命名空间。

    Parameters
    ----------
    vehicle : dict
        VehicleState.model_dump() 的结果
    environment : dict
        EnvironmentContext.model_dump() 的结果
    order : dict
        OrderState.model_dump() 的结果（Robotaxi 模式）
    user : dict
        UserProfile.model_dump() 的结果
    action : dict
        当前请求的动作信息，如 {"type": "open_window", "tool": "window_control", ...}

    Returns
    -------
    dict[str, _DotDict]
        可直接传给 eval() 作为命名空间的上下文
    """
    ctx: dict[str, _DotDict] = {}

    if vehicle:
        ctx["vehicle"] = _DotDict(vehicle)
        ctx["driver"] = _DotDict(vehicle.get("driver", {}))
        ctx["cabin"] = _DotDict(vehicle.get("cabin", {}))
        ctx["battery"] = _DotDict(vehicle.get("battery", {}))
        ctx["trip"] = _DotDict(vehicle.get("trip", {}))

    if environment:
        ctx["time"] = _DotDict(environment.get("time", {}))
        ctx["weather"] = _DotDict(environment.get("weather", {}))
        ctx["traffic"] = _DotDict(environment.get("traffic", {}))

    if order:
        ctx["order"] = _DotDict(order)
        ctx["passenger"] = _DotDict(order.get("passenger", {}))

    if user:
        ctx["user"] = _DotDict(user)

    if action:
        ctx["action"] = _DotDict(action)

    # 安全事件（可由上游 Agent 注入）
    ctx.setdefault("safety_event", _DotDict({"level": 0}))

    # 媒体状态（可由 vehicle_mock 注入）
    ctx.setdefault("media", _DotDict({"volume": 30, "playing": False}))

    return ctx


# ── 安全规则引擎 ────────────────────────────

class RuleEngine:
    """安全规则引擎

    负责加载规则、评估条件、生成安全告警和被禁止动作列表。
    """

    def __init__(self, rules_file: Path | str | None = None):
        self._rules_file = Path(rules_file) if rules_file else RULES_FILE
        self._rule_set: SafetyRuleSet | None = None
        self._load_rules()

    # ── 加载 ──

    def _load_rules(self) -> None:
        """从 JSON 文件加载安全规则"""
        logger.info(f"加载安全规则: {self._rules_file}")
        with open(self._rules_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        self._rule_set = SafetyRuleSet.model_validate(data)
        logger.info(
            f"  规则已加载: {len(self._rule_set.rules)} 条 "
            f"({sum(1 for r in self._rule_set.rules if r.type == 'hard')} 硬 + "
            f"{sum(1 for r in self._rule_set.rules if r.type == 'soft')} 软)"
        )

    def reload(self) -> None:
        """重新加载规则（规则文件变更后调用）"""
        self._load_rules()

    @property
    def rules(self) -> list[SafetyRule]:
        """返回所有规则列表"""
        return self._rule_set.rules if self._rule_set else []

    # ── 条件评估 ──

    @staticmethod
    def _eval_condition(condition: str, namespace: dict[str, _DotDict]) -> bool:
        """安全地评估规则触发条件表达式

        使用受限的 eval（禁用 __builtins__）来评估条件字符串。

        Parameters
        ----------
        condition : str
            条件表达式，如 ``driver.fatigue_level >= 2``
        namespace : dict
            变量命名空间

        Returns
        -------
        bool
            条件是否成立
        """
        # 注入 JSON 风格的布尔值和 null，让条件表达式可用 true/false/null
        safe_globals = {
            "__builtins__": {},
            "true": True,
            "false": False,
            "null": None,
        }
        try:
            result = eval(condition, safe_globals, namespace)  # noqa: S307
            return bool(result)
        except Exception as e:
            logger.warning(f"规则条件评估失败: '{condition}' → {e}")
            return False

    # ── 消息渲染 ──

    @staticmethod
    def _render_message(template: str, namespace: dict[str, _DotDict]) -> str:
        """渲染消息模板，将 {变量} 替换为实际值

        使用安全的属性访问：缺失变量保留原占位符。
        """
        try:
            # 使用 format_map + 自定义 defaultdict 安全替换
            class _SafeDict(dict):
                def __missing__(self, key: str) -> str:
                    return f"{{{key}}}"

            # 从命名空间中提取所有可替换变量（展平一层）
            flat: dict[str, Any] = {}
            for ns_key, ns_val in namespace.items():
                if isinstance(ns_val, _DotDict):
                    for attr_key, attr_val in ns_val.__dict__.items():
                        flat[f"{ns_key}.{attr_key}"] = attr_val
                        flat[attr_key] = attr_val  # 也允许不带前缀的简写
                else:
                    flat[ns_key] = ns_val

            return template.format_map(_SafeDict(flat))
        except Exception:
            return template

    # ── 核心检查 ──

    def check(
        self,
        context: dict[str, _DotDict],
    ) -> tuple[list[SafetyAlert], list[ForbiddenAction]]:
        """对所有规则执行检查，返回安全告警和被禁止动作。

        Parameters
        ----------
        context : dict[str, _DotDict]
            由 ``build_context()`` 构建的上下文命名空间

        Returns
        -------
        tuple[list[SafetyAlert], list[ForbiddenAction]]
            (安全告警列表, 被禁止动作列表)
        """
        alerts: list[SafetyAlert] = []
        forbidden: list[ForbiddenAction] = []

        for rule in self.rules:
            triggered = self._eval_condition(rule.trigger_condition, context)

            if not triggered:
                continue

            # 规则触发
            message = self._render_message(rule.message_template, context)

            # 根据 action 类型分类输出
            if rule.action == "reject":
                forbidden.append(ForbiddenAction(
                    action=f"[{rule.name}] 该操作被安全规则拒绝",
                    rule_id=rule.rule_id,
                    reason=message,
                ))
                alerts.append(SafetyAlert(
                    level=f"L{rule.escalation.level}",
                    rule_id=rule.rule_id,
                    message=message,
                    required_action="user",
                ))
            elif rule.action == "force":
                alerts.append(SafetyAlert(
                    level=f"L{rule.escalation.level}",
                    rule_id=rule.rule_id,
                    message=message,
                    required_action="agent",
                ))
            elif rule.action == "alert":
                required = "system" if rule.escalation.level >= 3 else "agent"
                alerts.append(SafetyAlert(
                    level=f"L{rule.escalation.level}",
                    rule_id=rule.rule_id,
                    message=message,
                    required_action=required,
                ))
            elif rule.action == "warn":
                alerts.append(SafetyAlert(
                    level=f"L{rule.escalation.level}",
                    rule_id=rule.rule_id,
                    message=message,
                    required_action="agent",
                ))

            logger.debug(f"规则触发: {rule.rule_id} ({rule.name}) → {rule.action}")

        return alerts, forbidden

    # ── 快捷方法 ──

    def check_vehicle(
        self,
        vehicle: dict[str, Any],
        environment: dict[str, Any] | None = None,
        order: dict[str, Any] | None = None,
        user: dict[str, Any] | None = None,
        action: dict[str, Any] | None = None,
    ) -> tuple[list[SafetyAlert], list[ForbiddenAction]]:
        """快捷方法：传入数据模型 dict，自动构建上下文并检查。"""
        ctx = build_context(
            vehicle=vehicle,
            environment=environment,
            order=order,
            user=user,
            action=action,
        )
        return self.check(ctx)

    def get_hard_rules(self) -> list[SafetyRule]:
        """返回所有硬规则"""
        return [r for r in self.rules if r.type == "hard"]

    def get_soft_rules(self) -> list[SafetyRule]:
        """返回所有软规则"""
        return [r for r in self.rules if r.type == "soft"]

    def get_rule(self, rule_id: str) -> SafetyRule | None:
        """根据 ID 获取单条规则"""
        for r in self.rules:
            if r.rule_id == rule_id:
                return r
        return None
