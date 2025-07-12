"""
Enhanced error handling system for MCP Associative Memory Server

This module provides comprehensive error management with:
- Specific error types for different failure scenarios
- User-friendly error messages with actionable guidance
- Detailed debugging information for developers
- Structured error responses for consistent API behavior
"""

import traceback
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from fastmcp import Context


class ErrorSeverity(Enum):
    """Error severity levels for proper escalation and handling"""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Categories of errors for proper classification and handling"""

    USER_INPUT = "user_input"  # Invalid input parameters, validation errors
    SYSTEM = "system"  # Database errors, file system issues
    NETWORK = "network"  # Connection timeouts, API failures
    AUTHENTICATION = "authentication"  # Permission denied, invalid credentials
    RESOURCE = "resource"  # Memory limits, disk space, etc.
    LOGIC = "logic"  # Business logic errors, invalid state
    DEPENDENCY = "dependency"  # External service failures
    TEMPORARY = "temporary"  # Transient issues that might resolve


@dataclass
class ErrorDetails:
    """Structured error information for consistent handling"""

    code: str  # Error identifier (e.g., "MEMORY_NOT_FOUND")
    category: ErrorCategory
    severity: ErrorSeverity
    message: str  # User-friendly message
    technical_message: str  # Technical details for debugging
    suggestions: List[str]  # Actionable user guidance
    context: Dict[str, Any]  # Additional context information
    timestamp: datetime
    stack_trace: Optional[str] = None  # Stack trace for debugging


class MCPError(Exception):
    """Base exception for MCP Associative Memory errors"""

    def __init__(self, details: ErrorDetails):
        self.details = details
        super().__init__(details.message)


class MemoryNotFoundError(MCPError):
    """Memory with specified ID not found"""

    def __init__(self, memory_id: str, context: Dict[str, Any] = None):
        details = ErrorDetails(
            code="MEMORY_NOT_FOUND",
            category=ErrorCategory.USER_INPUT,
            severity=ErrorSeverity.WARNING,
            message=f"Memory with ID '{memory_id}' was not found",
            technical_message=f"Memory lookup failed for ID: {memory_id}",
            suggestions=[
                "Verify the memory ID is correct",
                "Use memory_search to find the memory by content",
                "Check if the memory exists in a different scope",
            ],
            context={"memory_id": memory_id, **(context or {})},
            timestamp=datetime.now(),
        )
        super().__init__(details)


class InvalidScopeError(MCPError):
    """Invalid scope format or non-existent scope"""

    def __init__(self, scope: str, context: Dict[str, Any] = None):
        details = ErrorDetails(
            code="INVALID_SCOPE",
            category=ErrorCategory.USER_INPUT,
            severity=ErrorSeverity.WARNING,
            message=f"Invalid scope format: '{scope}'",
            technical_message=f"Scope validation failed: {scope}",
            suggestions=[
                "Use format: category/subcategory (e.g., work/projects)",
                "Check available scopes with scope_list",
                "Use scope_suggest for automatic categorization",
            ],
            context={"scope": scope, **(context or {})},
            timestamp=datetime.now(),
        )
        super().__init__(details)


class DatabaseConnectionError(MCPError):
    """Database connection or query failure"""

    def __init__(self, operation: str, original_error: Exception, context: Dict[str, Any] = None):
        details = ErrorDetails(
            code="DATABASE_CONNECTION_ERROR",
            category=ErrorCategory.SYSTEM,
            severity=ErrorSeverity.ERROR,
            message="Database connection failed - please try again in a moment",
            technical_message=f"Database operation '{operation}' failed: {str(original_error)}",
            suggestions=[
                "Try the operation again in a few seconds",
                "Check if the server is running properly",
                "Contact administrator if the problem persists",
            ],
            context={"operation": operation, "original_error": str(original_error), **(context or {})},
            timestamp=datetime.now(),
            stack_trace=traceback.format_exc(),
        )
        super().__init__(details)


class MemoryManagerNotInitializedError(MCPError):
    """Memory manager not properly initialized"""

    def __init__(self, operation: str, context: Dict[str, Any] = None):
        details = ErrorDetails(
            code="MEMORY_MANAGER_NOT_INITIALIZED",
            category=ErrorCategory.SYSTEM,
            severity=ErrorSeverity.ERROR,
            message="Memory system is not properly initialized",
            technical_message=f"MemoryManager not initialized for operation: {operation}",
            suggestions=[
                "Wait a moment for system initialization",
                "Restart the MCP server if the problem persists",
                "Check server logs for initialization errors",
            ],
            context={"operation": operation, **(context or {})},
            timestamp=datetime.now(),
        )
        super().__init__(details)


class ValidationError(MCPError):
    """Input validation failure"""

    def __init__(self, field: str, value: Any, reason: str, context: Dict[str, Any] = None):
        details = ErrorDetails(
            code="VALIDATION_ERROR",
            category=ErrorCategory.USER_INPUT,
            severity=ErrorSeverity.WARNING,
            message=f"Invalid {field}: {reason}",
            technical_message=f"Validation failed for field '{field}' with value '{value}': {reason}",
            suggestions=[
                f"Check the format of {field}",
                "Refer to the API documentation for valid values",
                "Use the provided examples as reference",
            ],
            context={"field": field, "value": str(value), "reason": reason, **(context or {})},
            timestamp=datetime.now(),
        )
        super().__init__(details)


class ResourceLimitError(MCPError):
    """Resource limit exceeded (memory, disk, etc.)"""

    def __init__(self, resource: str, limit: str, current: str, context: Dict[str, Any] = None):
        details = ErrorDetails(
            code="RESOURCE_LIMIT_ERROR",
            category=ErrorCategory.RESOURCE,
            severity=ErrorSeverity.ERROR,
            message=f"Resource limit exceeded: {resource} ({current} > {limit})",
            technical_message=f"Resource limit exceeded - {resource}: current={current}, limit={limit}",
            suggestions=[
                f"Reduce the {resource} usage in your request",
                "Split large operations into smaller batches",
                "Clean up unused data if applicable",
            ],
            context={"resource": resource, "limit": limit, "current": current, **(context or {})},
            timestamp=datetime.now(),
        )
        super().__init__(details)


class ErrorHandler:
    """Centralized error handling and response formatting"""

    @staticmethod
    async def handle_error(
        error: Union[Exception, MCPError],
        ctx: Context,
        operation: str,
        fallback_response: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Handle any error and return a structured response

        Args:
            error: The exception that occurred
            ctx: FastMCP context for logging
            operation: Description of the operation that failed
            fallback_response: Optional fallback response for graceful degradation

        Returns:
            Structured error response dictionary
        """

        # Convert to MCPError if needed
        if isinstance(error, MCPError):
            details = error.details
        else:
            details = ErrorHandler._create_generic_error_details(error, operation)

        # Log based on severity
        await ErrorHandler._log_error(ctx, details)

        # Return structured response
        response = {
            "success": False,
            "error": {
                "code": details.code,
                "message": details.message,
                "category": details.category.value,
                "severity": details.severity.value,
                "suggestions": details.suggestions,
                "timestamp": details.timestamp.isoformat(),
                "context": details.context,
            },
        }

        # Include technical details for debugging in development
        if details.severity in [ErrorSeverity.ERROR, ErrorSeverity.CRITICAL]:
            response["error"]["technical_message"] = details.technical_message
            if details.stack_trace:
                response["error"]["stack_trace"] = details.stack_trace

        # Add fallback data if available
        if fallback_response:
            response["data"] = fallback_response
            response["message"] = "Operation completed with fallback data due to error"
        else:
            response["data"] = {}
            response["message"] = details.message

        return response

    @staticmethod
    def _create_generic_error_details(error: Exception, operation: str) -> ErrorDetails:
        """Create error details for unexpected exceptions"""
        return ErrorDetails(
            code="UNEXPECTED_ERROR",
            category=ErrorCategory.SYSTEM,
            severity=ErrorSeverity.ERROR,
            message="An unexpected error occurred. Please try again.",
            technical_message=f"Unexpected error in {operation}: {str(error)}",
            suggestions=[
                "Try the operation again",
                "Check your input parameters",
                "Contact support if the problem persists",
            ],
            context={"operation": operation, "error_type": type(error).__name__},
            timestamp=datetime.now(),
            stack_trace=traceback.format_exc(),
        )

    @staticmethod
    async def _log_error(ctx: Context, details: ErrorDetails) -> None:
        """Log error based on severity level"""
        log_message = f"[{details.code}] {details.message}"

        if details.severity == ErrorSeverity.INFO:
            await ctx.info(log_message)
        elif details.severity == ErrorSeverity.WARNING:
            await ctx.warning(log_message)
        elif details.severity == ErrorSeverity.ERROR:
            await ctx.error(f"{log_message} | Technical: {details.technical_message}")
        elif details.severity == ErrorSeverity.CRITICAL:
            await ctx.error(f"CRITICAL: {log_message} | Technical: {details.technical_message}")
            if details.stack_trace:
                await ctx.error(f"Stack trace: {details.stack_trace}")


