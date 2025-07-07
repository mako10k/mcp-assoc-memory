"""
TransportManager（雛形）
"""

from .stdio_handler import StdioTransport
from .http_handler import HttpTransport
from .sse_handler import SseTransport

class TransportManager:
    """
    各種トランスポート（STDIO/HTTP/SSE）を管理するマネージャ
    """
    def __init__(self, router, config=None, sse_enabled=False, mcp_server=None):
        # 設定値取得
        stdio_enabled = True
        http_enabled = True
        sse_enabled_flag = sse_enabled
        http_host = "0.0.0.0"
        http_port = 8000
        if config is not None:
            stdio_enabled = getattr(config.transport, "stdio_enabled", True)
            http_enabled = getattr(config.transport, "http_enabled", True)
            http_host = getattr(config.transport, "http_host", "0.0.0.0")
            http_port = getattr(config.transport, "http_port", 8000)
            sse_enabled_flag = getattr(config.transport, "sse_enabled", sse_enabled)

        self.stdio = StdioTransport(router) if stdio_enabled else None
        self.http = HttpTransport(router, host=http_host, port=http_port, enabled=http_enabled)
        if sse_enabled_flag and mcp_server is not None:
            try:
                from .sse_handler import SseTransport
                # mount_pathを"/mcp"に変更し、/mcpでSSEストリームを受け付ける
                self.sse = SseTransport(mcp_server, mount_path="/mcp")
            except Exception as e:
                import logging
                logging.warning(f"SSEトランスポート初期化失敗: {e}")
                self.sse = None
        else:
            self.sse = None

    def start_all(self):
        # すべての有効なトランスポートを起動
        if self.stdio:
            self.stdio.start()
        if self.http:
            self.http.start()
        if self.sse:
            self.sse.start()

    def stop_all(self):
        # すべての有効なトランスポートを停止
        if self.stdio:
            self.stdio.stop()
        if self.http:
            self.http.stop()
        if self.sse:
            self.sse.stop()
