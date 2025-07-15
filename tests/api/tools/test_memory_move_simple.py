"""Simple test for memory_move functionality."""
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from src.mcp_assoc_memory.api.tools.other_tools import handle_memory_move
from src.mcp_assoc_memory.api.models.requests import MemoryMoveRequest
from src.mcp_assoc_memory.api.models.common import ResponseLevel


@pytest.mark.asyncio
async def test_memory_move_basic():
    """Test basic memory move functionality."""
    # Create request
    request = MemoryMoveRequest(
        memory_ids=["test-memory-123"],
        target_scope="new/target/scope",
        response_level=ResponseLevel.MINIMAL
    )

    # Mock context
    mock_context = AsyncMock()
    mock_context.info = AsyncMock()
    mock_context.error = AsyncMock()

    # Mock memory object
    mock_memory = MagicMock()
    mock_memory.id = "test-memory-123"
    mock_memory.content = "Test memory content"
    mock_memory.scope = "new/target/scope"
    mock_memory.tags = ["test"]
    mock_memory.category = "test"
    mock_memory.metadata = {}

    # Mock memory manager
    with patch('src.mcp_assoc_memory.api.tools.other_tools.get_or_create_memory_manager') as mock_manager_factory:
        mock_manager = AsyncMock()
        mock_manager.update_memory.return_value = mock_memory
        mock_manager_factory.return_value = mock_manager

        # Execute
        response = await handle_memory_move(request, mock_context)

        # Basic assertions
        assert isinstance(response, dict)
        assert "success" in response
        assert response["success"] is True
        assert "moved_count" in response
        assert response["moved_count"] == 1


if __name__ == "__main__":
    asyncio.run(test_memory_move_basic())
