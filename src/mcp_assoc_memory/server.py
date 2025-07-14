"""
FastMCP-compliant memory management server implementation with associative memory capabilities
"""

import asyncio
import logging
import sys
import traceback
from pathlib import Path
from typing import Annotated, Any, Dict, List, Optional


# CRITICAL: Initialize logging first, before any imports that might fail
def initialize_early_logging() -> None:
    """Initialize logging before anything else to capture startup errors"""
    try:
        # Ensure logs directory exists
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        # Configure logging immediately - only file handler to avoid duplicates
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s [%(levelname)s][%(name)s] %(message)s',
            handlers=[
                logging.FileHandler('logs/mcp_server.log', mode='a')
            ]
        )

        logger = logging.getLogger(__name__)
        logger.info("=" * 80)
        logger.info("MCP Associative Memory Server - Starting up")
        logger.info(f"Python version: {sys.version}")
        logger.info(f"Working directory: {Path.cwd()}")
        logger.info(f"Python path: {sys.path[:3]}")  # First 3 entries

        return logger
    except Exception as e:
        # Fallback: write to stderr directly
        print(f"CRITICAL: Failed to initialize logging: {e}", file=sys.stderr)
        print(f"CRITICAL: Traceback: {traceback.format_exc()}", file=sys.stderr)
        sys.exit(1)


# Initialize logging immediately
logger = initialize_early_logging()

try:
    logger.info("Importing FastMCP and Pydantic...")
    from fastmcp import Context, FastMCP
    from pydantic import Field
    logger.info("Core imports successful")

    logger.info("Importing project dependencies...")
    from .api.dependencies import set_global_dependencies
    logger.info("Dependencies import successful")

    logger.info("Importing API models...")
    from .api.models import (
        MemoryManageRequest,
        MemoryMoveRequest,
        MemoryResponse,
        MemoryStoreRequest,
        MemoryStoreResponse,
        MemorySyncRequest,
        ScopeListRequest,
        ScopeSuggestRequest,
        SessionManageRequest,
        UnifiedSearchRequest,
    )
    logger.info("API models import successful")

    logger.info("Importing API tools...")
    from .api.tools import (
        handle_analyze_memories_prompt,
        handle_memory_discover_associations,
        handle_memory_list_all,
        handle_memory_get,
        handle_memory_update,
        handle_memory_delete,
        handle_memory_move,
        handle_memory_stats,
        handle_scope_memories,
        handle_memory_store,
        handle_memory_export,
        handle_memory_import,
        handle_scope_list,
        handle_scope_suggest,
        handle_session_manage,
        handle_summarize_memory_prompt,
        handle_memory_search,
        handle_unified_search,
        handle_memory_manage,
        handle_memory_sync,
        handle_diversified_search,
        set_dependencies,
        set_prompt_dependencies,
        set_resource_dependencies,
        set_scope_dependencies,
    )
    logger.info("API tools import successful")

    logger.info("Importing additional tools...")
    from .api.tools.other_tools import set_dependencies as set_other_dependencies
    logger.info("Additional tools import successful")

    logger.info("Importing configuration...")
    from .config import get_config, initialize_config
    logger.info("Configuration import successful")

    logger.info("Importing embedding services...")
    from .core.embedding_service import (
        MockEmbeddingService,
        SentenceTransformerEmbeddingService,
    )
    logger.info("Embedding services import successful")

    logger.info("Importing core similarity and memory manager...")
    # Import the full associative memory architecture
    from .core.similarity import SimilarityCalculator
    from .core.singleton_memory_manager import (
        initialize_memory_manager,
    )
    logger.info("Memory manager import successful")

    logger.info("Importing storage components...")
    from .simple_persistence import get_persistent_storage
    from .storage.graph_store import NetworkXGraphStore
    from .storage.metadata_store import SQLiteMetadataStore
    from .storage.vector_store import ChromaVectorStore
    logger.info("Storage components import successful")

    logger.info("All imports completed successfully")

except ImportError as e:
    logger.error(f"IMPORT ERROR: {e}")
    logger.error(f"Failed import traceback: {traceback.format_exc()}")
    print(f"CRITICAL: Import failed: {e}", file=sys.stderr)
    sys.exit(1)
