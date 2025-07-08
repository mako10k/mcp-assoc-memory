import requests
import json

# MCPサーバのエンドポイント
MCP_URL = "http://localhost:3006/mcp"

# JSON-RPC initializeリクエスト
initialize_request = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {}
}

print(f"POST {MCP_URL} : {json.dumps(initialize_request)}")
response = requests.post(MCP_URL, json=initialize_request, timeout=10)
print(f"Status: {response.status_code}")
try:
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))
except Exception as e:
    print(f"Response decode error: {e}\nRaw: {response.text}")
