"""
FastMCPクライアントを使用したテストスクリプト
"""

import asyncio
import json
from fastmcp import Client

async def test_memory_operations():
    """メモリ操作をテストする"""
    
    # FastMCPクライアントを使用してサーバーに接続
    async with Client("http://localhost:8000/mcp") as client:
        print("FastMCPサーバーに接続しました")
        
        # 利用可能なツールの一覧を取得
        tools = await client.list_tools()
        print(f"利用可能なツール: {[tool.name for tool in tools]}")
        
        # テストデータ
        memories = [
            {"content": "テスト用メモリA", "domain": "user", "metadata": {"tag": "similar_test"}},
            {"content": "テスト用メモリAです", "domain": "user", "metadata": {"tag": "similar_test"}},
            {"content": "テスト用メモリAの詳細", "domain": "user", "metadata": {"tag": "similar_test"}},
        ]
        
        stored_memory_ids = []
        
        # メモリを保存
        for i, mem in enumerate(memories):
            print(f"\n[{i + 1}/{len(memories)}] 記憶を保存: {mem['content']}")
            
            result = await client.call_tool("memory_store", {"request": mem})
            print(f"保存結果: {result.content}")
            
            # 構造化された出力からmemory_idを取得
            if hasattr(result, 'structured_content') and result.structured_content:
                memory_id = result.structured_content.get('memory_id')
                if memory_id:
                    stored_memory_ids.append(memory_id)
                    print(f"Memory ID: {memory_id}")
        
        print(f"\n保存されたメモリID: {stored_memory_ids}")
        
        # 検索をテスト
        print("\n=== 検索テスト ===")
        search_result = await client.call_tool("memory_search", {
            "request": {
                "query": "テスト用メモリA",
                "domain": "user",
                "limit": 10
            }
        })
        print(f"検索結果: {search_result.content}")
        
        # 全記憶の一覧を取得
        print("\n=== 全記憶一覧 ===")
        list_result = await client.call_tool("memory_list_all", {})
        print(f"全記憶: {list_result.content}")
        
        # 特定のメモリを取得
        if stored_memory_ids:
            print(f"\n=== 特定記憶取得: {stored_memory_ids[0]} ===")
            get_result = await client.call_tool("memory_get", {"memory_id": stored_memory_ids[0]})
            print(f"取得結果: {get_result.content}")
        
        print("\nテスト完了")

if __name__ == "__main__":
    asyncio.run(test_memory_operations())
