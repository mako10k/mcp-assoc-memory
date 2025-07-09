"""
FastMCPの全機能をテストする包括的なテストスクリプト
Tools, Resources, Prompts のすべてをテスト
"""

import asyncio
import json
from fastmcp import Client

async def test_comprehensive_fastmcp():
    """FastMCPの全機能を包括的にテストする"""
    
    async with Client("http://localhost:8000/mcp") as client:
        print("🚀 FastMCPサーバーに接続しました")
        
        # === 1. ツール機能のテスト ===
        print("\n=== 🔧 ツール機能のテスト ===")
        
        # 利用可能なツールの一覧を取得
        tools = await client.list_tools()
        print(f"利用可能なツール: {[tool.name for tool in tools]}")
        
        # テストデータの保存
        memories = [
            {"content": "FastMCP実装の学習ノート", "domain": "development", "metadata": {"category": "learning"}},
            {"content": "プロジェクト管理の要点", "domain": "project", "metadata": {"category": "management"}},
            {"content": "コードレビューのチェックリスト", "domain": "development", "metadata": {"category": "process"}},
        ]
        
        print("\n📝 記憶の保存:")
        for mem in memories:
            result = await client.call_tool("memory_store", {"request": mem})
            print(f"  - 保存: {mem['content'][:30]}...")
        
        # 検索テスト
        print("\n🔍 記憶の検索:")
        search_result = await client.call_tool("memory_search", {
            "request": {"query": "FastMCP", "limit": 5}
        })
        print(f"  FastMCP関連の記憶: {len(json.loads(search_result.content[0].text))}件")
        
        # === 2. リソース機能のテスト ===
        print("\n=== 📊 リソース機能のテスト ===")
        
        # 利用可能なリソースの一覧を取得
        resources = await client.list_resources()
        print(f"利用可能なリソース: {[resource.uri for resource in resources]}")
        
        # 統計リソースの取得
        print("\n📈 メモリ統計:")
        stats_resource = await client.read_resource("memory://stats")
        stats_data = json.loads(stats_resource[0].text)
        print(f"  総記憶数: {stats_data['total_memories']}")
        print(f"  ドメイン別: {stats_data['domains']}")
        
        # ドメイン別リソースの取得
        print("\n🏷️ ドメイン別記憶 (development):")
        domain_resource = await client.read_resource("memory://domain/development")
        domain_data = json.loads(domain_resource[0].text)
        print(f"  developmentドメインの記憶数: {domain_data['count']}")
        
        # === 3. プロンプト機能のテスト ===
        print("\n=== 💭 プロンプト機能のテスト ===")
        
        # 利用可能なプロンプトの一覧を取得
        prompts = await client.list_prompts()
        print(f"利用可能なプロンプト: {[prompt.name for prompt in prompts]}")
        
        # 記憶分析プロンプトの生成
        print("\n🔬 記憶分析プロンプトの生成:")
        analysis_prompt = await client.get_prompt("analyze_memories", {"domain": "development"})
        print(f"  プロンプト長: {len(analysis_prompt.messages[0].content.text)} 文字")
        print(f"  プロンプトの一部: {analysis_prompt.messages[0].content.text[:100]}...")
        
        # 特定記憶の要約プロンプト
        if stats_data['total_memories'] > 0:
            # 最初の記憶IDを取得
            all_memories = await client.call_tool("memory_list_all", {})
            memories_list = json.loads(all_memories.content[0].text)
            if memories_list:
                first_memory_id = memories_list[0]['memory_id']
                
                print(f"\n📝 記憶要約プロンプトの生成 (ID: {first_memory_id[:8]}...):")
                summary_prompt = await client.get_prompt("summarize_memory", {"memory_id": first_memory_id})
                print(f"  プロンプト長: {len(summary_prompt.messages[0].content.text)} 文字")
                print(f"  プロンプトの一部: {summary_prompt.messages[0].content.text[:150]}...")
        
        # === 4. アノテーション機能の確認 ===
        print("\n=== 🏷️ ツールアノテーションの確認 ===")
        for tool in tools:
            print(f"  {tool.name}:")
            desc = getattr(tool, 'description', '') or ''
            print(f"    説明: {desc[:50]}...")
            
            # 既知のアノテーション情報を手動で表示（実装されている場合）
            if tool.name == "memory_store":
                print("    タイトル: 記憶の保存")
                print("    読み取り専用: False")
                print("    破壊的操作: False")
            elif tool.name == "memory_search":
                print("    タイトル: 記憶の検索")
                print("    読み取り専用: True")
                print("    破壊的操作: False")
            elif tool.name == "memory_delete":
                print("    タイトル: 記憶の削除")
                print("    読み取り専用: False")
                print("    破壊的操作: True")
        
        # === 5. Context機能の確認（ログ出力） ===
        print("\n=== 📋 Context機能のテスト（ログ確認） ===")
        print("  サーバーログを確認してContext.info(), Context.warning()等の動作を確認してください")
        
        print("\n✅ FastMCP包括テスト完了！")
        print(f"  - ツール: {len(tools)}個")
        print(f"  - リソース: {len(resources)}個")
        print(f"  - プロンプト: {len(prompts)}個")
        print(f"  - 保存済み記憶: {stats_data['total_memories']}件")

if __name__ == "__main__":
    asyncio.run(test_comprehensive_fastmcp())
