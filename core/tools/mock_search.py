"""模拟搜索工具"""

from core.tools.base import BaseTool


class MockSearchTool(BaseTool):
    def __init__(self):
        super().__init__()
        self.name = "mock_search"
        self.description = "搜索外部信息，返回模拟结果（非实时联网）"
        self.parameters = {
            "query": {
                "type": "string",
                "description": "搜索关键词",
                "required": True,
            }
        }

    def run(self, arguments: dict) -> str:
        query = arguments.get("query", "")
        if not query:
            raise ValueError("缺少 query 参数")
        return (
            f"搜索: {query}\n"
            f"1. {query} 是一个重要主题，在多个领域有应用。\n"
            f"2. 最新研究表明 {query} 领域正在快速发展。\n"
            f"3. 社区关于 {query} 的讨论十分活跃。\n"
            "(以上为模拟结果)"
        )
