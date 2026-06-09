"""文件日志 Handler — 追加写入 JSONL"""

import json
import os
from datetime import datetime
from core.hooks.base import BaseHookHandler


class FileHandler(BaseHookHandler):

    def __init__(self, filepath: str):
        os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
        self._filepath = filepath

    def _write(self, event: str, **data):
        record = {"timestamp": datetime.now().isoformat(), "event": event, **data}
        with open(self._filepath, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")

    def on_run_start(self, user_input: str):
        self._write("run_start", user_input=user_input)

    def on_llm_call_end(self, raw_preview: str):
        self._write("llm_call", raw_preview=raw_preview)

    def on_tool_call_start(self, tool_name: str, arguments: dict):
        self._write("tool_call", tool_name=tool_name, arguments=arguments)

    def on_tool_call_end(self, tool_name: str, success: bool, summary: str):
        self._write("tool_observation", tool_name=tool_name, success=success, summary=summary)

    def on_final_answer(self, content: str):
        self._write("final_answer", content=content[:300])

    def on_parse_error(self, raw: str):
        self._write("parse_error", raw=raw[:500])

    def on_error(self, message: str):
        self._write("error", message=message)

    def on_max_steps(self, max_steps: int):
        self._write("max_steps", max_steps=max_steps)

    def on_run_end(self, outcome: str):
        self._write("run_end", outcome=outcome)
