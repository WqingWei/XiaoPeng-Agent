"""基于 LLM 的意图理解引擎，包含可用的本地降级策略。"""

from __future__ import annotations

import re
from typing import Any, Literal

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from loguru import logger
from pydantic import BaseModel, Field

from core.context_manager import ConversationContext
from core.llm_utils import (
    create_chat_model,
    parse_json_object,
    response_content,
    template_environment,
)
from prompts.few_shot_examples import get_few_shot_examples
from prompts.system_prompt import build_system_prompt


class IntentResult(BaseModel):
    """结构化意图分析结果。"""

    detected_intent: str
    intent_type: Literal["explicit", "implicit", "urgent"] = "explicit"
    confidence: float = Field(default=0.5, ge=0, le=1)
    context_factors: list[str] = Field(default_factory=list)
    original_message: str = ""
    entities: dict[str, Any] = Field(default_factory=dict)


class IntentEngine:
    """渲染意图模板、调用模型并校验结构化结果。"""

    def __init__(self, llm: Any | None = None) -> None:
        self.llm = llm or create_chat_model(lite=True, temperature=0)
        self._template = template_environment().get_template("intent_analysis.j2")

    async def analyze(
        self,
        user_message: str,
        context: ConversationContext,
    ) -> IntentResult:
        if not user_message or not user_message.strip():
            raise ValueError("user_message 不能为空")

        prompt = self._template.render(
            user_message=user_message,
            mode=context.vehicle.mode,
            vehicle=context.vehicle.model_dump(mode="json"),
            environment=context.environment.model_dump(mode="json"),
            order=context.order.model_dump(mode="json") if context.order else None,
            user_profile=context.user_profile.model_dump(mode="json"),
            conversation_history=[
                message.model_dump(mode="json") for message in context.messages[-10:]
            ],
        )
        system_prompt = build_system_prompt(
            context.vehicle.mode,
            context.vehicle,
            context.environment,
            context.order,
            context.user_profile,
        )
        messages: list[Any] = [SystemMessage(content=system_prompt)]
        if context.scenario_id:
            for example in get_few_shot_examples(context.scenario_id):
                message_class = HumanMessage if example["role"] == "user" else AIMessage
                messages.append(message_class(content=example["content"]))
        messages.append(HumanMessage(content=prompt))

        try:
            response = await self.llm.ainvoke(messages)
            data = parse_json_object(response_content(response))
            result = IntentResult.model_validate(data)
            result.original_message = user_message.strip()
            result.entities = {**self._extract_entities(user_message), **result.entities}
            return result
        except Exception as exc:
            logger.warning(f"意图模型调用或解析失败，使用本地降级: {exc}")
            return self._fallback_analysis(user_message, context)

    @staticmethod
    def _extract_entities(user_message: str) -> dict[str, Any]:
        entities: dict[str, Any] = {}
        temperature = re.search(r"(-?\d+(?:\.\d+)?)\s*(?:度|°c)", user_message, re.I)
        if temperature:
            entities["temperature"] = float(temperature.group(1))

        destination = re.search(
            r"(?:改去|导航到|带我去|去)([^，。！？!?]{2,30})",
            user_message,
        )
        if destination:
            entities["destination"] = destination.group(1).strip()

        normalized = user_message.strip().lower()
        entities["confirmed"] = normalized in {
            "确认", "确认执行", "好的", "好", "yes", "confirm",
        }
        return entities

    def _fallback_analysis(
        self,
        user_message: str,
        context: ConversationContext,
    ) -> IntentResult:
        message = user_message.strip().lower()
        urgent_words = ("救命", "求助", "身体不适", "不舒服", "发烧", "事故", "sos", "help")

        intent_type: Literal["explicit", "implicit", "urgent"] = "explicit"
        if any(word in message for word in urgent_words):
            detected = "乘客紧急求助" if context.vehicle.mode == "robotaxi" else "紧急安全求助"
            intent_type = "urgent"
        elif any(word in message for word in ("困", "疲劳", "想睡")):
            detected = "疲劳驾驶干预"
            intent_type = "implicit"
        elif any(word in message for word in ("宝宝", "孩子", "儿童")):
            detected = "亲子出行安全与舒适服务"
            intent_type = "implicit"
        elif any(word in message for word in ("充电", "续航", "补能")):
            detected = "长途补能规划"
        elif any(word in message for word in ("停车", "车位", "快到公司")):
            detected = "通勤到达停车准备"
            intent_type = "implicit" if "快到" in message else "explicit"
        elif any(word in message for word in ("找不到车", "车在哪", "还没来")):
            detected = "定位 Robotaxi 车辆"
        elif any(word in message for word in ("上车点", "施工", "禁停", "高速路边")):
            detected = "处理异常上车点"
        elif any(word in message for word in ("改去", "改目的地", "不去那里")):
            detected = "修改行程目的地"
        elif any(word in message for word in ("空调", "冷", "热")):
            detected = "调节座舱空调"
        elif any(word in message for word in ("音乐", "歌曲", "播放", "视频")):
            detected = "控制车载媒体"
        elif any(word in message for word in ("导航", "带我去")):
            detected = "设置导航"
        else:
            detected = "查询车辆与出行状态"

        factors = [
            f"当前模式={context.vehicle.mode}",
            f"车速={context.vehicle.speed}km/h",
            f"电量={context.vehicle.battery.level}%",
            f"疲劳等级={context.vehicle.driver.fatigue_level}",
        ]
        if context.order:
            factors.append(f"订单状态={context.order.status}")
        if context.messages:
            factors.append(f"参考最近{min(len(context.messages), 10)}条对话")

        return IntentResult(
            detected_intent=detected,
            intent_type=intent_type,
            confidence=0.72,
            context_factors=factors,
            original_message=user_message.strip(),
            entities=self._extract_entities(user_message),
        )


__all__ = ["IntentEngine", "IntentResult"]
