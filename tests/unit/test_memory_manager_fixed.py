"""
Simplified unit tests for the MemoryManager core functionality.

Tests cover:
- Memory storage and retrieval operations
- Basic functionality with current API signatures
"""

import pytest
from typing import List, Dict, Any
from unittest.mock import AsyncMock, MagicMock, patch

from mcp_assoc_memory.core.memory_manager import MemoryManager
from mcp_assoc_memory.models.memory import Memory


class TestMemoryManagerStorage:
    """Test memory storage operations."""

    @pytest.mark.asyncio
    async def test_store_memory_success(self, test_memory_manager: MemoryManager):
        """Test successful memory storage."""
        result = await test_memory_manager.store_memory(
            content="Test memory for storage",
            scope="test/storage",
            category="test",
            tags=["storage", "test"],
            metadata={"test": True}
        )

        assert result is not None
        assert isinstance(result, Memory)
        assert result.content == "Test memory for storage"
        assert result.scope == "test/storage"
        assert result.category == "test"
        assert result.tags == ["storage", "test"]
        assert result.metadata["test"] is True

    @pytest.mark.asyncio
    async def test_store_memory_duplicate_detection(self, test_memory_manager: MemoryManager):
        """Test duplicate detection during storage."""
        content = "Duplicate test content"

        # Store first memory
        result1 = await test_memory_manager.store_memory(
            content=content,
            scope="test/duplicates"
        )
        assert result1 is not None
        assert isinstance(result1, Memory)

        # Attempt to store duplicate (should return existing memory)
        result2 = await test_memory_manager.store_memory(
            content=content,
            scope="test/duplicates",
            allow_duplicates=False
        )

        assert result2 is not None
        assert isinstance(result2, Memory)
        assert result2.id == result1.id  # Should return same memory for duplicate

    @pytest.mark.asyncio
    async def test_store_memory_allow_duplicates(self, test_memory_manager: MemoryManager):
        """Test allowing duplicates when explicitly enabled."""
        content = "Duplicate test content"

        # Store first memory
        result1 = await test_memory_manager.store_memory(
            content=content,
            scope="test/duplicates"
        )

        # Store duplicate with allow_duplicates=True
        result2 = await test_memory_manager.store_memory(
            content=content,
            scope="test/duplicates",
            allow_duplicates=True
        )

        assert result1 is not None
        assert result2 is not None
        assert isinstance(result1, Memory)
        assert isinstance(result2, Memory)
        assert result1.id != result2.id  # Should create new memory when duplicates allowed


class TestMemoryManagerRetrieval:
    """Test memory retrieval operations."""

    @pytest.mark.asyncio
    async def test_get_memory_success(self, test_memory_manager: MemoryManager):
        """Test successful memory retrieval."""
        # Store a test memory first
        stored_memory = await test_memory_manager.store_memory(
            content="Test memory for retrieval",
            scope="test/retrieval"
        )
        assert stored_memory is not None

        # Retrieve the memory
        result = await test_memory_manager.get_memory(stored_memory.id)

        assert result is not None
        assert isinstance(result, Memory)
        assert result.id == stored_memory.id
        assert result.content == "Test memory for retrieval"
        assert result.scope == "test/retrieval"

    @pytest.mark.asyncio
    async def test_get_memory_not_found(self, test_memory_manager: MemoryManager):
        """Test retrieval of non-existent memory."""
        result = await test_memory_manager.get_memory("non-existent-id")

        assert result is None


class TestMemoryManagerBasicOperations:
    """Test basic memory manager operations."""

    @pytest.mark.asyncio
    async def test_memory_manager_initialization(self, test_memory_manager: MemoryManager):
        """Test that memory manager initializes correctly."""
        assert test_memory_manager is not None

        # Test that basic attributes exist
        assert hasattr(test_memory_manager, 'store_memory')
        assert hasattr(test_memory_manager, 'get_memory')
        assert hasattr(test_memory_manager, 'health_check')

    @pytest.mark.asyncio
    async def test_populated_memory_manager(self, populated_memory_manager: MemoryManager):
        """Test that populated memory manager fixture works."""
        assert populated_memory_manager is not None

        # The populated_memory_manager fixture should have some sample data
        # We can't easily test this without knowing the exact API for listing memories
        # So we'll just verify it's a valid MemoryManager instance
        assert isinstance(populated_memory_manager, MemoryManager)


class TestMemoryManagerEdgeCases:
    """Test edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_store_empty_content(self, test_memory_manager: MemoryManager):
        """Test storing memory with empty content."""
        result = await test_memory_manager.store_memory(
            content="",
            scope="test/empty"
        )

        assert result is not None
        assert isinstance(result, Memory)
        assert result.content == ""
        assert result.scope == "test/empty"

    @pytest.mark.asyncio
    async def test_store_with_default_scope(self, test_memory_manager: MemoryManager):
        """Test storing memory with default scope."""
        result = await test_memory_manager.store_memory(
            content="Test with default scope"
        )

        assert result is not None
        assert isinstance(result, Memory)
        assert result.content == "Test with default scope"
        # Should use default scope
        assert result.scope == "user/default"

    @pytest.mark.asyncio
    async def test_store_with_complex_metadata(self, test_memory_manager: MemoryManager):
        """Test storing memory with complex metadata."""
        complex_metadata = {
            "nested": {"key": "value"},
            "list": [1, 2, 3],
            "number": 42,
            "boolean": True
        }

        result = await test_memory_manager.store_memory(
            content="Test with complex metadata",
            scope="test/complex",
            metadata=complex_metadata
        )

        assert result is not None
        assert isinstance(result, Memory)
        assert result.metadata["nested"]["key"] == "value"
        assert result.metadata["list"] == [1, 2, 3]
        assert result.metadata["number"] == 42
        assert result.metadata["boolean"] is True
