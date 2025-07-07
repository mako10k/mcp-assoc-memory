"""
メイン実行ファイル - MCPサーバの起動エントリーポイント
"""

import asyncio
import argparse
import sys
from typing import Optional

from .config import Config
from transport.manager import TransportManager
from mcp_assoc_memory.handlers.tool_router import MCPToolRouter
from mcp_assoc_memory.core.similarity import SimilarityCalculator
from mcp_assoc_memory.auth.session import SessionManager
from .core.memory_manager import MemoryManager
from .utils.logging import setup_logging


async def main():
    """メイン実行関数"""
    parser = argparse.ArgumentParser(description="MCP連想記憶サーバ")
    parser.add_argument(
        "--transport",
        choices=["stdio", "http", "sse"],
        default=None,
        help="トランスポート方式 (指定時のみ優先)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="HTTPポート番号 (指定時のみ優先)"
    )
    parser.add_argument(
        "--host",
        default=None,
        help="HTTPホスト名 (指定時のみ優先)"
    )
    parser.add_argument(
        "--config",
        help="設定ファイルパス"
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default=None,
        help="ログレベル (指定時のみ優先)"
    )

    args = parser.parse_args()


    # 設定読み込み（CLI > 環境変数 > config.json > デフォルト）
    cli_args = {}
    if args.transport is not None:
        cli_args["transport"] = args.transport
    if args.port is not None:
        cli_args["port"] = args.port
    if args.host is not None:
        cli_args["host"] = args.host
    if args.log_level is not None:
        cli_args["log_level"] = args.log_level

    config = Config.load(
        args.config,
        cli_args=cli_args if cli_args else None
    )
    # 設定の有効値をデバッグ出力（開発時のみ）
    if getattr(config, "debug_mode", False):
        import pprint
        pprint.pprint(config.__dict__)

    # ログ設定（config優先、CLIで上書き可）
    setup_logging(getattr(config, "log_level", args.log_level))

    try:
        # 記憶管理システム初期化

        # ストレージ・サービス初期化
        from mcp_assoc_memory.storage.vector_store import ChromaVectorStore
        from mcp_assoc_memory.storage.metadata_store import SQLiteMetadataStore
        from mcp_assoc_memory.storage.graph_store import NetworkXGraphStore
        from mcp_assoc_memory.core.embedding_service import create_embedding_service
        import os
        data_dir = config.storage.data_dir
        vector_store = ChromaVectorStore(persist_directory=data_dir)
        metadata_db_path = os.path.join(data_dir, "memory.db")
        metadata_store = SQLiteMetadataStore(database_path=metadata_db_path)
        graph_path = os.path.join(data_dir, "memory_graph.gml")
        graph_store = NetworkXGraphStore(graph_path=graph_path)
        embedding_service = create_embedding_service(config.to_dict())
        similarity_calc = SimilarityCalculator()

        memory_manager = MemoryManager(
            vector_store=vector_store,
            metadata_store=metadata_store,
            graph_store=graph_store,
            embedding_service=embedding_service,
            similarity_calculator=similarity_calc
        )
        await memory_manager.initialize()
        session_manager = SessionManager(session_timeout_minutes=config.security.session_timeout_minutes)
        router = MCPToolRouter(memory_manager, session_manager, similarity_calc)

        # トランスポート管理システム初期化
        # config.transport.mode（またはmode相当）で判定
        print(f"[DEBUG] config.transport.http_host={config.transport.http_host}, http_port={config.transport.http_port}, http_enabled={getattr(config.transport, 'http_enabled', None)}")
        transport_mode = getattr(config.transport, "mode", None) or args.transport
        sse_enabled = transport_mode == "sse"
        mcp_server = None
        if sse_enabled:
            try:
                from fastapi import FastAPI, Request
                from fastmcp import FastMCP  # 公式SDK
                from mcp_assoc_memory.handlers.base import MCPRequest
                app = FastAPI()
                # 公式推奨: FastAPIエンドポイントでMCPRequest→handle_request
                @app.post("/mcp")
                async def mcp_endpoint(request: Request):
                    req_json = await request.json()
                    # JSON-RPC形式（jsonrpc, method, id, params）なら分岐
                    if "jsonrpc" in req_json and "method" in req_json:
                        mcp_req = MCPRequest(
                            id=req_json.get("id"),
                            method=req_json.get("method"),
                            params=req_json.get("params", {})
                        )
                    else:
                        mcp_req = MCPRequest.from_dict(req_json)
                    mcp_resp = await router.handle_request(mcp_req)
                    return mcp_resp.to_dict()
                mcp_server = FastMCP(app)
            except Exception as e:
                import logging
                logging.warning(f"SSE用FastMCPサーバ初期化失敗: {e}")
                mcp_server = None
        # TransportManagerに渡す直前の値を明示
        print(f"[DEBUG] TransportManagerに渡す http_host={config.transport.http_host}, http_port={config.transport.http_port}, http_enabled={getattr(config.transport, 'http_enabled', None)}")
        transport_manager = TransportManager(router, config=config, sse_enabled=sse_enabled, mcp_server=mcp_server)


        # サーバ起動
        transport_manager.start_all()

        # --- 暫定: HTTPサーバスレッドが生きている間はメインスレッドを維持 ---
        import time
        http = getattr(transport_manager, "http", None)
        if http and getattr(http, "server_thread", None):
            try:
                while http.server_thread.is_alive():
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\nサーバを停止しています...")

    except KeyboardInterrupt:
        print("\nサーバを停止しています...")
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        sys.exit(1)
    finally:
        # クリーンアップ
        if 'transport_manager' in locals():
            transport_manager.stop_all()
        if 'memory_manager' in locals():
            await memory_manager.close()


if __name__ == "__main__":
    asyncio.run(main())
