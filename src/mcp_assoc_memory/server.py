"""
FastMCP-compliant memory management server implementation with associative memory capabilities
"""

from typing import Any, Dict, List, Optional, Annotated
from fastmcp import FastMCP, Context
from pydantic import Field, BaseModel
from datetime import datetime, timedelta
import logging
import asyncio
import uuid
import json
import gzip
import base64
import os
from pathlib import Path
import logging
import uuid
import asyncio

# Import the full associative memory architecture
from .core.memory_manager import MemoryManager
from .core.embedding_service import EmbeddingService, MockEmbeddingService, SentenceTransformerEmbeddingService
from .core.similarity import SimilarityCalculator
from .storage.vector_store import ChromaVectorStore
from .storage.metadata_store import SQLiteMetadataStore
from .storage.graph_store import NetworkXGraphStore
from .config import get_config
from .simple_persistence import get_persistent_storage

logger = logging.getLogger(__name__)

# FastMCP server instance
mcp = FastMCP(name="AssocMemoryServer")

# Initialize the associative memory system
config = get_config()

# Initialize storage components
vector_store = ChromaVectorStore()
metadata_store = SQLiteMetadataStore()
graph_store = NetworkXGraphStore()

# Use SentenceTransformerEmbeddingService for production, fallback to Mock for testing
try:
    embedding_service = SentenceTransformerEmbeddingService()
    logger.info("Using SentenceTransformerEmbeddingService for production")
except Exception as e:
    logger.warning(f"Failed to initialize SentenceTransformerEmbeddingService: {e}")
    embedding_service = MockEmbeddingService()
    logger.info("Falling back to MockEmbeddingService")

similarity_calculator = SimilarityCalculator()

# Initialize memory manager
memory_manager = MemoryManager(
    vector_store=vector_store,
    metadata_store=metadata_store,
    graph_store=graph_store,
    embedding_service=embedding_service,
    similarity_calculator=similarity_calculator
)

# Fallback simple storage for compatibility
memory_storage, persistence = get_persistent_storage()

# Global initialization flag
_initialized = False


async def ensure_initialized():
    """Ensure memory manager is initialized"""
    global _initialized
    if not _initialized:
        await memory_manager.initialize()
        _initialized = True


# Pydantic model definitions
class MemoryStoreRequest(BaseModel):
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
        examples=["learning/programming/python", "work/project/backend", "personal/ideas"]
    )
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")
    tags: Optional[List[str]] = Field(default=None, description="Memory tags")
    category: Optional[str] = Field(default=None, description="Memory category")
    auto_associate: bool = Field(default=True, description="Enable automatic association discovery")
    allow_duplicates: bool = Field(default=False, description="Allow storing duplicate content")
    similarity_threshold: float = Field(
        default=0.95, 
        ge=0.0, le=1.0, 
        description="""Duplicate detection threshold:
        
        Values & Use Cases:
        • 0.95-1.0: Prevent only near-identical content ← RECOMMENDED
        • 0.85-0.95: Block similar variations (stricter)
        • 0.70-0.85: Aggressive duplicate prevention
        
        Strategy: Keep high (0.95) unless you need strict deduplication
        Example: similarity_threshold=0.95 for most cases""",
        examples=[0.95, 0.90, 0.85]
    )


class MemoryResponse(BaseModel):
    memory_id: str
    content: str
    scope: str
    metadata: Dict[str, Any]
    tags: List[str]
    category: Optional[str]
    created_at: datetime
    similarity_score: Optional[float] = Field(default=None, description="Similarity score when from search")
    associations: Optional[List[str]] = Field(default=None, description="Related memory IDs")
    is_duplicate: bool = Field(default=False, description="Whether this was a duplicate detection")
    duplicate_of: Optional[str] = Field(default=None, description="Original memory ID if duplicate")


class MemorySearchRequest(BaseModel):
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
        examples=["learning/programming", "work/project", None]
    )
    include_child_scopes: bool = Field(default=False, description="Include child scopes in search")
    limit: int = Field(
        default=10, 
        ge=1, le=100, 
        description="""Maximum number of memories to retrieve:
        
        Values & Use Cases:
        • 5-10: Focused search (finding specific information) ← RECOMMENDED
        • 10-20: Balanced exploration (general ideation, learning review)
        • 20-50: Comprehensive discovery (brainstorming, research phase)
        
        Strategy: Start small (10), increase if you need broader context
        Example: limit=15 for creative thinking sessions
        
        ⚠️ Performance: Higher values increase processing time""",
        examples=[10, 15, 5]
    )
    similarity_threshold: float = Field(
        default=0.1, 
        ge=0.0, le=1.0, 
        description="""Similarity threshold for memory matching:
        
        Values & Use Cases:
        • 0.8-1.0: Near-identical content (duplicate detection, exact recall)
        • 0.4-0.8: Clear relevance (general search, learning review)
        • 0.2-0.4: Broader associations (idea expansion, new perspectives)
        • 0.1-0.2: Creative connections (brainstorming, unexpected links) ← RECOMMENDED
        
        Strategy: ChromaDB uses Top-K search, so low threshold (0.1) filters noise while LLM judges relevance via similarity scores
        Example: similarity_threshold=0.1 for most searches (trust Top-K ranking)""",
        examples=[0.1, 0.2, 0.4]
    )
    include_associations: bool = Field(default=True, description="Include related memories in results")


class ScopeListRequest(BaseModel):
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
        examples=[None, "work", "learning", "session"]
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
        
        Example: include_memory_counts=False for rapid scope exploration"""
    )


class ScopeSuggestRequest(BaseModel):
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
        examples=[None, "work/projects", "learning", "personal"]
    )


class MemoryUpdateRequest(BaseModel):
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
        Example: scope="work/projects/mcp-improvements" for project organization"""
    )
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="New metadata for the memory (optional)")
    tags: Optional[List[str]] = Field(default=None, description="New tags for the memory (optional)")
    category: Optional[str] = Field(default=None, description="New category for the memory (optional)")
    preserve_associations: bool = Field(
        default=True, 
        description="Whether to preserve existing associations when updating content"
    )


class MemoryMoveRequest(BaseModel):
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


class SessionManageRequest(BaseModel):
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
        examples=[None, "project-alpha", "meeting-notes", "experiment-001"]
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
        examples=[1, 7, 14, 30]
    )


class ScopeInfo(BaseModel):
    scope: str
    memory_count: int
    child_scopes: List[str]
    last_updated: Optional[datetime]


class SessionInfo(BaseModel):
    session_id: str
    scope: str
    memory_count: int
    created_at: datetime
    last_updated: datetime


class PaginationInfo(BaseModel):
    page: int
    per_page: int
    total_items: int
    total_pages: int
    has_next: bool
    has_prev: bool


class PaginatedResponse(BaseModel):
    items: List[Any]
    pagination: PaginationInfo


class ScopeListResponse(BaseModel):
    scopes: List[ScopeInfo]
    pagination: PaginationInfo
    total_scopes: int


class ScopeSuggestResponse(BaseModel):
    suggested_scope: str
    confidence: float
    reasoning: str
    alternatives: List[Dict[str, Any]]


class MemoryMoveResponse(BaseModel):
    success: bool
    moved_memories: int
    old_scope: str
    new_scope: str
    memory_ids: List[str]


class SessionManageResponse(BaseModel):
    action: str
    session_id: Optional[str] = None
    active_sessions: List[SessionInfo]
    cleaned_sessions: Optional[int] = None


class MemoryExportRequest(BaseModel):
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
        
        Example: scope="work/projects/mcp-improvements" for project-specific export"""
    )
    include_associations: bool = Field(
        default=True, 
        description="Include association relationships in export"
    )
    export_format: str = Field(
        default="json", 
        description="Export format (json, yaml)",
        pattern="^(json|yaml)$"
    )
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
        
        Security: Server validates paths against configured allowed directories"""
    )
    compression: bool = Field(
        default=False, 
        description="Compress export data (gzip)"
    )


