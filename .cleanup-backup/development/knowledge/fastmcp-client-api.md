# FastMCP 2.0 Client API Documentation

## Overview
FastMCP 2.0 provides a `Client` class for connecting to MCP servers. The client supports various transports and can auto-detect the correct one.

## Basic Usage

### Import
```python
from fastmcp import Client
```

### Connection Methods

#### 1. Direct Server Instance (In-Memory Transport)
Best for testing - connects directly to a FastMCP server instance:
```python
from fastmcp import FastMCP, Client

mcp = FastMCP("My MCP Server")

async def main():
    async with Client(mcp) as client:
        tools = await client.list_tools()
        result = await client.call_tool("tool_name", {"param": "value"})
```

#### 2. SSE (Server-Sent Events)
For web deployments:
```python
async with Client("http://localhost:8000/sse") as client:
    # use the client
    pass
```

#### 3. STDIO
For local scripts:
```python
async with Client("my_server.py") as client:
    tools = await client.list_tools()
    result = await client.call_tool("add", {"a": 5, "b": 3})
```

#### 4. Multiple Servers
Using standard MCP configuration format:
```python
config = {
    "mcpServers": {
        "weather": {"url": "https://weather-api.example.com/mcp"},
        "assistant": {"command": "python", "args": ["./assistant_server.py"]}
    }
}

client = Client(config)
async with client:
    # Access tools with server prefixes
    forecast = await client.call_tool("weather_get_forecast", {"city": "London"})
    answer = await client.call_tool("assistant_answer_question", {"query": "What is MCP?"})
```

## Client Methods

Based on the API inspection, available methods include:

- `list_tools()` - List available tools
- `call_tool(name, params)` - Call a specific tool
- `list_resources()` - List available resources
- `read_resource(uri)` - Read a specific resource
- `list_prompts()` - List available prompts
- `get_prompt(name, params)` - Get a specific prompt
- `ping()` - Test connection
- `is_connected` - Check connection status

## Important Notes

1. **Context Manager**: Always use `async with` for proper resource cleanup
2. **Auto-detection**: Client often auto-detects the correct transport
3. **Testing**: In-memory transport (direct server instance) is recommended for testing
4. **No Network Calls**: In-memory testing eliminates process management or network calls

## Version Information
- FastMCP version: 2.10.4
- MCP version: 1.10.1
- Last updated: 2025-01-10

## Sources
- https://github.com/jlowin/fastmcp
- https://gofastmcp.com/clients/client
- https://gofastmcp.com/clients/transports
