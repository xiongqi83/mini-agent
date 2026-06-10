# Mini Agent

从零实现的轻量 AI Agent。不依赖 LangChain 等框架，自己写 ReAct 循环、工具调用、多轮记忆。

```
用户输入 → LLM 判断 → 直接回答 或 调用工具 → 工具执行 → 回填结果 → 继续推理 → 输出答案
```

## 运行方式

```bash
pip install -r requirements.txt
```

`config/settings.py` 里填 API Key：

```python
API_KEY = "sk-xxxxxxxx"
```

启动：

```bash
python main.py
```

输入 `/exit` 退出。Trace 日志自动保存到 `data/traces/{会话时间}.jsonl`。

## 系统设计

核心循环在 `core/runtime.py`：

```
run(user_input)
  → 用户输入写入 Memory（只存对话，不存轨迹）
  → 初始化 Scratchpad（空列表，仅限本轮）
  → 循环 (最多 MAX_STEPS 步):
      → 构建 Prompt（系统指令 + 对话历史 + Scratchpad）
      → 调用 LLM
      → 解析 JSON 输出
      → final_answer → 写入 Memory → 返回
      → tool_call → 参数校验 → 执行工具 → observation 写入 Scratchpad → 继续
      → 解析错误 → 写入 Scratchpad → 继续
  → 超时兜底
```

三个内置工具：`calculator`（数学计算）、`mock_search`（模拟搜索）、`read_docs`（读取本地文档）。工具通过 `BaseTool` 基类统一接口，`ToolRegistry` 管理注册和执行。新增工具只需继承 `BaseTool` 并调用 `tools.register()`。

运行轨迹通过 Hook 系统输出：`ConsoleHandler` 打印到终端，`FileHandler` 追加到 JSONL 文件。

## Memory 的召回时机与放置方式

Memory 分为两部分：**对话记忆** 和 **执行轨迹**，两者严格分离。

| | 对话记忆 (conversation_history) | 执行轨迹 (scratchpad) |
|---|---|---|
| 内容 | 用户输入 + 助手最终回答 | 本轮 action / observation / error |
| 生命周期 | 跨轮持久化，整个会话共享 | 仅限当前 `run()`，用完销毁 |
| 是否进 Prompt | **是** | **是** |
| 是否写入 Memory | 是 | 否 |

**召回时机**：每次调用 LLM 之前，从 Memory 中取出全部对话历史。

**放置方式**：`build_messages()` 组装为：

```
[system]   系统指令 + 工具列表
[user]     第1轮问题        ← 来自 Memory
[assistant] 第1轮回答        ← 来自 Memory
[user]     第2轮问题        ← 来自 Memory
[assistant] 第2轮回答        ← 来自 Memory
[user]     当前问题
[assistant] Thought: {Scratchpad 文本}   ← 本轮推理轨迹
```

对话历史以独立 messages 追加（保留 role 标签），Scratchpad 以 `Thought:` 前缀嵌入 assistant 消息。这样 LLM 既能理解上下文，又能看到本轮已执行的工具步骤，决定下一步。

## 演示

**直接回答**
```
你: 什么是 Agent Runtime？
Agent: Agent Runtime 是运行智能代理的核心执行环境...
```

**工具调用**
```
你: 帮我算 128 * 36 + 952
  [Step 1/3] -> 调用工具: calculator - 成功
  [Step 2/3] -> 直接回答
Agent: 128 × 36 + 952 = 5560
```

**跨轮次追问**
```
你: 搜索人工智能进展
  [Step 1/3] -> mock_search - 成功
Agent: 人工智能最新进展包括...

你: 刚才那个搜索成功了吗？
Agent: 是的，刚才的搜索成功了。
```

**异常处理**
```
你: 读取 not_exist.md
  [Step 1/3] -> read_docs - 失败: 文件不存在
  [Step 2/3] -> 直接回答
Agent: 读取失败，文件 not_exist.md 在本地不存在。
```