class MemoryImportRequest(BaseModel):
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
        • file_path="/shared/project-memories.json": Absolute path mode"""
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
        3. Import to target environment with import_data=<copied_data>"""
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
        • create_versions: Preserve both local and imported versions"""
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
        
        Use Cases: Isolate imported memories, avoid scope conflicts"""
    )
    validate_data: bool = Field(
        default=True, 
        description="Validate imported data structure and content"
    )


class MemoryExportResponse(BaseModel):
    success: bool
    exported_count: int
    export_scope: Optional[str]
    file_path: Optional[str] = None
    export_data: Optional[str] = None  # For Pattern B
    export_size: int  # Size in bytes
    compression_used: bool
    metadata: Dict[str, Any]


class MemoryImportResponse(BaseModel):
    success: bool
    imported_count: int
    skipped_count: int
    overwritten_count: int
    import_source: str  # "file" or "direct_data"
    merge_strategy_used: str
    validation_errors: List[str]
    imported_scopes: List[str]


# Memory management tools
@mcp.tool(
    name="memory_store",
    description="""💾 Store New Memory: Solve "I want to remember this for later"

When to use:
→ Important insights you don't want to lose
→ Learning content that should connect with existing knowledge
→ Reference information for future projects

How it works:
Stores your content as a searchable memory, automatically discovers connections to existing memories, and integrates into your knowledge network.

💡 Quick Start:
- Auto-categorize: Let scope_suggest recommend the best scope
- Prevent duplicates: allow_duplicates=False (default) saves space
- Enable connections: auto_associate=True (default) builds knowledge links
- Quality control: similarity_threshold=0.95 prevents near-duplicates

⚠️ Important: Duplicate detection may block intentionally similar content

➡️ What's next: Use memory_discover_associations to explore new connections""",
    annotations={
        "title": "Memory Storage with Auto-Association",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False
    }
)
async def memory_store(
    request: MemoryStoreRequest,
    ctx: Context
) -> MemoryResponse:
    """Store a memory with full associative capabilities"""
    try:
        await ensure_initialized()
        await ctx.info(f"Storing memory in scope '{request.scope}': {request.content[:50]}...")
        
        # Store using the full memory manager with scope-based organization
        original_memory_id = None
        memory = await memory_manager.store_memory(
            scope=request.scope,  # Hierarchical scope for organization
            content=request.content,
            metadata=request.metadata or {},
            tags=request.tags or [],
            category=request.category,
            auto_associate=request.auto_associate,
            allow_duplicates=request.allow_duplicates,
            similarity_threshold=request.similarity_threshold
        )
        
        if not memory:
            raise ValueError("Failed to store memory")
        
        # Check if this was a duplicate detection
        is_duplicate = False
        if not request.allow_duplicates:
            # If the content was not new and we have an existing memory
            existing_in_storage = any(
                stored_mem["content"].strip() == request.content.strip() 
                for stored_mem in memory_storage.values()
                if stored_mem["memory_id"] != memory.id
            )
            if existing_in_storage:
                is_duplicate = True
                # Find the original memory ID
                for stored_mem in memory_storage.values():
                    if (stored_mem["content"].strip() == request.content.strip() and 
                        stored_mem["memory_id"] != memory.id):
                        original_memory_id = stored_mem["memory_id"]
                        break
        
        # Also store in simple storage for compatibility
        memory_data = {
            "memory_id": memory.id,
            "content": memory.content,
            "scope": request.scope,
            "metadata": memory.metadata,
            "tags": memory.tags,
            "category": memory.category,
            "created_at": memory.created_at
        }
        memory_storage[memory.id] = memory_data
        persistence.save_memories(memory_storage)
        
        action_msg = "existing duplicate returned" if is_duplicate else "new memory stored"
        await ctx.info(f"Memory {action_msg} with associations: {memory.id}")
        
        return MemoryResponse(
            memory_id=memory.id,
            content=memory.content,
            scope=request.scope,
            metadata=memory.metadata,
            tags=memory.tags,
            category=memory.category,
            created_at=memory.created_at,
            is_duplicate=is_duplicate,
            duplicate_of=original_memory_id
        )
        
    except Exception as e:
        await ctx.error(f"Failed to store memory: {e}")
        raise


@mcp.tool(
    name="memory_search",
    description="""🔍 Semantic Memory Search: Find related memories using natural language

When to use:
→ "What did I learn about [topic]?"
→ "Find memories related to [concept]"  
→ "Show me similar ideas to [content]"

How it works:
Converts your query to semantic embeddings and searches the vector space for conceptually similar memories, ranked by relevance.

💡 Quick Start:
- Default: similarity_threshold=0.1 (noise filtering with Top-K results)
- No results? Check limit parameter instead of lowering threshold
- Precision needed? Raise to 0.4+ for stricter matching
- Include associations: include_associations=True for richer context

⚠️ Important: ChromaDB returns Top-K results; threshold mainly filters noise, LLM judges relevance via similarity scores

➡️ What's next: Use memory_get for details, memory_discover_associations for deeper exploration""",
    annotations={
        "title": "Semantic Memory Search",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True
    }
)
async def memory_search(
    request: MemorySearchRequest,
    ctx: Context
) -> List[MemoryResponse]:
    """Search memories with full semantic and associative capabilities"""
    try:
        await ensure_initialized()
        scope_info = f" in scope '{request.scope}'" if request.scope else ""
        child_info = " (including child scopes)" if request.include_child_scopes else ""
        await ctx.info(f"Searching memories: '{request.query}'{scope_info}{child_info} (similarity >= {request.similarity_threshold})")
        
        # Perform semantic search using memory manager with scope
        search_results = await memory_manager.search_memories(
            query=request.query,
            scope=request.scope,  # Hierarchical scope for organization
            limit=request.limit,
            similarity_threshold=request.similarity_threshold
        )
        
        # Convert results to response format
        results = []
        for result in search_results:
            memory = result["memory"]
            similarity = result["similarity"]
            
            # Check scope filtering if needed
            memory_scope = memory.metadata.get("scope", memory.scope)
            if request.scope:
                if request.include_child_scopes:
                    # Include if memory scope starts with request scope (hierarchical match)
                    if not (memory_scope == request.scope or memory_scope.startswith(request.scope + "/")):
                        continue
                else:
                    # Exact scope match only
                    if memory_scope != request.scope:
                        continue
            
            # Get associations if requested
            associations = []
            if request.include_associations:
                try:
                    assoc_results = await memory_manager.search_memories(
                        query=memory.content,
                        scope=request.scope,
                        limit=5,
                        similarity_threshold=0.8
                    )
                    associations = [r["memory"].id for r in assoc_results if r["memory"].id != memory.id][:3]
                except Exception as e:
                    await ctx.warning(f"Failed to get associations for {memory.id}: {e}")
            
            results.append(MemoryResponse(
                memory_id=memory.id,
                content=memory.content,
                scope=memory_scope,
                metadata=memory.metadata,
                tags=memory.tags,
                category=memory.category,
                created_at=memory.created_at,
                similarity_score=similarity,
                associations=associations if associations else None
            ))
        
        await ctx.info(f"Found {len(results)} memories with semantic similarity")
        return results
        
    except Exception as e:
        await ctx.error(f"Failed to search memories: {e}")
        
        # Fallback to simple text search for compatibility
        await ctx.warning("Falling back to simple text search")
        
        results = []
        for memory_data in memory_storage.values():
            # Scope filtering
            if request.scope:
                memory_scope = memory_data["scope"]
                if request.include_child_scopes:
                    if not (memory_scope == request.scope or memory_scope.startswith(request.scope + "/")):
                        continue
                else:
                    if memory_scope != request.scope:
                        continue
            
            # Simple text matching
            if request.query.lower() in memory_data["content"].lower():
                results.append(MemoryResponse(
                    memory_id=memory_data["memory_id"],
                    content=memory_data["content"],
                    scope=memory_data["scope"],
                    metadata=memory_data.get("metadata", {}),
                    tags=memory_data.get("tags", []),
                    category=memory_data.get("category"),
                    created_at=memory_data["created_at"]
                ))
                if len(results) >= request.limit:
                    break
        
        return results


