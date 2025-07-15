"""
Test suite for memory_manage tool response levels implementation
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from mcp_assoc_memory.api.models.requests import MemoryManageRequest
from mcp_assoc_memory.api.models.common import ResponseLevel
from mcp_assoc_memory.api.tools.memory_tools import handle_memory_manage


@pytest.fixture
def mock_context():
    """Mock context for testing."""
    mock_ctx = MagicMock()
    mock_ctx.info = AsyncMock()
    mock_ctx.error = AsyncMock()
    mock_ctx.warning = AsyncMock()
    return mock_ctx


@pytest.fixture
def mock_memory_data():
    """Mock memory data for testing."""
    return {
        "memory_id": "test-memory-123",
        "content": "This is test memory content for response level testing",
        "scope": "test/scope",
        "metadata": {"test": "data"},
        "tags": ["test", "memory"],
        "category": "test",
        "created_at": datetime.now(),
        "associations": [
            {
                "source_id": "test-memory-123",
                "target_id": "related-memory-456",
                "association_type": "semantic",
                "strength": 0.85,
                "auto_generated": True,
                "created_at": datetime.now()
            }
        ]
    }


class TestMemoryManageResponseLevels:
    """Test memory_manage response levels implementation."""

    @pytest.mark.asyncio
    async def test_memory_manage_request_inheritance(self):
        """Test that MemoryManageRequest inherits from CommonToolParameters."""
        request = MemoryManageRequest(
            operation="get",
            memory_id="test-123",
            response_level=ResponseLevel.STANDARD
        )

        # Should have response_level from CommonToolParameters
        assert hasattr(request, 'response_level')
        assert request.response_level == ResponseLevel.STANDARD
        assert hasattr(request, 'get_response_level')
        assert request.get_response_level() == ResponseLevel.STANDARD

    @pytest.mark.asyncio
    async def test_memory_manage_get_minimal_response(self, mock_context, mock_memory_data):
        """Test GET operation with minimal response level."""
        request = MemoryManageRequest(
            operation="get",
            memory_id="test-memory-123",
            response_level=ResponseLevel.MINIMAL
        )

        with patch('mcp_assoc_memory.api.tools.memory_tools.ensure_initialized') as mock_init:
            with patch('mcp_assoc_memory.api.tools.memory_tools.handle_memory_get') as mock_get:
                mock_init.return_value = AsyncMock()
                mock_get.return_value = mock_memory_data

                response = await handle_memory_manage(request, mock_context)

                # Verify minimal response structure
                assert response["success"] is True
                assert response["operation"] == "get"
                assert response["memory_id"] == "test-memory-123"
                assert "message" in response

                # Minimal level should not include memory details
                assert "memory" not in response

    @pytest.mark.asyncio
    async def test_memory_manage_get_standard_response(self, mock_context, mock_memory_data):
        """Test GET operation with standard response level."""
        request = MemoryManageRequest(
            operation="get",
            memory_id="test-memory-123",
            response_level=ResponseLevel.STANDARD
        )

        with patch('mcp_assoc_memory.api.tools.memory_tools.ensure_initialized') as mock_init:
            with patch('mcp_assoc_memory.api.tools.memory_tools.handle_memory_get') as mock_get:
                mock_init.return_value = AsyncMock()
                mock_get.return_value = mock_memory_data

                response = await handle_memory_manage(request, mock_context)

                # Verify standard response structure
                assert response["success"] is True
                assert response["operation"] == "get"
                assert response["memory_id"] == "test-memory-123"
                assert "memory" in response

                # Check memory preview structure
                memory = response["memory"]
                assert "memory_id" in memory
                assert "scope" in memory
                assert "content_preview" in memory
                assert len(memory["content_preview"]) <= 103  # 100 chars + "..."

    @pytest.mark.asyncio
    async def test_memory_manage_get_full_response(self, mock_context, mock_memory_data):
        """Test GET operation with full response level."""
        request = MemoryManageRequest(
            operation="get",
            memory_id="test-memory-123",
            response_level=ResponseLevel.FULL
        )

        with patch('mcp_assoc_memory.api.tools.memory_tools.ensure_initialized') as mock_init:
            with patch('mcp_assoc_memory.api.tools.memory_tools.handle_memory_get') as mock_get:
                mock_init.return_value = AsyncMock()
                mock_get.return_value = mock_memory_data

                response = await handle_memory_manage(request, mock_context)

                # Verify full response structure
                assert response["success"] is True
                assert response["operation"] == "get"
                assert response["memory_id"] == "test-memory-123"
                assert "memory" in response

                # Check complete memory structure
                memory = response["memory"]
                assert memory["memory_id"] == "test-memory-123"
                assert memory["content"] == mock_memory_data["content"]
                assert memory["scope"] == mock_memory_data["scope"]
                assert memory["metadata"] == mock_memory_data["metadata"]
                assert memory["tags"] == mock_memory_data["tags"]

    @pytest.mark.asyncio
    async def test_memory_manage_update_response_levels(self, mock_context):
        """Test UPDATE operation with different response levels."""
        request = MemoryManageRequest(
            operation="update",
            memory_id="test-memory-123",
            content="Updated content",
            scope="updated/scope",
            response_level=ResponseLevel.STANDARD
        )

        mock_update_response = MagicMock()
        mock_update_response.dict.return_value = {
            "success": True,
            "message": "Memory updated successfully",
            "memory_id": "test-memory-123",
            "content": "Updated content",
            "scope": "updated/scope",
            "metadata": {},
            "tags": [],
            "category": None,
            "created_at": datetime.now()
        }

        with patch('mcp_assoc_memory.api.tools.memory_tools.ensure_initialized') as mock_init:
            with patch('mcp_assoc_memory.api.tools.memory_tools.handle_memory_update') as mock_update:
                mock_init.return_value = AsyncMock()
                mock_update.return_value = mock_update_response

                response = await handle_memory_manage(request, mock_context)

                # Verify update response structure
                assert response["success"] is True
                assert response["operation"] == "update"
                assert response["memory_id"] == "test-memory-123"
                assert "memory" in response

                # Check memory preview for standard level
                memory = response["memory"]
                assert "content_preview" in memory
                assert len(memory["content_preview"]) <= 103  # Truncated content

    @pytest.mark.asyncio
    async def test_memory_manage_delete_response_levels(self, mock_context):
        """Test DELETE operation with different response levels."""
        request = MemoryManageRequest(
            operation="delete",
            memory_id="test-memory-123",
            response_level=ResponseLevel.MINIMAL
        )

        with patch('mcp_assoc_memory.api.tools.memory_tools.ensure_initialized') as mock_init:
            with patch('mcp_assoc_memory.api.tools.memory_tools.handle_memory_delete') as mock_delete:
                mock_init.return_value = AsyncMock()
                mock_delete.return_value = {
                    "success": True,
                    "message": "Memory test-memory-123 deleted successfully"
                }

                response = await handle_memory_manage(request, mock_context)

                # Verify delete response structure
                assert response["success"] is True
                assert response["operation"] == "delete"
                assert response["memory_id"] == "test-memory-123"
                assert "message" in response

                # Delete responses are minimal by nature
                assert "memory" not in response

    @pytest.mark.asyncio
    async def test_memory_manage_error_response_levels(self, mock_context):
        """Test error responses respect response levels."""
        request = MemoryManageRequest(
            operation="get",
            memory_id="nonexistent-memory",
            response_level=ResponseLevel.MINIMAL
        )

        with patch('mcp_assoc_memory.api.tools.memory_tools.ensure_initialized') as mock_init:
            with patch('mcp_assoc_memory.api.tools.memory_tools.handle_memory_get') as mock_get:
                mock_init.return_value = AsyncMock()
                mock_get.return_value = {"error": "Memory not found"}

                response = await handle_memory_manage(request, mock_context)

                # Verify error response structure
                assert response["success"] is False
                assert response["operation"] == "get"
                assert response["memory_id"] == "nonexistent-memory"
                assert "message" in response

                # Error responses should be minimal
                assert "memory" not in response

    @pytest.mark.asyncio
    async def test_memory_manage_invalid_operation(self, mock_context):
        """Test invalid operation handling."""
        request = MemoryManageRequest(
            operation="invalid_operation",
            memory_id="test-memory-123",
            response_level=ResponseLevel.STANDARD
        )

        with patch('mcp_assoc_memory.api.tools.memory_tools.ensure_initialized') as mock_init:
            mock_init.return_value = AsyncMock()

            response = await handle_memory_manage(request, mock_context)

            # Verify invalid operation response
            assert response["success"] is False
            assert response["operation"] == "invalid_operation"
            assert response["memory_id"] == "test-memory-123"
            assert "Unknown operation" in response["message"]

    @pytest.mark.asyncio
    async def test_memory_manage_exception_handling(self, mock_context):
        """Test exception handling with response levels."""
        request = MemoryManageRequest(
            operation="get",
            memory_id="test-memory-123",
            response_level=ResponseLevel.FULL
        )

        with patch('mcp_assoc_memory.api.tools.memory_tools.ensure_initialized') as mock_init:
            mock_init.side_effect = Exception("Memory manager error")

            response = await handle_memory_manage(request, mock_context)

            # Verify exception response structure
            assert response["success"] is False
            assert response["operation"] == "get"
            assert response["memory_id"] == "test-memory-123"
            assert "Memory manager error" in response["message"]

    def test_response_size_estimates(self):
        """Test response size estimates for different levels."""
        # Mock responses for each level
        minimal_response = {
            "success": True,
            "operation": "get",
            "memory_id": "test-123",
            "message": "Memory retrieved successfully: test-123"
        }

        standard_response = {
            **minimal_response,
            "memory": {
                "memory_id": "test-123",
                "scope": "test/scope",
                "content_preview": "This is a truncated content preview..."
            }
        }

        full_response = {
            **minimal_response,
            "memory": {
                "memory_id": "test-123",
                "content": "This is the complete memory content with all details included for comprehensive analysis",
                "scope": "test/scope",
                "metadata": {"key": "value"},
                "tags": ["tag1", "tag2"],
                "category": "test",
                "created_at": "2025-07-15T00:00:00",
                "associations": []
            }
        }

        # Estimate token counts (rough approximation)
        minimal_tokens = len(str(minimal_response)) // 4
        standard_tokens = len(str(standard_response)) // 4
        full_tokens = len(str(full_response)) // 4

        # Verify token optimization
        assert minimal_tokens < 50, f"Minimal response too large: {minimal_tokens} tokens"
        assert standard_tokens < 200, f"Standard response too large: {standard_tokens} tokens"
        assert full_tokens > standard_tokens, "Full response should be larger than standard"

        print(f"Token estimates - Minimal: {minimal_tokens}, Standard: {standard_tokens}, Full: {full_tokens}")

    @pytest.mark.asyncio
    async def test_memory_manage_update_failure_handling(self, mock_context):
        """Test update operation failure handling."""
        request = MemoryManageRequest(
            operation="update",
            memory_id="test-memory-123",
            content="Updated content",
            response_level=ResponseLevel.STANDARD
        )

        mock_update_response = MagicMock()
        mock_update_response.dict.return_value = {
            "success": False,
            "message": "Update failed: Memory not found",
            "memory_id": "test-memory-123",
            "content": "",
            "scope": "error",
            "created_at": datetime.now()
        }

        with patch('mcp_assoc_memory.api.tools.memory_tools.ensure_initialized') as mock_init:
            with patch('mcp_assoc_memory.api.tools.memory_tools.handle_memory_update') as mock_update:
                mock_init.return_value = AsyncMock()
                mock_update.return_value = mock_update_response

                response = await handle_memory_manage(request, mock_context)

                # Verify failure response structure
                assert response["success"] is False
                assert response["operation"] == "update"
                assert response["memory_id"] == "test-memory-123"
                assert "Update failed" in response["message"]
