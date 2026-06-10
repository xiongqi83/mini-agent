"""Agent Runtime — ReAct 循环"""

import json
import re
from config.settings import MAX_STEPS
from core.llm_client import LLMClient
from core.tools.registry import ToolRegistry
from core.memory.conversation import ConversationMemory
from core.scratchpad import TraceRecord, render_scratchpad
from core.system_prompt import build_system_prompt, build_messages
from core.hooks.manager import HookManager

VALID_TYPES = {"final_answer", "tool_call"}


class Runtime:
    """ReAct Agent 运行时"""

    def __init__(
        self,
        llm_client: LLMClient,
        tool_registry: ToolRegistry,
        memory: ConversationMemory,
        hooks: HookManager | None = None,
    ):
        self.llm = llm_client
        self.tools = tool_registry
        self.memory = memory
        self.hooks = hooks or HookManager()

    # ── 主入口 ────────────────────────────────

    def run(self, user_input: str) -> str:
        self.hooks.on_run_start(user_input)

        # 用户输入写入 memory（只保存对话）
        self.memory.add_message("user", user_input)

        # 本轮推理轨迹（列表，生命周期仅限当前 run）
        scratchpad: list[TraceRecord] = []

        # 构建 system prompt（工具 schema 不变，只构建一次）
        system = build_system_prompt(tools_schema=self.tools.render())

        for step in range(1, MAX_STEPS + 1):
            self.hooks.on_step_start(step, MAX_STEPS)

            # 组装 messages: system + history + user_input + Thought(scratchpad)
            messages = build_messages(
                system_prompt=system,
                user_input=user_input,
                chat_history=self.memory.get_history(),
                scratchpad_text=render_scratchpad(scratchpad),
            )

            # ── 调用 LLM ──
            self.hooks.on_llm_call_start()
            raw = self.llm.chat(messages)
            self.hooks.on_llm_call_end(raw[:300])

            # ── 解析 ──
            parsed = self._parse_response(raw)
            if parsed is None:
                scratchpad.append(TraceRecord(step, "error", f"JSON 解析失败，请重新输出 JSON。原文: {raw[:200]}"))
                self.hooks.on_parse_error(raw[:300])
                continue

            rtype = parsed.get("type", "")

            # ── final_answer ──
            if rtype == "final_answer":
                content = parsed.get("content", "")
                self.memory.add_message("assistant", content)
                self.hooks.on_final_answer(content[:200])
                self.hooks.on_run_end("success")
                return content

            # ── tool_call ──
            if rtype == "tool_call":
                tool_name = parsed.get("tool_name", "")
                tool_args = parsed.get("arguments", {})
                if isinstance(tool_args, str):
                    try:
                        tool_args = json.loads(tool_args)
                    except json.JSONDecodeError:
                        scratchpad.append(TraceRecord(step, "error", f"tool_call 参数 JSON 解析失败: {tool_args}"))
                        continue

                self.hooks.on_tool_call_start(tool_name, tool_args)

                # 参数校验
                tool = self.tools.get(tool_name)
                if tool is None:
                    obs = f"[错误] 工具 '{tool_name}' 不存在。可用: {', '.join(self.tools.list_tools())}"
                    scratchpad.append(TraceRecord(step, "action", f"{tool_name}({json.dumps(tool_args, ensure_ascii=False)})"))
                    scratchpad.append(TraceRecord(step, "error", obs))
                    self.hooks.on_tool_call_end(tool_name, False, obs[:80])
                    continue

                missing = [p for p in tool.get_required_params()
                           if p not in tool_args or not tool_args[p]]
                if missing:
                    obs = f"[错误] 工具 '{tool_name}' 缺少必填参数: {', '.join(missing)}"
                    scratchpad.append(TraceRecord(step, "action", f"{tool_name}({json.dumps(tool_args, ensure_ascii=False)})"))
                    scratchpad.append(TraceRecord(step, "error", obs))
                    self.hooks.on_tool_call_end(tool_name, False, obs[:80])
                    continue

                # 执行工具，拿到原始字符串 observation
                observation = self.tools.execute(tool_name, tool_args)
                scratchpad.append(TraceRecord(step, "action", f"{tool_name}({json.dumps(tool_args, ensure_ascii=False)})"))
                scratchpad.append(TraceRecord(step, "observation", observation))

                success = not observation.startswith("[")
                self.hooks.on_tool_call_end(tool_name, success, observation[:80])
                continue

            # ── 未知类型 ──
            scratchpad.append(TraceRecord(step, "error", f"未知响应类型: {rtype}"))
            self.hooks.on_error(f"未知类型: {rtype}")
            continue

        # max_steps
        self.hooks.on_max_steps(MAX_STEPS)
        fallback = f"抱歉，处理超时（{MAX_STEPS}步）。请尝试简化问题。"
        self.memory.add_message("assistant", fallback)
        self.hooks.on_run_end("max_steps")
        return fallback

    # ── JSON 解析 ─────────────────────────────

    def _parse_response(self, raw: str) -> dict | None:
        if not raw or not raw.strip():
            return None

        candidates = [raw.strip()]

        m = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', raw, re.DOTALL)
        if m:
            candidates.append(m.group(1).strip())

        for bm in re.finditer(r'\{', raw):
            depth, end = 0, bm.start()
            for i, ch in enumerate(raw[bm.start():], bm.start()):
                if ch == '{':
                    depth += 1
                elif ch == '}':
                    depth -= 1
                    if depth == 0:
                        end = i + 1
                        break
            if end > bm.start():
                candidates.append(raw[bm.start():end])

        for c in candidates:
            if not c:
                continue
            try:
                obj = json.loads(c)
            except json.JSONDecodeError:
                continue
            if "type" not in obj or obj["type"] not in VALID_TYPES:
                continue
            return obj

        return None