@mcp.tool(
    name="memory_get",
    description="""📄 Retrieve Memory Details: Get complete information about a specific memory

When to use:
→ After finding a memory ID from search results
→ When you need full content and metadata
→ To explore related memories through associations

How it works:
Fetches the complete memory record including content, metadata, tags, and optionally finds related memories for deeper exploration.

💡 Quick Start:
- Include associations: include_associations=True (default) for rich context
- Skip associations: include_associations=False for faster retrieval
- Use with search: memory_search → memory_get → explore details

⚠️ Important: Requires valid memory_id from previous search or storage

➡️ What's next: Use memory_discover_associations for deeper exploration, memory_store for new insights""",
    annotations={
        "title": "Memory Detail Retrieval",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True
    }
)
async def memory_get(
    memory_id: Annotated[str, Field(description="Memory ID")],
    ctx: Context,
    include_associations: Annotated[bool, Field(default=True, description="Include related memories")] = True
) -> Optional[MemoryResponse]:
    """Retrieve a memory with its associations"""
    try:
        await ensure_initialized()
        await ctx.info(f"Retrieving memory: {memory_id}")
        
        # Try to get from memory manager first
        memory = await memory_manager.get_memory(memory_id)
        
        if memory:
            # Get associations if requested
            associations = []
            if include_associations:
                try:
                    # Search for similar memories
                    assoc_results = await memory_manager.search_memories(
                        query=memory.content,
                        limit=5,
                        similarity_threshold=0.7
                    )
                    associations = [r["memory"].id for r in assoc_results if r["memory"].id != memory.id][:3]
                except Exception as e:
                    await ctx.warning(f"Failed to get associations: {e}")
            
            memory_scope = memory.metadata.get("scope", memory.scope)
            
            await ctx.info(f"Memory retrieved with {len(associations)} associations: {memory_id}")
            
            return MemoryResponse(
                memory_id=memory.id,
                content=memory.content,
                scope=memory_scope,
                metadata=memory.metadata,
                tags=memory.tags,
                category=memory.category,
                created_at=memory.created_at,
                associations=associations if associations else None
            )
        
        # Fallback to simple storage
        memory_data = memory_storage.get(memory_id)
        
        if not memory_data:
            await ctx.warning(f"Memory not found: {memory_id}")
            return None
            
        await ctx.info(f"Memory retrieved from fallback storage: {memory_id}")
        
        return MemoryResponse(
            memory_id=memory_data["memory_id"],
            content=memory_data["content"],
            scope=memory_data["scope"],
            metadata=memory_data.get("metadata", {}),
            tags=memory_data.get("tags", []),
            category=memory_data.get("category"),
            created_at=memory_data["created_at"]
        )
        
    except Exception as e:
        await ctx.error(f"Failed to retrieve memory: {e}")
        raise


@mcp.tool(
    name="memory_delete",
    description="""🗑️ Delete Memory: Permanently remove unwanted or incorrect memories

When to use:
→ Remove duplicate or incorrect information
→ Clean up outdated or irrelevant memories
→ Maintain clean and organized memory space

How it works:
Permanently removes the specified memory from storage. This action cannot be undone, so use with caution.

💡 Quick Start:
- Double-check: Use memory_get first to confirm content
- Safety first: Consider memory_move to archive instead of delete
- Bulk cleanup: Use memory_list_all to find candidates for deletion

⚠️ Important: This is a destructive operation - deleted memories cannot be recovered

➡️ What's next: Use scope_list to verify organization, memory_store to add corrected content""",
    annotations={
        "title": "Memory Deletion",
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": True
    }
)
async def memory_delete(
    memory_id: Annotated[str, Field(description="ID of the memory to delete")],
    ctx: Context
) -> Dict[str, Any]:
    """Delete a memory"""
    try:
        await ctx.warning(f"Deleting memory: {memory_id}")
        
        if memory_id in memory_storage:
            del memory_storage[memory_id]
            # Save to persistent storage
            persistence.save_memories(memory_storage)
            await ctx.info(f"Memory deleted: {memory_id}")
            return {"success": True, "message": "Memory deleted successfully", "memory_id": memory_id}
        else:
            await ctx.warning(f"Memory not found: {memory_id}")
            return {"success": False, "message": "Memory not found", "memory_id": memory_id}
        
    except Exception as e:
        await ctx.error(f"Failed to delete memory: {e}")
        raise


@mcp.tool(
    name="memory_update",
    description="""✏️ Update Memory: Modify existing memory content and metadata

When to use:
→ Correct or improve stored information
→ Add new insights to existing memories
→ Update categorization or organization
→ Refine content while preserving associations

How it works:
Updates specific fields of an existing memory while preserving other data and optionally maintaining semantic associations.

💡 Quick Start:
- Partial updates: Only specify fields you want to change
- Content updates: Provide new content, optionally preserve associations
- Reorganization: Change scope, tags, or category for better organization  
- Safe operation: Original memory preserved if update fails

⚠️ Important: Content changes may affect semantic associations

➡️ What's next: Use memory_get to verify changes, memory_discover_associations to explore new connections""",
    annotations={
        "title": "Memory Update",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False
    }
)
async def memory_update(
    request: MemoryUpdateRequest,
    ctx: Context
) -> MemoryResponse:
    """Update an existing memory"""
    try:
        await ensure_initialized()
        await ctx.info(f"Updating memory: {request.memory_id}")
        
        # First check if memory exists in advanced storage
        memory = await memory_manager.get_memory(request.memory_id)
        
        if memory:
            # Note: memory_manager.update_memory may not exist yet
            # For now, use direct updates to storage systems
            
            # Update scope in metadata if provided
            new_metadata = dict(memory.metadata)
            if request.scope:
                new_metadata["scope"] = request.scope
            if request.metadata:
                new_metadata.update(request.metadata)
            
            # Create updated memory object with new data
            updated_content = request.content if request.content is not None else memory.content
            updated_tags = request.tags if request.tags is not None else memory.tags
            updated_category = request.category if request.category is not None else memory.category
            
            # Also update in simple storage for compatibility
            if request.memory_id in memory_storage:
                memory_data = memory_storage[request.memory_id]
                if request.content is not None:
                    memory_data["content"] = request.content
                if request.scope is not None:
                    memory_data["scope"] = request.scope
                if request.metadata is not None:
                    if "metadata" not in memory_data:
                        memory_data["metadata"] = {}
                    memory_data["metadata"].update(request.metadata)
                if request.tags is not None:
                    memory_data["tags"] = request.tags
                if request.category is not None:
                    memory_data["category"] = request.category
                
                persistence.save_memories(memory_storage)
            
            memory_scope = new_metadata.get("scope", memory.scope)
            
            await ctx.info(f"Memory updated successfully: {request.memory_id}")
            
            return MemoryResponse(
                memory_id=memory.id,
                content=updated_content,
                scope=memory_scope,
                metadata=new_metadata,
                tags=updated_tags,
                category=updated_category,
                created_at=memory.created_at
            )
        
        # Fallback to simple storage update
        if request.memory_id not in memory_storage:
            await ctx.warning(f"Memory not found: {request.memory_id}")
            raise ValueError(f"Memory not found: {request.memory_id}")
        
        memory_data = memory_storage[request.memory_id]
        
        # Update specified fields only
        if request.content is not None:
            memory_data["content"] = request.content
        if request.scope is not None:
            memory_data["scope"] = request.scope
        if request.metadata is not None:
            if "metadata" not in memory_data:
                memory_data["metadata"] = {}
            memory_data["metadata"].update(request.metadata)
        if request.tags is not None:
            memory_data["tags"] = request.tags
        if request.category is not None:
            memory_data["category"] = request.category
        
        # Save to persistent storage
        persistence.save_memories(memory_storage)
        
        await ctx.info(f"Memory updated in fallback storage: {request.memory_id}")
        
        return MemoryResponse(
            memory_id=memory_data["memory_id"],
            content=memory_data["content"],
            scope=memory_data["scope"],
            metadata=memory_data.get("metadata", {}),
            tags=memory_data.get("tags", []),
            category=memory_data.get("category"),
            created_at=memory_data["created_at"]
        )
        
    except Exception as e:
        await ctx.error(f"Failed to update memory: {e}")
        raise


