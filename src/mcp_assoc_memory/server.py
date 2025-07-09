"""
FastMCP-compliant memory management server implementation
"""

from typing import Any, Dict, List, Optional, Annotated
from fastmcp import FastMCP, Context
from pydantic import Field, BaseModel
from datetime import datetime
import logging
import uuid

logger = logging.getLogger(__name__)

# FastMCP server instance
mcp = FastMCP(name="AssocMemoryServer")

# Simple memory storage (stub for actual implementation)
memory_storage = {}


# Pydantic model definitions
class MemoryStoreRequest(BaseModel):
    content: str = Field(description="Memory content to store")
    scope: str = Field(default="user/default", description="Memory scope (hierarchical path)")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")


class MemoryResponse(BaseModel):
    memory_id: str
    content: str
    scope: str
    metadata: Dict[str, Any]
    created_at: datetime


class MemorySearchRequest(BaseModel):
    query: str = Field(description="Search query")
    scope: Optional[str] = Field(default=None, description="Target scope for search (supports hierarchy)")
    include_child_scopes: bool = Field(default=False, description="Include child scopes in search")
    limit: int = Field(default=10, ge=1, le=100, description="Maximum number of results")


class ScopeListRequest(BaseModel):
    parent_scope: Optional[str] = Field(default=None, description="Parent scope to list children from")
    include_memory_counts: bool = Field(default=True, description="Include memory counts for each scope")


class ScopeSuggestRequest(BaseModel):
    content: str = Field(description="Content to suggest scope for")
    current_scope: Optional[str] = Field(default=None, description="Current scope for context")


class MemoryMoveRequest(BaseModel):
    memory_ids: List[str] = Field(description="List of memory IDs to move")
    target_scope: str = Field(description="Target scope to move memories to")


class SessionManageRequest(BaseModel):
    action: str = Field(description="Session action: 'create', 'list', 'cleanup', 'archive'")
    session_id: Optional[str] = Field(default=None, description="Session ID for specific actions")
    max_age_days: Optional[int] = Field(default=7, description="Maximum age for cleanup operations")


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


# Memory management tools
@mcp.tool(
    name="memory_store",
    description="Store a new memory",
    annotations={
        "title": "Store Memory",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False
    }
)
async def memory_store(
    request: MemoryStoreRequest,
    ctx: Context
) -> MemoryResponse:
    """Store a memory"""
    try:
        await ctx.info(f"Storing memory in scope '{request.scope}': {request.content[:50]}...")
        
        # Store memory
        memory_id = str(uuid.uuid4())
        memory_data = {
            "memory_id": memory_id,
            "content": request.content,
            "scope": request.scope,
            "metadata": request.metadata or {},
            "created_at": datetime.now()
        }
        
        memory_storage[memory_id] = memory_data
        
        await ctx.info(f"Memory stored: {memory_id}")
        
        return MemoryResponse(**memory_data)
        
    except Exception as e:
        await ctx.error(f"Failed to store memory: {e}")
        raise


@mcp.tool(
    name="memory_search",
    description="Search memories using similarity-based search",
    annotations={
        "title": "Search Memories",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True
    }
)
async def memory_search(
    request: MemorySearchRequest,
    ctx: Context
) -> List[MemoryResponse]:
    """Search memories with scope support"""
    try:
        scope_info = f" in scope '{request.scope}'" if request.scope else ""
        child_info = " (including child scopes)" if request.include_child_scopes else ""
        await ctx.info(f"Searching memories: '{request.query}'{scope_info}{child_info}")
        
        # Search implementation with scope filtering
        results = []
        for memory_data in memory_storage.values():
            # Scope filtering
            if request.scope:
                memory_scope = memory_data["scope"]
                if request.include_child_scopes:
                    # Include if memory scope starts with request scope (hierarchical match)
                    if not (memory_scope == request.scope or memory_scope.startswith(request.scope + "/")):
                        continue
                else:
                    # Exact scope match only
                    if memory_scope != request.scope:
                        continue
            
            # Content search (simple text matching - will be enhanced with embeddings later)
            if request.query.lower() in memory_data["content"].lower():
                results.append(MemoryResponse(**memory_data))
                if len(results) >= request.limit:
                    break
        
        await ctx.info(f"Found {len(results)} memories")
        return results
        
    except Exception as e:
        await ctx.error(f"Failed to search memories: {e}")
        raise


@mcp.tool(
    name="memory_get",
    description="Retrieve a memory by its ID",
    annotations={
        "title": "Get Memory",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True
    }
)
async def memory_get(
    memory_id: Annotated[str, Field(description="Memory ID")],
    ctx: Context
) -> Optional[MemoryResponse]:
    """Retrieve a memory"""
    try:
        await ctx.info(f"Retrieving memory: {memory_id}")
        
        memory_data = memory_storage.get(memory_id)
        
        if not memory_data:
            await ctx.warning(f"Memory not found: {memory_id}")
            return None
            
        await ctx.info(f"Memory retrieved: {memory_id}")
        
        return MemoryResponse(**memory_data)
        
    except Exception as e:
        await ctx.error(f"Failed to retrieve memory: {e}")
        raise


@mcp.tool(
    name="memory_delete",
    description="Delete a specified memory",
    annotations={
        "title": "Delete Memory",
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
            await ctx.info(f"Memory deleted: {memory_id}")
            return {"success": True, "message": "Memory deleted successfully", "memory_id": memory_id}
        else:
            await ctx.warning(f"Memory not found: {memory_id}")
            return {"success": False, "message": "Memory not found", "memory_id": memory_id}
        
    except Exception as e:
        await ctx.error(f"Failed to delete memory: {e}")
        raise


@mcp.tool(
    name="memory_list_all",
    description="List all memories (for debugging purposes)",
    annotations={
        "title": "List All Memories",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True
    }
)
async def memory_list_all(ctx: Context) -> List[MemoryResponse]:
    """List all memories (for debugging)"""
    try:
        await ctx.info("Retrieving all memories...")
        
        results = [MemoryResponse(**memory_data) for memory_data in memory_storage.values()]
        
        await ctx.info(f"Retrieved {len(results)} memories")
        
        return results
        
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
    # Run with stdio transport for better MCP client compatibility
    mcp.run(transport="stdio")
