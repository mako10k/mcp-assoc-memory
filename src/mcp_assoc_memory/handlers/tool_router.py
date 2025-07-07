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

from typing import Dict, Any, Optional
import logging

from .base import BaseHandler, ToolCall, ToolResponse
from .tools import (
    MemoryToolHandler, 
    MemoryManageToolHandler,
    SearchToolHandler
)
from .tools_extended import (
    ProjectToolHandler,
    UserToolHandler, 
    VisualizeToolHandler,
    AdminToolHandler
)
from ..core.memory_manager import MemoryManager
from ..core.similarity import SimilarityCalculator
from ..auth.session import SessionManager

logger = logging.getLogger(__name__)


class MCPToolRouter(BaseHandler):
    async def route(self, req_json: dict) -> dict:
        """MCPリクエスト(JSON)を解釈し、対応ツールを呼び出す"""
        # MCPRequest形式: {"tool": ..., "action": ..., "params": ...}
        tool = req_json.get("tool")
        action = req_json.get("action")
        params = req_json.get("params", {})
        if not tool or not action:
            return {"success": False, "error": "INVALID_REQUEST", "message": "'tool'と'action'は必須です"}
        tool_name = f"{tool}.{action}"
        return await self.call_tool(tool_name, params)
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
        
        # ツールハンドラーを初期化
        self.memory_handler = MemoryToolHandler(memory_manager)
        self.memory_manage_handler = MemoryManageToolHandler(memory_manager)
        self.search_handler = SearchToolHandler(memory_manager, similarity_calc)
        self.project_handler = ProjectToolHandler(memory_manager, session_manager)
        self.user_handler = UserToolHandler(session_manager, self.project_handler)
        self.visualize_handler = VisualizeToolHandler(memory_manager)
        self.admin_handler = AdminToolHandler(memory_manager, session_manager)
        
        # ツールマッピングを定義
        self.tool_mappings = {
            # memory ツールグループ
            'memory.store': self.memory_handler.handle_store,
            'memory.search': self.memory_handler.handle_search,
            'memory.get': self.memory_handler.handle_get,
            'memory.get_related': self.memory_handler.handle_get_related,
            'memory.update': self.memory_handler.handle_update,
            'memory.delete': self.memory_handler.handle_delete,
            
            # memory_manage ツールグループ
            'memory_manage.stats': self.memory_manage_handler.handle_stats,
            'memory_manage.export': self.memory_manage_handler.handle_export,
            'memory_manage.import': self.memory_manage_handler.handle_import,
            'memory_manage.change_domain': self.memory_manage_handler.handle_change_domain,
            'memory_manage.batch_delete': self.memory_manage_handler.handle_batch_delete,
            'memory_manage.cleanup': self.memory_manage_handler.handle_cleanup,
            
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
            'admin.cleanup_orphans': self.admin_handler.handle_cleanup_orphans,
        }
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """ツール呼び出しを実行"""
        try:
            # ツールマッピングから対応するハンドラーを取得
            handler = self.tool_mappings.get(tool_name)
            
            if not handler:
                return ToolResponse(
                    success=False,
                    error="TOOL_NOT_FOUND",
                    message=f"ツール '{tool_name}' が見つかりません"
                ).to_dict()
            
            # ハンドラーを実行
            response = await handler(arguments)
            
            # ログ出力
            logger.info(
                f"Tool executed: {tool_name}",
                extra={
                    'tool_name': tool_name,
                    'success': response.success,
                    'args_keys': list(arguments.keys())
                }
            )
            
            return response.to_dict()
            
        except Exception as e:
            logger.error(f"ツール実行エラー ({tool_name}): {e}")
            return ToolResponse(
                success=False,
                error="TOOL_EXECUTION_ERROR",
                message=f"ツール '{tool_name}' の実行中にエラーが発生しました: {str(e)}"
            ).to_dict()
    
    def get_available_tools(self) -> Dict[str, Dict[str, Any]]:
        """利用可能なツール一覧を取得"""
        tools = {}
        
        # memory ツールグループ
        tools['memory'] = {
            'description': '基本記憶操作',
            'subcommands': {
                'store': '記憶を保存する',
                'search': '記憶を検索する', 
                'get': '記憶を取得する',
                'get_related': '関連記憶を取得する',
                'update': '記憶を更新する',
                'delete': '記憶を削除する'
            }
        }
        
        # memory_manage ツールグループ
        tools['memory_manage'] = {
            'description': '記憶管理・統計',
            'subcommands': {
                'stats': '記憶統計を取得する',
                'export': '記憶をエクスポートする',
                'import': '記憶をインポートする',
                'change_domain': '記憶のドメインを変更する',
                'batch_delete': '記憶を一括削除する',
                'cleanup': 'データベースをクリーンアップする'
            }
        }
        
        # search ツールグループ
        tools['search'] = {
            'description': '高度検索機能',
            'subcommands': {
                'semantic': '意味的検索を実行する',
                'tags': 'タグ検索を実行する',
                'timerange': '時間範囲検索を実行する',
                'advanced': '高度検索を実行する',
                'similar': '類似記憶検索を実行する'
            }
        }
        
        # project ツールグループ
        tools['project'] = {
            'description': 'プロジェクト管理',
            'subcommands': {
                'create': 'プロジェクトを作成する',
                'list': 'プロジェクト一覧を取得する',
                'get': 'プロジェクト詳細を取得する',
                'add_member': 'プロジェクトメンバーを追加する',
                'remove_member': 'プロジェクトメンバーを削除する',
                'update': 'プロジェクトを更新する',
                'delete': 'プロジェクトを削除する'
            }
        }
        
        # user ツールグループ
        tools['user'] = {
            'description': 'ユーザー・セッション管理',
            'subcommands': {
                'get_current': '現在のユーザー情報を取得する',
                'get_projects': 'ユーザーのプロジェクト一覧を取得する',
                'get_sessions': 'ユーザーのセッション一覧を取得する',
                'create_session': '新しいセッションを作成する',
                'switch_session': 'セッションのプロジェクトを切り替える',
                'end_session': 'セッションを終了する'
            }
        }
        
        # visualize ツールグループ
        tools['visualize'] = {
            'description': '可視化・分析',
            'subcommands': {
                'memory_map': '記憶マップを生成する',
                'stats_dashboard': '統計ダッシュボードを生成する',
                'domain_graph': 'ドメイングラフを生成する',
                'timeline': 'タイムライン表示を生成する',
                'category_chart': 'カテゴリチャートを生成する'
            }
        }
        
        # admin ツールグループ
        tools['admin'] = {
            'description': 'システム管理・保守',
            'subcommands': {
                'health_check': 'システムヘルスチェックを実行する',
                'system_stats': 'システム統計を取得する',
                'backup': 'システムバックアップを実行する',
                'restore': 'システムリストアを実行する',
                'reindex': 'インデックス再構築を実行する',
                'cleanup_orphans': '孤立データをクリーンアップする'
            }
        }
        
        return tools
    
    def get_tool_count(self) -> int:
        """総ツール数を取得"""
        return len(self.tool_mappings)
    
    def get_tools_by_group(self, group: str) -> Dict[str, Any]:
        """グループ別ツール一覧を取得"""
        tools = self.get_available_tools()
        return tools.get(group, {})
    
    async def handle_request(self, mcp_req) -> dict:
        """
        JSON-RPC形式のmethod: initialize なら即時応答（toolsは7グループのみ）、それ以外はroute()へ委譲
        """
        if hasattr(mcp_req, "method") and mcp_req.method == "initialize":
            tools_info = self.get_available_tools()
            return {
                "jsonrpc": "2.0",
                "id": getattr(mcp_req, "id", None),
                "result": {
                    "capabilities": {
                        "streaming": True,
                        "tools": list(tools_info.keys()),  # 7グループのみ
                        "tool_details": tools_info
                    }
                }
            }
        # MCPツール形式はroute()で処理
        if hasattr(mcp_req, "to_dict"):
            req_json = mcp_req.to_dict()
        else:
            req_json = dict(mcp_req)
        return await self.route(req_json)