except Exception as e:
    logger.error(f"UNEXPECTED ERROR during imports: {e}")
    logger.error(f"Full traceback: {traceback.format_exc()}")
    print(f"CRITICAL: Unexpected error: {e}", file=sys.stderr)
    sys.exit(1)

logger = logging.getLogger(__name__)

# FastMCP server instance
mcp: FastMCP = FastMCP(name="AssocMemoryServer")

# Initialize the associative memory system
try:
    logger.info("Initializing configuration...")
    # Initialize configuration singleton with explicit config file path
    config_path = "config.json"  # Explicitly specify the config file
    config = initialize_config(config_path)
    logger.info(f"Server initialized with config from: {config_path}")
    logger.info(f"API configuration loaded: {hasattr(config.api, 'default_response_level')}")
    if hasattr(config.api, 'default_response_level'):
        logger.info(f"Default response level: {config.api.default_response_level}")
    logger.info("Configuration initialized successfully")

    logger.info("Initializing storage components...")
    # Initialize storage components
    vector_store = ChromaVectorStore()
    metadata_store = SQLiteMetadataStore()
    graph_store = NetworkXGraphStore()
    logger.info("Storage components initialized successfully")

    logger.info("Initializing embedding service...")
    # Use SentenceTransformerEmbeddingService for production, fallback to Mock for testing
    try:
        embedding_service = SentenceTransformerEmbeddingService()
        logger.info("Using SentenceTransformerEmbeddingService for production")
    except Exception as e:
        logger.warning(f"Failed to initialize SentenceTransformerEmbeddingService: {e}")
        embedding_service = MockEmbeddingService()  # type: ignore
        logger.info("Using MockEmbeddingService as fallback")

    logger.info("All components initialized successfully")

except Exception as e:
    logger.error(f"INITIALIZATION ERROR: {e}")
    logger.error(f"Full traceback: {traceback.format_exc()}")
    print(f"CRITICAL: Initialization failed: {e}", file=sys.stderr)
    sys.exit(1)

similarity_calculator = SimilarityCalculator()

# Initialize memory manager using singleton pattern (will be done in ensure_initialized)
memory_manager = None

# Fallback simple storage for compatibility
memory_storage, persistence = get_persistent_storage()

# Global initialization flag
_initialized = False


async def ensure_initialized() -> None:
    """Ensure memory manager is initialized using singleton pattern"""
    global _initialized, memory_manager
    if not _initialized:
        try:
            # Initialize memory manager using singleton pattern
            memory_manager = await initialize_memory_manager(
                vector_store=vector_store,
                metadata_store=metadata_store,
                graph_store=graph_store,
                embedding_service=embedding_service,
                similarity_calculator=similarity_calculator,
            )

            # Set up tool dependencies - use centralized dependency manager
            set_global_dependencies(memory_manager, memory_storage, persistence)

            # Also set legacy dependencies for backward compatibility
            set_dependencies(memory_manager, memory_storage, persistence)
            set_scope_dependencies(memory_manager)
            set_resource_dependencies(memory_manager, memory_storage, persistence)
            set_prompt_dependencies(memory_manager, memory_storage, persistence)
            set_other_dependencies(memory_manager)

            _initialized = True
            logger.info("Memory manager initialized successfully using singleton pattern")

        except Exception as e:
            # Reset flag to allow retry
            _initialized = False
            logger.error(f"Memory manager initialization failed: {e}")
            raise


# Debug tool to check memory manager state
@mcp.tool(
    name="debug_memory_manager",
    description="Debug tool to check memory manager state in MCP context",
)
async def debug_memory_manager(ctx: Context) -> Dict[str, Any]:
    """Debug tool to check memory manager state"""
    # Import memory tools to check global state
    from .api.dependencies import dependencies
    from .api.tools.memory_tools import memory_manager as tools_memory_manager

    return {
        "server_memory_manager": str(memory_manager),
        "server_memory_manager_type": str(type(memory_manager)),
        "tools_memory_manager": str(tools_memory_manager),
        "tools_memory_manager_type": str(type(tools_memory_manager)),
        "dependencies_memory_manager": str(dependencies.memory_manager),
        "dependencies_memory_manager_type": str(type(dependencies.memory_manager)),
        "are_same_object": memory_manager is tools_memory_manager,
        "server_initialized": "_initialized" in globals() and globals()["_initialized"],
    }


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
- Duplicate handling: duplicate_threshold=0.85 (prevent similar content), =null (no checking)
- Force storage: allow_duplicates=true (store even if duplicate detected)
- Enable connections: auto_associate=True (default) builds knowledge links

