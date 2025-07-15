"""
Simplified test fixture to isolate hang issue.
Tests the most basic functionality without complex async fixtures.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock


@pytest.mark.asyncio
async def test_simple_async():
    """Simplest possible async test to check if basic async works."""
    mock = AsyncMock()
    mock.simple_method.return_value = "test"

    result = await mock.simple_method()
    assert result == "test"


def test_simple_sync():
    """Simplest possible sync test."""
    assert True


@pytest.mark.asyncio
async def test_mock_embedding_service():
    """Test just the mock embedding service without other dependencies."""
    from tests.conftest import mock_embedding_service

    # Get the fixture manually without pytest fixture injection
    mock_service = AsyncMock()
    mock_service.get_embedding.return_value = [0.1] * 384

    result = await mock_service.get_embedding("test")
    assert len(result) == 384
    assert result[0] == 0.1


if __name__ == "__main__":
    # Run directly to test outside pytest
    import asyncio

    async def main():
        print("Testing simple async...")
        await test_simple_async()
        print("Simple async test passed!")

        print("Testing mock embedding...")
        await test_mock_embedding_service()
        print("Mock embedding test passed!")

        print("All tests passed!")

    asyncio.run(main())
