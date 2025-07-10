#!/usr/bin/env python3
"""
ChromaDB状態確認スクリプト
削除機能のデバッグ用
"""

import asyncio
import sys
import os

# プロジェクトルートを追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from mcp_assoc_memory.storage.vector_store import ChromaVectorStore

async def debug_chroma_state():
    """ChromaDB状態をデバッグ"""
    print("🔍 ChromaDB削除機能デバッグ")
    print("=" * 50)
    
    # ChromaVectorStoreインスタンス作成
    vector_store = ChromaVectorStore(persist_directory="./data/chroma_db")
    
    try:
        # Single collection への移行確認
        print(f"Available collection: {vector_store.collection}")
        
        collection = vector_store.collection
        if collection:
            print(f"\n📁 Scope-based Collection:")
            
            # コレクション内のアイテム数確認
            count = collection.count()
            print(f"   Total items: {count}")
            
            if count > 0:
                # 最初の10アイテムのIDを取得
                result = collection.get(limit=min(10, count))
                ids = result.get("ids", [])
                print(f"   Sample IDs: {ids[:5] if len(ids) > 5 else ids}")
                
                # 削除したはずのIDをチェック
                test_ids = [
                    "be08b812-fd35-4d16-b000-10aa0e6de085",  # 削除したPython記憶
                    "c40cb0c0-854a-4033-8743-15989e64ebcf",  # 削除したPython記憶
                    "4622723d-45ce-43e8-9fbf-efecd8285a11"   # 削除したML記憶
                ]
                
                for test_id in test_ids:
                    # 直接チェック
                    try:
                        direct_result = collection.get(ids=[test_id])
                        if direct_result["ids"]:
                            print(f"   ❌ DELETED MEMORY STILL EXISTS: {test_id}")
                            metadata = direct_result.get('metadatas', [{}])
                            if metadata and metadata[0]:
                                print(f"      Content preview: {str(metadata[0])[:100]}...")
                        else:
                            print(f"   ✅ Memory properly deleted: {test_id}")
                    except Exception as e:
                        print(f"   ✅ Memory properly deleted: {test_id} (not found)")
            else:
                print(f"   📭 Empty collection")
        
        print(f"\n🔄 削除テスト実行")
        # 既知の削除されるべき記憶IDで削除をテスト
        test_delete_id = "be08b812-fd35-4d16-b000-10aa0e6de085"
        result = await vector_store.delete_vector(test_delete_id)
        print(f"   Delete result for {test_delete_id}: {result}")
        
        # 削除後の確認（single collectionベースに変更）
        if vector_store.collection:
            try:
                check_result = vector_store.collection.get(ids=[test_delete_id])
                if check_result["ids"]:
                    print(f"   ❌ STILL EXISTS in collection after delete!")
                else:
                    print(f"   ✅ Properly removed from collection")
            except Exception:
                print(f"   ✅ Not found in collection (expected)")
                
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_chroma_state())
