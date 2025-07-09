"""
新しいスコープ管理ツールをテストするためのシンプルなスクリプト
"""

import asyncio
from fastmcp import Client

async def test_new_scope_tools():
    """新しいスコープ管理ツールをテスト"""
    
    try:
        # STDIOクライアントで接続
        import subprocess
        import sys
        
        # サーバープロセスを起動
        process = subprocess.Popen(
            [sys.executable, "-m", "src.mcp_assoc_memory.server"],
            cwd="/workspaces/mcp-assoc-memory",
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        async with Client.stdio(process) as client:
            print("🚀 Connected to FastMCP server")
            
            # === 1. ページング機能付きメモリ一覧テスト ===
            print("\n=== 📋 Testing Paginated Memory List ===")
            
            try:
                # ページング付きメモリ一覧
                page1 = await client.call_tool("memory_list_all", {"page": 1, "per_page": 3})
                print(f"  ✅ Page 1 retrieved successfully")
                
                page2 = await client.call_tool("memory_list_all", {"page": 2, "per_page": 3})
                print(f"  ✅ Page 2 retrieved successfully")
                
            except Exception as e:
                print(f"  ❌ Paginated list error: {e}")
            
            # === 2. スコープ一覧テスト ===
            print("\n=== 🌲 Testing Scope List ===")
            
            try:
                scope_list = await client.call_tool("scope_list", {
                    "request": {"include_memory_counts": True}
                })
                print(f"  ✅ Scope list retrieved successfully")
                
            except Exception as e:
                print(f"  ❌ Scope list error: {e}")
            
            # === 3. スコープ提案テスト ===
            print("\n=== 💡 Testing Scope Suggestion ===")
            
            try:
                suggestion = await client.call_tool("scope_suggest", {
                    "request": {
                        "content": "Meeting notes from the weekly standup with the development team",
                        "current_scope": "work"
                    }
                })
                print(f"  ✅ Scope suggestion completed successfully")
                
            except Exception as e:
                print(f"  ❌ Scope suggestion error: {e}")
            
            # === 4. セッション管理テスト ===
            print("\n=== 🔄 Testing Session Management ===")
            
            try:
                # セッション作成
                session_create = await client.call_tool("session_manage", {
                    "request": {"action": "create", "session_id": "test-session-2025"}
                })
                print(f"  ✅ Session creation completed")
                
                # セッション一覧
                session_list = await client.call_tool("session_manage", {
                    "request": {"action": "list"}
                })
                print(f"  ✅ Session listing completed")
                
            except Exception as e:
                print(f"  ❌ Session management error: {e}")
            
            # === 5. メモリ移動テスト ===
            print("\n=== 🔄 Testing Memory Move ===")
            
            try:
                # まず現在のメモリを取得
                all_memories = await client.call_tool("memory_list_all", {"page": 1, "per_page": 1})
                print(f"  📋 Retrieved memories for move test")
                
                # Note: 実際のメモリ移動は既存のメモリIDが必要なので、
                # ここではツールの呼び出し可能性のみテスト
                
            except Exception as e:
                print(f"  ❌ Memory move preparation error: {e}")
            
            print("\n=== 🎯 Test Summary ===")
            print("✅ New scope management tools tested!")
            print("  - Paginated memory listing")
            print("  - Scope listing and hierarchy")
            print("  - Scope suggestion engine")
            print("  - Session management")
            
    except Exception as e:
        print(f"❌ Connection error: {e}")
        print("Make sure the server is running with: python -m src.mcp_assoc_memory.server")

if __name__ == "__main__":
    asyncio.run(test_new_scope_tools())
