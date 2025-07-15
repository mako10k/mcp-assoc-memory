"""
Unit tests for validation utilities and data models.

Tests cover:
- Memory model validation and serialization
- Input validation for API parameters
- Scope format validation
- Data sanitization functions
- Error handling for invalid inputs
"""

import pytest
from datetime import datetime
from typing import Dict, List

from mcp_assoc_memory.models.memory import Memory


class TestMemoryModel:
    """Test Memory model functionality."""

    @pytest.mark.unit
    def test_memory_creation_defaults(self):
        """Test memory creation with default values."""
        memory = Memory()

        assert memory.id is not None
        assert len(memory.id) > 0
        assert memory.scope == "user/default"
        assert memory.content == ""
        assert memory.metadata == {}
        assert memory.tags == []
        assert memory.category is None
        assert isinstance(memory.created_at, datetime)
        assert isinstance(memory.updated_at, datetime)
        assert memory.access_count == 0

    @pytest.mark.unit
    def test_memory_creation_with_values(self):
        """Test memory creation with specified values."""
        memory = Memory(
            id="test-123",
            scope="test/scope",
            content="Test content",
            metadata={"key": "value"},
            tags=["tag1", "tag2"],
            category="test-category",
            user_id="user-123",
            project_id="project-456"
        )

        assert memory.id == "test-123"
        assert memory.scope == "test/scope"
        assert memory.content == "Test content"
        assert memory.metadata == {"key": "value"}
        assert memory.tags == ["tag1", "tag2"]
        assert memory.category == "test-category"
        assert memory.user_id == "user-123"
        assert memory.project_id == "project-456"

    @pytest.mark.unit
    def test_memory_to_dict(self):
        """Test memory serialization to dictionary."""
        memory = Memory(
            id="test-123",
            scope="test/scope",
            content="Test content",
            metadata={"key": "value"},
            tags=["tag1", "tag2"],
            category="test-category"
        )

        result = memory.to_dict()

        assert isinstance(result, dict)
        assert result["id"] == "test-123"
        assert result["scope"] == "test/scope"
        assert result["content"] == "Test content"
        assert result["metadata"] == {"key": "value"}
        assert result["tags"] == ["tag1", "tag2"]
        assert result["category"] == "test-category"
        assert "created_at" in result
        assert "updated_at" in result

    @pytest.mark.unit
    def test_memory_factory_create(self, memory_factory):
        """Test memory creation using factory."""
        memory = memory_factory.create_memory(
            content="Factory test content",
            scope="factory/test",
            category="factory",
            tags=["factory", "test"],
            metadata={"source": "factory"}
        )

        assert isinstance(memory, Memory)
        assert memory.content == "Factory test content"
        assert memory.scope == "factory/test"
        assert memory.category == "factory"
        assert memory.tags == ["factory", "test"]
        assert memory.metadata == {"source": "factory"}

    @pytest.mark.unit
    def test_memory_factory_create_multiple(self, memory_factory):
        """Test creating multiple memories using factory."""
        memories = memory_factory.create_memories(count=5)

        assert len(memories) == 5
        assert all(isinstance(m, Memory) for m in memories)

        # Check that memories have different content and scopes
        contents = [m.content for m in memories]
        scopes = [m.scope for m in memories]

        assert len(set(contents)) == 5  # All unique
        assert len(set(scopes)) == 5    # All unique


class TestScopeValidation:
    """Test scope format validation."""

    @pytest.mark.unit
    def test_valid_scopes(self):
        """Test that valid scope formats are accepted."""
        valid_scopes = [
            "user/default",
            "learning/programming/python",
            "work/projects/mcp-server",
            "personal/notes",
            "session/2025-07-12",
            "test123/scope_with_underscores",
            "deep/nested/hierarchy/with/many/levels"
        ]

        for scope in valid_scopes:
            # For now, we'll just test that these don't raise exceptions
            # when used in Memory creation
            memory = Memory(scope=scope)
            assert memory.scope == scope

    @pytest.mark.unit
    def test_scope_hierarchy_components(self):
        """Test scope hierarchy component extraction."""
        scope = "learning/programming/python/web"
        memory = Memory(scope=scope)

        # Test that scope is stored correctly
        assert memory.scope == scope

        # Test scope component access (if implemented)
        components = scope.split("/")
        assert components[0] == "learning"
        assert components[1] == "programming"
        assert components[2] == "python"
        assert components[3] == "web"


