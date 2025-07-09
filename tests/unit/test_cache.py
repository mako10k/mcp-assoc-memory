"""
キャッシュのテスト
"""

import time

import pytest

from mcp_assoc_memory.utils.cache import EmbeddingCache, LRUCache, SearchCache


class TestLRUCache:
    """LRUキャッシュのテスト"""

    def test_basic_operations(self):
        """基本操作のテスト"""
        cache = LRUCache(max_size=3)

        # 設定と取得
        cache.set("key1", "value1")
        cache.set("key2", "value2")

        assert cache.get("key1") == "value1"
        assert cache.get("key2") == "value2"
        assert cache.get("nonexistent") is None

    def test_lru_eviction(self):
        """LRU排除のテスト"""
        cache = LRUCache(max_size=2)

        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")  # key1が排除される

        assert cache.get("key1") is None
        assert cache.get("key2") == "value2"
        assert cache.get("key3") == "value3"

    def test_lru_update(self):
        """LRU更新のテスト"""
        cache = LRUCache(max_size=2)

        cache.set("key1", "value1")
        cache.set("key2", "value2")

        # key1にアクセスして最新にする
        cache.get("key1")

        cache.set("key3", "value3")  # key2が排除される

        assert cache.get("key1") == "value1"
        assert cache.get("key2") is None
        assert cache.get("key3") == "value3"

    def test_ttl_expiry(self):
        """TTL期限切れのテスト"""
        cache = LRUCache(max_size=10, ttl_seconds=1)

        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

        # TTL期限切れを待つ
        time.sleep(1.1)
        assert cache.get("key1") is None

    def test_delete(self):
        """削除のテスト"""
        cache = LRUCache(max_size=10)

        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

        assert cache.delete("key1")
        assert cache.get("key1") is None
        assert not cache.delete("nonexistent")

    def test_clear(self):
        """クリアのテスト"""
        cache = LRUCache(max_size=10)

        cache.set("key1", "value1")
        cache.set("key2", "value2")

        cache.clear()

        assert cache.get("key1") is None
        assert cache.get("key2") is None

    def test_stats(self):
        """統計のテスト"""
        cache = LRUCache(max_size=10)

        cache.set("key1", "value1")
        cache.get("key1")  # ヒット
        cache.get("nonexistent")  # ミス

        stats = cache.get_stats()

        assert stats["size"] == 1
        assert stats["max_size"] == 10
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["hit_rate"] == 0.5


class TestEmbeddingCache:
    """埋め込みキャッシュのテスト"""

    def test_embedding_operations(self):
        """埋め込み操作のテスト"""
        cache = EmbeddingCache(max_size=10)

        text = "テストテキスト"
        model = "test-model"
        embedding = [0.1, 0.2, 0.3]

        cache.set_embedding(text, model, embedding)
        result = cache.get_embedding(text, model)

        assert result == embedding
        assert cache.get_embedding(text, "other-model") is None
        assert cache.get_embedding("other-text", model) is None


class TestSearchCache:
    """検索キャッシュのテスト"""

    def test_search_operations(self):
        """検索操作のテスト"""
        cache = SearchCache(max_size=10)

        query = "検索クエリ"
        domain = "user"
        filters = {"tag": "test"}
        results = [{"id": "1", "content": "結果1"}]

        cache.set_search_result(query, domain, filters, results)
        cached_results = cache.get_search_result(query, domain, filters)

        assert cached_results == results

        # 異なるフィルターでは取得できない
        other_filters = {"tag": "other"}
        assert cache.get_search_result(query, domain, other_filters) is None
