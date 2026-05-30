# AI 辅助开发记录

## 项目初始化 (2026-05-30)

### Prompt 1: 搭建最小框架
```
你接下来需要帮我搭建一个最小的框架，
不用实现真实的工具逻辑，不去实现复杂功能，不需要搭建web前端：
1. 按照如下指定目录进行创建目录: [目录结构]
2. 在main函数中能够启动一轮CLI对话，写一个最基本的Agent运行框架
3. llm_client, tool_registry, session_manager, trace_logger 可以先写mock
4. 保证代码能运行。
```

### 架构决策

- **LangGraph 替代方案**: 自实现 Runtime 主循环，核心流程为 while 循环调用 LLM ↔ 执行工具
- **工具定义格式**: 采用 OpenAI function calling 兼容格式，可直接对接 DeepSeek API
- **Mock 策略**: LLM 客户端根据关键词返回 tool_calls；工具返回假数据
- **存储格式**: JSON 文件存储，简单可靠，适合学习阶段

### 待解决问题

1. [ ] 接入真实 DeepSeek API
2. [ ] 引入真实的搜索工具（如 DuckDuckGo）
3. [ ] 实现流式输出（streaming）
4. [ ] 考虑 ReAct / Plan-Execute 等增强策略
5. [ ] 多轮对话的工具调用链追踪优化
