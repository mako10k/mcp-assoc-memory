#!/usr/bin/env python3
"""
ChromaDBとメタデータストアを同期させるクリーンアップスクリプト
"""

import asyncio
import os
import sys

from mcp_assoc_memory.storage.metadata_store import SQLiteMetadataStore
from mcp_assoc_memory.storage.vector_store import ChromaVectorStore

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


async def cleanup_orphaned_vectors():
    """孤立したベクトルをクリーンアップ"""

    print("🧹 ChromaDBクリーンアップ - 孤立したベクトルを削除")
    print("=" * 60)

    # コンポーネント初期化
    vector_store = ChromaVectorStore(persist_directory="./data/chroma_db")
    metadata_store = SQLiteMetadataStore(database_path="./data/memory.db")

    # 初期化
    await vector_store.initialize()
    await metadata_store.initialize()

    # メタデータストアの全メモリを取得
    metadata_memories = await metadata_store.get_memories_by_scope(None, limit=10000)
    metadata_ids = {m.id for m in metadata_memories}
    print(f"📝 Metadata Store Memories: {len(metadata_ids)}")

    # ChromaDBの全ベクトルを取得
    chroma_memory_ids = set()
    orphaned_by_scope = {}

    for scope, collection in vector_store.collections.items():
        try:
            result = collection.get()
            scope_ids = result.get("ids", [])
            chroma_memory_ids.update(scope_ids)

            # このスコープの孤立したベクトルを特定
            scope_orphaned = set(scope_ids) - metadata_ids
            if scope_orphaned:
                orphaned_by_scope[scope] = scope_orphaned
                print(f"🔗 ChromaDB {scope} scope: {len(scope_ids)} vectors, {len(scope_orphaned)} orphaned")
            else:
                print(f"🔗 ChromaDB {scope} scope: {len(scope_ids)} vectors, no orphaned")

        except Exception as e:
            print(f"❌ Error accessing {scope} collection: {e}")

    # 孤立したベクトルの削除
    total_orphaned = sum(len(orphaned) for orphaned in orphaned_by_scope.values())
    if total_orphaned == 0:
        print("✅ 孤立したベクトルは見つかりませんでした")
        return

    print(f"\n⚠️  {total_orphaned}個の孤立したベクトルを削除します:")

    deleted_count = 0
    for scope, orphaned_ids in orphaned_by_scope.items():
        collection = vector_store.collections[scope]
        print(f"\n🗑️  {scope} scope から {len(orphaned_ids)}個のベクトルを削除:")

        for memory_id in orphaned_ids:
            try:
                collection.delete(ids=[memory_id])
                print(f"   ✅ 削除: {memory_id}")
                deleted_count += 1
            except Exception as e:
                print(f"   ❌ 削除失敗: {memory_id} - {e}")

    print(f"\n🎉 クリーンアップ完了: {deleted_count}/{total_orphaned}個のベクトルを削除しました")

    # 削除後の状態確認
    print("\n📊 削除後の状態:")
    for domain, collection in vector_store.collections.items():
        try:
            result = collection.get()
            remaining_count = len(result.get("ids", []))
            print(f"   {domain}: {remaining_count} vectors remaining")
        except Exception as e:
            print(f"   {domain}: Error - {e}")


if __name__ == "__main__":
    asyncio.run(cleanup_orphaned_vectors())
