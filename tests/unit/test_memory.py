"""
記憶モデルのテスト
"""

import pytest
from datetime import datetime
from mcp_assoc_memory.models.memory import Memory, MemoryDomain, MemoryStats


class TestMemory:
    """記憶モデルのテスト"""
    
    def test_memory_creation(self):
        """記憶の作成をテスト"""
        memory = Memory(
            content="テスト記憶",
            domain=MemoryDomain.USER,
            tags=["test", "example"]
        )
        
        assert memory.content == "テスト記憶"
        assert memory.domain == MemoryDomain.USER
        assert "test" in memory.tags
        assert "example" in memory.tags
        assert memory.access_count == 0
        assert isinstance(memory.created_at, datetime)
    
    def test_memory_to_dict(self):
        """記憶の辞書変換をテスト"""
        memory = Memory(
            content="テスト記憶",
            domain=MemoryDomain.PROJECT,
            user_id="user123",
            project_id="proj456"
        )
        
        data = memory.to_dict()
        
        assert data["content"] == "テスト記憶"
        assert data["domain"] == "project"
        assert data["user_id"] == "user123"
        assert data["project_id"] == "proj456"
        assert "created_at" in data
        assert "updated_at" in data
    
    def test_memory_from_dict(self):
        """辞書からの記憶復元をテスト"""
        data = {
            "id": "test-id",
            "content": "テスト記憶",
            "domain": "session",
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
        assert memory.domain == MemoryDomain.SESSION
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


class TestMemoryDomain:
    """記憶ドメインのテスト"""
    
    def test_domain_values(self):
        """ドメイン値をテスト"""
        assert MemoryDomain.GLOBAL.value == "global"
        assert MemoryDomain.USER.value == "user" 
        assert MemoryDomain.PROJECT.value == "project"
        assert MemoryDomain.SESSION.value == "session"
    
    def test_domain_from_string(self):
        """文字列からドメイン作成をテスト"""
        assert MemoryDomain("global") == MemoryDomain.GLOBAL
        assert MemoryDomain("user") == MemoryDomain.USER
        assert MemoryDomain("project") == MemoryDomain.PROJECT
        assert MemoryDomain("session") == MemoryDomain.SESSION
        
        with pytest.raises(ValueError):
            MemoryDomain("invalid")


class TestMemoryStats:
    """記憶統計のテスト"""
    
    def test_stats_creation(self):
        """統計の作成をテスト"""
        stats = MemoryStats(
            total_count=100,
            domain_counts={"user": 50, "project": 30, "global": 20},
            tag_counts={"test": 10, "example": 5}
        )
        
        assert stats.total_count == 100
        assert stats.domain_counts["user"] == 50
        assert stats.tag_counts["test"] == 10
        assert isinstance(stats.last_updated, datetime)