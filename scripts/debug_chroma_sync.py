#!/usr/bin/env python3
"""
ChromaDBとメタデータストアの同期状態をデバッグするスクリプト
"""

import asyncio
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from mcp_assoc_memory.core.memory_manager import MemoryManager
from mcp_assoc_memory.core.embedding_service import EmbeddingService
from mcp_assoc_memory.storage.vector_store import ChromaVectorStore
from mcp_assoc_memory.storage.metadata_store import SQLiteMetadataStore
from mcp_assoc_memory.storage.graph_store import NetworkXGraphStore


async def debug_sync_state():
    """ChromaDBとメタデータストアの同期状態をデバッグ"""
    
    print("🔍 ChromaDBとメタデータストアの同期状態デバッグ")
    print("=" * 60)
    
    # コンポーネント初期化
    vector_store = ChromaVectorStore(persist_directory="./data/chroma_db")
    metadata_store = SQLiteMetadataStore(database_path="./data/memory.db")
    graph_store = NetworkXGraphStore()
    
    # 初期化
    await vector_store.initialize()
    await metadata_store.initialize()
    await graph_store.initialize()
    
    print(f"📊 Vector Store Collection: {vector_store.collection}")
    
    # メタデータストアの全メモリを取得（全スコープから）
    metadata_memories = await metadata_store.get_memories_by_scope(None, limit=10000)
    print(f"📝 Metadata Store Memories: {len(metadata_memories)}")
    
    # スコープ情報を表示
    scope_counts = {}
    for memory in metadata_memories:
        scope = memory.metadata.get('scope', 'unknown')
        scope_counts[scope] = scope_counts.get(scope, 0) + 1
    
    print(f"📊 Scope Distribution:")
    for scope, count in sorted(scope_counts.items()):
        print(f"   {scope}: {count} memories")
    
    # Get all vectors from ChromaDB
    chroma_memory_ids = set()
    for scope, collection in vector_store.collections.items():
        try:
            result = collection.get()
            scope_ids = result.get('ids', [])
            chroma_memory_ids.update(scope_ids)
            print(f"🔗 ChromaDB {scope} scope: {len(scope_ids)} vectors")
            if len(scope_ids) > 0:
                print(f"   Sample IDs: {scope_ids[:3]}")
                # ChromaDB metadata sample
                sample_result = collection.get(ids=scope_ids[:1], include=["metadatas"])
                if sample_result.get('metadatas'):
                    sample_metadata = sample_result['metadatas'][0]
                    print(f"   Sample metadata: {sample_metadata}")
        except Exception as e:
            print(f"❌ Error accessing {scope} collection: {e}")
    
    print(f"🔗 Total ChromaDB Memory IDs: {len(chroma_memory_ids)}")
    
    # Check metadata and vector synchronization
    metadata_ids = {m.id for m in metadata_memories}
    
    print("\n🔄 同期状態チェック:")
    print(f"   メタデータのみ (ChromaDBにない): {len(metadata_ids - chroma_memory_ids)}")
    print(f"   ChromaDBのみ (メタデータにない): {len(chroma_memory_ids - metadata_ids)}")
    print(f"   同期済み: {len(metadata_ids & chroma_memory_ids)}")
    
    # ChromaDBにのみ存在するIDを表示（削除されていないベクトル）
    orphaned_vectors = chroma_memory_ids - metadata_ids
    if orphaned_vectors:
        print(f"\n⚠️  孤立したChromaDBベクトル ({len(orphaned_vectors)}個):")
        for i, vid in enumerate(list(orphaned_vectors)[:10]):  # 最初の10個を表示
            print(f"   {i+1}. {vid}")
        if len(orphaned_vectors) > 10:
            print(f"   ... and {len(orphaned_vectors) - 10} more")
    
    # メタデータにのみ存在するID（エンベディングが削除された）
    missing_vectors = metadata_ids - chroma_memory_ids
    if missing_vectors:
        print(f"\n⚠️  ベクトルが欠落したメタデータ ({len(missing_vectors)}個):")
        for i, mid in enumerate(list(missing_vectors)[:10]):
            print(f"   {i+1}. {mid}")
        if len(missing_vectors) > 10:
            print(f"   ... and {len(missing_vectors) - 10} more")
    
    # 特定のメモリIDの削除テスト
    print(f"\n🧪 削除テスト:")
    test_ids = ["be08b812-fd35-4d16-b000-10aa0e6de085", "921c9fa1-df83-4e52-9dbf-f7f47d0cc694"]
    
    for test_id in test_ids:
        metadata_exists = any(m.id == test_id for m in metadata_memories)
        chroma_exists = test_id in chroma_memory_ids
        print(f"   {test_id}:")
        print(f"      メタデータ: {'✅ 存在' if metadata_exists else '❌ 削除済み'}")
        print(f"      ChromaDB: {'✅ 存在' if chroma_exists else '❌ 削除済み'}")
        
        if chroma_exists and not metadata_exists:
            print(f"      🐛 不整合: ChromaDBに残存している削除済みメモリ")


if __name__ == "__main__":
    asyncio.run(debug_sync_state())
