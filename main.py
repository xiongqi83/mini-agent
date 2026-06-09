"""Mini Agent Runtime — CLI 入口"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.settings import API_KEY, API_BASE_URL, MODEL_NAME, MAX_STEPS
from core.llm_client import LLMClient
from core.tools.registry import ToolRegistry
from core.memory.conversation import ConversationMemory
from core.runtime import Runtime
from core.hooks import HookManager, ConsoleHandler
from core.hooks.file import FileHandler
from core.memory.store import InMemoryStore


def main():
    print("Mini Agent Runtime")
    print(f"  模型: {MODEL_NAME}")
    print(f"  工具: {', '.join(ToolRegistry().list_tools())}")
    print(f"  最大步数: {MAX_STEPS}")
    print()

    llm = LLMClient(API_KEY, API_BASE_URL, MODEL_NAME)
    tools = ToolRegistry()
    memory = ConversationMemory(InMemoryStore())

    # Hook 系统：控制台输出
    hooks = HookManager()
    hooks.register(ConsoleHandler())

    runtime = Runtime(llm, tools, memory, hooks)

    while True:
        try:
            user_input = input("你: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见")
            break

        if not user_input:
            continue
        if user_input in ("/exit", "/quit"):
            print("再见")
            break

        response = runtime.run(user_input)
        print(f"\nAgent: {response}\n")


if __name__ == "__main__":
    main()
