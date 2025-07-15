"""
Request models for MCP Associative Memory Server API
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from .common import CommonToolParameters, ResponseLevel


class MCPRequestBase(BaseModel, ABC):
    """
    Abstract base class for all MCP request types

    Provides common functionality for:
    - Request validation
    - Metadata extraction
    - Response level determination
    - Debugging and audit trails
    """

    def get_request_type(self) -> str:
        """Get request type for logging and processing"""
        return self.__class__.__name__

    def get_operation_id(self) -> str:
        """Get unique operation identifier for tracking"""
        return f"{self.get_request_type()}_{id(self)}"

    @abstractmethod
    def get_primary_identifier(self) -> str:
        """Get primary identifier for this request (e.g., memory_id, query)"""
        pass

    def get_response_level(self) -> str:
        """
        Determine response detail level based on request characteristics

        Returns:
            str: "minimal", "standard", or "full"
        """
        # Check if this request inherits from CommonToolParameters
        if hasattr(self, 'response_level') and self.response_level:
            return str(self.response_level.value)

        # Default implementation for requests without response_level
        if hasattr(self, 'minimal_response') and self.minimal_response:
            return "minimal"
        return "standard"

    def get_processing_metadata(self) -> Dict[str, Any]:
        """Get metadata for request processing and debugging"""
        return {
            "request_type": self.get_request_type(),
            "operation_id": self.get_operation_id(),
            "primary_identifier": self.get_primary_identifier(),
            "response_level": self.get_response_level(),
            "model_dump_size": len(str(self.model_dump())),
        }


class MemoryStoreRequest(MCPRequestBase, CommonToolParameters):
    content: str = Field(description="Memory content to store")
    scope: str = Field(
        default="user/default",
        description="""Memory scope for hierarchical organization:

        Values & Use Cases:
        • learning/[topic]/[subtopic]: Academic and skill development
          Example: learning/programming/python, learning/ml/transformers
        • work/[project]/[category]: Professional and project content
          Example: work/webapp/backend, work/client-meetings/feedback
        • personal/[category]: Private thoughts and ideas
          Example: personal/ideas, personal/reflections, personal/goals
        • session/[identifier]: Temporary session-based memories
          Example: session/2025-07-10, session/current-project

        Strategy: Use scope_suggest for automatic categorization
        Example: scope="learning/mcp/implementation" for this context""",
        examples=["learning/programming/python", "work/project/backend", "personal/ideas"],
    )
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")
    tags: Optional[List[str]] = Field(default=None, description="Memory tags")
    category: Optional[str] = Field(default=None, description="Memory category")
    auto_associate: bool = Field(default=True, description="Enable automatic association discovery")
    allow_duplicates: bool = Field(default=False, description="Allow storing duplicate content")
    duplicate_threshold: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="""Duplicate detection threshold for pre-registration check:

        Values & Use Cases:
        • None: No duplicate checking - allow any content including duplicates ← DEFAULT
        • 0.95-1.0: Strict - only prevent near-identical content
        • 0.85-0.95: Standard - prevent similar variations ← RECOMMENDED
        • 0.70-0.85: Aggressive - prevent related content duplication

        Strategy: Leave None for no duplicate checking, use 0.85-0.95 for duplicate prevention
        If similarity score ≥ threshold, registration will fail with duplicate error
        Example: duplicate_threshold=0.85 for standard duplicate prevention""",
        examples=[None, 0.85, 0.90, 0.95],
    )

    def get_primary_identifier(self) -> str:
        """Primary identifier is the content preview"""
        return f"content:{self.content[:50]}..." if len(self.content) > 50 else f"content:{self.content}"


class MemorySearchRequest(MCPRequestBase, CommonToolParameters):
    query: str = Field(description="Search query")
    scope: Optional[str] = Field(
        default=None,
        description="""Target scope for search (supports hierarchy):

        Examples:
        • learning/programming: Find programming-related memories
        • work/current-project: Search current project context
        • personal: Browse personal thoughts and ideas
        • None: Search across all scopes

        Strategy: Start broad, narrow down if too many results""",
        examples=["learning/programming", "work/project", None],
    )
    include_child_scopes: bool = Field(default=False, description="Include child scopes in search")
    limit: int = Field(
        default=10,
        ge=1,
        le=100,
        description="""Maximum number of memories to retrieve:

        Values & Use Cases:
        • 5-10: Focused search (finding specific information) ← RECOMMENDED
        • 10-20: Balanced exploration (general ideation, learning review)
        • 20-50: Comprehensive discovery (brainstorming, research phase)

        Strategy: Start small (10), increase if you need broader context
        Example: limit=15 for creative thinking sessions

        ⚠️ Performance: Higher values increase processing time""",
        examples=[10, 15, 5],
    )
    similarity_threshold: float = Field(
        default=0.1,
        ge=0.0,
        le=1.0,
        description="""Similarity threshold for memory matching:

        Values & Use Cases:
        • 0.8-1.0: Near-identical content (duplicate detection, exact recall)
        • 0.4-0.8: Clear relevance (general search, learning review)
        • 0.2-0.4: Broader associations (idea expansion, new perspectives)
        • 0.1-0.2: Creative connections (brainstorming, unexpected links) ← RECOMMENDED

        Strategy: ChromaDB uses Top-K search, so low threshold (0.1) filters noise while LLM judges relevance via similarity scores
        Example: similarity_threshold=0.1 for most searches (trust Top-K ranking)""",
        examples=[0.1, 0.2, 0.4],
    )
    include_associations: bool = Field(default=True, description="Include related memories in results")

    def get_primary_identifier(self) -> str:
        """Primary identifier is the search query"""
        return f"query:{self.query[:50]}..." if len(self.query) > 50 else f"query:{self.query}"


class DiversifiedSearchRequest(MCPRequestBase):
    """Diversified similarity search request for broader knowledge exploration"""

    query: str = Field(description="Search query")
    scope: Optional[str] = Field(
        default=None,
        description="""Target scope for search (supports hierarchy):

        Examples:
        • learning/programming: Find programming-related diverse memories
        • work/current-project: Search current project context broadly
        • personal: Browse personal thoughts with variety
        • None: Search across all scopes with diversity

        Strategy: Start broad, narrow down if too many results""",
        examples=["learning/programming", "work/project", None],
    )
    limit: int = Field(
        default=10,
        ge=1,
        le=100,
        description="""Maximum number of diverse memories to retrieve:

        Values & Use Cases:
        • 5-10: Focused diverse exploration ← RECOMMENDED
        • 10-20: Balanced diverse discovery (creative sessions)
        • 20-50: Comprehensive diverse exploration (brainstorming)

        Strategy: Start small (10), increase for broader creative exploration
        Example: limit=15 for diverse creative thinking sessions

        ⚠️ Performance: Higher values increase processing time""",
        examples=[10, 15, 5],
    )
    min_score: float = Field(
        default=0.1,
        ge=0.0,
        le=1.0,
        description="""Minimum similarity threshold for candidates:

        Values & Use Cases:
        • 0.1-0.2: Broad exploration (creative connections) ← RECOMMENDED
        • 0.2-0.4: Moderate relevance (balanced diversity)
        • 0.4-0.8: Focused but diverse (specific domain exploration)

        Strategy: Lower values for more creative, unexpected connections
        Example: min_score=0.1 for diverse brainstorming""",
        examples=[0.1, 0.2, 0.4],
    )
    diversity_threshold: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="""Similarity threshold for excluding similar items:

        Values & Use Cases:
        • 0.8-0.9: Moderate diversity (exclude very similar) ← RECOMMENDED
        • 0.6-0.8: High diversity (exclude somewhat similar)
        • 0.9-1.0: Low diversity (exclude only near-duplicates)

        Strategy: 0.8 provides good balance of relevance and diversity
        Example: diversity_threshold=0.8 for balanced diverse results""",
        examples=[0.8, 0.7, 0.9],
    )
    expansion_factor: float = Field(
        default=2.5,
        ge=1.0,
        le=10.0,
        description="""Initial expansion multiplier for candidate search:

        Values & Use Cases:
        • 2.0-3.0: Balanced performance and diversity ← RECOMMENDED
        • 3.0-5.0: Higher diversity, more processing time
        • 1.5-2.0: Faster processing, less diversity

        Strategy: 2.5 provides good balance for most use cases
        Example: expansion_factor=2.5 for standard diverse search""",
        examples=[2.5, 3.0, 2.0],
    )
    max_expansion_factor: float = Field(
        default=5.0,
        ge=1.0,
        le=20.0,
        description="""Maximum expansion when fallback is needed:

        Values & Use Cases:
        • 5.0-10.0: Good fallback coverage ← RECOMMENDED
        • 10.0-20.0: Extensive fallback (slow but thorough)
        • 2.0-5.0: Limited fallback (faster but less comprehensive)

        Strategy: 5.0 provides good fallback without excessive processing
        Example: max_expansion_factor=5.0 for balanced fallback""",
        examples=[5.0, 7.0, 3.0],
    )
    include_associations: bool = Field(default=True, description="Include related memories in results")

    def get_primary_identifier(self) -> str:
        """Primary identifier is the search query"""
        return f"query:{self.query[:50]}..." if len(self.query) > 50 else f"query:{self.query}"


class MemoryUpdateRequest(MCPRequestBase):
    memory_id: str = Field(description="ID of the memory to update")
    content: Optional[str] = Field(default=None, description="New content for the memory (optional)")
    scope: Optional[str] = Field(
        default=None,
        description="""New scope for the memory (optional):

        Scope Organization:
        • learning/programming: Technical and programming content
        • work/projects: Project-related memories
        • personal/notes: Personal thoughts and reminders
        • session/[name]: Temporary session-specific content

        Strategy: Use scope_suggest for recommendations if unsure
        Example: scope="work/projects/mcp-improvements" for project organization""",
    )
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="New metadata for the memory (optional)")
    tags: Optional[List[str]] = Field(default=None, description="New tags for the memory (optional)")
    category: Optional[str] = Field(default=None, description="New category for the memory (optional)")
    preserve_associations: bool = Field(
        default=True, description="Whether to preserve existing associations when updating content"
    )

    def get_primary_identifier(self) -> str:
        """Primary identifier is the memory ID"""
        return self.memory_id


class MemoryMoveRequest(CommonToolParameters):
    memory_ids: List[str] = Field(
        description="""List of memory IDs to move to new scope:

        Operation Types:
        • Single memory: ["memory-id-123"] for individual moves
        • Bulk operation: ["id1", "id2", "id3"] for batch reorganization
        • Related memories: Move memories discovered via associations

        Source Identification:
        • Use memory_search to find target memories
        • Use memory_list_all for bulk scope changes
        • Use memory_discover_associations for related content

        Safety Notes:
        • All memory IDs must exist (operation validates)
        • Invalid IDs are skipped with warnings
        • Move preserves all content and metadata

        Example: ["mem-001", "mem-002"] to move two related memories"""
    )
    target_scope: str = Field(
        description="""Target scope for moved memories:

        Scope Validation:
        • Must follow valid scope format (letters, numbers, _, -, /)
        • Maximum 10 levels deep in hierarchy
        • Cannot use reserved patterns (., ..)
        • Automatically validated before move operation

        Organization Patterns:
        • work/projects/new-feature (hierarchical organization)
        • learning/programming/python (topical organization)
        • personal/archive (lifecycle organization)

        Best Practices:
        • Use consistent naming conventions
        • Follow existing hierarchy patterns
        • Consider future organization needs

        Example: target_scope="work/projects/mcp-improvements" for project reorganization"""
    )

    def get_primary_identifier(self) -> str:
        """Primary identifier is the list of memory IDs"""
        return f"memory_ids:{','.join(self.memory_ids)}"


class ScopeListRequest(MCPRequestBase, CommonToolParameters):
    parent_scope: Optional[str] = Field(
        default=None,
        description="""Parent scope to filter hierarchy view:

        Navigation Strategy:
        • None: Show complete scope hierarchy (full overview)
        • "work": Show work/* scopes only (focused view)
        • "learning/programming": Show programming sub-scopes
        • "session": Show all session scopes

        Use Cases:
        • Complete overview: Leave empty for all scopes
        • Focused exploration: Specify parent for specific area
        • Hierarchical browsing: Navigate from general to specific

        Example: parent_scope="work" to explore work-related organization""",
        examples=[None, "work", "learning", "session"],
    )
    include_memory_counts: bool = Field(
        default=True,
        description="""Include memory count statistics:

        Performance Trade-off:
        • True: Complete information with memory counts (slower but informative)
        • False: Structure-only view (faster, focuses on organization)

        Use Cases:
        • Planning storage: True to understand distribution
        • Quick navigation: False for faster hierarchy browsing
        • System monitoring: True for usage analytics

        Example: include_memory_counts=False for rapid scope exploration""",
    )

    def get_primary_identifier(self) -> str:
        """Primary identifier is the parent scope"""
        return self.parent_scope if self.parent_scope else "root"


class ScopeSuggestRequest(MCPRequestBase):
    content: str = Field(
        description="""Content to analyze for scope recommendation:

        Content Analysis:
        • Include full text for best categorization accuracy
        • Keywords are automatically detected (technical, meeting, personal)
        • Context matters: related concepts help determine scope
        • Language support: Both English and Japanese content

        Examples:
        • "Meeting notes from standup discussion" → work/meetings
        • "Python FastMCP implementation details" → learning/programming
        • "Personal reminder to call dentist" → personal/tasks

        Strategy: Provide complete content rather than truncated text"""
    )
    current_scope: Optional[str] = Field(
        default=None,
        description="""Current scope context for enhanced recommendations:

        Context Enhancement:
        • Helps suggest related scopes in same hierarchy
        • Improves accuracy for similar content types
        • Enables contextual sub-scope suggestions
        • None: Analyze content independently

        Use Cases:
        • Related content: Include current scope for similar items
        • Independent analysis: Leave empty for fresh categorization
        • Contextual refinement: Help system understand work flow

        Example: current_scope="work/projects" for project-related content""",
        examples=[None, "work/projects", "learning", "personal"],
    )

    def get_primary_identifier(self) -> str:
        """Primary identifier is the content preview"""
        return f"content:{self.content[:50]}..." if len(self.content) > 50 else f"content:{self.content}"


class SessionManageRequest(MCPRequestBase):
    action: str = Field(
        description="""Session management action to perform:

        Available Actions:
        • "create": Create new session scope (auto-generates ID if not provided)
        • "list": List all active sessions with statistics
        • "cleanup": Remove old sessions based on max_age_days
        • "archive": (Future) Archive sessions before cleanup

        Workflow Patterns:
        • Project sessions: create → work in session → cleanup when done
        • Conversation sessions: create → store context → auto-cleanup
        • Temporary workspaces: create → experiment → cleanup

        Example: action="create" to start new isolated working session"""
    )
    session_id: Optional[str] = Field(
        default=None,
        description="""Custom session identifier:

        ID Generation:
        • None: Auto-generate with timestamp format (session-YYYYMMDD-HHMMSS)
        • Custom: Use meaningful names for important sessions
        • Format: alphanumeric, hyphens, underscores allowed

        Use Cases:
        • Auto-generated: Quick temporary sessions
        • Named sessions: "project-alpha", "meeting-notes-Q1"
        • Systematic naming: Follow team conventions

        Example: session_id="mcp-development-session" for project work""",
        examples=[None, "project-alpha", "meeting-notes", "experiment-001"],
    )
    max_age_days: Optional[int] = Field(
        default=7,
        description="""Maximum age for cleanup operations (days):

        Cleanup Strategy:
        • 1-3 days: Aggressive cleanup for short-term sessions
        • 7 days (default): Balanced retention for weekly workflows
        • 30+ days: Conservative cleanup for important sessions

        Use Cases:
        • Daily sessions: max_age_days=1 for fresh starts
        • Project sessions: max_age_days=30 for longer work
        • Archive before cleanup: Use higher values with periodic review

        Example: max_age_days=14 for bi-weekly session cleanup""",
        examples=[1, 7, 14, 30],
    )

    def get_primary_identifier(self) -> str:
        """Primary identifier is the action and session ID"""
        return f"action:{self.action}, session_id:{self.session_id}"


class MemoryExportRequest(MCPRequestBase):
    scope: Optional[str] = Field(
        default=None,
        description="""Scope to export (optional):

        Export Scope Strategy:
        • None: Export all memories (full backup)
        • "work": Export only work-related memories
        • "session/project-name": Export specific session
        • "learning": Export learning-related memories

        Use Cases:
        • Full backup: Leave empty for complete export
        • Partial sync: Specify scope for targeted export
        • Project handoff: Export specific project scope

        Example: scope="work/projects/mcp-improvements" for project-specific export""",
    )
    include_associations: bool = Field(default=True, description="Include association relationships in export")
    export_format: str = Field(default="json", description="Export format (json, yaml)", pattern="^(json|yaml)$")
    file_path: Optional[str] = Field(
        default=None,
        description="""Server-side file path for export (Pattern A):

        File Path Strategy:
        • None: Return data directly via response (Pattern B)
        • Relative path: Save to server-configured export directory
        • Absolute path: Save to specified location (if permitted)

        Examples:
        • file_path=None: Direct data exchange mode
        • file_path="backup/memories-2025-07-10.json": Server-side file
        • file_path="/shared/project-memories.json": Absolute path mode

        Security: Server validates paths against configured allowed directories""",
    )
    compression: bool = Field(default=False, description="Compress export data (gzip)")

    def get_primary_identifier(self) -> str:
        """Primary identifier is the scope and file path"""
        return f"scope:{self.scope}, file_path:{self.file_path}"


class MemoryImportRequest(MCPRequestBase):
    file_path: Optional[str] = Field(
        default=None,
        description="""Server-side file path for import (Pattern A):

        Import Source Strategy:
        • None: Expect data in import_data field (Pattern B)
        • Relative path: Load from server-configured import directory
        • Absolute path: Load from specified location (if permitted)

        Examples:
        • file_path=None: Direct data import mode
        • file_path="backup/memories-2025-07-10.json": Server-side file
        • file_path="/shared/project-memories.json": Absolute path mode""",
    )
    import_data: Optional[str] = Field(
        default=None,
        description="""Direct import data (Pattern B):

        Data Format:
        • JSON string containing exported memory data
        • Used when file_path is None
        • Enables cross-node memory transfer
        • Supports compressed data (base64 encoded gzip)

        Usage Pattern:
        1. Export from source environment with file_path=None
        2. Copy export response data
        3. Import to target environment with import_data=<copied_data>""",
    )
    merge_strategy: str = Field(
        default="skip_duplicates",
        description="""How to handle duplicate memories:

        Merge Strategies:
        • "skip_duplicates": Keep existing, skip imports (safe default)
        • "overwrite": Replace existing with imported data
        • "create_versions": Create new versions of duplicates
        • "merge_metadata": Combine metadata while keeping content

        Use Cases:
        • skip_duplicates: Safe import without conflicts
        • overwrite: Force update from authoritative source
        • create_versions: Preserve both local and imported versions""",
    )
    target_scope_prefix: Optional[str] = Field(
        default=None,
        description="""Prefix to add to imported memory scopes:

        Scope Mapping:
        • None: Keep original scopes (default)
        • "imported/": Prefix all imported scopes
        • "backup/2025-07-10/": Add dated prefix

        Examples:
        • Original: "work/projects/alpha"
        • With prefix "imported/": "imported/work/projects/alpha"

        Use Cases: Isolate imported memories, avoid scope conflicts""",
    )
    validate_data: bool = Field(default=True, description="Validate imported data structure and content")

    def get_primary_identifier(self) -> str:
        """Primary identifier is the file path or import data preview"""
        if self.file_path:
            return f"file_path:{self.file_path}"
        if self.import_data:
            return f"import_data:{self.import_data[:50]}..." if len(self.import_data) > 50 else f"import_data:{self.import_data}"
        return "no_identifier"


class UnifiedSearchRequest(MCPRequestBase):
    """Unified search request supporting both standard and diversified search modes"""

    query: str = Field(description="Search query")
    mode: str = Field(
        default="standard",
        description="""Search mode:

        Modes:
        • "standard": Standard semantic search (default)
        • "diversified": Creative exploration with diversity filtering

        Strategy: Use 'standard' for targeted search, 'diversified' for brainstorming""",
        examples=["standard", "diversified"],
    )
    scope: Optional[str] = Field(
        default=None,
        description="""Target scope for search (supports hierarchy):

        Examples:
        • learning/programming: Find programming-related memories
        • work/current-project: Search current project context
        • personal: Browse personal thoughts and ideas
        • None: Search across all scopes

        Strategy: Start broad, narrow down if too many results""",
        examples=["learning/programming", "work/project", None],
    )
    include_child_scopes: bool = Field(default=False, description="Include child scopes in search")
    limit: int = Field(
        default=10,
        ge=1,
        le=100,
        description="""Maximum number of memories to retrieve:

        Values & Use Cases:
        • 5-10: Focused search (finding specific information) ← RECOMMENDED
        • 10-20: Balanced exploration (general ideation, learning review)
        • 20-50: Comprehensive discovery (brainstorming, research phase)

        Strategy: Start small (10), increase if you need broader context
        Example: limit=15 for creative thinking sessions

        ⚠️ Performance: Higher values increase processing time""",
        examples=[10, 15, 5],
    )
    similarity_threshold: float = Field(
        default=0.1,
        ge=0.0,
        le=1.0,
        description="""Similarity threshold for memory matching:

        Values & Use Cases:
        • 0.8-1.0: Near-identical content (duplicate detection, exact recall)
        • 0.4-0.8: Clear relevance (general search, learning review)
        • 0.2-0.4: Broader associations (idea expansion, new perspectives)
        • 0.1-0.2: Creative connections (brainstorming, unexpected links) ← RECOMMENDED

        Strategy: ChromaDB uses Top-K search, so low threshold (0.1) filters noise while LLM judges relevance via similarity scores
        Example: similarity_threshold=0.1 for most searches (trust Top-K ranking)""",
        examples=[0.1, 0.2, 0.4],
    )
    include_associations: bool = Field(default=True, description="Include related memories in results")

    # Diversified search specific parameters (only used when mode="diversified")
    min_score: float = Field(
        default=0.1,
        ge=0.0,
        le=1.0,
        description="""Minimum similarity threshold for candidates (diversified mode only):

        Values & Use Cases:
        • 0.1-0.2: Broad exploration (creative connections) ← RECOMMENDED
        • 0.2-0.4: Moderate relevance (balanced diversity)
        • 0.4-0.8: Focused but diverse (specific domain exploration)

        Strategy: Lower values for more creative, unexpected connections
        Example: min_score=0.1 for diverse brainstorming""",
        examples=[0.1, 0.2, 0.4],
    )
    diversity_threshold: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="""Similarity threshold for excluding similar items (diversified mode only):

        Values & Use Cases:
        • 0.8-0.9: Moderate diversity (exclude very similar) ← RECOMMENDED
        • 0.6-0.8: High diversity (exclude somewhat similar)
        • 0.9-1.0: Low diversity (exclude only near-duplicates)

        Strategy: 0.8 provides good balance of relevance and diversity
        Example: diversity_threshold=0.8 for balanced diverse results""",
        examples=[0.8, 0.7, 0.9],
    )
    expansion_factor: float = Field(
        default=2.5,
        ge=1.0,
        le=10.0,
        description="""Initial expansion multiplier for candidate search (diversified mode only):

        Values & Use Cases:
        • 2.0-3.0: Balanced performance and diversity ← RECOMMENDED
        • 3.0-5.0: Higher diversity, more processing time
        • 1.5-2.0: Faster processing, less diversity

        Strategy: 2.5 provides good balance for most use cases
        Example: expansion_factor=2.5 for standard diverse search""",
        examples=[2.5, 3, 2],
    )
    max_expansion_factor: float = Field(
        default=5,
        ge=1.0,
        le=20.0,
        description="""Maximum expansion when fallback is needed (diversified mode only):

        Values & Use Cases:
        • 5.0-10.0: Good fallback coverage ← RECOMMENDED
        • 10.0-20.0: Extensive fallback (slow but thorough)
        • 2.0-5.0: Limited fallback (faster but less comprehensive)

        Strategy: 5.0 provides good fallback without excessive processing
        Example: max_expansion_factor=5.0 for balanced fallback""",
        examples=[5, 7, 3],
    )

    def get_primary_identifier(self) -> str:
        """Primary identifier is the query preview"""
        return f"query:{self.query[:50]}..." if len(self.query) > 50 else f"query:{self.query}"


class MemoryManageRequest(CommonToolParameters):
    """Unified CRUD operations request model"""

    operation: str = Field(
        description="""CRUD operation to perform:

        Operations:
        • "get": Retrieve memory by ID
        • "update": Modify existing memory content/metadata
        • "delete": Remove memory permanently

        Strategy: Use 'get' for retrieval, 'update' for modifications, 'delete' for cleanup""",
        examples=["get", "update", "delete"],
    )
    memory_id: str = Field(description="Memory ID for the operation")

    # Optional parameters for different operations
    include_associations: bool = Field(default=True, description="Include related memories (used for 'get' operation)")

    # Update operation parameters (optional, only used when operation="update")
    content: Optional[str] = Field(default=None, description="New content for the memory (update operation only)")
    scope: Optional[str] = Field(
        default=None,
        description="""New scope for the memory (update operation only):

        Scope Organization:
        • learning/programming: Technical and programming content
        • work/projects: Project-related memories
        • personal/notes: Personal thoughts and reminders
        • session/[name]: Temporary session-specific content

        Strategy: Use scope_suggest for recommendations if unsure
        Example: scope="work/projects/mcp-improvements" for project organization""",
    )
    tags: Optional[List[str]] = Field(default=None, description="New tags for the memory (update operation only)")
    category: Optional[str] = Field(default=None, description="New category for the memory (update operation only)")
    metadata: Optional[Dict[str, Any]] = Field(
        default=None, description="New metadata for the memory (update operation only)"
    )
    preserve_associations: bool = Field(
        default=True,
        description="Whether to preserve existing associations when updating content (update operation only)",
    )

    def get_primary_identifier(self) -> str:
        """Primary identifier is the memory ID"""
        return self.memory_id


class MemorySyncRequest(MCPRequestBase, CommonToolParameters):
    """Unified import/export operations request model"""

    operation: str = Field(
        description="""Sync operation to perform:

        Operations:
        • "export": Backup memories to file or get data directly
        • "import": Restore memories from file or direct data

        Strategy: Use 'export' for backup/sharing, 'import' for restore/merge""",
        examples=["export", "import"],
    )

    # Common parameters
    scope: Optional[str] = Field(
        default=None,
        description="""Scope to export/target scope prefix for import:

        Export Scope Strategy:
        • None: Export all memories (full backup)
        • "work": Export only work-related memories
        • "session/project-name": Export specific session
        • "learning": Export learning-related memories

        Import Strategy (as target_scope_prefix):
        • None: Keep original scopes (default)
        • "imported/": Prefix all imported scopes
        • "backup/2025-07-10/": Add dated prefix

        Example: scope="work/projects/mcp-improvements" for project-specific sync""",
    )
    file_path: Optional[str] = Field(
        default=None,
        description="""File path for sync operation:

        File Path Strategy:
        • None: Return/expect data directly via response/request
        • Relative path: Save to/load from server-configured directory
        • Absolute path: Save to/load from specified location (if permitted)

        Examples:
        • file_path=None: Direct data exchange mode
        • file_path="backup/memories-2025-07-11.json": Server-side file
        • file_path="/shared/project-memories.json": Absolute path mode""",
    )

    # Export-specific parameters
    include_associations: bool = Field(
        default=True, description="Include association relationships in export (export operation only)"
    )
    compression: bool = Field(default=False, description="Compress export data with gzip (export operation only)")

    def get_primary_identifier(self) -> str:
        """Primary identifier is the operation and optional file path"""
        if self.file_path:
            return f"{self.operation}:{self.file_path}"
        return f"{self.operation}:direct_data"


class MemoryDiscoverAssociationsRequest(CommonToolParameters):
    """Request model for discovering memory associations"""

    memory_id: str = Field(description="Memory ID to discover associations for")
    limit: int = Field(
        default=10,
        description="""Maximum number of associations to retrieve:

        Values & Use Cases:
        • 5-10: Focused associations (finding specific relationships) ← RECOMMENDED
        • 10-20: Balanced exploration (general ideation, learning review)
        • 20-50: Comprehensive discovery (brainstorming, research phase)

        Strategy: Start small (10), increase if you need broader context
        Example: limit=15 for creative thinking sessions

        ⚠️ Performance: Higher values increase processing time""",
        examples=[10, 15, 5],
        ge=1,
        le=100
    )
    similarity_threshold: float = Field(
        default=0.1,
        description="""Similarity threshold for association matching:

        Values & Use Cases:
        • 0.8-1.0: Near-identical content (duplicate detection, exact recall)
        • 0.4-0.8: Clear relevance (general search, learning review)
        • 0.2-0.4: Broader associations (idea expansion, new perspectives)
        • 0.1-0.2: Creative connections (brainstorming, unexpected links) ← RECOMMENDED

        Strategy: ChromaDB uses Top-K search, so low threshold (0.1) filters noise while LLM judges relevance via similarity scores
        Example: similarity_threshold=0.1 for most searches (trust Top-K ranking)""",
        examples=[0.1, 0.2, 0.4],
        ge=0.0,
        le=1.0
    )

    def get_primary_identifier(self) -> str:
        """Primary identifier is the memory_id"""
        return f"memory_id:{self.memory_id}"
