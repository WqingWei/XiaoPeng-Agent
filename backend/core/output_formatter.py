"""Agent 标准输出组装与自然语言生成。"""

from __future__ import annotations

from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from loguru import logger

from core.context_manager import ConversationContext
from core.intent_engine import IntentResult
from core.llm_utils import (
    create_chat_model,
    parse_json_object,
    response_content,
    template_environment,
)
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
            response = await self.llm.ainvoke(
                [
                    SystemMessage(
                        content="你是温暖、专业且绝不虚构执行结果的小鹏出行管家。"
                    ),
                    HumanMessage(content=prompt),
                ]
            )
            data = parse_json_object(response_content(response))
            user_response = str(data["user_response"]).strip()
            if not user_response:
                raise ValueError("user_response 为空")
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
        elif safety_result.safety_alerts:
            parts.append(safety_result.safety_alerts[0].message)

        successful_messages = [
            str(result.output.get("message"))
            for result in tool_results
            if result.success and result.output.get("message")
        ]
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


__all__ = ["OutputFormatter"]
