"""
MCP基底クラスとデータ構造
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional, List, Union
from enum import Enum
import json
from datetime import datetime


class MCPMessageType(Enum):
    """MCPメッセージタイプ"""
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    ERROR = "error"


class MCPResourceType(Enum):
    """MCPリソースタイプ"""
    MEMORY = "memory"
    ASSOCIATION = "association"
    PROJECT = "project"
    USER = "user"


@dataclass
class MCPRequest:
    """MCPリクエスト"""
    id: Optional[str] = None
    method: str = ""
    params: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.params is None:
            self.params = {}
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MCPRequest":
        """辞書からMCPRequestを作成"""
        return cls(
            id=data.get("id"),
            method=data.get("method", ""),
            params=data.get("params", {})
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書に変換"""
        result = {
            "method": self.method,
            "params": self.params
        }
        if self.id is not None:
            result["id"] = self.id
        return result


@dataclass 
class MCPResponse:
    """MCPレスポンス"""
    id: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional["MCPError"] = None
    
    def __post_init__(self):
        if self.result is None:
            self.result = {}
    
    @classmethod
    def success(cls, request_id: Optional[str], result: Dict[str, Any]) -> "MCPResponse":
        """成功レスポンスを作成"""
        return cls(id=request_id, result=result)
    
    @classmethod
    def error(cls, request_id: Optional[str], error: "MCPError") -> "MCPResponse":
        """エラーレスポンスを作成"""
        return cls(id=request_id, error=error)
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書に変換"""
        result = {}
        if self.id is not None:
            result["id"] = self.id
        
        if self.error:
            result["error"] = self.error.to_dict()
        else:
            result["result"] = self.result
        
        return result


@dataclass
class MCPError:
    """MCPエラー"""
    code: int
    message: str
    data: Optional[Dict[str, Any]] = None
    
    # エラーコード定数
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603
    
    # カスタムエラーコード
    MEMORY_NOT_FOUND = -1001
    ASSOCIATION_NOT_FOUND = -1002
    PROJECT_NOT_FOUND = -1003
    USER_NOT_FOUND = -1004
    PERMISSION_DENIED = -1005
    VALIDATION_ERROR = -1006
    STORAGE_ERROR = -1007
    EMBEDDING_ERROR = -1008
    
    @classmethod
    def parse_error(cls, message: str = "Parse error") -> "MCPError":
        """解析エラー"""
        return cls(cls.PARSE_ERROR, message)
    
    @classmethod
    def invalid_request(cls, message: str = "Invalid request") -> "MCPError":
        """無効なリクエスト"""
        return cls(cls.INVALID_REQUEST, message)
    
    @classmethod
    def method_not_found(cls, method: str) -> "MCPError":
        """メソッドが見つからない"""
        return cls(cls.METHOD_NOT_FOUND, f"Method not found: {method}")
    
    @classmethod
    def invalid_params(cls, message: str = "Invalid params") -> "MCPError":
        """無効なパラメータ"""
        return cls(cls.INVALID_PARAMS, message)
    
    @classmethod
    def internal_error(cls, message: str = "Internal error") -> "MCPError":
        """内部エラー"""
        return cls(cls.INTERNAL_ERROR, message)
    
    @classmethod
    def memory_not_found(cls, memory_id: str) -> "MCPError":
        """記憶が見つからない"""
        return cls(cls.MEMORY_NOT_FOUND, f"Memory not found: {memory_id}")
    
    @classmethod
    def validation_error(cls, message: str) -> "MCPError":
        """バリデーションエラー"""
        return cls(cls.VALIDATION_ERROR, f"Validation error: {message}")
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書に変換"""
        result = {
            "code": self.code,
            "message": self.message
        }
        if self.data:
            result["data"] = self.data
        return result


@dataclass
class Tool:
    """MCPツール定義"""
    name: str
    description: str
    input_schema: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書に変換"""
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.input_schema
        }


@dataclass
class Resource:
    """MCPリソース定義"""
    uri: str
    name: str
    description: str
    mime_type: str = "application/json"
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書に変換"""
        return {
            "uri": self.uri,
            "name": self.name,
            "description": self.description,
            "mimeType": self.mime_type
        }


