"""
LRUCache実装
"""
from collections import OrderedDict
from typing import Any, Optional

class LRUCache:
    def __init__(self, capacity: int = 128):
        self.cache = OrderedDict()
        self.capacity = capacity

    def get(self, key: Any) -> Optional[Any]:
        if key not in self.cache:
            return None
        self.cache.move_to_end(key)
        return self.cache[key]

    def set(self, key: Any, value: Any) -> None:
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = value
        if len(self.cache) > self.capacity:
            self.cache.popitem(last=False)
