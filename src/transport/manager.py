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
    def __init__(self, router):
        self.stdio = StdioTransport(router)
        self.http = HttpTransport(router)
        self.sse = SseTransport(router)

    def start_all(self):
        # TODO: すべてのトランスポートを起動
        self.stdio.start()
        self.http.start()
        self.sse.start()

    def stop_all(self):
        # TODO: すべてのトランスポートを停止
        self.stdio.stop()
        self.http.stop()
        self.sse.stop()
