"""
メイン実行ファイル - MCPサーバの起動エントリーポイント
"""

from .server import mcp


if __name__ == "__main__":
    mcp.run(transport="http", port=8000)
