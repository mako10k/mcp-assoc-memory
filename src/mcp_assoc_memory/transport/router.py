"""
RequestRouter（雛形）
"""


class RequestRouter:
    """
    リクエストルーティングを担当
    """

    def __init__(self):
        # ハンドラーを格納する辞書
        self.handlers = {}

    def register(self, method, func):
        """
        メソッドと関数の関連付けを行う
        """
        self.handlers[method] = func

    def route(self, request):
        """
        リクエストに基づいて適切なハンドラーを呼び出す
        """
        method = request.get("method")
        params = request.get("params", {})
        if method in self.handlers:
            return self.handlers[method](**params)
        return {"error": f"Unknown method: {method}"}
