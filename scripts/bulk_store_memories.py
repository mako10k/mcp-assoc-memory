import json
import time

import requests

MCP_URL = "http://localhost:3006/mcp"

# テスト用記憶データリスト
memories = [
    {"content": "テスト用メモリA", "metadata": {"tag": "test", "purpose": "bulk"}},
    {"content": "テスト用メモリB", "metadata": {"tag": "test", "purpose": "bulk"}},
    {"content": "テスト用メモリC", "metadata": {"tag": "test", "purpose": "bulk"}},
    {"content": "テスト用メモリD", "metadata": {"tag": "test", "purpose": "bulk"}},
    {"content": "テスト用メモリAの類似文", "metadata": {"tag": "test", "purpose": "bulk"}},
    {"content": "これは全く違う内容です", "metadata": {"tag": "other", "purpose": "bulk"}},
    {"content": "テスト用メモリBの関連文", "metadata": {"tag": "test", "purpose": "bulk"}},
    {"content": "テスト用メモリCの追加文", "metadata": {"tag": "test", "purpose": "bulk"}}
]

results = []
for i, mem in enumerate(memories):
    store_request = {
        "tool": "memory",
        "action": "store",
        "params": {
            "domain": "user",
            "content": mem["content"],
            "metadata": mem["metadata"]
        }
    }
    print(f"[{i + 1}/{len(memories)}] POST {MCP_URL} : {mem['content']}")
    response = requests.post(MCP_URL, json=store_request, timeout=10)
    try:
        resp_json = response.json()
        print(json.dumps(resp_json, indent=2, ensure_ascii=False))
        results.append(resp_json)
    except Exception as e:
        print(f"Response decode error: {e}\nRaw: {response.text}")
    time.sleep(0.5)  # サーバ負荷軽減のため少し待つ

print("\n保存されたmemory_id一覧:")
for r in results:
    if r.get("success") and r.get("data"):
        print(r["data"].get("memory_id"))
