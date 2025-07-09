import json

import requests

MCP_URL = "http://localhost:3006/mcp"

MEMORY_ID = input("memory_idを入力してください: ")

get_related_request = {
    "tool": "memory",
    "action": "get_related",
    "params": {
        "memory_id": MEMORY_ID,
        "limit": 5,         # 取得件数（任意）
        "min_score": 0.3    # 類似度閾値（任意）
    }
}

print(f"POST {MCP_URL} : {json.dumps(get_related_request, ensure_ascii=False)}")
response = requests.post(MCP_URL, json=get_related_request, timeout=10)
print(f"Status: {response.status_code}")
try:
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))
except Exception as e:
    print(f"Response decode error: {e}\nRaw: {response.text}")