@mcp.tool(
    name="memory_list_all",
    description="""📋 Browse All Memories: "Show me everything I've stored"

When to use:
→ Initial exploration of your memory collection
→ Content auditing and organization review
→ Debug data consistency issues
→ System administration and bulk operations

How it works:
Retrieves all stored memories with pagination support, providing a complete overview of your knowledge base for management and debugging purposes.

💡 Quick Start:
- Start small: page=1, per_page=10 for initial overview
- Browse efficiently: Use pagination to avoid overwhelming results
- System check: per_page=50+ for bulk data validation
- Monitor growth: Regular checks to understand storage patterns

⚠️ Important: Large collections may take time to load; prefer memory_search for targeted access

➡️ What's next: Use memory_search for specific content, scope_list for organization overview""",
    annotations={
        "title": "All Memories List",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True
    }
)
async def memory_list_all(
    ctx: Context,
    page: Annotated[int, Field(
        default=1, 
        ge=1, 
        description="""Page number for pagination:
        
        Navigation Strategy:
        • Start with page=1 for initial overview
        • Use pagination.has_next to continue browsing
        • Jump to specific pages for targeted access
        • Monitor total_pages to understand collection size
        
        Example: page=1 for first overview, page=3 for deeper exploration""",
        examples=[1, 2, 3]
    )] = 1,
    per_page: Annotated[int, Field(
        default=10, 
        ge=1, 
        le=100, 
        description="""Items per page (1-100):
        
        Values & Use Cases:
        • 5-10: Quick overview (manageable chunks) ← RECOMMENDED
        • 20-50: Efficient browsing (bulk review)
        • 50-100: System analysis (comprehensive data check)
        
        Strategy: Start with 10, increase for bulk operations
        Example: per_page=25 for efficient content review""",
        examples=[10, 25, 50]
    )] = 10
) -> Dict[str, Any]:
    """List all memories with pagination (for debugging)"""
    try:
        await ctx.info(f"Retrieving memories (page {page}, {per_page} per page)...")
        
        all_memories = list(memory_storage.values())
        total_items = len(all_memories)
        
        # Calculate pagination
        total_pages = (total_items + per_page - 1) // per_page
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        
        # Get page items
        page_memories = all_memories[start_idx:end_idx]
        results = []
        for memory_data in page_memories:
            results.append(MemoryResponse(
                memory_id=memory_data["memory_id"],
                content=memory_data["content"],
                scope=memory_data["scope"],
                metadata=memory_data.get("metadata", {}),
                tags=memory_data.get("tags", []),
                category=memory_data.get("category"),
                created_at=memory_data["created_at"]
            ))
        
        pagination = PaginationInfo(
            page=page,
            per_page=per_page,
            total_items=total_items,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1
        )
        
        await ctx.info(f"Retrieved {len(results)} memories (page {page}/{total_pages})")
        
        return {
            "memories": results,
            "pagination": pagination
        }
        
    except Exception as e:
        await ctx.error(f"Failed to list memories: {e}")
        raise


# Resource definitions - Another important FastMCP concept
@mcp.resource("memory://stats")
async def get_memory_stats(ctx: Context) -> dict:
    """Provide memory statistics resource"""
    await ctx.info("Generating memory statistics...")
    
    stats = {
        "total_memories": len(memory_storage),
        "scopes": {},
        "active_sessions": [],
        "recent_memories": []
    }
    
    # Scope-wise statistics and hierarchy detection
    scope_counts = {}
    session_scopes = set()
    
    for memory_data in memory_storage.values():
        scope = memory_data["scope"]
        scope_counts[scope] = scope_counts.get(scope, 0) + 1
        
        # Track session scopes
        if scope.startswith("session/"):
            session_scopes.add(scope)
    
    # Build scope hierarchy information
    for scope, count in scope_counts.items():
        # Find child scopes (direct children only)
        child_scopes = get_child_scopes(scope, list(scope_counts.keys()))
        
        # Get last updated timestamp for this scope
        scope_memories = [m for m in memory_storage.values() if m["scope"] == scope]
        last_updated = max((m["created_at"] for m in scope_memories), default=None)
        
        stats["scopes"][scope] = {
            "count": count,
            "child_scopes": child_scopes,
            "last_updated": last_updated.isoformat() if last_updated else None
        }
    
    stats["active_sessions"] = list(session_scopes)
    
    # Latest 5 memories
    sorted_memories = sorted(
        memory_storage.values(),
        key=lambda x: x["created_at"],
        reverse=True
    )[:5]
    
    stats["recent_memories"] = [
        {"memory_id": m["memory_id"], "content": m["content"][:50] + "...", "scope": m["scope"]}
        for m in sorted_memories
    ]
    
    return stats


@mcp.resource("memory://scope/{scope}")
async def get_scope_memories(scope: str, ctx: Context) -> dict:
    """Provide memory list for specified scope resource"""
    await ctx.info(f"Retrieving memories for scope '{scope}'...")
    
    scope_memories = [
        memory_data for memory_data in memory_storage.values()
        if memory_data["scope"] == scope
    ]
    
    result = {
        "scope": scope,
        "count": len(scope_memories),
        "memories": [
            {
                "memory_id": m["memory_id"],
                "content": m["content"],
                "created_at": m["created_at"]
            }
            for m in scope_memories
        ]
    }
    
    return result


# Prompt definitions - LLM interaction patterns
@mcp.prompt(
    name="analyze_memories",
    description="Generate prompts for memory analysis"
)
async def analyze_memories_prompt(
    ctx: Context,
    scope: Annotated[str, Field(default="user/default", description="Target scope for analysis")] = "user/default",
    include_child_scopes: Annotated[bool, Field(default=True, description="Include child scopes in analysis")] = True
) -> str:
    """Generate memory analysis prompt"""
    await ctx.info(f"Generating analysis prompt for scope '{scope}'...")
    
    scope_memories = []
    for memory_data in memory_storage.values():
        memory_scope = memory_data["scope"]
        if include_child_scopes:
            # Include if memory scope starts with request scope (hierarchical match)
            if memory_scope == scope or memory_scope.startswith(scope + "/"):
                scope_memories.append(memory_data)
        else:
            # Exact scope match only
            if memory_scope == scope:
                scope_memories.append(memory_data)
    
    memories_text = "\n".join([
        f"- [{m['scope']}] {m['content']}" for m in scope_memories[:10]  # Maximum 10 memories
    ])
    
    scope_info = " and child scopes" if include_child_scopes else ""
    
    prompt = f"""The following memories are stored in the "{scope}" scope{scope_info}:

{memories_text}

Please analyze these memories and provide insights on the following aspects:
1. Main themes and patterns within this scope
2. Important keywords and concepts
3. Relationships between memories
4. Scope organization effectiveness
5. Recommendations for future memory management

Please provide the analysis in a structured format."""

    return prompt


@mcp.prompt(
    name="summarize_memory",
    description="Generate prompts for summarizing specific memories"
)
async def summarize_memory_prompt(
    ctx: Context,
    memory_id: Annotated[str, Field(description="ID of the memory to summarize")],
    context_scope: Annotated[str, Field(default="", description="Contextual scope for summary generation")] = ""
) -> str:
    """Generate memory summary prompt"""
    await ctx.info(f"Generating summary prompt for memory '{memory_id}'...")
    
    memory_data = memory_storage.get(memory_id)
    if not memory_data:
        raise ValueError(f"Memory not found: {memory_id}")
    
    context_info = f" within the context of '{context_scope}' scope" if context_scope else ""
    
    prompt = f"""Please summarize the following memory{context_info}:

Memory ID: {memory_data['memory_id']}
Scope: {memory_data['scope']}
Created: {memory_data['created_at']}
Content: {memory_data['content']}
Metadata: {memory_data['metadata']}

Please provide the summary in the following format:
- Key Points: [Main points]
- Keywords: [Important keywords]
- Category: [Appropriate category]
- Scope Context: [How this memory fits within its scope]
- Relationships: [Potential relationships with other memories]"""

    return prompt


# Scope management tools implementation

