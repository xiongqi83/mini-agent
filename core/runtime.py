"""Agent 运行时 — 核心主循环 + 状态查询捷径 + 去重
每次 run() 生成独立 run_id，全程记录 trace，结束时更新 session_state 并保存。
"""

import json
import re
import os
from datetime import datetime

from config.settings import MAX_STEPS, DEBUG
from core.llm_client import MockLLMClient, RealLLMClient
from core.tool_registry import ToolRegistry
from core.session_manager import SessionManager
from core.trace_logger import TraceLogger
from core.prompt_builder import (
    build_messages,
    build_observation_message,
    update_system_state_in_prompt,
)

VALID_RESPONSE_TYPES = {"final_answer", "tool_call"}

# ── 状态查询关键词 ──────────────────────────
# 命中以下模式 → 直接由 runtime 回答，不调 LLM

STATE_QUERY_PATTERNS = [
    r'最近.*?(做了|干了).*?什么',
    r'刚才.{0,6}(任务|执行|运行)',
    r'上一个?任务',
    r'上一次.{0,8}(成功|失败)',
    r'最近.{0,6}(任务|记录|历史)',
    r'刚才做了',
    r'执行历史',
    r'做过.*(哪些|什么)',
]


def is_session_state_query(user_input: str) -> bool:
    """判断用户输入是否为 session_state 查询"""
    text = user_input.strip().lower()
    for pat in STATE_QUERY_PATTERNS:
        if re.search(pat, text):
            return True
    return False


# ── 工具签名（去重用）──────────────────────

def _make_tool_signature(tool_name: str, arguments: dict) -> str:
    try:
        args_str = json.dumps(arguments, sort_keys=True, ensure_ascii=False)
    except Exception:
        args_str = str(arguments)
    return f"{tool_name}:{args_str}"


# ── 公共 JSON 解析函数 ─────────────────────

def parse_llm_response(raw: str) -> dict | None:
    """从 LLM 原始输出中提取并验证 JSON。

    支持: 直接 JSON / ```json``` 代码块 / 自然语言中提取第一个 JSON
    验证: 必须有 type 字段，且为 final_answer 或 tool_call
    """
    if not raw or not raw.strip():
        return None

    candidates: list[str] = []

    # 1. 直接解析
    candidates.append(raw.strip())

    # 2. ```json ... ``` 或 ``` ... ```
    m = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', raw, re.DOTALL)
    if m:
        candidates.append(m.group(1).strip())

    # 3. 花括号平衡提取
    for bm in re.finditer(r'\{', raw):
        depth = 0
        end = bm.start()
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

    for candidate in candidates:
        if not candidate:
            continue
        try:
            obj = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if "type" not in obj:
            continue
        if obj["type"] not in VALID_RESPONSE_TYPES:
            continue
        return obj

    return None


# ── 状态查询回答生成 ─────────────────────────

def _generate_state_query_answer(state: dict, user_input: str) -> str:
    """根据 session_state 生成自然语言回答"""
    text = user_input.strip().lower()
    last_task = state.get("last_task_run")
    last_ok = state.get("last_successful_task_run")
    last_run = state.get("last_run")
    recent = state.get("recent_runs", [])

    # 最近做了什么
    if "最近" in text and ("做了" in text or "什么" in text or "记录" in text or "历史" in text):
        if not recent:
            return "目前还没有执行记录。"
        lines = ["最近几轮执行记录："]
        for i, r in enumerate(reversed(recent), 1):
            status_icon = {"success": "✓", "failed": "✗", "partial": "~"}.get(r.get("status", ""), "?")
            goal = r.get("goal", "?")[:80]
            tools = r.get("tools_called", [])
            tool_str = f" (工具: {', '.join(tools)})" if tools else ""
            err = f" [错误: {r.get('error', '')[:40]}]" if r.get("error") else ""
            lines.append(f"  {i}. [{status_icon}] {goal}{tool_str}{err}")
        return "\n".join(lines)

    # 刚才那个任务
    if "刚才" in text:
        target = last_task or last_run
        if not target:
            return "目前还没有执行过任务。"
        status = target.get("status", "?")
        tools = target.get("tools_called", [])
        goal = target.get("goal", "")[:100]
        err = target.get("error", "")
        parts = [f"刚才的任务是：{goal}"]
        parts.append(f"执行状态：{status}")
        if tools:
            parts.append(f"调用的工具：{', '.join(tools)}")
        if status == "failed" and err:
            parts.append(f"失败原因：{err}")
        elif status == "success":
            parts.append("任务执行成功。")
        return "\n".join(parts)

    # 上一次成功
    if "上一次" in text and "成功" in text:
        if not last_ok:
            return "目前还没有成功执行过任务。"
        return f"上一次成功的任务是：{last_ok.get('goal', '')[:100]}\n状态：成功\n工具：{', '.join(last_ok.get('tools_called', []))}"

    # 上一次失败
    if "上一次" in text and "失败" in text:
        for r in reversed(recent):
            if r.get("status") == "failed" and r.get("run_type", "task") == "task":
                return f"上一次失败的任务是：{r.get('goal', '')[:100]}\n错误：{r.get('error', '')[:200]}"
        return "目前没有失败的任务记录。"

    # 上一个任务
    if "上一个" in text and "任务" in text:
        if not last_task:
            return "目前还没有执行过任务。"
        return f"上一个任务是：{last_task.get('goal', '')[:100]}\n状态：{last_task.get('status', '')}\n工具：{', '.join(last_task.get('tools_called', []))}"

    # 兜底
    if last_run:
        return f"最近一次执行：{last_run.get('goal', '')[:100]} (状态: {last_run.get('status', '')})"
    return "目前还没有执行记录。"


