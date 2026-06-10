# Mini Agent

从零实现的轻量 AI Agent。不依赖 LangChain 等框架，自己写 ReAct 循环、工具调用、多轮记忆。

```
用户输入 → LLM 判断 → 直接回答 或 调用工具 → 工具执行 → 回填结果 → 继续推理 → 输出答案
```

## 运行

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

## 演示

**直接回答**
```
你: 什么是 Agent Runtime？
Agent: Agent Runtime 是运行智能代理的核心执行环境，负责管理决策循环、工具调用和上下文...
```

**工具调用**
```
你: 帮我算 128 * 36 + 952
  [Step 1/3] 调用 LLM... -> 调用工具: calculator - 成功
  [Step 2/3] 调用 LLM... -> 直接回答
Agent: 128 × 36 + 952 = 5560
```

**跨轮次追问**（多轮记忆）
```
你: 搜索人工智能的最新进展
  [Step 1/3] -> mock_search - 成功
Agent: 人工智能最新进展包括...

你: 刚才那个搜索成功了吗？
Agent: 是的，刚才的搜索成功了，搜到了人工智能进展的相关信息。
```

**异常处理**（不会崩溃）
```
你: 读取 not_exist.md
  [Step 1/3] -> read_docs - 失败: 文件不存在
  [Step 2/3] -> 解析失败，回填 observation
  [Step 3/3] -> 直接回答
Agent: 读取失败，文件 not_exist.md 在本地不存在。
```
