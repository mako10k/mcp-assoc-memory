"""
FastMCPアノテーション機能のテストスクリプト
"""

import asyncio
import json
from fastmcp import Client

async def test_annotations():
    """アノテーション機能をテストする"""
    
    async with Client("http://localhost:8000/mcp") as client:
        print("🏷️ FastMCPアノテーション機能のテスト")
        
        # ツール一覧を取得してアノテーションを確認
        tools = await client.list_tools()
        
        print("\n=== 📋 ツールアノテーションの詳細 ===")
        for tool in tools:
            print(f"\n🔧 ツール: {tool.name}")
            print(f"   説明: {tool.description}")
            
            # アノテーションがある場合
            if hasattr(tool, 'annotations') and tool.annotations:
                print("   アノテーション:")
                annotations_dict = tool.annotations.model_dump() if hasattr(tool.annotations, 'model_dump') else tool.annotations.__dict__
                for key, value in annotations_dict.items():
                    print(f"     {key}: {value}")
            else:
                print("   アノテーション: なし")
        
        # 実際にツールを呼び出してログ出力を確認
        print("\n=== 🎯 実際のツール呼び出しテスト ===")
        
        # 破壊的でない操作
        print("\n📊 非破壊的操作のテスト (memory_list_all):")
        list_result = await client.call_tool("memory_list_all", {})
        memories = json.loads(list_result.content[0].text)
        print(f"取得された記憶数: {len(memories)}")
        
        # 新しい記憶を保存（非破壊的）
        print("\n💾 記憶保存のテスト (memory_store):")
        store_result = await client.call_tool("memory_store", {
            "request": {
                "content": "アノテーション機能のテスト記憶",
                "domain": "test",
                "metadata": {"test": "annotations"}
            }
        })
        stored_memory = json.loads(store_result.content[0].text)
        print(f"保存された記憶ID: {stored_memory['memory_id']}")
        
        # 検索（読み取り専用）
        print("\n🔍 検索のテスト (memory_search):")
        search_result = await client.call_tool("memory_search", {
            "request": {
                "query": "アノテーション",
                "limit": 5
            }
        })
        found_memories = json.loads(search_result.content[0].text)
        print(f"検索結果: {len(found_memories)}件")
        
        print("\n✅ アノテーションテスト完了")
        print("サーバーログでContext.info()、Context.warning()等の出力を確認してください")

if __name__ == "__main__":
    asyncio.run(test_annotations())