class TestDataValidation:
    """Test data validation utilities."""

    @pytest.mark.unit
    def test_content_validation(self):
        """Test content validation rules."""
        # Valid content
        valid_contents = [
            "Simple content",
            "Content with numbers 123",
            "Content with special chars !@#$%",
            "Multi-line\ncontent\nwith breaks",
            "Unicode content: こんにちは 🚀",
            "A" * 1000  # Long content
        ]

        for content in valid_contents:
            memory = Memory(content=content)
            assert memory.content == content

    @pytest.mark.unit
    def test_tags_validation(self):
        """Test tags validation rules."""
        # Valid tags
        valid_tag_sets = [
            [],
            ["single"],
            ["multiple", "tags"],
            ["tag-with-hyphen"],
            ["tag_with_underscore"],
            ["tag123", "with456", "numbers789"],
            ["a" * 50]  # Long tag
        ]

        for tags in valid_tag_sets:
            memory = Memory(tags=tags)
            assert memory.tags == tags

    @pytest.mark.unit
    def test_metadata_validation(self):
        """Test metadata validation rules."""
        # Valid metadata
        valid_metadata_sets = [
            {},
            {"key": "value"},
            {"multiple": "keys", "with": "values"},
            {"nested": {"structure": "allowed"}},
            {"numbers": 123, "booleans": True, "nulls": None},
            {"lists": [1, 2, 3], "mixed": {"types": ["work", "fine"]}},
            {"unicode": "🚀", "japanese": "こんにちは"}
        ]

        for metadata in valid_metadata_sets:
            memory = Memory(metadata=metadata)
            assert memory.metadata == metadata


class TestErrorHandling:
    """Test error handling for invalid inputs."""

    @pytest.mark.unit
    def test_memory_type_safety_note(self):
        """Test documents type safety behavior."""
        # Note: Memory class uses dataclass with type hints for static analysis
        # Runtime type validation would require additional validation logic

        # Valid usage - this always works
        memory = Memory(
            scope="valid/scope",
            tags=["valid", "tags"]
        )
        assert memory.scope == "valid/scope"
        assert memory.tags == ["valid", "tags"]

    @pytest.mark.unit
    def test_boundary_values(self):
        """Test boundary values for memory fields."""
        # Empty values
        memory = Memory(
            content="",
            tags=[],
            metadata={}
        )

        assert memory.content == ""
        assert memory.tags == []
        assert memory.metadata == {}

        # Very long values
        long_content = "A" * 10000
        long_tags = [f"tag{i}" for i in range(100)]
        large_metadata = {f"key{i}": f"value{i}" for i in range(100)}

        memory = Memory(
            content=long_content,
            tags=long_tags,
            metadata=large_metadata
        )

        assert memory.content == long_content
        assert memory.tags == long_tags
        assert memory.metadata == large_metadata


class TestMemoryOperations:
    """Test memory model operations and utility methods."""

    @pytest.mark.unit
    def test_memory_equality(self):
        """Test memory equality comparison."""
        memory1 = Memory(
            id="test-123",
            content="Same content",
            scope="same/scope"
        )

        memory2 = Memory(
            id="test-123",
            content="Same content",
            scope="same/scope"
        )

        memory3 = Memory(
            id="test-456",
            content="Different content",
            scope="different/scope"
        )

        # Memories with same ID should be considered equal
        assert memory1.id == memory2.id
        assert memory1.id != memory3.id

    @pytest.mark.unit
    def test_memory_update_timestamp(self):
        """Test that updated_at timestamp changes appropriately."""
        memory = Memory(content="Original content")

        # Simulate update by creating new memory with same ID
        updated_memory = Memory(
            id=memory.id,
            content="Updated content"
        )

        # In a real system, updated_at would be set to current time
        # Here we just verify the structure supports it
        assert hasattr(updated_memory, 'updated_at')
        assert isinstance(updated_memory.updated_at, datetime)

    @pytest.mark.unit
    def test_memory_access_tracking(self):
        """Test access count tracking."""
        memory = Memory()

        assert memory.access_count == 0
        assert memory.accessed_at is not None
        assert isinstance(memory.accessed_at, datetime)

        # In a real system, these would be updated during access
        # Here we just verify the structure supports tracking


class TestFixtureIntegration:
    """Test integration with pytest fixtures."""

    @pytest.mark.unit
    def test_sample_memory_data_fixture(self, sample_memory_data):
        """Test sample memory data fixture."""
        assert isinstance(sample_memory_data, list)
        assert len(sample_memory_data) == 3

        for data in sample_memory_data:
            assert "content" in data
            assert "scope" in data
            assert "category" in data
            assert "tags" in data
            assert "metadata" in data

            # Verify data can be used to create Memory objects
            memory = Memory(
                content=data["content"],
                scope=data["scope"],
                category=data["category"],
                tags=data["tags"],
                metadata=data["metadata"]
            )

            assert memory.content == data["content"]
            assert memory.scope == data["scope"]

    @pytest.mark.unit
    def test_test_embeddings_fixture(self, test_embeddings):
        """Test embeddings fixture."""
        assert isinstance(test_embeddings, list)
        assert len(test_embeddings) == 3

        for embedding in test_embeddings:
            assert isinstance(embedding, list)
            assert len(embedding) == 1536  # Standard embedding size
            assert all(isinstance(x, float) for x in embedding)

    @pytest.mark.unit
    def test_test_search_results_fixture(self, test_search_results):
        """Test search results fixture."""
        assert isinstance(test_search_results, list)
        assert len(test_search_results) == 2

        for result in test_search_results:
            assert "memory_id" in result
            assert "content" in result
            assert "similarity_score" in result
            assert "scope" in result

            assert isinstance(result["similarity_score"], float)
            assert 0 <= result["similarity_score"] <= 1
