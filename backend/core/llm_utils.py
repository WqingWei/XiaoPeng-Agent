"""LLM 初始化、调用和容错 JSON 解析工具。"""

from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any, TypeVar

from jinja2 import Environment, FileSystemLoader, StrictUndefined
from langchain_core.messages import AIMessage, HumanMessage
from langchain_openai import ChatOpenAI
from loguru import logger
from pydantic import BaseModel

from config.settings import get_settings


TEMPLATE_DIR = Path(__file__).parents[1] / "prompts" / "templates"
StructuredModel = TypeVar("StructuredModel", bound=BaseModel)


class StructuredOutputError(ValueError):
    """模型输出在规定重试次数内始终未通过结构化校验。"""


def create_chat_model(*, lite: bool = False, temperature: float = 0.1) -> ChatOpenAI:
    """按项目配置创建 OpenAI 兼容的百炼聊天模型。"""

    settings = get_settings()
    return ChatOpenAI(
        model=settings.model_name_lite if lite else settings.model_name,
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
        temperature=temperature,
        timeout=30,
        # 结构化输出重试由 invoke_structured 统一管理，避免 SDK 与业务层叠加重试。
        max_retries=0,
    )


def template_environment() -> Environment:
    """返回启用严格变量检查的 Prompt 模板环境。"""

    return Environment(
        loader=FileSystemLoader(TEMPLATE_DIR),
        undefined=StrictUndefined,
        autoescape=False,
        trim_blocks=True,
        lstrip_blocks=True,
    )


def response_content(response: Any) -> str:
    """兼容 LangChain 字符串或多内容块响应。"""

    content = getattr(response, "content", response)
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and isinstance(item.get("text"), str):
                parts.append(item["text"])
        return "".join(parts)
    return str(content)


def parse_json_object(text: str) -> dict[str, Any]:
    """从纯 JSON、代码围栏或混合文本中提取首个 JSON 对象。"""

    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        stripped = "\n".join(lines).strip()

    try:
        parsed = json.loads(stripped)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    decoder = json.JSONDecoder()
    for index, character in enumerate(stripped):
        if character != "{":
            continue
        try:
            parsed, _ = decoder.raw_decode(stripped[index:])
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return parsed
    raise ValueError("LLM 响应中未找到有效 JSON 对象")


async def invoke_structured(
    llm: Any,
    messages: Sequence[Any],
    response_model: type[StructuredModel],
    *,
    task_name: str,
    max_retries: int = 2,
) -> StructuredModel:
    """调用模型并以 Pydantic 强校验，失败时最多自动重试 ``max_retries`` 次。"""

    if max_retries < 0:
        raise ValueError("max_retries 不能小于 0")

    base_messages = list(messages)
    attempt_messages = base_messages
    errors: list[str] = []
    for attempt in range(max_retries + 1):
        try:
            response = await llm.ainvoke(attempt_messages)
        except Exception as exc:
            error_summary = " ".join(str(exc).split())[:600] or type(exc).__name__
            raise StructuredOutputError(
                f"{task_name}模型调用失败，未进行格式重试: {error_summary}"
            ) from exc

        raw_content = response_content(response)
        try:
            return response_model.model_validate(parse_json_object(raw_content))
        except Exception as exc:
            error_summary = " ".join(str(exc).split())[:600] or type(exc).__name__
            errors.append(error_summary)
            if attempt >= max_retries:
                break

            logger.warning(
                f"{task_name}结构化输出未通过，执行第{attempt + 1}/{max_retries}次自动重试: "
                f"{error_summary}"
            )
            repair_prompt = (
                "上一次输出未通过 JSON/Pydantic 校验。请修正后重新回答，只输出一个 JSON "
                "对象，不要输出 Markdown 或解释。\n"
                f"校验错误：{error_summary}\n"
                "目标 JSON Schema：\n"
                + json.dumps(response_model.model_json_schema(), ensure_ascii=False)
            )
            attempt_messages = list(base_messages)
            if raw_content:
                attempt_messages.append(AIMessage(content=raw_content))
            attempt_messages.append(HumanMessage(content=repair_prompt))

    raise StructuredOutputError(
        f"{task_name}在{max_retries + 1}次尝试后仍未通过结构化校验: "
        + " | ".join(errors)
    )


__all__ = [
    "create_chat_model",
    "invoke_structured",
    "parse_json_object",
    "response_content",
    "template_environment",
    "StructuredOutputError",
]
