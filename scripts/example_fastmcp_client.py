#!/usr/bin/env python3
"""
Example FastMCP client for connecting to the AssocMemoryServer
Based on the actual patterns used in your existing test scripts

FastMCP Client.__init__ Parameters:
- transport: Can be URL string, FastMCP server instance, transport dict, or MCPConfig
- roots: List of allowed root paths for file access (optional)
- timeout: Connection timeout in seconds (default 30.0)
- client_info: Dict with 'name' and 'version' keys for client identification

Common Transport Types:
1. HTTP URL: "http://localhost:8000/mcp"
2. STDIO dict: {"type": "stdio", "command": ["python", "-m", "server"], "cwd": "/path"}
3. Direct server instance: FastMCP app object
4. File path: Path to server executable
5. MCPConfig object: Full configuration

Your server supports:
- HTTP transport (when running with mcp.run(transport="http", port=8000))
- STDIO transport (when running with mcp.run(transport="stdio"))
"""

import asyncio
from fastmcp import Client
import json


async def test_http_client_connection():
    """Test connecting to the HTTP server using FastMCP client"""
    
    print("=== Testing HTTP FastMCP Client Connection ===")
    
    try:
        # Connect using HTTP endpoint (like your test scripts)
        async with Client("http://localhost:8000/mcp") as client:
            print("✅ Client connected successfully to HTTP endpoint!")
            
            # List available tools
            tools = await client.list_tools()
            print(f"\n📋 Available tools: {[tool.name for tool in tools]}")
            
            # Test memory_store tool with new scope system
            print("\n💾 Testing memory_store...")
            store_result = await client.call_tool("memory_store", {
                "request": {
                    "content": "Test memory from FastMCP HTTP client",
                    "scope": "client/http/test",
                    "metadata": {"client": "fastmcp", "transport": "http", "test": True}
                }
            })
            print(f"Store result: {store_result.content}")
            
            # Test memory_search tool
            print("\n🔍 Testing memory_search...")
            search_result = await client.call_tool("memory_search", {
                "request": {
                    "query": "Test memory",
                    "scope": "client",
                    "include_child_scopes": True,
                    "limit": 5
                }
            })
            print(f"Search result: {search_result.content}")
            
            # Test new scope_list tool
            print("\n📁 Testing scope_list...")
            scope_result = await client.call_tool("scope_list", {
                "request": {
                    "include_memory_counts": True
                }
            })
            print(f"Scope result: {scope_result.content}")
            
            # Test scope_suggest tool
            print("\n� Testing scope_suggest...")
            suggest_result = await client.call_tool("scope_suggest", {
                "request": {
                    "content": "Meeting notes from the weekly standup",
                    "current_scope": "work/meetings"
                }
            })
            print(f"Suggestion result: {suggest_result.content}")
            
            # Test memory_list_all with pagination
            print("\n📋 Testing memory_list_all with pagination...")
            list_result = await client.call_tool("memory_list_all", {
                "request": {
                    "page": 1,
                    "per_page": 5
                }
            })
            print(f"List result: {list_result.content}")
            
            # List resources
            print("\n📄 Testing resources...")
            resources = await client.list_resources()
            print(f"Available resources: {[resource.uri for resource in resources]}")
            
            # Get memory stats resource
            if resources:
                print("\n📊 Testing memory stats resource...")
                stats_resource = await client.read_resource("memory://stats")
                print(f"Memory stats: {stats_resource[0] if stats_resource else 'No content'}")
        
    except Exception as e:
        print(f"❌ HTTP Client error: {e}")
        import traceback
        traceback.print_exc()


