"""
Test scope_list response levels and ResponseBuilder integration
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.mcp_assoc_memory.api.models.requests import ScopeListRequest
from src.mcp_assoc_memory.api.models.common import ResponseLevel
from src.mcp_assoc_memory.api.tools.scope_tools import handle_scope_list


class TestScopeListResponseLevels:
    """Test suite for scope_list response level handling"""

    @pytest.mark.asyncio
    async def test_scope_list_request_inheritance(self):
        """Test that ScopeListRequest properly inherits from CommonToolParameters"""
        # Test basic request creation with response level
        request = ScopeListRequest(
            parent_scope="work",
            include_memory_counts=True,
            response_level=ResponseLevel.STANDARD
        )

        # Test inheritance
        assert isinstance(request, ScopeListRequest)
        assert hasattr(request, 'response_level')
        assert request.response_level == ResponseLevel.STANDARD

        # Test default response level
        request_default = ScopeListRequest(
            parent_scope="work",
            include_memory_counts=True
        )
        assert request_default.response_level == ResponseLevel.STANDARD

    @pytest.mark.asyncio
    async def test_scope_list_minimal_response_structure(self):
        """Test scope_list minimal response structure and token efficiency"""
        request = ScopeListRequest(
            parent_scope=None,
            include_memory_counts=False,
            response_level=ResponseLevel.MINIMAL
        )

        mock_context = AsyncMock()
        mock_manager = AsyncMock()
        mock_manager.get_all_scopes.return_value = ["work", "learning", "personal"]

        with patch('src.mcp_assoc_memory.api.tools.scope_tools.get_or_create_memory_manager', return_value=mock_manager):
            response = await handle_scope_list(request, mock_context)

        # Verify response structure
        assert isinstance(response, dict)
        assert response["success"] is True
        assert "message" in response
        assert "total_scopes" in response
        assert response["total_scopes"] == 3

        # Minimal response should not contain detailed scope information
        assert "scopes" not in response or response.get("scopes") is None

    @pytest.mark.asyncio
    async def test_scope_list_standard_response_structure(self):
        """Test scope_list standard response structure with balanced detail"""
        request = ScopeListRequest(
            parent_scope="work",
            include_memory_counts=True,
            response_level=ResponseLevel.STANDARD
        )

        mock_context = AsyncMock()
        mock_manager = AsyncMock()
        mock_manager.get_all_scopes.return_value = [
            "work", "work/projects", "work/testing", "learning"
        ]
        mock_manager.get_memory_count_by_scope.return_value = 5

        with patch('src.mcp_assoc_memory.api.tools.scope_tools.get_or_create_memory_manager', return_value=mock_manager):
            with patch('src.mcp_assoc_memory.api.tools.scope_tools.get_child_scopes', return_value=["work/projects", "work/testing"]):
                response = await handle_scope_list(request, mock_context)

        # Verify response structure
        assert isinstance(response, dict)
        assert response["success"] is True
        assert "parent_scope" in response
        assert response["parent_scope"] == "work"
        assert "scope_preview" in response
        assert isinstance(response["scope_preview"], list)

        # Standard response should contain preview information
        for scope_item in response["scope_preview"]:
            assert "scope" in scope_item
            assert "memory_count" in scope_item
            assert "child_count" in scope_item

    @pytest.mark.asyncio
    async def test_scope_list_full_response_structure(self):
        """Test scope_list full response structure with complete details"""
        request = ScopeListRequest(
            parent_scope="work",
            include_memory_counts=True,
            response_level=ResponseLevel.FULL
        )

        mock_context = AsyncMock()
        mock_manager = AsyncMock()
        mock_manager.get_all_scopes.return_value = [
            "work", "work/projects", "work/testing", "learning"
        ]
        mock_manager.get_memory_count_by_scope.return_value = 8

        with patch('src.mcp_assoc_memory.api.tools.scope_tools.get_or_create_memory_manager', return_value=mock_manager):
            with patch('src.mcp_assoc_memory.api.tools.scope_tools.get_child_scopes', return_value=["work/projects", "work/testing"]):
                response = await handle_scope_list(request, mock_context)

        # Verify response structure
        assert isinstance(response, dict)
        assert response["success"] is True
        assert "scopes" in response
        assert "hierarchy_stats" in response
        assert isinstance(response["scopes"], list)

        # Full response should contain complete scope information
        for scope_item in response["scopes"]:
            assert "scope" in scope_item
            assert "memory_count" in scope_item
            assert "child_scopes" in scope_item

        # Verify hierarchy stats
        hierarchy_stats = response["hierarchy_stats"]
        assert "total_scopes" in hierarchy_stats
        assert "filtered_scopes" in hierarchy_stats
        assert "include_memory_counts" in hierarchy_stats

    @pytest.mark.asyncio
    async def test_scope_list_error_handling_minimal(self):
        """Test error handling with minimal response level"""
        request = ScopeListRequest(
            parent_scope="invalid/scope/format",
            response_level=ResponseLevel.MINIMAL
        )

        mock_context = AsyncMock()
        mock_manager = AsyncMock()
        mock_manager.get_all_scopes.return_value = ["work", "learning"]

        with patch('src.mcp_assoc_memory.api.tools.scope_tools.get_or_create_memory_manager', return_value=mock_manager):
            with patch('src.mcp_assoc_memory.api.tools.scope_tools.validate_scope_path', return_value=False):
                response = await handle_scope_list(request, mock_context)

        # Verify error response structure
        assert isinstance(response, dict)
        assert response["success"] is False
        assert "message" in response
        assert "error" in response
        assert response["error"] == "INVALID_SCOPE"

    @pytest.mark.asyncio
    async def test_scope_list_error_handling_standard(self):
        """Test error handling with standard response level"""
        request = ScopeListRequest(
            parent_scope="test",
            response_level=ResponseLevel.STANDARD
        )

        mock_context = AsyncMock()

        with patch('src.mcp_assoc_memory.api.tools.scope_tools.get_or_create_memory_manager', return_value=None):
            response = await handle_scope_list(request, mock_context)

        # Verify error response structure
        assert isinstance(response, dict)
        assert response["success"] is False
        assert "message" in response
        assert "error" in response
        assert response["error"] == "Memory manager not initialized"

    @pytest.mark.asyncio
    async def test_scope_list_without_memory_counts(self):
        """Test scope_list with include_memory_counts=False for performance"""
        request = ScopeListRequest(
            parent_scope=None,
            include_memory_counts=False,
            response_level=ResponseLevel.FULL
        )

        mock_context = AsyncMock()
        mock_manager = AsyncMock()
        mock_manager.get_all_scopes.return_value = ["work", "learning", "personal"]

        with patch('src.mcp_assoc_memory.api.tools.scope_tools.get_or_create_memory_manager', return_value=mock_manager):
            response = await handle_scope_list(request, mock_context)

        # Verify response structure
        assert isinstance(response, dict)
        assert response["success"] is True
        assert "scopes" in response

        # Verify memory manager methods
        mock_manager.get_all_scopes.assert_called_once()
        mock_manager.get_memory_count_by_scope.assert_not_called()  # Should not be called when include_memory_counts=False

        # Verify memory counts are 0 when not requested
        for scope_item in response["scopes"]:
            assert scope_item["memory_count"] == 0

    @pytest.mark.asyncio
    async def test_scope_list_parent_scope_filtering(self):
        """Test scope filtering by parent scope"""
        request = ScopeListRequest(
            parent_scope="work",
            include_memory_counts=True,
            response_level=ResponseLevel.FULL
        )

        mock_context = AsyncMock()
        mock_manager = AsyncMock()
        mock_manager.get_all_scopes.return_value = [
            "work", "work/projects", "work/testing", "learning", "personal"
        ]
        mock_manager.get_memory_count_by_scope.return_value = 3

        with patch('src.mcp_assoc_memory.api.tools.scope_tools.get_or_create_memory_manager', return_value=mock_manager):
            with patch('src.mcp_assoc_memory.api.tools.scope_tools.get_child_scopes', return_value=["work/projects", "work/testing"]):
                with patch('src.mcp_assoc_memory.api.tools.scope_tools.validate_scope_path', return_value=True):
                    response = await handle_scope_list(request, mock_context)

        # Verify response structure
        assert isinstance(response, dict)
        assert response["success"] is True
        assert response["parent_scope"] == "work"
        assert "scopes" in response

        # Verify scope filtering was applied
        assert len(response["scopes"]) == 2  # Only work/projects and work/testing

    @pytest.mark.asyncio
    async def test_scope_list_memory_count_error_handling(self):
        """Test graceful handling of memory count retrieval errors"""
        request = ScopeListRequest(
            parent_scope=None,
            include_memory_counts=True,
            response_level=ResponseLevel.FULL
        )

        mock_context = AsyncMock()
        mock_manager = AsyncMock()
        mock_manager.get_all_scopes.return_value = ["work", "learning"]
        mock_manager.get_memory_count_by_scope.side_effect = Exception("Database error")

        with patch('src.mcp_assoc_memory.api.tools.scope_tools.get_or_create_memory_manager', return_value=mock_manager):
            response = await handle_scope_list(request, mock_context)

        # Verify response structure and error handling
        assert isinstance(response, dict)
        assert response["success"] is True  # Should succeed despite memory count errors
        assert "scopes" in response

        # Verify memory counts default to 0 when errors occur
        for scope_item in response["scopes"]:
            assert scope_item["memory_count"] == 0

    @pytest.mark.asyncio
    async def test_scope_list_exception_handling(self):
        """Test exception handling and error response format"""
        request = ScopeListRequest(
            parent_scope="test",
            response_level=ResponseLevel.FULL
        )

        mock_context = AsyncMock()
        mock_manager = AsyncMock()
        mock_manager.get_all_scopes.side_effect = Exception("Unexpected error")

        with patch('src.mcp_assoc_memory.api.tools.scope_tools.get_or_create_memory_manager', return_value=mock_manager):
            response = await handle_scope_list(request, mock_context)

        # Verify error response structure
        assert isinstance(response, dict)
        assert response["success"] is False
        assert "message" in response
        assert "error" in response
        assert response["error"] == "SCOPE_LIST_ERROR"
        assert "Unexpected error" in response["message"]
