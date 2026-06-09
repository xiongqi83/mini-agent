"""工具注册中心 — 接受工具实例，管理注册和执行"""

from core.tools.base import BaseTool
from core.tools.calculator import CalculatorTool
from core.tools.mock_search import MockSearchTool
from core.tools.read_docs import ReadDocsTool


class ToolRegistry:
    """工具注册与调度。参数校验交给 runtime。"""

    def __init__(self):
        self._tools: dict[str, BaseTool] = {}
        # 注册内置工具
        for inst in [CalculatorTool(), MockSearchTool(), ReadDocsTool()]:
            self.register(inst)

    def register(self, tool: BaseTool):
        """注册工具实例"""
        if not tool.name:
            raise ValueError("工具缺少 name")
        if not tool.description:
            raise ValueError(f"工具 '{tool.name}' 缺少 description")
        if not callable(tool.run):
            raise ValueError(f"工具 '{tool.name}' 的 run 不可调用")
        self._tools[tool.name] = tool

    def execute(self, name: str, arguments: dict) -> str:
        """执行工具。成功返回结果文本，失败返回错误文本。不会崩溃。"""
        tool = self._tools.get(name)
        if tool is None:
            return f"[错误] 工具 '{name}' 不存在。可用: {', '.join(self.list_tools())}"

        try:
            return tool.run(arguments)
        except Exception as e:
            return f"[{name} 错误] {type(e).__name__}: {e}"

    def render(self) -> str:
        """将所有工具渲染为 Prompt 文本"""
        parts = [t.render() for t in self._tools.values()]
        return "\n".join(parts) if parts else "（无可用工具）"

    def list_tools(self) -> list[str]:
        return list(self._tools.keys())

    def get(self, name: str) -> BaseTool | None:
        return self._tools.get(name)

    def get_all(self) -> list[BaseTool]:
        return list(self._tools.values())