@mcp.tool(
    name="scope_list",
    description="""🗂️ Browse Scope Hierarchy: "Show me how my memories are organized"

When to use:
→ Understand your memory organization structure
→ Plan new memory storage locations
→ Review memory distribution across topics
→ Navigate hierarchical knowledge organization

How it works:
Displays the hierarchical structure of all scopes with memory counts, helping you understand and navigate your knowledge organization.

💡 Quick Start:
- Full overview: No parent_scope (shows everything)
- Focused view: parent_scope="work" (shows work/* hierarchy)
- Quick counts: include_memory_counts=True (default, shows distribution)
- Structure only: include_memory_counts=False (faster, organization focus)

⚠️ Important: Large scope hierarchies may have many entries

➡️ What's next: Use scope_suggest for new content placement, memory_search for specific scope exploration""",
    annotations={
        "title": "Scope Hierarchy List",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True
    }
)
async def scope_list(
    request: ScopeListRequest,
    ctx: Context
) -> ScopeListResponse:
    """List scopes with pagination and hierarchy"""
    try:
        await ctx.info(f"Listing scopes from parent: {request.parent_scope or 'root'}")
        
        # Get all unique scopes
        all_scopes = list(set(memory_data["scope"] for memory_data in memory_storage.values()))
        
        # Filter by parent scope if specified
        if request.parent_scope:
            filtered_scopes = [
                scope for scope in all_scopes 
                if scope.startswith(request.parent_scope + "/") or scope == request.parent_scope
            ]
        else:
            filtered_scopes = all_scopes
        
        # Build scope info
        scope_infos = []
        for scope in sorted(filtered_scopes):
            memory_count = len([m for m in memory_storage.values() if m["scope"] == scope])
            child_scopes = get_child_scopes(scope, all_scopes)
            
            # Get last updated
            scope_memories = [m for m in memory_storage.values() if m["scope"] == scope]
            last_updated = max((m["created_at"] for m in scope_memories), default=None)
            
            scope_infos.append(ScopeInfo(
                scope=scope,
                memory_count=memory_count if request.include_memory_counts else 0,
                child_scopes=child_scopes,
                last_updated=last_updated
            ))
        
        # Simple pagination (page 1, all items for now)
        total_scopes = len(scope_infos)
        pagination = PaginationInfo(
            page=1,
            per_page=total_scopes,
            total_items=total_scopes,
            total_pages=1,
            has_next=False,
            has_prev=False
        )
        
        await ctx.info(f"Found {total_scopes} scopes")
        
        return ScopeListResponse(
            scopes=scope_infos,
            pagination=pagination,
            total_scopes=total_scopes
        )
        
    except Exception as e:
        await ctx.error(f"Failed to list scopes: {e}")
        raise


@mcp.tool(
    name="scope_suggest",
    description="""🎯 Smart Scope Recommendation: "Where should I store this content?"

When to use:
→ Before storing new memories (optimal organization)
→ When unsure about content categorization
→ To maintain consistent organization patterns
→ For automatic content classification workflows

How it works:
Analyzes your content using keyword detection and context patterns to recommend the most appropriate scope, with confidence scores and alternative suggestions.

💡 Quick Start:
- Auto-categorize: Provide content, get scope recommendation
- Context-aware: Include current_scope for related content placement
- Multiple options: Review alternatives array for flexibility
- High confidence: confidence >0.8 indicates strong recommendation

⚠️ Important: Suggestions are based on keyword patterns; review recommendations for accuracy

➡️ What's next: Use memory_store with suggested scope, scope_list to verify organization""",
    annotations={
        "title": "Scope Recommendation",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True
    }
)
async def scope_suggest(
    request: ScopeSuggestRequest,
    ctx: Context
) -> ScopeSuggestResponse:
    """Suggest scope based on content analysis"""
    try:
        await ctx.info(f"Analyzing content for scope suggestion: {request.content[:50]}...")
        
        content_lower = request.content.lower()
        
        # Simple rule-based scope suggestion
        suggestions = []
        
        # Technical keywords
        if any(word in content_lower for word in ["code", "programming", "fastmcp", "python", "implementation"]):
            suggestions.append(("learning/programming", 0.8, "Contains technical programming content"))
        
        # Meeting keywords
        if any(word in content_lower for word in ["meeting", "minutes", "standup", "review"]):
            suggestions.append(("work/meetings", 0.9, "Contains meeting-related content"))
        
        # Project keywords
        if any(word in content_lower for word in ["project", "feature", "implementation", "development"]):
            suggestions.append(("work/projects", 0.7, "Contains project-related content"))
        
        # Personal keywords
        if any(word in content_lower for word in ["personal", "private", "reminder", "todo"]):
            suggestions.append(("personal/notes", 0.8, "Contains personal content"))
        
        # Security keywords
        if any(word in content_lower for word in ["security", "auth", "authentication", "secure"]):
            suggestions.append(("work/projects/security", 0.9, "Contains security-related content"))
        
        # Default suggestion
        if not suggestions:
            suggestions.append(("user/default", 0.5, "No specific patterns detected, using default scope"))
        
        # Use current scope context if available
        if request.current_scope and suggestions:
            best_suggestion = max(suggestions, key=lambda x: x[1])
            # Enhance with current scope context
            if request.current_scope.startswith("work/"):
                suggestions.insert(0, (f"{request.current_scope}/related", 0.6, "Based on current work context"))
        
        # Sort by confidence and pick the best
        suggestions.sort(key=lambda x: x[1], reverse=True)
        best = suggestions[0]
        
        alternatives = [
            {"scope": s[0], "confidence": s[1], "reasoning": s[2]} 
            for s in suggestions[1:4]  # Top 3 alternatives
        ]
        
        await ctx.info(f"Suggested scope: {best[0]} (confidence: {best[1]})")
        
        return ScopeSuggestResponse(
            suggested_scope=best[0],
            confidence=best[1],
            reasoning=best[2],
            alternatives=alternatives
        )
        
    except Exception as e:
        await ctx.error(f"Failed to suggest scope: {e}")
        raise


@mcp.tool(
    name="memory_move",
    description="""📦 Reorganize Memories: "Move these memories to better organize my knowledge"

When to use:
→ Reorganizing content after learning better categorization
→ Consolidating scattered memories into unified scopes
→ Correcting initial storage mistakes
→ Refactoring knowledge structure as it grows

How it works:
Moves specified memories from their current scopes to a new target scope, preserving all content and metadata while updating organization.

💡 Quick Start:
- Single memory: memory_ids=["id1"], target_scope="new/location"
- Bulk operation: memory_ids=["id1","id2","id3"] for efficient reorganization
- Scope validation: System validates target_scope format automatically
- Safe operation: All content and metadata preserved during move

⚠️ Important: Cannot undo moves; verify target_scope before execution

➡️ What's next: Use scope_list to verify new organization, memory_search in new scope to confirm placement""",
    annotations={
        "title": "Memory Move",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False
    }
)
async def memory_move(
    request: MemoryMoveRequest,
    ctx: Context
) -> MemoryMoveResponse:
    """Move memories to a different scope"""
    try:
        await ctx.info(f"Moving {len(request.memory_ids)} memories to scope '{request.target_scope}'")
        
        # Validate target scope
        if not validate_scope_path(request.target_scope):
            raise ValueError(f"Invalid target scope: {request.target_scope}")
        
        moved_memories = 0
        successful_ids = []
        old_scopes = set()
        
        for memory_id in request.memory_ids:
            if memory_id in memory_storage:
                old_scope = memory_storage[memory_id]["scope"]
                old_scopes.add(old_scope)
                
                # Update the scope
                memory_storage[memory_id]["scope"] = request.target_scope
                moved_memories += 1
                successful_ids.append(memory_id)
                
                await ctx.info(f"Moved memory {memory_id} from '{old_scope}' to '{request.target_scope}'")
            else:
                await ctx.warning(f"Memory not found: {memory_id}")
        
        old_scope_summary = ", ".join(old_scopes) if old_scopes else "unknown"
        
        # Save to persistent storage if any memories were moved
        if moved_memories > 0:
            persistence.save_memories(memory_storage)
        
        await ctx.info(f"Successfully moved {moved_memories} memories")
        
        return MemoryMoveResponse(
            success=moved_memories > 0,
            moved_memories=moved_memories,
            old_scope=old_scope_summary,
            new_scope=request.target_scope,
            memory_ids=successful_ids
        )
        
    except Exception as e:
        await ctx.error(f"Failed to move memories: {e}")
        raise


