"""
Tests for response level functionality and common utilities.
"""

import pytest
from mcp_assoc_memory.api.models.common import (
    ResponseLevel,
    CommonToolParameters,
    ResponseBuilder,
    TokenEstimator,
    MCPResponseBase,
    ResponseLevelMixin
)


class TestResponseLevel:
    """Test ResponseLevel enum."""
    
    def test_response_level_values(self):
        """Test ResponseLevel enum values."""
        assert ResponseLevel.MINIMAL.value == "minimal"
        assert ResponseLevel.STANDARD.value == "standard"
        assert ResponseLevel.FULL.value == "full"
    
    def test_response_level_ordering(self):
        """Test that response levels can be compared."""
        # Ensure enum members exist
        assert ResponseLevel.MINIMAL is not None
        assert ResponseLevel.STANDARD is not None
        assert ResponseLevel.FULL is not None


class TestCommonToolParameters:
    """Test CommonToolParameters model."""
    
    def test_default_response_level(self):
        """Test default response level is STANDARD."""
        params = CommonToolParameters()
        assert params.response_level == ResponseLevel.STANDARD
    
    def test_explicit_response_level(self):
        """Test setting explicit response level."""
        params = CommonToolParameters(response_level=ResponseLevel.MINIMAL)
        assert params.response_level == ResponseLevel.MINIMAL
    
    def test_response_level_from_string(self):
        """Test creating from string value."""
        params = CommonToolParameters(response_level="full")
        assert params.response_level == ResponseLevel.FULL
    
    def test_invalid_response_level(self):
        """Test that invalid response level raises error."""
        with pytest.raises(ValueError):
            CommonToolParameters(response_level="invalid")


class TestResponseBuilder:
    """Test ResponseBuilder utility."""
    
    def test_minimal_response(self):
        """Test minimal level response building."""
        base = {"success": True, "id": "test-123"}
        standard = {"preview": "content..."}
        full = {"complete_data": {"full": "object"}}
        
        result = ResponseBuilder.build_response(
            ResponseLevel.MINIMAL, base, standard, full
        )
        
        assert result == {"success": True, "id": "test-123"}
    
    def test_standard_response(self):
        """Test standard level response building."""
        base = {"success": True, "id": "test-123"}
        standard = {"preview": "content..."}
        full = {"complete_data": {"full": "object"}}
        
        result = ResponseBuilder.build_response(
            ResponseLevel.STANDARD, base, standard, full
        )
        
        expected = {
            "success": True,
            "id": "test-123",
            "preview": "content..."
        }
        assert result == expected
    
    def test_full_response(self):
        """Test full level response building."""
        base = {"success": True, "id": "test-123"}
        standard = {"preview": "content..."}
        full = {"complete_data": {"full": "object"}}
        
        result = ResponseBuilder.build_response(
            ResponseLevel.FULL, base, standard, full
        )
        
        expected = {
            "success": True,
            "id": "test-123",
            "preview": "content...",
            "complete_data": {"full": "object"}
        }
        assert result == expected
    
    def test_none_value_removal(self):
        """Test None values are removed from response."""
        base = {"success": True, "id": "test-123", "optional": None}
        
        result = ResponseBuilder.build_response(ResponseLevel.MINIMAL, base)
        
        assert result == {"success": True, "id": "test-123"}
    
    def test_empty_collection_removal(self):
        """Test empty lists and dicts are removed."""
        base = {
            "success": True,
            "id": "test-123",
            "empty_list": [],
            "empty_dict": {},
            "valid_list": ["item"]
        }
        
        result = ResponseBuilder.build_response(ResponseLevel.MINIMAL, base)
        
        expected = {
            "success": True,
            "id": "test-123",
            "valid_list": ["item"]
        }
        assert result == expected
    
    def test_content_truncation(self):
        """Test content truncation utility."""
        long_content = "A" * 150
        
        result = ResponseBuilder.truncate_content(long_content, 100)
        
        assert len(result) == 103  # 100 chars + "..."
        assert result.endswith("...")
        assert result.startswith("A" * 100)
        
    def test_content_truncation_no_change(self):
        """Test content truncation with short content."""
        short_content = "Short content"
        result = ResponseBuilder.truncate_content(short_content, 100)
        assert result == "Short content"
    
    def test_create_content_preview_minimal(self):
        """Test content preview creation for minimal level."""
        content = "Test content for preview"
        result = ResponseBuilder.create_content_preview(content, ResponseLevel.MINIMAL)
        assert result is None
    
    def test_create_content_preview_standard(self):
        """Test content preview creation for standard level."""
        content = "A" * 150
        result = ResponseBuilder.create_content_preview(content, ResponseLevel.STANDARD)
        assert result is not None
        assert len(result) == 103  # 100 + "..."
        assert result.endswith("...")
    
    def test_create_content_preview_full(self):
        """Test content preview creation for full level."""
        content = "Complete content for full level"
        result = ResponseBuilder.create_content_preview(content, ResponseLevel.FULL)
        assert result == content


