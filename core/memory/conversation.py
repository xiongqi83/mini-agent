"""Memory 第二层：对话记忆 — 提取 + 渲染 + 清空"""

from core.memory.store import MemoryStore, InMemoryStore


class ConversationMemory:
    """对话记忆层。兼容 runtime 原有接口。"""

    def __init__(self, store: MemoryStore | None = None):
        self._store = store or InMemoryStore()

    # ── 提取并存入 ────────────────────────────

    def add_message(self, role: str, content: str):
        """提取单条对话并存入 memory"""
        self._store.add_batch([{"role": role, "content": content}])

    # ── 渲染为 Prompt 文本 ────────────────────

    def render(self, max_messages: int = 10) -> str:
        """将 memory 渲染成纯文本，用于注入 Prompt"""
        msgs = self._store.get_all()
        recent = msgs[-max_messages:] if len(msgs) > max_messages else msgs
        if not recent:
            return "（暂无对话历史）"

        lines = []
        for m in recent:
            label = "用户" if m["role"] == "user" else "助手" if m["role"] == "assistant" else m["role"]
            content = m.get("content", "")[:200]
            lines.append(f"{label}: {content}")
        return "\n".join(lines)

    # ── 清空 ──────────────────────────────────

    def clear(self):
        self._store.clear()

    # ── runtime 兼容接口 ──────────────────────

    def get_history(self, n: int = 20) -> list[dict]:
        """返回最近 N 条消息（runtime 兼容）"""
        msgs = self._store.get_all()
        return msgs[-n:] if len(msgs) > n else list(msgs)

    def get_messages(self) -> list[dict]:
        """返回所有消息"""
        return self._store.get_all()
