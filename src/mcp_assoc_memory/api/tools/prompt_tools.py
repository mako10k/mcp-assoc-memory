"""
Prompt generation tools for MCP Associative Memory Server
"""

from typing import Any, Dict, List, Optional

from fastmcp import Context

from ...core.singleton_memory_manager import get_memory_manager

# Module-level dependencies (for backward compatibility)
memory_manager: Optional[Any] = None
memory_storage: Optional[Dict[str, Any]] = None
persistence = None


def set_dependencies(mm: Any, ms: Dict[str, Any], p: Any) -> None:
    """Set global dependencies from server.py (backward compatibility)"""
    global memory_manager, memory_storage, persistence
    memory_manager = mm
    memory_storage = ms
    persistence = p


async def handle_analyze_memories_prompt(
    scope: str = "user/default", include_child_scopes: bool = True, ctx: Optional[Context] = None
) -> str:
    """Generate memory analysis prompt"""
    if ctx:
        await ctx.info(f"Generating analysis prompt for scope '{scope}'...")

    # Use Singleton memory manager with fallback
    manager = await get_memory_manager()
    if not manager:
        # Fallback to module-level memory_storage if available
        if not memory_storage:
            raise ValueError("No memory manager or storage available")

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
    else:
        # Use Singleton memory manager
        try:
            # Get memories from the metadata store via scope
            if include_child_scopes:
                # Use search to get all memories and filter
                all_memories = await manager.search_memories("", scope=scope, limit=1000, min_score=0.0)
                scope_memories = []
                for memory in all_memories:
                    memory_scope = memory.get("scope", "")
                    if memory_scope == scope or memory_scope.startswith(scope + "/"):
                        scope_memories.append(memory)
            else:
                # Direct scope query
                memories = await manager.metadata_store.get_memories_by_scope(scope)
                scope_memories = []
                for memory in memories:
                    scope_memories.append(
                        {
                            "id": memory.id,
                            "content": memory.content,
                            "scope": memory.scope,
                            "category": memory.category,
                            "tags": memory.tags,
                            "created_at": memory.created_at,
                            "metadata": memory.metadata,
                        }
                    )
        except Exception as e:
            if ctx:
                await ctx.error(f"Failed to retrieve memories from manager: {e}")
            raise ValueError(f"Failed to retrieve memories: {e}")

    memories_text = "\n".join([f"- [{m['scope']}] {m['content']}" for m in scope_memories[:10]])  # Maximum 10 memories

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


async def handle_summarize_memory_prompt(memory_id: str, context_scope: str = "", ctx: Optional[Context] = None) -> str:
    """Generate memory summary prompt"""
    if ctx:
        await ctx.info(f"Generating summary prompt for memory '{memory_id}'...")

    # Use Singleton memory manager with fallback
    manager = await get_memory_manager()
    if not manager:
        # Fallback to module-level memory_storage if available
        if not memory_storage:
            raise ValueError("No memory manager or storage available")

        memory_data = memory_storage.get(memory_id)
        if not memory_data:
            raise ValueError(f"Memory not found: {memory_id}")
    else:
        # Use Singleton memory manager
        try:
            memory = await manager.get_memory(memory_id)
            if not memory:
                raise ValueError(f"Memory not found: {memory_id}")

            memory_data = {
                "memory_id": memory.id,
                "scope": memory.scope,
                "created_at": memory.created_at,
                "content": memory.content,
                "metadata": memory.metadata,
            }
        except Exception as e:
            if ctx:
                await ctx.error(f"Failed to retrieve memory: {e}")
            raise ValueError(f"Failed to retrieve memory: {e}")

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
