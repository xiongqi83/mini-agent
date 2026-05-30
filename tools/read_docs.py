"""本地文档读取工具 — 读取 data/docs/ 下的文档"""

import re
from pathlib import Path

# 基于当前文件位置定位项目根目录（tools/ 的上层）
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = PROJECT_ROOT / "data" / "docs"


def _extract_filename(raw: str) -> str | None:
    """从可能带有路径、自然语言描述等噪声的字符串中提取文件名。

    "agent_runtime.md"              → "agent_runtime.md"
    "读取agent_runtime.md，并总结"   → "agent_runtime.md"
    "G:\\agent\\mini_agent\\data\\docs\\agent_runtime.md" → "agent_runtime.md"
    "请读取 agent_runtime.md"       → "agent_runtime.md"
    """
    # 匹配 .md 或 .txt 文件名（ASCII 字母、数字、下划线、连字符）
    m = re.search(r'[a-zA-Z0-9_\-]+\.(?:md|txt)', raw)
    return m.group(0) if m else None


def _read_docs(arguments: dict) -> str:
    """读取 data/docs/ 下的文档"""
    raw_filename = arguments.get("filename", "").strip()
    limit = arguments.get("limit", 100)

    if not raw_filename:
        return "[read_docs 错误] 缺少 filename 参数"

    # 提取纯文件名（去除路径、自然语言等噪声）
    filename = _extract_filename(raw_filename)
    if not filename:
        return (
            f"[read_docs 错误] 无法从输入中提取有效文件名: '{raw_filename}'。"
            "支持 .md 和 .txt 文件，如 'agent_runtime.md'"
        )

    # 安全：只取 basename，禁止路径穿越
    filename = Path(filename).name

    # 构造绝对路径
    filepath = DOCS_DIR / filename
    filepath_str = str(filepath.resolve())

    if not filepath.exists():
        return (
            f"[read_docs 错误] 文件不存在: {filename}"
            f"\n  实际查找路径: {filepath_str}"
        )

    try:
        text = filepath.read_text(encoding="utf-8")
        lines = text.splitlines(keepends=True)
        total = len(lines)
        preview = "".join(lines[:limit])

        result = f"文件: {filename} (共 {total} 行)\n---\n{preview}"
        if total > limit:
            result += f"\n---\n(仅显示前 {limit} 行)"
        return result
    except Exception as e:
        return f"[read_docs 错误] 读取失败: {e}\n  文件路径: {filepath_str}"


read_docs_tool = {
    "name": "read_docs",
    "description": "读取 data/docs/ 下的本地 Markdown 或文本文件。参数 filename 只需文件名如 'agent_runtime.md'。",
    "definition": {
        "type": "function",
        "function": {
            "name": "read_docs",
            "description": "读取 data/docs/ 下的本地 Markdown 或文本文件。参数 filename 只需文件名如 'agent_runtime.md'。",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "文件名，如 'agent_runtime.md'。只需文件名，不要带路径。",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "最多读取行数，默认 100",
                    },
                },
                "required": ["filename"],
            },
        },
    },
    "handler": _read_docs,
}
