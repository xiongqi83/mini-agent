# Agent Runtime 设计概述

> 此文档用于测试 read_docs 工具。

## 什么是 Agent Runtime

Agent Runtime 是一个最小化的 AI Agent 执行框架。它的核心循环是：

```
用户输入 → LLM 推理 → 决策（直接回答 / 调用工具）
                         ↓
                    工具执行 → 结果回传 → 继续推理 → 最终回答
```

## 核心组件

### Runtime
主循环控制器，协调 LLM 调用和工具执行。每轮用户输入触发一次 run，生成独立的 run_id 和 trace。

### LLM Client
封装 DeepSeek API（OpenAI 兼容），支持 mock 和真实两种模式。

### Tool Registry
工具注册中心，管理工具的注册、参数校验和执行。所有工具执行结果统一返回 observation 格式。

### Session Manager
维护 conversation_history 和 session_state，支持多轮对话和跨轮次延续。

### Prompt Builder
构建每次 LLM 调用的输入，包括 system prompt、工具列表、历史对话、session_state 和当前用户输入。

### Trace Logger
以 JSONL 格式记录每次 run 的完整执行轨迹，包括 LLM 请求/响应、工具调用、观察结果、错误等。

## 设计原则

1. 最小依赖：不引入 LangChain 等重型框架
2. 统一协议：LLM 输出只允许 final_answer 或 tool_call 两种 JSON
3. 错误不崩溃：任何异常都被捕获、记录、兜底
4. 可追溯：每一步都有 trace 记录
5. 跨轮次：通过 session_state 让模型知道上一轮做了什么

## 版本

- v0.2.0 (2026-05-30): 重构工具层、session_state、统一 observation 格式
- v0.1.0 (2026-05-30): 初始版本