@mcp.tool(
    name="session_manage",
    description="""⏱️ Session Lifecycle Management: "Manage temporary memory sessions"

When to use:
→ Creating isolated working sessions for projects
→ Organizing temporary memories that may be cleaned up
→ Managing conversation or task-specific memory scopes
→ Cleaning up old session data to maintain system performance

How it works:
Provides complete session lifecycle management including creation, listing, and automated cleanup of session-scoped memories based on age.

💡 Quick Start:
- New session: action="create" (auto-generates session ID)
- Custom session: action="create", session_id="my-project-session"
- View sessions: action="list" (shows all active sessions)
- Auto cleanup: action="cleanup", max_age_days=7 (removes old sessions)

⚠️ Important: Cleanup is permanent; archive important session data before cleanup

➡️ What's next: Use memory_store with session scope, memory_search within sessions""",
    annotations={
        "title": "Session Management",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False
    }
)
async def session_manage(
    request: SessionManageRequest,
    ctx: Context
) -> SessionManageResponse:
    """Manage sessions and cleanup"""
    try:
        await ctx.info(f"Session management action: {request.action}")
        
        if request.action == "create":
            # Create a new session scope
            session_id = request.session_id or f"session-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            session_scope = f"session/{session_id}"
            
            # Add a session marker memory
            session_memory = {
                "memory_id": str(uuid.uuid4()),
                "content": f"Session created: {session_id}",
                "scope": session_scope,
                "metadata": {"session_marker": True, "created_by": "session_manage"},
                "created_at": datetime.now()
            }
            memory_storage[session_memory["memory_id"]] = session_memory
            
            # Save to persistent storage
            persistence.save_memories(memory_storage)
            
            await ctx.info(f"Created session: {session_id}")
            
            return SessionManageResponse(
                action="create",
                session_id=session_id,
                active_sessions=[SessionInfo(
                    session_id=session_id,
                    scope=session_scope,
                    memory_count=1,
                    created_at=datetime.now(),
                    last_updated=datetime.now()
                )]
            )
        
        elif request.action == "list":
            # List all active sessions
            session_scopes = {}
            for memory_data in memory_storage.values():
                scope = memory_data["scope"]
                if scope.startswith("session/"):
                    session_id = scope.split("/", 1)[1]
                    if session_id not in session_scopes:
                        session_scopes[session_id] = {
                            "scope": scope,
                            "memories": [],
                            "created_at": memory_data["created_at"],
                            "last_updated": memory_data["created_at"]
                        }
                    session_scopes[session_id]["memories"].append(memory_data)
                    session_scopes[session_id]["last_updated"] = max(
                        session_scopes[session_id]["last_updated"],
                        memory_data["created_at"]
                    )
            
            active_sessions = [
                SessionInfo(
                    session_id=session_id,
                    scope=data["scope"],
                    memory_count=len(data["memories"]),
                    created_at=data["created_at"],
                    last_updated=data["last_updated"]
                )
                for session_id, data in session_scopes.items()
            ]
            
            await ctx.info(f"Found {len(active_sessions)} active sessions")
            
            return SessionManageResponse(
                action="list",
                active_sessions=active_sessions
            )
        
        elif request.action == "cleanup":
            # Clean up old sessions
            cutoff_date = datetime.now() - timedelta(days=request.max_age_days or 7)
            cleaned_count = 0
            
            memories_to_delete = []
            for memory_id, memory_data in memory_storage.items():
                if (memory_data["scope"].startswith("session/") and
                        memory_data["created_at"] < cutoff_date):
                    memories_to_delete.append(memory_id)
            
            for memory_id in memories_to_delete:
                del memory_storage[memory_id]
                cleaned_count += 1
            
            # Save to persistent storage if any memories were cleaned
            if cleaned_count > 0:
                persistence.save_memories(memory_storage)
            
            await ctx.info(f"Cleaned up {cleaned_count} old session memories")
            
            return SessionManageResponse(
                action="cleanup",
                active_sessions=[],
                cleaned_sessions=cleaned_count
            )
        
        else:
            raise ValueError(f"Unknown action: {request.action}")
        
    except Exception as e:
        await ctx.error(f"Failed to manage session: {e}")
        raise


# Associative memory discovery tool
@mcp.tool(
    name="memory_discover_associations",
    description="""🧩 Discover Memory Associations: "What else is related to this idea?"

When to use:
→ After finding a relevant memory (follow-up exploration)
→ Before making decisions (gather related context)
→ During creative thinking (find unexpected connections)

How it works:
Takes a specific memory as starting point and finds semantically related memories using advanced similarity matching and diversity filtering.

💡 Quick Start:
- Reliable connections: similarity_threshold=0.7, limit=10
- Idea expansion: threshold=0.5, limit=15 (broader exploration)
- Creative brainstorming: threshold=0.3, limit=20+ (surprising links)
- Quality results: System automatically filters duplicates for diversity

⚠️ Important: Lower thresholds may include tangentially related content

➡️ What's next: Use memory_get for details, memory_store for new insights""",
    annotations={
        "title": "Memory Association Discovery",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True
    }
)
async def memory_discover_associations(
    memory_id: Annotated[str, Field(description="Memory ID to find associations for")],
    ctx: Context,
    limit: Annotated[int, Field(
        default=10, 
        ge=1, le=50, 
        description="""Maximum number of associations to discover:
        
        Values & Use Cases:
        • 5-10: Quick overview (essential connections) ← RECOMMENDED
        • 10-20: Thorough exploration (comprehensive context)
        • 20-50: Deep discovery (research, creative sessions)
        
        Strategy: Start with 10, increase for broader exploration
        Example: limit=15 for creative brainstorming""",
        examples=[10, 15, 5]
    )] = 10,
    similarity_threshold: Annotated[float, Field(
        default=0.1, 
        ge=0.0, le=1.0, 
        description="""Minimum similarity score for associations:
        
        Values & Use Cases:
        • 0.7-1.0: Strong connections (reliable relations)
        • 0.4-0.7: Interesting links (idea expansion)
        • 0.2-0.4: Creative leaps (brainstorming, innovation)
        • 0.1-0.2: Surprising connections (artistic thinking) ← RECOMMENDED
        
        Strategy: ChromaDB uses Top-K search; low threshold filters noise, LLM judges via similarity scores
        Example: similarity_threshold=0.1 for broad creative exploration""",
        examples=[0.1, 0.2, 0.4]
    )] = 0.1
) -> Dict[str, Any]:
    """Discover semantic associations for a specific memory"""
    try:
        await ensure_initialized()
        await ctx.info(f"Discovering associations for memory: {memory_id}")
        
        # Get the source memory
        memory = await memory_manager.get_memory(memory_id)
        if not memory:
            await ctx.warning(f"Memory not found: {memory_id}")
            return {"error": "Memory not found", "associations": []}
        
        # Find similar memories with enhanced search strategy
        search_results = await memory_manager.search_memories(
            query=memory.content,
            limit=limit * 3,  # Search more to account for filtering
            similarity_threshold=max(0.1, similarity_threshold - 0.2)  # Lower threshold for diversity
        )
        
        # If we didn't find enough diverse results, try with the original content plus tags
        if len(search_results) < limit:
            # Create enhanced query with tags and category
            enhanced_query = memory.content
            if memory.tags:
                enhanced_query += " " + " ".join(memory.tags)
            if memory.category:
                enhanced_query += " " + memory.category
            
            additional_results = await memory_manager.search_memories(
                query=enhanced_query,
                limit=limit * 2,
                similarity_threshold=max(0.1, similarity_threshold - 0.3)
            )
            
            # Merge results (will be deduplicated later)
            search_results.extend(additional_results)
        
        # Filter out the source memory and format results
        associations = []
        seen_content = set()  # Track content to avoid duplicates
        
        for result in search_results:
            assoc_memory = result["memory"]
            
            # Skip the source memory itself
            if assoc_memory.id == memory_id:
                continue
            
            # Skip memories with identical content to promote diversity
            content_hash = hash(assoc_memory.content.strip().lower())
            if content_hash in seen_content:
                continue
            seen_content.add(content_hash)
            
            memory_scope = assoc_memory.metadata.get("scope", assoc_memory.scope)
            
            associations.append({
                "memory_id": assoc_memory.id,
                "content": assoc_memory.content[:100] + "..." if len(assoc_memory.content) > 100 else assoc_memory.content,
                "scope": memory_scope,
                "similarity_score": result["similarity"],
                "category": assoc_memory.category,
                "tags": assoc_memory.tags,
                "created_at": assoc_memory.created_at
            })
            
            # Break if we have enough diverse associations
            if len(associations) >= limit:
                break
        
        await ctx.info(f"Found {len(associations)} associations for memory {memory_id}")
        
        return {
            "source_memory_id": memory_id,
            "source_content": memory.content[:100] + "..." if len(memory.content) > 100 else memory.content,
            "associations": associations,
            "total_found": len(associations),
            "similarity_threshold": similarity_threshold
        }
        
    except Exception as e:
        await ctx.error(f"Failed to discover associations: {e}")
        return {"error": str(e), "associations": []}


