"""HookManager — 持有所有 Handler，每个 hook 方法广播到所有 Handler"""

from core.hooks.base import BaseHookHandler


class HookManager:
    def __init__(self):
        self._handlers: list[BaseHookHandler] = []

    def register(self, handler: BaseHookHandler):
        self._handlers.append(handler)

    # ── 广播方法 ─────────────────────────────

    def on_run_start(self, user_input: str):
        for h in self._handlers:
            try: h.on_run_start(user_input)
            except Exception: pass

    def on_step_start(self, step: int, max_steps: int):
        for h in self._handlers:
            try: h.on_step_start(step, max_steps)
            except Exception: pass

    def on_llm_call_start(self):
        for h in self._handlers:
            try: h.on_llm_call_start()
            except Exception: pass

    def on_llm_call_end(self, raw_preview: str):
        for h in self._handlers:
            try: h.on_llm_call_end(raw_preview)
            except Exception: pass

    def on_tool_call_start(self, tool_name: str, arguments: dict):
        for h in self._handlers:
            try: h.on_tool_call_start(tool_name, arguments)
            except Exception: pass

    def on_tool_call_end(self, tool_name: str, success: bool, summary: str):
        for h in self._handlers:
            try: h.on_tool_call_end(tool_name, success, summary)
            except Exception: pass

    def on_final_answer(self, content: str):
        for h in self._handlers:
            try: h.on_final_answer(content)
            except Exception: pass

    def on_parse_error(self, raw: str):
        for h in self._handlers:
            try: h.on_parse_error(raw)
            except Exception: pass

    def on_error(self, message: str):
        for h in self._handlers:
            try: h.on_error(message)
            except Exception: pass

    def on_max_steps(self, max_steps: int):
        for h in self._handlers:
            try: h.on_max_steps(max_steps)
            except Exception: pass

    def on_run_end(self, outcome: str):
        for h in self._handlers:
            try: h.on_run_end(outcome)
            except Exception: pass
