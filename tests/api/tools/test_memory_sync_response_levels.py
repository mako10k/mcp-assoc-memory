"""Comprehensive response level tests for memory_sync tool."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Any, Dict

from src.mcp_assoc_memory.api.tools.memory_tools import handle_memory_sync
from src.mcp_assoc_memory.api.models.requests import MemorySyncRequest
from src.mcp_assoc_memory.api.models.common import ResponseLevel, CommonToolParameters


class TestMemorySyncResponseLevels:
    """Test memory_sync tool with different response levels."""

    @pytest.fixture
    def mock_context(self):
        """Create mock context for testing."""
        context = AsyncMock()
        context.info = AsyncMock()
        context.error = AsyncMock()
        return context

    @pytest.fixture
    def mock_export_response(self):
        """Create mock export response."""
        return {
            "success": True,
            "exported_count": 5,
            "file_path": "test/export.json",
            "export_format": "json",
            "scope": "test/scope"
        }

    @pytest.fixture
    def mock_import_response(self):
        """Create mock import response."""
        response = MagicMock()
        response.dict.return_value = {
            "success": True,
            "imported_count": 3,
            "skipped_count": 1,
            "error_count": 0,
            "import_summary": {}
        }
        return response

    @pytest.mark.asyncio
    async def test_request_inheritance(self):
        """Test that MemorySyncRequest properly inherits from CommonToolParameters."""
        request = MemorySyncRequest(
            operation="export",
            file_path="test.json",
            response_level=ResponseLevel.STANDARD
        )

        # Test inheritance
        assert isinstance(request, CommonToolParameters)
        assert hasattr(request, 'response_level')
        assert request.response_level == ResponseLevel.STANDARD

        # Test default response level
        request_default = MemorySyncRequest(
            operation="export",
            file_path="test.json"
        )
        assert request_default.response_level == ResponseLevel.STANDARD

    @pytest.mark.asyncio
    async def test_memory_sync_export_minimal_response(self, mock_context, mock_export_response):
        """Test memory sync export with minimal response level."""
        request = MemorySyncRequest(
            operation="export",
            file_path="test/export.json",
            scope="test/scope",
            response_level=ResponseLevel.MINIMAL
        )

        with patch('src.mcp_assoc_memory.api.tools.memory_tools.handle_memory_export') as mock_export:
            mock_export.return_value = mock_export_response

            response = await handle_memory_sync(request, mock_context)

            # Verify minimal response structure
            assert response["success"] is True
            assert response["operation"] == "export"
            assert response["exported_count"] == 5

            # Minimal response should not include detailed data
            assert "file_path" not in response
            assert "export_details" not in response
            assert "scope" not in response

    @pytest.mark.asyncio
    async def test_memory_sync_export_standard_response(self, mock_context, mock_export_response):
        """Test memory sync export with standard response level."""
        request = MemorySyncRequest(
            operation="export",
            file_path="test/export.json",
            scope="test/scope",
            include_associations=True,
            response_level=ResponseLevel.STANDARD
        )

        with patch('src.mcp_assoc_memory.api.tools.memory_tools.handle_memory_export') as mock_export:
            mock_export.return_value = mock_export_response

            response = await handle_memory_sync(request, mock_context)

            # Verify standard response structure
            assert response["success"] is True
            assert response["operation"] == "export"
            assert response["exported_count"] == 5
            assert response["file_path"] == "test/export.json"
            assert response["scope"] == "test/scope"
            assert response["include_associations"] is True

            # Standard response should not include full details
            assert "export_details" not in response

    @pytest.mark.asyncio
    async def test_memory_sync_export_full_response(self, mock_context, mock_export_response):
        """Test memory sync export with full response level."""
        request = MemorySyncRequest(
            operation="export",
            file_path="test/export.json",
            scope="test/scope",
            include_associations=True,
            compression=True,
            response_level=ResponseLevel.FULL
        )

        with patch('src.mcp_assoc_memory.api.tools.memory_tools.handle_memory_export') as mock_export:
            mock_export.return_value = mock_export_response

            response = await handle_memory_sync(request, mock_context)

            # Verify full response structure
            assert response["success"] is True
            assert response["operation"] == "export"
            assert response["exported_count"] == 5
            assert response["file_path"] == "test/export.json"
            assert response["scope"] == "test/scope"
            assert response["include_associations"] is True
            assert "export_details" in response
            assert response["compression_enabled"] is True
            assert response["format"] == "json"

    @pytest.mark.asyncio
    async def test_memory_sync_import_minimal_response(self, mock_context, mock_import_response):
        """Test memory sync import with minimal response level."""
        request = MemorySyncRequest(
            operation="import",
            file_path="test/import.json",
            scope="test/target",
            response_level=ResponseLevel.MINIMAL
        )

        with patch('src.mcp_assoc_memory.api.tools.memory_tools.handle_memory_import') as mock_import:
            mock_import.return_value = mock_import_response

            response = await handle_memory_sync(request, mock_context)

            # Verify minimal response structure
            assert response["success"] is True
            assert response["operation"] == "import"
            assert response["imported_count"] == 3

            # Minimal response should not include detailed data
            assert "file_path" not in response
            assert "import_details" not in response
            assert "target_scope" not in response

    @pytest.mark.asyncio
    async def test_memory_sync_import_standard_response(self, mock_context, mock_import_response):
        """Test memory sync import with standard response level."""
        request = MemorySyncRequest(
            operation="import",
            file_path="test/import.json",
            scope="test/target",
            response_level=ResponseLevel.STANDARD
        )

        with patch('src.mcp_assoc_memory.api.tools.memory_tools.handle_memory_import') as mock_import:
            mock_import.return_value = mock_import_response

            response = await handle_memory_sync(request, mock_context)

            # Verify standard response structure
            assert response["success"] is True
            assert response["operation"] == "import"
            assert response["imported_count"] == 3
            assert response["file_path"] == "test/import.json"
            assert response["target_scope"] == "test/target"
            assert response["skipped_count"] == 1

            # Standard response should not include full details
            assert "import_details" not in response

    @pytest.mark.asyncio
    async def test_memory_sync_import_full_response(self, mock_context, mock_import_response):
        """Test memory sync import with full response level."""
        request = MemorySyncRequest(
            operation="import",
            file_path="test/import.json",
            scope="test/target",
            response_level=ResponseLevel.FULL
        )

        with patch('src.mcp_assoc_memory.api.tools.memory_tools.handle_memory_import') as mock_import:
            mock_import.return_value = mock_import_response

            response = await handle_memory_sync(request, mock_context)

            # Verify full response structure
            assert response["success"] is True
            assert response["operation"] == "import"
            assert response["imported_count"] == 3
            assert response["file_path"] == "test/import.json"
            assert response["target_scope"] == "test/target"
            assert response["skipped_count"] == 1
            assert "import_details" in response
            assert response["merge_strategy"] == "skip_duplicates"
            assert response["validation_enabled"] is True

    @pytest.mark.asyncio
    async def test_memory_sync_invalid_operation(self, mock_context):
        """Test memory sync with invalid operation."""
        request = MemorySyncRequest(
            operation="invalid_op",
            file_path="test.json",
            response_level=ResponseLevel.MINIMAL
        )

        response = await handle_memory_sync(request, mock_context)

        # Verify error response
        assert response["success"] is False
        assert "error" in response
        assert "Unknown sync operation" in response["error"]
        assert response["operation"] == "invalid_op"

    @pytest.mark.asyncio
    async def test_memory_sync_exception_handling(self, mock_context):
        """Test memory sync with exception during operation."""
        request = MemorySyncRequest(
            operation="export",
            file_path="test.json",
            response_level=ResponseLevel.FULL
        )

        with patch('src.mcp_assoc_memory.api.tools.memory_tools.handle_memory_export') as mock_export:
            mock_export.side_effect = Exception("Export failed")

            response = await handle_memory_sync(request, mock_context)

            # Verify error response
            assert response["success"] is False
            assert "error" in response
            assert "Memory sync operation failed" in response["error"]
            assert response["operation"] == "export"

    def test_response_size_estimates(self):
        """Test response size estimates for different levels."""
        # Minimal response fields
        minimal_fields = ["success", "operation", "exported_count"]
        minimal_estimated_size = len(str(minimal_fields)) + 100  # Conservative estimate
        assert minimal_estimated_size < 200  # Should be under 200 chars

        # Standard response includes file details
        standard_additional = ["file_path", "scope", "include_associations"]
        standard_estimated_size = minimal_estimated_size + len(str(standard_additional)) + 300
        assert standard_estimated_size < 800  # Should be reasonable

        # Full response includes complete operation details
        full_additional = ["export_details", "compression_enabled", "format"]
        full_estimated_size = standard_estimated_size + len(str(full_additional)) + 500
        assert full_estimated_size > standard_estimated_size  # Should be larger than standard

    @pytest.mark.asyncio
    async def test_memory_sync_ensure_initialized(self, mock_context):
        """Test that ensure_initialized is called."""
        request = MemorySyncRequest(
            operation="export",
            file_path="test.json",
            response_level=ResponseLevel.MINIMAL
        )

        with patch('src.mcp_assoc_memory.api.tools.memory_tools.ensure_initialized') as mock_init:
            with patch('src.mcp_assoc_memory.api.tools.memory_tools.handle_memory_export') as mock_export:
                mock_export.return_value = {"success": True, "exported_count": 0}

                await handle_memory_sync(request, mock_context)

                # Verify ensure_initialized was called
                mock_init.assert_called_once()

    @pytest.mark.asyncio
    async def test_memory_sync_operations_delegation(self, mock_context, mock_export_response, mock_import_response):
        """Test that operations are properly delegated to specific handlers."""
        # Test export delegation
        export_request = MemorySyncRequest(
            operation="export",
            file_path="test.json",
            response_level=ResponseLevel.MINIMAL
        )

        with patch('src.mcp_assoc_memory.api.tools.memory_tools.handle_memory_export') as mock_export:
            mock_export.return_value = mock_export_response

            await handle_memory_sync(export_request, mock_context)

            # Verify export handler was called
            mock_export.assert_called_once()
            call_args = mock_export.call_args[0][0]  # First argument (export request)
            assert call_args.file_path == "test.json"
            assert call_args.export_format == "json"

        # Test import delegation
        import_request = MemorySyncRequest(
            operation="import",
            file_path="test.json",
            response_level=ResponseLevel.MINIMAL
        )

        with patch('src.mcp_assoc_memory.api.tools.memory_tools.handle_memory_import') as mock_import:
            mock_import.return_value = mock_import_response

            await handle_memory_sync(import_request, mock_context)

            # Verify import handler was called
            mock_import.assert_called_once()
            call_args = mock_import.call_args[0][0]  # First argument (import request)
            assert call_args.file_path == "test.json"
            assert call_args.merge_strategy == "skip_duplicates"
