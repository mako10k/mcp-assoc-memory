"""
FastMCP-compliant memory management server implementation with associative memory capabilities
"""

import logging
import json
import gzip
import base64
import uuid
import asyncio
from typing import Any, Dict, List, Optional, Annotated
from fastmcp import FastMCP, Context
from pydantic import Field, BaseModel
from datetime import datetime, timedelta
from pathlib import Path

# Import the full associative memory architecture
from .core.memory_manager import MemoryManager
from .core.embedding_service import EmbeddingService, MockEmbeddingService, SentenceTransformerEmbeddingService
from .core.similarity import SimilarityCalculator
from .storage.vector_store import ChromaVectorStore
from .storage.metadata_store import SQLiteMetadataStore
from .storage.graph_store import NetworkXGraphStore
from .config import get_config
from .simple_persistence import get_persistent_storage
from .api.models import (
    MemoryStoreRequest, MemorySearchRequest, DiversifiedSearchRequest, MemoryUpdateRequest,
    MemoryMoveRequest, ScopeListRequest, ScopeSuggestRequest,
    SessionManageRequest, MemoryExportRequest, MemoryImportRequest,
    Memory, SearchResult, Association, MemoryWithAssociations,
    SearchResultWithAssociations, ScopeInfo, ScopeRecommendation,
    SessionInfo, PaginationInfo, MemoryResponse, ScopeListResponse,
    ScopeSuggestResponse, MemoryMoveResponse, SessionManageResponse,
    MemoryImportResponse, MemoryExportResponse, MCPResponse, ErrorResponse
)
from .api.utils import validate_scope_path, get_child_scopes, get_parent_scope
from .api.tools import (
    set_dependencies,
    set_scope_dependencies,
    set_resource_dependencies,
    set_prompt_dependencies,
    handle_memory_store,
    handle_memory_search,
    handle_diversified_search,
    handle_memory_get,
    handle_memory_delete,
    handle_memory_update,
    handle_memory_discover_associations,
    handle_memory_import,
    handle_memory_list_all,
    handle_scope_list,
    handle_scope_suggest,
    handle_memory_export,
    handle_memory_move,
    handle_session_manage,
    handle_memory_stats,
    handle_scope_memories,
    handle_analyze_memories_prompt,
    handle_summarize_memory_prompt
)

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

# Set up tool dependencies
set_dependencies(memory_manager, memory_storage, persistence)
set_scope_dependencies(memory_manager)
set_resource_dependencies(memory_manager, memory_storage, persistence)
set_prompt_dependencies(memory_manager, memory_storage, persistence)

# Global initialization flag
_initialized = False


async def ensure_initialized():
    """Ensure memory manager is initialized"""
    global _initialized
    if not _initialized:
        await memory_manager.initialize()
        # Set dependencies for tool handlers
        set_dependencies(memory_manager, memory_storage, persistence)
        set_scope_dependencies(memory_manager)
        set_resource_dependencies(memory_manager, memory_storage, persistence)
        set_prompt_dependencies(memory_manager, memory_storage, persistence)
        _initialized = True


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
    return await handle_memory_store(request, ctx)


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
    # Delegate to handler
    result = await handle_memory_search(request, ctx)
    # Convert handler result to expected format
    if isinstance(result, dict) and "results" in result:
        return result["results"]
    return result


@mcp.tool(
    name="memory_diversified_search",
    description="""🔄 Diversified Memory Search: Find diverse memories for creative exploration

When to use:
→ Brainstorming and creative thinking sessions
→ Breaking out of similar content clusters
→ Exploring different perspectives on a topic
→ Discovering unexpected connections and ideas

How it works:
Uses a diversified similarity algorithm to find memories that are relevant but not too similar to each other, ensuring broader coverage of your knowledge space rather than drilling deep into specific topics.

💡 Quick Start:
- Creative exploration: Use default settings for balanced diversity
- Broad brainstorming: Lower diversity_threshold (0.6-0.7) for more variety
- Focused diversity: Higher min_score (0.3-0.5) for relevant but diverse results
- Deep exploration: Increase limit (15-25) for comprehensive diverse coverage

⚠️ Important: This method prioritizes diversity over pure similarity ranking

➡️ What's next: Use memory_get for details, memory_search for focused follow-up""",
    annotations={
        "title": "Diversified Similarity Search",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True
    }
)
async def memory_diversified_search(
    request: DiversifiedSearchRequest,
    ctx: Context
) -> List[MemoryResponse]:
    """Search memories with diversification for creative exploration"""
    # Delegate to handler
    result = await handle_diversified_search(request, ctx)
    # Convert handler result to expected format
    if isinstance(result, dict) and "results" in result:
        return result["results"]
    return result


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
    result = await handle_memory_get(memory_id, ctx, include_associations)
    # Convert handler result to expected format  
    if isinstance(result, dict) and "error" not in result:
        return MemoryResponse(**result)
    return None


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
    return await handle_memory_delete(memory_id, ctx)


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
    return await handle_memory_update(request, ctx)


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
    return await handle_memory_list_all(page, per_page, ctx)


# Resource definitions - Another important FastMCP concept
@mcp.resource("memory://stats")
async def get_memory_stats(ctx: Context) -> dict:
    """Provide memory statistics resource"""
    return await handle_memory_stats(ctx)


@mcp.resource("memory://scope/{scope}")
async def get_scope_memories(scope: str, ctx: Context) -> dict:
    """Provide memory list for specified scope resource"""
    return await handle_scope_memories(scope, ctx)


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
    return await handle_analyze_memories_prompt(scope, include_child_scopes, ctx)


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
    return await handle_summarize_memory_prompt(memory_id, context_scope, ctx)


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
        "title": "Session Lifecycle Management",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False
    }
)
async def session_manage(request: SessionManageRequest, ctx: Context):
    """Manage sessions and cleanup"""
    return await handle_session_manage(request, ctx)


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
async def scope_list(request: ScopeListRequest, ctx: Context):
    """List scopes with pagination and hierarchy"""
    return await handle_scope_list(request, ctx)


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
async def scope_suggest(request: ScopeSuggestRequest, ctx: Context):
    """Suggest scope based on content analysis"""
    return await handle_scope_suggest(request, ctx)


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
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True
    }
)
async def memory_export(request: MemoryExportRequest, ctx: Context):
    """Export memories to file or direct data exchange"""
    return await handle_memory_export(request, ctx)


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
async def memory_import(request: MemoryImportRequest, ctx: Context):
    """Import memories from file or direct data"""
    return await handle_memory_import(request, ctx)


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
async def memory_move(request: MemoryMoveRequest, ctx: Context):
    """Move memories to a new scope"""
    return await handle_memory_move(request, ctx)


@mcp.tool(
    name="memory_discover_associations",
    description="""🧠 Discover Memory Associations: "What else is related to this idea?"

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
    memory_id: str,
    limit: int = 10,
    similarity_threshold: float = 0.1,
    ctx: Context = None
):
    """Discover semantic associations for a specific memory"""
    return await handle_memory_discover_associations(memory_id, ctx, limit, similarity_threshold)


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
