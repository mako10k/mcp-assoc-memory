# FastMCP Client Usage with AssocMemoryServer

## Client Initialization

Based on the FastMCP Client `__init__` signature you shared, here are the key parameters and usage patterns for connecting to your AssocMemoryServer:

### Constructor Parameters

```python
class Client:
    def __init__(
        self,
        transport: str | FastMCP | dict | Path | MCPConfig,
        *,
        roots: list[str] | None = None,
        timeout: float = 30.0,
        client_info: dict[str, str] | None = None
    ):
```

## Transport Options

### 1. HTTP URL String
```python
from fastmcp import Client

async with Client("http://localhost:8000/mcp") as client:
    result = await client.call_tool("memory_store", {
        "request": {
            "content": "Test memory",
            "scope": "user/default"
        }
    })
```

### 2. STDIO Transport Dictionary
```python
transport = {
    "type": "stdio",
    "command": ["python", "-m", "src.mcp_assoc_memory.server"],
    "cwd": "/workspaces/mcp-assoc-memory"
}

async with Client(transport) as client:
    tools = await client.list_tools()
```

### 3. Direct Server Instance
```python
from mcp_assoc_memory.server import mcp

async with Client(mcp) as client:
    result = await client.call_tool("memory_search", {
        "request": {
            "query": "search term",
            "scope": "work/projects",
            "limit": 5
        }
    })
```

### 4. File Path to Server
```python
from pathlib import Path

server_path = Path("/workspaces/mcp-assoc-memory/src/mcp_assoc_memory/server.py")
async with Client(server_path) as client:
    # Use client...
```

### 5. With Additional Options
```python
client = Client(
    transport="http://localhost:8000/mcp",
    timeout=60.0,
    client_info={
        "name": "my-memory-client",
        "version": "1.0.0"
    },
    roots=["/workspaces/mcp-assoc-memory"]  # For file access if needed
)
```

## Key Usage Patterns

### Tool Calls with Request Structure
All your tools use the `request` parameter pattern:

```python
# Memory storage
await client.call_tool("memory_store", {
    "request": {
        "content": "Meeting notes",
        "scope": "work/meetings/weekly",
        "metadata": {"date": "2024-01-15"}
    }
})

# Memory search with scope hierarchy
await client.call_tool("memory_search", {
    "request": {
        "query": "project status",
        "scope": "work",
        "include_child_scopes": True,
        "limit": 10
    }
})

# Scope management
await client.call_tool("scope_list", {
    "request": {
        "include_memory_counts": True
    }
})
```

### Resource Access
```python
# List available resources
resources = await client.list_resources()

# Read memory statistics
stats = await client.read_resource("memory://stats")
```

### Prompt Usage
```python
# Get analysis prompt for a scope
prompt = await client.get_prompt("analyze_memories", {
    "scope": "work/projects"
})
```

## Server Configuration

### HTTP Mode (for testing)
Your `__main__.py` currently runs:
```python
mcp.run(transport="http", port=8000)
```

### STDIO Mode (for VSCode MCP integration)
Update `__main__.py` to:
```python
mcp.run(transport="stdio")
```

## New Features in Your Implementation

### Hierarchical Scopes
- `user/default` (default scope)
- `work/projects/alpha` (nested scopes)
- `personal/notes/2024` (deep hierarchy)
- Support for Unicode: `プロジェクト/会議`

### Scope Management Tools
```python
# Get scope suggestions
await client.call_tool("scope_suggest", {
    "request": {
        "content": "Meeting notes from standup",
        "current_scope": "work/meetings"
    }
})

# Move memories between scopes
await client.call_tool("memory_move", {
    "request": {
        "memory_ids": ["mem1", "mem2"],
        "target_scope": "archive/old-projects"
    }
})

# Session management
await client.call_tool("session_manage", {
    "request": {
        "action": "create",
        "session_id": "user-session-123"
    }
})
```

### Pagination Support
```python
# List with pagination
await client.call_tool("memory_list_all", {
    "request": {
        "page": 1,
        "per_page": 20
    }
})
```

## Error Handling

```python
try:
    async with Client("http://localhost:8000/mcp") as client:
        result = await client.call_tool("memory_store", {
            "request": {"content": "test"}
        })
except RuntimeError as e:
    print(f"Connection failed: {e}")
except Exception as e:
    print(f"Tool call failed: {e}")
```

## Complete Example

```python
import asyncio
from fastmcp import Client

async def demo_memory_workflow():
    """Complete workflow demonstrating all features"""
    
    # Connect using HTTP (ensure server is running)
    async with Client("http://localhost:8000/mcp") as client:
        
        # 1. List available tools
        tools = await client.list_tools()
        print(f"Available tools: {[t.name for t in tools]}")
        
        # 2. Store memories in different scopes
        memories = [
            {"content": "Project kickoff", "scope": "work/projects/alpha"},
            {"content": "Personal notes", "scope": "personal/diary"},
            {"content": "Study materials", "scope": "education/courses"}
        ]
        
        for memory in memories:
            await client.call_tool("memory_store", {"request": memory})
        
        # 3. Search with scope hierarchy
        results = await client.call_tool("memory_search", {
            "request": {
                "query": "project",
                "scope": "work",
                "include_child_scopes": True
            }
        })
        
        # 4. Get scope overview
        scopes = await client.call_tool("scope_list", {
            "request": {"include_memory_counts": True}
        })
        
        # 5. Check statistics
        stats = await client.read_resource("memory://stats")
        
        return {
            "tools": len(tools),
            "results": results,
            "scopes": scopes,
            "stats": stats
        }

if __name__ == "__main__":
    # Make sure server is running: python -m src.mcp_assoc_memory
    result = asyncio.run(demo_memory_workflow())
    print("Demo completed successfully!")
```

## VSCode Integration

For VSCode MCP client integration, your `.vscode/mcp.json` should use STDIO:

```json
{
  "mcpServers": {
    "mcp-assoc-memory": {
      "command": "python",
      "args": ["-m", "src.mcp_assoc_memory.server"],
      "cwd": "/workspaces/mcp-assoc-memory"
    }
  }
}
```

And update your server to run in STDIO mode for VSCode compatibility.
