"""
記憶モデルのテスト
"""

from datetime import datetime

import pytest

from mcp_assoc_memory
class TestMemoryStats:
    """記憶統計のテスト"""

    def test_memory_stats_creation(self):
        """記憶統計の作成をテスト"""
        stats = MemoryStats(
            total_count=100,
            scope_counts={"user/default": 50, "project/test": 30},
            tag_counts={"test": 10, "example": 5}
        )

        assert stats.total_count == 100
        assert stats.scope_counts["user/default"] == 50
        assert stats.tag_counts["test"] == 10
        assert isinstance(stats.last_updated, datetime)mport Memory, MemoryStats


class TestMemory:
    """記憶モデルのテスト"""

    def test_memory_creation(self):
        """記憶の作成をテスト"""
        memory = Memory(
            content="テスト記憶",
            scope="user/test",
            tags=["test", "example"]
        )

        assert memory.content == "テスト記憶"
        assert memory.scope == "user/test"
        assert "test" in memory.tags
        assert "example" in memory.tags
        assert memory.access_count == 0
        assert isinstance(memory.created_at, datetime)

    def test_memory_to_dict(self):
        """記憶の辞書変換をテスト"""
        memory = Memory(
            content="テスト記憶",
            scope="project/test",
            user_id="user123",
            project_id="proj456"
        )

        data = memory.to_dict()

        assert data["content"] == "テスト記憶"
        assert data["scope"] == "project/test"
        assert data["user_id"] == "user123"
        assert data["project_id"] == "proj456"
        assert "created_at" in data
        assert "updated_at" in data

    def test_memory_from_dict(self):
        """辞書からの記憶復元をテスト"""
        data = {
            "id": "test-id",
            "content": "テスト記憶",
            "scope": "session/test",
            "metadata": {"category": "test"},
            "tags": ["test"],
            "user_id": "user123",
            "project_id": None,
            "session_id": "session789",
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
            "accessed_at": "2024-01-01T00:00:00",
            "access_count": 5
        }

        memory = Memory.from_dict(data)

        assert memory.id == "test-id"
        assert memory.content == "テスト記憶"
        assert memory.scope == "session/test"
        assert memory.metadata["category"] == "test"
        assert memory.access_count == 5

    def test_memory_update_access(self):
        """アクセス情報更新をテスト"""
        memory = Memory(content="テスト")
        initial_count = memory.access_count
        initial_time = memory.accessed_at

        memory.update_access()

        assert memory.access_count == initial_count + 1
        assert memory.accessed_at > initial_time


class TestMemoryStats:
    """Memory statistics tests"""

    def test_stats_creation(self):
        """Test statistics creation"""
        stats = MemoryStats(
            total_count=100,
            scope_counts={"user/default": 50, "work/project": 30, "personal": 20},
            tag_counts={"test": 10, "example": 5}
        )

        assert stats.total_count == 100
        assert stats.scope_counts["user/default"] == 50
        assert stats.tag_counts["test"] == 10
        assert isinstance(stats.last_updated, datetime)
