"""Memory 第一层：抽象存储基类 + 内存实现"""

from abc import ABC, abstractmethod


class MemoryStore(ABC):
    """抽象存储基类。后续如需存储到文件/数据库，只需继承此类。"""

    @abstractmethod
    def add_batch(self, messages: list[dict]) -> None:
        """批量加入消息"""

    @abstractmethod
    def get_all(self) -> list[dict]:
        """返回所有消息"""

    @abstractmethod
    def clear(self) -> None:
        """清空所有消息"""


class InMemoryStore(MemoryStore):
    """内存存储实现"""

    def __init__(self):
        self._messages: list[dict] = []

    def add_batch(self, messages: list[dict]) -> None:
        self._messages.extend(messages)

    def get_all(self) -> list[dict]:
        return list(self._messages)

    def clear(self) -> None:
        self._messages.clear()
