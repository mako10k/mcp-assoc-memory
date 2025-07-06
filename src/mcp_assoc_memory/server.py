"""
MCPAssocMemoryServer - SDK統合サーバ実装
"""

from mcp.server import Server
from mcp.types import Tool, Resource
from mcp_assoc_memory.handlers.tool_router import MCPToolRouter
from mcp_assoc_memory.core.memory_manager import MemoryManager
from mcp_assoc_memory.config import load_config

class MCPAssocMemoryServer:
    def __init__(self, config):
        self.config = config
        self.server = Server("mcp-assoc-memory")
        self.memory_manager = MemoryManager(config)
        self.tool_router = MCPToolRouter(self.memory_manager)
        self._register_tools()
        self._register_resources()

    def _register_tools(self):
        # MCPToolRouterからツール定義を取得しSDKに登録
        for tool in self.tool_router.get_tools():
            self.server.register_tool(tool)

    def _register_resources(self):
        # MCPToolRouterからリソース定義を取得しSDKに登録
        for resource in self.tool_router.get_resources():
            self.server.register_resource(resource)

    def run(self):
        # 設定に応じて有効なトランスポートで起動
        self.server.run(config=self.config)
