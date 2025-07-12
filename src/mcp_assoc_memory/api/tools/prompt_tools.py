"""
Prompt handlers for MCP Associative Memory Server
"""

from typing import Any, Dict, Optional
from fastmcp import Context

# Global references (will be set by server.py)
memory_manager: Optional[Any] = None
memory_storage: Optional[Dict[str, Any]] = None
persistence = None


def set_dependencies(mm: Any, ms: Dict[str, Any], p: Any) -> None:
    """Set global dependencies from server.py"""
    global memory_manager, memory_storage, persistence
    memory_manager = mm
    memory_storage = ms
    persistence = p


async def handle_analyze_memories_prompt(
    scope: str = "user/default",
    include_child_scopes: bool = True,
    ctx: Optional[Context] = None
) -> str:
    """Generate memory analysis prompt"""
    if ctx:
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


async def handle_summarize_memory_prompt(
    memory_id: str,
    context_scope: str = "",
    ctx: Optional[Context] = None
) -> str:
    """Generate memory summary prompt"""
    if ctx:
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
