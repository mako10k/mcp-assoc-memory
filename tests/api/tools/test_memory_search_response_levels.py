"""
Tests for memory_search tool with response level functionality.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from mcp_assoc_memory.api.models.requests import MemorySearchRequest
from mcp_assoc_memory.api.models.common import ResponseLevel
from mcp_assoc_memory.api.tools.memory_tools import handle_memory_search
from mcp_assoc_memory.api.models import Memory


class TestMemorySearchResponseLevels:
    """Test memory_search tool with response levels."""

    @pytest.fixture
    def mock_context(self):
        """Mock FastMCP context."""
        ctx = MagicMock()
        ctx.info = AsyncMock()
        ctx.error = AsyncMock()
        ctx.warning = AsyncMock()
        return ctx

    @pytest.fixture
    def sample_memories(self):
        """Sample memory objects for testing."""
        return [
            Memory(
                id="test-memory-1",
                content="Python programming best practices for web development",
                scope="learning/programming",
                category="programming",
                tags=["python", "web", "best-practices"],
                metadata={"language": "python", "difficulty": "intermediate"},
                created_at="2025-07-15T00:00:00Z",
                updated_at="2025-07-15T00:00:00Z"
            ),
            Memory(
                id="test-memory-2",
                content="FastAPI framework usage patterns and performance optimization",
                scope="learning/programming",
                category="framework",
                tags=["fastapi", "python", "performance"],
                metadata={"framework": "fastapi", "type": "tutorial"},
                created_at="2025-07-15T01:00:00Z",
                updated_at="2025-07-15T01:00:00Z"
            )
        ]

    @pytest.fixture
    def mock_search_results(self, sample_memories):
        """Mock search results."""
        return [
            {"memory": sample_memories[0], "similarity": 0.85},
            {"memory": sample_memories[1], "similarity": 0.75}
        ]

    @pytest.mark.asyncio
    async def test_memory_search_minimal_response(self, mock_context, mock_search_results):
        """Test memory_search with minimal response level."""
        request = MemorySearchRequest(
            query="Python programming",
            response_level=ResponseLevel.MINIMAL
        )

        with patch('mcp_assoc_memory.api.tools.memory_tools.ensure_initialized') as mock_init:
            mock_manager = AsyncMock()
            mock_manager.search_memories.return_value = mock_search_results
            mock_init.return_value = mock_manager

            response = await handle_memory_search(request, mock_context)

            # Verify minimal response structure
            assert response["success"] is True
            assert response["total_count"] == 2
            assert "message" in response
            
            # Should NOT include standard/full level data
            assert "query" not in response
            assert "results" not in response
            assert "scope" not in response
            assert "search_metadata" not in response

    @pytest.mark.asyncio
    async def test_memory_search_standard_response(self, mock_context, mock_search_results):
        """Test memory_search with standard response level."""
        request = MemorySearchRequest(
            query="Python programming",
            scope="learning/programming",
            response_level=ResponseLevel.STANDARD
        )

        with patch('mcp_assoc_memory.api.tools.memory_tools.ensure_initialized') as mock_init:
            mock_manager = AsyncMock()
            mock_manager.search_memories.return_value = mock_search_results
            mock_init.return_value = mock_manager

            response = await handle_memory_search(request, mock_context)

            # Verify standard response structure
            assert response["success"] is True
            assert response["total_count"] == 2
            assert response["query"] == "Python programming"
            assert response["scope"] == "learning/programming"
            assert "results" in response
            assert len(response["results"]) == 2
            
            # Check result structure for standard level
            result = response["results"][0]
            assert "memory_id" in result
            assert "scope" in result
            assert "content_preview" in result
            assert "similarity_score" in result
            
            # Should NOT include full level data
            assert "content" not in result  # Only preview in standard
            assert "search_metadata" not in response

    @pytest.mark.asyncio
    async def test_memory_search_full_response(self, mock_context, mock_search_results):
        """Test memory_search with full response level."""
        request = MemorySearchRequest(
            query="Python programming",
            scope="learning/programming",
            response_level=ResponseLevel.FULL,
            include_associations=True
        )

        with patch('mcp_assoc_memory.api.tools.memory_tools.ensure_initialized') as mock_init:
            mock_manager = AsyncMock()
            mock_manager.search_memories.return_value = mock_search_results
            mock_init.return_value = mock_manager

            response = await handle_memory_search(request, mock_context)

            # Verify full response structure
            assert response["success"] is True
            assert response["total_count"] == 2
            assert response["query"] == "Python programming"
            assert response["scope"] == "learning/programming"
            assert "results" in response
            assert len(response["results"]) == 2
            
            # Check result structure for full level
            result = response["results"][0]
            assert "memory_id" in result
            assert "content" in result  # Full content, not preview
            assert "scope" in result
            assert "similarity_score" in result
            assert "tags" in result
            assert "category" in result
            assert "created_at" in result
            assert "metadata" in result
            assert "associations" in result
            
            # Should include full level metadata
            assert "search_metadata" in response
            assert "scope_coverage" in response["search_metadata"]
            assert "similarity_threshold" in response["search_metadata"]

    @pytest.mark.asyncio
    async def test_memory_search_error_response_levels(self, mock_context):
        """Test error responses respect response levels."""
        request = MemorySearchRequest(
            query="test query",
            response_level=ResponseLevel.MINIMAL
        )

        with patch('mcp_assoc_memory.api.tools.memory_tools.ensure_initialized') as mock_init:
            mock_init.side_effect = Exception("Memory manager error")

            response = await handle_memory_search(request, mock_context)

            # Verify error response structure
            assert response["success"] is False
            assert "message" in response
            assert response["total_count"] == 0
            
            # Minimal level should not include error details
            assert "error_details" not in response

    @pytest.mark.asyncio
    async def test_memory_search_error_response_full(self, mock_context):
        """Test error responses include details in full level."""
        request = MemorySearchRequest(
            query="test query",
            response_level=ResponseLevel.FULL
        )

        with patch('mcp_assoc_memory.api.tools.memory_tools.ensure_initialized') as mock_init:
            mock_init.side_effect = ValueError("Specific error message")

            response = await handle_memory_search(request, mock_context)

            # Verify full error response structure
            assert response["success"] is False
            assert "message" in response
            assert response["total_count"] == 0
            assert "error_details" in response
            assert response["error_details"]["error_type"] == "ValueError"
            assert response["error_details"]["query"] == "test query"

    @pytest.mark.asyncio
    async def test_response_level_inheritance(self, mock_context):
        """Test that MemorySearchRequest inherits response_level correctly."""
        # Test default response level
        request_default = MemorySearchRequest(query="test")
        assert request_default.response_level == ResponseLevel.STANDARD

        # Test explicit response level
        request_explicit = MemorySearchRequest(
            query="test",
            response_level=ResponseLevel.MINIMAL
        )
        assert request_explicit.response_level == ResponseLevel.MINIMAL

        # Test response level from string
        request_string = MemorySearchRequest(
            query="test",
            response_level="full"
        )
        assert request_string.response_level == ResponseLevel.FULL

    @pytest.mark.asyncio
    async def test_empty_results_response_levels(self, mock_context):
        """Test response levels with no search results."""
        request = MemorySearchRequest(
            query="nonexistent query",
            response_level=ResponseLevel.STANDARD
        )

        with patch('mcp_assoc_memory.api.tools.memory_tools.ensure_initialized') as mock_init:
            mock_manager = AsyncMock()
            mock_manager.search_memories.return_value = []  # No results
            mock_init.return_value = mock_manager

            response = await handle_memory_search(request, mock_context)

            # Verify empty results response
            assert response["success"] is True
            assert response["total_count"] == 0
            assert response["query"] == "nonexistent query"
            # Note: Empty results array is cleaned by ResponseBuilder._clean_response()
            # so "results" field should not be present when no results found
            assert "results" not in response

    def test_response_size_estimates(self):
        """Test response size estimates for different levels."""
        # Mock responses for each level
        minimal_response = {
            "success": True,
            "total_count": 5,
            "message": "Found 5 memories for query: Python"
        }

        standard_response = {
            **minimal_response,
            "query": "Python",
            "scope": "learning/programming",
            "results": [
                {
                    "memory_id": "test-123",
                    "scope": "learning/programming",
                    "content_preview": "Python programming best practices for...",
                    "similarity_score": 0.85
                }
            ] * 5  # 5 results
        }

        full_response = {
            **standard_response,
            "search_metadata": {
                "scope_coverage": "exact",
                "similarity_threshold": 0.1,
                "include_child_scopes": False,
                "include_associations": True
            }
        }
        # Update results to include full content
        full_response["results"] = [
            {
                "memory_id": "test-123",
                "content": "Python programming best practices for web development including FastAPI patterns",
                "scope": "learning/programming",
                "similarity_score": 0.85,
                "tags": ["python", "web", "best-practices"],
                "category": "programming",
                "created_at": "2025-07-15T00:00:00Z",
                "metadata": {"language": "python"},
                "associations": []
            }
        ] * 5

        # Estimate sizes
        minimal_size = len(str(minimal_response))
        standard_size = len(str(standard_response))
        full_size = len(str(full_response))

        # Verify size progression
        assert minimal_size < standard_size
        assert standard_size < full_size
        
        # Verify size targets (approximate)
        assert minimal_size < 200  # Should be under 50 tokens (~200 chars)
        assert standard_size < 2000  # Should be reasonable for 5 results
        assert full_size > standard_size  # Full should be significantly larger


class TestMemorySearchRequestValidation:
    """Test MemorySearchRequest parameter validation."""

    def test_common_parameters_inheritance(self):
        """Test that common parameters are inherited correctly."""
        request = MemorySearchRequest(
            query="test query",
            response_level=ResponseLevel.MINIMAL
        )

        # Test CommonToolParameters methods
        assert request.get_response_level() == "minimal"
        assert request.response_level == ResponseLevel.MINIMAL

    def test_backward_compatibility(self):
        """Test existing parameters still work."""
        request = MemorySearchRequest(
            query="test query",
            scope="learning/programming",
            limit=20,
            similarity_threshold=0.5,
            include_associations=False
        )

        assert request.response_level == ResponseLevel.STANDARD  # Default
        assert request.scope == "learning/programming"
        assert request.limit == 20
        assert request.similarity_threshold == 0.5
        assert request.include_associations is False
