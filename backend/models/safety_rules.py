"""安全规则数据模型

定义安全规则的触发条件、动作和升级策略。
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


# ── 子模型 ──────────────────────────────────

class EscalationConfig(BaseModel):
    """安全升级配置"""
    level: int = Field(default=1, ge=1, le=4, description="安全等级 (1-4)")
    transfer_to_human: bool = Field(default=False, description="是否转人工")
    call_emergency: str | None = Field(
        default=None,
        description="紧急呼叫服务 (110/120/119 或 null)",
    )


# ── 主模型 ──────────────────────────────────

class SafetyRule(BaseModel):
    """单条安全规则"""
    rule_id: str = Field(description="规则ID，如 S01")
    name: str = Field(description="规则名称")
    type: Literal["hard", "soft"] = Field(description="硬规则(不可违反) / 软规则(可酌情)")
    trigger_condition: str = Field(description="触发条件表达式")
    action: Literal["reject", "warn", "force", "alert"] = Field(description="触发动作")
    message_template: str = Field(default="", description="告警消息模板（支持 {变量} 占位）")
    escalation: EscalationConfig = Field(default_factory=EscalationConfig)


class SafetyRuleSet(BaseModel):
    """安全规则集合"""
    rules: list[SafetyRule] = Field(default_factory=list)
