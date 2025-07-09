#!/usr/bin/env python3
"""
永続化機能テストスクリプト
サーバー再起動前後でデータが保持されるかテスト
"""

import asyncio
import json
from fastmcp import Client
from pathlib import Path
import uuid

STORAGE_FILE = Path("/workspaces/mcp-assoc-memory/data/memories.json")

async def test_persistence():
    """永続化機能の包括テスト"""
    
    print("🔍 永続化機能テスト開始")
    print("=" * 50)
    
    # 1. 既存データの確認
    print("\n📊 既存データの確認:")
    if STORAGE_FILE.exists():
        with open(STORAGE_FILE, 'r', encoding='utf-8') as f:
            existing_data = json.load(f)
        print(f"  既存メモリ数: {len(existing_data)}")
        for mem_id, data in existing_data.items():
            print(f"    {mem_id[:8]}...: {data['content'][:30]}... (scope: {data['scope']})")
    else:
        print("  データファイルが存在しません")
    
    try:
        # 2. サーバーに接続してデータを追加
        print("\n🚀 サーバーに接続...")
        async with Client("http://localhost:8000/mcp") as client:
            print("✅ 接続成功!")
            
            # 現在のメモリリストを取得
            print("\n📋 現在のメモリリスト:")
            list_result = await client.call_tool("memory_list_all", {
                "page": 1, "per_page": 10
            })
            print(f"  サーバー内メモリ情報: {str(list_result.content)[:200]}...")
            
            # 新しいテストメモリを保存
            test_memory_id = str(uuid.uuid4())
            test_content = f"永続化テスト - {test_memory_id[:8]}"
            
            print(f"\n💾 新しいメモリを保存: {test_content}")
            store_result = await client.call_tool("memory_store", {
                "request": {
                    "content": test_content,
                    "scope": "test/persistence",
                    "metadata": {"test": True, "timestamp": "2025-07-09"}
                }
            })
            print(f"  保存結果: {store_result.content}")
            
            # スコープリストを確認
            print("\n📁 スコープリスト:")
            scope_result = await client.call_tool("scope_list", {
                "request": {"include_memory_counts": True}
            })
            print(f"  スコープ情報: {scope_result.content}")
            
            # 検索テスト
            print("\n🔍 検索テスト:")
            search_result = await client.call_tool("memory_search", {
                "request": {
                    "query": "永続化テスト",
                    "scope": "test",
                    "include_child_scopes": True,
                    "limit": 5
                }
            })
            print(f"  検索結果: {search_result.content}")
            
    except Exception as e:
        print(f"❌ サーバー接続エラー: {e}")
        print("  サーバーが起動していない可能性があります")
        print("  コマンド: python -m src.mcp_assoc_memory")
        return False
    
    # 3. ファイルシステムでデータ確認
    print("\n📄 保存後のファイル状況:")
    if STORAGE_FILE.exists():
        with open(STORAGE_FILE, 'r', encoding='utf-8') as f:
            updated_data = json.load(f)
        print(f"  更新後メモリ数: {len(updated_data)}")
        print(f"  ファイルサイズ: {STORAGE_FILE.stat().st_size} bytes")
        
        # 最近追加されたメモリを表示
        for mem_id, data in list(updated_data.items())[-3:]:
            print(f"    {mem_id[:8]}...: {data['content'][:50]}... (scope: {data['scope']})")
    else:
        print("  ❌ データファイルが作成されていません")
        return False
    
    print("\n✅ 永続化テスト完了!")
    print("\n📚 次のステップ:")
    print("  1. サーバーを再起動")
    print("  2. データが保持されているか確認")
    print("  3. 新しいクライアント接続でデータアクセステスト")
    
    return True


async def test_server_restart_persistence():
    """サーバー再起動後の永続化テスト"""
    
    print("\n🔄 サーバー再起動後の永続化テスト")
    print("=" * 50)
    
    try:
        async with Client("http://localhost:8000/mcp") as client:
            print("✅ 再起動後サーバーに接続成功!")
            
            # データが保持されているか確認
            list_result = await client.call_tool("memory_list_all", {
                "page": 1, "per_page": 20
            })
            print(f"📋 再起動後メモリ情報: {str(list_result.content)[:200]}...")
            
            # 検索で永続化テストデータを確認
            search_result = await client.call_tool("memory_search", {
                "request": {
                    "query": "永続化テスト",
                    "limit": 10
                }
            })
            print(f"🔍 永続化テストデータ検索: {search_result.content}")
            
            return True
            
    except Exception as e:
        print(f"❌ 再起動後接続エラー: {e}")
        return False


if __name__ == "__main__":
    print("🎯 FastMCP永続化機能テスト")
    print("=" * 60)
    
    # 基本永続化テスト
    result = asyncio.run(test_persistence())
    
    if result:
        print("\n" + "="*60)
        print("💡 手動でサーバーを再起動してから次のテストを実行してください：")
        print("   python scripts/test_persistence.py --restart-test")
    else:
        print("\n❌ 永続化テストが失敗しました")