# ── Runtime ────────────────────────────────

class Runtime:
    """Agent 核心运行时"""

    def __init__(
        self,
        llm_client: "MockLLMClient | RealLLMClient",
        tool_registry: ToolRegistry,
        session: SessionManager,
    ):
        self.llm = llm_client
        self.tools = tool_registry
        self.session = session

    # ── 主入口 ────────────────────────────────

    def run(self, user_input: str) -> str:
        run_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:20]
        tracer = TraceLogger(self.session.session_id, run_id)
        tracer.log_event(0, "run_start", {"user_input": user_input})

        # ── 状态查询捷径 ──
        if is_session_state_query(user_input):
            return self._handle_state_query(user_input, run_id, tracer)

        # ── 正常流程 ──
        tools_called: list[str] = []
        last_observation: dict | None = None
        run_error: str | None = None
        had_tool_error: bool = False
        seen_signatures: set = set()  # 去重

        self.session.add_message("user", user_input)

        messages = build_messages(
            tools_schema=self.tools.get_tool_definitions(),
            session_state=self.session.get_state(),
            history=self.session.get_history()[:-1],
            user_input=user_input,
        )

        for step in range(1, MAX_STEPS + 1):
            self.session.step_count = step
            print(f"\n  [Step {step}/{MAX_STEPS}]", end=" ")

            tracer.log_event(step, "llm_request", {
                "messages_count": len(messages),
                "messages_tail": [
                    {"role": m.get("role"), "content": str(m.get("content", ""))[:80]}
                    for m in messages[-3:]
                ],
            })
            print("调用 LLM...", end=" ")
            raw_response = self.llm.chat(messages)

            tracer.log_event(step, "llm_response", {"raw_response": raw_response[:500]})

            parsed = parse_llm_response(raw_response)
            if parsed is None:
                run_error = "JSON 解析失败"
                tracer.log_event(step, "error", {
                    "message": run_error,
                    "raw_response_full": raw_response[:1000],
                })
                return self._finish(
                    step=step, run_id=run_id, user_input=user_input, run_type="task",
                    outcome="failed", error=run_error,
                    tools_called=tools_called, last_observation=last_observation,
                    tracer=tracer,
                    fallback="抱歉，模型返回了无法识别的格式，请换一种方式提问。",
                )

            response_type = parsed.get("type", "")

            if response_type == "final_answer":
                return self._handle_final_answer(
                    step, run_id, user_input, parsed,
                    tools_called, last_observation, run_error, had_tool_error, tracer,
                )

            if response_type == "tool_call":
                result = self._handle_tool_call(step, parsed, messages, tracer, seen_signatures)
                if isinstance(result, str):
                    run_error = result
                    tracer.log_event(step, "run_end", {"outcome": "tool_error"})
                    tracer.close()
                    self._record_run(run_id, user_input, "task", "failed", tools_called, last_observation, run_error)
                    self.session.save_to_file()
                    return f"工具调用失败: {result}"
                obs = result
                # obs 为 None 表示被去重拦截（duplicate_tool_call_blocked）
                if obs is None:
                    continue
                tools_called.append(parsed.get("tool_name", ""))
                last_observation = obs
                if not obs.get("success"):
                    had_tool_error = True
                messages.append({"role": "assistant", "content": json.dumps(parsed, ensure_ascii=False)})
                messages.append(build_observation_message(parsed.get("tool_name", ""), obs))
                update_system_state_in_prompt(messages, self.session.get_state(), self.tools.get_tool_definitions())
                continue

            run_error = f"未知响应类型: {response_type}"
            tracer.log_event(step, "error", {"message": run_error, "parsed": parsed})
            return self._finish(
                step=step, run_id=run_id, user_input=user_input, run_type="task",
                outcome="failed", error=run_error,
                tools_called=tools_called, last_observation=last_observation,
                tracer=tracer,
                fallback="抱歉，模型返回了无法识别的响应类型。",
            )

        # max_steps
        tracer.log_event(MAX_STEPS + 1, "max_steps_reached", {"max_steps": MAX_STEPS})
        return self._finish(
            step=MAX_STEPS + 1, run_id=run_id, user_input=user_input, run_type="task",
            outcome="partial", error="达到最大步数",
            tools_called=tools_called, last_observation=last_observation,
            tracer=tracer,
            fallback=f"抱歉，处理超时（{MAX_STEPS}步）。请尝试简化问题。",
        )

    # ── 状态查询处理 ──────────────────────────

    def _handle_state_query(self, user_input: str, run_id: str, tracer: TraceLogger) -> str:
        """不调 LLM，直接从 session_state 生成回答"""
        answer = _generate_state_query_answer(self.session.get_state(), user_input)
        self.session.add_message("user", user_input)
        self.session.add_message("assistant", answer)

        tracer.log_event(1, "session_state_answer", {"user_input": user_input, "answer": answer[:300]})
        tracer.log_event(1, "run_end", {"outcome": "success", "total_steps": 0})

        self._record_run(
            run_id=run_id, goal=user_input, run_type="state_query",
            status="success", tools_called=[], result_summary=answer[:200], error=None,
        )
        tracer.log_event(1, "session_state_update", {"state": self.session.get_state()})
        tracer.close()
        self.session.save_to_file()

        print("-> 状态查询 (直接回答)")
        return answer

    # ── 处理器 ────────────────────────────────

    def _handle_final_answer(self, step, run_id, user_input, parsed, tools_called, last_observation, run_error, had_tool_error, tracer):
        content = parsed.get("content", "")
        self.session.add_message("assistant", content)
        tracer.log_event(step, "final_answer", {"content": content[:300]})
        outcome = "failed" if (run_error or had_tool_error) else "success"
        return self._finish(
            step=step, run_id=run_id, user_input=user_input, run_type="task",
            outcome=outcome, error=run_error,
            tools_called=tools_called, last_observation=last_observation,
            tracer=tracer, fallback=None,
        )

    def _handle_tool_call(self, step, parsed, messages, tracer, seen_signatures: set) -> dict | str | None:
        """执行工具调用。返回:
          - dict: observation（成功或失败的执行结果）
          - str: 不可恢复的错误信息
          - None: 被去重拦截（duplicate_tool_call_blocked）
        """
        tool_name = parsed.get("tool_name", "")
        tool_args = parsed.get("arguments", {})
        if not tool_name:
            return "tool_call 缺少 tool_name"
        if isinstance(tool_args, str):
            try:
                tool_args = json.loads(tool_args)
            except json.JSONDecodeError:
                tool_args = {}

        # 去重检查
        sig = _make_tool_signature(tool_name, tool_args)
        if sig in seen_signatures:
            tracer.log_event(step, "duplicate_tool_call_blocked", {
                "tool_name": tool_name,
                "arguments": tool_args,
            })
            print(f"-> 重复调用已阻止: {tool_name}", end=" ")
            # 向 messages 中加入提示
            messages.append({
                "role": "user",
                "content": f"[系统提示] 工具 {tool_name} 已经成功执行过，请基于已有 observation 直接输出 final_answer，不要再重复调用。",
            })
            return None

        seen_signatures.add(sig)

        print(f"-> 调用工具: {tool_name}", end=" ")

        tracer.log_event(step, "tool_call", {"tool_name": tool_name, "arguments": tool_args})
        observation = self.tools.execute(tool_name, tool_args)
        tracer.log_event(step, "tool_observation", {
            "tool_name": tool_name,
            "success": observation.get("success"),
            "summary": observation.get("summary", "")[:300],
            "error": observation.get("error"),
        })

        if observation.get("success"):
            print("- 执行成功")
        else:
            print(f"- 失败: {observation.get('summary', '')[:60]}")

        return observation

    # ── 统一收尾 ─────────────────────────────

    def _finish(self, step, run_id, user_input, run_type, outcome, error, tools_called, last_observation, tracer, fallback):
        summary = None
        if last_observation:
            summary = last_observation.get("summary", "")
        elif fallback:
            summary = fallback[:200]

        if outcome == "partial":
            for m in reversed(self.session.conversation_history):
                if m.get("role") == "assistant":
                    summary = m.get("content", "")[:200]
                    break

        effective_error = error
        if not effective_error and last_observation and not last_observation.get("success"):
            effective_error = last_observation.get("error") or last_observation.get("summary", "")

        self._record_run(
            run_id=run_id, goal=user_input, run_type=run_type,
            status=outcome, tools_called=tools_called,
            result_summary=summary, error=effective_error,
        )

        tracer.log_event(step, "session_state_update", {"state": self.session.get_state()})
        tracer.log_event(step, "run_end", {"outcome": outcome, "total_steps": min(step, MAX_STEPS)})
        tracer.close()

        self.session.save_to_file()

        if fallback:
            self.session.add_message("assistant", fallback)
            print(f"\n  [结果] {outcome}: {fallback[:80]}")
            return fallback
        else:
            last_msg = self.session.conversation_history[-1]["content"] if self.session.conversation_history else ""
            print("-> 模型直接回答")
            return last_msg

    # ── session_state 更新 ────────────────────

    def _record_run(self, run_id, goal, run_type, status, tools_called, result_summary, error):
        run_summary = {
            "run_id": run_id,
            "goal": goal[:200] if goal else None,
            "run_type": run_type,
            "status": status,
            "tools_called": tools_called,
            "result_summary": result_summary[:300] if result_summary else None,
            "error": error,
            "created_at": datetime.now().isoformat(),
        }
        self.session.add_run_to_state(run_summary)
