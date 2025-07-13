#!/usr/bin/env python3
"""Test move operation directly"""

import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from mcp_assoc_memory.core.singleton_memory_manager import get_or_create_memory_manager

async def test_move_operation():
    print("Testing move operation...")
    
    # Get memory manager
    memory_manager = await get_or_create_memory_manager()
    if not memory_manager:
        print("ERROR: Memory manager not available")
        return False
    
    memory_id = "36b626d8-c4f0-46a5-8100-a1ca7a785b33"
    target_scope = "testing/final-destination"
    
    # Get current memory state
    print(f"Getting memory {memory_id}...")
    current_memory = await memory_manager.get_memory(memory_id)
    if not current_memory:
        print(f"ERROR: Memory {memory_id} not found")
        return False
    
    print(f"Current scope: {current_memory.scope}")
    print(f"Current metadata scope: {current_memory.metadata.get('scope', 'NOT_SET')}")
    
    # Perform move operation
    print(f"Moving to {target_scope}...")
    updated_memory = await memory_manager.update_memory(
        memory_id=memory_id,
        scope=target_scope,
        metadata={"scope": target_scope}
    )
    
    if updated_memory is None:
        print("ERROR: update_memory returned None")
        return False
    
    print(f"Updated scope: {updated_memory.scope}")
    print(f"Updated metadata scope: {updated_memory.metadata.get('scope', 'NOT_SET')}")
    
    # Verify in database
    print("Verifying in database...")
    verify_memory = await memory_manager.get_memory(memory_id)
    if not verify_memory:
        print("ERROR: Could not retrieve memory after update")
        return False
    
    print(f"DB scope: {verify_memory.scope}")
    print(f"DB metadata scope: {verify_memory.metadata.get('scope', 'NOT_SET')}")
    
    if verify_memory.scope == target_scope and verify_memory.metadata.get('scope') == target_scope:
        print("SUCCESS: Move operation completed successfully!")
        return True
    else:
        print("ERROR: Move operation failed - scope mismatch")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_move_operation())
    sys.exit(0 if result else 1)
