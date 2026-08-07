"""Prompt 构建与 Few-shot 示例。"""

from prompts.few_shot_examples import (
    SCENARIO_FEW_SHOT_EXAMPLES,
    get_few_shot_examples,
)
from prompts.system_prompt import build_intent_system_prompt, build_system_prompt

__all__ = [
    "SCENARIO_FEW_SHOT_EXAMPLES",
    "build_intent_system_prompt",
    "build_system_prompt",
    "get_few_shot_examples",
]
