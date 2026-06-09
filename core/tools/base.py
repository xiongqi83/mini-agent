"""工具基类 — 所有工具继承此类"""

from abc import ABC, abstractmethod


class BaseTool(ABC):
    """工具抽象基类"""

    def __init__(self):
        self.name: str = ""
        self.description: str = ""
        self.parameters: dict = {}

    @abstractmethod
    def run(self, arguments: dict) -> str:
        """执行工具，返回纯文本结果"""

    def render(self) -> str:
        """渲染为可注入 Prompt 的文本"""
        lines = [f"### {self.name}", f"  描述: {self.description}"]
        if self.parameters:
            lines.append("  参数:")
            for pname, pinfo in self.parameters.items():
                req = "(必填)" if pinfo.get("required") else ""
                ptype = pinfo.get("type", "any")
                pdesc = pinfo.get("description", "")
                lines.append(f"    {pname}: {ptype} {req} — {pdesc}")
        lines.append("")
        return "\n".join(lines)

    def get_required_params(self) -> list[str]:
        """返回必填参数列表"""
        return [k for k, v in self.parameters.items() if v.get("required")]