def create_success_response(
    message: str, data: Dict[str, Any], additional_info: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Create a standardized success response"""
    response = {"success": True, "message": message, "data": data, "timestamp": datetime.now().isoformat()}

    if additional_info:
        response.update(additional_info)

    return response


# Utility functions for common validations
def validate_memory_id(memory_id: str) -> None:
    """Validate memory ID format"""
    if not memory_id or not isinstance(memory_id, str):
        raise ValidationError("memory_id", memory_id, "must be a non-empty string")

    if len(memory_id.strip()) == 0:
        raise ValidationError("memory_id", memory_id, "cannot be empty or whitespace only")


def validate_scope(scope: str) -> None:
    """Validate scope format"""
    if not scope or not isinstance(scope, str):
        raise ValidationError("scope", scope, "must be a non-empty string")

    # Basic scope format validation
    if not scope.replace("/", "").replace("-", "").replace("_", "").replace(".", "").isalnum():
        raise InvalidScopeError(scope, {"reason": "contains invalid characters"})

    if scope.startswith("/") or scope.endswith("/"):
        raise InvalidScopeError(scope, {"reason": "cannot start or end with '/'"})


def validate_content(content: str, max_length: int = 1000000) -> None:
    """Validate memory content"""
    if not content or not isinstance(content, str):
        raise ValidationError("content", content, "must be a non-empty string")

    if len(content.strip()) == 0:
        raise ValidationError("content", content, "cannot be empty or whitespace only")

    if len(content) > max_length:
        raise ResourceLimitError(
            "content_length", str(max_length), str(len(content)), {"content_preview": content[:100] + "..."}
        )
