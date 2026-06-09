"""Scratchpad — 当前 run 的推理轨迹（thought / action / observation / error）"""


class Scratchpad:
    """存放本轮推理轨迹，不写入 memory"""

    def __init__(self):
        self._entries: list[dict] = []

    def add(self, step: int, entry_type: str, content: str):
        """entry_type: action / observation / error"""
        self._entries.append({
            "step": step,
            "type": entry_type,
            "content": str(content)[:500],
        })

    def render(self) -> str:
        """渲染为 Prompt 可用的文本"""
        if not self._entries:
            return "（暂无轨迹）"

        lines = []
        for e in self._entries:
            label = {"action": "Action", "observation": "Observation", "error": "Error"}.get(e["type"], e["type"])
            lines.append(f"Step {e['step']} [{label}]: {e['content'][:300]}")
        return "\n".join(lines)

    def clear(self):
        self._entries.clear()
