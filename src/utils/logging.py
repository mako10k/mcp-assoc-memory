"""
構造化ログ設定ユーティリティ
"""
import logging
from typing import Any, Dict, Optional

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s %(extra)s', datefmt='%Y-%m-%dT%H:%M:%S')

class StructuredLogger(logging.Logger):
    def __init__(self, name: str = "mcp_assoc_memory"):
        super().__init__(name)
        self.setLevel(logging.DEBUG)
        self.propagate = True

        # ルートロガーもDEBUG/StreamHandler必須
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        if not root_logger.handlers:
            sh = logging.StreamHandler()
            sh.setLevel(logging.DEBUG)
            formatter = logging.Formatter(
                '[%(asctime)s][%(levelname)s][%(name)s] %(message)s %(extra)s'
            )
            sh.setFormatter(formatter)
            root_logger.addHandler(sh)
        for handler in root_logger.handlers:
            handler.setLevel(logging.DEBUG)

        # 自分自身のハンドラもDEBUG
        for handler in self.handlers:
            handler.setLevel(logging.DEBUG)
        if not self.handlers:
            sh = logging.StreamHandler()
            sh.setLevel(logging.DEBUG)
            formatter = logging.Formatter(
                '[%(asctime)s][%(levelname)s][%(name)s] %(message)s %(extra)s'
            )
            sh.setFormatter(formatter)
            self.addHandler(sh)
        for handler in self.handlers:
            handler.setLevel(logging.DEBUG)

    def log(self, level: str, message: str, **kwargs: Any) -> None:
        # loggingのextraはdictで、ユーザー定義キーを追加できる
        # ただしextraに'levelname'や'message'などlogging予約語は使えない
        extra = kwargs if kwargs else {}
        if "extra" not in extra:
            extra["extra"] = ""
        super().log(getattr(logging, level.upper(), logging.INFO), message, extra=extra)

    def info(self, message: str, **kwargs: Any) -> None:
        self.log("info", message, **kwargs)

    def debug(self, message: str, **kwargs: Any) -> None:
        self.log("debug", message, **kwargs)

    def warning(self, message: str, **kwargs: Any) -> None:
        self.log("warning", message, **kwargs)

    def error(self, message: str, **kwargs: Any) -> None:
        self.log("error", message, **kwargs)

def get_memory_logger(name: str = "mcp_assoc_memory"):
    return StructuredLogger(name)
