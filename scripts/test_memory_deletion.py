#!/usr/bin/env python3
"""
メモリ削除機能のテストスクリプト
"""

import asyncio
import os
import sys

from mcp_assoc_memory.core.embedding_service import EmbeddingService
from mcp_assoc_memory.core.memory_manager import MemoryManager
from mcp_assoc_memory.storage.graph_store import NetworkXGraphStore
from mcp_assoc_memory.storage.metadata_store import SQLiteMetadataStore
from mcp_assoc_memory.storage.vector_store import ChromaVectorStore

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


async def test_memory_deletion():
    """Memory deletion functionality test"""

    print("🧪 Memory deletion functionality test")
    print("=" * 50)

    # Initialize components
    vector_store = ChromaVectorStore(persist_directory="./data/chroma_db")
    metadata_store = SQLiteMetadataStore(database_path="./data/memory.db")
    graph_store = NetworkXGraphStore()
    embedding_service = EmbeddingService()

    # Initialize
    await vector_store.initialize()
    await metadata_store.initialize()
    await graph_store.initialize()
    await embedding_service.initialize()

    # Create MemoryManager
    memory_manager = MemoryManager(
        vector_store=vector_store,
        metadata_store=metadata_store,
        graph_store=graph_store,
        embedding_service=embedding_service,
    )

    # Create test memory
    print("📝 Creating test memory...")
    test_memory = await memory_manager.store_memory(
        scope="test/deletion",
        content="This is a test memory for deletion testing",
        metadata={"test": True},
        tags=["test", "deletion"],
        category="test",
    )

    if not test_memory:
        print("❌ Failed to create test memory")
        return

    test_id = test_memory.id
    print(f"✅ Test memory created: {test_id}")

    # 作成後の確認
    print("🔍 作成後の状態確認...")

    # メタデータ存在確認
    metadata_memory = await metadata_store.get_memory(test_id)
    print(f"   メタデータ: {'✅ 存在' if metadata_memory else '❌ なし'}")

    # Vector existence check
    vector_exists = False
    for scope, collection in vector_store.collections.items():
        try:
            result = collection.get(ids=[test_id])
            if result.get("ids") and test_id in result["ids"]:
                vector_exists = True
                print(f"   Vector: ✅ exists in {scope} scope")
                break
        except Exception:
            continue

    if not vector_exists:
        print("   ベクトル: ❌ なし")

    # 削除実行
    print(f"\n🗑️  メモリ削除実行: {test_id}")
    deletion_result = await memory_manager.delete_memory(test_id)
    print(f"   削除結果: {'✅ 成功' if deletion_result else '❌ 失敗'}")

    # 削除後の確認
    print("🔍 削除後の状態確認...")

    # メタデータ削除確認
    metadata_memory_after = await metadata_store.get_memory(test_id)
    print(f"   メタデータ: {'❌ 削除済み' if not metadata_memory_after else '⚠️  残存'}")

    # Vector deletion check
    vector_exists_after = False
    for scope, collection in vector_store.collections.items():
        try:
            result = collection.get(ids=[test_id])
            if result.get("ids") and test_id in result["ids"]:
                vector_exists_after = True
                print(f"   Vector: ⚠️  still exists in {scope} scope")
                break
        except Exception:
            continue

    if not vector_exists_after:
        print("   Vector: ✅ deleted")

    # Detailed test of deletion function
    print("\n🔧 Detailed vector deletion test...")
    if vector_exists_after:
        # Call delete_vector directly
        direct_deletion = await vector_store.delete_vector(test_id)
        print(f"   Direct deletion result: {'✅ success' if direct_deletion else '❌ failure'}")

        # Final check
        final_vector_exists = False
        for scope, collection in vector_store.collections.items():
            try:
                result = collection.get(ids=[test_id])
                if result.get("ids") and test_id in result["ids"]:
                    final_vector_exists = True
                    print(f"   Final check: ⚠️  still exists in {scope} scope")
                    break
            except Exception:
                continue

        if not final_vector_exists:
            print("   Final check: ✅ deleted")


if __name__ == "__main__":
    asyncio.run(test_memory_deletion())
