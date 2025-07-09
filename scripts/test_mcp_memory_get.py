import json

import requests

MCP_URL = "http://localhost:3006/mcp"

# まずstoreで保存したIDをここにセットしてください
MEMORY_ID = input("memory_idを入力してください: ")

get_request = {
    "tool": "memory",
    "action": "get",
    "params": {
        "memory_id": MEMORY_ID
    }
}

print(f"POST {MCP_URL} : {json.dumps(get_request, ensure_ascii=False)}")
response = requests.post(MCP_URL, json=get_request, timeout=10)
print(f"Status: {response.status_code}")
try:
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))
except Exception as e:
    print(f"Response decode error: {e}\nRaw: {response.text}")
