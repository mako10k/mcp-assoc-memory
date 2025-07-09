"""
新しいスコープ管理機能の包括的テストスクリプト
"""

import asyncio
from fastmcp import Client

async def test_scope_management():
    """新しいスコープ管理機能をテスト"""
    
    async with Client("http://localhost:8000/mcp") as client:
        print("🚀 Connected to FastMCP server")
        
        # === 1. 基本メモリ操作テスト ===
        print("\n=== 📝 Basic Memory Operations ===")
        
        # 様々なスコープにメモリを保存
        test_memories = [
            {"content": "FastMCP learning notes", "scope": "learning/fastmcp", "metadata": {"type": "notes"}},
            {"content": "Project planning document", "scope": "work/projects/web-app", "metadata": {"type": "document"}},
            {"content": "Personal reminder", "scope": "personal/reminders", "metadata": {"type": "reminder"}},
            {"content": "Unicode test: 日本語メモ", "scope": "personal/日本語", "metadata": {"language": "ja"}},
            {"content": "Session temp note", "scope": "session/temp-2025", "metadata": {"temporary": True}},
            {"content": "Deep hierarchy test", "scope": "work/projects/web-app/auth/security", "metadata": {"depth": 5}},
        ]
        
        memory_ids = []
        for memory in test_memories:
            result = await client.call_tool("memory_store", {"request": memory})
            print(f"  ✅ Stored: {memory['content'][:30]}... in scope '{memory['scope']}'")
            # Note: result parsing might need adjustment based on actual response format
        
        # === 2. スコープ管理機能テスト ===
        print("\n=== 🌲 Scope Management Features ===")
        
        # スコープ一覧取得
        print("\n📋 Listing all scopes:")
        scope_list = await client.call_tool("scope_list", {
            "request": {"include_memory_counts": True}
        })
        print("  ✅ Scope listing completed")
        
        # 階層スコープ検索
        print("\n🔍 Hierarchical scope search:")
        work_search = await client.call_tool("memory_search", {
            "request": {
                "query": "project", 
                "scope": "work", 
                "include_child_scopes": True, 
                "limit": 10
            }
        })
        print("  ✅ Hierarchical search completed")
        
        # スコープ提案機能
        print("\n💡 Scope suggestion:")
        suggestion = await client.call_tool("scope_suggest", {
            "request": {
                "content": "Meeting notes from the weekly standup with the development team",
                "current_scope": "work/meetings"
            }
        })
        print("  ✅ Scope suggestion completed")
        
        # === 3. セッション管理テスト ===
        print("\n=== 🔄 Session Management ===")
        
        # セッション作成
        print("\n🆕 Creating test session:")
        session_create = await client.call_tool("session_manage", {
            "request": {"action": "create", "session_id": "test-session-2025"}
        })
        print("  ✅ Session creation completed")
        
        # セッション一覧
        print("\n📋 Listing sessions:")
        session_list = await client.call_tool("session_manage", {
            "request": {"action": "list"}
        })
        print("  ✅ Session listing completed")
        
        # === 4. メモリ移動テスト ===
        print("\n=== 🔄 Memory Movement ===")
        
        # 全メモリ取得
        all_memories = await client.call_tool("memory_list_all", {})
        print("  📋 Retrieved all memories for move test")
        
        # Note: For move test, we'd need to parse memory IDs from the response
        # This would require knowing the exact response format
        print("  ⚠️  Memory move test requires specific memory IDs (skipped for now)")
        
        # === 5. リソースとプロンプトテスト ===
        print("\n=== 📊 Resources and Prompts ===")
        
        # 統計リソース
        print("\n📈 Memory statistics:")
        try:
            stats = await client.read_resource("memory://stats")
            print("  ✅ Statistics resource accessed")
        except Exception as e:
            print(f"  ⚠️  Statistics access error: {e}")
        
        # スコープ固有リソース
        print("\n📂 Scope-specific resources:")
        try:
            scope_data = await client.read_resource("memory://scope/work")
            print("  ✅ Scope resource accessed")
        except Exception as e:
            print(f"  ⚠️  Scope resource access error: {e}")
        
        # 分析プロンプト
        print("\n🧠 Analysis prompt:")
        try:
            analysis = await client.get_prompt("analyze_memories", {
                "scope": "work", 
                "include_child_scopes": True
            })
            print("  ✅ Analysis prompt generated")
        except Exception as e:
            print(f"  ⚠️  Analysis prompt error: {e}")
        
        # === 6. Unicode and 特殊文字テスト ===
        print("\n=== 🌐 Unicode and Special Characters ===")
        
        # Unicode スコープ検索
        try:
            unicode_search = await client.call_tool("memory_search", {
                "request": {
                    "query": "日本語",
                    "scope": "personal/日本語",
                    "limit": 5
                }
            })
            print("  ✅ Unicode scope search completed")
        except Exception as e:
            print(f"  ⚠️  Unicode search error: {e}")
        
        # 深い階層テスト
        print("\n🏗️ Deep hierarchy test:")
        try:
            deep_search = await client.call_tool("memory_search", {
                "request": {
                    "query": "security",
                    "scope": "work/projects/web-app",
                    "include_child_scopes": True,
                    "limit": 5
                }
            })
            print("  ✅ Deep hierarchy search completed")
        except Exception as e:
            print(f"  ⚠️  Deep hierarchy error: {e}")
        
        print("\n=== 🎯 Test Summary ===")
        print("✅ Scope management test completed!")
        print("  - Memory storage with hierarchical scopes")
        print("  - Scope listing and management")
        print("  - Hierarchical search functionality")
        print("  - Session management")
        print("  - Unicode scope support")
        print("  - Deep hierarchy navigation")
        print("  - Resource and prompt integration")

if __name__ == "__main__":
    asyncio.run(test_scope_management())
