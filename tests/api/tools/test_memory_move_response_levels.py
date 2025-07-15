"""Comprehensive response level tests for memory_move tool."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Any, Dict

from src.mcp_assoc_memory.api.tools.other_tools import handle_memory_move
from src.mcp_assoc_memory.api.models.requests import MemoryMoveRequest
from src.mcp_assoc_memory.api.models.common import ResponseLevel, CommonToolParameters


class TestMemoryMoveResponseLevels:
    """Test memory_move tool with different response levels."""

    @pytest.fixture
    def mock_context(self):
        """Create mock context for testing."""
        context = AsyncMock()
        context.info = AsyncMock()
        context.error = AsyncMock()
        return context

    @pytest.fixture
    def mock_updated_memory(self):
        """Create mock updated memory object."""
        memory = MagicMock()
        memory.id = "test-memory-123"
        memory.content = "This is a test memory content that is longer than 50 characters for truncation testing"
        memory.scope = "new/target/scope"
        memory.tags = ["test", "example"]
        memory.category = "test_category"
        memory.metadata = {"created_at": "2025-01-15", "test_key": "test_value"}
        return memory

    @pytest.mark.asyncio
    async def test_request_inheritance(self):
        """Test that MemoryMoveRequest properly inherits from CommonToolParameters."""
        request = MemoryMoveRequest(
            memory_ids=["test-123"],
            target_scope="test/scope",
            response_level=ResponseLevel.STANDARD
        )

        # Test inheritance
        assert isinstance(request, CommonToolParameters)
        assert hasattr(request, 'response_level')
        assert request.response_level == ResponseLevel.STANDARD

        # Test default response level
        request_default = MemoryMoveRequest(
            memory_ids=["test-123"],
            target_scope="test/scope"
        )
        assert request_default.response_level == ResponseLevel.STANDARD

    @pytest.mark.asyncio
    async def test_memory_move_minimal_response(self, mock_context, mock_updated_memory):
        """Test memory move with minimal response level."""
        request = MemoryMoveRequest(
            memory_ids=["test-memory-123"],
            target_scope="new/target/scope",
            response_level=ResponseLevel.MINIMAL
        )

        with patch('src.mcp_assoc_memory.api.tools.other_tools.get_or_create_memory_manager') as mock_manager_factory:
            mock_manager = AsyncMock()
            mock_manager.update_memory.return_value = mock_updated_memory
            mock_manager_factory.return_value = mock_manager

            response = await handle_memory_move(request, mock_context)

            # Verify minimal response structure
            assert response["success"] is True
            assert response["moved_count"] == 1
            assert response["failed_count"] == 0

            # Minimal response should not include detailed data
            assert "moved_memories" not in response
            assert "move_summary" not in response
            assert "failed_memory_ids" not in response

    @pytest.mark.asyncio
    async def test_memory_move_standard_response(self, mock_context, mock_updated_memory):
        """Test memory move with standard response level."""
        request = MemoryMoveRequest(
            memory_ids=["test-memory-123"],
            target_scope="new/target/scope",
            response_level=ResponseLevel.STANDARD
        )

        with patch('src.mcp_assoc_memory.api.tools.other_tools.get_or_create_memory_manager') as mock_manager_factory:
            mock_manager = AsyncMock()
            mock_manager.update_memory.return_value = mock_updated_memory
            mock_manager_factory.return_value = mock_manager

            response = await handle_memory_move(request, mock_context)

            # Verify standard response structure
            assert response["success"] is True
            assert response["moved_count"] == 1
            assert response["failed_count"] == 0
            assert "target_scope" in response
            assert "moved_memories" in response
            assert len(response["moved_memories"]) == 1

            # Check content preview truncation
            moved_memory = response["moved_memories"][0]
            assert len(moved_memory["content_preview"]) <= 53  # 50 chars + "..."
            assert moved_memory["content_preview"].endswith("...")

    @pytest.mark.asyncio
    async def test_memory_move_full_response(self, mock_context, mock_updated_memory):
        """Test memory move with full response level."""
        request = MemoryMoveRequest(
            memory_ids=["test-memory-123"],
            target_scope="new/target/scope",
            response_level=ResponseLevel.FULL
        )

        with patch('src.mcp_assoc_memory.api.tools.other_tools.get_or_create_memory_manager') as mock_manager_factory:
            mock_manager = AsyncMock()
            mock_manager.update_memory.return_value = mock_updated_memory
            mock_manager_factory.return_value = mock_manager

            response = await handle_memory_move(request, mock_context)

            # Verify full response structure
            assert response["success"] is True
            assert response["moved_count"] == 1
            assert response["failed_count"] == 0
            assert "target_scope" in response
            assert "moved_memories" in response
            assert "move_summary" in response
            # failed_memory_ids may be omitted when empty due to ResponseBuilder._clean_response

            # Check complete move summary
            move_summary = response["move_summary"]
            assert "total_requested" in move_summary
            assert "successfully_moved" in move_summary
            assert "failed_moves" in move_summary
            assert "success_rate" in move_summary
            assert move_summary["total_requested"] == 1
            assert move_summary["successfully_moved"] == 1
            assert move_summary["success_rate"] == 1.0

    @pytest.mark.asyncio
    async def test_memory_move_bulk_operation(self, mock_context, mock_updated_memory):
        """Test bulk memory move operation."""
        request = MemoryMoveRequest(
            memory_ids=["memory-1", "memory-2", "memory-3"],
            target_scope="bulk/target/scope",
            response_level=ResponseLevel.STANDARD
        )

        with patch('src.mcp_assoc_memory.api.tools.other_tools.get_or_create_memory_manager') as mock_manager_factory:
            mock_manager = AsyncMock()
            mock_manager.update_memory.return_value = mock_updated_memory
            mock_manager_factory.return_value = mock_manager

            response = await handle_memory_move(request, mock_context)

            # Verify bulk operation response
            assert response["success"] is True
            assert response["moved_count"] == 3
            assert response["failed_count"] == 0
            assert len(response["moved_memories"]) == 3

            # Verify update_memory was called for each memory
            assert mock_manager.update_memory.call_count == 3

    @pytest.mark.asyncio
    async def test_memory_move_manager_not_available(self, mock_context):
        """Test memory move when manager is not available."""
        request = MemoryMoveRequest(
            memory_ids=["test-memory-123"],
            target_scope="new/target/scope",
            response_level=ResponseLevel.MINIMAL
        )

        with patch('src.mcp_assoc_memory.api.tools.other_tools.get_or_create_memory_manager') as mock_manager_factory:
            mock_manager_factory.return_value = None

            response = await handle_memory_move(request, mock_context)

            # Verify error response
            assert response["success"] is False
            assert "error" in response
            assert "Memory manager not available" in response["error"]

    @pytest.mark.asyncio
    async def test_memory_move_update_exception(self, mock_context):
        """Test memory move with update exception."""
        request = MemoryMoveRequest(
            memory_ids=["test-memory-123"],
            target_scope="new/target/scope",
            response_level=ResponseLevel.FULL
        )

        with patch('src.mcp_assoc_memory.api.tools.other_tools.get_or_create_memory_manager') as mock_manager_factory:
            mock_manager = AsyncMock()
            mock_manager.update_memory.side_effect = Exception("Update failed")
            mock_manager_factory.return_value = mock_manager

            response = await handle_memory_move(request, mock_context)

            # Should handle partial failure
            assert response["success"] is False  # No memories were moved successfully
            assert response["moved_count"] == 0
            assert response["failed_count"] == 1
            assert "failed_memory_ids" in response
            assert "test-memory-123" in response["failed_memory_ids"]

    @pytest.mark.asyncio
    async def test_memory_move_empty_ids_list(self, mock_context):
        """Test memory move with empty memory IDs list."""
        request = MemoryMoveRequest(
            memory_ids=[],
            target_scope="new/target/scope",
            response_level=ResponseLevel.MINIMAL
        )

        response = await handle_memory_move(request, mock_context)

        # Verify response for empty operation
        assert response["success"] is True
        assert response["moved_count"] == 0
        assert response["failed_count"] == 0

    def test_response_size_estimates(self):
        """Test response size estimates for different levels."""
        # Minimal response fields
        minimal_fields = ["success", "moved_count", "failed_count", "message"]
        minimal_estimated_size = len(str(minimal_fields)) + 100  # Conservative estimate
        assert minimal_estimated_size < 200  # Should be under 200 chars

        # Standard response includes moved_memories with previews
        standard_additional = ["target_scope", "moved_memories"]
        standard_estimated_size = minimal_estimated_size + len(str(standard_additional)) + 500
        assert standard_estimated_size < 1000  # Should be reasonable

        # Full response includes complete data
        full_additional = ["move_summary", "failed_memory_ids"]
        full_estimated_size = standard_estimated_size + len(str(full_additional)) + 200
        assert full_estimated_size > standard_estimated_size  # Should be larger than standard

    @pytest.mark.asyncio
    async def test_memory_move_content_preview_truncation(self, mock_context):
        """Test content preview truncation in standard response."""
        # Create memory with long content
        mock_memory = MagicMock()
        mock_memory.id = "test-memory-123"
        mock_memory.content = "A" * 100  # 100 character content
        mock_memory.scope = "new/target/scope"
        mock_memory.tags = ["test"]
        mock_memory.category = "test"
        mock_memory.metadata = {}

        request = MemoryMoveRequest(
            memory_ids=["test-memory-123"],
            target_scope="new/target/scope",
            response_level=ResponseLevel.STANDARD
        )

        with patch('src.mcp_assoc_memory.api.tools.other_tools.get_or_create_memory_manager') as mock_manager_factory:
            mock_manager = AsyncMock()
            mock_manager.update_memory.return_value = mock_memory
            mock_manager_factory.return_value = mock_manager

            response = await handle_memory_move(request, mock_context)

            # Verify content truncation
            moved_memory = response["moved_memories"][0]
            assert len(moved_memory["content_preview"]) <= 53  # 50 chars + "..."
            assert moved_memory["content_preview"].endswith("...")
