"""
Enhanced error handling demonstration for MCP tools

This module demonstrates how the enhanced error handling system
can be integrated into MCP tool functions with improved user experience.
"""

import asyncio
from datetime import datetime
from typing import Dict, Any

from fastmcp import Context

from mcp_assoc_memory.api.error_handling import (
    ErrorHandler,
    MemoryNotFoundError,
    ValidationError,
    create_success_response,
    validate_content,
    validate_scope,
    validate_memory_id,
)


async def demo_enhanced_memory_validation(
    memory_id: str,
    content: str,
    scope: str,
    ctx: Context
) -> Dict[str, Any]:
    """
    Demonstration function showing enhanced error handling for memory operations
    
    This function shows how input validation and error handling can provide
    better user experience with actionable error messages.
    """
    try:
        # Comprehensive input validation with specific error messages
        validate_memory_id(memory_id)
        validate_content(content)
        validate_scope(scope)
        
        await ctx.info(f"Validating memory operation: ID={memory_id}, scope={scope}")
        
        # Simulate some processing
        if len(content) > 10000:
            from mcp_assoc_memory.api.error_handling import ResourceLimitError
            raise ResourceLimitError(
                "content_length",
                "10000",
                str(len(content)),
                {"content_preview": content[:100] + "..."}
            )
        
        # Simulate successful operation
        return create_success_response(
            message=f"Memory validation successful for ID: {memory_id}",
            data={
                "memory_id": memory_id,
                "content_length": len(content),
                "scope": scope,
                "validation_status": "passed",
                "timestamp": datetime.now().isoformat()
            }
        )
        
    except (ValidationError, MemoryNotFoundError) as e:
        # Handle known errors with structured response
        return await ErrorHandler.handle_error(e, ctx, "memory_validation")
    
    except Exception as e:
        # Handle unexpected errors
        return await ErrorHandler.handle_error(e, ctx, "memory_validation")


async def demo_memory_search_with_error_handling(
    query: str,
    scope: str,
    ctx: Context
) -> Dict[str, Any]:
    """
    Demonstration of search operation with enhanced error handling
    """
    try:
        # Input validation
        if not query or len(query.strip()) == 0:
            raise ValidationError("query", query, "cannot be empty")
        
        if scope:
            validate_scope(scope)
        
        await ctx.info(f"Performing enhanced search: query='{query}', scope='{scope}'")
        
        # Simulate search operation
        if query.lower() == "trigger_error":
            raise RuntimeError("Simulated search engine error")
        
        # Simulate successful search with fallback behavior
        results = []
        if query.lower() == "empty_results":
            # Demonstrate fallback suggestions
            fallback_data = {
                "results": [],
                "suggestions": [
                    "Try broader search terms",
                    "Check the scope setting",
                    "Use different keywords"
                ],
                "fallback": True
            }
            return create_success_response(
                message="No results found, but here are some suggestions",
                data=fallback_data
            )
        
        # Normal successful results
        results = [
            {
                "id": f"result-{i}",
                "content": f"Mock result {i} for query: {query}",
                "scope": scope or "global",
                "relevance": 0.9 - (i * 0.1)
            }
            for i in range(3)
        ]
        
        return create_success_response(
            message=f"Found {len(results)} results for query: {query}",
            data={
                "results": results,
                "query": query,
                "scope": scope,
                "total_results": len(results)
            }
        )
        
    except ValidationError as e:
        # Return error with specific validation guidance
        return await ErrorHandler.handle_error(e, ctx, "memory_search")
    
    except Exception as e:
        # Handle unexpected errors with fallback empty results
        fallback_response = {
            "results": [],
            "query": query,
            "error_recovery": True
        }
        return await ErrorHandler.handle_error(
            e, ctx, "memory_search", 
            fallback_response=fallback_response
        )


class MockContext:
    """Mock context for demonstration"""
    
    async def info(self, message: str):
        print(f"[INFO] {message}")
    
    async def warning(self, message: str):
        print(f"[WARNING] {message}")
    
    async def error(self, message: str):
        print(f"[ERROR] {message}")


async def main():
    """Demonstrate enhanced error handling in action"""
    print("🔧 Enhanced Error Handling Demo for MCP Tools")
    print("=" * 60)
    
    ctx = MockContext()
    
    # Test 1: Successful validation
    print("\n1. Testing successful validation:")
    result = await demo_enhanced_memory_validation(
        "valid-id-123", "This is valid content", "work/projects", ctx
    )
    print(f"✅ Success: {result['message']}")
    
    # Test 2: Validation error
    print("\n2. Testing validation error:")
    result = await demo_enhanced_memory_validation(
        "", "content", "work/projects", ctx
    )
    print(f"❌ Error handled: {result['error']['message']}")
    print(f"   Suggestions: {result['error']['suggestions']}")
    
    # Test 3: Successful search
    print("\n3. Testing successful search:")
    result = await demo_memory_search_with_error_handling(
        "python programming", "work/learning", ctx
    )
    print(f"✅ Search success: {result['message']}")
    print(f"   Results: {len(result['data']['results'])}")
    
    # Test 4: Search with fallback
    print("\n4. Testing search with fallback suggestions:")
    result = await demo_memory_search_with_error_handling(
        "empty_results", "work/test", ctx
    )
    print(f"💡 Fallback: {result['message']}")
    print(f"   Suggestions: {result['data']['suggestions']}")
    
    # Test 5: Error handling with recovery
    print("\n5. Testing error handling with recovery:")
    result = await demo_memory_search_with_error_handling(
        "trigger_error", "work/test", ctx
    )
    print(f"🔄 Error recovery: {result['message']}")
    print(f"   Fallback data: {result['data']}")
    
    print("\n" + "=" * 60)
    print("🎉 Enhanced error handling demonstration completed!")
    print("\n📈 Benefits shown:")
    print("   • Clear, actionable error messages")
    print("   • Structured error responses with suggestions")
    print("   • Graceful degradation with fallback data")
    print("   • Consistent error categorization and severity")
    print("   • Better debugging information for developers")


if __name__ == "__main__":
    asyncio.run(main())
