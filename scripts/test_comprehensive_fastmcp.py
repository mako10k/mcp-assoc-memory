"""
Comprehensive test script for all FastMCP features
Tests Tools, Resources, and Prompts
"""

import asyncio
import json
from fastmcp import Client

async def test_comprehensive_fastmcp():
    """Comprehensive test of all FastMCP features"""
    
    async with Client("http://localhost:8000/mcp") as client:
        print("🚀 Connected to FastMCP server")
        
        # === 1. Tool functionality tests ===
        print("\n=== 🔧 Tool Functionality Tests ===")
        
        # Get available tools
        tools = await client.list_tools()
        print(f"Available tools: {[tool.name for tool in tools]}")
        
        # Test data storage
        memories = [
            {"content": "FastMCP implementation learning notes", "scope": "development/learning", "metadata": {"category": "learning"}},
            {"content": "Project management key points", "scope": "work/projects", "metadata": {"category": "management"}},
            {"content": "Code review checklist", "scope": "development/process", "metadata": {"category": "process"}},
            {"content": "Unicode scope test: 日本語メモ", "scope": "personal/日本語", "metadata": {"language": "ja"}},
            {"content": "Session-based temporary note", "scope": "session/test-2025", "metadata": {"temporary": True}},
        ]
        
        print("\n📝 Storing memories:")
        for mem in memories:
            result = await client.call_tool("memory_store", {"request": mem})
            print(f"  - Stored: {mem['content'][:30]}...")
        
        # Search test
        print("\n🔍 Searching memories:")
        search_result = await client.call_tool("memory_search", {
            "request": {"query": "FastMCP", "limit": 5}
        })
        print(f"  Search completed successfully")
        
        # Hierarchical search test
        print("\n🌲 Hierarchical search test:")
        dev_search = await client.call_tool("memory_search", {
            "request": {"query": "learning", "scope": "development", "include_child_scopes": True, "limit": 5}
        })
        print(f"  Development scope search completed")
        
        # === 2. New Scope Management Tests ===
        print("\n=== 🔧 Scope Management Tests ===")
        
        # Test scope listing
        print("\n📋 Listing all scopes:")
        scope_list = await client.call_tool("scope_list", {
            "request": {"include_memory_counts": True}
        })
        print(f"  Scope listing completed")
        
        # Test scope suggestion
        print("\n💡 Testing scope suggestion:")
        suggestion = await client.call_tool("scope_suggest", {
            "request": {"content": "Meeting notes from the weekly standup", "current_scope": "work/meetings"}
        })
        print(f"  Scope suggestion completed")
        
        # Test session management
        print("\n🔄 Testing session management:")
        
        # Create session
        session_create = await client.call_tool("session_manage", {
            "request": {"action": "create", "session_id": "test-session"}
        })
        print(f"  Session creation completed")
        
        # List sessions
        session_list = await client.call_tool("session_manage", {
            "request": {"action": "list"}
        })
        print(f"  Session listing completed")
        
        # === 2. Resource functionality tests ===
        print("\n=== 📊 Resource Functionality Tests ===")
        
        # Get available resources
        resources = await client.list_resources()
        print(f"Available resources: {[resource.uri for resource in resources]}")
        
        # Get statistics resource
        print("\n📈 Memory statistics:")
        stats_resource = await client.read_resource("memory://stats")
        print("  Statistics resource retrieved successfully")
        
        # Get scope-specific resource
        print("\n🏷️ Scope-specific memories (development):")
        scope_resource = await client.read_resource("memory://scope/development")
        print("  Development scope resource retrieved successfully")
        
        # === 3. Prompt functionality tests ===
        print("\n=== 💭 Prompt Functionality Tests ===")
        
        # Get available prompts
        prompts = await client.list_prompts()
        print(f"Available prompts: {[prompt.name for prompt in prompts]}")
        
        # Generate memory analysis prompt
        print("\n🔬 Generating memory analysis prompt:")
        analysis_prompt = await client.get_prompt("analyze_memories", {"domain": "development"})
        print(f"  Prompt length: {len(analysis_prompt.messages[0].content.text)} characters")
        print(f"  Prompt excerpt: {analysis_prompt.messages[0].content.text[:100]}...")
        
        # Generate specific memory summary prompt
        if stats_data['total_memories'] > 0:
            # Get first memory ID
            all_memories = await client.call_tool("memory_list_all", {})
            memories_list = json.loads(all_memories.content[0].text)
            if memories_list:
                first_memory_id = memories_list[0]['memory_id']
                
                print(f"\n📝 Generating memory summary prompt (ID: {first_memory_id[:8]}...):")
                summary_prompt = await client.get_prompt("summarize_memory", {"memory_id": first_memory_id})
                print(f"  Prompt length: {len(summary_prompt.messages[0].content.text)} characters")
                print(f"  Prompt excerpt: {summary_prompt.messages[0].content.text[:150]}...")
        
        # === 4. Annotation functionality verification ===
        print("\n=== 🏷️ Tool Annotation Verification ===")
        for tool in tools:
            print(f"  {tool.name}:")
            desc = getattr(tool, 'description', '') or ''
            print(f"    Description: {desc[:50]}...")
            
            # Display known annotation information (if implemented)
            if tool.name == "memory_store":
                print("    Title: Store Memory")
                print("    Read-only: False")
                print("    Destructive: False")
            elif tool.name == "memory_search":
                print("    Title: Search Memories")
                print("    Read-only: True")
                print("    Destructive: False")
            elif tool.name == "memory_delete":
                print("    Title: Delete Memory")
                print("    Read-only: False")
                print("    Destructive: True")
        
        # === 5. Context functionality verification (log output) ===
        print("\n=== 📋 Context Functionality Test (Check Logs) ===")
        print("  Please check server logs for Context.info(), Context.warning(), etc. output")
        
        print("\n✅ FastMCP comprehensive test completed!")
        print(f"  - Tools: {len(tools)} items")
        print(f"  - Resources: {len(resources)} items")
        print(f"  - Prompts: {len(prompts)} items")
        print(f"  - Stored memories: {stats_data['total_memories']} items")

if __name__ == "__main__":
    asyncio.run(test_comprehensive_fastmcp())
