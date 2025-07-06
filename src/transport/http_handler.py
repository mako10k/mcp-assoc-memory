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
    def __init__(self, router):
        self.router = router
        self.app = FastAPI()
        self._setup_routes()
        self.server_thread = None

    def _setup_routes(self):
        @self.app.post("/mcp")
        async def mcp_endpoint(request: Request):
            req_json = await request.json()
            resp = self.router.route(req_json)
            return resp

    def start(self):
        def run():
            uvicorn.run(self.app, host="0.0.0.0", port=8000, log_level="info")
        self.server_thread = threading.Thread(target=run, daemon=True)
        self.server_thread.start()

    def stop(self):
        # uvicornのプログラム的停止は省略（本番はSIGTERM等で管理）
        pass
