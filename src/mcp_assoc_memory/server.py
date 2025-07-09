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
class MemoryCreateRequest(BaseModel):
    content: str = Field(description="Memory content")
    domain: str = Field(default="user", description="Memory domain")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")


class MemoryResponse(BaseModel):
    memory_id: str
    content: str
    domain: str
    metadata: Dict[str, Any]
    created_at: datetime


class MemorySearchRequest(BaseModel):
    query: str = Field(description="Search query")
    domain: Optional[str] = Field(default=None, description="Target domain for search")
    limit: int = Field(default=10, ge=1, le=100, description="Maximum number of results")


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
    request: MemoryCreateRequest,
    ctx: Context
) -> MemoryResponse:
    """Store a memory"""
    try:
        await ctx.info(f"Storing memory: {request.content[:50]}...")
        
        # Store memory
        memory_id = str(uuid.uuid4())
        memory_data = {
            "memory_id": memory_id,
            "content": request.content,
            "domain": request.domain,
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
    """Search memories"""
    try:
        await ctx.info(f"Searching memories: {request.query}")
        
        # Simple search implementation (actual implementation would use embedding-based similarity search)
        results = []
        for memory_data in memory_storage.values():
            if request.domain and memory_data["domain"] != request.domain:
                continue
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
        "domains": {},
        "recent_memories": []
    }
    
    # Domain-wise statistics
    for memory_data in memory_storage.values():
        domain = memory_data["domain"]
        stats["domains"][domain] = stats["domains"].get(domain, 0) + 1
    
    # Latest 5 memories
    sorted_memories = sorted(
        memory_storage.values(),
        key=lambda x: x["created_at"],
        reverse=True
    )[:5]
    
    stats["recent_memories"] = [
        {"memory_id": m["memory_id"], "content": m["content"][:50] + "..."}
        for m in sorted_memories
    ]
    
    return stats


@mcp.resource("memory://domain/{domain}")
async def get_domain_memories(domain: str, ctx: Context) -> dict:
    """Provide memory list for specified domain resource"""
    await ctx.info(f"Retrieving memories for domain '{domain}'...")
    
    domain_memories = [
        memory_data for memory_data in memory_storage.values()
        if memory_data["domain"] == domain
    ]
    
    result = {
        "domain": domain,
        "count": len(domain_memories),
        "memories": [
            {
                "memory_id": m["memory_id"],
                "content": m["content"],
                "created_at": m["created_at"]
            }
            for m in domain_memories
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
    domain: Annotated[str, Field(default="user", description="Target domain for analysis")] = "user"
) -> str:
    """Generate memory analysis prompt"""
    await ctx.info(f"Generating analysis prompt for domain '{domain}'...")
    
    domain_memories = [
        memory_data for memory_data in memory_storage.values()
        if memory_data["domain"] == domain
    ]
    
    memories_text = "\n".join([
        f"- {m['content']}" for m in domain_memories[:10]  # Maximum 10 memories
    ])
    
    prompt = f"""The following memories are stored in the "{domain}" domain:

{memories_text}

Please analyze these memories and provide insights on the following aspects:
1. Main themes and patterns
2. Important keywords
3. Relationships between memories
4. Recommendations for future memory management

Please provide the analysis in a structured format."""

    return prompt


@mcp.prompt(
    name="summarize_memory",
    description="Generate prompts for summarizing specific memories"
)
async def summarize_memory_prompt(
    memory_id: Annotated[str, Field(description="ID of the memory to summarize")],
    ctx: Context
) -> str:
    """Generate memory summary prompt"""
    await ctx.info(f"Generating summary prompt for memory '{memory_id}'...")
    
    memory_data = memory_storage.get(memory_id)
    if not memory_data:
        raise ValueError(f"Memory not found: {memory_id}")
    
    prompt = f"""Please summarize the following memory:

Memory ID: {memory_data['memory_id']}
Domain: {memory_data['domain']}
Created: {memory_data['created_at']}
Content: {memory_data['content']}
Metadata: {memory_data['metadata']}

Please provide the summary in the following format:
- Key Points: [Main points]
- Keywords: [Important keywords]
- Category: [Appropriate category]
- Relationships: [Potential relationships with other memories]"""

    return prompt


if __name__ == "__main__":
    mcp.run(transport="http", host="127.0.0.1", port=8000, path="/mcp")
