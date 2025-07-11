"""
Response models for MCP Associative Memory Server API
"""

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field
from datetime import datetime


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
    strength: float = Field(description="Association strength (0.0-1.0)")
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
class MemoryStoreResponse(BaseModel):
    """Response for memory store operation"""
    success: bool = Field(description="Operation success status")
    message: str = Field(description="Human-readable message")
    data: Dict[str, Any] = Field(description="Response data")
    memory: Optional[Memory] = Field(default=None, description="Stored memory (if successful)")
    associations_created: List[Association] = Field(default_factory=list, description="Auto-created associations")


class MemorySearchResponse(BaseModel):
    """Response for memory search operation"""
    success: bool = Field(description="Operation success status")
    message: str = Field(description="Human-readable message")
    data: Dict[str, Any] = Field(description="Response data")
    results: List[SearchResultWithAssociations] = Field(default_factory=list, description="Search results")
    query: str = Field(description="Original search query")
    total_found: int = Field(default=0, description="Total number of results found")


class MemoryGetResponse(BaseModel):
    """Response for memory get operation"""
    success: bool = Field(description="Operation success status")
    message: str = Field(description="Human-readable message")
    data: Dict[str, Any] = Field(description="Response data")
    memory: Optional[MemoryWithAssociations] = Field(default=None, description="Retrieved memory with associations")


class MemoryUpdateResponse(BaseModel):
    """Response for memory update operation"""
    success: bool = Field(description="Operation success status")
    message: str = Field(description="Human-readable message")
    data: Dict[str, Any] = Field(description="Response data")
    memory: Optional[Memory] = Field(default=None, description="Updated memory (if successful)")
    associations_updated: List[Association] = Field(default_factory=list, description="Updated associations")


class MemoryDeleteResponse(BaseModel):
    """Response for memory delete operation"""
    success: bool = Field(description="Operation success status")
    message: str = Field(description="Human-readable message")
    data: Dict[str, Any] = Field(description="Response data")
    deleted_memory_id: Optional[str] = Field(default=None, description="ID of deleted memory")
    associations_removed: int = Field(default=0, description="Number of associations removed")


class MemoryMoveResponse(BaseModel):
    """Response for memory move operation"""
    success: bool = Field(description="Operation success status")
    message: str = Field(description="Human-readable message")
    data: Dict[str, Any] = Field(description="Response data")
    moved_memories: List[Memory] = Field(default_factory=list, description="Successfully moved memories")
    failed_memory_ids: List[str] = Field(default_factory=list, description="Memory IDs that failed to move")


class MemoryListAllResponse(BaseModel):
    """Response for memory list all operation"""
    success: bool = Field(description="Operation success status")
    message: str = Field(description="Human-readable message")
    data: Dict[str, Any] = Field(description="Response data")
    memories: List[Memory] = Field(default_factory=list, description="List of memories")
    pagination: PaginationInfo = Field(description="Pagination information")


class MemoryDiscoverAssociationsResponse(BaseModel):
    """Response for memory discover associations operation"""
    success: bool = Field(description="Operation success status")
    message: str = Field(description="Human-readable message")
    data: Dict[str, Any] = Field(description="Response data")
    source_memory: Optional[Memory] = Field(default=None, description="Source memory")
    associations: List[SearchResultWithAssociations] = Field(default_factory=list, description="Discovered associations")
    total_found: int = Field(default=0, description="Total number of associations found")


class ScopeListResponse(BaseModel):
    """Response for scope list operation"""
    success: bool = Field(description="Operation success status")
    message: str = Field(description="Human-readable message")
    data: Dict[str, Any] = Field(description="Response data")
    scopes: List[ScopeInfo] = Field(default_factory=list, description="List of scopes")
    total_scopes: int = Field(default=0, description="Total number of scopes")


class ScopeSuggestResponse(BaseModel):
    """Response for scope suggest operation"""
    success: bool = Field(description="Operation success status")
    message: str = Field(description="Human-readable message")
    data: Dict[str, Any] = Field(description="Response data")
    recommendation: Optional[ScopeRecommendation] = Field(default=None, description="Primary recommendation")
    alternatives: List[ScopeRecommendation] = Field(default_factory=list, description="Alternative suggestions")


class SessionManageResponse(BaseModel):
    """Response for session manage operation"""
    success: bool = Field(description="Operation success status")
    message: str = Field(description="Human-readable message")
    data: Dict[str, Any] = Field(description="Response data")
    session: Optional[SessionInfo] = Field(default=None, description="Session information (for create)")
    sessions: List[SessionInfo] = Field(default_factory=list, description="List of sessions (for list)")
    cleaned_sessions: List[str] = Field(default_factory=list, description="Cleaned session IDs (for cleanup)")


class MemoryExportResponse(BaseModel):
    """Response for memory export operation"""
    success: bool = Field(description="Operation success status")
    message: str = Field(description="Human-readable message")
    data: Dict[str, Any] = Field(description="Response data")
    export_data: Optional[str] = Field(default=None, description="Exported data (if file_path=None)")
    file_path: Optional[str] = Field(default=None, description="Export file path (if file_path specified)")
    exported_count: int = Field(default=0, description="Number of memories exported")
    export_format: str = Field(default="json", description="Export format used")


class MemoryImportResponse(BaseModel):
    """Response for memory import operation"""
    success: bool = Field(description="Operation success status")
    message: str = Field(description="Human-readable message")
    data: Dict[str, Any] = Field(description="Response data")
    imported_count: int = Field(default=0, description="Number of memories imported")
    skipped_count: int = Field(default=0, description="Number of memories skipped")
    error_count: int = Field(default=0, description="Number of import errors")
    import_summary: Dict[str, Any] = Field(default_factory=dict, description="Import operation summary")


# Legacy compatibility response model (used by tools)
class MemoryResponse(BaseModel):
    """Legacy memory response for tool compatibility"""
    memory_id: str = Field(description="Memory identifier")
    content: str = Field(description="Memory content")
    scope: str = Field(description="Memory scope")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Memory metadata")
    tags: List[str] = Field(default_factory=list, description="Memory tags")
    category: Optional[str] = Field(default=None, description="Memory category")
    created_at: datetime = Field(description="Creation timestamp")
    similarity_score: Optional[float] = Field(default=None, description="Similarity score when from search")
    associations: Optional[List[str]] = Field(default=None, description="Related memory IDs")
    is_duplicate: bool = Field(default=False, description="Whether this was a duplicate detection")
    duplicate_of: Optional[str] = Field(default=None, description="Original memory ID if duplicate")


# Generic error response
class ErrorResponse(BaseModel):
    """Error response"""
    success: bool = Field(default=False, description="Operation success status")
    message: str = Field(description="Error message")
    error: str = Field(description="Error type or code")
    data: Dict[str, Any] = Field(default_factory=dict, description="Error context data")


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
    ErrorResponse
]
