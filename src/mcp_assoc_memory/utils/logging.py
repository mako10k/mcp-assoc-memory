"""
ログ設定ユーティリティ
構造化ログの設定と管理
"""

import logging
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path


class StructuredFormatter(logging.Formatter):
    """構造化ログフォーマッター"""
    
    def format(self, record: logging.LogRecord) -> str:
        """ログレコードを構造化JSONに変換"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # 追加情報があれば含める
        if hasattr(record, 'extra_data'):
            log_entry.update(record.extra_data)
        
        # 例外情報があれば含める
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry, ensure_ascii=False)


class MemoryLogger:
    """記憶システム専用ログ"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
    
    def memory_stored(self, memory_id: str, domain: str, content_length: int, **kwargs):
        """記憶保存ログ"""
        self.logger.info(
            "Memory stored",
            extra={
                "extra_data": {
                    "action": "memory_stored",
                    "memory_id": memory_id,
                    "domain": domain,
                    "content_length": content_length,
                    **kwargs
                }
            }
        )
    
    def memory_searched(self, query: str, domain: str, result_count: int, duration_ms: float, **kwargs):
        """記憶検索ログ"""
        self.logger.info(
            "Memory searched",
            extra={
                "extra_data": {
                    "action": "memory_searched",
                    "query": query,
                    "domain": domain,
                    "result_count": result_count,
                    "duration_ms": duration_ms,
                    **kwargs
                }
            }
        )
    
    def memory_accessed(self, memory_id: str, domain: str, access_type: str, **kwargs):
        """記憶アクセスログ"""
        self.logger.info(
            "Memory accessed",
            extra={
                "extra_data": {
                    "action": "memory_accessed",
                    "memory_id": memory_id,
                    "domain": domain,
                    "access_type": access_type,
                    **kwargs
                }
            }
        )
    
    def error(self, message: str, error_code: str = None, **kwargs):
        """エラーログ"""
        self.logger.error(
            message,
            extra={
                "extra_data": {
                    "action": "error",
                    "error_code": error_code,
                    **kwargs
                }
            }
        )
    
    def info(self, message: str, extra_data: Dict[str, Any] = None, **kwargs):
        """情報ログ"""
        data = {"action": "info"}
        if extra_data:
            data.update(extra_data)
        data.update(kwargs)
        
        self.logger.info(
            message,
            extra={"extra_data": data}
        )
    
    def debug(self, message: str, extra_data: Dict[str, Any] = None, **kwargs):
        """デバッグログ"""
        data = {"action": "debug"}
        if extra_data:
            data.update(extra_data)
        data.update(kwargs)
        
        self.logger.debug(
            message,
            extra={"extra_data": data}
        )
    
    def warning(
        self,
        message: str,
        extra_data: Dict[str, Any] = None,
        **kwargs
    ):
        """警告ログ"""
        data = {"action": "warning"}
        if extra_data:
            data.update(extra_data)
        data.update(kwargs)
        
        self.logger.warning(
            message,
            extra={"extra_data": data}
        )


class PerformanceTimer:
    """パフォーマンス測定"""
    
    def __init__(self, logger: logging.Logger, operation: str):
        self.logger = logger
        self.operation = operation
        self.start_time = None
    
    def __enter__(self):
        """コンテキスト開始"""
        self.start_time = datetime.utcnow()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """コンテキスト終了"""
        if self.start_time:
            duration = (
                datetime.utcnow() - self.start_time
            ).total_seconds() * 1000
            self.logger.info(
                f"Operation completed: {self.operation}",
                extra={
                    "extra_data": {
                        "action": "performance",
                        "operation": self.operation,
                        "duration_ms": duration,
                        "success": exc_type is None
                    }
                }
            )


def setup_logging(level: str = "INFO", log_file: Optional[str] = None) -> None:
    """ログ設定を初期化"""
    
    # ログレベル設定
    numeric_level = getattr(logging, level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {level}")
    
    # ルートロガー設定
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # 既存のハンドラーをクリア
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # コンソールハンドラー
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(StructuredFormatter())
    root_logger.addHandler(console_handler)
    
    # ファイルハンドラー（オプション）
    if log_file:
        file_path = Path(log_file)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(file_path, encoding='utf-8')
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(StructuredFormatter())
        root_logger.addHandler(file_handler)
    
    # 外部ライブラリのログレベル調整
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("chromadb").setLevel(logging.WARNING)


def get_memory_logger(name: str) -> MemoryLogger:
    """記憶システム専用ログの取得"""
    return MemoryLogger(name)
