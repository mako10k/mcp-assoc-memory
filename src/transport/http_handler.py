"""
HTTPトランスポートハンドラー（雛形）
"""

from fastapi import FastAPI, Request
import uvicorn
import threading

class HttpTransport:
    """
    HTTP API (FastAPI) を担当
    """
    def __init__(self, router, host="0.0.0.0", port=8000, enabled=True):
        self.router = router
        self.host = host
        self.port = port
        self.enabled = enabled
        self.app = FastAPI()
        self._setup_routes()
        self.server_thread = None

    def _setup_routes(self):
        @self.app.post("/mcp")
        async def mcp_endpoint(request: Request):
            req_json = await request.json()
            resp = await self.router.route(req_json)
            return resp

    def start(self):
        if not self.enabled:
            return
        def run():
            uvicorn.run(self.app, host=self.host, port=self.port, log_level="info")
        self.server_thread = threading.Thread(target=run, daemon=True)
        self.server_thread.start()

    def stop(self):
        # uvicornのプログラム的停止は省略（本番はSIGTERM等で管理）
        pass
