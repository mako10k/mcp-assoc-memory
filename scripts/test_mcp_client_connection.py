#!/usr/bin/env python3
"""
MCP Client Connection Test
Test the actual MCP server via stdio connection
"""

import asyncio
import json
import sys
import subprocess
from pathlib import Path

async def test_mcp_client_connection():
    """Test MCP server connection and tool calls"""
    print("🔌 MCP Client Connection Test")
    print("=" * 35)
    
    try:
        # Find the server module
        server_path = Path(__file__).parent.parent / "src" / "mcp_assoc_memory"
        
        print(f"📍 Server path: {server_path}")
        print("🚀 Starting MCP server process...")
        
        # Start the MCP server process
        process = subprocess.Popen(
            [sys.executable, "-m", "mcp_assoc_memory"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=server_path.parent
        )
        
        print("✅ Server process started")
        
        # Send initialize request
        print("📝 Sending initialize request...")
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        }
        
        process.stdin.write(json.dumps(init_request) + "\n")
        process.stdin.flush()
        
        # Read response
        response_line = process.stdout.readline()
        if response_line:
            response = json.loads(response_line.strip())
            print(f"✅ Initialize response: {response.get('id')} - {response.get('result', {}).get('protocolVersion', 'unknown')}")
        
        # Send tools/list request
        print("📋 Requesting tools list...")
        tools_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }
        
        process.stdin.write(json.dumps(tools_request) + "\n")
        process.stdin.flush()
        
        # Read tools response
        tools_response_line = process.stdout.readline()
        if tools_response_line:
            tools_response = json.loads(tools_response_line.strip())
            tools = tools_response.get('result', {}).get('tools', [])
            print(f"✅ Found {len(tools)} tools:")
            for tool in tools[:3]:  # Show first 3
                print(f"   - {tool.get('name', 'unknown')}: {tool.get('description', 'no description')[:40]}...")
        
        # Test memory_store tool call
        print("📝 Testing memory_store tool call...")
        store_request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "memory_store",
                "arguments": {
                    "request": {
                        "content": "MCP client connection test memory",
                        "scope": "user/client_test",
                        "metadata": {"source": "client_test"},
                        "tags": ["client", "test"],
                        "category": "client_test"
                    }
                }
            }
        }
        
        process.stdin.write(json.dumps(store_request) + "\n")
        process.stdin.flush()
        
        # Read store response
        store_response_line = process.stdout.readline()
        if store_response_line:
            store_response = json.loads(store_response_line.strip())
            if store_response.get('result', {}).get('content'):
                print("✅ memory_store call successful!")
                content = store_response['result']['content']
                if isinstance(content, list) and len(content) > 0:
                    result_data = json.loads(content[0].get('text', '{}'))
                    if result_data.get('success'):
                        memory_id = result_data.get('data', {}).get('memory_id', 'unknown')
                        print(f"   🆔 Memory ID: {memory_id}")
                    else:
                        print(f"   ❌ Store failed: {result_data.get('error', 'unknown')}")
                else:
                    print(f"   📊 Raw response: {store_response}")
            else:
                print(f"   ❌ No content in response: {store_response}")
        
        print("🔚 Terminating server process...")
        process.terminate()
        process.wait(timeout=5)
        
        print("🎉 MCP client connection test completed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        
        # Clean up process if it exists
        try:
            process.terminate()
        except:
            pass

if __name__ == "__main__":
    asyncio.run(test_mcp_client_connection())