async def test_stdio_client_connection():
    """Test connecting via STDIO transport (like VSCode integration)"""
    
    print("\n=== Testing STDIO FastMCP Client Connection ===")
    
    # This follows the pattern from your new scope tools test
    transport = {
        "type": "stdio",
        "command": ["python", "-m", "src.mcp_assoc_memory.server"],
        "cwd": "/workspaces/mcp-assoc-memory"
    }
    
    try:
        async with Client(transport) as client:
            print("✅ STDIO Client connected successfully!")
            
            # Test basic functionality
            tools = await client.list_tools()
            print(f"📋 Available tools via STDIO: {[tool.name for tool in tools]}")
            
            # Store a memory via STDIO
            store_result = await client.call_tool("memory_store", {
                "request": {
                    "content": "STDIO transport test memory",
                    "scope": "client/stdio/test",
                    "metadata": {"transport": "stdio"}
                }
            })
            print("💾 STDIO store successful")
            
            # Test session management
            session_result = await client.call_tool("session_manage", {
                "request": {
                    "action": "create",
                    "session_id": "fastmcp-client-test"
                }
            })
            print("🔄 Session management test successful")
            
    except Exception as e:
        print(f"❌ STDIO Client error: {e}")
        import traceback
        traceback.print_exc()


async def demonstrate_client_patterns():
    """Demonstrate different client usage patterns"""
    
    print("\n=== FastMCP Client Usage Patterns ===")
    
    # Pattern 1: Basic tool call with structured request
    print("\n📌 Pattern 1: Structured Request")
    async with Client("http://localhost:8000/mcp") as client:
        result = await client.call_tool("memory_store", {
            "request": {
                "content": "Example structured request",
                "scope": "examples/patterns",
                "metadata": {"pattern": "structured"}
            }
        })
        print(f"   Result type: {type(result)}")
        print(f"   Content preview: {str(result.content)[:100]}...")
    
    # Pattern 2: Resource reading
    print("\n📌 Pattern 2: Resource Reading")
    async with Client("http://localhost:8000/mcp") as client:
        stats = await client.read_resource("memory://stats")
        print(f"   Resource type: {type(stats)}")
        print(f"   Content preview: {str(stats[0] if stats else 'No content')[:100]}...")
    
    # Pattern 3: Prompt usage
    print("\n📌 Pattern 3: Prompt Usage")
    async with Client("http://localhost:8000/mcp") as client:
        # First get a memory to analyze
        memories = await client.call_tool("memory_list_all", {
            "request": {"page": 1, "per_page": 1}
        })
        
        prompt = await client.get_prompt("analyze_memories", {
            "scope": "examples"
        })
        print(f"   Prompt messages: {len(prompt.messages)}")
        # Handle different content types safely
        first_content = prompt.messages[0].content if prompt.messages else None
        if first_content:
            content_text = getattr(first_content, 'text', str(first_content))
            print(f"   First message preview: {content_text[:100]}...")
        else:
            print("   No messages available")


if __name__ == "__main__":
    print("🚀 FastMCP Client Examples and Patterns")
    print("Demonstrating various ways to connect to AssocMemoryServer...")
    
    # Run different connection tests
    asyncio.run(test_http_client_connection())
    asyncio.run(test_stdio_client_connection())
    asyncio.run(demonstrate_client_patterns())
    
    print("\n✨ Client examples completed!")
    print("\n📚 Key Takeaways:")
    print("   - Use 'request' parameter for tool calls")
    print("   - HTTP transport: 'http://localhost:8000/mcp'")
    print("   - STDIO transport: transport dict with command")
    print("   - All tools use structured request/response format")
    print("   - New scope system replaces old domain system")


if __name__ == "__main__":
    print("🚀 FastMCP Client Examples and Patterns")
    print("Demonstrating various ways to connect to AssocMemoryServer...")
    
    # Run different connection tests
    asyncio.run(test_http_client_connection())
    asyncio.run(test_stdio_client_connection())
    asyncio.run(demonstrate_client_patterns())
    
    print("\n✨ Client examples completed!")
    print("\n📚 Key Takeaways:")
    print("   - Use 'request' parameter for tool calls")
    print("   - HTTP transport: 'http://localhost:8000/mcp'")
    print("   - STDIO transport: transport dict with command")
    print("   - All tools use structured request/response format")
    print("   - New scope system replaces old domain system")
