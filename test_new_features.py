#!/usr/bin/env python3
"""
Test script for new scope management features
"""

import asyncio
import sys
sys.path.append('/workspaces/mcp-assoc-memory')

from src.mcp_assoc_memory.server import memory_storage

def test_memory_storage():
    """Test that we have memories in storage"""
    print(f"Current memory storage has {len(memory_storage)} memories")
    for mem_id, mem_data in memory_storage.items():
        print(f"  - {mem_data['scope']}: {mem_data['content'][:50]}...")
    print()

def test_scope_analysis():
    """Analyze current scopes"""
    scopes = set()
    for mem_data in memory_storage.values():
        scopes.add(mem_data['scope'])
    
    print(f"Found {len(scopes)} unique scopes:")
    for scope in sorted(scopes):
        mem_count = len([m for m in memory_storage.values() if m['scope'] == scope])
        print(f"  - {scope}: {mem_count} memories")
    print()

def test_hierarchy():
    """Test scope hierarchy functions"""
    from src.mcp_assoc_memory.server import get_child_scopes, get_parent_scope
    
    all_scopes = list(set(m['scope'] for m in memory_storage.values()))
    
    print("Testing scope hierarchy:")
    for scope in sorted(all_scopes):
        parent = get_parent_scope(scope)
        children = get_child_scopes(scope, all_scopes)
        print(f"  {scope}")
        print(f"    Parent: {parent}")
        print(f"    Children: {children}")
    print()

if __name__ == "__main__":
    print("=== Scope Management Test ===")
    test_memory_storage()
    test_scope_analysis()
    test_hierarchy()
    print("✅ All tests completed!")
