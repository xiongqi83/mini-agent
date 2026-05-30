"""MiniAgent — 程序入口，CLI 对话循环"""

import sys
import os

# 确保项目根目录在 sys.path 中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.settings import API_KEY, API_BASE_URL, MODEL_NAME
from core.llm_client import create_llm_client, MockLLMClient
from core.tool_registry import ToolRegistry
from core.session_manager import SessionManager
from core.runtime import Runtime


def print_banner():
    print(r"""
╔══════════════════════════════════════╗
║         MiniAgent v0.1.0             ║
║  最小可运行 Agent 框架（Mock 模式）   ║
╚══════════════════════════════════════╝
输入 /exit 退出, /save 保存会话, /help 帮助
""")


def main():
    print_banner()

    # 初始化组件（自动选择 Mock 或真实 API）
    llm = create_llm_client(api_key=API_KEY, base_url=API_BASE_URL, model=MODEL_NAME)
    tools = ToolRegistry()
    session = SessionManager()

    is_mock = isinstance(llm, MockLLMClient)

    runtime = Runtime(
        llm_client=llm,
        tool_registry=tools,
        session=session,
    )

    print(f"模式: {'MOCK (离线调试)' if is_mock else 'REAL API (DeepSeek)'}")
    print(f"模型: {MODEL_NAME}")
    print("已加载工具:", [t["function"]["name"] for t in tools.get_tool_definitions()])
    print(f"最大步数: {MAX_STEPS}")
    print(f"\n开始对话\n")

    # CLI 主循环
    while True:
        try:
            user_input = input("你: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见！")
            break

        if not user_input:
            continue

        # 处理特殊命令
        if user_input == "/exit":
            print("再见！")
            break
        elif user_input == "/save":
            session.save_to_file()
            print(f"会话已保存: data/sessions/{session.session_id}.json")
            print(f"轨迹文件目录: data/traces/")
            continue
        elif user_input == "/help":
            print("""
命令:
  /exit   - 退出程序
  /save   - 保存当前会话和轨迹
  /help   - 显示此帮助
  /state  - 查看当前 session_state
            """)
            continue
        elif user_input == "/state":
            state = session.get_state()
            print("当前 session_state:")
            for k, v in state.items():
                print(f"  {k}: {v}")
            continue

        # 执行一轮对话
        response = runtime.run(user_input)
        print(f"\nMiniAgent: {response}")


if __name__ == "__main__":
    # 导入放这里避免循环引用
    from config.settings import MAX_STEPS
    main()