⚠️ Important: Duplicate detection may block intentionally similar content

➡️ What's next: Use memory_discover_associations to explore new connections""",
    annotations={
        "title": "Memory Storage",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
    },
)
async def memory_store(request: MemoryStoreRequest, ctx: Context) -> Dict[str, Any]:
    """Store a memory with full associative capabilities"""
    return await handle_memory_store(request, ctx)


# Old memory_search deleted - replaced by memory_search_unified (renamed to memory_search)


# Old memory_diversified_search deleted - replaced by memory_search diversified mode


# Old memory_get deleted - replaced by memory_manage get operation


# Old memory_delete deleted - replaced by memory_manage delete operation


# Old memory_update deleted - replaced by memory_manage update operation


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
    annotations={"title": "All Memories List", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True},
)
async def memory_list_all(
    ctx: Context,
    page: Annotated[
        int,
        Field(
            default=1,
            ge=1,
            description="""Page number for pagination:

        Navigation Strategy:
        • Start with page=1 for initial overview
        • Use pagination.has_next to continue browsing
        • Jump to specific pages for targeted access
        • Monitor total_pages to understand collection size

        Example: page=1 for first overview, page=3 for deeper exploration""",
            examples=[1, 2, 3],
        ),
    ] = 1,
    per_page: Annotated[
        int,
        Field(
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
            examples=[10, 25, 50],
        ),
    ] = 10,
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
@mcp.prompt(name="analyze_memories", description="Generate prompts for memory analysis")
async def analyze_memories_prompt(
    ctx: Context,
    scope: Annotated[str, Field(default="user/default", description="Target scope for analysis")] = "user/default",
    include_child_scopes: Annotated[bool, Field(default=True, description="Include child scopes in analysis")] = True,
) -> str:
    """Generate memory analysis prompt"""
    return await handle_analyze_memories_prompt(scope, include_child_scopes, ctx)


@mcp.prompt(name="summarize_memory", description="Generate prompts for summarizing specific memories")
async def summarize_memory_prompt(
    ctx: Context,
    memory_id: Annotated[str, Field(description="ID of the memory to summarize")],
    context_scope: Annotated[str, Field(default="", description="Contextual scope for summary generation")] = "",
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
        "idempotentHint": False,
    },
)
async def session_manage(request: SessionManageRequest, ctx: Context) -> Any:
    """Manage sessions and cleanup"""
    response = await handle_session_manage(request, ctx)
    return response


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
        "idempotentHint": True,
    },
)
async def scope_list(request: ScopeListRequest, ctx: Context) -> Any:
    """List scopes with pagination and hierarchy"""
    response = await handle_scope_list(request, ctx)
    return response


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
        "idempotentHint": True,
    },
)
async def scope_suggest(request: ScopeSuggestRequest, ctx: Context) -> Any:
    """Suggest scope based on content analysis"""
    response = await handle_scope_suggest(request, ctx)
    return response


# Old memory_export deleted - replaced by memory_sync export operation


# Old memory_import deleted - replaced by memory_sync import operation


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
    annotations={"title": "Memory Move", "readOnlyHint": False, "destructiveHint": False, "idempotentHint": False},
)
async def memory_move(request: MemoryMoveRequest, ctx: Context) -> Any:
    """Move memories to a new scope"""
    response = await handle_memory_move(request, ctx)
    return response


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
        "idempotentHint": True,
    },
)
async def memory_discover_associations(
    memory_id: str, limit: int = 10, similarity_threshold: float = 0.1, ctx: Optional[Context] = None
) -> Any:
    """Discover semantic associations for a specific memory"""
    response = await handle_memory_discover_associations(memory_id, ctx, limit, similarity_threshold)
    return response


