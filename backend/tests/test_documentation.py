"""步骤十七交付文档契约测试。"""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).parents[2]
README = ROOT / "README.md"
DELIVERY = ROOT / "DELIVERY_CHECKLIST.md"
SCENARIO_DIR = ROOT / "scenarios"
SCENARIO_FILES = {
    "fatigue_driving.md",
    "parent_child.md",
    "long_distance_charging.md",
    "commute_arrival.md",
    "robotaxi_cant_find_car.md",
    "pickup_abnormal.md",
    "change_destination.md",
    "passenger_help.md",
}
REQUIRED_SCENARIO_SECTIONS = {
    "## 场景描述",
    "## 预设初始状态",
    "## 推荐测试对话",
    "## Agent 预期行为",
    "## 安全规则触发",
}


def test_root_readme_contains_step17_required_sections() -> None:
    content = README.read_text(encoding="utf-8")

    for heading in (
        "## 三层架构",
        "## 技术栈",
        "## 本地运行（3 条命令）",
        "## 标准场景",
        "## 场景截图",
        "## 目录结构",
    ):
        assert heading in content
    assert content.count("subgraph L") == 3


def test_exactly_eight_scenario_documents_have_required_content() -> None:
    actual = {path.name for path in SCENARIO_DIR.glob("*.md") if path.name != "README.md"}

    assert actual == SCENARIO_FILES
    for filename in SCENARIO_FILES:
        content = (SCENARIO_DIR / filename).read_text(encoding="utf-8")
        assert REQUIRED_SCENARIO_SECTIONS.issubset(set(content.splitlines()))
        assert "## 验收要点" in content


def test_all_relative_markdown_links_resolve() -> None:
    markdown_files = [README, DELIVERY, *sorted(SCENARIO_DIR.glob("*.md"))]
    link_pattern = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
    missing: list[str] = []

    for markdown_file in markdown_files:
        for target in link_pattern.findall(markdown_file.read_text(encoding="utf-8")):
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            relative_target = target.split("#", 1)[0]
            if not (markdown_file.parent / relative_target).resolve().exists():
                missing.append(f"{markdown_file.relative_to(ROOT)} -> {target}")

    assert missing == []


def test_delivery_checklist_records_intentional_video_omission() -> None:
    content = DELIVERY.read_text(encoding="utf-8")

    assert "Demo 视频 | ➖ 不适用" in content
    assert "用户明确指示本次不用录制" in content
    assert "8 个场景截图 | ⏳ 待补采" in content
