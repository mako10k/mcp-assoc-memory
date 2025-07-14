"""
Response models for MCP Associative Memory Server API
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class MCPResponseBase(BaseModel, ABC):
    """Abstract base class for all MCP response models with unified response generation"""

    @abstractmethod
    def to_response_dict(self, level: str = "minimal", **kwargs: Any) -> Dict[str, Any]:
        """
        Generate response dictionary with specified detail level.
        
        Args:
            level: Response detail level ("minimal", "standard", "full")
            **kwargs: Additional arguments for response customization
            
        Returns:
            Dict containing response data appropriate for the specified level
        """
        pass

    @classmethod
    def success_response(
        cls,
        message: str,
        data: Optional[Any] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Create standardized success response

        Args:
            message: Success message
            data: Response data (optional)
            metadata: Additional metadata (optional)
            **kwargs: Additional fields

        Returns:
            Standardized success response dictionary
        """
        response = {
            "success": True,
            "message": message,
        }

        if data is not None:
            response["data"] = data

        if metadata is not None:
            response["metadata"] = metadata

        # Add any additional fields
        response.update(kwargs)

        return response

    @classmethod
    def error_response(
        cls,
        message: str,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Create standardized error response

        Args:
            message: Error message
            error: Detailed error information (optional)
            metadata: Additional metadata (optional)
            **kwargs: Additional fields

        Returns:
            Standardized error response dictionary
        """
        response = {
            "success": False,
            "message": message,
        }

        if error is not None:
            response["error"] = error

        if metadata is not None:
            response["metadata"] = metadata

        # Add any additional fields
        response.update(kwargs)

        return response


class Memory(BaseModel):
    """Memory model with all fields"""

    id: str = Field(description="Unique memory identifier")
    content: str = Field(description="Memory content")
    scope: str = Field(description="Memory scope for hierarchical organization")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    tags: List[str] = Field(default_factory=list, description="Memory tags")
    category: Optional[str] = Field(default=None, description="Memory category")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")


class SearchResult(BaseModel):
    """Search result with similarity score"""

    memory: Memory = Field(description="Memory object")
    similarity_score: float = Field(description="Similarity score (0.0-1.0)")


class Association(BaseModel):
    """Memory association"""

    source_id: str = Field(description="Source memory ID")
    target_id: str = Field(description="Target memory ID")
    association_type: str = Field(description="Type of association (semantic, temporal, causal, similar)")
    strength: float = Field(description="Association strength (0.0-1.0)")
    auto_generated: bool = Field(description="Whether association was auto-generated")
    created_at: datetime = Field(description="Association creation timestamp")


class MemoryWithAssociations(BaseModel):
    """Memory with its associations"""

    memory: Memory = Field(description="Memory object")
    associations: List[Association] = Field(default_factory=list, description="Related associations")


class SearchResultWithAssociations(BaseModel):
    """Search result with associations"""

    memory: Memory = Field(description="Memory object")
    similarity_score: float = Field(description="Similarity score (0.0-1.0)")
    associations: List[Association] = Field(default_factory=list, description="Related associations")


class ScopeInfo(BaseModel):
    """Scope information with statistics"""

    scope: str = Field(description="Scope path")
    memory_count: int = Field(default=0, description="Number of memories in this scope")
    child_scopes: List[str] = Field(default_factory=list, description="Child scope paths")


class ScopeRecommendation(BaseModel):
    """Scope recommendation with confidence"""

    scope: str = Field(description="Recommended scope")
    confidence: float = Field(description="Confidence score (0.0-1.0)")
    reasoning: str = Field(description="Explanation for the recommendation")


class SessionInfo(BaseModel):
    """Session information"""

    session_id: str = Field(description="Session identifier")
    created_at: datetime = Field(description="Session creation timestamp")
    memory_count: int = Field(default=0, description="Number of memories in session")
    last_activity: Optional[datetime] = Field(default=None, description="Last activity timestamp")


class PaginationInfo(BaseModel):
    """Pagination information"""

    page: int = Field(description="Current page number")
    per_page: int = Field(description="Items per page")
    total_items: int = Field(description="Total number of items")
    total_pages: int = Field(description="Total number of pages")
    has_next: bool = Field(description="Whether there is a next page")
    has_previous: bool = Field(description="Whether there is a previous page")


# Response models for each operation
class MemoryStoreResponse(MCPResponseBase):
    """Response for memory store operation"""

    success: bool = Field(description="Operation success status")
    message: str = Field(description="Human-readable message")
    data: Dict[str, Any] = Field(description="Response data")
    memory: Optional[Memory] = Field(default=None, description="Stored memory (if successful)")
    associations_created: List[Association] = Field(default_factory=list, description="Auto-created associations")

    def to_response_dict(self, level: str = "minimal", **kwargs: Any) -> Dict[str, Any]:
        """Generate response dictionary with specified detail level"""
        if level == "minimal":
            return {
                "success": self.success,
                "memory_id": self.memory.id if self.memory else None,
                "created_at": self.memory.created_at.isoformat() if self.memory else None,
            }
        elif level == "standard":
            response = {
                "success": self.success,
                "message": self.message,
                "memory_id": self.memory.id if self.memory else None,
                "created_at": self.memory.created_at.isoformat() if self.memory else None,
            }
            if self.associations_created:
                response["associations_created_count"] = len(self.associations_created)
            return response
        elif level == "full":
            return {
                "success": self.success,
                "message": self.message,
                "data": self.data,
                "memory": self.memory.model_dump() if self.memory else None,
                "associations_created": [assoc.model_dump() for assoc in self.associations_created],
            }
        else:
            # Default to minimal for unknown levels
            return self.to_response_dict(level="minimal", **kwargs)


class MemorySearchResponse(MCPResponseBase):
    """Response for memory search operation"""

    success: bool = Field(description="Operation success status")
    message: str = Field(description="Human-readable message")
    data: Dict[str, Any] = Field(description="Response data")
    results: List[SearchResultWithAssociations] = Field(default_factory=list, description="Search results")
    query: str = Field(description="Original search query")
    total_found: int = Field(default=0, description="Total number of results found")

    def to_response_dict(self, level: str = "minimal", **kwargs: Any) -> Dict[str, Any]:
        """Generate response dictionary with specified detail level"""
        if level == "minimal":
            return {
                "success": self.success,
                "query": self.query,
                "total_found": self.total_found,
            }
        elif level == "standard":
            return {
                "success": self.success,
                "message": self.message,
                "query": self.query,
                "total_found": self.total_found,
                "results": [{"memory_id": r.memory.id, "similarity_score": r.similarity_score} for r in self.results[:5]],
            }
        elif level == "full":
            return {
                "success": self.success,
                "message": self.message,
                "data": self.data,
                "query": self.query,
                "total_found": self.total_found,
                "results": [r.model_dump() for r in self.results],
            }
        else:
            return self.to_response_dict(level="minimal", **kwargs)


class MemoryGetResponse(MCPResponseBase):
    """Response for memory get operation"""

    success: bool = Field(description="Operation success status")
    message: str = Field(description="Human-readable message")
    data: Dict[str, Any] = Field(description="Response data")
    memory: Optional[MemoryWithAssociations] = Field(default=None, description="Retrieved memory with associations")

    def to_response_dict(self, level: str = "minimal", **kwargs: Any) -> Dict[str, Any]:
        """Generate response dictionary with specified detail level"""
        if level == "minimal":
            return {
                "success": self.success,
                "memory_id": self.memory.memory.id if self.memory else None,
            }
        elif level == "standard":
            if not self.memory:
                return {"success": self.success, "message": self.message}
            return {
                "success": self.success,
                "message": self.message,
                "memory": {
                    "id": self.memory.memory.id,
                    "category": self.memory.memory.category,
                    "scope": self.memory.memory.scope,
                    "tags": self.memory.memory.tags,
                    "content_length": len(self.memory.memory.content),
                },
            }
        elif level == "full":
            return {
                "success": self.success,
                "message": self.message,
                "data": self.data,
                "memory": self.memory.model_dump() if self.memory else None,
            }
        else:
            return self.to_response_dict(level="minimal", **kwargs)


class MemoryUpdateResponse(MCPResponseBase):
    """Response for memory update operation"""

    success: bool = Field(description="Operation success status")
    message: str = Field(description="Human-readable message")
    data: Dict[str, Any] = Field(description="Response data")
    memory: Optional[Memory] = Field(default=None, description="Updated memory (if successful)")
    associations_updated: List[Association] = Field(default_factory=list, description="Updated associations")

    def to_response_dict(self, level: str = "minimal", **kwargs: Any) -> Dict[str, Any]:
        """Generate response dictionary with specified detail level"""
        if level == "minimal":
            minimal_response = {
                "success": self.success,
                "memory_id": self.memory.id if self.memory else None,
            }
            return minimal_response
        elif level == "standard":
            return {
                "success": self.success,
                "message": self.message,
                "memory_id": self.memory.id if self.memory else None,
                "updated_at": self.memory.updated_at.isoformat() if self.memory else None,
            }
        elif level == "full":
            return {
                "success": self.success,
                "message": self.message,
                "data": self.data,
                "memory": self.memory.model_dump() if self.memory else None,
                "associations_updated": [assoc.model_dump() for assoc in self.associations_updated],
            }
        else:
            return self.to_response_dict(level="minimal", **kwargs)


class MemoryDeleteResponse(MCPResponseBase):
    """Response for memory delete operation"""

    success: bool = Field(description="Operation success status")
    message: str = Field(description="Human-readable message")
    data: Dict[str, Any] = Field(description="Response data")
    deleted_memory_id: Optional[str] = Field(default=None, description="ID of deleted memory")
    associations_removed: int = Field(default=0, description="Number of associations removed")

    def to_response_dict(self, level: str = "minimal", **kwargs: Any) -> Dict[str, Any]:
        """Generate response dictionary with specified detail level"""
        if level == "minimal":
            return {
                "success": self.success,
                "deleted_memory_id": self.deleted_memory_id,
            }
        elif level == "standard":
            return {
                "success": self.success,
                "message": self.message,
                "deleted_memory_id": self.deleted_memory_id,
                "associations_removed": self.associations_removed,
            }
        elif level == "full":
            return {
                "success": self.success,
                "message": self.message,
                "data": self.data,
                "deleted_memory_id": self.deleted_memory_id,
                "associations_removed": self.associations_removed,
            }
        else:
            return self.to_response_dict(level="minimal", **kwargs)


class MemoryMoveResponse(MCPResponseBase):
    """Response for memory move operation"""

    success: bool = Field(description="Operation success status")
    message: str = Field(description="Human-readable message")
    data: Dict[str, Any] = Field(description="Response data")
    moved_memories: List[Memory] = Field(default_factory=list, description="Successfully moved memories")
    failed_memory_ids: List[str] = Field(default_factory=list, description="Memory IDs that failed to move")

    def to_response_dict(self, level: str = "minimal", **kwargs: Any) -> Dict[str, Any]:
        """Generate response dictionary with specified detail level"""
        if level == "minimal":
            return {
                "success": self.success,
                "moved_count": len(self.moved_memories),
                "failed_count": len(self.failed_memory_ids),
            }
        elif level == "standard":
            return {
                "success": self.success,
                "message": self.message,
                "moved_count": len(self.moved_memories),
                "failed_count": len(self.failed_memory_ids),
                "failed_memory_ids": self.failed_memory_ids if self.failed_memory_ids else None,
            }
        elif level == "full":
            return {
                "success": self.success,
                "message": self.message,
                "data": self.data,
                "moved_memories": [mem.model_dump() for mem in self.moved_memories],
                "failed_memory_ids": self.failed_memory_ids,
            }
        else:
            return self.to_response_dict(level="minimal", **kwargs)


class MemoryListAllResponse(MCPResponseBase):
    """Response for memory list all operation"""

    success: bool = Field(description="Operation success status")
    message: str = Field(description="Human-readable message")
    data: Dict[str, Any] = Field(description="Response data")
    memories: List[Memory] = Field(default_factory=list, description="List of memories")
    pagination: PaginationInfo = Field(description="Pagination information")

    def to_response_dict(self, level: str = "minimal", **kwargs: Any) -> Dict[str, Any]:
        """Generate response dictionary with specified detail level"""
        if level == "minimal":
            return {
                "success": self.success,
                "total_memories": len(self.memories),
                "page": self.pagination.page,
                "total_pages": self.pagination.total_pages,
            }
        elif level == "standard":
            return {
                "success": self.success,
                "message": self.message,
                "total_memories": len(self.memories),
                "pagination": self.pagination.model_dump(),
            }
        elif level == "full":
            return {
                "success": self.success,
                "message": self.message,
                "data": self.data,
                "memories": [mem.model_dump() for mem in self.memories],
                "pagination": self.pagination.model_dump(),
            }
        else:
            return self.to_response_dict(level="minimal", **kwargs)


class MemoryDiscoverAssociationsResponse(MCPResponseBase):
    """Response for memory discover associations operation"""

    success: bool = Field(description="Operation success status")
    message: str = Field(description="Human-readable message")
    data: Dict[str, Any] = Field(description="Response data")
    source_memory: Optional[Memory] = Field(default=None, description="Source memory")
    associations: List[SearchResultWithAssociations] = Field(
        default_factory=list, description="Discovered associations"
    )
    total_found: int = Field(default=0, description="Total number of associations found")

    def to_response_dict(self, level: str = "minimal", **kwargs: Any) -> Dict[str, Any]:
        """Generate response dictionary with specified detail level"""
        if level == "minimal":
            minimal_response: Dict[str, Any] = {
                "success": self.success,
                "total_found": self.total_found,
            }
            if self.source_memory:
                minimal_response["source_memory_id"] = self.source_memory.id
            return minimal_response
        elif level == "standard":
            standard_response = {
                "success": self.success,
                "message": self.message,
                "total_found": self.total_found,
            }
            if self.source_memory:
                standard_response["source_memory_id"] = self.source_memory.id
            return standard_response
        elif level == "full":
            full_response = {
                "success": self.success,
                "message": self.message,
                "data": self.data,
                "source_memory": self.source_memory.model_dump() if self.source_memory else None,
                "associations": [assoc.model_dump() for assoc in self.associations],
                "total_found": self.total_found,
            }
            return full_response
        else:
            return self.to_response_dict(level="minimal", **kwargs)


class ScopeListResponse(MCPResponseBase):
    """Response for scope list operation"""

    success: bool = Field(description="Operation success status")
    message: str = Field(description="Human-readable message")
    data: Dict[str, Any] = Field(description="Response data")
    scopes: List[ScopeInfo] = Field(default_factory=list, description="List of scopes")
    total_scopes: int = Field(default=0, description="Total number of scopes")

    def to_response_dict(self, level: str = "minimal", **kwargs: Any) -> Dict[str, Any]:
        """Generate response dictionary with specified detail level"""
        if level == "minimal":
            return {
                "success": self.success,
                "total_scopes": self.total_scopes,
            }
        elif level == "standard":
            return {
                "success": self.success,
                "message": self.message,
                "total_scopes": self.total_scopes,
                "scopes": [{"scope": scope.scope, "memory_count": scope.memory_count} for scope in self.scopes],
            }
        elif level == "full":
            return {
                "success": self.success,
                "message": self.message,
                "data": self.data,
                "scopes": [scope.model_dump() for scope in self.scopes],
                "total_scopes": self.total_scopes,
            }
        else:
            return self.to_response_dict(level="minimal", **kwargs)


class ScopeSuggestResponse(MCPResponseBase):
    """Response for scope suggest operation"""

    success: bool = Field(description="Operation success status")
    message: str = Field(description="Human-readable message")
    data: Dict[str, Any] = Field(description="Response data")
    recommendation: Optional[ScopeRecommendation] = Field(default=None, description="Primary recommendation")
    alternatives: List[ScopeRecommendation] = Field(default_factory=list, description="Alternative suggestions")

    def to_response_dict(self, level: str = "minimal", **kwargs: Any) -> Dict[str, Any]:
        """Generate response dictionary with specified detail level"""
        if level == "minimal":
            minimal_response: Dict[str, Any] = {
                "success": self.success,
            }
            if self.recommendation:
                minimal_response["recommended_scope"] = self.recommendation.scope
                minimal_response["confidence"] = self.recommendation.confidence
            return minimal_response
        elif level == "standard":
            standard_response: Dict[str, Any] = {
                "success": self.success,
                "message": self.message,
            }
            if self.recommendation:
                standard_response["recommendation"] = {
                    "scope": self.recommendation.scope,
                    "confidence": self.recommendation.confidence,
                }
            standard_response["alternatives_count"] = len(self.alternatives)
            return standard_response
        elif level == "full":
            full_response: Dict[str, Any] = {
                "success": self.success,
                "message": self.message,
                "data": self.data,
                "recommendation": self.recommendation.model_dump() if self.recommendation else None,
                "alternatives": [alt.model_dump() for alt in self.alternatives],
            }
            return full_response
        else:
            return self.to_response_dict(level="minimal", **kwargs)


class SessionManageResponse(MCPResponseBase):
    """Response for session manage operation"""

    success: bool = Field(description="Operation success status")
    message: str = Field(description="Human-readable message")
    data: Dict[str, Any] = Field(description="Response data")
    session: Optional[SessionInfo] = Field(default=None, description="Session information (for create)")
    sessions: List[SessionInfo] = Field(default_factory=list, description="List of sessions (for list)")
    cleaned_sessions: List[str] = Field(default_factory=list, description="Cleaned session IDs (for cleanup)")

    def to_response_dict(self, level: str = "minimal", **kwargs: Any) -> Dict[str, Any]:
        """Generate response dictionary with specified detail level"""
        if level == "minimal":
            minimal_response: Dict[str, Any] = {
                "success": self.success,
            }
            if self.session:
                minimal_response["session_id"] = self.session.session_id
            minimal_response["sessions_count"] = len(self.sessions)
            minimal_response["cleaned_count"] = len(self.cleaned_sessions)
            return minimal_response
        elif level == "standard":
            return {
                "success": self.success,
                "message": self.message,
                "sessions_count": len(self.sessions),
                "cleaned_count": len(self.cleaned_sessions),
            }
        elif level == "full":
            return {
                "success": self.success,
                "message": self.message,
                "data": self.data,
                "session": self.session.model_dump() if self.session else None,
                "sessions": [session.model_dump() for session in self.sessions],
                "cleaned_sessions": self.cleaned_sessions,
            }
        else:
            return self.to_response_dict(level="minimal", **kwargs)


class MemoryExportResponse(MCPResponseBase):
    """Response for memory export operation"""

    success: bool = Field(description="Operation success status")
    message: str = Field(description="Human-readable message")
    data: Dict[str, Any] = Field(description="Response data")
    export_data: Optional[str] = Field(default=None, description="Exported data (if file_path=None)")
    file_path: Optional[str] = Field(default=None, description="Export file path (if file_path specified)")
    exported_count: int = Field(default=0, description="Number of memories exported")
    export_format: str = Field(default="json", description="Export format used")

    def to_response_dict(self, level: str = "minimal", **kwargs: Any) -> Dict[str, Any]:
        """Generate response dictionary with specified detail level"""
        if level == "minimal":
            return {
                "success": self.success,
                "exported_count": self.exported_count,
                "export_format": self.export_format,
            }
        elif level == "standard":
            standard_response: Dict[str, Any] = {
                "success": self.success,
                "message": self.message,
                "exported_count": self.exported_count,
                "export_format": self.export_format,
            }
            if self.file_path:
                standard_response["file_path"] = self.file_path
            return standard_response
        elif level == "full":
            return {
                "success": self.success,
                "message": self.message,
                "data": self.data,
                "export_data": self.export_data,
                "file_path": self.file_path,
                "exported_count": self.exported_count,
                "export_format": self.export_format,
            }
        else:
            return self.to_response_dict(level="minimal", **kwargs)


class MemoryImportResponse(MCPResponseBase):
    """Response for memory import operation"""

    success: bool = Field(description="Operation success status")
    message: str = Field(description="Human-readable message")
    data: Dict[str, Any] = Field(description="Response data")
    imported_count: int = Field(default=0, description="Number of memories imported")
    skipped_count: int = Field(default=0, description="Number of memories skipped")
    error_count: int = Field(default=0, description="Number of import errors")
    import_summary: Dict[str, Any] = Field(default_factory=dict, description="Import operation summary")

    def to_response_dict(self, level: str = "minimal", **kwargs: Any) -> Dict[str, Any]:
        """Generate response dictionary with specified detail level"""
        if level == "minimal":
            return {
                "success": self.success,
                "imported_count": self.imported_count,
                "skipped_count": self.skipped_count,
                "error_count": self.error_count,
            }
        elif level == "standard":
            return {
                "success": self.success,
                "message": self.message,
                "imported_count": self.imported_count,
                "skipped_count": self.skipped_count,
                "error_count": self.error_count,
            }
        elif level == "full":
            return {
                "success": self.success,
                "message": self.message,
                "data": self.data,
                "imported_count": self.imported_count,
                "skipped_count": self.skipped_count,
                "error_count": self.error_count,
                "import_summary": self.import_summary,
            }
        else:
            return self.to_response_dict(level="minimal", **kwargs)


# Legacy compatibility response model (used by tools)
class MemoryResponse(MCPResponseBase):
    """Legacy memory response for tool compatibility"""

    success: bool = Field(default=True, description="Operation success status")
    message: str = Field(default="", description="Operation status message")
    memory_id: str = Field(description="Memory identifier")
    content: str = Field(description="Memory content")
    scope: Optional[str] = Field(default=None, description="Memory scope (optional for lightweight responses)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Memory metadata")
    tags: List[str] = Field(default_factory=list, description="Memory tags")
    category: Optional[str] = Field(default=None, description="Memory category")
    created_at: datetime = Field(description="Creation timestamp")
    similarity_score: Optional[float] = Field(default=None, description="Similarity score when from search")
    associations: Optional[List[Association]] = Field(default=None, description="Related associations")
    is_duplicate: bool = Field(default=False, description="Whether this was a duplicate detection")
    duplicate_of: Optional[str] = Field(default=None, description="Original memory ID if duplicate")

    def to_response_dict(self, level: str = "minimal", include_scope_if_modified: bool = False, original_scope: Optional[str] = None, **kwargs: Any) -> Dict[str, Any]:
        """Generate response dictionary with specified detail level"""
        if level == "minimal":
            minimal_response = {
                "success": self.success,
                "memory_id": self.memory_id,
                "created_at": self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            }
            # Include scope only if it was modified/normalized from the request
            if include_scope_if_modified and self.scope and self.scope != original_scope:
                minimal_response["scope"] = self.scope
            return minimal_response
        elif level == "standard":
            standard_response = {
                "success": self.success,
                "message": self.message,
                "memory_id": self.memory_id,
                "content": "",  # Don't echo input content
                "created_at": self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            }
            # Include scope only if it was modified/normalized from the request
            if include_scope_if_modified and self.scope and self.scope != original_scope:
                standard_response["scope"] = self.scope
            # Only include non-empty auto-generated fields
            if self.metadata:
                standard_response["metadata"] = self.metadata
            if self.tags:
                standard_response["tags"] = self.tags
            if self.category:
                standard_response["category"] = self.category
            return standard_response
        elif level == "full":
            return {
                "success": self.success,
                "message": self.message,
                "memory_id": self.memory_id,
                "content": self.content,
                "scope": self.scope,
                "metadata": self.metadata,
                "tags": self.tags,
                "category": self.category,
                "created_at": self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
                "similarity_score": self.similarity_score,
                "associations": [assoc.model_dump() for assoc in self.associations] if self.associations else None,
                "is_duplicate": self.is_duplicate,
                "duplicate_of": self.duplicate_of,
            }
        else:
            return self.to_response_dict(level="minimal", include_scope_if_modified=include_scope_if_modified, original_scope=original_scope, **kwargs)


# Generic error response
class ErrorResponse(MCPResponseBase):
    """Error response"""

    success: bool = Field(default=False, description="Operation success status")
    message: str = Field(description="Error message")
    error: str = Field(description="Error type or code")
    data: Dict[str, Any] = Field(default_factory=dict, description="Error context data")

    def to_response_dict(self, level: str = "minimal", **kwargs: Any) -> Dict[str, Any]:
        """Generate response dictionary with specified detail level"""
        if level == "minimal":
            return {
                "success": self.success,
                "error": self.error,
            }
        elif level == "standard":
            return {
                "success": self.success,
                "message": self.message,
                "error": self.error,
            }
        elif level == "full":
            return {
                "success": self.success,
                "message": self.message,
                "error": self.error,
                "data": self.data,
            }
        else:
            return self.to_response_dict(level="minimal", **kwargs)


# Union type for all possible responses
MCPResponse = Union[
    MemoryStoreResponse,
    MemorySearchResponse,
    MemoryGetResponse,
    MemoryUpdateResponse,
    MemoryDeleteResponse,
    MemoryMoveResponse,
    MemoryListAllResponse,
    MemoryDiscoverAssociationsResponse,
    ScopeListResponse,
    ScopeSuggestResponse,
    SessionManageResponse,
    MemoryExportResponse,
    MemoryImportResponse,
    ErrorResponse,
]
