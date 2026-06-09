"""LLM 客户端 — DeepSeek API（OpenAI 兼容）"""

import json
from config.settings import API_KEY, API_BASE_URL, MODEL_NAME, TEMPERATURE, MAX_TOKENS


class LLMClient:
    """封装 DeepSeek API 调用"""

    def __init__(self, api_key: str = API_KEY, base_url: str = API_BASE_URL, model: str = MODEL_NAME):
        from openai import OpenAI
        self._client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model
        print(f"[LLM] 已连接 {model} ({base_url})")

    def chat(self, messages: list[dict]) -> str:
        """调用 API，返回原始文本"""
        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=TEMPERATURE,
                max_tokens=MAX_TOKENS,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            print(f"  [LLM 错误] {e}")
            return json.dumps(
                {"type": "final_answer", "content": f"LLM 调用失败: {e}"},
                ensure_ascii=False,
            )
