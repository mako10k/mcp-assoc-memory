"""
設定管理モジュール
環境変数とデフォルト値を管理
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, Optional
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class DatabaseConfig:
    """データベース設定"""
    type: str = "sqlite"  # sqlite, postgresql
    path: str = "data/memory.db"  # SQLiteの場合
    host: str = "localhost"  # PostgreSQLの場合
    port: int = 5432
    database: str = "mcp_memory"
    username: str = ""
    password: str = ""
    pool_size: int = 10


@dataclass
class EmbeddingConfig:
    """埋め込み設定"""
    provider: str = "openai"  # openai, sentence_transformers, local
    model: str = "text-embedding-3-small"
    api_key: str = ""
    cache_size: int = 1000
    batch_size: int = 100


@dataclass
class StorageConfig:
    """ストレージ設定"""
    data_dir: str = "data"
    vector_store_type: str = "chromadb"  # chromadb, faiss, local
    graph_store_type: str = "networkx"  # networkx, neo4j
    backup_enabled: bool = True
    backup_interval_hours: int = 24


@dataclass
class SecurityConfig:
    """セキュリティ設定"""
    auth_enabled: bool = False
    api_key_required: bool = False
    jwt_secret: str = ""
    session_timeout_minutes: int = 60
    rate_limit_requests_per_minute: int = 100


@dataclass
class TransportConfig:
    """トランスポート設定"""
    stdio_enabled: bool = True
    http_enabled: bool = True
    sse_enabled: bool = True
    http_host: str = "localhost"
    http_port: int = 8000
    sse_host: str = "localhost"
    sse_port: int = 8001
    cors_origins: list = field(default_factory=lambda: ["*"])


@dataclass
class Config:
    """メイン設定クラス"""
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    embedding: EmbeddingConfig = field(default_factory=EmbeddingConfig)
    storage: StorageConfig = field(default_factory=StorageConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    transport: TransportConfig = field(default_factory=TransportConfig)

    log_level: str = "INFO"
    debug_mode: bool = False

    @classmethod
    def load(cls, config_path: Optional[str] = None) -> "Config":
        """設定を読み込み"""
        config = cls()

        # 環境変数から設定を読み込み
        config._load_from_env()

        # 設定ファイルがあれば読み込み
        if config_path and Path(config_path).exists():
            config._load_from_file(config_path)

        # バリデーション
        config._validate()

        return config

    def _load_from_env(self):
        """環境変数から設定を読み込み"""
        # データベース設定
        self.database.type = os.getenv("DB_TYPE", self.database.type)
        self.database.path = os.getenv("DB_PATH", self.database.path)
        self.database.host = os.getenv("DB_HOST", self.database.host)
        self.database.port = int(os.getenv("DB_PORT", str(self.database.port)))
        self.database.database = os.getenv("DB_NAME", self.database.database)
        self.database.username = os.getenv("DB_USER", self.database.username)
        self.database.password = os.getenv(
            "DB_PASSWORD", self.database.password)

        # 埋め込み設定
        self.embedding.provider = os.getenv(
            "EMBEDDING_PROVIDER", self.embedding.provider)
        self.embedding.model = os.getenv(
            "EMBEDDING_MODEL", self.embedding.model)
        self.embedding.api_key = os.getenv(
            "OPENAI_API_KEY", self.embedding.api_key)

        # ストレージ設定
        self.storage.data_dir = os.getenv("DATA_DIR", self.storage.data_dir)

        # セキュリティ設定
        self.security.auth_enabled = os.getenv(
            "AUTH_ENABLED", "false").lower() == "true"
        self.security.api_key_required = os.getenv(
            "API_KEY_REQUIRED", "false").lower() == "true"
        self.security.jwt_secret = os.getenv(
            "JWT_SECRET", self.security.jwt_secret)

        # トランスポート設定
        self.transport.http_host = os.getenv(
            "HTTP_HOST", self.transport.http_host)
        self.transport.http_port = int(
            os.getenv(
                "HTTP_PORT", str(
                    self.transport.http_port)))
        self.transport.sse_host = os.getenv(
            "SSE_HOST", self.transport.sse_host)
        self.transport.sse_port = int(
            os.getenv(
                "SSE_PORT", str(
                    self.transport.sse_port)))

        # その他
        self.log_level = os.getenv("LOG_LEVEL", self.log_level)
        self.debug_mode = os.getenv("DEBUG", "false").lower() == "true"

    def _load_from_file(self, config_path: str):
        """設定ファイルから読み込み"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)

            # 設定をマージ（ファイルが優先）
            self._merge_config(config_data)

        except Exception as e:
            logger.warning(f"設定ファイルの読み込みに失敗: {e}")

    def _merge_config(self, config_data: Dict[str, Any]):
        """設定データをマージ"""
        for section, values in config_data.items():
            if hasattr(self, section) and isinstance(values, dict):
                section_obj = getattr(self, section)
                for key, value in values.items():
                    if hasattr(section_obj, key):
                        setattr(section_obj, key, value)

    def _validate(self):
        """設定値のバリデーション"""
        # データディレクトリの作成
        Path(self.storage.data_dir).mkdir(parents=True, exist_ok=True)

        # 必須設定のチェック
        if self.embedding.provider == "openai" and not self.embedding.api_key:
            logger.warning("OpenAI API keyが設定されていません")

        if self.security.auth_enabled and not self.security.jwt_secret:
            raise ValueError("認証が有効ですがJWT secretが設定されていません")

    def to_dict(self) -> Dict[str, Any]:
        """設定を辞書形式で取得"""
        return {
            "database": self.database.__dict__,
            "embedding": self.embedding.__dict__,
            "storage": self.storage.__dict__,
            "security": self.security.__dict__,
            "transport": self.transport.__dict__,
            "log_level": self.log_level,
            "debug_mode": self.debug_mode,
        }


# グローバル設定インスタンス
_global_config = None


def get_config() -> Dict[str, Any]:
    """グローバル設定を取得"""
    global _global_config
    if _global_config is None:
        _global_config = Config.load()
    return _global_config.to_dict()


def set_config(config: Config) -> None:
    """グローバル設定を設定"""
    global _global_config
    _global_config = config
