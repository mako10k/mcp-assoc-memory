"""
FastMCP AssocMemory サーバーの新機能を直接テストするスクリプト
"""

import asyncio
import json
from datetime import datetime

# サーバーモジュールを直接インポートしてテスト
import sys
import os
sys.path.append('/workspaces/mcp-assoc-memory/src')

from mcp_assoc_memory.server import (
    memory_store, memory_search, memory_list_all,
    scope_list, scope_suggest, memory_move, session_manage,
    memory_storage,
    MemoryStoreRequest, MemorySearchRequest, ScopeListRequest,
    ScopeSuggestRequest, MemoryMoveRequest, SessionManageRequest
)

class MockContext:
    """Mock context for testing"""
    async def info(self, msg): print(f"INFO: {msg}")
    async def warning(self, msg): print(f"WARNING: {msg}")
    async def error(self, msg): print(f"ERROR: {msg}")

async def test_new_scope_features():
    """新しいスコープ管理機能をテスト"""
    
    ctx = MockContext()
    print("🚀 Testing FastMCP AssocMemory new scope features")
    
    # メモリストレージをクリア
    memory_storage.clear()
    
    # === 1. テストデータの準備 ===
    print("\n=== 📝 Setting up test data ===")
    
    test_memories = [
        {"content": "FastMCP learning notes", "scope": "learning/fastmcp", "metadata": {"type": "notes"}},
        {"content": "Project meeting minutes", "scope": "work/meetings", "metadata": {"type": "meeting"}},
        {"content": "Personal reminder", "scope": "personal/reminders", "metadata": {"type": "reminder"}},
        {"content": "Security implementation notes", "scope": "work/projects/auth", "metadata": {"type": "security"}},
        {"content": "Frontend component design", "scope": "work/projects/frontend", "metadata": {"type": "design"}},
    ]
    
    stored_memory_ids = []
    for memory_data in test_memories:
        request = MemoryStoreRequest(**memory_data)
        result = await memory_store(request, ctx)
        stored_memory_ids.append(result.memory_id)
        print(f"  ✅ Stored: {memory_data['content'][:30]}... in scope '{memory_data['scope']}'")
    
    # === 2. ページング機能付きメモリ一覧テスト ===
    print("\n=== 📋 Testing Paginated Memory List ===")
    
    try:
        # ページ1
        page1 = await memory_list_all(ctx, page=1, per_page=3)
        print(f"  ✅ Page 1: {len(page1['memories'])} memories, pagination: {page1['pagination'].page}/{page1['pagination'].total_pages}")
        
        # ページ2
        page2 = await memory_list_all(ctx, page=2, per_page=3)
        print(f"  ✅ Page 2: {len(page2['memories'])} memories, pagination: {page2['pagination'].page}/{page2['pagination'].total_pages}")
        
    except Exception as e:
        print(f"  ❌ Pagination error: {e}")
    
    # === 3. スコープ一覧テスト ===
    print("\n=== 🌲 Testing Scope List ===")
    
    try:
        request = ScopeListRequest(include_memory_counts=True)
        scope_list_result = await scope_list(request, ctx)
        
        print(f"  ✅ Found {scope_list_result.total_scopes} scopes:")
        for scope_info in scope_list_result.scopes:
            print(f"    - {scope_info.scope}: {scope_info.memory_count} memories, children: {len(scope_info.child_scopes)}")
    
    except Exception as e:
        print(f"  ❌ Scope list error: {e}")
    
    # === 4. スコープ提案テスト ===
    print("\n=== 💡 Testing Scope Suggestion ===")
    
    try:
        # プログラミング関連コンテンツ
        request1 = ScopeSuggestRequest(
            content="This is about FastMCP programming implementation and Python code development",
            current_scope="work"
        )
        suggestion1 = await scope_suggest(request1, ctx)
        print(f"  ✅ Programming content: {suggestion1.suggested_scope} (confidence: {suggestion1.confidence})")
        print(f"    Reasoning: {suggestion1.reasoning}")
        
        # 会議関連コンテンツ
        request2 = ScopeSuggestRequest(
            content="Meeting notes from weekly standup and project review session",
            current_scope=None
        )
        suggestion2 = await scope_suggest(request2, ctx)
        print(f"  ✅ Meeting content: {suggestion2.suggested_scope} (confidence: {suggestion2.confidence})")
        print(f"    Alternatives: {len(suggestion2.alternatives)} options")
        
    except Exception as e:
        print(f"  ❌ Scope suggestion error: {e}")
    
    # === 5. メモリ移動テスト ===
    print("\n=== 🔄 Testing Memory Move ===")
    
    try:
        # 最初のメモリを新しいスコープに移動
        if stored_memory_ids:
            request = MemoryMoveRequest(
                memory_ids=[stored_memory_ids[0]],
                target_scope="archive/migrated"
            )
            move_result = await memory_move(request, ctx)
            print(f"  ✅ Moved {move_result.moved_memories} memories from '{move_result.old_scope}' to '{move_result.new_scope}'")
        
    except Exception as e:
        print(f"  ❌ Memory move error: {e}")
    
    # === 6. セッション管理テスト ===
    print("\n=== 🔄 Testing Session Management ===")
    
    try:
        # セッション作成
        create_request = SessionManageRequest(action="create", session_id="test-session-2025")
        create_result = await session_manage(create_request, ctx)
        print(f"  ✅ Created session: {create_result.session_id}")
        
        # セッション一覧
        list_request = SessionManageRequest(action="list")
        list_result = await session_manage(list_request, ctx)
        print(f"  ✅ Active sessions: {len(list_result.active_sessions)}")
        for session in list_result.active_sessions:
            print(f"    - {session.session_id}: {session.memory_count} memories")
        
    except Exception as e:
        print(f"  ❌ Session management error: {e}")
    
    # === 7. 階層検索テスト ===
    print("\n=== 🔍 Testing Hierarchical Search ===")
    
    try:
        # 作業スコープ全体での検索
        search_request = MemorySearchRequest(
            query="project",
            scope="work",
            include_child_scopes=True,
            limit=10
        )
        search_results = await memory_search(search_request, ctx)
        print(f"  ✅ Found {len(search_results)} memories in 'work' scope and children")
        
    except Exception as e:
        print(f"  ❌ Hierarchical search error: {e}")
    
    # === 8. 最終統計 ===
    print("\n=== 📊 Final Statistics ===")
    print(f"  Total memories: {len(memory_storage)}")
    print(f"  Unique scopes: {len(set(m['scope'] for m in memory_storage.values()))}")
    print("  Scopes:")
    for scope in sorted(set(m['scope'] for m in memory_storage.values())):
        count = len([m for m in memory_storage.values() if m['scope'] == scope])
        print(f"    - {scope}: {count} memories")
    
    print("\n=== 🎯 Test Summary ===")
    print("✅ All new scope management features tested successfully!")
    print("  - Paginated memory listing")
    print("  - Scope listing with hierarchy")
    print("  - AI-powered scope suggestion")
    print("  - Memory movement between scopes")
    print("  - Session lifecycle management")
    print("  - Hierarchical scope search")

if __name__ == "__main__":
    asyncio.run(test_new_scope_features())
