"""计算器工具 — 安全执行数学表达式"""

import re


def _calculate(arguments: dict) -> str:
    """执行计算，返回纯文本结果"""
    expression = arguments.get("expression", "")
    if not expression:
        return "[calculator 错误] 缺少 expression 参数"

    if not re.match(r'^[\d+\-*/().%\s]+$', expression):
        return "[calculator 错误] 表达式包含非法字符"

    try:
        result = eval(expression, {"__builtins__": {}}, {})
        return f"{expression} = {result}"
    except Exception as e:
        return f"[calculator 错误] {e}"


calculator_tool = {
    "name": "calculator",
    "description": "执行复杂数学表达式计算，支持 + - * / % 和括号。简单口算请直接回答。",
    "definition": {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "执行复杂数学表达式计算，支持 + - * / % 和括号。简单口算请直接回答。",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "数学表达式，如 '128 * 36 + 952'",
                    }
                },
                "required": ["expression"],
            },
        },
    },
    "handler": _calculate,
}
