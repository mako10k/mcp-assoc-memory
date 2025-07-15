"""
Test suite for memory_discover_associations tool response levels implementation
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from mcp_assoc_memory.api.models.requests import MemoryDiscoverAssociationsRequest
from mcp_assoc_memory.api.models.common import ResponseLevel
from mcp_assoc_memory.api.tools.memory_tools import handle_memory_discover_associations


@pytest.fixture
def mock_context():
    """Mock context for testing."""
    mock_ctx = MagicMock()
    mock_ctx.info = AsyncMock()
    mock_ctx.error = AsyncMock()
    mock_ctx.warning = AsyncMock()
    return mock_ctx


@pytest.fixture
def mock_source_memory():
    """Mock source memory for testing."""
    mock_memory = MagicMock()
    mock_memory.id = "source-memory-123"
    mock_memory.content = "This is the source memory content for association discovery"
    mock_memory.scope = "test/source"
    mock_memory.tags = ["test", "source"]
    mock_memory.category = "test"
    mock_memory.created_at = datetime.now()
    mock_memory.metadata = {"test": "source_data"}
    return mock_memory


@pytest.fixture
def mock_association_results():
    """Mock association search results for testing."""
    results = []
    for i in range(3):
        mock_memory = MagicMock()
        mock_memory.id = f"assoc-memory-{i + 1}"
        mock_memory.content = f"Associated memory content {i + 1} with related information"
        mock_memory.scope = f"test/associations/{i + 1}"
        mock_memory.tags = ["test", "association"]
        mock_memory.category = "test"
        mock_memory.created_at = datetime.now()
        mock_memory.metadata = {"test": f"assoc_data_{i + 1}"}

        results.append({
            "memory": mock_memory,
            "similarity": 0.8 - (i * 0.1)  # Decreasing similarity
        })
    return results


class TestMemoryDiscoverAssociationsResponseLevels:
    """Test memory_discover_associations response levels implementation."""

    @pytest.mark.asyncio
    async def test_request_inheritance(self):
        """Test that MemoryDiscoverAssociationsRequest inherits from CommonToolParameters."""
        request = MemoryDiscoverAssociationsRequest(
            memory_id="test-memory-123",
            response_level=ResponseLevel.STANDARD
        )

        # Should have response_level from CommonToolParameters
        assert hasattr(request, 'response_level')
        assert request.response_level == ResponseLevel.STANDARD
        assert hasattr(request, 'get_response_level')
        assert request.get_response_level() == ResponseLevel.STANDARD

    @pytest.mark.asyncio
    async def test_discover_associations_minimal_response(self, mock_context, mock_source_memory, mock_association_results):
        """Test discover associations with minimal response level."""
        request = MemoryDiscoverAssociationsRequest(
            memory_id="source-memory-123",
            limit=10,
            similarity_threshold=0.1,
            response_level=ResponseLevel.MINIMAL
        )

        with patch('mcp_assoc_memory.api.tools.memory_tools.ensure_initialized') as mock_init:
            with patch('mcp_assoc_memory.api.tools.memory_tools.get_or_create_memory_manager') as mock_manager_factory:
                mock_init.return_value = AsyncMock()

                mock_manager = AsyncMock()
                mock_manager.get_memory.return_value = mock_source_memory
                mock_manager.search_memories.return_value = mock_association_results
                mock_manager_factory.return_value = mock_manager

                response = await handle_memory_discover_associations(request, mock_context)

                # Verify minimal response structure
                assert response["success"] is True
                assert response["source_memory_id"] == "source-memory-123"
                assert response["total_found"] == 3
                assert "message" in response

                # Minimal level should not include associations or source content
                assert "associations" not in response
                assert "source_content_preview" not in response
                assert "source_memory" not in response

    @pytest.mark.asyncio
    async def test_discover_associations_standard_response(self, mock_context, mock_source_memory, mock_association_results):
        """Test discover associations with standard response level."""
        request = MemoryDiscoverAssociationsRequest(
            memory_id="source-memory-123",
            limit=10,
            similarity_threshold=0.1,
            response_level=ResponseLevel.STANDARD
        )

        with patch('mcp_assoc_memory.api.tools.memory_tools.ensure_initialized') as mock_init:
            with patch('mcp_assoc_memory.api.tools.memory_tools.get_or_create_memory_manager') as mock_manager_factory:
                mock_init.return_value = AsyncMock()

                mock_manager = AsyncMock()
                mock_manager.get_memory.return_value = mock_source_memory
                mock_manager.search_memories.return_value = mock_association_results
                mock_manager_factory.return_value = mock_manager

                response = await handle_memory_discover_associations(request, mock_context)

                # Verify standard response structure
                assert response["success"] is True
                assert response["source_memory_id"] == "source-memory-123"
                assert response["total_found"] == 3
                assert "source_content_preview" in response
                assert "associations" in response
                assert len(response["associations"]) == 3

                # Check association preview structure for standard level
                association = response["associations"][0]
                assert "memory_id" in association
                assert "scope" in association
                assert "content_preview" in association
                assert "similarity_score" in association
                assert len(association["content_preview"]) <= 53  # 50 chars + "..."

    @pytest.mark.asyncio
    async def test_discover_associations_full_response(self, mock_context, mock_source_memory, mock_association_results):
        """Test discover associations with full response level."""
        request = MemoryDiscoverAssociationsRequest(
            memory_id="source-memory-123",
            limit=10,
            similarity_threshold=0.1,
            response_level=ResponseLevel.FULL
        )

        with patch('mcp_assoc_memory.api.tools.memory_tools.ensure_initialized') as mock_init:
            with patch('mcp_assoc_memory.api.tools.memory_tools.get_or_create_memory_manager') as mock_manager_factory:
                mock_init.return_value = AsyncMock()

                mock_manager = AsyncMock()
                mock_manager.get_memory.return_value = mock_source_memory
                mock_manager.search_memories.return_value = mock_association_results
                mock_manager_factory.return_value = mock_manager

                response = await handle_memory_discover_associations(request, mock_context)

                # Verify full response structure
                assert response["success"] is True
                assert response["source_memory_id"] == "source-memory-123"
                assert response["total_found"] == 3
                assert "source_memory" in response
                assert "associations" in response
                assert "search_metadata" in response

                # Check complete source memory structure
                source_memory = response["source_memory"]
                assert source_memory["memory_id"] == "source-memory-123"
                assert source_memory["content"] == mock_source_memory.content
                assert source_memory["scope"] == mock_source_memory.scope
                assert source_memory["tags"] == mock_source_memory.tags
                assert source_memory["metadata"] == mock_source_memory.metadata

                # Check complete association structure
                association = response["associations"][0]
                assert "memory_id" in association
                assert "content" in association  # Full content, not preview
                assert "scope" in association
                assert "similarity_score" in association
                assert "tags" in association
                assert "category" in association
                assert "created_at" in association

    @pytest.mark.asyncio
    async def test_discover_associations_memory_not_found(self, mock_context):
        """Test memory not found error handling."""
        request = MemoryDiscoverAssociationsRequest(
            memory_id="nonexistent-memory",
            response_level=ResponseLevel.STANDARD
        )

        with patch('mcp_assoc_memory.api.tools.memory_tools.ensure_initialized') as mock_init:
            with patch('mcp_assoc_memory.api.tools.memory_tools.get_or_create_memory_manager') as mock_manager_factory:
                mock_init.return_value = AsyncMock()

                mock_manager = AsyncMock()
                mock_manager.get_memory.return_value = None  # Memory not found
                mock_manager_factory.return_value = mock_manager

                response = await handle_memory_discover_associations(request, mock_context)

                # Verify error response structure
                assert response["success"] is False
                assert response["source_memory_id"] == "nonexistent-memory"
                assert response["total_found"] == 0
                assert "Memory not found" in response["message"]

    @pytest.mark.asyncio
    async def test_discover_associations_manager_not_available(self, mock_context):
        """Test memory manager not available error handling."""
        request = MemoryDiscoverAssociationsRequest(
            memory_id="test-memory-123",
            response_level=ResponseLevel.MINIMAL
        )

        with patch('mcp_assoc_memory.api.tools.memory_tools.ensure_initialized') as mock_init:
            with patch('mcp_assoc_memory.api.tools.memory_tools.get_or_create_memory_manager') as mock_manager_factory:
                mock_init.return_value = AsyncMock()
                mock_manager_factory.return_value = None  # Manager not available

                response = await handle_memory_discover_associations(request, mock_context)

                # Verify error response structure
                assert response["success"] is False
                assert response["source_memory_id"] == "test-memory-123"
                assert response["total_found"] == 0
                assert "Memory manager not available" in response["message"]

    @pytest.mark.asyncio
    async def test_discover_associations_no_results(self, mock_context, mock_source_memory):
        """Test discover associations with no association results."""
        request = MemoryDiscoverAssociationsRequest(
            memory_id="source-memory-123",
            limit=10,
            similarity_threshold=0.9,  # High threshold
            response_level=ResponseLevel.STANDARD
        )

        with patch('mcp_assoc_memory.api.tools.memory_tools.ensure_initialized') as mock_init:
            with patch('mcp_assoc_memory.api.tools.memory_tools.get_or_create_memory_manager') as mock_manager_factory:
                mock_init.return_value = AsyncMock()

                mock_manager = AsyncMock()
                mock_manager.get_memory.return_value = mock_source_memory
                mock_manager.search_memories.return_value = []  # No results
                mock_manager_factory.return_value = mock_manager

                response = await handle_memory_discover_associations(request, mock_context)

                # Verify empty results response
                assert response["success"] is True
                assert response["source_memory_id"] == "source-memory-123"
                assert response["total_found"] == 0
                # Note: Empty associations array is cleaned by ResponseBuilder._clean_response()
                # so "associations" field should not be present when no results found
                assert "associations" not in response

    @pytest.mark.asyncio
    async def test_discover_associations_exception_handling(self, mock_context):
        """Test exception handling with response levels."""
        request = MemoryDiscoverAssociationsRequest(
            memory_id="test-memory-123",
            response_level=ResponseLevel.FULL
        )

        with patch('mcp_assoc_memory.api.tools.memory_tools.ensure_initialized') as mock_init:
            mock_init.side_effect = Exception("Memory system error")

            response = await handle_memory_discover_associations(request, mock_context)

            # Verify exception response structure
            assert response["success"] is False
            assert response["source_memory_id"] == "test-memory-123"
            assert response["total_found"] == 0
            assert "Memory system error" in response["message"]

    @pytest.mark.asyncio
    async def test_discover_associations_enhanced_search(self, mock_context, mock_source_memory):
        """Test enhanced search with tags and category."""
        # Source memory with tags and category for enhanced search
        mock_source_memory.tags = ["python", "programming"]
        mock_source_memory.category = "learning"

        request = MemoryDiscoverAssociationsRequest(
            memory_id="source-memory-123",
            limit=5,  # Small limit to trigger enhanced search
            similarity_threshold=0.5,
            response_level=ResponseLevel.STANDARD
        )

        with patch('mcp_assoc_memory.api.tools.memory_tools.ensure_initialized') as mock_init:
            with patch('mcp_assoc_memory.api.tools.memory_tools.get_or_create_memory_manager') as mock_manager_factory:
                mock_init.return_value = AsyncMock()

                mock_manager = AsyncMock()
                mock_manager.get_memory.return_value = mock_source_memory
                # First search returns insufficient results
                mock_manager.search_memories.side_effect = [
                    [],  # First search with original content
                    [{"memory": mock_source_memory, "similarity": 0.7}]  # Enhanced search with tags
                ]
                mock_manager_factory.return_value = mock_manager

                await handle_memory_discover_associations(request, mock_context)

                # Verify enhanced search was triggered
                assert mock_manager.search_memories.call_count == 2
                # Second call should include enhanced query with tags
                second_call_args = mock_manager.search_memories.call_args_list[1]
                enhanced_query = second_call_args[1]["query"]
                assert "python" in enhanced_query
                assert "programming" in enhanced_query
                assert "learning" in enhanced_query

    def test_response_size_estimates(self):
        """Test response size estimates for different levels."""
        # Mock responses for each level
        minimal_response = {
            "success": True,
            "source_memory_id": "test-123",
            "total_found": 5,
            "message": "Found 5 associations for memory: test-123"
        }

        standard_response = {
            **minimal_response,
            "source_content_preview": "This is a truncated source content preview...",
            "associations": [
                {
                    "memory_id": "assoc-1",
                    "scope": "test/associations",
                    "content_preview": "This is association preview...",
                    "similarity_score": 0.85
                }
            ] * 5  # 5 associations
        }

        full_response = {
            **minimal_response,
            "source_memory": {
                "memory_id": "test-123",
                "content": "This is the complete source memory content with all details",
                "scope": "test/source",
                "tags": ["tag1", "tag2"],
                "category": "test",
                "created_at": "2025-07-15T00:00:00",
                "metadata": {"key": "value"}
            },
            "associations": [
                {
                    "memory_id": "assoc-1",
                    "content": "This is the complete association content with all details and metadata",
                    "scope": "test/associations",
                    "similarity_score": 0.85,
                    "tags": ["assoc_tag"],
                    "category": "association",
                    "created_at": "2025-07-15T00:00:00"
                }
            ] * 5,
            "search_metadata": {
                "similarity_threshold": 0.1,
                "limit": 10,
                "search_strategy": "enhanced_query_with_tags"
            }
        }

        # Estimate token counts (rough approximation)
        minimal_tokens = len(str(minimal_response)) // 4
        standard_tokens = len(str(standard_response)) // 4
        full_tokens = len(str(full_response)) // 4

        # Verify token optimization
        assert minimal_tokens < 50, f"Minimal response too large: {minimal_tokens} tokens"
        assert standard_tokens < 300, f"Standard response too large: {standard_tokens} tokens"
        assert full_tokens > standard_tokens, "Full response should be larger than standard"

        print(f"Token estimates - Minimal: {minimal_tokens}, Standard: {standard_tokens}, Full: {full_tokens}")

    @pytest.mark.asyncio
    async def test_discover_associations_limit_parameter(self, mock_context, mock_source_memory):
        """Test association limit parameter handling."""
        # Create more results than the limit
        mock_results = []
        for i in range(15):  # More than limit of 10
            mock_memory = MagicMock()
            mock_memory.id = f"assoc-memory-{i + 1}"
            mock_memory.content = f"Association content {i + 1}"
            mock_memory.scope = f"test/scope/{i + 1}"
            mock_memory.tags = ["test"]
            mock_memory.category = "test"
            mock_memory.created_at = datetime.now()
            mock_memory.metadata = {}
            mock_results.append({
                "memory": mock_memory,
                "similarity": 0.9 - (i * 0.01)
            })

        request = MemoryDiscoverAssociationsRequest(
            memory_id="source-memory-123",
            limit=10,
            similarity_threshold=0.1,
            response_level=ResponseLevel.STANDARD
        )

        with patch('mcp_assoc_memory.api.tools.memory_tools.ensure_initialized') as mock_init:
            with patch('mcp_assoc_memory.api.tools.memory_tools.get_or_create_memory_manager') as mock_manager_factory:
                mock_init.return_value = AsyncMock()

                mock_manager = AsyncMock()
                mock_manager.get_memory.return_value = mock_source_memory
                mock_manager.search_memories.return_value = mock_results
                mock_manager_factory.return_value = mock_manager

                response = await handle_memory_discover_associations(request, mock_context)

                # Verify limit is respected
                assert response["success"] is True
                assert response["total_found"] == 10  # Limited to request.limit
                assert len(response["associations"]) == 10
