"""Mock 搜索工具 — 返回模拟搜索结果"""


def _mock_search(arguments: dict) -> str:
    """模拟搜索，返回固定格式结果"""
    query = arguments.get("query", "")
    if not query:
        return "[mock_search 错误] 缺少 query 参数"

    lines = [
        f"搜索: {query}",
        f"1. {query} 是一个重要主题，在多个领域有应用。",
        f"2. 最新研究表明 {query} 领域正在快速发展。",
        f"3. 社区关于 {query} 的讨论十分活跃。",
        "(以上为模拟结果，非实时数据)",
    ]
    return "\n".join(lines)


mock_search_tool = {
    "name": "mock_search",
    "description": "搜索外部信息，返回模拟结果（非实时联网）",
    "definition": {
        "type": "function",
        "function": {
            "name": "mock_search",
            "description": "搜索外部信息，返回模拟结果（非实时联网）",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "搜索关键词",
                    }
                },
                "required": ["query"],
            },
        },
    },
    "handler": _mock_search,
}
