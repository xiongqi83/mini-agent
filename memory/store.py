"""简单记忆存储 — 基于 JSON 文件的键值存储"""

import json
import os


MEMORY_FILE = "memory/memory.json"


class MemoryStore:
    """持久化键值记忆存储"""

    def __init__(self, filepath: str = MEMORY_FILE):
        self.filepath = filepath
        self._data: dict[str, str] = {}
        self._load()

    def _load(self):
        if os.path.exists(self.filepath):
            with open(self.filepath, "r", encoding="utf-8") as f:
                self._data = json.load(f)

    def _save(self):
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(self._data, f, ensure_ascii=False, indent=2)

    def set(self, key: str, value: str):
        self._data[key] = value
        self._save()

    def get(self, key: str, default: str = "") -> str:
        return self._data.get(key, default)

    def delete(self, key: str):
        if key in self._data:
            del self._data[key]
            self._save()

    def all(self) -> dict[str, str]:
        return dict(self._data)
