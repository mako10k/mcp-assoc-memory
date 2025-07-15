"""
Tests for memory_list_all response level functionality
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from mcp_assoc_memory.api.models.requests import MemoryListAllRequest
from mcp_assoc_memory.api.models.common import ResponseLevel
from mcp_assoc_memory.api.tools.memory_tools import handle_memory_list_all


@pytest.mark.asyncio
async def test_memory_list_all_minimal_response():
    """Test memory listing with minimal response level"""
    async with AsyncMock() as mock_context:
        request = MemoryListAllRequest(
            page=1,
            per_page=10,
            response_level=ResponseLevel.MINIMAL
        )

        # Mock the singleton memory manager to prevent actual initialization
        with patch('mcp_assoc_memory.core.singleton_memory_manager.get_or_create_memory_manager') as mock_singleton:
            mock_memory_manager = MagicMock()
            
            # Mock the actual methods called in handle_memory_list_all
            mock_memory_manager.get_all_memories = AsyncMock(return_value=[])
            mock_singleton.return_value = mock_memory_manager

            result = await handle_memory_list_all(request, mock_context)

            assert result["success"] is True
            assert result["total_count"] == 0
            # Minimal response should only have essential pagination data
            assert "page" in result
            assert "per_page" in result
            assert "total_pages" in result
            # Should not include memories details in minimal
            assert "memories" not in result or len(result.get("memories", [])) == 0


@pytest.mark.asyncio
async def test_memory_list_all_standard_response():
    """Test memory listing with standard response level"""
    async with AsyncMock() as mock_context:
        request = MemoryListAllRequest(
            page=1,
            per_page=10,
            response_level=ResponseLevel.STANDARD
        )

        with patch('mcp_assoc_memory.api.tools.memory_tools.ensure_initialized') as mock_init:
            mock_memory_manager = MagicMock()
            
            # Mock memory data
            mock_memory = MagicMock()
            mock_memory.id = "memory-123"
            mock_memory.content = "Test content"
            mock_memory.scope = "test/scope"
            mock_memory.tags = []
            mock_memory.category = None
            mock_memory.created_at = datetime.now()
            mock_memory.updated_at = datetime.now()
            mock_memory.metadata = {}
            
            mock_memory_manager.get_all_memories = AsyncMock(return_value=[mock_memory])
            mock_init.return_value = mock_memory_manager

            result = await handle_memory_list_all(request, mock_context)

            assert result["success"] is True
            assert result["total_count"] == 1
            # Standard response should include memories and pagination
            assert "memories" in result
            assert "pagination" in result
            assert len(result["memories"]) == 1


@pytest.mark.asyncio
async def test_memory_list_all_full_response():
    """Test memory listing with full response level"""
    async with AsyncMock() as mock_context:
        request = MemoryListAllRequest(
            page=1,
            per_page=10,
            response_level=ResponseLevel.FULL
        )

        with patch('mcp_assoc_memory.api.tools.memory_tools.ensure_initialized') as mock_init:
            mock_memory_manager = MagicMock()
            
            # Mock memory data
            mock_memory = MagicMock()
            mock_memory.id = "memory-123"
            mock_memory.content = "Test content"
            mock_memory.scope = "test/scope"
            mock_memory.tags = []
            mock_memory.category = None
            mock_memory.created_at = datetime.now()
            mock_memory.updated_at = datetime.now()
            mock_memory.metadata = {}
            
            mock_memory_manager.get_all_memories = AsyncMock(return_value=[mock_memory])
            mock_init.return_value = mock_memory_manager

            result = await handle_memory_list_all(request, mock_context)

            assert result["success"] is True
            assert result["total_count"] == 1
            # Full response should include memories, pagination, and metadata
            assert "memories" in result
            assert "pagination" in result
            assert "search_metadata" in result
            # Should include full metadata details
            metadata = result["search_metadata"]
            assert "request_type" in metadata
            assert "timestamp" in metadata
            assert metadata["request_type"] == "memory_list_all"


@pytest.mark.asyncio
async def test_memory_list_all_error_response():
    """Test memory listing error handling with response levels"""
    async with AsyncMock() as mock_context:
        request = MemoryListAllRequest(
            page=1,
            per_page=10,
            response_level=ResponseLevel.STANDARD
        )

        with patch('mcp_assoc_memory.api.tools.memory_tools.ensure_initialized') as mock_init:
            # Mock error condition
            mock_init.side_effect = Exception("Test error")

            result = await handle_memory_list_all(request, mock_context)

            assert result["success"] is False
            assert "Failed to list memories" in result["message"]
            assert result["total_count"] == 0


@pytest.mark.asyncio
async def test_memory_list_all_pagination():
    """Test memory listing pagination logic"""
    async with AsyncMock() as mock_context:
        request = MemoryListAllRequest(
            page=2,
            per_page=5,
            response_level=ResponseLevel.STANDARD
        )

        with patch('mcp_assoc_memory.api.tools.memory_tools.ensure_initialized') as mock_init:
            mock_memory_manager = MagicMock()
            
            # Mock total of 12 memories, but only return the 5 for page 2
            mock_memories = []
            for i in range(5):  # Second page would have 5 memories (memories 5-9)
                mock_memory = MagicMock()
                mock_memory.id = f"memory-{i+5}"
                mock_memory.content = f"Test content {i+5}"
                mock_memory.scope = "test/scope"
                mock_memory.tags = []
                mock_memory.category = None
                mock_memory.created_at = datetime.now()
                mock_memory.updated_at = datetime.now()
                mock_memory.metadata = {}
                mock_memories.append(mock_memory)
            
            # We'll mock that get_all_memories returns all 12 but the logic will slice
            all_memories = []
            for i in range(12):
                mock_memory = MagicMock()
                mock_memory.id = f"memory-{i}"
                mock_memory.content = f"Test content {i}"
                mock_memory.scope = "test/scope"
                mock_memory.tags = []
                mock_memory.category = None
                mock_memory.created_at = datetime.now()
                mock_memory.updated_at = datetime.now()
                mock_memory.metadata = {}
                all_memories.append(mock_memory)
            
            mock_memory_manager.get_all_memories = AsyncMock(return_value=all_memories)
            mock_init.return_value = mock_memory_manager

            result = await handle_memory_list_all(request, mock_context)

            assert result["success"] is True
            assert result["total_count"] == 12
            assert len(result["memories"]) == 5  # Page 2 should have 5 memories
            
            # Check pagination info
            pagination = result["pagination"]
            assert pagination["current_page"] == 2
            assert pagination["per_page"] == 5
            assert pagination["total_pages"] == 3  # 12 memories / 5 per page = 3 pages
            assert pagination["has_next"] is True
            assert pagination["has_previous"] is True
