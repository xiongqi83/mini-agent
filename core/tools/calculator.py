"""计算器工具"""

import re
from core.tools.base import BaseTool


class CalculatorTool(BaseTool):
    def __init__(self):
        super().__init__()
        self.name = "calculator"
        self.description = "执行复杂数学表达式计算，支持 + - * / % 和括号"
        self.parameters = {
            "expression": {
                "type": "string",
                "description": "数学表达式，如 '128 * 36 + 952'",
                "required": True,
            }
        }

    def run(self, arguments: dict) -> str:
        expression = arguments.get("expression", "")
        if not expression:
            raise ValueError("缺少 expression 参数")
        if not re.match(r'^[\d+\-*/().%\s]+$', expression):
            raise ValueError(f"表达式包含非法字符: {expression}")
        result = eval(expression, {"__builtins__": {}}, {})
        return f"{expression} = {result}"
