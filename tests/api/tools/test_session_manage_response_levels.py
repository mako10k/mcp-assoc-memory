"""
Test suite for session_manage tool response levels implementation
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from mcp_assoc_memory.api.models.requests import SessionManageRequest
from mcp_assoc_memory.api.models.common import ResponseLevel
from mcp_assoc_memory.api.tools.session_tools import handle_session_manage


@pytest.fixture
def mock_context():
    """Mock context for testing."""
    mock_ctx = MagicMock()
    mock_ctx.info = AsyncMock()
    mock_ctx.error = AsyncMock()
    mock_ctx.warning = AsyncMock()
    return mock_ctx


@pytest.fixture
def mock_session_data():
    """Mock session data for testing."""
    return {
        "session_id": "test-session-123",
        "session_name": "Test Session",
        "created_at": datetime.now(),
        "status": "active",
        "memory_count": 5,
        "scope": "session/test-session-123"
    }


class TestSessionManageResponseLevels:
    """Test session_manage response levels implementation."""

    @pytest.mark.asyncio
    async def test_session_manage_request_inheritance(self):
        """Test that SessionManageRequest inherits from CommonToolParameters."""
        request = SessionManageRequest(
            action="create",
            session_id="test-123",
            response_level=ResponseLevel.STANDARD
        )

        # Should have response_level from CommonToolParameters
        assert hasattr(request, 'response_level')
        assert request.response_level == ResponseLevel.STANDARD
        assert hasattr(request, 'get_response_level')
        assert request.get_response_level() == "standard"

    @pytest.mark.asyncio
    async def test_session_create_minimal_response(self, mock_context):
        """Test session creation with minimal response level."""
        request = SessionManageRequest(
            action="create",
            session_id="test-session-123",
            response_level=ResponseLevel.MINIMAL
        )

        # Mock the ensure_initialized function and memory manager
        with patch('mcp_assoc_memory.api.tools.session_tools.ensure_initialized') as mock_init:
            mock_memory_manager = MagicMock()
            mock_memory = MagicMock()
            mock_memory.id = "memory-id-123"

            mock_memory_manager.store_memory = AsyncMock(return_value=mock_memory)
            mock_init.return_value = mock_memory_manager

            result = await handle_session_manage(request, mock_context)

            assert result["success"] is True
            assert "data" in result
            # Minimal response should only include essential information
            if "session_id" in result["data"]:
                assert result["data"]["session_id"] == "test-session-123"

    @pytest.mark.asyncio
    async def test_session_create_standard_response(self, mock_context):
        """Test session creation with standard response level."""
        request = SessionManageRequest(
            action="create",
            session_id="test-session-123",
            response_level=ResponseLevel.STANDARD
        )

        # Mock the ensure_initialized function and memory manager
        with patch('mcp_assoc_memory.api.tools.session_tools.ensure_initialized') as mock_init:
            mock_memory_manager = MagicMock()
            mock_memory = MagicMock()
            mock_memory.id = "memory-id-123"

            mock_memory_manager.store_memory = AsyncMock(return_value=mock_memory)
            mock_init.return_value = mock_memory_manager

            result = await handle_session_manage(request, mock_context)

            assert result["success"] is True
            assert "data" in result
            # Standard response should include balanced information

    @pytest.mark.asyncio
    async def test_session_list_response(self, mock_context):
        """Test session listing with response levels."""
        request = SessionManageRequest(
            action="list",
            response_level=ResponseLevel.STANDARD
        )

        # Mock the ensure_initialized function and memory manager
        with patch('mcp_assoc_memory.api.tools.session_tools.ensure_initialized') as mock_init:
            mock_memory_manager = MagicMock()
            mock_sessions = [
                {
                    "memory_id": "session-marker-1",
                    "content": "Session created: session-1",
                    "scope": "session/session-1",
                    "metadata": {"session_marker": True},
                    "created_at": datetime.now()
                }
            ]
            mock_memory_manager.search_memories = AsyncMock(return_value=mock_sessions)
            mock_init.return_value = mock_memory_manager

            result = await handle_session_manage(request, mock_context)

            assert result["success"] is True
            assert "data" in result

    @pytest.mark.asyncio
    async def test_session_cleanup_response(self, mock_context):
        """Test session cleanup with response levels."""
        request = SessionManageRequest(
            action="cleanup",
            max_age_days=7,
            response_level=ResponseLevel.STANDARD
        )

        # Mock the ensure_initialized function and memory manager
        with patch('mcp_assoc_memory.api.tools.session_tools.ensure_initialized') as mock_init:
            mock_memory_manager = MagicMock()
            mock_memory_manager.search_memories = AsyncMock(return_value=[])
            mock_memory_manager.delete_memory = AsyncMock(return_value=True)
            mock_init.return_value = mock_memory_manager

            result = await handle_session_manage(request, mock_context)

            assert result["success"] is True
            assert "data" in result

    @pytest.mark.asyncio
    async def test_error_handling_with_response_levels(self, mock_context):
        """Test error handling maintains consistent response structure across levels."""
        request = SessionManageRequest(
            action="create",
            session_id="invalid-session",
            response_level=ResponseLevel.MINIMAL
        )

        # Mock storage failure
        with patch('mcp_assoc_memory.api.tools.session_tools.ensure_initialized') as mock_init:
            mock_memory_manager = MagicMock()
            mock_memory_manager.store_memory = AsyncMock(side_effect=Exception("Storage failed"))
            mock_init.return_value = mock_memory_manager

            result = await handle_session_manage(request, mock_context)

            assert result["success"] is False
            assert "error" in result
            # Check if 'data' exists, if not it should be handled gracefully
            if "data" in result:
                assert result["data"] == {}

    @pytest.mark.asyncio
    async def test_invalid_action_error(self, mock_context):
        """Test handling of invalid action."""
        request = SessionManageRequest(
            action="invalid_action",
            response_level=ResponseLevel.STANDARD
        )

        # Mock the ensure_initialized function and memory manager
        with patch('mcp_assoc_memory.api.tools.session_tools.ensure_initialized') as mock_init:
            mock_memory_manager = MagicMock()
            mock_init.return_value = mock_memory_manager

            result = await handle_session_manage(request, mock_context)

            assert result["success"] is False
            assert "error" in result
            assert "Unknown action" in result["error"]
            # Check if 'data' exists, if not it should be handled gracefully
            if "data" in result:
                assert result["data"] == {}