@dataclass
class ToolCall:
    """ツール呼び出し情報"""
    name: str
    arguments: Dict[str, Any]
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ToolCall":
        """辞書からToolCallを作成"""
        return cls(
            name=data.get("name", ""),
            arguments=data.get("arguments", {})
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書に変換"""
        return {
            "name": self.name,
            "arguments": self.arguments
        }


@dataclass
class ToolResponse:
    """ツール実行結果"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    message: Optional[str] = None
    
    def __post_init__(self):
        if self.data is None:
            self.data = {}
    
    @classmethod
    def success_response(cls, data: Dict[str, Any], message: str = "") -> "ToolResponse":
        """成功レスポンスを作成"""
        return cls(success=True, data=data, message=message)
    
    @classmethod
    def error_response(cls, error: str, message: str = "") -> "ToolResponse":
        """エラーレスポンスを作成"""
        return cls(success=False, error=error, message=message)
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書に変換"""
        result: Dict[str, Any] = {
            "success": self.success
        }
        
        if self.success:
            if self.data is not None:
                result["data"] = self.data
            if self.message:
                result["message"] = self.message
        else:
            if self.error is not None:
                result["error"] = self.error
            if self.message:
                result["message"] = self.message
        
        return result


class MCPHandler:
    """MCP基底ハンドラ"""
    
    def __init__(self):
        self.tools: Dict[str, Tool] = {}
        self.resources: Dict[str, Resource] = {}
    
    def register_tool(self, tool: Tool) -> None:
        """ツールを登録"""
        self.tools[tool.name] = tool
    
    def register_resource(self, resource: Resource) -> None:
        """リソースを登録"""
        self.resources[resource.uri] = resource
    
    def get_tools(self) -> List[Tool]:
        """登録されたツール一覧を取得"""
        return list(self.tools.values())
    
    def get_resources(self) -> List[Resource]:
        """登録されたリソース一覧を取得"""
        return list(self.resources.values())
    
    async def handle_request(self, request: MCPRequest) -> MCPResponse:
        """リクエストを処理"""
        try:
            # ツール呼び出し
            if request.method == "tools/call":
                return await self._handle_tool_call(request)
            
            # リソース読み取り
            elif request.method == "resources/read":
                return await self._handle_resource_read(request)
            
            # ツール一覧
            elif request.method == "tools/list":
                return await self._handle_tools_list(request)
            
            # リソース一覧
            elif request.method == "resources/list":
                return await self._handle_resources_list(request)
            
            else:
                return MCPResponse.error(
                    request.id,
                    MCPError.method_not_found(request.method)
                )
        
        except Exception as e:
            return MCPResponse.error(
                request.id,
                MCPError.internal_error(str(e))
            )
    
    async def _handle_tool_call(self, request: MCPRequest) -> MCPResponse:
        """ツール呼び出しを処理"""
        params = request.params or {}
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if not tool_name:
            return MCPResponse.error(
                request.id,
                MCPError.invalid_params("Tool name is required")
            )
        
        if tool_name not in self.tools:
            return MCPResponse.error(
                request.id,
                MCPError.method_not_found(tool_name)
            )
        
        # サブクラスで実装
        result = await self.call_tool(tool_name, arguments)
        return MCPResponse.success(request.id, {"content": [result]})
    
    async def _handle_resource_read(self, request: MCPRequest) -> MCPResponse:
        """リソース読み取りを処理"""
        params = request.params or {}
        uri = params.get("uri")
        
        if not uri:
            return MCPResponse.error(
                request.id,
                MCPError.invalid_params("URI is required")
            )
        
        if uri not in self.resources:
            return MCPResponse.error(
                request.id,
                MCPError.method_not_found(f"Resource not found: {uri}")
            )
        
        # サブクラスで実装
        content = await self.read_resource(uri)
        return MCPResponse.success(request.id, {"contents": [content]})
    
    async def _handle_tools_list(self, request: MCPRequest) -> MCPResponse:
        """ツール一覧を処理"""
        tools = [tool.to_dict() for tool in self.get_tools()]
        return MCPResponse.success(request.id, {"tools": tools})
    
    async def _handle_resources_list(self, request: MCPRequest) -> MCPResponse:
        """リソース一覧を処理"""
        resources = [resource.to_dict() for resource in self.get_resources()]
        return MCPResponse.success(request.id, {"resources": resources})
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """ツール呼び出し（サブクラスで実装）"""
        raise NotImplementedError
    
    async def read_resource(self, uri: str) -> Dict[str, Any]:
        """リソース読み取り（サブクラスで実装）"""
        raise NotImplementedError


class BaseHandler(MCPHandler):
    """ツール用基底ハンドラークラス"""
    
    def __init__(self):
        super().__init__()
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """ツール呼び出しの基本実装"""
        # サブクラスで具体的な実装を行う
        raise NotImplementedError(f"Tool {tool_name} is not implemented")
    
    async def read_resource(self, uri: str) -> Dict[str, Any]:
        """リソース読み取りの基本実装"""
        # サブクラスで具体的な実装を行う
        raise NotImplementedError(f"Resource {uri} is not supported")


def validate_schema(data: Any, schema: Dict[str, Any]) -> bool:
    """簡易スキーマバリデーション"""
    if schema.get("type") == "object":
        if not isinstance(data, dict):
            return False
        
        required = schema.get("required", [])
        for field in required:
            if field not in data:
                return False
        
        properties = schema.get("properties", {})
        for key, value in data.items():
            if key in properties:
                if not validate_schema(value, properties[key]):
                    return False
    
    elif schema.get("type") == "string":
        return isinstance(data, str)
    
    elif schema.get("type") == "number":
        return isinstance(data, (int, float))
    
    elif schema.get("type") == "boolean":
        return isinstance(data, bool)
    
    elif schema.get("type") == "array":
        if not isinstance(data, list):
            return False
        
        items_schema = schema.get("items")
        if items_schema:
            for item in data:
                if not validate_schema(item, items_schema):
                    return False
    
    return True
