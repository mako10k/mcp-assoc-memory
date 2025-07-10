"""
LRUCache実装
"""
from collections import OrderedDict
from typing import Any, Optional


class LRUCache:
    def __init__(self, max_size: int = 128, ttl_seconds: Optional[float] = None):
        self.cache = OrderedDict()
        self.capacity = max_size
        self.ttl_seconds = ttl_seconds
        self.expiry = dict()  # key: expire_time
        self.hits = 0
        self.misses = 0

    def clear(self) -> None:
        """キャッシュを全消去"""
        self.cache.clear()

    def get_stats(self) -> dict:
        """キャッシュ統計情報を返す"""
        total = len(self.cache)
        hit_rate = self.hits / (self.hits + self.misses) if (self.hits + self.misses) > 0 else 0.0
        return {
            "size": total,
            "max_size": self.capacity,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": hit_rate
        }

    def get(self, key: Any) -> Optional[Any]:
        import time
        if key not in self.cache:
            self.misses += 1
            return None
        if self.ttl_seconds is not None:
            expire = self.expiry.get(key)
            if expire is not None and time.time() > expire:
                del self.cache[key]
                del self.expiry[key]
                self.misses += 1
                return None
        self.cache.move_to_end(key)
        self.hits += 1
        return self.cache[key]

    def set(self, key: Any, value: Any) -> None:
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = value
        if self.ttl_seconds is not None:
            import time
            self.expiry[key] = time.time() + self.ttl_seconds
        if len(self.cache) > self.capacity:
            old_key, _ = self.cache.popitem(last=False)
            if old_key in self.expiry:
                del self.expiry[old_key]

    def delete(self, key: Any) -> bool:
        """指定したキーを削除。成功時True、未存在時False"""
        if key in self.cache:
            del self.cache[key]
            return True
        return False

# --- EmbeddingCache ---


class EmbeddingCache(LRUCache):
    def set_embedding(self, text: str, model: str, embedding: list) -> None:
        key = (text, model)
        self.set(key, embedding)

    def get_embedding(self, text: str, model: str) -> Optional[list]:
        key = (text, model)
        return self.get(key)

# --- SearchCache ---


class SearchCache(LRUCache):
    def set_search_result(self, query: str, scope: str, filters: dict, results: list) -> None:
        key = (query, scope, frozenset(filters.items()) if filters else None)
        self.set(key, results)

    def get_search_result(self, query: str, scope: str, filters: dict) -> Optional[list]:
        key = (query, scope, frozenset(filters.items()) if filters else None)
        return self.get(key)
