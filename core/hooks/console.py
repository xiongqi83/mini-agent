"""控制台输出 Handler"""

from core.hooks.base import BaseHookHandler


class ConsoleHandler(BaseHookHandler):

    def on_step_start(self, step: int, max_steps: int):
        print(f"\n  [Step {step}/{max_steps}]", end=" ")

    def on_llm_call_start(self):
        print("调用 LLM...", end=" ")

    def on_tool_call_start(self, tool_name: str, arguments: dict):
        print(f"-> 调用工具: {tool_name}", end=" ")

    def on_tool_call_end(self, tool_name: str, success: bool, summary: str):
        if success:
            print("- 成功")
        else:
            print(f"- 失败: {summary[:50]}")

    def on_final_answer(self, content: str):
        print("-> 直接回答")

    def on_parse_error(self, raw: str):
        print("-> 解析失败，回填 observation")

    def on_error(self, message: str):
        print(f"-> 错误: {message[:60]}")

    def on_max_steps(self, max_steps: int):
        print(f"\n  [超时] 已达最大步数 {max_steps}")
