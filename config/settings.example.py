"""全局配置 — 复制为 settings.py 并填入真实值"""

# ── DeepSeek API 配置 ──────────────────────
# 申请地址: https://platform.deepseek.com/api_keys
API_KEY = "your-deepseek-api-key"
API_BASE_URL = "https://api.deepseek.com"
MODEL_NAME = "deepseek-chat"

# PICO 备选配置
PICO_MODEL_NAME = "deepseek-chat"
PICO_BASE_URL = "https://api.deepseek.com"
PICO_API_KEY = ""

# ── Mock 开关 ─────────────────────────────
USE_MOCK = True     # True=离线mock / False=真实API

# ── Agent 配置 ────────────────────────────
MAX_STEPS = 10
TEMPERATURE = 0.7
MAX_TOKENS = 4096

# ── 路径配置 ──────────────────────────────
TRACE_DIR = "data/traces"
SESSION_DIR = "data/sessions"
DOCS_DIR = "data/docs"

# ── 调试开关 ──────────────────────────────
DEBUG = True
