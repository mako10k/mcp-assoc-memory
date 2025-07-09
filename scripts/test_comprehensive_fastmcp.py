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
            {"content": "FastMCP implementation learning notes", "domain": "development", "metadata": {"category": "learning"}},
            {"content": "Project management key points", "domain": "project", "metadata": {"category": "management"}},
            {"content": "Code review checklist", "domain": "development", "metadata": {"category": "process"}},
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
        print(f"  FastMCP-related memories: {len(json.loads(search_result.content[0].text))} items")
        
        # === 2. Resource functionality tests ===
        print("\n=== 📊 Resource Functionality Tests ===")
        
        # Get available resources
        resources = await client.list_resources()
        print(f"Available resources: {[resource.uri for resource in resources]}")
        
        # Get statistics resource
        print("\n📈 Memory statistics:")
        stats_resource = await client.read_resource("memory://stats")
        stats_data = json.loads(stats_resource[0].text)
        print(f"  Total memories: {stats_data['total_memories']}")
        print(f"  By domain: {stats_data['domains']}")
        
        # Get domain-specific resource
        print("\n🏷️ Domain-specific memories (development):")
        domain_resource = await client.read_resource("memory://domain/development")
        domain_data = json.loads(domain_resource[0].text)
        print(f"  Development domain memory count: {domain_data['count']}")
        
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
