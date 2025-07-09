"""
MCPツール統合ルーター

7つのメインツールグループを統合管理:
1. memory - 基本記憶操作
2. memory_manage - 記憶管理・統計
3. search - 高度検索機能
4. project - プロジェクト管理
5. user - ユーザー・セッション管理
6. visualize - 可視化・分析
7. admin - システム管理・保守
"""

import logging
from typing import Any, Dict

from mcp.types import (
    INTERNAL_ERROR,
    INVALID_PARAMS,
    INVALID_REQUEST,
    METHOD_NOT_FOUND,
    ErrorData,
    JSONRPCError,
)

from ..auth.session import SessionManager
from ..core.memory_manager import MemoryManager
from ..core.similarity import SimilarityCalculator
from .base import BaseHandler
from .tools import (
    admin_backup,
    admin_cleanup_orphans,
    admin_health_check,
    admin_reindex_embeddings,
    admin_restore,
    admin_system_stats,
    memory_manage_batch_delete,
    memory_manage_change_domain,
    memory_manage_cleanup,
    memory_manage_export,
    memory_manage_import,
    memory_manage_stats,
    project_add_member,
    project_create,
    project_delete,
    project_get,
    project_list,
    project_remove_member,
    project_update,
    user_create_session,
    user_end_session,
    user_get_current,
    user_get_projects,
    user_get_sessions,
    user_switch_session,
    visualize_category_chart,
    visualize_domain_graph,
    visualize_memory_map,
    visualize_stats_dashboard,
    visualize_timeline,
)

logger = logging.getLogger(__name__)


