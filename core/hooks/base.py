"""Hook 基类 — 定义所有钩子方法，默认空实现"""


class BaseHookHandler:
    """所有 Handler 的基类。重写需要的方法即可。"""

    def on_run_start(self, user_input: str): pass
    def on_step_start(self, step: int, max_steps: int): pass
    def on_llm_call_start(self): pass
    def on_llm_call_end(self, raw_preview: str): pass
    def on_tool_call_start(self, tool_name: str, arguments: dict): pass
    def on_tool_call_end(self, tool_name: str, success: bool, summary: str): pass
    def on_final_answer(self, content: str): pass
    def on_parse_error(self, raw: str): pass
    def on_error(self, message: str): pass
    def on_max_steps(self, max_steps: int): pass
    def on_run_end(self, outcome: str): pass
