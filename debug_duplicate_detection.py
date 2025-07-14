#!/usr/bin/env python3
"""
Debug script for duplicate detection functionality
"""
import asyncio
import json
from src.mcp_assoc_memory.api.models.requests import MemoryStoreRequest
from src.mcp_assoc_memory.api.tools.memory_tools import handle_memory_store
from fastmcp import FastMCP, Context

async def debug_duplicate_detection():
    """Test duplicate detection logic"""
    print("=== Testing Duplicate Detection Logic ===")
    
    # Create mock context
    class MockContext(Context):
        def __init__(self):
            pass
            
        async def info(self, message: str):
            print(f"[INFO] {message}")
            
        async def warning(self, message: str):
            print(f"[WARNING] {message}")
            
        async def error(self, message: str):
            print(f"[ERROR] {message}")
    
    ctx = MockContext()
    
    # Test 1: Store without threshold (should succeed)
    print("\n--- Test 1: Store without threshold ---")
    request1 = MemoryStoreRequest(
        content="Debug test memory content for duplicate detection",
        scope="debug/test1",
        duplicate_threshold=None
    )
    result1 = await handle_memory_store(request1, ctx)
    print(f"Result 1: {json.dumps(result1, indent=2)}")
    
    # Test 2: Store with threshold (should succeed first time)
    print("\n--- Test 2: Store with threshold (first time) ---")
    request2 = MemoryStoreRequest(
        content="Debug test memory content for duplicate detection",
        scope="debug/test2",
        duplicate_threshold=0.95
    )
    result2 = await handle_memory_store(request2, ctx)
    print(f"Result 2: {json.dumps(result2, indent=2)}")
    
    # Test 3: Store same content with threshold (should fail with duplicate)
    print("\n--- Test 3: Store same content with threshold (should fail) ---")
    request3 = MemoryStoreRequest(
        content="Debug test memory content for duplicate detection",
        scope="debug/test3",
        duplicate_threshold=0.95
    )
    result3 = await handle_memory_store(request3, ctx)
    print(f"Result 3: {json.dumps(result3, indent=2)}")
    
    print("\n=== Debug Complete ===")

if __name__ == "__main__":
    asyncio.run(debug_duplicate_detection())
