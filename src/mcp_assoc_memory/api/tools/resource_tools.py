"""
Resource handlers for MCP Associative Memory Server
"""

from typing import Any, Dict, Optional
from fastmcp import Context
from ...core.memory_manager import MemoryManager
from ..utils import get_child_scopes

# Global references (will be set by server.py)
memory_manager: Optional[MemoryManager] = None
memory_storage: Optional[Dict[str, Any]] = None
persistence = None


def set_dependencies(mm: MemoryManager, ms: Dict[str, Any], p: Any) -> None:
    """Set global dependencies from server.py"""
    global memory_manager, memory_storage, persistence
    memory_manager = mm
    memory_storage = ms
    persistence = p


async def handle_memory_stats(ctx: Context) -> dict:
    """Provide memory statistics resource"""
    if ctx:
        await ctx.info("Generating memory statistics...")

    stats = {"total_memories": len(memory_storage), "scopes": {}, "active_sessions": [], "recent_memories": []}

    # Scope-wise statistics and hierarchy detection
    scope_counts: Dict[str, int] = {}
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
            "last_updated": last_updated.isoformat() if last_updated else None,
        }

    stats["active_sessions"] = list(session_scopes)

    # Latest 5 memories
    sorted_memories = sorted(memory_storage.values(), key=lambda x: x["created_at"], reverse=True)[:5]

    stats["recent_memories"] = [
        {"memory_id": m["memory_id"], "content": m["content"][:50] + "...", "scope": m["scope"]}
        for m in sorted_memories
    ]

    return stats


async def handle_scope_memories(scope: str, ctx: Context) -> dict:
    """Provide memory list for specified scope resource"""
    if ctx:
        await ctx.info(f"Retrieving memories for scope '{scope}'...")

    scope_memories = [memory_data for memory_data in memory_storage.values() if memory_data["scope"] == scope]

    result = {
        "scope": scope,
        "count": len(scope_memories),
        "memories": [
            {"memory_id": m["memory_id"], "content": m["content"], "created_at": m["created_at"]}
            for m in scope_memories
        ],
    }

    return result
