"""
構造化ログ設定ユーティリティ
"""
import logging
from typing import Any, Dict, Optional, Tuple

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s', datefmt='%Y-%m-%dT%H:%M:%S')


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
                '[%(asctime)s][%(levelname)s][%(name)s] %(message)s'
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
                '[%(asctime)s][%(levelname)s][%(name)s] %(message)s'
            )
            sh.setFormatter(formatter)
            self.addHandler(sh)
        for handler in self.handlers:
            handler.setLevel(logging.DEBUG)

    def log(self, level: str, message: str, **kwargs: Any) -> None:
        # カスタムパラメータを処理
        error_code = kwargs.pop('error_code', None)
        extra_data = kwargs.pop('extra_data', None)
        error = kwargs.pop('error', None)
        
        # extraに統合
        extra = {}
        if error_code:
            extra['error_code'] = error_code
        if extra_data:
            extra.update(extra_data)
        if error:
            extra['error'] = error
        
        # 残りのkwargsもextraに含める
        extra.update(kwargs)
        
        # メッセージを拡張
        if error_code or error:
            extended_message = message
            if error_code:
                extended_message += f" [Error Code: {error_code}]"
            if error:
                extended_message += f" [Error: {error}]"
            message = extended_message
        
        super().log(getattr(logging, level.upper(), logging.INFO), message, extra=extra if extra else None)

    def info(self, message: str, **kwargs: Any) -> None:
        self.log("info", message, **kwargs)

    def debug(self, message: str, **kwargs: Any) -> None:
        self.log("debug", message, **kwargs)

    def warning(self, message: str, **kwargs: Any) -> None:
        self.log("warning", message, **kwargs)

    def error(self, message: str, **kwargs: Any) -> None:
        self.log("error", message, **kwargs)


class LoggerWrapper:
    """標準ロガーラッパー - カスタムパラメータを処理"""
    
    def __init__(self, logger: logging.Logger):
        self._logger = logger
    
    def _format_message(self, message: str, **kwargs: Any) -> Tuple[str, Optional[Dict[str, Any]]]:
        """メッセージとextraを処理"""
        error_code = kwargs.pop('error_code', None)
        extra_data = kwargs.pop('extra_data', None)
        error = kwargs.pop('error', None)
        
        # extraに統合
        extra = {}
        if error_code:
            extra['error_code'] = error_code
        if extra_data:
            extra.update(extra_data)
        if error:
            extra['error'] = error
        
        # 残りのkwargsもextraに含める
        extra.update(kwargs)
        
        # メッセージを拡張
        if error_code or error:
            extended_message = message
            if error_code:
                extended_message += f" [Error Code: {error_code}]"
            if error:
                extended_message += f" [Error: {error}]"
            message = extended_message
        
        return message, extra if extra else None
    
    def info(self, message: str, *args, **kwargs: Any) -> None:
        formatted_msg, extra = self._format_message(message, **kwargs)
        self._logger.info(formatted_msg, *args, extra=extra)
    
    def debug(self, message: str, *args, **kwargs: Any) -> None:
        formatted_msg, extra = self._format_message(message, **kwargs)
        self._logger.debug(formatted_msg, *args, extra=extra)
    
    def warning(self, message: str, *args, **kwargs: Any) -> None:
        formatted_msg, extra = self._format_message(message, **kwargs)
        self._logger.warning(formatted_msg, *args, extra=extra)
    
    def error(self, message: str, *args, **kwargs: Any) -> None:
        formatted_msg, extra = self._format_message(message, **kwargs)
        self._logger.error(formatted_msg, *args, extra=extra)


def get_memory_logger(name: str = "mcp_assoc_memory"):
    """カスタムパラメータ対応ロガーを返す"""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s][%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    logger.propagate = True
    return LoggerWrapper(logger)
