"""System Prompt 构建器 — PREFIX + FORMAT_INSTRUCTIONS + SUFFIX"""

from config.settings import MAX_STEPS

PREFIX = """你是一个智能助手，能够使用工具来完成用户的任务。

## 可用工具
{tools_schema}

"""

FORMAT_INSTRUCTIONS = """## 输出协议
每次必须严格输出一个 JSON 对象，禁止任何其他文字。示例如下：

直接回答：
{{"type": "final_answer", "content": "你的回答"}}

调用工具：
{{"type": "tool_call", "tool_name": "工具名", "arguments": {{"参数": "值"}}}}

规则：
- 只输出纯 JSON。输出会被 json.loads() 直接解析，输入任何除json以外的字符都会导致系统报错，禁止 markdown。禁止代码块。禁止解释前缀。
- 工具执行成功或失败，你都必须在下一步输出 JSON。不能输出自然语言。
- 工具执行后你会收到 Observation，必须基于observation继续推理，禁止编造工具执行结果。
- 当用户问题已经得到充分回答的时候，必须输出 final_answer
- 不要为了验证结果重复调用同一个工具
- 调用工具的时候只能调用tools_schema 中列出的工具，禁止虚构工具
- **任何数学计算请求都必须调用 calculator 工具。禁止口算直接回答。**
- 最大 {max_steps} 步。"""

SUFFIX = """开始！记住你每次只能输出一个json对象"""


def build_system_prompt(tools_schema: str = "（无可用工具）") -> str:
    """只构建 system prompt"""
    prefix = PREFIX.format(tools_schema=tools_schema or "（无可用工具）")
    fmt = FORMAT_INSTRUCTIONS.format(max_steps=MAX_STEPS)
    return prefix + fmt + SUFFIX


def build_messages(
    system_prompt: str,
    user_input: str,
    chat_history: list[dict],
    scratchpad_text: str,
) -> list[dict]:
    """组装完整 messages 列表"""
    messages = [{"role": "system", "content": system_prompt}]

    # 跨轮对话历史（只含 user/assistant 问答，不含推理轨迹）
    messages.extend(chat_history)

    # 当前轮：用户问题
    messages.append({"role": "user", "content": user_input})

    # agent_scratchpad：紧挨 Thought: 标签，LLM 从这里接着写
    if scratchpad_text:
        messages.append({
            "role": "assistant",
            "content": f"Thought: {scratchpad_text}",
        })
    else:
        messages.append({
            "role": "assistant",
            "content": "Thought: ",
        })

    return messages
