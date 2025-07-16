"""
Common models and utilities for MCP tools response level management.
"""

from enum import Enum
from typing import Any, Dict, Optional, Union
from pydantic import BaseModel, Field


class ResponseLevel(Enum):
    """Response detail level for all MCP tools."""

    MINIMAL = "minimal"
    STANDARD = "standard"
    FULL = "full"


class CommonToolParameters(BaseModel):
    """Common parameters inherited by all MCP tools."""

    response_level: ResponseLevel = Field(
        default=ResponseLevel.STANDARD,
        description=(
            "Response detail level:\n"
            "• minimal: Success status + essential IDs only (minimal tokens)\n"
            "• standard: Balanced info for workflow continuity + content previews\n"
            "• full: Complete data + metadata + associations (maximum detail)"
        ),
    )


class ResponseBuilder:
    """Helper for building level-appropriate responses."""

    @staticmethod
    def build_response(
        level: ResponseLevel,
        base_data: Dict[str, Any],
        standard_data: Optional[Dict[str, Any]] = None,
        full_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Build response according to specified level.

        Args:
            level: Response detail level
            base_data: Always included (minimal level)
            standard_data: Added for standard and full levels
            full_data: Added only for full level

        Returns:
            Level-appropriate response dictionary
        """
        response = base_data.copy()

        if level == ResponseLevel.MINIMAL:
            return ResponseBuilder._clean_response(response)

        if level in [ResponseLevel.STANDARD, ResponseLevel.FULL] and standard_data:
            response.update(standard_data)

        if level == ResponseLevel.FULL and full_data:
            response.update(full_data)

        return ResponseBuilder._clean_response(response)

    @staticmethod
    def _clean_response(response: Dict[str, Any]) -> Dict[str, Any]:
        """Remove None values and empty collections to minimize response size."""
        cleaned = {}
        for key, value in response.items():
            if value is not None:
                if isinstance(value, (list, dict)) and len(value) == 0:
                    continue  # Skip empty collections
                cleaned[key] = value
        return cleaned

    @staticmethod
    def truncate_content(content: str, max_chars: int = 100) -> str:
        """
        Truncate content for preview with ellipsis.

        Args:
            content: Content to truncate
            max_chars: Maximum characters to keep

        Returns:
            Truncated content with ellipsis if needed
        """
        if len(content) <= max_chars:
            return content
        return content[:max_chars] + "..."

    @staticmethod
    def create_content_preview(content: str, level: ResponseLevel) -> Optional[str]:
        """
        Create content preview based on response level.

        Args:
            content: Full content
            level: Response level

        Returns:
            Content preview or None for minimal level
        """
        if level == ResponseLevel.MINIMAL:
            return None
        elif level == ResponseLevel.STANDARD:
            return ResponseBuilder.truncate_content(content, 100)
        else:  # FULL
            return content


class TokenEstimator:
    """Utility for estimating token counts in responses."""

    @staticmethod
    def estimate_tokens(text: str) -> int:
        """
        Rough token estimation (1 token ≈ 4 characters for English).

        Args:
            text: Text to estimate

        Returns:
            Estimated token count
        """
        return max(1, len(text) // 4)

    @staticmethod
    def estimate_response_tokens(response: Dict[str, Any]) -> int:
        """
        Estimate total tokens in response.

        Args:
            response: Response dictionary

        Returns:
            Estimated total token count
        """
        total_chars = len(str(response))
        return TokenEstimator.estimate_tokens(str(total_chars))


class MCPResponseBase(BaseModel):
    """Base class for all MCP tool responses."""

    success: bool = Field(description="Operation success status")
    message: str = Field(description="Brief operation result message")
    data: Dict[str, Any] = Field(default_factory=dict, description="Additional response data")

    class Config:
        """Pydantic configuration."""

        extra = "forbid"  # Prevent accidental field additions
        validate_assignment = True


class ResponseLevelMixin:
    """Mixin for adding response level functionality to tool parameter classes."""

    def get_response_level(self) -> ResponseLevel:
        """Get the response level from the request."""
        return getattr(self, "response_level", ResponseLevel.STANDARD)

    def should_include_preview(self) -> bool:
        """Check if content previews should be included."""
        return self.get_response_level() != ResponseLevel.MINIMAL

    def should_include_full_content(self) -> bool:
        """Check if full content should be included."""
        return self.get_response_level() == ResponseLevel.FULL
