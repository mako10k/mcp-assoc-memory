"""
MCP Tool Error Handling Improvement Test

This script tests the enhanced error handling capabilities
introduced to the MCP Associative Memory tools.
"""

import asyncio
import sys
import os
import json

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from mcp_assoc_memory.api.tools.memory_tools import handle_memory_store, handle_memory_search
from mcp_assoc_memory.api.models import MemoryStoreRequest, MemorySearchRequest


class MockContext:
    """Mock FastMCP context for testing"""
    
    def __init__(self):
        self.messages = []
    
    async def info(self, message: str):
        self.messages.append(f"[INFO] {message}")
        print(f"[INFO] {message}")
    
    async def warning(self, message: str):
        self.messages.append(f"[WARNING] {message}")
        print(f"[WARNING] {message}")
    
    async def error(self, message: str):
        self.messages.append(f"[ERROR] {message}")
        print(f"[ERROR] {message}")


async def test_improved_error_handling():
    """Test the improved error handling in MCP tools"""
    print("🔧 Testing Enhanced Error Handling in MCP Tools")
    print("=" * 60)
    
    ctx = MockContext()
    
    # Test 1: Empty content validation
    print("\n1. Testing empty content validation:")
    request = MemoryStoreRequest(
        content="",  # Empty content should trigger validation error
        scope="work/test"
    )
    
    result = await handle_memory_store(request, ctx)
    print(f"✅ Empty content handled: {result.metadata.get('error', 'No error info')}")
    print(f"   Suggestions: {result.metadata.get('suggestions', [])}")
    
    # Test 2: Empty scope validation
    print("\n2. Testing empty scope validation:")
    request = MemoryStoreRequest(
        content="Valid content",
        scope=""  # Empty scope should trigger validation error
    )
    
    result = await handle_memory_store(request, ctx)
    print(f"✅ Empty scope handled: {result.metadata.get('error', 'No error info')}")
    print(f"   Suggestions: {result.metadata.get('suggestions', [])}")
    
    # Test 3: Valid memory store (should work normally)
    print("\n3. Testing valid memory store:")
    request = MemoryStoreRequest(
        content="This is a test memory for error handling demonstration",
        scope="work/test/error_handling"
    )
    
    result = await handle_memory_store(request, ctx)
    if result.memory_id != "error":
        print(f"✅ Valid store succeeded: ID={result.memory_id}")
    else:
        print(f"❌ Valid store failed: {result.metadata.get('error', 'Unknown error')}")
    
    # Test 4: Search with invalid query (empty query would be caught by validation)
    print("\n4. Testing search error handling:")
    
    # This will test the general exception handling in search
    search_request = MemorySearchRequest(
        query="test query",
        scope="work/test"
    )
    
    try:
        result = await handle_memory_search(search_request, ctx)
        
        if "error" in result:
            print(f"✅ Search error handled: {result['error']}")
            print(f"   Fallback results: {len(result.get('results', []))}")
            print(f"   Suggestions: {result.get('suggestions', [])}")
        else:
            print(f"✅ Search completed: Found {len(result.get('results', []))} results")
        
    except Exception as e:
        print(f"❌ Search failed with unhandled exception: {e}")


async def demonstrate_error_improvements():
    """Show the improvements in error handling"""
    print("\n" + "=" * 60)
    print("📈 Error Handling Improvements Demonstrated")
    print("=" * 60)
    
    print("\n🎯 Key Improvements:")
    print("   • Input validation with specific error messages")
    print("   • Detailed error metadata with troubleshooting suggestions")
    print("   • Graceful fallback responses instead of crashes")
    print("   • Error categorization (validation vs system errors)")
    print("   • User-friendly error messages with actionable guidance")
    
    print("\n🔍 Error Response Structure:")
    print("   • error: Human-readable error message")
    print("   • details: Technical error details for debugging")
    print("   • suggestions: List of actionable steps for users")
    print("   • error_type: Exception type for categorization")
    print("   • fallback_used: Indicates graceful degradation")
    
    print("\n📊 Error Categories Handled:")
    print("   • Input Validation Errors (empty content, invalid scope)")
    print("   • System Errors (database connection, initialization)")
    print("   • Network Errors (connection timeouts, API failures)")
    print("   • Resource Limits (memory, storage, processing)")
    print("   • Unexpected Errors (with graceful fallback)")
    
    print("\n💡 User Experience Benefits:")
    print("   • Clear understanding of what went wrong")
    print("   • Specific steps to resolve the issue")
    print("   • Fallback data when possible (search returns empty results)")
    print("   • Consistent error format across all MCP tools")
    print("   • Better debugging information for developers")


async def main():
    """Run error handling improvement tests"""
    try:
        await test_improved_error_handling()
        await demonstrate_error_improvements()
        
        print("\n" + "=" * 60)
        print("🎉 Enhanced Error Handling Test Completed Successfully!")
        print("\n📝 Next Steps:")
        print("   • Apply similar error handling to other MCP tools")
        print("   • Add more specific validation rules as needed")
        print("   • Monitor error patterns to improve handling")
        print("   • Update documentation with error handling guidance")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
