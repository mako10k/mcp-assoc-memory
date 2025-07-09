"""
STDIOトランスポートハンドラー（雛形）
"""

import json
import sys
import threading


class StdioTransport:
    """
    STDIO通信を担当
    """

    def __init__(self, router):
        self.router = router
        self.running = False
        self.thread = None

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._serve, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=1)

    def _serve(self):
        while self.running:
            line = sys.stdin.readline()
            if not line:
                break
            try:
                req = json.loads(line)
                resp = self.router.route(req)
                print(json.dumps(resp), flush=True)
            except Exception as e:
                print(json.dumps({"error": str(e)}), flush=True)
