"""LLM 初始化、调用和容错 JSON 解析工具。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, StrictUndefined
from langchain_openai import ChatOpenAI

from config.settings import get_settings


TEMPLATE_DIR = Path(__file__).parents[1] / "prompts" / "templates"


def create_chat_model(*, lite: bool = False, temperature: float = 0.1) -> ChatOpenAI:
    """按项目配置创建 OpenAI 兼容的百炼聊天模型。"""

    settings = get_settings()
    return ChatOpenAI(
        model=settings.model_name_lite if lite else settings.model_name,
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
        temperature=temperature,
        timeout=30,
        max_retries=1,
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


__all__ = [
    "create_chat_model",
    "parse_json_object",
    "response_content",
    "template_environment",
]
