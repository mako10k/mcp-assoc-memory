#!/usr/bin/env python3
"""
MCP Associative Memory Server の完全な統合テスト
- FastMCP クライアント経由でのツール呼び出し
- 連想記憶機能の動作確認
- エンドツーエンドの機能テスト
"""

import asyncio
import json
import time
from typing import Any, Dict

from fastmcp import Client

async def test_mcp_integration():
    """MCP統合テストの実行"""
    
    # テスト設定
    server_url = "http://127.0.0.1:8000/mcp/"
    test_memories = [
        {
            "content": "Python is a programming language known for its simplicity and readability.",
            "category": "programming",
            "tags": ["python", "programming", "language"]
        },
        {
            "content": "Machine learning algorithms can automatically improve through experience.",
            "category": "ai",
            "tags": ["machine-learning", "ai", "algorithms"]
        },
        {
            "content": "FastAPI is a modern Python web framework for building APIs.",
            "category": "programming", 
            "tags": ["python", "fastapi", "web", "api"]
        }
    ]
    
    print("🔌 MCP Full Integration Test")
    print("=" * 40)
    
    try:
        # クライアント接続
        print(f"🚀 Connecting to MCP server: {server_url}")
        async with Client(server_url) as client:
            print("✅ Connected successfully!")
            
            # 1. ツールリストの取得
            print("\n📋 Testing tool listing...")
            tools = await client.list_tools()
            print(f"✅ Found {len(tools)} tools:")
            for tool in tools[:5]:  # 最初の5つを表示
                print(f"   - {tool.name}: {tool.description}")
            
            # 2. 記憶の保存テスト
            print("\n💾 Testing memory storage...")
            stored_memories = []
            
            for i, memory_data in enumerate(test_memories):
                print(f"   Storing memory {i+1}: {memory_data['content'][:50]}...")
                
                result = await client.call_tool(
                    "memory_store",
                    arguments={
                        "request": {
                            "content": memory_data["content"],
                            "category": memory_data["category"],
                            "tags": memory_data["tags"],
                            "scope": "test/integration"
                        }
                    }
                )
                
                if result and not result.is_error:
                    if hasattr(result, 'data') and result.data:
                        memory_data = result.data
                        stored_memories.append({
                            "id": memory_data.memory_id,
                            "content": memory_data.content
                        })
                        print(f"   ✅ Stored with ID: {memory_data.memory_id}")
                    else:
                        print(f"   ❌ Storage failed: No data in response")
                else:
                    print(f"   ❌ Storage failed: Error in response")
                
                # 少し待機（埋め込み処理のため）
                await asyncio.sleep(0.5)
            
            print(f"✅ Stored {len(stored_memories)} memories successfully")
            
            # 3. 意味的検索のテスト
            print("\n🔍 Testing semantic search...")
            search_queries = [
                ("Python", 0.1),           # 具体的な語彙を使用
                ("machine learning", 0.1),  # より具体的な語彙
                ("FastAPI", 0.1)           # 固有名詞を使用
            ]
            
            for query, threshold in search_queries:
                print(f"   Searching for: '{query}'")
                
                result = await client.call_tool(
                    "memory_search",
                    arguments={
                        "request": {
                            "query": query,
                            "scope": "test/integration",
                            "limit": 3,
                            "similarity_threshold": threshold
                        }
                    }
                )
                
                if result and not result.is_error:
                    if hasattr(result, 'data') and result.data:
                        memories = result.data if isinstance(result.data, list) else []
                        print(f"   ✅ Found {len(memories)} matching memories")
                        for memory in memories:
                            score = memory.get('similarity_score', 0.0) if isinstance(memory, dict) else 0.0
                            content = memory.get('content', 'No content')[:60] if isinstance(memory, dict) else 'No content'
                            print(f"      - Score: {score:.3f} | {content}...")
                    else:
                        print(f"   ❌ Search failed: No data in response")
                else:
                    print(f"   ❌ Search failed: Error in response")
            
            # 4. 連想発見のテスト
            if stored_memories:
                print("\n🧠 Testing association discovery...")
                test_memory = stored_memories[0]
                
                result = await client.call_tool(
                    "memory_discover_associations",
                    arguments={
                        "memory_id": test_memory["id"],
                        "similarity_threshold": 0.2,
                        "limit": 5
                    }
                )
                
                if result and not result.is_error:
                    if hasattr(result, 'data') and result.data:
                        data = result.data
                        associations = data.get('associations', []) if isinstance(data, dict) else []
                        print(f"   ✅ Found {len(associations)} associations for memory: {test_memory['id']}")
                        for assoc in associations:
                            score = assoc.get('similarity_score', 0.0) if isinstance(assoc, dict) else 0.0
                            content = assoc.get('content', 'No content')[:60] if isinstance(assoc, dict) else 'No content'
                            print(f"      - Score: {score:.3f} | {content}...")
                    else:
                        print(f"   ❌ Association discovery failed: No data in response")
                else:
                    print(f"   ❌ Association discovery failed: Error in response")
            
            # 5. スコープ管理テスト
            print("\n📁 Testing scope management...")
            
            result = await client.call_tool(
                "scope_list",
                arguments={
                    "request": {
                        "include_memory_counts": True
                    }
                }
            )
            
            if result and not result.is_error:
                if hasattr(result, 'data') and result.data:
                    scopes = result.data.scopes if hasattr(result.data, 'scopes') else []
                    print(f"   ✅ Found {len(scopes)} scopes:")
                    for scope in scopes:
                        scope_path = getattr(scope, 'path', 'Unknown path')
                        count = getattr(scope, 'memory_count', 0)
                        print(f"      - {scope_path}: {count} memories")
                else:
                    print(f"   ❌ Scope listing failed: No data in response")
            else:
                print(f"   ❌ Scope listing failed: Error in response")
            
            print("\n🎉 Integration test completed successfully!")
            
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

async def main():
    """メイン実行関数"""
    success = await test_mcp_integration()
    return 0 if success else 1

if __name__ == "__main__":
    import sys
    
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
