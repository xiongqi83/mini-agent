"""LLM 客户端 — 支持 Mock 和真实 DeepSeek API 两种模式

切换方式:
  1. 修改 config/settings.py 中的 USE_MOCK = False
  2. 填入真实的 API_KEY（非 your-... 占位符）
  3. 自动走真实 API
"""

import json
import re
from config.settings import (
    API_KEY,
    API_BASE_URL,
    MODEL_NAME,
    TEMPERATURE,
    MAX_TOKENS,
    USE_MOCK,
    DEBUG,
)

# ── Mock 实现 ──────────────────────────────
# 保留完整的 mock 逻辑，方便离线调试

class MockLLMClient:
    """Mock LLM — 关键词匹配，返回 JSON 协议字符串，不调用任何 API"""

    def __init__(self, api_key: str = "", base_url: str = "", model: str = MODEL_NAME):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self._call_count = 0

    def chat(self, messages: list) -> str:
        self._call_count += 1

        # 上一条是 observation（user 角色 + 执行标记）→ final_answer
        last_msg = messages[-1] if messages else {}
        if last_msg.get("role") == "user":
            lc = last_msg.get("content", "")
            if "执行成功" in lc or "执行失败" in lc:
                return json.dumps(
                    {"type": "final_answer", "content": f"[mock] 根据工具结果: {lc[:150]}"},
                    ensure_ascii=False,
                )

        # 最后一条用户消息
        last_user_msg = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                last_user_msg = m.get("content", "")
                break

        # ── 关键词匹配 ──
        # 计算 — 显式关键词或包含数字+运算符的模式
        has_math_keyword = "计算" in last_user_msg or "算" in last_user_msg
        has_math_pattern = bool(re.search(r'\d+\s*[\+\-\*\/]\s*\d+', last_user_msg))
        if has_math_keyword or has_math_pattern:
            expr = self._extract_expression(last_user_msg)
            return json.dumps(
                {"type": "tool_call", "tool_name": "calculator", "arguments": {"expression": expr}},
                ensure_ascii=False,
            )

        # 搜索
        if "搜索" in last_user_msg or "查询" in last_user_msg:
            return json.dumps(
                {"type": "tool_call", "tool_name": "mock_search", "arguments": {"query": last_user_msg}},
                ensure_ascii=False,
            )

        # 读取文档
        if "读取" in last_user_msg or "文档" in last_user_msg or "read" in last_user_msg.lower():
            filename = self._extract_filename(last_user_msg)
            return json.dumps(
                {"type": "tool_call", "tool_name": "read_docs", "arguments": {"filename": filename}},
                ensure_ascii=False,
            )

        # 跨轮次追问 → 根据 session_state 直接回答
        if "刚才" in last_user_msg or "上一轮" in last_user_msg or "上次" in last_user_msg:
            state_info = self._extract_session_state(messages)
            return json.dumps(
                {"type": "final_answer", "content": f"[mock] 根据上次执行记录: {state_info}"},
                ensure_ascii=False,
            )

        # 默认
        return json.dumps(
            {"type": "final_answer", "content": f"[mock] 收到: '{last_user_msg[:50]}'。"},
            ensure_ascii=False,
        )

    def _extract_expression(self, text: str) -> str:
        # 提取数学表达式: 数字、运算符、空格、点号
        m = re.search(r'[\d\+\-\*\/\(\)\.%\s]+', text)
        return m.group().strip() if m else text

    def _extract_filename(self, text: str) -> str:
        m = re.search(r'([\w\-]+\.md)', text)
        return m.group(1) if m else "agent_runtime.md"

    def _extract_session_state(self, messages: list) -> str:
        for m in messages:
            if m.get("role") == "system":
                content = m.get("content", "")
                if "上一轮" in content:
                    # 提取 session_state 部分
                    start = content.find("上次执行状态")
                    if start >= 0:
                        return content[start:start+300].replace("\n", " ")
        return "暂无上次执行记录"


# ── 真实 API 实现 ──────────────────────────

class RealLLMClient:
    """真实 LLM — 通过 OpenAI 兼容接口调用 DeepSeek API"""

    def __init__(self, api_key: str, base_url: str, model: str = MODEL_NAME):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self._call_count = 0

        try:
            from openai import OpenAI
            self._client = OpenAI(api_key=api_key, base_url=base_url)
            self._available = True
            if DEBUG:
                print(f"[LLMClient] 初始化完成, model={self.model} (真实 API: {base_url})")
        except ImportError:
            self._available = False
            print("[LLMClient] 警告: openai 库未安装，回退到 mock 模式。请运行: pip install openai")
        except Exception as e:
            self._available = False
            print(f"[LLMClient] 警告: 初始化失败 ({e})，回退到 mock 模式")

    def chat(self, messages: list) -> str:
        """调用真实 API，返回 LLM 原始输出文本"""
        self._call_count += 1

        if not self._available:
            # 回退到 mock
            mock = MockLLMClient()
            return mock.chat(messages)

        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=TEMPERATURE,
                max_tokens=MAX_TOKENS,
            )
            content = response.choices[0].message.content
            return content or ""
        except Exception as e:
            print(f"  [API 错误] {e}")
            return json.dumps(
                {
                    "type": "final_answer",
                    "content": f"抱歉，LLM 调用出错: {e}。请稍后重试。",
                },
                ensure_ascii=False,
            )


# ── 工厂函数 ───────────────────────────────

def create_llm_client(
    api_key: str = API_KEY,
    base_url: str = API_BASE_URL,
    model: str = MODEL_NAME,
) -> MockLLMClient | RealLLMClient:
    """根据配置自动选择 Mock 或真实客户端。

    规则:
      - USE_MOCK=True          → Mock
      - API_KEY 为空或占位符    → Mock
      - API_KEY 以 "sk-" 开头  → 真实 API
    """
    if USE_MOCK:
        if DEBUG:
            print("[LLMClient] USE_MOCK=True, 使用 mock 模式")
        return MockLLMClient(api_key, base_url, model)

    if not api_key or api_key.startswith("your-"):
        if DEBUG:
            print("[LLMClient] API_KEY 未配置或为占位符, 使用 mock 模式")
        return MockLLMClient(api_key, base_url, model)

    if DEBUG:
        print("[LLMClient] 检测到真实 API_KEY, 使用真实 API")
    return RealLLMClient(api_key=api_key, base_url=base_url, model=model)


# ── 兼容别名 ───────────────────────────────
# 旧代码中 import LLMClient 的地方无需修改
LLMClient = create_llm_client
