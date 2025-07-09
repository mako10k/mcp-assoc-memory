"""
FastMCP annotation functionality test script
"""

import asyncio
import json
from fastmcp import Client

async def test_annotations():
    """Test annotation functionality"""
    
    async with Client("http://localhost:8000/mcp") as client:
        print("🏷️ FastMCP Annotation Functionality Test")
        
        # Get tool list and check annotations
        tools = await client.list_tools()
        
        print("\n=== 📋 Tool Annotation Details ===")
        for tool in tools:
            print(f"\n🔧 Tool: {tool.name}")
            print(f"   Description: {tool.description}")
            
            # If annotations exist
            if hasattr(tool, 'annotations') and tool.annotations:
                print("   Annotations:")
                annotations_dict = tool.annotations.model_dump() if hasattr(tool.annotations, 'model_dump') else tool.annotations.__dict__
                for key, value in annotations_dict.items():
                    print(f"     {key}: {value}")
            else:
                print("   Annotations: None")
        
        # Actually call tools to check log output
        print("\n=== 🎯 Actual Tool Call Tests ===")
        
        # Non-destructive operation
        print("\n📊 Non-destructive operation test (memory_list_all):")
        list_result = await client.call_tool("memory_list_all", {})
        memories = json.loads(list_result.content[0].text)
        print(f"Retrieved memory count: {len(memories)}")
        
        # Store new memory (non-destructive)
        print("\n💾 Memory storage test (memory_store):")
        store_result = await client.call_tool("memory_store", {
            "request": {
                "content": "Annotation functionality test memory",
                "domain": "test",
                "metadata": {"test": "annotations"}
            }
        })
        stored_memory = json.loads(store_result.content[0].text)
        print(f"Stored memory ID: {stored_memory['memory_id']}")
        
        # Search (read-only)
        print("\n🔍 Search test (memory_search):")
        search_result = await client.call_tool("memory_search", {
            "request": {
                "query": "Annotation",
                "limit": 5
            }
        })
        found_memories = json.loads(search_result.content[0].text)
        print(f"Search results: {len(found_memories)} items")
        
        print("\n✅ Annotation test completed")
        print("Please check server logs for Context.info(), Context.warning(), etc. output")

if __name__ == "__main__":
    asyncio.run(test_annotations())
