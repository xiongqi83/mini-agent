# 测试文档 — MiniAgent 功能说明

> 此文件用于测试 read_docs 工具的读取功能。

## 项目简介

MiniAgent 是一个最小化的 AI Agent 学习框架，实现了以下核心流程：

```
用户输入 → LLM 推理 → 工具调用 → 结果回传 → 循环推理 → 最终回答
```

## 核心模块

### 1. Runtime（运行时）

Agent 主循环，负责调度 LLM 调用和工具执行，是框架的心脏。

关键参数：
- MAX_STEPS: 最大工具调用步数，默认 10
- 每一步记录完整的 trace 日志

### 2. LLM Client

封装 DeepSeek API 调用，当前为 mock 模式。

### 3. Tool Registry

工具注册中心，管理工具的注册、查找、参数校验和执行。

已注册工具：
- calculator: 数学表达式计算
- mock_search: 模拟搜索
- todo: 待办任务管理
- read_docs: 本地文档读取

### 4. Session Manager

会话管理器，维护对话历史，支持 JSON 格式的保存和加载。

### 5. Trace Logger

轨迹日志记录器，记录每一步的执行详情。

## 使用方式

```bash
cd mini_agent
python main.py
```

启动后输入问题即可开始对话，支持以下命令：
- `/exit` — 退出程序
- `/save` — 保存会话和轨迹
- `/help` — 显示帮助

## 版本历史

- v0.1.0 (2026-05-30): 初始版本，mock 模式
