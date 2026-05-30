# Mini Agent Runtime

## 1. 项目简介

Mini Agent Runtime 是一个从零实现的最小可用 Agent 示例项目。项目不依赖 LangChain、OpenHands 等现成 Agent 框架完成主流程，实现 Agent Runtime、工具注册、工具调用、Session 维护、Memory 召回、Trace 日志和最大步数控制。

本项目最基本的运行闭环：

用户输入 → LLM 判断 → 直接回答或调用工具 → 工具执行 → Observation 回填 → 继续推理 → 输出最终答案

当前项目支持：

- 多轮对话和 session 维护
- Agent Runtime 主循环
- 真实 LLM API 调用
- calculator、mock_search、read_docs 三个工具
- 工具调用 observation 回填
- 最大步数限制
- 基本异常处理
- 独立 trace 执行日志
- 基于 session_state 的跨轮次状态追问

---

## 2. 运行方式

### 2.1 安装依赖

```pip install -r requirements.txt```

## 2.2 配置 API Key

修改模型名称或接口地址，在 config/settings.py 中调整

## 2.3 启动项目

```python main.py```

启动后即可进行对话，输入`exit`或者`quit`退出

## 3. 系统设计

项目核心流程由 `core/runtime.py` 控制，整体执行链路如下：

```text
用户输入
--> 加载当前 session
--> 生成本轮 run_id
--> 构建 prompt
--> 调用 LLM
--> 解析模型输出
--> 如果是 final_answer：保存回答，结束本轮
--> 如果是 tool_call：调用工具，获得 observation
--> 将 observation 回填给模型，继续循环
--> 直到得到 final_answer 或达到 max_steps

模型输出统一采用 JSON 协议，只允许两种类型：

{
  "type": "final_answer",
  "content": "最终回答内容"
}
{
  "type": "tool_call",
  "tool_name": "calculator",
  "arguments": {
    "expression": "1 + 1"
  }
}

Runtime 根据 type 字段控制流程：final_answer 表示本轮任务完成；tool_call 表示需要调用工具，并将工具结果作为 observation 回填给模型继续推理。若模型输出无法解析、工具调用失败或达到最大步数限制，runtime 会记录 trace，并返回兜底结果。
```

## 4.memory 的召回时机与放置方式说明

本项目使用 `session_state` 作为当前会话内的轻量级 memory，用来保存对后续对话有帮助的结构化状态。

每一轮用户输入进入 `runtime` 后，会先根据 `session_id` 加载对应的 session。session 中主要包含两部分：

- `conversation_history`：保存用户和助手的历史对话。
- `session_state`：保存最近任务的结构化状态，例如任务目标、执行状态、调用工具、结果摘要和错误信息。

Memory 的召回发生在**每次调用 LLM 之前**。`prompt_builder` 会从 session 中取出最近10轮对话和 `session_state`，并放入本轮 prompt。

整体放置方式如下：

```
system prompt
  --> tools schema # 工具库
  --> session_state # 对话状态
  --> recent conversation_history # 近期历史
  --> current user input # 当前对话用户输入
  --> latest observation # 最新的观察状态
```

其中，session_state 用于回答跨轮次追问，例如：刚才那个任务执行成功了吗？上一次失败的任务是什么？最近几轮我让你做了什么？
trace 不作为 memory 放入 prompt。它单独保存在 data/traces/ 中，只用于调试和查看 Agent 每一轮的执行过程。