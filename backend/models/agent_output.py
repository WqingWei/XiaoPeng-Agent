"""Agent 标准输出数据模型

定义每次 Agent 响应的完整 JSON 结构，包括用户回复、服务计划、
推理过程、安全告警和后续确认。
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


# ── 服务计划子模型 ─────────────────────────

class ServiceStep(BaseModel):
    """服务计划中的单个步骤"""
    step_id: int = Field(ge=1, description="步骤序号")
    action: str = Field(description="动作描述")
    tool: str = Field(description="调用的工具 ID")
    params: dict = Field(default_factory=dict, description="工具参数")
    dependency: int | None = Field(default=None, description="依赖的步骤 step_id（null=无依赖）")
    estimated_duration_s: float = Field(default=5, ge=0, description="预估耗时 (秒)")


class ServicePlan(BaseModel):
    """服务计划"""
    summary: str = Field(default="", description="计划摘要")
    steps: list[ServiceStep] = Field(default_factory=list)
    total_estimated_time_s: float = Field(default=0, ge=0, description="总预估耗时 (秒)")


# ── 推理过程子模型 ─────────────────────────

class ToolSelectionReason(BaseModel):
    """工具选择理由"""
    tool: str = Field(description="工具 ID")
    reason: str = Field(description="选择理由")


class AlternativeConsidered(BaseModel):
    """被否决的替代方案"""
    option: str = Field(description="替代方案描述")
    reason_rejected: str = Field(description="未选择的原因")


class Reasoning(BaseModel):
    """Agent 推理过程"""
    detected_intent: str = Field(default="", description="识别到的用户意图")
    intent_type: Literal["explicit", "implicit", "urgent"] = Field(default="explicit")
    context_factors: list[str] = Field(default_factory=list, description="影响决策的上下文因素")
    tool_selection_reasons: list[ToolSelectionReason] = Field(default_factory=list)
    alternatives_considered: list[AlternativeConsidered] = Field(default_factory=list)


# ── 安全相关子模型 ─────────────────────────

class ForbiddenAction(BaseModel):
    """被禁止的动作"""
    action: str = Field(description="被禁止的动作描述")
    rule_id: str = Field(description="触发规则 ID")
    reason: str = Field(description="禁止原因")


class SafetyAlert(BaseModel):
    """安全告警"""
    level: Literal["L0", "L1", "L2", "L3", "L4"] = Field(description="安全等级")
    rule_id: str = Field(description="触发规则 ID")
    message: str = Field(description="告警信息")
    required_action: Literal["agent", "user", "system"] = Field(
        default="agent", description="处理方"
    )


# ── 后续确认子模型 ─────────────────────────

class FollowUp(BaseModel):
    """后续交互引导"""
    needs_confirmation: bool = Field(default=False, description="是否需要用户确认")
    confirmation_message: str = Field(default="", description="确认提示语")
    suggested_replies: list[str] = Field(default_factory=list, description="建议的用户回复选项")


# ── 主模型 ──────────────────────────────────

class AgentResponse(BaseModel):
    """Agent 标准输出响应

    每次 Agent 交互必须返回此结构，确保前端和其他系统
    能统一解析响应内容。
    """
    timestamp: datetime = Field(default_factory=datetime.now)
    session_id: str = Field(default="", description="会话 ID")
    turn_id: int = Field(default=0, ge=0, description="当前轮次序号")

    user_response: str = Field(
        default="你好！我是小鹏 AI 出行服务管家，请问有什么可以帮您？",
        description="面向用户的自然语言回复",
    )

    service_plan: ServicePlan = Field(default_factory=ServicePlan)
    reasoning: Reasoning = Field(default_factory=Reasoning)

    forbidden_actions: list[ForbiddenAction] = Field(default_factory=list)
    safety_alerts: list[SafetyAlert] = Field(default_factory=list)

    follow_up: FollowUp = Field(default_factory=FollowUp)
