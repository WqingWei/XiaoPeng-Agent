"""多会话上下文管理。"""

from __future__ import annotations

from datetime import datetime
from threading import RLock
from typing import Any, Literal

from pydantic import BaseModel, Field

from core.persistence import PersistenceBackend
from mock.scenario_presets import load_scenario
from models.environment import EnvironmentContext
from models.order import OrderState
from models.user_profile import UserProfile
from models.vehicle import VehicleState


class ConversationMessage(BaseModel):
    """一条会话消息。"""

    role: Literal["system", "user", "assistant"]
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    agent_response: dict[str, Any] | None = None


class ConversationContext(BaseModel):
    """单个会话所需的完整运行时上下文。"""

    session_id: str
    scenario_id: str | None = None
    messages: list[ConversationMessage] = Field(default_factory=list)
    vehicle: VehicleState = Field(default_factory=VehicleState)
    environment: EnvironmentContext = Field(default_factory=EnvironmentContext)
    order: OrderState | None = None
    user_profile: UserProfile = Field(default_factory=UserProfile)
    turn_id: int = 0

    def prompt_snapshot(self, history_limit: int = 10) -> dict:
        """返回适合注入 Prompt 的精简、可序列化快照。"""

        return {
            "session_id": self.session_id,
            "scenario_id": self.scenario_id,
            "turn_id": self.turn_id,
            "messages": [
                message.model_dump(mode="json")
                for message in self.messages[-history_limit:]
            ],
            "vehicle": self.vehicle.model_dump(mode="json"),
            "environment": self.environment.model_dump(mode="json"),
            "order": self.order.model_dump(mode="json") if self.order else None,
            "user_profile": self.user_profile.model_dump(mode="json"),
        }


class ContextManager:
    """以内存方式维护隔离的多会话上下文。"""

    def __init__(self, persistence: PersistenceBackend | None = None) -> None:
        self._contexts: dict[str, ConversationContext] = {}
        self._lock = RLock()
        self._persistence = persistence

    def get_context(self, session_id: str) -> ConversationContext:
        """返回已有上下文；不存在时创建默认上下文。"""

        if not session_id or not session_id.strip():
            raise ValueError("session_id 不能为空")
        with self._lock:
            if session_id not in self._contexts:
                restored = (
                    self._persistence.load_context(session_id)
                    if self._persistence
                    else None
                )
                if restored is not None:
                    self._contexts[session_id] = ConversationContext.model_validate(
                        restored
                    )
                else:
                    profile = None
                    if self._persistence:
                        stored_profile = self._persistence.load_profile("U-001")
                        if stored_profile is not None:
                            profile = UserProfile.model_validate(stored_profile)
                    self._contexts[session_id] = ConversationContext(
                        session_id=session_id,
                        user_profile=profile or UserProfile(),
                    )
                    self._save(self._contexts[session_id])
            return self._contexts[session_id]

    def add_message(
        self,
        session_id: str,
        role: Literal["system", "user", "assistant"],
        content: str,
        agent_response: dict[str, Any] | None = None,
    ) -> ConversationMessage:
        """追加消息；每条用户消息开启一个新轮次。"""

        if not content or not content.strip():
            raise ValueError("消息内容不能为空")
        with self._lock:
            context = self.get_context(session_id)
            message = ConversationMessage(
                role=role,
                content=content.strip(),
                agent_response=agent_response,
            )
            context.messages.append(message)
            if role == "user":
                context.turn_id += 1
            self._save(context)
            return message

    def update_vehicle_state(
        self,
        session_id: str,
        state: VehicleState,
    ) -> ConversationContext:
        """更新指定会话的车辆状态。"""

        with self._lock:
            context = self.get_context(session_id)
            context.vehicle = state.model_copy(deep=True)
            self._save(context)
            return context

    def update_order(
        self,
        session_id: str,
        order: OrderState | None,
    ) -> ConversationContext:
        """更新指定会话的订单状态。"""

        with self._lock:
            context = self.get_context(session_id)
            context.order = order.model_copy(deep=True) if order else None
            self._save(context)
            return context

    def reset(self, session_id: str, scenario_id: str) -> ConversationContext:
        """使用场景预设完全重置会话。"""

        vehicle, environment, order, user, system_message = load_scenario(scenario_id)
        context = ConversationContext(
            session_id=session_id,
            scenario_id=scenario_id,
            vehicle=vehicle,
            environment=environment,
            order=order,
            user_profile=user,
        )
        if system_message:
            context.messages.append(
                ConversationMessage(role="system", content=system_message)
            )
        with self._lock:
            self._contexts[session_id] = context
            self._save(context)
        return context

    def reset_to_mode(
        self,
        session_id: str,
        mode: Literal["owner", "robotaxi"],
    ) -> ConversationContext:
        """清除场景并创建指定模式的中性默认上下文。"""

        context = ConversationContext(
            session_id=session_id,
            vehicle=VehicleState(mode=mode),
            user_profile=UserProfile(
                role="owner" if mode == "owner" else "passenger"
            ),
        )
        with self._lock:
            self._contexts[session_id] = context
            self._save(context)
        return context

    def save(self, context: ConversationContext) -> ConversationContext:
        """保存当前上下文快照，并保证内存与外部存储一致。"""

        with self._lock:
            self._contexts[context.session_id] = context
            self._save(context)
            return context

    def remove(self, session_id: str) -> bool:
        """移除会话，返回此前是否存在。"""

        with self._lock:
            removed = self._contexts.pop(session_id, None) is not None
            if self._persistence:
                self._persistence.delete_context(session_id)
            return removed

    def _save(self, context: ConversationContext) -> None:
        if self._persistence:
            self._persistence.save_context(
                context.session_id,
                context.model_dump(mode="json"),
            )

    @property
    def session_count(self) -> int:
        with self._lock:
            return len(self._contexts)


__all__ = ["ContextManager", "ConversationContext", "ConversationMessage"]
