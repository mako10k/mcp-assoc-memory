"""
Basic integration tests for response_level functionality

Focuses on testing that all tools correctly implement response_level
without complex mocking that causes validation issues.
"""
import pytest
import time
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

from mcp_assoc_memory.api.models.common import ResponseLevel
from mcp_assoc_memory.api.models.requests import (
    ScopeListRequest,
    ScopeSuggestRequest,
    SessionManageRequest,
)

from mcp_assoc_memory.api.tools.scope_tools import (
    handle_scope_list,
    handle_scope_suggest,
)
from mcp_assoc_memory.api.tools.session_tools import handle_session_manage


class TestBasicResponseLevelIntegration:
    """Basic integration tests focusing on response structure consistency"""

    @pytest.mark.asyncio
    async def test_response_level_structure_consistency(self):
        """Test that all tools return consistent response structures across levels"""
        async with AsyncMock() as mock_context:

            # Test scope tools (simpler, less validation issues)
            with patch('mcp_assoc_memory.api.tools.scope_tools.get_or_create_memory_manager') as mock_scope_init:
                mock_memory_manager = MagicMock()
                mock_memory_manager.get_all_scopes = AsyncMock(return_value=["test/scope1", "test/scope2"])
                mock_memory_manager.get_memory_count_by_scope = AsyncMock(return_value=5)
                mock_scope_init.return_value = mock_memory_manager

                # Test all response levels for scope_list
                for level in [ResponseLevel.MINIMAL, ResponseLevel.STANDARD, ResponseLevel.FULL]:
                    request = ScopeListRequest(response_level=level)
                    result = await handle_scope_list(request, mock_context)

                    # Basic structure should be consistent
                    assert isinstance(result, dict), f"Response should be dict for {level.value}"
                    assert "success" in result, f"Missing 'success' for {level.value}"
                    assert "message" in result, f"Missing 'message' for {level.value}"

                    if result["success"]:
                        assert "total_scopes" in result, f"Missing 'total_scopes' for {level.value}"

                        # Check level-specific content
                        if level == ResponseLevel.MINIMAL:
                            # Minimal should have fewer fields
                            assert len(result) <= 5, f"Minimal response too verbose: {len(result)} fields"
                        elif level == ResponseLevel.FULL:
                            # Full should have more comprehensive data
                            assert "scopes" in result or "hierarchy_stats" in result, \
                                "Full response missing detailed data"

    @pytest.mark.asyncio
    async def test_scope_suggest_response_levels(self):
        """Test scope suggestion with different response levels"""
        async with AsyncMock() as mock_context:
            with patch('mcp_assoc_memory.api.tools.scope_tools.get_or_create_memory_manager') as mock_init:
                mock_memory_manager = MagicMock()
                mock_init.return_value = mock_memory_manager

                test_cases = [
                    ("Python programming tutorial", ResponseLevel.MINIMAL),
                    ("Python project meeting notes with debugging", ResponseLevel.STANDARD),
                    ("Python API design project documentation", ResponseLevel.FULL),
                ]

                for content, level in test_cases:
                    request = ScopeSuggestRequest(content=content, response_level=level)
                    result = await handle_scope_suggest(request, mock_context)

                    assert result["success"] is True, f"Failed for {content} with {level.value}"
                    assert "suggested_scope" in result, f"Missing suggested_scope for {level.value}"
                    assert "confidence" in result, f"Missing confidence for {level.value}"

                    # Check level-specific content
                    if level == ResponseLevel.MINIMAL:
                        # Should not have detailed reasoning
                        assert "reasoning" not in result, "Minimal should not have reasoning"
                        assert "alternatives" not in result, "Minimal should not have alternatives"
                    elif level == ResponseLevel.STANDARD:
                        # Should have reasoning and alternatives (may be empty if only one suggestion)
                        assert "reasoning" in result, "Standard should have reasoning"
                        assert "alternatives" in result, "Standard should have alternatives (may be empty)"
                        # Note: alternatives can be empty list if only one suggestion
                    elif level == ResponseLevel.FULL:
                        # Should have detailed analysis
                        assert "reasoning" in result, "Full should have reasoning"
                        assert "alternatives" in result, "Full should have alternatives"
                        assert "detailed_alternatives" in result, "Full should have detailed_alternatives"
                        assert "analysis_metadata" in result, "Full should have analysis_metadata"

    @pytest.mark.asyncio
    async def test_session_manage_response_levels(self):
        """Test session management with different response levels"""
        async with AsyncMock() as mock_context:
            with patch('mcp_assoc_memory.api.tools.session_tools.get_memory_manager') as mock_init:
                mock_memory_manager = MagicMock()
                mock_memory_manager.get_all_scopes = AsyncMock(return_value=["session/test-session-1", "session/test-session-2"])
                mock_memory_manager.search_memories = AsyncMock(return_value=[])
                mock_init.return_value = mock_memory_manager

                # Test session list operation
                for level in [ResponseLevel.MINIMAL, ResponseLevel.STANDARD, ResponseLevel.FULL]:
                    request = SessionManageRequest(action="list", response_level=level)
                    result = await handle_session_manage(request, mock_context)

                    assert result["success"] is True, f"Session list failed for {level.value}"
                    assert "message" in result, f"Missing message for {level.value}"

                    # Check response completeness based on level
                    response_size = len(str(result))
                    if level == ResponseLevel.MINIMAL:
                        assert response_size < 200, f"Minimal response too large: {response_size} chars"
                    elif level == ResponseLevel.FULL:
                        # Full responses should be more comprehensive
                        assert "data" in result and ("sessions" in result["data"] or "session_metadata" in result["data"]), \
                            "Full response missing detailed session data"

    @pytest.mark.asyncio
    async def test_error_handling_consistency(self):
        """Test that error responses are consistent across tools and levels"""
        async with AsyncMock() as mock_context:

            # Test error handling for scope_suggest
            with patch('mcp_assoc_memory.api.tools.scope_tools.get_or_create_memory_manager') as mock_init:
                mock_init.return_value = None  # Simulate initialization failure

                for level in [ResponseLevel.MINIMAL, ResponseLevel.STANDARD, ResponseLevel.FULL]:
                    request = ScopeSuggestRequest(content="test", response_level=level)
                    result = await handle_scope_suggest(request, mock_context)

                    # Error responses should be consistent regardless of level
                    assert result["success"] is False, f"Should fail for {level.value}"
                    assert "message" in result, f"Error should have message for {level.value}"
                    assert "error" in result, f"Error should have error field for {level.value}"

                    # Error responses should be concise regardless of requested level
                    assert len(str(result)) < 300, f"Error response too verbose for {level.value}"

    @pytest.mark.asyncio
    async def test_performance_basic(self):
        """Basic performance test - ensure responses complete within reasonable time"""
        async with AsyncMock() as mock_context:
            with patch('mcp_assoc_memory.api.tools.scope_tools.get_or_create_memory_manager') as mock_init:
                mock_memory_manager = MagicMock()
                mock_init.return_value = mock_memory_manager

                # Test response time for scope_suggest (least complex)
                start_time = time.time()

                request = ScopeSuggestRequest(
                    content="Performance test content",
                    response_level=ResponseLevel.STANDARD
                )
                result = await handle_scope_suggest(request, mock_context)

                end_time = time.time()
                duration = end_time - start_time

                assert result["success"] is True, "Performance test should succeed"
                assert duration < 2.0, f"Response too slow: {duration:.3f}s"

    @pytest.mark.asyncio
    async def test_null_value_handling(self):
        """Test that null/None values are properly handled in responses"""
        async with AsyncMock() as mock_context:
            with patch('mcp_assoc_memory.api.tools.scope_tools.get_or_create_memory_manager') as mock_init:
                mock_memory_manager = MagicMock()
                mock_init.return_value = mock_memory_manager

                # Test with explicit None values
                request = ScopeSuggestRequest(
                    content="test content",
                    current_scope=None,  # Explicitly None
                    response_level=ResponseLevel.STANDARD
                )
                result = await handle_scope_suggest(request, mock_context)

                assert result["success"] is True
                # None values should be cleaned from response
                assert "current_scope" not in result, \
                    "None values should be removed by ResponseBuilder"

                # But other fields should still be present
                assert "suggested_scope" in result
                assert "confidence" in result

    @pytest.mark.asyncio
    async def test_default_response_level(self):
        """Test that default response level works correctly"""
        async with AsyncMock() as mock_context:
            with patch('mcp_assoc_memory.api.tools.scope_tools.get_or_create_memory_manager') as mock_init:
                mock_memory_manager = MagicMock()
                mock_init.return_value = mock_memory_manager

                # Test without specifying response_level (should default to STANDARD)
                request = ScopeSuggestRequest(content="Python project meeting notes with debugging")
                result = await handle_scope_suggest(request, mock_context)

                assert result["success"] is True
                # Should include standard-level fields
                assert "reasoning" in result, "Default level should include reasoning"
                assert "alternatives" in result, "Default level should include alternatives (may be empty)"
                # Should not include full-level fields
                assert "detailed_alternatives" not in result, \
                    "Default level should not include full-level details"
