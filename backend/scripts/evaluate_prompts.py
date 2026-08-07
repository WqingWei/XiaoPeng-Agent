"""运行第十五步的 8 场景、16 输入 Prompt 质量评测。"""

from __future__ import annotations

import argparse
import asyncio
import json
import re
from pathlib import Path
from typing import Any

from loguru import logger

from core.agent import Agent
from prompts.few_shot_examples import PROMPT_EVALUATION_CASES


class OfflineLLM:
    """让 Agent 使用生产降级链，评测不访问外部模型。"""

    async def ainvoke(self, messages: Any) -> Any:
        raise RuntimeError("Prompt 离线评测禁用外部 LLM")


def _highest_safety_level(response: Any) -> str:
    level = max(
        (int(alert.level.removeprefix("L")) for alert in response.safety_alerts),
        default=0,
    )
    return f"L{level}"


def _quality_checks(response: Any, case: dict[str, Any]) -> dict[str, bool]:
    actual_tools = {step.tool for step in response.service_plan.steps}
    expected_tools = set(case["tools"])
    expected_confirmation = bool(case.get("confirm", False))
    response_text = response.user_response.strip()
    machine_tokens = ("driver", "rear", "service_area", "parking_lot")
    return {
        "intent_type": response.reasoning.intent_type == case["type"],
        "required_tools": expected_tools.issubset(actual_tools),
        "safety_level": _highest_safety_level(response) == case.get("level", "L0"),
        "confirmation": response.follow_up.needs_confirmation == expected_confirmation,
        "natural_response": bool(response_text)
        and not response_text.startswith(("{", "```"))
        and not any(token in response_text for token in machine_tokens)
        and re.search(r"[。！？]。", response_text) is None,
    }


async def evaluate(
    mode: str,
    scenario_filter: str | None = None,
    case_filter: int | None = None,
) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    for scenario_id, cases in PROMPT_EVALUATION_CASES.items():
        if scenario_filter and scenario_id != scenario_filter:
            continue
        for case_index, case in enumerate(cases, start=1):
            if case_filter and case_index != case_filter:
                continue
            agent = Agent(llm=OfflineLLM()) if mode == "offline" else Agent()
            session_id = f"step15-{mode}-{scenario_id}-{case_index}"
            agent.context_manager.reset(session_id, scenario_id)
            response = await agent.process(session_id, case["user"])
            checks = _quality_checks(response, case)
            results.append(
                {
                    "scenario": scenario_id,
                    "case": case_index,
                    "input": case["user"],
                    "detected_intent": response.reasoning.detected_intent,
                    "intent_type": response.reasoning.intent_type,
                    "confidence": response.reasoning.confidence,
                    "tools": [step.tool for step in response.service_plan.steps],
                    "safety_level": _highest_safety_level(response),
                    "needs_confirmation": response.follow_up.needs_confirmation,
                    "user_response": response.user_response,
                    "checks": checks,
                    "passed": all(checks.values()),
                }
            )

    passed = sum(item["passed"] for item in results)
    return {
        "mode": mode,
        "summary": {
            "scenarios": len({item["scenario"] for item in results}),
            "cases": len(results),
            "passed": passed,
            "failed": len(results) - passed,
        },
        "results": results,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("live", "offline"), default="offline")
    parser.add_argument("--scenario", choices=tuple(PROMPT_EVALUATION_CASES))
    parser.add_argument("--case", type=int, choices=(1, 2))
    parser.add_argument("--output", type=Path)
    parser.add_argument("--summary-only", action="store_true")
    parser.add_argument("--strict", action="store_true")
    return parser.parse_args()


async def main() -> int:
    args = parse_args()
    if args.summary_only:
        logger.remove()
    report = await evaluate(args.mode, args.scenario, args.case)
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    if args.summary_only:
        print(json.dumps({"mode": report["mode"], "summary": report["summary"]}, ensure_ascii=False))
    else:
        print(rendered)
    return 1 if args.strict and report["summary"]["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
