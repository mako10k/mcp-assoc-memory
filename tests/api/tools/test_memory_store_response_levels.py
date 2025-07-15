"""
Tests for memory_store tool with response level functionality.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from mcp_assoc_memory.api.models.requests import MemoryStoreRequest
from mcp_assoc_memory.api.models.common import ResponseLevel
from mcp_assoc_memory.api.tools.memory_tools import handle_memory_store
from mcp_assoc_memory.api.models import Memory


class TestMemoryStoreResponseLevels:
    """Test memory_store tool with response levels."""

    @pytest.fixture
    def mock_context(self):
        """Mock FastMCP context."""
        ctx = MagicMock()
        ctx.info = AsyncMock()
        ctx.error = AsyncMock()
        ctx.warning = AsyncMock()
        return ctx

    @pytest.fixture
    def sample_memory(self):
        """Sample memory object for testing."""
        return Memory(
            id="test-memory-123",
            content="Test memory content for response level testing",
            scope="test/scope",
            category="test",
            tags=["test", "response-level"],
            metadata={"test": True},
            created_at="2025-07-15T00:00:00Z",
            updated_at="2025-07-15T00:00:00Z"
        )

    @pytest.mark.asyncio
    async def test_memory_store_minimal_response(self, mock_context, sample_memory):
        """Test memory_store with minimal response level."""
        request = MemoryStoreRequest(
            content="Test content",
            scope="test/scope",
            response_level=ResponseLevel.MINIMAL
        )

        with patch('mcp_assoc_memory.api.tools.memory_tools.ensure_initialized') as mock_init:
            mock_manager = AsyncMock()
            mock_manager.store_memory.return_value = sample_memory
            mock_init.return_value = mock_manager

            response = await handle_memory_store(request, mock_context)

            # Verify minimal response structure
            assert response["success"] is True
            assert response["memory_id"] == "test-memory-123"
            assert "message" in response

            # Should NOT include standard/full level data
            assert "scope" not in response
            assert "associations_count" not in response
            assert "memory" not in response
            assert "duplicate_analysis" not in response

    @pytest.mark.asyncio
    async def test_memory_store_standard_response(self, mock_context, sample_memory):
        """Test memory_store with standard response level."""
        request = MemoryStoreRequest(
            content="Test content",
            scope="test/scope",
            response_level=ResponseLevel.STANDARD
        )

        with patch('mcp_assoc_memory.api.tools.memory_tools.ensure_initialized') as mock_init:
            mock_manager = AsyncMock()
            mock_manager.store_memory.return_value = sample_memory
            mock_init.return_value = mock_manager

            response = await handle_memory_store(request, mock_context)

            # Verify standard response structure
            assert response["success"] is True
            assert response["memory_id"] == "test-memory-123"
            assert response["scope"] == "test/scope"
            assert response["associations_count"] == 0
            assert "created_at" in response

            # Should NOT include full level data
            assert "memory" not in response
            assert "duplicate_analysis" not in response

    @pytest.mark.asyncio
    async def test_memory_store_full_response(self, mock_context, sample_memory):
        """Test memory_store with full response level."""
        request = MemoryStoreRequest(
            content="Test content",
            scope="test/scope",
            response_level=ResponseLevel.FULL,
            duplicate_threshold=0.85
        )

        with patch('mcp_assoc_memory.api.tools.memory_tools.ensure_initialized') as mock_init:
            mock_manager = AsyncMock()
            mock_manager.store_memory.return_value = sample_memory
            mock_init.return_value = mock_manager

            response = await handle_memory_store(request, mock_context)

            # Verify full response structure
            assert response["success"] is True
            assert response["memory_id"] == "test-memory-123"
            assert response["scope"] == "test/scope"
            assert response["associations_count"] == 0
            assert "created_at" in response

            # Should include full level data
            assert "memory" in response
            assert response["memory"]["id"] == "test-memory-123"
            assert "duplicate_analysis" in response
            assert response["duplicate_analysis"]["duplicate_check_performed"] is True
            assert response["duplicate_analysis"]["threshold_used"] == 0.85

    @pytest.mark.asyncio
    async def test_memory_store_error_response_levels(self, mock_context):
        """Test error responses respect response levels."""
        # Test with minimal level
        request_minimal = MemoryStoreRequest(
            content="",  # Empty content should cause error
            response_level=ResponseLevel.MINIMAL
        )

        response = await handle_memory_store(request_minimal, mock_context)
        assert response["success"] is False
        assert "message" in response
        # None values are cleaned, so memory_id won't be present
        assert "memory_id" not in response  # None values are removed
        # Should only have minimal fields (success, message)
        assert set(response.keys()) == {"success", "message"}

    @pytest.mark.asyncio
    async def test_memory_store_duplicate_detection_levels(self, mock_context):
        """Test duplicate detection responses respect levels."""
        request = MemoryStoreRequest(
            content="Test content",
            scope="test/scope",
            response_level=ResponseLevel.FULL,
            duplicate_threshold=0.85
        )

        # Mock duplicate detection
        mock_memory = Memory(
            id="existing-123",
            content="Similar content",
            scope="test/scope",
            category="test",
            tags=[],
            metadata={},
            created_at="2025-07-15T00:00:00Z",
            updated_at="2025-07-15T00:00:00Z"
        )

        with patch('mcp_assoc_memory.api.tools.memory_tools.ensure_initialized') as mock_init:
            mock_manager = AsyncMock()
            # Mock search to return similar memory
            mock_search_result = {
                "memory": mock_memory,
                "similarity": 0.90  # Above threshold
            }
            mock_manager.search_memories.return_value = [mock_search_result]
            mock_init.return_value = mock_manager

            response = await handle_memory_store(request, mock_context)

            # Should be error response with duplicate info
            assert response["success"] is False
            assert "memory_id" not in response  # None values are cleaned
            assert "duplicate_analysis" in response
            assert response["duplicate_analysis"]["duplicate_found"] is True
            assert response["duplicate_analysis"]["similarity_score"] == 0.90

    @pytest.mark.asyncio
    async def test_response_level_inheritance(self, mock_context):
        """Test that MemoryStoreRequest inherits response_level correctly."""
        # Test default response level
        request_default = MemoryStoreRequest(content="Test")
        assert request_default.response_level == ResponseLevel.STANDARD

        # Test explicit response level
        request_explicit = MemoryStoreRequest(
            content="Test",
            response_level=ResponseLevel.MINIMAL
        )
        assert request_explicit.response_level == ResponseLevel.MINIMAL

        # Test response level from string
        request_string = MemoryStoreRequest(
            content="Test",
            response_level="full"
        )
        assert request_string.response_level == ResponseLevel.FULL

    def test_response_size_estimates(self):
        """Test response size estimates for different levels."""
        # Mock responses for each level
        minimal_response = {
            "success": True,
            "memory_id": "test-123",
            "message": "Memory stored successfully"
        }

        standard_response = {
            **minimal_response,
            "scope": "test/scope",
            "associations_count": 0,
            "created_at": "2025-07-15T00:00:00Z"
        }

        full_response = {
            **standard_response,
            "memory": {
                "id": "test-123",
                "content": "Test memory content",
                "scope": "test/scope",
                "tags": ["test"],
                "metadata": {}
            },
            "duplicate_analysis": {
                "duplicate_check_performed": True,
                "threshold_used": 0.85
            }
        }

        # Estimate token counts (rough approximation)
        minimal_size = len(str(minimal_response))
        standard_size = len(str(standard_response))
        full_size = len(str(full_response))

        # Verify size progression
        assert minimal_size < standard_size
        assert standard_size < full_size

        # Verify size targets (approximate)
        assert minimal_size < 200  # Should be under 50 tokens (~200 chars)
        assert standard_size < 800  # Should be under 200 tokens (~800 chars)


class TestMemoryStoreRequestValidation:
    """Test MemoryStoreRequest parameter validation."""

    def test_common_parameters_inheritance(self):
        """Test that common parameters are inherited correctly."""
        request = MemoryStoreRequest(
            content="Test content",
            scope="test/scope",
            response_level=ResponseLevel.MINIMAL
        )

        # Test CommonToolParameters methods
        assert request.get_response_level() == "minimal"
        assert request.response_level == ResponseLevel.MINIMAL

    def test_backward_compatibility(self):
        """Test that removing minimal_response doesn't break existing code."""
        # Should work without minimal_response parameter
        request = MemoryStoreRequest(
            content="Test content",
            scope="test/scope"
        )

        assert request.response_level == ResponseLevel.STANDARD
        # Other existing parameters should still work
        assert request.auto_associate is True
        assert request.allow_duplicates is False
