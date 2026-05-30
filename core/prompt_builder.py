"""Prompt 构建器 — system prompt + tools schema + history + session_state + user input"""

from config.settings import MAX_STEPS


def _format_tools_schema(tools_schema: list[dict]) -> str:
    if not tools_schema:
        return "（无可用工具）"
    lines = []
    for t in tools_schema:
        fn = t.get("function", {})
        name = fn.get("name", "?")
        desc = fn.get("description", "")
        params = fn.get("parameters", {}).get("properties", {})
        required = fn.get("parameters", {}).get("required", [])
        param_strs = []
        for pname, pinfo in params.items():
            req_mark = "(必填)" if pname in required else ""
            ptype = pinfo.get("type", "any")
            pdesc = pinfo.get("description", "")
            enum_hint = ""
            if "enum" in pinfo:
                enum_hint = f" 可选值: {', '.join(pinfo['enum'])}"
            param_strs.append(f"    {pname}: {ptype} {req_mark} — {pdesc}{enum_hint}")
        lines.append(f"### {name}")
        lines.append(f"  {desc}")
        if param_strs:
            lines.append("  参数:")
            lines.extend(param_strs)
        lines.append("")
    return "\n".join(lines)


def _format_one_run(label: str, run: dict | None) -> str:
    if not run:
        return f"{label}: （无记录）"
    goal = run.get("goal", "?")
    status = run.get("status", "?")
    tools = run.get("tools_called", [])
    summary = run.get("result_summary", "")
    error = run.get("error")
    parts = [f"{label}:", f"  目标: {goal[:150]}", f"  状态: {status}"]
    if tools:
        parts.append(f"  工具: {', '.join(tools)}")
    if summary:
        parts.append(f"  摘要: {summary[:200]}")
    if error:
        parts.append(f"  错误: {error[:200]}")
    return "\n".join(parts)


def _format_recent_runs(runs: list) -> str:
    if not runs:
        return "（无历史记录）"
    lines = []
    for i, run in enumerate(reversed(runs[-10:]), 1):
        goal = run.get("goal", "?")[:80]
        status = run.get("status", "?")
        tools = run.get("tools_called", [])
        rtype = run.get("run_type", "task")
        type_tag = "[查询]" if rtype == "state_query" else ""
        lines.append(f"  {i}. [{status}] {type_tag} {goal}" + (f" (工具: {', '.join(tools)})" if tools else ""))
    return "\n".join(lines)


def _format_session_state(state: dict) -> str:
    last_task = state.get("last_task_run")
    last_ok = state.get("last_successful_task_run")
    recent = state.get("recent_runs", [])

    if not last_task and not recent:
        return "（还没有执行记录）"

    parts = []
    parts.append(_format_one_run("**最近一次任务 (last_task_run)**", last_task))
    parts.append("")
    parts.append(_format_one_run("**最近一次成功任务 (last_successful_task_run)**", last_ok))
    parts.append("")
    parts.append("**最近执行历史 (recent_runs):**")
    parts.append(_format_recent_runs(recent))
    return "\n".join(parts)


def build_system_content(tools_schema: list[dict], session_state: dict) -> str:
    tools_text = _format_tools_schema(tools_schema)
    state_text = _format_session_state(session_state)

    return f"""你是 Mini Agent Runtime。

## 输出铁律 — 违反以下任何一条都会导致解析失败

1. **只能输出纯 JSON，不能输出任何其他文字。**
2. **禁止输出 markdown 代码块（不要用 ```json 或 ``` 包裹）。**
3. **禁止在 JSON 前后加任何解释、前缀、后缀。**
4. **整个回复内容必须是一个 JSON 对象，以 {{ 开头，以 }} 结尾。**
5. **JSON 必须包含 "type" 字段，值为 "final_answer" 或 "tool_call"。**

## 决策原则

- **任何数学计算请求都必须调用 calculator 工具。禁止心算直接回答。**
- 搜索信息 → mock_search
- 读取文档 → read_docs
- 询问"刚才""上次""最近"任务状态 → 直接 final_answer，答案从「执行状态」获取

## 工具去重规则
- 如果 observation 已包含足够信息（如已成功读取了某个文件），**不要重复调用同一个文件**。
- 基于已有 observation 直接输出 final_answer，不要为了"获取更多内容"重复调用。

## 可用工具
{tools_text}

## 执行状态
{state_text}

## 跨轮次追问规则

- "刚才那个任务..." → 查看 last_task_run
- "上一次成功..." → 查看 last_successful_task_run
- "最近做过什么" → 查看 recent_runs
- "调用了什么工具" → 查看对应 run 的 tools_called
- "成功了吗 / 出错了吗" → 查看对应 run 的 status 和 error

## 输出格式

直接回答:
{{"type": "final_answer", "content": "回答内容"}}

调用工具:
{{"type": "tool_call", "tool_name": "工具名", "arguments": {{"参数名": "值"}}}}

最大 {MAX_STEPS} 步。现在开始。"""


def build_messages(
    tools_schema: list[dict],
    session_state: dict,
    history: list[dict],
    user_input: str,
    max_history: int = 20,
) -> list[dict]:
    messages = [{"role": "system", "content": build_system_content(tools_schema, session_state)}]
    recent = history[-max_history:] if len(history) > max_history else history
    messages.extend(recent)
    if user_input:
        messages.append({"role": "user", "content": user_input})
    return messages


def build_observation_message(tool_name: str, observation: dict) -> dict:
    success = observation.get("success", False)
    summary = observation.get("summary", "")
    error = observation.get("error", "")
    if success:
        text = f"[{tool_name} 执行成功]\n{summary}"
    else:
        text = f"[{tool_name} 执行失败]\n{summary}"
        if error:
            text += f"\n错误: {error}"
    return {"role": "user", "content": text}


def update_system_state_in_prompt(messages: list[dict], session_state: dict, tools_schema: list[dict]):
    if messages and messages[0]["role"] == "system":
        messages[0]["content"] = build_system_content(tools_schema, session_state)
