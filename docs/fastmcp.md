# fastmcp公式SDK利用方針・API仕様

## 基本方針
- MCPサーバのSSE/WebSocketトランスポートは、必ず公式SDK（PyPI: fastmcp）の FastMCP クラスを利用する。
- FastMCPの初期化・依存注入は、公式ドキュメント・現物API仕様に厳密に従うこと。
- routerや独自ハンドラを直接渡すのではなく、FastAPIアプリや公式が要求する型・構造で渡す。
- 公式SDKのバージョンアップ時は必ずAPI仕様変更を確認し、現場設計に反映する。

## 参考リンク
- [fastmcp PyPI](https://pypi.org/project/fastmcp/)
- [fastmcp GitHub](https://github.com/fastmcp/fastmcp)
- [公式ドキュメント（API/実装例）](https://github.com/fastmcp/fastmcp#usage)

## 実装例・注意点
- main.py等でSSE有効時は `from fastmcp import FastMCP` でimportする。
- FastMCPの初期化は `FastMCP(app: FastAPI, ...)` など、公式の推奨パターンで行う。
- routerやMCPToolRouterを直接渡す設計は禁止。
- 依存注入・ラップが必要な場合はFastAPIのAPIRouter等を活用し、公式サンプルに準拠する。

---

このファイルは「SSE/WSトランスポート・公式SDK利用」に関する全ての設計判断の根拠・参照元とする。