@mcp.tool(
    name="memory_import",
    description="""📥 Import Memories: "Restore or sync memories from backup or other environments"

When to use:
→ Restore memories from backup files
→ Sync memories from other development environments
→ Import shared project memories from team
→ Merge memory datasets

How it works:
Imports memories and metadata from files or direct data, with configurable merge strategies to handle duplicates and conflicts.

💡 Quick Start:
- File import: file_path="backup/memories-2025-07-10.json"
- Direct import: import_data="<exported_json_data>"
- Safe merge: merge_strategy="skip_duplicates" (default)
- Scope isolation: target_scope_prefix="imported/" to avoid conflicts

⚠️ Important: Embeddings will be re-computed after import

➡️ What's next: Use memory_search to verify imported memories""",
    annotations={
        "title": "Memory Import",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False
    }
)
async def memory_import(
    request: MemoryImportRequest,
    ctx: Context
) -> MemoryImportResponse:
    """Import memories from file or direct data"""
    try:
        await ensure_initialized()
        
        import_mode = "file" if request.file_path else "direct data"
        await ctx.info(f"Importing memories via {import_mode} with merge strategy: {request.merge_strategy}")
        
        # Load import data
        import_data_str = None
        import_source = ""
        
        if request.file_path:
            # Pattern A: File import
            file_path = await _resolve_import_path(request.file_path)
            
            if not Path(file_path).exists():
                raise ValueError(f"Import file not found: {file_path}")
            
            # Check file size
            file_size = Path(file_path).stat().st_size
            try:
                max_size_mb = config.storage.max_import_size_mb
            except AttributeError:
                max_size_mb = 100  # Default 100MB limit
                
            if file_size > max_size_mb * 1024 * 1024:
                raise ValueError(f"Import file size ({file_size / 1024 / 1024:.1f}MB) exceeds limit ({max_size_mb}MB)")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                file_content = f.read()
                
            # Handle compressed files
            if file_content.startswith("# Compressed MCP Memory Export"):
                lines = file_content.split('\n', 1)
                if len(lines) > 1:
                    compressed_data = base64.b64decode(lines[1])
                    import_data_str = gzip.decompress(compressed_data).decode('utf-8')
                else:
                    raise ValueError("Invalid compressed file format")
            else:
                import_data_str = file_content
                
            import_source = f"file:{file_path}"
            
        elif request.import_data:
            # Pattern B: Direct data import
            import_data_str = request.import_data
            
            # Check if it's compressed (base64 encoded)
            try:
                if not import_data_str.strip().startswith('{'):
                    # Assume it's compressed
                    compressed_data = base64.b64decode(import_data_str)
                    import_data_str = gzip.decompress(compressed_data).decode('utf-8')
            except:
                pass  # If decompression fails, assume it's plain JSON
                
            import_source = "direct_data"
            
        else:
            raise ValueError("Either file_path or import_data must be provided")
        
        # Parse JSON data
        try:
            import_data = json.loads(import_data_str)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON data: {e}")
        
        # Validate data structure if requested
        validation_errors = []
        if request.validate_data:
            validation_errors = await _validate_import_data(import_data)
            if validation_errors and request.validate_data:
                raise ValueError(f"Validation errors: {validation_errors}")
        
        # Process import
        imported_count = 0
        skipped_count = 0
        overwritten_count = 0
        imported_scopes = set()
        
        memories_to_import = import_data.get("memories", [])
        
        for memory_data in memories_to_import:
            try:
                memory_id = memory_data["memory_id"]
                original_scope = memory_data["scope"]
                
                # Apply scope prefix if specified
                final_scope = original_scope
                if request.target_scope_prefix:
                    final_scope = f"{request.target_scope_prefix.rstrip('/')}/{original_scope}"
                
                imported_scopes.add(final_scope)
                
                # Check for existing memory
                existing_memory = memory_storage.get(memory_id)
                
                if existing_memory:
                    if request.merge_strategy == "skip_duplicates":
                        skipped_count += 1
                        continue
                    elif request.merge_strategy == "overwrite":
                        # Proceed with overwrite
                        overwritten_count += 1
                    elif request.merge_strategy == "create_versions":
                        # Create new ID for version
                        memory_id = f"{memory_id}_v{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    elif request.merge_strategy == "merge_metadata":
                        # Merge metadata while keeping existing content
                        if "metadata" not in existing_memory:
                            existing_memory["metadata"] = {}
                        existing_memory["metadata"].update(memory_data.get("metadata", {}))
                        memory_storage[memory_id] = existing_memory
                        imported_count += 1
                        continue
                
                # Prepare memory for import
                imported_memory = {
                    "memory_id": memory_id,
                    "content": memory_data["content"],
                    "scope": final_scope,
                    "metadata": memory_data.get("metadata", {}),
                    "tags": memory_data.get("tags", []),
                    "category": memory_data.get("category"),
                    "created_at": datetime.fromisoformat(memory_data["created_at"]) if isinstance(memory_data["created_at"], str) else memory_data["created_at"]
                }
                
                # Store in simple storage
                memory_storage[memory_id] = imported_memory
                imported_count += 1
                
                # TODO: Store in advanced storage if available
                # This would require re-computing embeddings and associations
                
            except Exception as e:
                validation_errors.append(f"Failed to import memory {memory_data.get('memory_id', 'unknown')}: {e}")
                continue
        
        # Save to persistent storage
        persistence.save_memories(memory_storage)
        
        await ctx.info(f"Import completed: {imported_count} imported, {skipped_count} skipped, {overwritten_count} overwritten")
        
        return MemoryImportResponse(
            success=True,
            imported_count=imported_count,
            skipped_count=skipped_count,
            overwritten_count=overwritten_count,
            import_source=import_source,
            merge_strategy_used=request.merge_strategy,
            validation_errors=validation_errors,
            imported_scopes=list(imported_scopes)
        )
        
    except Exception as e:
        await ctx.error(f"Failed to import memories: {e}")
        raise


# File path resolution utilities
async def _resolve_export_path(file_path: str) -> Path:
    """Resolve and validate export file path"""
    if Path(file_path).is_absolute():
        try:
            allow_absolute = config.storage.allow_absolute_paths
        except AttributeError:
            allow_absolute = False
        if not allow_absolute:
            raise ValueError("Absolute paths not allowed in configuration")
        return Path(file_path)
    else:
        # Relative to export directory
        try:
            data_dir = config.storage.data_dir
            export_dir_name = config.storage.export_dir
        except AttributeError:
            data_dir = "data"
            export_dir_name = "exports"
        export_dir = Path(data_dir) / export_dir_name
        return export_dir / file_path


