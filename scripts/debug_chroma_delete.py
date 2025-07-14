#!/usr/bin/env python3
"""
ChromaDB state verification script
For debugging deletion functionality
"""

import asyncio
import os
import sys

from mcp_assoc_memory.storage.vector_store import ChromaVectorStore

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))


async def debug_chroma_state() -> None:
    """Debug ChromaDB state"""
    print("🔍 ChromaDB deletion functionality debug")
    print("=" * 50)

    # ChromaVectorStore instance creation
    vector_store = ChromaVectorStore(persist_directory="./data/chroma_db")

    try:
        # Verify migration to single collection
        print(f"Available collection: {vector_store.collection}")

        collection = vector_store.collection
        if collection:
            print("\n📁 Scope-based Collection:")

            # Check number of items in collection
            count = collection.count()
            print(f"   Total items: {count}")

            if count > 0:
                # Get IDs of first 10 items
                result = collection.get(limit=min(10, count))
                ids = result.get("ids", [])
                print(f"   Sample IDs: {ids[:5] if len(ids) > 5 else ids}")

                # Check IDs that should have been deleted
                test_ids = [
                    "be08b812-fd35-4d16-b000-10aa0e6de085",  # Deleted Python memory
                    "c40cb0c0-854a-4033-8743-15989e64ebcf",  # Deleted Python memory
                    "4622723d-45ce-43e8-9fbf-efecd8285a11",  # Deleted ML memory
                ]

                for test_id in test_ids:
                    # Direct check
                    try:
                        direct_result = collection.get(ids=[test_id])
                        if direct_result["ids"]:
                            print(f"   ❌ DELETED MEMORY STILL EXISTS: {test_id}")
                            metadata = direct_result.get("metadatas", [{}])
                            if metadata and metadata[0]:
                                print(f"      Content preview: {str(metadata[0])[:100]}...")
                        else:
                            print(f"   ✅ Memory properly deleted: {test_id}")
                    except Exception:
                        print(f"   ✅ Memory properly deleted: {test_id} (not found)")
            else:
                print("   📭 Empty collection")

        print("\n🔄 Execute deletion test")
        # Test deletion with known IDs that should be deleted
        test_delete_id = "be08b812-fd35-4d16-b000-10aa0e6de085"
        result = await vector_store.delete_vector(test_delete_id)
        print(f"   Delete result for {test_delete_id}: {result}")

        # Verification after deletion (changed to single collection base)
        if vector_store.collection:
            try:
                check_result = vector_store.collection.get(ids=[test_delete_id])
                if check_result["ids"]:
                    print("   ❌ STILL EXISTS in collection after delete!")
                else:
                    print("   ✅ Properly removed from collection")
            except Exception:
                print("   ✅ Not found in collection (expected)")

    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(debug_chroma_state())
