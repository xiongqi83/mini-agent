"""本地文档读取工具"""

import re
from pathlib import Path
from core.tools.base import BaseTool

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DOCS_DIR = PROJECT_ROOT / "data" / "docs"


class ReadDocsTool(BaseTool):
    def __init__(self):
        super().__init__()
        self.name = "read_docs"
        self.description = "读取 data/docs/ 下的本地文档"
        self.parameters = {
            "filename": {
                "type": "string",
                "description": "文件名，如 'agent_runtime.md'",
                "required": True,
            },
            "limit": {
                "type": "integer",
                "description": "最多读取行数，默认 100",
                "required": False,
            },
        }

    def run(self, arguments: dict) -> str:
        raw = arguments.get("filename", "").strip()
        limit = arguments.get("limit", 100)

        if not raw:
            raise ValueError("缺少 filename 参数")

        m = re.search(r'[a-zA-Z0-9_\-]+\.(?:md|txt)', raw)
        if not m:
            raise ValueError(f"无法提取文件名: '{raw}'")

        filename = Path(m.group(0)).name
        filepath = DOCS_DIR / filename

        if not filepath.exists():
            raise FileNotFoundError(f"文件不存在: {filename}\n  实际路径: {filepath}")

        text = filepath.read_text(encoding="utf-8")
        lines = text.splitlines(keepends=True)
        total = len(lines)
        preview = "".join(lines[:limit])
        result = f"文件: {filename} (共 {total} 行)\n---\n{preview}"
        if total > limit:
            result += f"\n---\n(仅显示前 {limit} 行)"
        return result
