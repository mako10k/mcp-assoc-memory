import json
import time

import requests

MCP_URL = "http://localhost:8000/mcp"

# ほぼ同じ文を複数保存するテストデータ
memories = [
    {"content": "テスト用メモリA", "domain": "user", "metadata": {"tag": "similar_test"}},
    {"content": "テスト用メモリAです", "domain": "user", "metadata": {"tag": "similar_test"}},
    {"content": "テスト用メモリAの詳細", "domain": "user", "metadata": {"tag": "similar_test"}},
    {"content": "テスト用メモリAの補足説明", "domain": "user", "metadata": {"tag": "similar_test"}},
    {"content": "テスト用メモリAの関連情報", "domain": "user", "metadata": {"tag": "similar_test"}},
    {"content": "テスト用メモリAの追加情報", "domain": "user", "metadata": {"tag": "similar_test"}}
]

results = []
for i, mem in enumerate(memories):
    # FastMCP形式のリクエスト
    store_request = {
        "jsonrpc": "2.0",
        "id": i + 1,
        "method": "tools/call",
        "params": {
            "name": "memory_store",
            "arguments": {
                "request": mem
            }
        }
    }
    print(f"[{i + 1}/{len(memories)}] POST {MCP_URL} : {mem['content']}")
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream"
    }
    response = requests.post(MCP_URL, json=store_request, headers=headers, timeout=10)
    try:
        resp_json = response.json()
        print(json.dumps(resp_json, indent=2, ensure_ascii=False))
        results.append(resp_json)
    except Exception as e:
        print(f"Response decode error: {e}\nRaw: {response.text}")
    time.sleep(0.5)

print("\n保存されたmemory_id一覧:")
for r in results:
    if r.get("result") and r["result"].get("content"):
        result_data = r["result"]["content"][0]["text"] if isinstance(r["result"]["content"], list) else r["result"]
        try:
            # 構造化された出力を確認
            if isinstance(result_data, dict) and "memory_id" in result_data:
                print(result_data["memory_id"])
        except Exception:
            print("ID extraction failed for result:", result_data)
