"""
構造化ログ設定ユーティリティ
"""
import logging
from typing import Any, Dict, Optional

class StructuredLogger:
    def __init__(self, name: str = "mcp_assoc_memory"):
        self.logger = logging.getLogger(name)
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            fmt='%(asctime)s %(levelname)s %(message)s %(extra)s',
            datefmt='%Y-%m-%dT%H:%M:%S'
        )
        handler.setFormatter(formatter)
        if not self.logger.handlers:
            self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

    def log(self, level: str, message: str, **kwargs: Any) -> None:
        extra = {"extra": kwargs}
        self.logger.log(getattr(logging, level.upper(), logging.INFO), message, extra=extra)

    def info(self, message: str, **kwargs: Any) -> None:
        self.log("info", message, **kwargs)

    def debug(self, message: str, **kwargs: Any) -> None:
        self.log("debug", message, **kwargs)

    def warning(self, message: str, **kwargs: Any) -> None:
        self.log("warning", message, **kwargs)

    def error(self, message: str, **kwargs: Any) -> None:
        self.log("error", message, **kwargs)

logger = StructuredLogger()
