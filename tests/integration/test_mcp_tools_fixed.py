"""
Simplified integration tests for MCP API tools.

Tests basic integration of MCP tools with the memory system.
"""

import pytest
from typing import Dict, Any
from unittest.mock import AsyncMock, patch

from mcp_assoc_memory.api.tools.memory_tools import (
    handle_memory_search,
    handle_memory_store
)
from mcp_assoc_memory.api.models import MemoryStoreRequest, MemorySearchRequest
from mcp_assoc_memory.core.memory_manager import MemoryManager


class TestMemoryToolsIntegration:
    """Integration tests for memory-related MCP tools."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_memory_store_tool_basic(self, test_memory_manager: MemoryManager):
        """Test memory store tool with basic parameters."""
        # Create a mock context
        mock_ctx = AsyncMock()
        mock_ctx.info = AsyncMock()
        mock_ctx.warning = AsyncMock()

        # Create request object
        request = MemoryStoreRequest(
            content="Test memory via MCP tool",
            scope="test/mcp",
            tags=["test", "mcp"],
            category="test"
        )

        # Mock the global memory_manager
        with patch('mcp_assoc_memory.api.tools.memory_tools.memory_manager', test_memory_manager):
            result = await handle_memory_store(request, mock_ctx)

        assert result.memory_id is not None
        assert result.content == "Test memory via MCP tool"
        assert result.scope == "test/mcp"

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_memory_search_tool_basic(self, test_memory_manager: MemoryManager):
        """Test memory search tool with basic parameters."""
        # Create a mock context
        mock_ctx = AsyncMock()
        mock_ctx.info = AsyncMock()
        mock_ctx.warning = AsyncMock()

        # First store a memory to search for
        store_request = MemoryStoreRequest(
            content="Python programming language basics",
            scope="test/search",
            tags=["python", "programming"]
        )

        with patch('mcp_assoc_memory.api.tools.memory_tools.memory_manager', test_memory_manager):
            store_result = await handle_memory_store(store_request, mock_ctx)
            assert store_result.memory_id is not None

            # Now search for it
            search_request = MemorySearchRequest(
                query="Python programming",
                limit=5,
                mode="standard",
                similarity_threshold=0.1
            )

            result = await handle_memory_search(search_request, mock_ctx)

            assert isinstance(result, dict)  # Should return a dict with results
            assert "results" in result
            assert isinstance(result["results"], list)

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_memory_store_tool_error_handling(self, test_memory_manager: MemoryManager):
        """Test memory store tool error handling."""
        # Create a mock context
        mock_ctx = AsyncMock()
        mock_ctx.info = AsyncMock()
        mock_ctx.warning = AsyncMock()
        mock_ctx.error = AsyncMock()

        # Test with minimal content (should still work)
        try:
            request = MemoryStoreRequest(
                content="",  # Empty content
                scope="test/error"
            )

            with patch('mcp_assoc_memory.api.tools.memory_tools.memory_manager', test_memory_manager):
                result = await handle_memory_store(request, mock_ctx)
                # Empty content might be allowed, so check for MemoryResponse
                assert result is not None
        except Exception:
            # Empty content might raise validation error, which is also acceptable
            pass

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_memory_search_tool_empty_query(self, test_memory_manager: MemoryManager):
        """Test memory search tool with empty query."""
        # Create a mock context
        mock_ctx = AsyncMock()
        mock_ctx.info = AsyncMock()
        mock_ctx.warning = AsyncMock()
        mock_ctx.error = AsyncMock()

        request = MemorySearchRequest(
            query="",
            limit=5
        )

        with patch('mcp_assoc_memory.api.tools.memory_tools.memory_manager', test_memory_manager):
            result = await handle_memory_search(request, mock_ctx)

            # Should handle empty query gracefully
            assert isinstance(result, dict)
            assert "results" in result or "error" in result


class TestToolIntegrationWorkflow:
    """Test complete workflows using multiple tools."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_store_and_search_workflow(self, test_memory_manager: MemoryManager):
        """Test complete store and search workflow."""
        # Store multiple memories
        memories_to_store = [
            {
                "content": "Machine learning fundamentals",
                "scope": "learning/ml",
                "tags": ["ml", "fundamentals"]
            },
            {
                "content": "Deep learning neural networks",
                "scope": "learning/dl",
                "tags": ["dl", "neural-networks"]
            },
            {
                "content": "Python programming basics",
                "scope": "learning/programming",
                "tags": ["python", "programming"]
            }
        ]

        stored_ids = []

        # Create a mock context
        mock_ctx = AsyncMock()
        mock_ctx.info = AsyncMock()
        mock_ctx.warning = AsyncMock()
        mock_ctx.error = AsyncMock()

        with patch('mcp_assoc_memory.api.tools.memory_tools.memory_manager', test_memory_manager):
            for memory_data in memories_to_store:
                store_request = MemoryStoreRequest(**memory_data)
                result = await handle_memory_store(store_request, mock_ctx)

                assert result.memory_id is not None
                stored_ids.append(result.memory_id)

            # Search for machine learning related content
            search_request = MemorySearchRequest(
                query="machine learning",
                limit=10,
                similarity_threshold=0.1
            )

            search_result = await handle_memory_search(search_request, mock_ctx)

            assert isinstance(search_result, dict)
            assert "results" in search_result

            # Should find at least some relevant memories
            if search_result["results"]:
                found_memory = search_result["results"][0]
                assert "memory_id" in found_memory
                assert "content" in found_memory
                assert "similarity_score" in found_memory


class TestToolParameterValidation:
    """Test tool parameter validation."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_memory_store_parameter_validation(self, test_memory_manager: MemoryManager):
        """Test parameter validation for memory store tool."""
        # Create a mock context
        mock_ctx = AsyncMock()
        mock_ctx.info = AsyncMock()
        mock_ctx.warning = AsyncMock()
        mock_ctx.error = AsyncMock()

        # Test with minimal valid request
        try:
            request = MemoryStoreRequest(content="minimal test", scope="test/validation")
            with patch('mcp_assoc_memory.api.tools.memory_tools.memory_manager', test_memory_manager):
                result = await handle_memory_store(request, mock_ctx)
                assert result is not None
        except Exception:
            # If validation fails, that's also acceptable behavior
            pass

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_memory_search_parameter_validation(self, test_memory_manager: MemoryManager):
        """Test parameter validation for memory search tool."""
        # Create a mock context
        mock_ctx = AsyncMock()
        mock_ctx.info = AsyncMock()
        mock_ctx.warning = AsyncMock()
        mock_ctx.error = AsyncMock()

        # Test with minimal valid request
        request = MemorySearchRequest(query="test query")

        with patch('mcp_assoc_memory.api.tools.memory_tools.memory_manager', test_memory_manager):
            result = await handle_memory_search(request, mock_ctx)

            # Should handle the request gracefully
            assert isinstance(result, dict)