@mcp.tool(
    name="memory_search",
    description="""🔍 Memory Search: Flexible search with standard and diversified modes

When to use:
→ Standard search for specific information
→ Diversified search for creative exploration
→ Unified API for different search strategies

How it works:
Provides unified interface for both standard semantic search and diversified search modes. Use mode parameter to control search behavior.

💡 Quick Start:
- Standard search: mode="standard" for focused results (default)
- Creative exploration: mode="diversified" for diverse perspectives
- Auto-categorize: Let system recommend best approach
- Consistent interface: Same parameters across modes

⚠️ Important: Different modes may return different result structures

➡️ What's next: Use memory_manage to get details, adjust mode based on needs""",
    annotations={
        "title": "Memory Search Interface",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
    },
)
async def memory_search(request: UnifiedSearchRequest, ctx: Context) -> Dict[str, Any]:
    """Unified search supporting both standard and diversified modes"""
    # Delegate to handler
    result = await handle_unified_search(request, ctx)
    # Return the complete handler result
    if isinstance(result, dict):
        return result
    # Return empty results structure if result format is unexpected
    return {"results": [], "success": False, "message": "Unexpected result format"}


@mcp.tool(
    name="memory_manage",
    description="""🔧 Unified Memory Management: Handle get, update, and delete operations

When to use:
→ Single interface for common memory operations
→ Consistent parameter patterns across CRUD operations
→ Reduced API surface complexity

How it works:
Provides unified interface for memory retrieval, updates, and deletion using operation parameter to control behavior.

💡 Quick Start:
- Get memory: operation="get", memory_id="...", include_associations=True
- Update memory: operation="update", memory_id="...", content="new content"
- Delete memory: operation="delete", memory_id="..."
- Consistent interface: Same response patterns across operations

⚠️ Important: Delete operations are permanent and cannot be undone

➡️ What's next: Use memory_discover_associations after updates to explore new connections""",
    annotations={
        "title": "Unified Memory Management",
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
    },
)
async def memory_manage(request: MemoryManageRequest, ctx: Context) -> Dict[str, Any]:
    """Unified CRUD operations for memory management"""
    # Delegate to handler
    return await handle_memory_manage(request, ctx)


@mcp.tool(
    name="memory_sync",
    description="""🔄 Unified Memory Sync: Handle import and export operations

When to use:
→ Single interface for data synchronization operations
→ Backup and restore memories with consistent interface
→ Cross-environment memory transfer with unified parameters

How it works:
Provides unified interface for both import and export operations using operation parameter to control behavior.

💡 Quick Start:
- Export backup: operation="export", scope="work", file_path="backup.json"
- Import restore: operation="import", file_path="backup.json", merge_strategy="skip_duplicates"
- Direct transfer: Use file_path=None for data exchange without files
- Consistent interface: Same response patterns across operations

⚠️ Important: Import operations may modify existing data based on merge strategy

➡️ What's next: Use memory_search to verify sync results, scope_list to review organization""",
    annotations={
        "title": "Unified Memory Synchronization",
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
    },
)
async def memory_sync(request: MemorySyncRequest, ctx: Context) -> Dict[str, Any]:
    """Unified import/export operations for memory synchronization"""
    # Delegate to handler
    return await handle_memory_sync(request, ctx)


def main() -> None:
    """Main entry point for the MCP server"""

    async def startup() -> None:
        """Initialize the memory system on startup"""
        try:
            # Initialize response processor
            from .api.processing import create_response_processor, set_global_processor
            processor = create_response_processor(config)
            set_global_processor(processor)
            logger.info("Response processor initialized successfully")

            # Initialize memory system
            await ensure_initialized()
            logger.info("Associative memory system initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize systems: {e}")
            # Continue with simple storage as fallback

    # Initialize before running
    asyncio.run(startup())

    # Use transport configuration from config object
    transport_config = config.transport

    if transport_config.http_enabled:
        # HTTP transport
        port = transport_config.http_port
        host = getattr(transport_config, 'http_host', "0.0.0.0")
        logger.info(f"Starting server on HTTP transport: {host}:{port}")
        mcp.run(transport="http", host=host, port=port)
    elif transport_config.sse_enabled:
        # SSE transport
        port = getattr(transport_config, 'sse_port', 8000)
        host = getattr(transport_config, 'sse_host', "0.0.0.0")
        logger.info(f"Starting server on SSE transport: {host}:{port}")
        mcp.run(transport="sse", host=host, port=port)
    else:
        # Default to STDIO transport
        logger.info("Starting server on STDIO transport")
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
