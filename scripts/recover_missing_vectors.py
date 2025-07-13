#!/usr/bin/env python3
"""
欠損ベクトルの個別復旧スクリプト
メタDBには存在するがベクターDBに欠損しているメモリの埋め込みを再作成します
"""

import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from mcp_assoc_memory.config import Config
from mcp_assoc_memory.core.embedding_service import create_embedding_service
from mcp_assoc_memory.storage.metadata_store import SQLiteMetadataStore
from mcp_assoc_memory.storage.vector_store import ChromaVectorStore


async def recover_missing_vectors():
    """欠損ベクトルを個別に復旧"""
    
    print("🔧 欠損ベクトル個別復旧スクリプト開始")
    print("=" * 60)
    
    # Configuration and services
    config = Config.load()
    metadata_store = SQLiteMetadataStore(config.database.path)
    vector_store = ChromaVectorStore(persist_directory=config.storage.data_dir + "/chroma_db")
    embedding_service = create_embedding_service(config.embedding.__dict__)
    
    # Initialize services
    await metadata_store.initialize()
    await vector_store.initialize()
    
    # Get all memory IDs from both databases
    print("📊 データベース状況を確認中...")
    all_memories = await metadata_store.get_memories_by_scope(None, limit=1000)
    meta_ids = {m.id for m in all_memories}
    
    # Get vector IDs (with proper ChromaDB API usage)
    try:
        if vector_store.collection:
            all_vectors = vector_store.collection.get()
            vector_ids = set(all_vectors['ids']) if all_vectors and all_vectors['ids'] else set()
        else:
            vector_ids = set()
    except Exception as e:
        print(f"ChromaDB取得エラー: {e}")
        vector_ids = set()
    
    # Find missing vectors
    missing_ids = meta_ids - vector_ids
    
    print(f"メタDB: {len(meta_ids)} 件")
    print(f"ベクターDB: {len(vector_ids)} 件")
    print(f"欠損: {len(missing_ids)} 件")
    
    if not missing_ids:
        print("✅ 欠損ベクトルなし - 同期完了")
        return
    
    print(f"\n🔧 {len(missing_ids)} 件の欠損ベクトルを復旧中...")
    
    recovered = 0
    failed = 0
    
    for i, memory_id in enumerate(missing_ids, 1):
        # Get memory from metadata store
        memory = next((m for m in all_memories if m.id == memory_id), None)
        if not memory:
            print(f"[{i:2d}/{len(missing_ids)}] ❌ {memory_id[:8]}... - メタDBから取得失敗")
            failed += 1
            continue
        
        try:
            # Generate embedding
            embedding = await embedding_service.get_embedding(memory.content)
            if embedding is None:
                print(f"[{i:2d}/{len(missing_ids)}] ❌ {memory_id[:8]}... - 埋め込み生成失敗")
                failed += 1
                continue
            
            # Store in vector database
            await vector_store.store_embedding(memory_id, embedding, memory.to_dict())
            print(f"[{i:2d}/{len(missing_ids)}] ✅ {memory_id[:8]}... - {memory.scope} - 復旧完了")
            recovered += 1
            
        except Exception as e:
            print(f"[{i:2d}/{len(missing_ids)}] ❌ {memory_id[:8]}... - エラー: {e}")
            failed += 1
    
    print("\n📊 復旧結果:")
    print(f"  成功: {recovered} 件")
    print(f"  失敗: {failed} 件")
    print(f"  成功率: {recovered / (recovered + failed) * 100:.1f}%")
    
    # Verify final sync
    if vector_store.collection:
        final_vector_count = vector_store.collection.count()
        print(f"\n🎯 最終確認:")
        print(f"  メタDB: {len(meta_ids)} 件")
        print(f"  ベクターDB: {final_vector_count} 件")
        print(f"  差異: {len(meta_ids) - final_vector_count} 件")
        
        if len(meta_ids) == final_vector_count:
            print("🎉 完全同期達成！")
        else:
            print(f"⚠️ まだ {len(meta_ids) - final_vector_count} 件の差異が残存")


if __name__ == "__main__":
    asyncio.run(recover_missing_vectors())
