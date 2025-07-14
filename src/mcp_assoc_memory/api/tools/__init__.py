"""Tool handlers for MCP associative memory server."""

# Memory management tools
# Export/import tools - RE-ENABLED
from .export_tools import handle_memory_export
from .memory_tools import (
    ensure_initialized,
    handle_diversified_search,
    handle_memory_delete,
    handle_memory_get,
    handle_memory_import,
    handle_memory_list_all,
    handle_memory_search,
    handle_memory_store,
    handle_memory_update,
    handle_unified_search,
    handle_memory_manage,
    handle_memory_sync,
    set_dependencies,
)

# Other memory tools - RE-ENABLED
from .other_tools import (
    handle_memory_discover_associations,
    handle_memory_move,
    handle_session_manage,
)

# Prompt tools
from .prompt_tools import (
    handle_analyze_memories_prompt,
    handle_summarize_memory_prompt,
)
from .prompt_tools import set_dependencies as set_prompt_dependencies

# Resource tools
from .resource_tools import handle_memory_stats, handle_scope_memories
from .resource_tools import set_dependencies as set_resource_dependencies

# Scope management tools
from .scope_tools import handle_scope_list, handle_scope_suggest
from .scope_tools import set_dependencies as set_scope_dependencies

__all__ = [
    # Core handlers
    "set_dependencies",
    "set_scope_dependencies",
    "set_resource_dependencies",
    "set_prompt_dependencies",
    "ensure_initialized",
    "handle_memory_store",
    "handle_memory_search",
    "handle_diversified_search",
    "handle_memory_get",
    "handle_memory_delete",
    "handle_memory_update",
    "handle_unified_search",
    "handle_memory_manage",
    "handle_memory_sync",
    "handle_memory_import",
    "handle_memory_list_all",
    "handle_scope_list",
    "handle_scope_suggest",
    # Re-enabled handlers
    "handle_memory_export",
    "handle_memory_move",
    "handle_memory_discover_associations",
    "handle_session_manage",
    # Resource handlers
    "handle_memory_stats",
    "handle_scope_memories",
    # Prompt handlers
    "handle_analyze_memories_prompt",
    "handle_summarize_memory_prompt",
]
