"""小鹏 AI 出行服务管家的七步核心流水线。"""

from __future__ import annotations

import asyncio
from collections import defaultdict
from collections.abc import Awaitable, Callable
from typing import Any, Literal

from core.context_manager import ContextManager
from core.intent_engine import IntentEngine
from core.orchestrator import Orchestrator
from core.output_formatter import OutputFormatter
from core.safety_engine import SafetyEngine
from core.user_profile_manager import UserProfileManager
from models.agent_output import AgentResponse


StepCallback = Callable[[str], Awaitable[None]]


class Agent:
    """编排上下文、意图、安全、工具与输出的完整处理流程。"""

    def __init__(
        self,
        *,
        llm: Any | None = None,
        context_manager: ContextManager | None = None,
        user_profile_manager: UserProfileManager | None = None,
        intent_engine: IntentEngine | None = None,
        safety_engine: SafetyEngine | None = None,
        orchestrator: Orchestrator | None = None,
        output_formatter: OutputFormatter | None = None,
    ) -> None:
        self.context_manager = context_manager or ContextManager()
        self.user_profile_manager = user_profile_manager or UserProfileManager()
        self.intent_engine = intent_engine or IntentEngine(llm=llm)
        self.safety_engine = safety_engine or SafetyEngine()
        self.orchestrator = orchestrator or Orchestrator(llm=llm)
        self.output_formatter = output_formatter or OutputFormatter(llm=llm)
        self._session_locks: defaultdict[str, asyncio.Lock] = defaultdict(asyncio.Lock)

    async def process(
        self,
        session_id: str,
        user_message: str,
        on_step: StepCallback | None = None,
        mode: Literal["owner", "robotaxi"] | None = None,
    ) -> AgentResponse:
        """执行七步流水线，并在成功组装响应后更新会话历史。"""

        if not user_message or not user_message.strip():
            raise ValueError("user_message 不能为空")

        async with self._session_locks[session_id]:
            # Step 1: 获取上下文
            context = self.context_manager.get_context(session_id)
            if mode:
                context.vehicle.mode = mode
                context.user_profile.role = (
                    "owner" if mode == "owner" else "passenger"
                )

            # Step 2: 意图理解
            if on_step:
                await on_step("intent_analysis")
            intent = await self.intent_engine.analyze(user_message, context)

            # Step 3: 安全检查
            if on_step:
                await on_step("safety_check")
            safety = self.safety_engine.check(
                context.vehicle,
                context.environment,
                intent,
                user_message,
            )

            # Step 4: 服务编排
            if on_step:
                await on_step("orchestrating")
            plan = await self.orchestrator.plan(intent, safety, context)

            # Step 5: 工具执行
            tool_results = await self.orchestrator.execute(plan, context)

            # Step 6: 输出生成
            if on_step:
                await on_step("generating")
            response = await self.output_formatter.format(
                intent,
                plan,
                tool_results,
                safety,
                context,
            )

            # Step 7: 更新上下文与画像后返回
            self.context_manager.add_message(session_id, "user", user_message)
            self.context_manager.add_message(
                session_id, "assistant", response.user_response
            )
            self.user_profile_manager.save_profile(context.user_profile)
            response.turn_id = context.turn_id
            return response


__all__ = ["Agent", "StepCallback"]
