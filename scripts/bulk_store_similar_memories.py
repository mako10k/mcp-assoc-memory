import json
import time

import requests

MCP_URL = "http://localhost:8000/mcp/"

# Test data with similar content for bulk storage
memories = [
    {"content": "Test memory A", "scope": "user/test", "metadata": {"tag": "similar_test"}},
    {"content": "Test memory A variant", "scope": "user/test", "metadata": {"tag": "similar_test"}},
    {"content": "Test memory A details", "scope": "user/test", "metadata": {"tag": "similar_test"}},
    {"content": "Test memory A supplementary info", "scope": "user/test", "metadata": {"tag": "similar_test"}},
    {"content": "Test memory A related information", "scope": "user/test", "metadata": {"tag": "similar_test"}},
    {"content": "Test memory A additional info", "scope": "user/test", "metadata": {"tag": "similar_test"}},
]

results = []
for i, mem in enumerate(memories):
    # FastMCP format request
    store_request = {
        "jsonrpc": "2.0",
        "id": i + 1,
        "method": "tools/call",
        "params": {"name": "memory_store", "arguments": {"request": mem}},
    }
    print(f"[{i + 1}/{len(memories)}] POST {MCP_URL} : {mem['content']}")
    headers = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
    response = requests.post(MCP_URL, json=store_request, headers=headers, timeout=10)
    try:
        resp_json = response.json()
        print(json.dumps(resp_json, indent=2, ensure_ascii=False))
        results.append(resp_json)
    except Exception as e:
        print(f"Response decode error: {e}\nRaw: {response.text}")
    time.sleep(0.5)

print("\nStored memory_id list:")
for r in results:
    if r.get("result") and r["result"].get("content"):
        result_data = r["result"]["content"][0]["text"] if isinstance(r["result"]["content"], list) else r["result"]
        try:
            # Check structured output
            if isinstance(result_data, dict) and "memory_id" in result_data:
                print(result_data["memory_id"])
        except Exception:
            print("ID extraction failed for result:", result_data)
