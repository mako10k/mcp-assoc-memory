"""
メイン実行ファイル - MCPサーバの起動エントリーポイント
"""

import asyncio
import argparse
import sys
from typing import Optional

from .config import Config
from .transport.manager import TransportManager
from .core.memory_manager import MemoryManager
from .utils.logging import setup_logging


async def main():
    """メイン実行関数"""
    parser = argparse.ArgumentParser(description="MCP連想記憶サーバ")
    parser.add_argument(
        "--transport",
        choices=["stdio", "http", "sse"],
        default="stdio",
        help="トランスポート方式 (デフォルト: stdio)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="HTTPポート番号 (デフォルト: 8000)"
    )
    parser.add_argument(
        "--host",
        default="localhost",
        help="HTTPホスト名 (デフォルト: localhost)"
    )
    parser.add_argument(
        "--config",
        help="設定ファイルパス"
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="ログレベル (デフォルト: INFO)"
    )

    args = parser.parse_args()

    # 設定読み込み
    config = Config.load(args.config)

    # ログ設定
    setup_logging(args.log_level)

    try:
        # 記憶管理システム初期化
        memory_manager = MemoryManager(config)
        await memory_manager.initialize()

        # トランスポート管理システム初期化
        transport_manager = TransportManager(memory_manager, config)

        # サーバ起動
        await transport_manager.start(
            transport_type=args.transport,
            host=args.host,
            port=args.port
        )

    except KeyboardInterrupt:
        print("\nサーバを停止しています...")
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        sys.exit(1)
    finally:
        # クリーンアップ
        if 'transport_manager' in locals():
            await transport_manager.stop()
        if 'memory_manager' in locals():
            await memory_manager.close()


if __name__ == "__main__":
    asyncio.run(main())
