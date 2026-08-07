"""Agent 标准输出组装与自然语言生成。"""

from __future__ import annotations

from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from loguru import logger
from pydantic import BaseModel, ConfigDict, Field, field_validator

from core.context_manager import ConversationContext
from core.intent_engine import IntentResult
from core.llm_utils import (
    create_chat_model,
    invoke_structured,
    template_environment,
)


class GeneratedResponse(BaseModel):
    """回复模型唯一允许返回的结构。"""

    model_config = ConfigDict(extra="forbid")

    user_response: str = Field(min_length=1, max_length=500)

    @field_validator("user_response", mode="before")
    @classmethod
    def normalize_response(cls, value: Any) -> str:
        if not isinstance(value, str):
            raise ValueError("user_response 必须是字符串")
        normalized = value.strip()
        if not normalized:
            raise ValueError("user_response 不能为空")
        return normalized
from core.orchestrator import OrchestrationPlan, ToolResult
from core.safety_engine import SafetyResult
from models.agent_output import (
    AgentResponse,
    FollowUp,
    Reasoning,
    ServicePlan,
    ToolExecutionResult,
)


class OutputFormatter:
    """生成自然语言并组装完整 AgentResponse。"""

    def __init__(self, llm: Any | None = None) -> None:
        self.llm = llm or create_chat_model(temperature=0.2)
        self._template = template_environment().get_template(
            "response_generation.j2"
        )

    async def format(
        self,
        intent: IntentResult,
        plan: ServicePlan,
        tool_results: list[ToolResult],
        safety_result: SafetyResult,
        context: ConversationContext,
    ) -> AgentResponse:
        prompt = self._template.render(
            intent=intent.model_dump(mode="json"),
            plan=plan.model_dump(mode="json"),
            tool_results=[result.model_dump(mode="json") for result in tool_results],
            safety=safety_result.model_dump(mode="json"),
            mode=context.vehicle.mode,
            is_driving=context.vehicle.speed > 0,
        )
        try:
            generated = await invoke_structured(
                self.llm,
                [
                    SystemMessage(
                        content="你是温暖、专业且绝不虚构执行结果的小鹏出行管家。"
                    ),
                    HumanMessage(content=prompt),
                ],
                GeneratedResponse,
                task_name="回复生成",
            )
            user_response = generated.user_response
        except Exception as exc:
            logger.warning(f"回复生成模型调用或解析失败，使用本地降级: {exc}")
            user_response = self._fallback_response(
                plan, tool_results, safety_result
            )

        orchestration = (
            plan if isinstance(plan, OrchestrationPlan) else OrchestrationPlan.model_validate(plan)
        )
        service_plan = ServicePlan(
            summary=plan.summary,
            steps=plan.steps,
            total_estimated_time_s=plan.total_estimated_time_s,
        )
        follow_up = FollowUp(
            needs_confirmation=orchestration.requires_confirmation,
            confirmation_message=orchestration.confirmation_message,
            suggested_replies=(
                ["确认执行", "暂不执行"]
                if orchestration.requires_confirmation
                else []
            ),
        )
        return AgentResponse(
            session_id=context.session_id,
            turn_id=context.turn_id + 1,
            user_response=user_response,
            service_plan=service_plan,
            tool_results=[
                ToolExecutionResult.model_validate(result.model_dump(mode="json"))
                for result in tool_results
            ],
            reasoning=Reasoning(
                detected_intent=intent.detected_intent,
                intent_type=intent.intent_type,
                confidence=intent.confidence,
                context_factors=intent.context_factors,
                tool_selection_reasons=orchestration.tool_selection_reasons,
                alternatives_considered=orchestration.alternatives_considered,
            ),
            forbidden_actions=safety_result.forbidden_actions,
            safety_alerts=safety_result.safety_alerts,
            follow_up=follow_up,
        )

    @staticmethod
    def _fallback_response(
        plan: ServicePlan,
        tool_results: list[ToolResult],
        safety_result: SafetyResult,
    ) -> str:
        orchestration = (
            plan if isinstance(plan, OrchestrationPlan) else OrchestrationPlan.model_validate(plan)
        )
        parts: list[str] = []

        if safety_result.safety_level in {"L3", "L4"}:
            parts.append("已按最高安全优先级处理，请保持冷静。")
        elif safety_result.safety_level == "L2" and safety_result.safety_alerts:
            parts.append(safety_result.safety_alerts[0].message)
        elif not tool_results and safety_result.forbidden_actions:
            parts.append(safety_result.forbidden_actions[0].reason)

        actions = {step.step_id: step.action for step in plan.steps}
        successful_messages = [
            OutputFormatter._naturalize_tool_result(
                result,
                actions.get(result.step_id, ""),
            )
            for result in tool_results
            if result.success
        ]
        successful_messages = [message for message in successful_messages if message]
        failed = [result for result in tool_results if not result.success]
        if successful_messages:
            parts.append("；".join(successful_messages[:3]) + "。")
        if failed:
            parts.append(
                f"有{len(failed)}项操作未完成，我已停止依赖步骤并保留当前安全状态。"
            )
        if orchestration.requires_confirmation and orchestration.confirmation_message:
            parts.append(orchestration.confirmation_message)
        if not parts:
            if plan.steps:
                parts.append("相关服务已处理完成。")
            else:
                parts.append("我已理解您的需求，目前没有需要立即执行的操作。")

        return "".join(parts[:3])

    @staticmethod
    def _naturalize_tool_result(result: ToolResult, action: str) -> str:
        output = result.output
        count = output.get("count", 0)
        if result.tool == "search_poi":
            target = "服务区" if "服务区" in action else "安全候选上车点"
            return f"已找到{count}个附近{target}"
        if result.tool == "search_parking":
            return f"已找到{count}个附近停车场"
        if result.tool == "search_charger":
            chargers = output.get("chargers") or []
            xpeng_count = sum(bool(item.get("is_xpeng")) for item in chargers)
            return f"已找到{count}个充电站，其中{xpeng_count}个为小鹏自营"
        if result.tool == "get_order_status":
            return "已查询当前订单状态与费用信息"
        if result.tool == "traffic_info":
            congestion = {
                "low": "畅通",
                "medium": "缓行",
                "high": "拥堵",
            }.get(str(output.get("congestion_level")), "未知")
            return f"当前路线交通状况为{congestion}"
        if result.tool == "emergency_stop":
            return "车辆已在安全位置停靠"
        if result.tool == "call_emergency":
            return f"已呼叫{output.get('service', '紧急')}紧急服务并提供车辆位置"
        if result.tool == "transfer_human":
            return "已为您接入人工客服"

        message = str(output.get("message", "")).strip("。；; ")
        replacements = {
            "driver": "驾驶位",
            "passenger": "副驾驶位",
            "rear": "后排",
            "service_area": "服务区",
            "parking_lot": "停车场",
            "auto": "自动",
            "cool": "制冷",
            "high": "拥堵",
        }
        for raw, localized in replacements.items():
            message = message.replace(raw, localized)
        return message


__all__ = ["GeneratedResponse", "OutputFormatter"]