class MCPToolRouter(BaseHandler):
    async def route(self, req_json: dict) -> dict:
        """
        MCPリクエスト(JSON)を解釈し、
        params形式: {"subcommand": ..., "domain":..., ...各種引数...} のみをサポート。
        後方互換は廃止。
        """
        logger.info(f"[MCPToolRouter.route] 受信req_json: {req_json}")
        params_raw = req_json.get("params", {})
        # MCPクライアントからのリクエスト形式に柔軟対応
        # params: {name, arguments}
        tool = params_raw.get("name")
        arguments = params_raw.get("arguments", {})
        if "subcommand" not in arguments:
            logger.error(f"[MCPToolRouter.route] 'subcommand'がargumentsに存在しません: {arguments}")
            return JSONRPCError(
                jsonrpc="2.0",
                id=req_json.get("id") or "",
                error=ErrorData(
                    code=INVALID_PARAMS,
                    message="'params'は{subcommand: ..., ...}形式である必要があります",
                    data=None
                )
            ).model_dump()
        subcommand = arguments["subcommand"]
        arguments = {k: v for k, v in arguments.items() if k != "subcommand"}
        tool_name = f"{tool}.{subcommand}"
        logger.info(f"[MCPToolRouter.route] tool_name: {tool_name}, arguments: {arguments}")
        # スキーマ取得
        tools_info = self.get_available_tools()
        tool_entry = next((t for t in tools_info['tools'] if t['name'] == tool), None)
        sub_schema = None
        if tool_entry and 'parameters' in tool_entry and subcommand in tool_entry['parameters']:
            sub_schema = tool_entry['parameters'][subcommand]
        # バリデーション
        validation_error = None
        if sub_schema:
            import jsonschema
            try:
                jsonschema.validate(arguments, {
                    'type': 'object',
                    'properties': sub_schema.get('properties', {}),
                    'required': sub_schema.get('required', [])
                })
            except jsonschema.ValidationError as ve:
                validation_error = str(ve)
        if validation_error:
            logger.info(f"[MCPToolRouter.route] バリデーションエラー: {validation_error}")
            return JSONRPCError(
                jsonrpc="2.0",
                id=req_json.get("id") or "",
                error=ErrorData(
                    code=INVALID_PARAMS,
                    message=f"引数が不正です: {validation_error}",
                    data=sub_schema
                )
            ).model_dump()
        # ツール実行
        try:
            return await self.call_tool(tool_name, arguments)
        except Exception as e:
            logger.error(f"ツール実行例外: {tool_name}: {e}")
            return JSONRPCError(
                jsonrpc="2.0",
                id=req_json.get("id") or "",
                error=ErrorData(
                    code=INTERNAL_ERROR,
                    message=f"ツール '{tool_name}' の実行中に例外が発生しました: {str(e)}",
                    data=sub_schema
                )
            ).model_dump()

    """MCPツール統合ルーター"""
    def __init__(
        self,
        memory_manager: MemoryManager,
        session_manager: SessionManager,
        similarity_calc: SimilarityCalculator
    ):
        super().__init__()
        self.memory_manager = memory_manager
        self.session_manager = session_manager
        self.similarity_calc = similarity_calc

        # search, project, user, visualize, adminグループのハンドラのみインスタンス化
        from .tools_extended import ProjectToolHandler, UserToolHandler, VisualizeToolHandler, AdminToolHandler
        from .tools_extended import SearchToolHandler
        self.project_handler = ProjectToolHandler(memory_manager, session_manager)
        self.user_handler = UserToolHandler(session_manager, self.project_handler)
        self.visualize_handler = VisualizeToolHandler(memory_manager)
        self.admin_handler = AdminToolHandler(memory_manager, session_manager)
        self.search_handler = SearchToolHandler(memory_manager, similarity_calc)

        # ツールマッピングを定義
        self.tool_mappings = {
            # memory ツールグループ
            'memory.store': memory_manage_stats,  # 雛形
            'memory.search': memory_manage_export,
            'memory.get': memory_manage_import,
            'memory.get_related': memory_manage_change_domain,
            'memory.update': memory_manage_batch_delete,
            'memory.delete': memory_manage_cleanup,

            # memory_manage ツールグループ
            'memory_manage.stats': memory_manage_stats,
            'memory_manage.export': memory_manage_export,
            'memory_manage.import': memory_manage_import,
            'memory_manage.change_domain': memory_manage_change_domain,
            'memory_manage.batch_delete': memory_manage_batch_delete,
            'memory_manage.cleanup': memory_manage_cleanup,

            # search ツールグループ
            'search.semantic': self.search_handler.handle_semantic,
            'search.tags': self.search_handler.handle_tags,
            'search.timerange': self.search_handler.handle_timerange,
            'search.advanced': self.search_handler.handle_advanced,
            'search.similar': self.search_handler.handle_similar,

            # project ツールグループ
            'project.create': self.project_handler.handle_create,
            'project.list': self.project_handler.handle_list,
            'project.get': self.project_handler.handle_get,
            'project.add_member': self.project_handler.handle_add_member,
            'project.remove_member': self.project_handler.handle_remove_member,
            'project.update': self.project_handler.handle_update,
            'project.delete': self.project_handler.handle_delete,

            # user ツールグループ
            'user.get_current': self.user_handler.handle_get_current,
            'user.get_projects': self.user_handler.handle_get_projects,
            'user.get_sessions': self.user_handler.handle_get_sessions,
            'user.create_session': self.user_handler.handle_create_session,
            'user.switch_session': self.user_handler.handle_switch_session,
            'user.end_session': self.user_handler.handle_end_session,

            # visualize ツールグループ
            'visualize.memory_map': self.visualize_handler.handle_memory_map,
            'visualize.stats_dashboard': self.visualize_handler.handle_stats_dashboard,
            'visualize.domain_graph': self.visualize_handler.handle_domain_graph,
            'visualize.timeline': self.visualize_handler.handle_timeline,
            'visualize.category_chart': self.visualize_handler.handle_category_chart,

            # admin ツールグループ
            'admin.health_check': self.admin_handler.handle_health_check,
            'admin.system_stats': self.admin_handler.handle_system_stats,
            'admin.backup': self.admin_handler.handle_backup,
            'admin.restore': self.admin_handler.handle_restore,
            'admin.reindex': self.admin_handler.handle_reindex,
            'admin.reindex_embeddings': self.admin_handler.handle_reindex_embeddings,
            'admin.cleanup_orphans': self.admin_handler.handle_cleanup_orphans,
        }

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> dict:
        handler = self.tool_mappings.get(tool_name)
        if not handler:
            return {
                "success": False,
                "error": "TOOL_NOT_FOUND",
                "message": f"ツール '{tool_name}' が見つかりません"
            }
        # 関数型ハンドラの場合は同期実行
        if callable(handler):
            result = handler(**arguments) if arguments else handler()
            if not isinstance(result, dict):
                return {
                    "success": False,
                    "error": "INVALID_HANDLER_RETURN",
                    "message": f"ツール '{tool_name}' のハンドラの戻り値がdict型ではありません: {type(result)}"
                }
            return result
        # 非対応型
        return {
            "success": False,
            "error": "INVALID_HANDLER",
            "message": f"ツール '{tool_name}' のハンドラ型が不正です"
        }

    def get_available_tools(self) -> dict:
        """
        MCP仕様に準拠したツール一覧＋サブコマンドスキーマを返す。
        - inputSchema: {type: "object", properties: {}}（全ツール共通、Zodバリデーション対応）
        - parameters: サブコマンドスキーマ（memoryツールは詳細、他は空dict）
        """
        memory_parameters = {
            'subcommand': {
                'description': 'Subcommand to execute',
                'type': 'string',
                'enum': [
                    'store', 'search', 'get', 'get_related', 'update', 'delete'
                ]
            },
            'domain': {
                'description': 'Domain of memory',
                'type': 'string',
                'enum': [
                    'global', 'user', 'project', 'session'
                ]
            },
            'project_id': {
                'description': 'Project ID (Required for project domain)',
                'type': 'string',
            },
            'content': {
                'description': 'Content of memory (Required for store/update)',
                'type': 'string'
            },
            'metadata': {
                'description': 'Additional metadata (Required for store/update)',
                'type': 'object',
                'additionalProperties': True
            },
            'tags': {
                'description': 'Tags for memory (Optional)',
                'type': 'array',
                'items': {'type': 'string'}
            },
            'category': {
                'description': 'Category for memory (Optional)',
                'type': 'string'
            },
            'memory_id': {
                'description': 'Memory ID (Required for get, update, delete, get_related)',
                'type': 'string'
            },
            'query': {
                'description': 'Search query (Required for search)',
                'type': 'string'
            },
            'limit': {
                'description': 'Limit for search/get_related',
                'type': 'integer',
                'minimum': 1,
                'default': 10
            },
            'min_score': {
                'description': 'Minimum similarity score for get_related',
                'type': 'number',
                'minimum': 0,
                'maximum': 1,
                'default': 0.7
            },
        }
        empty_input_schema = {"type": "object", "properties": {}}
        tools = [
            {
                'name': 'memory',
                'description': 'Basic memory operations',
                'parameters': memory_parameters,
                'inputSchema': {
                    'type': 'object',
                    'properties': memory_parameters,
                    'required': ["subcommand", "domain"],
                    'description': 'Memory tool parameters'
                }
            },
            {
                'name': 'memory_manage',
                'description': '記憶管理・統計',
                'parameters': {},
                'inputSchema': empty_input_schema
            },
            {
                'name': 'search',
                'description': '高度検索機能',
                'parameters': {},
                'inputSchema': empty_input_schema
            },
            {
                'name': 'project',
                'description': 'プロジェクト管理',
                'parameters': {},
                'inputSchema': empty_input_schema
            },
            {
                'name': 'user',
                'description': 'ユーザー・セッション管理',
                'parameters': {},
                'inputSchema': empty_input_schema
            },
            {
                'name': 'visualize',
                'description': '可視化・分析',
                'parameters': {},
                'inputSchema': empty_input_schema
            },
            {
                'name': 'admin',
                'description': 'システム管理・保守',
                'parameters': {},
                'inputSchema': empty_input_schema
            }
        ]
        return {'tools': tools}

    def get_tool_count(self) -> int:
        """総ツール数を取得"""
        return len(self.tool_mappings)

    def get_tools_by_group(self, group: str) -> Dict[str, Any]:
        """グループ別ツール一覧を取得"""
        tools = self.get_available_tools()
        return tools.get(group, {})

    async def handle_request(self, mcp_req) -> dict:
        """
        JSON-RPC形式のmethodバリデーションを追加。
        許可されたmethod以外はエラー返却。
        """
        def _tools_list_to_dict(tools_info):
            # tools_info['tools']はlist→dictに変換
            return {t['name']: t for t in tools_info.get('tools', [])}

        # id抽出（どの形式でも必ずidを取得）
        req_id = None
        if hasattr(mcp_req, "id"):
            req_id = getattr(mcp_req, "id", None)
        elif isinstance(mcp_req, dict):
            req_id = mcp_req.get("id")
        if req_id is None:
            req_id = ""

        # method抽出
        method = None
        if isinstance(mcp_req, dict):
            method = mcp_req.get("method")
        elif hasattr(mcp_req, "method"):
            method = getattr(mcp_req, "method", None)
        if method is None:
            return JSONRPCError(
                jsonrpc="2.0",
                id=req_id,
                error=ErrorData(
                    code=INVALID_REQUEST,
                    message="Missing or invalid 'method' field.",
                    data=None
                )
            ).model_dump()

        # methodごとにルーティング
        async def not_implemented():
            return JSONRPCError(
                jsonrpc="2.0",
                id=req_id,
                error=ErrorData(
                    code=METHOD_NOT_FOUND,
                    message=f"Method '{method}' is not implemented.",
                    data=None
                )
            ).model_dump()

        async def handle_initialize():
            tools_info = self.get_available_tools()
            tools_dict = _tools_list_to_dict(tools_info)
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": "2025-03-26",
                    "capabilities": {
                        "streaming": True,
                        "tools": tools_dict
                    },
                    "serverInfo": {
                        "name": "MCP Assoc Memory Server",
                        "version": "0.1.0"
                    }
                }
            }

        async def handle_tools_list():
            tools_info = self.get_available_tools()
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": tools_info
            }

        async def handle_tools_call():
            # MCPツール呼び出し: route()に委譲
            result = await self.route(mcp_req)
            # MCPプロトコル: resultはToolResultまたはエラー
            if isinstance(result, dict) and (result.get("success") is False or result.get("error")):
                error_code = INTERNAL_ERROR
                error_message = result.get("message") or result.get("error") or "MCP error"
                error_data = {k: v for k, v in result.items() if k not in ("success", "error", "message")}
                return JSONRPCError(
                    jsonrpc="2.0",
                    id=req_id,
                    error=ErrorData(
                        code=error_code,
                        message=error_message,
                        data=error_data if error_data else None
                    )
                ).model_dump()
            # MCPプロトコル: resultは必ず { content: [ToolResult, ...] }
            # すでにバッチ形式（result={content: [...]})ならそのまま返す
            if isinstance(result, dict) and "content" in result and isinstance(result["content"], list):
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": result["content"]
                    }
                }
            # 単一ToolResultならラップ
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [result]
                }
            }

        async def handle_ping():
            # シンプルなping応答
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "pong": True
                }
            }

        # methodルーティングテーブル
        method_table = {
            "initialize": handle_initialize,
            "tools/list": handle_tools_list,
            "tools/call": handle_tools_call,
            "resources/list": not_implemented,
            "prompts/list": not_implemented,
            "$/progress": not_implemented,
            "$/cancelRequest": not_implemented,
            "notifications/initialized": not_implemented,
            "ping": handle_ping
        }
        handler = method_table.get(method, not_implemented)
        return await handler()
