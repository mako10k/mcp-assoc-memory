"""
Tests for scope_suggest response level functionality
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from mcp_assoc_memory.api.models.requests import ScopeSuggestRequest
from mcp_assoc_memory.api.models.common import ResponseLevel
from mcp_assoc_memory.api.tools.scope_tools import handle_scope_suggest


@pytest.mark.asyncio
async def test_scope_suggest_minimal_response():
    """Test scope suggestion with minimal response level"""
    async with AsyncMock() as mock_context:
        request = ScopeSuggestRequest(
            content="Python programming tutorial notes",
            response_level=ResponseLevel.MINIMAL
        )

        # Mock the singleton memory manager to prevent actual initialization
        with patch('mcp_assoc_memory.api.tools.scope_tools.get_or_create_memory_manager') as mock_singleton:
            mock_memory_manager = MagicMock()
            mock_singleton.return_value = mock_memory_manager

            result = await handle_scope_suggest(request, mock_context)

            assert result["success"] is True
            assert "suggested_scope" in result
            assert "confidence" in result
            # Minimal response should not include detailed reasoning
            assert "reasoning" not in result
            assert "alternatives" not in result


@pytest.mark.asyncio
async def test_scope_suggest_standard_response():
    """Test scope suggestion with standard response level"""
    async with AsyncMock() as mock_context:
        request = ScopeSuggestRequest(
            content="Python programming tutorial notes",
            response_level=ResponseLevel.STANDARD
        )

        with patch('mcp_assoc_memory.api.tools.scope_tools.get_or_create_memory_manager') as mock_singleton:
            mock_memory_manager = MagicMock()
            mock_singleton.return_value = mock_memory_manager

            result = await handle_scope_suggest(request, mock_context)

            assert result["success"] is True
            assert "suggested_scope" in result
            assert result["suggested_scope"] == "learning/programming"
            assert "confidence" in result
            # Standard response should include reasoning and alternatives
            assert "reasoning" in result
            assert "alternatives" in result
            # current_scope should only be present if it was provided in request
            if request.current_scope is not None:
                assert "current_scope" in result


@pytest.mark.asyncio
async def test_scope_suggest_full_response():
    """Test scope suggestion with full response level"""
    async with AsyncMock() as mock_context:
        request = ScopeSuggestRequest(
            content="Meeting notes from standup discussion about project deadlines",
            response_level=ResponseLevel.FULL
        )

        with patch('mcp_assoc_memory.api.tools.scope_tools.get_or_create_memory_manager') as mock_singleton:
            mock_memory_manager = MagicMock()
            mock_singleton.return_value = mock_memory_manager

            result = await handle_scope_suggest(request, mock_context)

            assert result["success"] is True
            assert "suggested_scope" in result
            assert "confidence" in result
            # Full response should include all metadata
            assert "reasoning" in result
            assert "alternatives" in result
            assert "detailed_alternatives" in result
            assert "analysis_metadata" in result

            # Check analysis metadata structure
            metadata = result["analysis_metadata"]
            assert "content_length" in metadata
            assert "context_aware" in metadata
            assert metadata["content_length"] > 0


@pytest.mark.asyncio
async def test_scope_suggest_with_context():
    """Test scope suggestion with current_scope context"""
    async with AsyncMock() as mock_context:
        request = ScopeSuggestRequest(
            content="New feature implementation notes",
            current_scope="work/projects/app-development",
            response_level=ResponseLevel.STANDARD
        )

        with patch('mcp_assoc_memory.api.tools.scope_tools.get_or_create_memory_manager') as mock_singleton:
            mock_memory_manager = MagicMock()
            mock_singleton.return_value = mock_memory_manager

            result = await handle_scope_suggest(request, mock_context)

            assert result["success"] is True
            assert "current_scope" in result
            assert result["current_scope"] == "work/projects/app-development"
            # Should suggest work-related scope due to context
            assert result["suggested_scope"].startswith("work/")


@pytest.mark.asyncio
async def test_scope_suggest_error_response():
    """Test scope suggestion error handling with response levels"""
    async with AsyncMock() as mock_context:
        request = ScopeSuggestRequest(
            content="Test content",
            response_level=ResponseLevel.STANDARD
        )

        with patch('mcp_assoc_memory.api.tools.scope_tools.get_or_create_memory_manager') as mock_singleton:
            # Mock error condition
            mock_singleton.side_effect = Exception("Test error")

            result = await handle_scope_suggest(request, mock_context)

            assert result["success"] is False
            assert "Failed to suggest scope" in result["message"]
            assert "error" in result


@pytest.mark.asyncio
async def test_scope_suggest_keyword_detection():
    """Test scope suggestion keyword detection"""
    test_cases = [
        ("Python programming tutorial", "learning/programming"),
        ("Meeting notes from standup", "work/meetings"),
        ("Personal diary entry", "personal/thoughts"),
        ("API endpoint documentation", "learning/api-design"),
        ("Bug fix implementation", "work/debugging"),
    ]

    for content, expected_scope in test_cases:
        async with AsyncMock() as mock_context:
            request = ScopeSuggestRequest(
                content=content,
                response_level=ResponseLevel.STANDARD
            )

            with patch('mcp_assoc_memory.api.tools.scope_tools.get_or_create_memory_manager') as mock_singleton:
                mock_memory_manager = MagicMock()
                mock_singleton.return_value = mock_memory_manager

                result = await handle_scope_suggest(request, mock_context)

                assert result["success"] is True
                assert result["suggested_scope"] == expected_scope, f"Content: {content}, Expected: {expected_scope}, Got: {result['suggested_scope']}"


@pytest.mark.asyncio
async def test_scope_suggest_memory_manager_none():
    """Test scope suggestion when memory manager is None"""
    async with AsyncMock() as mock_context:
        request = ScopeSuggestRequest(
            content="Test content",
            response_level=ResponseLevel.MINIMAL
        )

        with patch('mcp_assoc_memory.api.tools.scope_tools.get_or_create_memory_manager') as mock_singleton:
            mock_singleton.return_value = None

            result = await handle_scope_suggest(request, mock_context)

            assert result["success"] is False
            assert "Internal server error" in result["message"]
            assert "error" in result
