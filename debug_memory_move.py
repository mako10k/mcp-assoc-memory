#!/usr/bin/env python3
"""Debug script for memory_move response levels."""

import asyncio
from unittest.mock import AsyncMock, MagicMock

from mcp_assoc_memory.api.models.requests import MemoryMoveRequest
from mcp_assoc_memory.api.models.common import ResponseLevel
from mcp_assoc_memory.api.tools.other_tools import handle_memory_move


async def test_minimal_response():
    """Test minimal response level."""
    print("Testing minimal response level...")
    
    # Create mock context
    ctx = MagicMock()
    ctx.info = AsyncMock()
    ctx.error = AsyncMock()
    ctx.warning = AsyncMock()
    
    # Create request
    request = MemoryMoveRequest(
        memory_ids=["test-memory-123"],
        target_scope="new/target/scope",
        response_level=ResponseLevel.MINIMAL
    )
    
    print(f"Request created: {request}")
    print(f"Response level: {request.get_response_level()}")
    
    try:
        response = await handle_memory_move(request, ctx)
        print(f"Response: {response}")
        print("✅ Test completed successfully")
        return response
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    asyncio.run(test_minimal_response())
