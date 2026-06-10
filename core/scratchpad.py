"""Scratchpad — 本轮推理轨迹。每轮 run 内用列表维护，不写入 memory。"""

from dataclasses import dataclass, field


@dataclass
class TraceRecord:
    """单条轨迹记录"""
    step: int
    entry_type: str   # "action" | "observation" | "error"
    content: str


def render_scratchpad(entries: list[TraceRecord]) -> str:
    """将轨迹列表渲染为 Prompt 可用的纯文本"""
    if not entries:
        return ""

    lines = []
    for e in entries:
        label = {
            "action": "Action",
            "observation": "Observation",
            "error": "Error",
        }.get(e.entry_type, e.entry_type)
        # action/error 截断避免过长，observation 不截断（LLM 需要完整结果）
        content = e.content[:200] if e.entry_type in ("action", "error") else e.content
        lines.append(f"{label}: {content}")
    return "\n".join(lines)
