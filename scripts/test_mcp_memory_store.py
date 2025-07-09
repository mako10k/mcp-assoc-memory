import json

import requests

MCP_URL = "http://localhost:3006/mcp"

store_request = {
    "tool": "memory",
    "action": "store",
    "params": {
        "domain": "user",
        "content": "テスト用メモリ",
        "metadata": {"tag": "test", "purpose": "store API test"}
    }
}

print(f"POST {MCP_URL} : {json.dumps(store_request, ensure_ascii=False)}")
response = requests.post(MCP_URL, json=store_request, timeout=10)
print(f"Status: {response.status_code}")
try:
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))
except Exception as e:
    print(f"Response decode error: {e}\nRaw: {response.text}")
