"""工具注册中心 — 统一注册、校验、执行，返回统一 observation 格式"""

from tools.calculator import calculator_tool
from tools.mock_search import mock_search_tool
from tools.read_docs import read_docs_tool


BUILTIN_TOOLS = [calculator_tool, mock_search_tool, read_docs_tool]


class ToolRegistry:
    """工具注册与调度"""

    def __init__(self):
        self._tools: dict[str, dict] = {}
        self._register_defaults()

    def _register_defaults(self):
        for tool in BUILTIN_TOOLS:
            self.register(tool)

    def register(self, tool_def: dict):
        name = tool_def.get("name")
        if not name:
            raise ValueError("工具缺少 name 字段")
        if "handler" not in tool_def:
            raise ValueError(f"工具 '{name}' 缺少 handler")
        if "definition" not in tool_def:
            raise ValueError(f"工具 '{name}' 缺少 definition")
        self._tools[name] = tool_def

    def get(self, name: str) -> dict | None:
        return self._tools.get(name)

    def list_tools(self) -> list[str]:
        return list(self._tools.keys())

    def execute(self, name: str, arguments: dict) -> dict:
        """执行工具，统一返回 observation dict:
        {
          "success": bool,
          "tool_name": str,
          "summary": str,
          "data": dict | None,
          "error": str | None
        }
        """
        tool = self._tools.get(name)
        if tool is None:
            return {
                "success": False,
                "tool_name": name,
                "summary": f"工具 '{name}' 不存在",
                "data": None,
                "error": f"可用工具: {', '.join(self.list_tools())}",
            }

        # 参数校验
        param_error = self._validate_params(tool, arguments)
        if param_error:
            return {
                "success": False,
                "tool_name": name,
                "summary": f"参数缺失: {param_error}",
                "data": None,
                "error": param_error,
            }

        try:
            raw_result = tool["handler"](arguments)

            # handler 返回字符串 → 判断是否包含错误前缀
            if isinstance(raw_result, str):
                is_error = raw_result.startswith("[")
                return {
                    "success": not is_error,
                    "tool_name": name,
                    "summary": raw_result[:300],
                    "data": {"raw_result": raw_result} if not is_error else None,
                    "error": raw_result if is_error else None,
                }
            # handler 返回 dict → 直接使用
            return raw_result
        except Exception as e:
            return {
                "success": False,
                "tool_name": name,
                "summary": f"工具执行异常: {type(e).__name__}",
                "data": None,
                "error": str(e),
            }

    def _validate_params(self, tool: dict, arguments: dict) -> str | None:
        try:
            required = (
                tool.get("definition", {})
                .get("function", {})
                .get("parameters", {})
                .get("required", [])
            )
        except (AttributeError, KeyError):
            return None
        if not required:
            return None
        missing = [p for p in required if p not in arguments or not arguments[p]]
        if missing:
            return f"缺少必填参数: {', '.join(missing)}"
        return None

    def get_tool_definitions(self) -> list[dict]:
        return [t["definition"] for t in self._tools.values()]
