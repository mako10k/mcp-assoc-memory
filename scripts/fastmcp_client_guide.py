#!/usr/bin/env python3
"""
Simple FastMCP Client Usage Examples
Demonstrates how to use the FastMCP Client class with your AssocMemoryServer

This shows the correct patterns based on your existing test scripts and the
FastMCP Client.__init__ signature you shared.
"""

import asyncio
from fastmcp import Client


def explain_client_initialization():
    """Explain FastMCP Client initialization options"""
    
    print("🔧 FastMCP Client Initialization Options")
    print("=" * 50)
    
    print("\n1. HTTP Transport (URL string):")
    print("   client = Client('http://localhost:8000/mcp')")
    
    print("\n2. STDIO Transport (dict config):")
    print("   transport = {")
    print("       'type': 'stdio',")
    print("       'command': ['python', '-m', 'src.mcp_assoc_memory.server'],")
    print("       'cwd': '/workspaces/mcp-assoc-memory'")
    print("   }")
    print("   client = Client(transport)")
    
    print("\n3. Direct Server Instance:")
    print("   from mcp_assoc_memory.server import mcp")
    print("   client = Client(mcp)")
    
    print("\n4. With Additional Options:")
    print("   client = Client(")
    print("       transport='http://localhost:8000/mcp',")
    print("       timeout=30.0,")
    print("       client_info={'name': 'my-client', 'version': '1.0.0'}")
    print("   )")


async def demonstrate_usage_patterns():
    """Show usage patterns without actually connecting"""
    
    print("\n\n🔍 FastMCP Usage Patterns")
    print("=" * 50)
    
    print("\n📋 Pattern 1: Tool Calls with Request Parameter")
    print("```python")
    print("async with Client('http://localhost:8000/mcp') as client:")
    print("    result = await client.call_tool('memory_store', {")
    print("        'request': {")
    print("            'content': 'My memory content',")
    print("            'scope': 'user/notes',")
    print("            'metadata': {'category': 'personal'}")
    print("        }")
    print("    })")
    print("```")
    
    print("\n🔍 Pattern 2: Search with Scope Hierarchy")
    print("```python")
    print("result = await client.call_tool('memory_search', {")
    print("    'request': {")
    print("        'query': 'search term',")
    print("        'scope': 'work/projects',")
    print("        'include_child_scopes': True,")
    print("        'limit': 10")
    print("    }")
    print("})")
    print("```")
    
    print("\n📊 Pattern 3: Resources and Prompts")
    print("```python")
    print("# List resources")
    print("resources = await client.list_resources()")
    print("")
    print("# Read resource")
    print("stats = await client.read_resource('memory://stats')")
    print("")
    print("# Get prompt")
    print("prompt = await client.get_prompt('analyze_memories', {")
    print("    'scope': 'work/projects'")
    print("})")
    print("```")
    
    print("\n📄 Pattern 4: Pagination with List Tools")
    print("```python")
    print("result = await client.call_tool('memory_list_all', {")
    print("    'request': {")
    print("        'page': 1,")
    print("        'per_page': 20")
    print("    }")
    print("})")
    print("```")
    
    print("\n🔧 Pattern 5: New Scope Management Tools")
    print("```python")
    print("# List available scopes")
    print("scopes = await client.call_tool('scope_list', {")
    print("    'request': {'include_memory_counts': True}")
    print("})")
    print("")
    print("# Get scope suggestions")
    print("suggestion = await client.call_tool('scope_suggest', {")
    print("    'request': {")
    print("        'content': 'Meeting notes from standup',")
    print("        'current_scope': 'work/meetings'")
    print("    }")
    print("})")
    print("")
    print("# Move memories between scopes")
    print("move_result = await client.call_tool('memory_move', {")
    print("    'request': {")
    print("        'memory_ids': ['mem1', 'mem2'],")
    print("        'target_scope': 'archive/old-projects'")
    print("    }")
    print("})")
    print("```")


def show_server_startup_options():
    """Show how to start the server in different modes"""
    
    print("\n\n🚀 Server Startup Options")
    print("=" * 50)
    
    print("\n1. HTTP Mode (for Client testing):")
    print("   cd /workspaces/mcp-assoc-memory")
    print("   python -m src.mcp_assoc_memory")
    print("   # Server runs on http://localhost:8000/mcp")
    
    print("\n2. STDIO Mode (for VSCode MCP integration):")
    print("   # Update __main__.py to use:")
    print("   mcp.run(transport='stdio')")
    
    print("\n3. Custom Port:")
    print("   # Update __main__.py to use:")
    print("   mcp.run(transport='http', port=3000)")


