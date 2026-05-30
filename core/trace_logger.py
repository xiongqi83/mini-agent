"""轨迹日志 — JSONL 格式，每次 run 独立一个文件
安静模式: 只写文件，不在控制台输出。详细排查时打开 DEBUG。
"""

import json
import os
from datetime import datetime
from config.settings import TRACE_DIR, DEBUG


class TraceLogger:
    """每次 AgentRuntime.run() 创建一个新实例，记录完整执行轨迹。

    输出路径: data/traces/{session_id}_{run_id}.jsonl
    每条一行 JSON，包含: timestamp, session_id, run_id, step, event_type, detail
    """

    def __init__(self, session_id: str, run_id: str, directory: str = TRACE_DIR):
        self.session_id = session_id
        self.run_id = run_id
        self.directory = directory
        self._events: list[dict] = []

        os.makedirs(directory, exist_ok=True)
        self._filepath = os.path.join(directory, f"{session_id}_{run_id}.jsonl")
        self._file = open(self._filepath, "w", encoding="utf-8")

    def log_event(self, step: int, event_type: str, detail: dict | None = None):
        """记录一条事件，立即写入 JSONL 文件（不在控制台输出）"""
        record = {
            "timestamp": datetime.now().isoformat(),
            "session_id": self.session_id,
            "run_id": self.run_id,
            "step": step,
            "event_type": event_type,
            "detail": detail or {},
        }
        self._events.append(record)
        self._file.write(json.dumps(record, ensure_ascii=False) + "\n")
        self._file.flush()

    @property
    def filepath(self) -> str:
        return self._filepath

    def close(self):
        if self._file and not self._file.closed:
            self._file.close()

    def get_events(self) -> list[dict]:
        return list(self._events)

    def save(self, directory: str | None = None):
        self.close()
