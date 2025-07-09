import json
import requests

MCP_URL = "http://localhost:8000/mcp"

# FastMCP形式でメモリを検索するテストスクリプト
def test_memory_search():
    search_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "memory_search",
            "arguments": {
                "request": {
                    "query": "テスト用メモリA",
                    "domain": "user",
                    "limit": 10,
                    "min_similarity": 0.3
                }
            }
        }
    }
    
    print(f"POST {MCP_URL} - Memory Search")
    print("Request:", json.dumps(search_request, indent=2, ensure_ascii=False))
    
    response = requests.post(MCP_URL, json=search_request, timeout=10)
    
    try:
        resp_json = response.json()
        print("Response:", json.dumps(resp_json, indent=2, ensure_ascii=False))
        
        # 結果の表示
        if resp_json.get("result"):
            result = resp_json["result"]
            if isinstance(result, dict) and "content" in result:
                content = result["content"]
                if isinstance(content, list) and len(content) > 0:
                    print(f"\n検索結果: {len(content)}件")
                    for item in content:
                        if isinstance(item, dict):
                            print(f"- {item}")
        
    except Exception as e:
        print(f"Response decode error: {e}\nRaw: {response.text}")

if __name__ == "__main__":
    test_memory_search()