def show_key_differences():
    """Show key differences from legacy MCP"""
    
    print("\n\n✨ Key Differences from Legacy MCP")
    print("=" * 50)
    
    print("\n🔄 Request Structure:")
    print("   OLD: await client.call_tool('memory_store', content='...', domain='user')")
    print("   NEW: await client.call_tool('memory_store', {'request': {'content': '...', 'scope': 'user/default'}})")
    
    print("\n🗂️ Scope System:")
    print("   OLD: domain='user'")
    print("   NEW: scope='user/projects/alpha' (hierarchical)")
    
    print("\n📊 Tool Organization:")
    print("   OLD: Single 'memory' tool with action parameter")
    print("   NEW: Separate tools: memory_store, memory_search, memory_get, etc.")
    
    print("\n📋 Response Format:")
    print("   OLD: Direct JSON response")
    print("   NEW: Structured response with .content attribute")
    
    print("\n🔧 New Features:")
    print("   - Pagination (memory_list_all)")
    print("   - Scope management (scope_list, scope_suggest, memory_move)")
    print("   - Session management (session_manage)")
    print("   - Unicode scope support")
    print("   - Hierarchical scope inheritance")


async def practical_example():
    """Show a practical example flow"""
    
    print("\n\n📝 Practical Example: Complete Workflow")
    print("=" * 50)
    
    print("""
```python
async def complete_memory_workflow():
    async with Client('http://localhost:8000/mcp') as client:
        
        # 1. Store some memories
        memories = [
            {'content': 'Project Alpha kickoff notes', 'scope': 'work/projects/alpha'},
            {'content': 'Code review feedback', 'scope': 'work/development'},
            {'content': 'Meeting with client', 'scope': 'work/meetings'}
        ]
        
        stored_ids = []
        for memory in memories:
            result = await client.call_tool('memory_store', {'request': memory})
            # Extract memory_id from response
            stored_ids.append(result.content)  # Handle actual response format
        
        # 2. Search across work scope
        search_results = await client.call_tool('memory_search', {
            'request': {
                'query': 'project',
                'scope': 'work',
                'include_child_scopes': True,
                'limit': 10
            }
        })
        
        # 3. List all scopes to see organization
        scopes = await client.call_tool('scope_list', {
            'request': {'include_memory_counts': True}
        })
        
        # 4. Get suggestions for new content
        suggestion = await client.call_tool('scope_suggest', {
            'request': {
                'content': 'Follow-up tasks from the project review',
                'current_scope': 'work/projects/alpha'
            }
        })
        
        # 5. Archive old memories
        await client.call_tool('memory_move', {
            'request': {
                'memory_ids': stored_ids[:1],  # Move first memory
                'target_scope': 'archive/completed-projects'
            }
        })
        
        # 6. Get analytics
        stats = await client.read_resource('memory://stats')
        
        return {
            'stored': len(stored_ids),
            'search_results': search_results,
            'scopes': scopes,
            'suggestion': suggestion,
            'stats': stats
        }
```
""")


if __name__ == "__main__":
    print("🎯 FastMCP Client Guide for AssocMemoryServer")
    print("=" * 60)
    
    explain_client_initialization()
    asyncio.run(demonstrate_usage_patterns())
    show_server_startup_options()
    show_key_differences()
    asyncio.run(practical_example())
    
    print("\n\n🎉 Summary")
    print("=" * 50)
    print("✅ FastMCP Client uses structured 'request' parameters")
    print("✅ New scope system replaces legacy domain system")
    print("✅ Hierarchical scopes support Unicode and nesting")
    print("✅ New tools for scope management and pagination")
    print("✅ STDIO transport for VSCode integration")
    print("✅ HTTP transport for testing and development")
    
    print("\n📚 Next Steps:")
    print("1. Start server: python -m src.mcp_assoc_memory")
    print("2. Update .vscode/mcp.json for STDIO integration")
    print("3. Test with your own client code")
    print("4. Explore scope management features")
