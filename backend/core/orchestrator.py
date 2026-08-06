"""服务计划生成与依赖顺序工具执行。"""

from __future__ import annotations

import asyncio
from time import perf_counter
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from loguru import logger
from pydantic import BaseModel, Field

from core.context_manager import ConversationContext
from core.intent_engine import IntentResult
from core.llm_utils import (
    create_chat_model,
    parse_json_object,
    response_content,
    template_environment,
)
from core.safety_engine import SafetyResult
from models.agent_output import (
    AlternativeConsidered,
    ServicePlan,
    ServiceStep,
    ToolSelectionReason,
)
from tools.base import ToolContext, ToolRegistry


class OrchestrationPlan(ServicePlan):
    """带推理元数据和确认信息的服务计划。"""

    tool_selection_reasons: list[ToolSelectionReason] = Field(default_factory=list)
    alternatives_considered: list[AlternativeConsidered] = Field(default_factory=list)
    requires_confirmation: bool = False
    confirmation_message: str = ""


class ToolResult(BaseModel):
    """单步工具执行结果。"""

    step_id: int
    tool: str
    success: bool
    output: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None
    skipped: bool = False
    duration_ms: float = Field(default=0, ge=0)


class Orchestrator:
    """使用 LLM 规划工具链，并在安全校验后执行。"""

    def __init__(
        self,
        llm: Any | None = None,
        tool_registry: ToolRegistry | None = None,
    ) -> None:
        self.llm = llm or create_chat_model(temperature=0)
        self.registry = tool_registry or ToolRegistry()
        self.tools = {tool.name: tool for tool in self.registry.get_all_tools()}
        self._template = template_environment().get_template("service_planning.j2")
        # 工具层当前使用全局 ToolContext；串行化可防止不同会话状态串线。
        self._execution_lock = asyncio.Lock()

    def _tool_payload(self) -> list[dict[str, Any]]:
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.args,
            }
            for tool in self.tools.values()
        ]

    async def plan(
        self,
        intent: IntentResult,
        safety_result: SafetyResult,
        context: ConversationContext,
    ) -> OrchestrationPlan:
        prompt = self._template.render(
            intent=intent.model_dump(mode="json"),
            safety=safety_result.model_dump(mode="json"),
            context=context.prompt_snapshot(),
            tools=self._tool_payload(),
        )
        try:
            response = await self.llm.ainvoke(
                [
                    SystemMessage(
                        content="你是严格遵守安全规则的出行服务工具编排器。"
                    ),
                    HumanMessage(content=prompt),
                ]
            )
            data = parse_json_object(response_content(response))
            candidate = OrchestrationPlan.model_validate(data)
            normalized = self._normalize_plan(candidate, intent, safety_result)
            if candidate.steps and not normalized.steps and not normalized.requires_confirmation:
                raise ValueError("模型计划中的步骤均无效或被安全规则拦截")
            return normalized
        except Exception as exc:
            logger.warning(f"服务规划模型调用或解析失败，使用本地降级: {exc}")
            return self._fallback_plan(intent, safety_result, context)

    def _normalize_plan(
        self,
        candidate: OrchestrationPlan,
        intent: IntentResult,
        safety_result: SafetyResult,
    ) -> OrchestrationPlan:
        valid_steps: list[ServiceStep] = []
        id_mapping: dict[int, int] = {}
        confirmed = bool(intent.entities.get("confirmed"))
        requires_confirmation = candidate.requires_confirmation
        confirmation_message = candidate.confirmation_message

        for step in candidate.steps:
            tool = self.tools.get(step.tool)
            if tool is None:
                logger.warning(f"丢弃不存在的工具: {step.tool}")
                continue

            allowed_parameters = set(tool.args)
            params = {
                key: value for key, value in step.params.items() if key in allowed_parameters
            }
            required_parameters = {
                key for key, schema in tool.args.items() if "default" not in schema
            }
            if not required_parameters.issubset(params):
                logger.warning(f"丢弃缺少必填参数的工具步骤: {step.tool}")
                continue

            if step.tool in {"modify_order", "cancel_order"} and not confirmed:
                requires_confirmation = True
                confirmation_message = confirmation_message or "该订单变更需要您确认后执行。"
                continue
            if not self._step_allowed(step.tool, params, safety_result):
                logger.warning(f"安全规则拦截工具步骤: {step.tool}")
                continue

            new_id = len(valid_steps) + 1
            dependency = id_mapping.get(step.dependency) if step.dependency else None
            id_mapping[step.step_id] = new_id
            valid_steps.append(
                ServiceStep(
                    step_id=new_id,
                    action=step.action,
                    tool=step.tool,
                    params=params,
                    dependency=dependency,
                    estimated_duration_s=step.estimated_duration_s,
                )
            )

        used_tools = {step.tool for step in valid_steps}
        reasons = [
            reason
            for reason in candidate.tool_selection_reasons
            if reason.tool in used_tools
        ]
        return OrchestrationPlan(
            summary=candidate.summary,
            steps=valid_steps,
            total_estimated_time_s=sum(
                step.estimated_duration_s for step in valid_steps
            ),
            tool_selection_reasons=reasons,
            alternatives_considered=candidate.alternatives_considered,
            requires_confirmation=requires_confirmation,
            confirmation_message=confirmation_message,
        )

    @staticmethod
    def _step_allowed(
        tool_name: str,
        params: dict[str, Any],
        safety_result: SafetyResult,
    ) -> bool:
        rule_ids = {rule.rule_id for rule in safety_result.triggered_rules}
        if "S05" in rule_ids and tool_name == "media_control" and params.get("source") == "video":
            return False
        if "S06" in rule_ids and tool_name == "window_control":
            requested_level = 100 if params.get("action") == "open" else params.get("level", 0)
            if requested_level > 30:
                return False
        if "S07" in rule_ids and tool_name in {
            "navigate_to", "create_order", "modify_order", "cancel_order"
        }:
            return False
        if "S08" in rule_ids and tool_name in {"create_order", "modify_order"}:
            return False
        return True

    def _fallback_plan(
        self,
        intent: IntentResult,
        safety_result: SafetyResult,
        context: ConversationContext,
    ) -> OrchestrationPlan:
        message = intent.original_message.lower()
        detected = intent.detected_intent
        rule_ids = {rule.rule_id for rule in safety_result.triggered_rules}
        raw_steps: list[tuple[str, str, dict[str, Any], int | None]] = []
        requires_confirmation = False
        confirmation_message = ""
        alternatives: list[AlternativeConsidered] = []

        def add(tool: str, action: str, params: dict[str, Any], dependency: int | None = None) -> None:
            raw_steps.append((tool, action, params, dependency))

        if "S04" in rule_ids or "紧急求助" in detected:
            service = "120" if any(word in message for word in ("不舒服", "身体", "发烧", "晕", "吐")) else "110"
            add("emergency_stop", "寻找安全位置并紧急停车", {})
            add("call_emergency", f"呼叫{service}紧急服务", {"service": service}, 1)
            add(
                "transfer_human",
                "转接紧急人工客服",
                {"priority": "urgent", "context": intent.original_message},
                1,
            )
        elif "S03" in rule_ids:
            add(
                "safety_alert_tool",
                "发出儿童遗留紧急告警",
                {"level": "L3", "message": "驾驶员离座但后排仍有儿童"},
            )
            add(
                "transfer_human",
                "转接人工确认儿童安全",
                {"priority": "urgent", "context": "儿童遗留告警"},
                1,
            )
        elif "S01" in rule_ids or "疲劳" in detected:
            add(
                "safety_alert_tool",
                "发出疲劳驾驶提醒",
                {"level": "L2", "message": "请尽快前往休息区停车休息"},
            )
            add(
                "search_poi",
                "搜索附近服务区",
                {"category": "service_area", "radius": 20.0, "sort_by": "distance"},
            )
            add(
                "ac_control",
                "适度降低驾驶位温度",
                {"zone": "driver", "temp": 22.0, "fan_speed": 3, "mode": "cool"},
            )
            add(
                "seat_control",
                "开启驾驶位通风",
                {"seat_id": "driver", "cooling": True},
            )
            add(
                "media_control",
                "播放轻快音乐",
                {"action": "play", "source": "music", "volume": 30, "content_id": "upbeat"},
            )
        elif "S07" in rule_ids:
            alternatives.append(
                AlternativeConsidered(
                    option="立即移动车辆",
                    reason_rejected="车辆仍在充电，安全规则禁止移动",
                )
            )
        elif "补能" in detected or "充电" in message or "续航" in message or "S10" in rule_ids:
            add(
                "search_charger",
                "搜索并比较附近充电站",
                {"location": "当前位置", "radius": 30.0, "power_type": "fast", "sort_by": "distance"},
            )
        elif "亲子" in detected or any(word in message for word in ("宝宝", "孩子", "儿童")):
            if "关闭" not in message and not context.vehicle.cabin.child_lock:
                add("child_lock_control", "启用儿童安全锁", {"action": "enable"})
            add(
                "ac_control",
                "调节后排舒适温度",
                {"zone": "rear", "temp": 25.0, "fan_speed": 2, "mode": "auto"},
            )
        elif "停车" in detected or "车位" in message:
            add(
                "search_parking",
                "搜索附近停车场",
                {"location": "目的地附近", "radius": 3.0, "filter": "available"},
            )
        elif "定位 robotaxi" in detected.lower() or "找不到车" in message or "车在哪" in message:
            add("locate_vehicle", "定位订单车辆", {"order_id": ""})
            add(
                "signal_vehicle",
                "让车辆闪灯鸣笛",
                {"order_id": "", "action": "flash_and_honk"},
                1,
            )
        elif "上车点" in detected or "上车点" in message or "施工" in message:
            add(
                "search_poi",
                "搜索附近安全上车位置",
                {"category": "parking_lot", "radius": 2.0, "sort_by": "distance"},
            )
            requires_confirmation = True
            confirmation_message = "已发现原上车点存在风险，请确认后再更新为推荐位置。"
        elif "修改行程目的地" in detected or "改去" in message or "改目的地" in message:
            add("get_order_status", "查询当前订单和费用", {"order_id": ""})
            add("traffic_info", "评估新路线交通影响", {"route_id": "current"})
            requires_confirmation = True
            destination = intent.entities.get("destination", "新目的地")
            confirmation_message = f"请确认是否将目的地修改为{destination}；确认后才会更新订单。"
        elif "空调" in detected or "空调" in message or "冷" in message or "热" in message:
            temperature = float(
                intent.entities.get(
                    "temperature", context.user_profile.preferences.ac_temp_default
                )
            )
            add(
                "ac_control",
                "调节驾驶位空调",
                {"zone": "driver", "temp": temperature, "fan_speed": 3, "mode": "auto"},
            )
        elif "媒体" in detected or any(word in message for word in ("音乐", "歌曲", "播放", "视频")):
            source = "video" if "视频" in message else "music"
            add(
                "media_control",
                f"播放{source}",
                {"action": "play", "source": source, "volume": 30, "content_id": ""},
            )
        elif "导航" in detected or "导航" in message:
            destination = intent.entities.get("destination", "用户指定目的地")
            add(
                "navigate_to",
                f"设置导航到{destination}",
                {"destination": destination, "waypoints": "", "preference": "fastest"},
            )
        else:
            add("get_vehicle_status", "查询车辆状态", {})

        steps: list[ServiceStep] = []
        for index, (tool, action, params, dependency) in enumerate(raw_steps, start=1):
            if tool in self.tools and self._step_allowed(tool, params, safety_result):
                steps.append(
                    ServiceStep(
                        step_id=len(steps) + 1,
                        action=action,
                        tool=tool,
                        params=params,
                        dependency=dependency if dependency and dependency <= len(steps) else None,
                        estimated_duration_s=3,
                    )
                )

        return OrchestrationPlan(
            summary=f"处理意图：{intent.detected_intent}",
            steps=steps,
            total_estimated_time_s=sum(step.estimated_duration_s for step in steps),
            tool_selection_reasons=[
                ToolSelectionReason(tool=step.tool, reason=step.action) for step in steps
            ],
            alternatives_considered=alternatives,
            requires_confirmation=requires_confirmation,
            confirmation_message=confirmation_message,
        )

    async def execute(
        self,
        plan: ServicePlan,
        context: ConversationContext,
    ) -> list[ToolResult]:
        """按步骤依赖顺序执行工具，并将最终状态同步回会话。"""

        results: list[ToolResult] = []
        by_step: dict[int, ToolResult] = {}

        async with self._execution_lock:
            tool_context = ToolContext()
            tool_context.init_from_scenario(
                context.vehicle,
                context.environment,
                context.order,
                context.user_profile,
            )

            for step in sorted(plan.steps, key=lambda item: item.step_id):
                if step.dependency:
                    dependency = by_step.get(step.dependency)
                    if dependency is None or not dependency.success:
                        result = ToolResult(
                            step_id=step.step_id,
                            tool=step.tool,
                            success=False,
                            skipped=True,
                            error=f"依赖步骤 {step.dependency} 未成功",
                        )
                        results.append(result)
                        by_step[step.step_id] = result
                        continue

                tool = self.tools.get(step.tool)
                if tool is None:
                    result = ToolResult(
                        step_id=step.step_id,
                        tool=step.tool,
                        success=False,
                        error="工具不存在",
                    )
                    results.append(result)
                    by_step[step.step_id] = result
                    continue

                previous = (
                    tool_context.vehicle.model_copy(deep=True),
                    tool_context.environment.model_copy(deep=True),
                    tool_context.order.model_copy(deep=True) if tool_context.order else None,
                    tool_context.user.model_copy(deep=True),
                )
                started = perf_counter()
                try:
                    raw_output = await tool.ainvoke(step.params)
                    output = raw_output if isinstance(raw_output, dict) else {"result": raw_output}
                    result = ToolResult(
                        step_id=step.step_id,
                        tool=step.tool,
                        success=bool(output.get("success", True)),
                        output=output,
                        duration_ms=(perf_counter() - started) * 1000,
                    )
                except Exception as exc:
                    # 异常工具调用回滚到该步骤之前的状态。
                    tool_context.init_from_scenario(*previous)
                    logger.exception(f"工具执行失败: {step.tool}")
                    result = ToolResult(
                        step_id=step.step_id,
                        tool=step.tool,
                        success=False,
                        error=str(exc),
                        duration_ms=(perf_counter() - started) * 1000,
                    )
                results.append(result)
                by_step[step.step_id] = result

            context.vehicle = tool_context.vehicle.model_copy(deep=True)
            context.environment = tool_context.environment.model_copy(deep=True)
            context.order = (
                tool_context.order.model_copy(deep=True) if tool_context.order else None
            )
            context.user_profile = tool_context.user.model_copy(deep=True)

        return results


__all__ = ["OrchestrationPlan", "Orchestrator", "ToolResult"]
