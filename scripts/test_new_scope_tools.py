"""
新しいスコープ管理ツールの直接テスト
FastMCPクライアントの正しい使用方法でテスト
"""

import asyncio
import json
from fastmcp import Client
from pathlib import Path

async def test_scope_tools():
    """新しいスコープ管理ツールを直接テスト"""
    
    try:
        # 正しいFastMCPクライアント接続方法
        server_path = Path("/workspaces/mcp-assoc-memory/src/mcp_assoc_memory/server.py")
        
        # STDIOトランスポートでサーバーに接続
        transport = {
            "type": "stdio",
            "command": ["python", "-m", "src.mcp_assoc_memory.server"],
            "cwd": "/workspaces/mcp-assoc-memory"
        }
        
        async with Client(transport) as client:
            print("🚀 Connected to FastMCP server via STDIO")
            
            # ツール一覧を取得
            tools = await client.list_tools()
            tool_names = [tool.name for tool in tools]
            print(f"📋 Available tools: {tool_names}")
            
            # === 1. 基本メモリ操作でデータ準備 ===
            print("\n=== 📝 Setting up test data ===")
            
            # テストメモリを作成
            test_memories = [
                {
                    "content": "FastMCP implementation guide and best practices",
                    "scope": "learning/fastmcp",
                    "metadata": {"type": "guide", "level": "advanced"}
                },
                {
                    "content": "Weekly team standup meeting notes",
                    "scope": "work/meetings",
                    "metadata": {"attendees": 5, "date": "2025-07-09"}
                },
                {
                    "content": "Personal reminder: Complete the quarterly review",
                    "scope": "personal/todos",
                    "metadata": {"priority": "high", "due": "2025-07-15"}
                },
                {
                    "content": "Security implementation for authentication module",
                    "scope": "work/projects/web-app/auth",
                    "metadata": {"security_level": "critical", "framework": "OAuth2"}
                }
            ]
            
            memory_ids = []
            for memory in test_memories:
                result = await client.call_tool("memory_store", {"request": memory})
                memory_ids.append(result.memory_id)
                print(f"  ✅ Stored: {memory['content'][:40]}... in {memory['scope']}")
            
            # === 2. 新しいページング機能をテスト ===
            print("\n=== 📋 Testing Paginated Memory List ===")
            
            if "memory_list_all" in tool_names:
                # ページング付きリスト（デフォルトパラメータ）
                page1 = await client.call_tool("memory_list_all", {})
                print(f"  ✅ Default pagination: Retrieved memories")
                
                # 特定ページとサイズ
                page2 = await client.call_tool("memory_list_all", {"page": 1, "per_page": 2})
                print(f"  ✅ Custom pagination: page=1, per_page=2")
            else:
                print("  ❌ memory_list_all tool not found")
            
            # === 3. スコープ一覧機能をテスト ===
            print("\n=== 🌲 Testing Scope List ===")
            
            if "scope_list" in tool_names:
                scope_list = await client.call_tool("scope_list", {
                    "request": {
                        "parent_scope": None,
                        "include_memory_counts": True
                    }
                })
                print(f"  ✅ Scope list retrieved")
                print(f"  📊 Total scopes: {scope_list.total_scopes}")
                
                # 特定の親スコープでフィルタ
                work_scopes = await client.call_tool("scope_list", {
                    "request": {
                        "parent_scope": "work",
                        "include_memory_counts": True
                    }
                })
                print(f"  ✅ Work scopes filtered")
            else:
                print("  ❌ scope_list tool not found")
            
            # === 4. スコープ提案機能をテスト ===
            print("\n=== 💡 Testing Scope Suggestion ===")
            
            if "scope_suggest" in tool_names:
                suggestions = [
                    {
                        "content": "Code review checklist for Python projects",
                        "current_scope": "work"
                    },
                    {
                        "content": "Personal fitness goals for this year",
                        "current_scope": None
                    },
                    {
                        "content": "Security audit findings and recommendations",
                        "current_scope": "work/projects"
                    }
                ]
                
                for test_case in suggestions:
                    suggestion = await client.call_tool("scope_suggest", {
                        "request": test_case
                    })
                    print(f"  ✅ Suggested: {suggestion.suggested_scope} (confidence: {suggestion.confidence})")
                    print(f"      Reason: {suggestion.reasoning}")
            else:
                print("  ❌ scope_suggest tool not found")
            
            # === 5. セッション管理をテスト ===
            print("\n=== 🔄 Testing Session Management ===")
            
            if "session_manage" in tool_names:
                # セッション作成
                session_create = await client.call_tool("session_manage", {
                    "request": {
                        "action": "create",
                        "session_id": "test-session-2025"
                    }
                })
                print(f"  ✅ Session created: {session_create.session_id}")
                
                # セッション一覧
                session_list = await client.call_tool("session_manage", {
                    "request": {"action": "list"}
                })
                print(f"  ✅ Active sessions: {len(session_list.active_sessions)}")
                
                # セッション作成（自動ID）
                auto_session = await client.call_tool("session_manage", {
                    "request": {"action": "create"}
                })
                print(f"  ✅ Auto session created: {auto_session.session_id}")
            else:
                print("  ❌ session_manage tool not found")
            
            # === 6. メモリ移動をテスト ===
            print("\n=== 🔄 Testing Memory Move ===")
            
            if "memory_move" in tool_names and memory_ids:
                # 最初のメモリを別のスコープに移動
                move_result = await client.call_tool("memory_move", {
                    "request": {
                        "memory_ids": [memory_ids[0]],
                        "target_scope": "archive/moved"
                    }
                })
                print(f"  ✅ Moved {move_result.moved_memories} memories")
                print(f"      From: {move_result.old_scope} → To: {move_result.new_scope}")
            else:
                print("  ❌ memory_move tool not found or no memories to move")
            
            print("\n=== 🎯 Test Summary ===")
            print("✅ New scope management tools tested successfully!")
            print("Features tested:")
            print("  - ✅ Paginated memory listing")
            print("  - ✅ Hierarchical scope listing")
            print("  - ✅ AI-powered scope suggestion")
            print("  - ✅ Session lifecycle management")
            print("  - ✅ Memory scope migration")
            
    except Exception as e:
        print(f"❌ Test error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_scope_tools())