async def _resolve_import_path(file_path: str) -> Path:
    """Resolve and validate import file path"""
    if Path(file_path).is_absolute():
        try:
            allow_absolute = config.storage.allow_absolute_paths
        except AttributeError:
            allow_absolute = False
        if not allow_absolute:
            raise ValueError("Absolute paths not allowed in configuration")
        return Path(file_path)
    else:
        # Try import directory first, then export directory
        try:
            data_dir = config.storage.data_dir
            import_dir_name = config.storage.import_dir
            export_dir_name = config.storage.export_dir
        except AttributeError:
            data_dir = "data"
            import_dir_name = "imports"
            export_dir_name = "exports"
            
        import_dir = Path(data_dir) / import_dir_name
        import_path = import_dir / file_path
        
        if import_path.exists():
            return import_path
        
        # Fallback to export directory
        export_dir = Path(data_dir) / export_dir_name
        export_path = export_dir / file_path
        
        if export_path.exists():
            return export_path
            
        # Return original path for error handling
        return import_path


async def _validate_import_data(import_data: Dict[str, Any]) -> List[str]:
    """Validate import data structure"""
    errors = []
    
    # Check required fields
    if "memories" not in import_data:
        errors.append("Missing 'memories' field")
        return errors
    
    if not isinstance(import_data["memories"], list):
        errors.append("'memories' must be a list")
        return errors
    
    # Validate each memory
    for i, memory in enumerate(import_data["memories"]):
        if not isinstance(memory, dict):
            errors.append(f"Memory {i}: must be an object")
            continue
            
        required_fields = ["memory_id", "content", "scope", "created_at"]
        for field in required_fields:
            if field not in memory:
                errors.append(f"Memory {i}: missing required field '{field}'")
    
    return errors


@mcp.tool(
    name="memory_export",
    description="""📤 Export Memories: "Save my memories for backup or sync across environments"

When to use:
→ Backup memories before system changes
→ Sync memories across development environments
→ Share project-specific memories with team
→ Create portable memory snapshots

How it works:
Exports memories and metadata (excluding re-computable embeddings) to files or direct data exchange for cross-environment portability.

💡 Quick Start:
- Full backup: No scope specified, file_path=None for direct data
- Project export: scope="work/projects/my-project" 
- File export: file_path="backup/memories-2025-07-10.json"
- Compressed: compression=True for large datasets

⚠️ Important: Embeddings excluded (will be re-computed on import)

➡️ What's next: Use memory_import to restore in target environment""",
    annotations={
        "title": "Memory Export",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True
    }
)
async def memory_export(
    request: MemoryExportRequest,
    ctx: Context
) -> MemoryExportResponse:
    """Export memories to file or direct data exchange"""
    try:
        await ensure_initialized()
        
        scope_info = f" from scope '{request.scope}'" if request.scope else " (all scopes)"
        export_mode = "file" if request.file_path else "direct data"
        await ctx.info(f"Exporting memories{scope_info} via {export_mode}")
        
        # Filter memories by scope
        export_memories = []
        for memory_data in memory_storage.values():
            if request.scope:
                memory_scope = memory_data["scope"]
                # Include if memory scope matches or is a child of request scope
                if memory_scope == request.scope or memory_scope.startswith(request.scope + "/"):
                    export_memories.append(memory_data)
            else:
                export_memories.append(memory_data)
        
        # Prepare export data structure
        export_data = {
            "format_version": "1.0",
            "export_timestamp": datetime.now().isoformat(),
            "export_scope": request.scope,
            "total_memories": len(export_memories),
            "include_associations": request.include_associations,
            "memories": []
        }
        
        # Process each memory for export
        for memory_data in export_memories:
            memory_export = {
                "memory_id": memory_data["memory_id"],
                "content": memory_data["content"],
                "scope": memory_data["scope"],
                "metadata": memory_data.get("metadata", {}),
                "tags": memory_data.get("tags", []),
                "category": memory_data.get("category"),
                "created_at": memory_data["created_at"].isoformat() if isinstance(memory_data["created_at"], datetime) else memory_data["created_at"]
            }
            
            # Add associations if requested
            if request.include_associations:
                # Get associations from advanced storage if available
                try:
                    memory = await memory_manager.get_memory(memory_data["memory_id"])
                    if memory:
                        associations = await memory_manager.get_associations(memory.id)
                        memory_export["associations"] = [assoc.id for assoc in associations]
                except:
                    memory_export["associations"] = []
            
            export_data["memories"].append(memory_export)
        
        # Convert to JSON
        json_data = json.dumps(export_data, indent=2, ensure_ascii=False)
        
        # Apply compression if requested
        final_data = json_data
        compression_used = False
        if request.compression:
            compressed_data = gzip.compress(json_data.encode('utf-8'))
            final_data = base64.b64encode(compressed_data).decode('ascii')
            compression_used = True
        
        export_size = len(final_data.encode('utf-8'))
        
        # Check size limits (use fallback values if config not properly loaded)
        try:
            max_size_mb = config.storage.max_export_size_mb
        except AttributeError:
            max_size_mb = 100  # Default 100MB limit
            
        if export_size > max_size_mb * 1024 * 1024:
            raise ValueError(f"Export size ({export_size / 1024 / 1024:.1f}MB) exceeds limit ({max_size_mb}MB)")
        
        # Handle file export (Pattern A)
        if request.file_path:
            file_path = await _resolve_export_path(request.file_path)
            
            # Ensure export directory exists
            export_dir = Path(file_path).parent
            export_dir.mkdir(parents=True, exist_ok=True)
            
            # Write to file
            with open(file_path, 'w', encoding='utf-8') as f:
                if compression_used:
                    # For file export, store compressed data as base64
                    f.write(f"# Compressed MCP Memory Export (base64-encoded gzip)\n{final_data}")
                else:
                    f.write(final_data)
            
            await ctx.info(f"Exported {len(export_memories)} memories to file: {file_path}")
            
            return MemoryExportResponse(
                success=True,
                exported_count=len(export_memories),
                export_scope=request.scope,
                file_path=str(file_path),
                export_size=export_size,
                compression_used=compression_used,
                metadata={
                    "format_version": "1.0",
                    "export_format": request.export_format,
                    "timestamp": datetime.now().isoformat()
                }
            )
        
        # Handle direct data export (Pattern B)
        else:
            await ctx.info(f"Exported {len(export_memories)} memories as direct data")
            
            return MemoryExportResponse(
                success=True,
                exported_count=len(export_memories),
                export_scope=request.scope,
                export_data=final_data,
                export_size=export_size,
                compression_used=compression_used,
                metadata={
                    "format_version": "1.0",
                    "export_format": request.export_format,
                    "timestamp": datetime.now().isoformat()
                }
            )
            
    except Exception as e:
        await ctx.error(f"Failed to export memories: {e}")
        raise


# Scope validation utilities
def validate_scope_path(scope: str) -> bool:
    """Validate scope path format and constraints"""
    if not scope or len(scope) > 255:
        return False
    
    # Check for reserved patterns
    if scope.startswith('.') or '..' in scope:
        return False
    
    # Split and validate each segment
    segments = scope.split('/')
    if len(segments) > 10:  # Max depth limit
        return False
    
    for segment in segments:
        if not segment or len(segment) > 50:
            return False
        # Allow Unicode characters, alphanumeric, underscore, hyphen
        if not all(c.isalnum() or c in '_-' or ord(c) > 127 for c in segment):
            return False
    
    return True


def get_parent_scope(scope: str) -> Optional[str]:
    """Get parent scope from hierarchical path"""
    if '/' not in scope:
        return None
    return '/'.join(scope.split('/')[:-1])


def get_child_scopes(parent_scope: str, all_scopes: List[str]) -> List[str]:
    """Get direct child scopes"""
    children = []
    for scope in all_scopes:
        if scope.startswith(parent_scope + '/'):
            # Check if it's a direct child (not grandchild)
            relative_path = scope[len(parent_scope) + 1:]
            if '/' not in relative_path:
                children.append(scope)
    return children


if __name__ == "__main__":
    async def startup():
        """Initialize the memory system on startup"""
        try:
            await ensure_initialized()
            logger.info("Associative memory system initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize associative memory system: {e}")
            # Continue with simple storage as fallback
    
    # Initialize before running
    asyncio.run(startup())
    
    # Run with stdio transport for better MCP client compatibility
    mcp.run(transport="stdio")
