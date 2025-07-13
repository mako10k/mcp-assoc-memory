#!/usr/bin/env python3
"""
Debug script to test memory manager storage components individually
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from mcp_assoc_memory.core.singleton_memory_manager import get_or_create_memory_manager
from mcp_assoc_memory.models.memory import Memory
from datetime import datetime


async def test_storage_components():
    """Test each storage component individually"""
    print("🔍 Testing Storage Components Individually")
    print("=" * 50)
    
    try:
        # Get memory manager
        print("1. Getting memory manager...")
        manager = await get_or_create_memory_manager()
        if manager is None:
            print("❌ Memory manager is None")
            return
        print("✅ Memory manager obtained")
        
        # Check if components are initialized
        print("\n2. Checking component initialization...")
        print(f"   - Vector Store: {manager.vector_store is not None}")
        print(f"   - Metadata Store: {manager.metadata_store is not None}")  
        print(f"   - Graph Store: {manager.graph_store is not None}")
        print(f"   - Embedding Service: {manager.embedding_service is not None}")
        
        # Create test memory
        print("\n3. Creating test memory object...")
        test_memory = Memory(
            scope="test/debug",
            content="Test memory for storage debugging",
            metadata={"scope": "test/debug", "test": True},
            tags=["debug", "test"],
            category="testing"
        )
        print(f"✅ Test memory created: {test_memory.id}")
        
        # Test embedding generation
        print("\n4. Testing embedding generation...")
        try:
            embedding = await manager.embedding_service.get_embedding(test_memory.content)
            if embedding is None:
                print("❌ Embedding generation failed")
            else:
                print(f"✅ Embedding generated (length: {len(embedding)})")
        except Exception as e:
            print(f"❌ Embedding generation error: {e}")
            embedding = None
        
        # Test metadata store
        print("\n5. Testing metadata store...")
        try:
            metadata_result = await manager.metadata_store.store_memory(test_memory)
            print(f"✅ Metadata store result: {metadata_result}")
        except Exception as e:
            print(f"❌ Metadata store error: {e}")
            return
            
        # Test vector store (if embedding available)
        if embedding is not None:
            print("\n6. Testing vector store...")
            try:
                vector_result = await manager.vector_store.store_embedding(
                    test_memory.id, embedding, test_memory.to_dict()
                )
                print(f"✅ Vector store result: {vector_result}")
            except Exception as e:
                print(f"❌ Vector store error: {e}")
        else:
            print("\n6. Skipping vector store test (no embedding)")
            
        # Test graph store  
        print("\n7. Testing graph store...")
        try:
            graph_result = await manager.graph_store.add_memory_node(test_memory)
            print(f"✅ Graph store result: {graph_result}")
        except Exception as e:
            print(f"❌ Graph store error: {e}")
            
        print("\n" + "=" * 50)
        print("✅ Storage component testing completed")
        
    except Exception as e:
        print(f"❌ Fatal error during testing: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_storage_components())
