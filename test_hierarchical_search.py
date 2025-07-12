#!/usr/bin/env python3
"""
Demo script to test hierarchical scope fallback search functionality
"""

import asyncio
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.mcp_assoc_memory.api.tools.memory_tools import (
    _extract_parent_scope,
    _perform_hierarchical_fallback_search
)


class MockContext:
    """Mock context for testing"""
    
    async def info(self, message: str):
        print(f"INFO: {message}")
    
    async def warning(self, message: str):
        print(f"WARNING: {message}")
    
    async def error(self, message: str):
        print(f"ERROR: {message}")


class MockMemoryManager:
    """Mock memory manager for testing"""
    
    def __init__(self):
        # Sample memories for testing
        self.memories = {
            "work/architecture/decisions": [
                {"memory": MockMemory("architectural decision 1", "work/architecture/decisions"), "similarity": 0.8},
                {"memory": MockMemory("design pattern choice", "work/architecture/decisions"), "similarity": 0.7},
            ],
            "work/architecture": [
                {"memory": MockMemory("system architecture overview", "work/architecture"), "similarity": 0.9},
            ],
            "work": [
                {"memory": MockMemory("project status", "work/status"), "similarity": 0.6},
                {"memory": MockMemory("team meeting notes", "work/meetings"), "similarity": 0.5},
            ],
            "learning/programming": [
                {"memory": MockMemory("python best practices", "learning/programming/python"), "similarity": 0.8},
                {"memory": MockMemory("code review guidelines", "learning/programming/reviews"), "similarity": 0.7},
            ]
        }
    
    async def search_memories(self, query, scope=None, include_child_scopes=False, limit=5, min_score=0.1):
        """Mock search that returns results based on scope"""
        if scope is None:  # Global search
            all_results = []
            for scope_memories in self.memories.values():
                all_results.extend(scope_memories)
            return all_results[:limit]
        
        return self.memories.get(scope, [])


class MockMemory:
    """Mock memory object"""
    
    def __init__(self, content, scope):
        self.content = content
        self.scope = scope
        self.metadata = {"scope": scope}


async def test_hierarchical_fallback():
    """Test the hierarchical fallback search functionality"""
    
    print("=== Testing Hierarchical Scope Fallback Search ===\n")
    
    # Setup mocks
    ctx = MockContext()
    
    # Test cases
    test_cases = [
        {
            "query": "architecture documentation",
            "scope": "work/architecture/decisions/legacy",
            "expected_fallback_level": 2,
            "description": "Deep scope that should fallback to work/architecture"
        },
        {
            "query": "python tips",
            "scope": "learning/programming/advanced/frameworks",
            "expected_fallback_level": 2,
            "description": "Learning scope that should fallback to learning/programming"
        },
        {
            "query": "nonexistent topic",
            "scope": "nonexistent/scope/deep/nested",
            "expected_fallback_level": 4,
            "description": "Non-existent scope that should fallback to global search"
        }
    ]
    
    # Mock the global memory_manager
    import src.mcp_assoc_memory.api.tools.memory_tools as tools_module
    original_manager = tools_module.memory_manager
    tools_module.memory_manager = MockMemoryManager()
    
    try:
        for i, test_case in enumerate(test_cases, 1):
            print(f"Test Case {i}: {test_case['description']}")
            print(f"Query: '{test_case['query']}'")
            print(f"Original Scope: '{test_case['scope']}'")
            print(f"Expected Fallback Level: {test_case['expected_fallback_level']}")
            print()
            
            result = await _perform_hierarchical_fallback_search(
                query=test_case['query'],
                original_scope=test_case['scope'],
                ctx=ctx,
                limit=5,
                similarity_threshold=0.1,
                include_child_scopes=False
            )
            
            print("Result:")
            for key, value in result.items():
                print(f"  {key}: {value}")
            
            print(f"\nActual Fallback Level: {result.get('fallback_level', 'N/A')}")
            print(f"Found Scope Candidates: {len(result.get('candidates', []))}")
            print("-" * 60)
            print()
    
    finally:
        # Restore original manager
        tools_module.memory_manager = original_manager


async def test_parent_extraction():
    """Test parent scope extraction"""
    
    print("=== Testing Parent Scope Extraction ===\n")
    
    test_scopes = [
        "work/architecture/decisions/legacy",
        "work/architecture/decisions",
        "work/architecture",
        "work",
        "single",
        "",
        "a/b/c/d/e/f/g"
    ]
    
    for scope in test_scopes:
        parent = await _extract_parent_scope(scope)
        print(f"{scope:35} -> {parent}")
    
    print()


async def main():
    """Run all tests"""
    await test_parent_extraction()
    await test_hierarchical_fallback()
    print("=== All Tests Completed ===")


if __name__ == "__main__":
    asyncio.run(main())
