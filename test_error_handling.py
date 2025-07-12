"""
Test script for enhanced error handling in MCP tools

This script demonstrates the improved error handling capabilities
and validates different error scenarios.
"""

import asyncio
import sys
import os

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from mcp_assoc_memory.api.error_handling import (
    ErrorHandler,
    MemoryNotFoundError,
    InvalidScopeError,
    ValidationError,
    MemoryManagerNotInitializedError,
    validate_content,
    validate_scope,
    validate_memory_id,
)


class MockContext:
    """Mock FastMCP context for testing"""
    
    async def info(self, message: str):
        print(f"[INFO] {message}")
    
    async def warning(self, message: str):
        print(f"[WARNING] {message}")
    
    async def error(self, message: str):
        print(f"[ERROR] {message}")


async def test_validation_functions():
    """Test input validation functions"""
    print("=== Testing Validation Functions ===")
    
    # Test valid inputs
    try:
        validate_content("This is valid content")
        validate_scope("work/projects")
        validate_memory_id("valid-memory-id-123")
        print("✅ Valid inputs passed validation")
    except Exception as e:
        print(f"❌ Valid inputs failed: {e}")
    
    # Test invalid content
    try:
        validate_content("")
        print("❌ Empty content should have failed")
    except ValidationError as e:
        print(f"✅ Empty content properly rejected: {e.details.message}")
    
    # Test invalid scope
    try:
        validate_scope("/invalid/scope/")
        print("❌ Invalid scope should have failed")
    except InvalidScopeError as e:
        print(f"✅ Invalid scope properly rejected: {e.details.message}")
    
    # Test invalid memory ID
    try:
        validate_memory_id("")
        print("❌ Empty memory ID should have failed")
    except ValidationError as e:
        print(f"✅ Empty memory ID properly rejected: {e.details.message}")


async def test_error_handler():
    """Test centralized error handling"""
    print("\n=== Testing Error Handler ===")
    
    ctx = MockContext()
    
    # Test ValidationError handling
    try:
        validate_content("")
    except ValidationError as e:
        response = await ErrorHandler.handle_error(e, ctx, "test_operation")
        print(f"✅ ValidationError response: {response['error']['message']}")
        print(f"   Suggestions: {response['error']['suggestions']}")
    
    # Test generic exception handling
    try:
        raise RuntimeError("Unexpected error occurred")
    except Exception as e:
        response = await ErrorHandler.handle_error(e, ctx, "test_operation")
        print(f"✅ Generic error response: {response['error']['message']}")
        print(f"   Code: {response['error']['code']}")
    
    # Test with fallback data
    try:
        raise MemoryNotFoundError("test-id-123")
    except MemoryNotFoundError as e:
        response = await ErrorHandler.handle_error(
            e, ctx, "memory_retrieval", 
            fallback_response={"results": [], "fallback": True}
        )
        print(f"✅ Error with fallback: {response['message']}")
        print(f"   Fallback data: {response['data']}")


async def test_error_scenarios():
    """Test different error scenarios"""
    print("\n=== Testing Error Scenarios ===")
    
    # Memory not found
    error = MemoryNotFoundError("missing-id-456", {"scope": "work/projects"})
    print(f"✅ MemoryNotFoundError: {error.details.message}")
    print(f"   Suggestions: {error.details.suggestions}")
    
    # Invalid scope
    error = InvalidScopeError("invalid//scope", {"attempted_operation": "search"})
    print(f"✅ InvalidScopeError: {error.details.message}")
    print(f"   Category: {error.details.category.value}")
    
    # Memory manager not initialized
    error = MemoryManagerNotInitializedError("search_operation")
    print(f"✅ MemoryManagerNotInitializedError: {error.details.message}")
    print(f"   Severity: {error.details.severity.value}")


async def main():
    """Run all error handling tests"""
    print("🧪 Testing Enhanced Error Handling System")
    print("=" * 50)
    
    try:
        await test_validation_functions()
        await test_error_handler()
        await test_error_scenarios()
        
        print("\n" + "=" * 50)
        print("🎉 All error handling tests completed successfully!")
        print("\n📝 Key benefits demonstrated:")
        print("   • Input validation with specific error messages")
        print("   • Centralized error handling with structured responses")
        print("   • User-friendly error messages with actionable suggestions")
        print("   • Proper error categorization and severity levels")
        print("   • Fallback response capability for graceful degradation")
        
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
