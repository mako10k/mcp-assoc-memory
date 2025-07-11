"""Tool handlers for MCP associative memory server."""

# Memory management tools
from .memory_tools import (
    set_dependencies,
    ensure_initialized,
    handle_memory_store,
    handle_memory_search,
    handle_diversified_search,
    handle_memory_get,
    handle_memory_delete,
    handle_memory_update,
    handle_memory_discover_associations,
    handle_memory_import,
    handle_memory_list_all
)

# Scope management tools
from .scope_tools import (
    set_dependencies as set_scope_dependencies,
    handle_scope_list,
    handle_scope_suggest
)

# Export/import tools - RE-ENABLED
from .export_tools import (
    handle_memory_export,
    handle_memory_import
)

# Other memory tools - RE-ENABLED  
from .other_tools import (
    handle_memory_move,
    handle_memory_discover_associations,
    handle_session_manage
)

# Resource tools
from .resource_tools import (
    set_dependencies as set_resource_dependencies,
    handle_memory_stats,
    handle_scope_memories
)

# Prompt tools
from .prompt_tools import (
    set_dependencies as set_prompt_dependencies,
    handle_analyze_memories_prompt,
    handle_summarize_memory_prompt
)

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
    "handle_summarize_memory_prompt"
]
