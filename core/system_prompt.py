"""System Prompt 构建器 — PREFIX + FORMAT_INSTRUCTIONS + SUFFIX"""

from config.settings import MAX_STEPS

PREFIX = """你是 Mini Agent Runtime。

## 可用工具
{tools_schema}

## 本轮推理轨迹 (Scratchpad)
{scratchpad}

## 最新观察结果 (Observation)
{observation}
"""

FORMAT_INSTRUCTIONS = """## 输出协议
每次必须严格输出一个 JSON 对象，禁止任何其他文字。

直接回答：
{{"type": "final_answer", "content": "你的回答"}}

调用工具：
{{"type": "tool_call", "tool_name": "工具名", "arguments": {{"参数": "值"}}}}

规则：
- 只输出纯 JSON。禁止 markdown。禁止代码块。禁止解释前缀。
- 对话历史在下方消息列表中，据此理解上下文。
- 工具执行后你会收到 Observation，据此生成最终回答。
- **任何数学计算请求都必须调用 calculator 工具。禁止心算直接回答。**
- 最大 {max_steps} 步。"""

SUFFIX = """## 任务
处理用户的请求。现在开始。"""


def build_system_prompt(
    tools_schema: str = "（无可用工具）",
    scratchpad: str = "（暂无轨迹）",
    observation: str = "（无）",
) -> str:
    prefix = PREFIX.format(
        tools_schema=tools_schema or "（无可用工具）",
        scratchpad=scratchpad or "（暂无轨迹）",
        observation=observation or "（无）",
    )
    fmt = FORMAT_INSTRUCTIONS.format(max_steps=MAX_STEPS)
    return prefix + fmt + SUFFIX
