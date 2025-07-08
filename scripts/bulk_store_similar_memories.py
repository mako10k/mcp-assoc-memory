import requests
import json
import time

MCP_URL = "http://localhost:3006/mcp"

# ほぼ同じ文を複数保存するテストデータ
memories = [
    {"content": "テスト用メモリA"},
    {"content": "テスト用メモリAです"},
    {"content": "テスト用メモリAの詳細"},
    {"content": "テスト用メモリAの補足説明"},
    {"content": "テスト用メモリAの関連情報"},
    {"content": "テスト用メモリAの追加情報"}
]

results = []
for i, mem in enumerate(memories):
    store_request = {
        "tool": "memory",
        "action": "store",
        "params": {
            "domain": "user",
            "content": mem["content"],
            "metadata": {"tag": "similar_test"}
        }
    }
    print(f"[{i+1}/{len(memories)}] POST {MCP_URL} : {mem['content']}")
    response = requests.post(MCP_URL, json=store_request, timeout=10)
    try:
        resp_json = response.json()
        print(json.dumps(resp_json, indent=2, ensure_ascii=False))
        results.append(resp_json)
    except Exception as e:
        print(f"Response decode error: {e}\nRaw: {response.text}")
    time.sleep(0.5)

print("\n保存されたmemory_id一覧:")
for r in results:
    if r.get("success") and r.get("data"):
        print(r["data"].get("memory_id"))
