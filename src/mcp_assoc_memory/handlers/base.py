"""
MCP基底クラスとデータ構造（mcpパッケージ型を利用）
"""

from typing import Any, Dict, List, Optional

from mcp import (
    CallToolRequest,
    JSONRPCRequest,
    JSONRPCResponse,
    Tool,
)
from mcp.types import INTERNAL_ERROR, INVALID_PARAMS, METHOD_NOT_FOUND, ErrorData, JSONRPCError


class MCPHandler:
    """MCP基底ハンドラ（mcpパッケージ型を利用）"""

    def __init__(self):
        self.tools: Dict[str, Tool] = {}
        self.resources: Dict[str, Any] = {}

    def register_tool(self, tool: Tool) -> None:
        self.tools[tool.name] = tool

    def get_tools(self) -> List[Tool]:
        return list(self.tools.values())

    async def handle_request(self, request: JSONRPCRequest) -> dict:
        try:
            # ツール呼び出し
            if request.method == "tools/call":
                return await self._handle_tool_call(request)
            # ツール一覧
            elif request.method == "tools/list":
                return await self._handle_tools_list(request)
            else:
                return JSONRPCError(
                    jsonrpc="2.0",
                    id=request.id or "",
                    error=ErrorData(
                        code=METHOD_NOT_FOUND,
                        message=f"Method not found: {request.method}",
                        data=None
                    )
                ).model_dump()
        except Exception as e:
            return JSONRPCError(
                jsonrpc="2.0",
                id=request.id or "",
                error=ErrorData(
                    code=INTERNAL_ERROR,
                    message=str(e),
                    data=None
                )
            ).model_dump()

    async def _handle_tool_call(self, request: JSONRPCRequest) -> dict:
        try:
            params = request.params or {}
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
        except Exception:
            return JSONRPCError(
                jsonrpc="2.0",
                id=request.id or "",
                error=ErrorData(
                    code=INVALID_PARAMS,
                    message="Invalid tool call params",
                    data=None
                )
            ).model_dump()
        if not tool_name or tool_name not in self.tools:
            return JSONRPCError(
                jsonrpc="2.0",
                id=request.id or "",
                error=ErrorData(
                    code=METHOD_NOT_FOUND,
                    message=f"Tool not found: {tool_name}",
                    data=None
                )
            ).model_dump()
        result = await self.call_tool(tool_name, arguments)
        return JSONRPCResponse(
            jsonrpc="2.0",
            id=request.id,
            result={"content": [result]}
        ).model_dump()

    async def _handle_tools_list(self, request: JSONRPCRequest) -> dict:
        tools = [tool for tool in self.get_tools()]
        return JSONRPCResponse(
            jsonrpc="2.0",
            id=request.id,
            result={"tools": [vars(t) for t in tools]}
        ).model_dump()

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError


class BaseHandler(MCPHandler):
    """ツール用基底ハンドラークラス（mcp型利用）"""

    def __init__(self):
        super().__init__()

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError(f"Tool {tool_name} is not implemented")
