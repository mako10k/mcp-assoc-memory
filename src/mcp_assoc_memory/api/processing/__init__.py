"""
Shared response processing layer for MCP Associative Memory Server

This module provides unified response processing functionality that:
1. Takes configuration, request, and response objects
2. Applies response level control based on request and configuration
3. Returns final Dictionary for tool responses
4. Enables future extensibility for output level control
"""

from typing import Any, Dict, Optional, Union
from datetime import datetime
import logging

from ...config import Config
from ..models.requests import MCPRequestBase
from ..models.responses import MCPResponseBase

logger = logging.getLogger(__name__)


class ResponseProcessor:
    """
    Unified response processor for all MCP tool responses
    
    Handles:
    - Response level determination (minimal, standard, full)
    - Configuration-driven output control
    - Request metadata integration
    - Debugging and audit trail
    """
    
    def __init__(self, config: Config):
        """Initialize response processor with configuration"""
        self.config = config
        self._default_response_level = "standard"
        self._enable_audit_trail = config.get("api", {}).get("enable_audit_trail", False)
        self._enable_response_metadata = config.get("api", {}).get("enable_response_metadata", True)
    
    def process_tool_response(
        self,
        request: MCPRequestBase,
        response: MCPResponseBase,
        operation_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process tool response with unified configuration and request context
        
        Args:
            request: Original request object with metadata
            response: Response object from tool handler
            operation_context: Additional operation context (optional)
            
        Returns:
            Dict[str, Any]: Final response dictionary ready for tool return
        """
        # Determine response level from multiple sources
        response_level = self._determine_response_level(request, operation_context)
        
        # Generate base response using response object
        base_response = response.to_response_dict(level=response_level)
        
        # Enhance with metadata if enabled
        if self._enable_response_metadata:
            base_response = self._enhance_with_metadata(
                base_response, request, response_level, operation_context
            )
        
        # Add audit trail if enabled
        if self._enable_audit_trail:
            base_response = self._add_audit_trail(base_response, request, operation_context)
        
        # Apply any final transformations
        final_response = self._apply_final_transformations(base_response, response_level)
        
        self._log_response_processing(request, response_level, len(str(final_response)))
        
        return final_response
    
    def _determine_response_level(
        self,
        request: MCPRequestBase,
        operation_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Determine response detail level from multiple sources
        
        Priority order:
        1. Operation context override
        2. Request-specific level
        3. Configuration default
        4. System default
        """
        # 1. Operation context override (highest priority)
        if operation_context and "response_level" in operation_context:
            return operation_context["response_level"]
        
        # 2. Request-specific level
        request_level = request.get_response_level()
        if request_level != "standard":  # Non-default value
            return request_level
        
        # 3. Configuration default for this request type
        request_type = request.get_request_type()
        config_level = self.config.get("api", {}).get("response_levels", {}).get(request_type)
        if config_level:
            return config_level
        
        # 4. Global configuration default
        global_level = self.config.get("api", {}).get("default_response_level")
        if global_level:
            return global_level
        
        # 5. System default
        return self._default_response_level
    
    def _enhance_with_metadata(
        self,
        response: Dict[str, Any],
        request: MCPRequestBase,
        response_level: str,
        operation_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Add response metadata if enabled"""
        metadata = {
            "request_type": request.get_request_type(),
            "response_level": response_level,
            "processed_at": datetime.now().isoformat(),
            "operation_id": request.get_operation_id(),
        }
        
        # Add operation context metadata if available
        if operation_context:
            metadata["operation_context"] = {
                k: v for k, v in operation_context.items()
                if k not in ["response_level"]  # Avoid duplication
            }
        
        # Add metadata to response based on level
        if response_level in ["standard", "full"]:
            response["_metadata"] = metadata
        elif response_level == "minimal" and self.config.get("api", {}).get("force_minimal_metadata", False):
            response["_meta"] = {
                "request_type": metadata["request_type"],
                "operation_id": metadata["operation_id"]
            }
        
        return response
    
    def _add_audit_trail(
        self,
        response: Dict[str, Any],
        request: MCPRequestBase,
        operation_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Add audit trail information"""
        audit_info = {
            "timestamp": datetime.now().isoformat(),
            "request_type": request.get_request_type(),
            "primary_identifier": request.get_primary_identifier(),
            "processing_metadata": request.get_processing_metadata(),
        }
        
        if operation_context:
            audit_info["operation_context"] = operation_context
        
        # Only add audit trail for standard and full responses
        if response.get("_metadata"):
            response["_metadata"]["audit_trail"] = audit_info
        else:
            response["_audit"] = audit_info
        
        return response
    
    def _apply_final_transformations(
        self,
        response: Dict[str, Any],
        response_level: str
    ) -> Dict[str, Any]:
        """Apply final response transformations based on configuration"""
        # Remove null values if configured
        if self.config.get("api", {}).get("remove_null_values", False):
            response = self._remove_null_values(response)
        
        # Apply size limits for minimal responses
        if response_level == "minimal":
            max_size = self.config.get("api", {}).get("minimal_response_max_size", 1024)
            if len(str(response)) > max_size:
                logger.warning(
                    f"Minimal response size ({len(str(response))}) exceeds limit ({max_size})"
                )
        
        return response
    
    def _remove_null_values(self, obj: Any) -> Any:
        """Recursively remove null values from response"""
        if isinstance(obj, dict):
            return {k: self._remove_null_values(v) for k, v in obj.items() if v is not None}
        elif isinstance(obj, list):
            return [self._remove_null_values(item) for item in obj if item is not None]
        return obj
    
    def _log_response_processing(
        self,
        request: MCPRequestBase,
        response_level: str,
        response_size: int
    ) -> None:
        """Log response processing information"""
        logger.debug(
            f"Processed {request.get_request_type()} response: "
            f"level={response_level}, size={response_size}, "
            f"id={request.get_primary_identifier()}"
        )


def create_response_processor(config: Config) -> ResponseProcessor:
    """Factory function to create response processor"""
    return ResponseProcessor(config)


# Global processor instance (will be set by server initialization)
_global_processor: Optional[ResponseProcessor] = None


def set_global_processor(processor: ResponseProcessor) -> None:
    """Set global processor instance"""
    global _global_processor
    _global_processor = processor


def get_response_processor() -> ResponseProcessor:
    """Get global response processor instance"""
    if _global_processor is None:
        raise RuntimeError("Response processor not initialized. Call set_global_processor first.")
    return _global_processor


def process_tool_response(
    request: MCPRequestBase,
    response: MCPResponseBase,
    operation_context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Convenience function for processing tool responses
    
    Uses global processor instance for unified response processing
    """
    processor = get_response_processor()
    return processor.process_tool_response(request, response, operation_context)
