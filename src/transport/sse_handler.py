"""
MCP公式SDK/fastmcpベースのSSE/WebSocketトランスポート統合設計（SDKラッパー例）
"""

from mcp.server.fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.routing import Mount
import uvicorn
import threading

class SseTransport:
    """
    FastMCPサーバのSSEトランスポートラッパー
    """
    def __init__(self, mcp_server: FastMCP, mount_path: str = "/sse", host: str = "0.0.0.0", port: int = 8001):
        self.mcp_server = mcp_server
        self.mount_path = mount_path
        self.host = host
        self.port = port
        self.app = Starlette(routes=[
            Mount(self.mount_path, app=self.mcp_server.sse_app())
        ])
        self.server_thread = None

    def start(self):
        def run():
            uvicorn.run(self.app, host=self.host, port=self.port, log_level="info")
        self.server_thread = threading.Thread(target=run, daemon=True)
        self.server_thread.start()

    def stop(self):
        # uvicornのプログラム的停止は省略
        pass
