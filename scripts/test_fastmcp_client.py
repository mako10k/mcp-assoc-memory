"""
Test script using FastMCP client
"""

import asyncio
import json
from fastmcp import Client

async def test_memory_operations():
    """Test memory operations"""
    
    # Connect to server using FastMCP client
    async with Client("http://localhost:8000/mcp") as client:
        print("Connected to FastMCP server")
        
        # Get list of available tools
        tools = await client.list_tools()
        print(f"Available tools: {[tool.name for tool in tools]}")
        
        # Test data
        memories = [
            {"content": "Test memory A", "domain": "user", "metadata": {"tag": "similar_test"}},
            {"content": "Test memory A variant", "domain": "user", "metadata": {"tag": "similar_test"}},
            {"content": "Test memory A details", "domain": "user", "metadata": {"tag": "similar_test"}},
        ]
        
        stored_memory_ids = []
        
        # Store memories
        for i, mem in enumerate(memories):
            print(f"\n[{i + 1}/{len(memories)}] Storing memory: {mem['content']}")
            
            result = await client.call_tool("memory_store", {"request": mem})
            print(f"Store result: {result.content}")
            
            # Get memory_id from structured output
            if hasattr(result, 'structured_content') and result.structured_content:
                memory_id = result.structured_content.get('memory_id')
                if memory_id:
                    stored_memory_ids.append(memory_id)
                    print(f"Memory ID: {memory_id}")
        
        print(f"\nStored memory IDs: {stored_memory_ids}")
        
        # Test search
        print("\n=== Search Test ===")
        search_result = await client.call_tool("memory_search", {
            "request": {
                "query": "Test memory A",
                "domain": "user",
                "limit": 10
            }
        })
        print(f"Search result: {search_result.content}")
        
        # Get all memories
        print("\n=== All Memories List ===")
        list_result = await client.call_tool("memory_list_all", {})
        print(f"All memories: {list_result.content}")
        
        # Get specific memory
        if stored_memory_ids:
            print(f"\n=== Get Specific Memory: {stored_memory_ids[0]} ===")
            get_result = await client.call_tool("memory_get", {"memory_id": stored_memory_ids[0]})
            print(f"Get result: {get_result.content}")
        
        print("\nTest completed")

if __name__ == "__main__":
    asyncio.run(test_memory_operations())
