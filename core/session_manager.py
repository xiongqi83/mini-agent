"""会话管理器 — conversation_history + session_state + JSON 持久化"""

import json
import os
from datetime import datetime
from config.settings import SESSION_DIR

MAX_RECENT_RUNS = 10


class SessionManager:
    """管理一次连续对话。

    conversation_history: 用户和 assistant 的原始对话
    session_state:        结构化 run 摘要
      - last_run:                   最近一次 run（任务或状态查询都更新）
      - last_task_run:              最近一次真正的任务型 run
      - last_successful_task_run:   最近一次成功的任务型 run
      - recent_runs:                最近 N 条摘要
    """

    def __init__(self, session_id: str | None = None):
        now = datetime.now()
        self.session_id = session_id or now.strftime("%Y%m%d_%H%M%S")
        self.created_at = now.isoformat()
        self.updated_at = now.isoformat()
        self.conversation_history: list[dict] = []
        self.step_count = 0

        self.session_state: dict = {
            "last_run": None,
            "last_task_run": None,
            "last_successful_task_run": None,
            "recent_runs": [],
        }

    def _touch(self):
        self.updated_at = datetime.now().isoformat()

    # ── 对话历史 ──────────────────────────────

    def add_message(self, role: str, content: str | None, **kwargs):
        msg = {"role": role, "content": content, **kwargs}
        self.conversation_history.append(msg)
        self._touch()

    def get_history(self, recent_n: int | None = None) -> list[dict]:
        h = self.conversation_history
        if recent_n is not None:
            return h[-recent_n:] if len(h) > recent_n else h
        return list(h)

    # ── session_state ─────────────────────────

    def get_state(self) -> dict:
        return dict(self.session_state)

    def add_run_to_state(self, run_summary: dict):
        """添加一条 run 摘要。
        run_type = "task" → 更新 last_task_run / last_successful_task_run
        run_type = "state_query" → 只更新 last_run 和 recent_runs
        """
        run_type = run_summary.get("run_type", "task")
        status = run_summary.get("status", "failed")

        # 始终更新 last_run
        self.session_state["last_run"] = run_summary

        # 只有任务型 run 才更新 last_task_run
        if run_type == "task":
            self.session_state["last_task_run"] = run_summary
            # 只有成功任务才更新 last_successful_task_run
            if status == "success":
                self.session_state["last_successful_task_run"] = run_summary

        # recent_runs 包含所有类型
        self.session_state["recent_runs"].append(run_summary)
        if len(self.session_state["recent_runs"]) > MAX_RECENT_RUNS:
            self.session_state["recent_runs"] = self.session_state["recent_runs"][-MAX_RECENT_RUNS:]

        self._touch()

    # ── 持久化 ────────────────────────────────

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "conversation_history": self.conversation_history,
            "session_state": self.session_state,
        }

    @staticmethod
    def from_dict(data: dict) -> "SessionManager":
        sm = SessionManager(data["session_id"])
        sm.created_at = data.get("created_at", sm.created_at)
        sm.updated_at = data.get("updated_at", sm.updated_at)
        sm.conversation_history = data.get("conversation_history", [])
        sm.session_state = data.get("session_state", sm.session_state)
        return sm

    def save_to_file(self, directory: str = SESSION_DIR):
        self._touch()
        os.makedirs(directory, exist_ok=True)
        path = os.path.join(directory, f"{self.session_id}.json")
        with open(path, "w", encoding="utf-8") as f:
            try:
                json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
            except (UnicodeEncodeError, UnicodeDecodeError):
                f.seek(0)
                f.truncate()
                json.dump(self.to_dict(), f, ensure_ascii=True, indent=2)


def load_session(session_id: str, directory: str = SESSION_DIR) -> SessionManager:
    path = os.path.join(directory, f"{session_id}.json")
    if os.path.exists(path):
        sm = SessionManager(session_id)
        sm.load_from_file(path)
        return sm
    return SessionManager(session_id)


def save_session(session: SessionManager, directory: str = SESSION_DIR):
    session.save_to_file(directory)