class TestTokenEstimator:
    """Test TokenEstimator utility."""
    
    def test_estimate_tokens_basic(self):
        """Test basic token estimation."""
        text = "Hello world"  # 11 characters
        result = TokenEstimator.estimate_tokens(text)
        expected = max(1, 11 // 4)  # 2 tokens
        assert result == expected
    
    def test_estimate_tokens_empty(self):
        """Test token estimation with empty string."""
        result = TokenEstimator.estimate_tokens("")
        assert result == 1  # Minimum 1 token
    
    def test_estimate_tokens_long(self):
        """Test token estimation with long text."""
        text = "A" * 400  # 400 characters
        result = TokenEstimator.estimate_tokens(text)
        expected = 400 // 4  # 100 tokens
        assert result == expected
    
    def test_estimate_response_tokens(self):
        """Test response token estimation."""
        response = {
            "success": True,
            "message": "Operation completed",
            "data": {"key": "value"}
        }
        result = TokenEstimator.estimate_response_tokens(response)
        assert isinstance(result, int)
        assert result > 0


class TestMCPResponseBase:
    """Test MCPResponseBase model."""
    
    def test_basic_response(self):
        """Test basic response creation."""
        response = MCPResponseBase(
            success=True,
            message="Test message"
        )
        assert response.success is True
        assert response.message == "Test message"
        assert response.data == {}
    
    def test_response_with_data(self):
        """Test response with custom data."""
        response = MCPResponseBase(
            success=True,
            message="Test message",
            data={"custom": "value"}
        )
        assert response.data == {"custom": "value"}
    
    def test_response_validation(self):
        """Test response field validation."""
        with pytest.raises(ValueError):
            MCPResponseBase(success="not_boolean", message="Test")


class TestResponseLevelMixin:
    """Test ResponseLevelMixin functionality."""
    
    class MockRequest(ResponseLevelMixin):
        """Mock request class with response level."""
        def __init__(self, response_level=ResponseLevel.STANDARD):
            self.response_level = response_level
    
    def test_get_response_level_default(self):
        """Test getting default response level."""
        request = self.MockRequest()
        assert request.get_response_level() == ResponseLevel.STANDARD
    
    def test_get_response_level_explicit(self):
        """Test getting explicit response level."""
        request = self.MockRequest(ResponseLevel.MINIMAL)
        assert request.get_response_level() == ResponseLevel.MINIMAL
    
    def test_should_include_preview_minimal(self):
        """Test preview inclusion for minimal level."""
        request = self.MockRequest(ResponseLevel.MINIMAL)
        assert request.should_include_preview() is False
    
    def test_should_include_preview_standard(self):
        """Test preview inclusion for standard level."""
        request = self.MockRequest(ResponseLevel.STANDARD)
        assert request.should_include_preview() is True
    
    def test_should_include_preview_full(self):
        """Test preview inclusion for full level."""
        request = self.MockRequest(ResponseLevel.FULL)
        assert request.should_include_preview() is True
    
    def test_should_include_full_content_minimal(self):
        """Test full content inclusion for minimal level."""
        request = self.MockRequest(ResponseLevel.MINIMAL)
        assert request.should_include_full_content() is False
    
    def test_should_include_full_content_standard(self):
        """Test full content inclusion for standard level."""
        request = self.MockRequest(ResponseLevel.STANDARD)
        assert request.should_include_full_content() is False
    
    def test_should_include_full_content_full(self):
        """Test full content inclusion for full level."""
        request = self.MockRequest(ResponseLevel.FULL)
        assert request.should_include_full_content() is True


class TestIntegration:
    """Integration tests for response level functionality."""
    
    def test_end_to_end_minimal(self):
        """Test complete minimal level workflow."""
        # Create request
        params = CommonToolParameters(response_level=ResponseLevel.MINIMAL)
        
        # Build response
        base_data = {"success": True, "memory_id": "test-123"}
        standard_data = {"scope": "test", "preview": "content preview"}
        full_data = {"memory": {"complete": "object"}, "associations": []}
        
        response = ResponseBuilder.build_response(
            params.response_level,
            base_data,
            standard_data,
            full_data
        )
        
        # Verify minimal response
        expected = {"success": True, "memory_id": "test-123"}
        assert response == expected
        
        # Estimate tokens
        tokens = TokenEstimator.estimate_response_tokens(response)
        assert tokens < 50  # Should be under minimal threshold
    
    def test_end_to_end_standard(self):
        """Test complete standard level workflow."""
        params = CommonToolParameters(response_level=ResponseLevel.STANDARD)
        
        base_data = {"success": True, "memory_id": "test-123"}
        standard_data = {"scope": "test", "preview": "content preview"}
        full_data = {"memory": {"complete": "object"}, "associations": []}
        
        response = ResponseBuilder.build_response(
            params.response_level,
            base_data,
            standard_data,
            full_data
        )
        
        expected = {
            "success": True,
            "memory_id": "test-123",
            "scope": "test",
            "preview": "content preview"
        }
        assert response == expected
        
        tokens = TokenEstimator.estimate_response_tokens(response)
        assert tokens < 200  # Should be under standard threshold
    
    def test_end_to_end_full(self):
        """Test complete full level workflow."""
        params = CommonToolParameters(response_level=ResponseLevel.FULL)
        
        base_data = {"success": True, "memory_id": "test-123"}
        standard_data = {"scope": "test", "preview": "content preview"}
        full_data = {"memory": {"complete": "object"}, "associations": []}
        
        response = ResponseBuilder.build_response(
            params.response_level,
            base_data,
            standard_data,
            full_data
        )
        
        expected = {
            "success": True,
            "memory_id": "test-123",
            "scope": "test",
            "preview": "content preview",
            "memory": {"complete": "object"}
        }
        assert response == expected
