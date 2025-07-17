"""
Configuration management module
Manages environment variables and default values
"""

import json
import logging
import os
import re
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


@dataclass
class DatabaseConfig:
    """Database configuration"""

    type: str = "sqlite"  # sqlite, postgresql
    path: str = "data/memory.db"  # For SQLite
    host: str = "localhost"  # For PostgreSQL
    port: int = 5432
    database: str = "mcp_memory"
    username: str = ""
    password: str = ""
    pool_size: int = 10


@dataclass
class EmbeddingConfig:
    """Embedding configuration"""

    provider: str = ""  # "openai" or "local" - will be auto-determined if not set
    model: str = ""  # Will be set based on provider: "text-embedding-3-small" for openai, "all-MiniLM-L6-v2" for local
    api_key: str = ""
    cache_size: int = 1000
    batch_size: int = 100
    
    def _determine_default_provider(self) -> str:
        """Determine default provider based on API key availability"""
        if self.provider:
            return self.provider  # Explicit provider selection takes precedence
        
        # Auto-determine based on API key availability
        api_key = self.api_key or os.getenv("OPENAI_API_KEY", "")
        if api_key and api_key.strip():
            return "openai"
        else:
            return "local"
    
    def _determine_default_model(self, provider: str) -> str:
        """Determine default model based on provider"""
        if self.model:
            return self.model  # Explicit model selection takes precedence
            
        if provider == "openai":
            return "text-embedding-3-small"
        elif provider in ["local", "sentence_transformer"]:
            return "all-MiniLM-L6-v2"
        else:
            raise ValueError(f"Unsupported provider: {provider}")
    
    def __post_init__(self):
        """Initialize provider and model with defaults if not explicitly set"""
        # Determine provider if not set
        if not self.provider:
            self.provider = self._determine_default_provider()
        
        # Validate provider
        if self.provider not in ["openai", "local", "sentence_transformer"]:
            raise ValueError(f"Invalid provider '{self.provider}'. Must be 'openai', 'local', or 'sentence_transformer'")
        
        # Determine model if not set
        if not self.model:
            self.model = self._determine_default_model(self.provider)
        
        # Provider-specific validation
        if self.provider == "openai":
            api_key = self.api_key or os.getenv("OPENAI_API_KEY", "")
            if not api_key or not api_key.strip():
                raise ValueError("OpenAI provider requires OPENAI_API_KEY environment variable or api_key in config")


@dataclass
class StorageConfig:
    """Storage configuration"""

    data_dir: str = "data"
    vector_store_type: str = "chromadb"  # chromadb, faiss, local
    graph_store_type: str = "networkx"  # networkx, neo4j
    backup_enabled: bool = True
    backup_interval_hours: int = 24

    # File sync configuration
    export_dir: str = "exports"  # Directory for memory exports
    import_dir: str = "imports"  # Directory for memory imports
    allow_absolute_paths: bool = False  # Allow absolute file paths
    max_export_size_mb: int = 100  # Maximum export file size
    max_import_size_mb: int = 100  # Maximum import file size


@dataclass
class SecurityConfig:
    """Security configuration"""

    auth_enabled: bool = False
    api_key_required: bool = False
    jwt_secret: str = ""
    session_timeout_minutes: int = 60
    rate_limit_requests_per_minute: int = 100


@dataclass
class APIConfig:
    """API configuration for response processing"""

    # Response metadata configuration
    enable_response_metadata: bool = False
    enable_audit_trail: bool = False
    force_minimal_metadata: bool = False
    minimal_response_max_size: int = 1024  # bytes

    # Response processing configuration
    remove_null_values: bool = True

    # Caching configuration
    enable_response_caching: bool = False
    cache_ttl_seconds: int = 300


@dataclass
class TransportConfig:
    """Transport configuration"""

    stdio_enabled: bool = True
    http_enabled: bool = True
    sse_enabled: bool = True
    http_host: str = "localhost"
    http_port: int = 8000
    sse_host: str = "localhost"
    sse_port: int = 8001
    cors_origins: List[str] = field(default_factory=lambda: ["*"])


@dataclass
class Config:
    """Main configuration class"""

    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    embedding: EmbeddingConfig = field(default_factory=EmbeddingConfig)
    storage: StorageConfig = field(default_factory=StorageConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    transport: TransportConfig = field(default_factory=TransportConfig)
    api: APIConfig = field(default_factory=APIConfig)

    log_level: str = "INFO"
    debug_mode: bool = False

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value with dict-like interface"""
        if hasattr(self, key):
            return getattr(self, key)
        return default

    @classmethod
    def load(cls, config_path: Optional[str] = None, cli_args: Optional[dict] = None) -> "Config":
        """
        Load configuration using centralized configuration manager
        
        Priority: CLI args > environment variables > config file > defaults
        """
        manager = ConfigurationManager()
        return manager.load_configuration(config_path, cli_args)

    def _validate(self) -> None:
        """Validate configuration values"""
        # Create data directory
        Path(self.storage.data_dir).mkdir(parents=True, exist_ok=True)

        # Check required settings
        if self.embedding.provider == "openai" and not self.embedding.api_key:
            logger.warning("OpenAI API key is not configured")

        if self.security.auth_enabled and not self.security.jwt_secret:
            raise ValueError("Authentication is enabled but JWT secret is not configured")

    def _load_from_file(self, config_path: str) -> None:
        """Load configuration from file"""
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                if config_path.endswith(('.yaml', '.yml')):
                    import yaml
                    config_data = yaml.safe_load(f)
                else:
                    config_data = json.load(f)

            # 環境変数展開を実行
            config_data = expand_dict_env_vars(config_data)
            logger.info(f"Configuration loaded from {config_path} with environment variable expansion")

            # Merge configuration (file takes priority)
            self._merge_config(config_data)

        except Exception as e:
            logger.warning(f"Failed to load configuration file: {e}")

    def _merge_config(self, config_data: Dict[str, Any]) -> None:
        """Merge configuration data (transport uses dataclass regeneration for strict reflection)"""
        for section, values in config_data.items():
            if section == "transport" and isinstance(values, dict):
                # TransportConfig only: dict → dataclass regeneration
                self.transport = TransportConfig(**values)
            elif hasattr(self, section) and isinstance(values, dict):
                section_obj = getattr(self, section)
                for key, value in values.items():
                    if hasattr(section_obj, key):
                        setattr(section_obj, key, value)

    def _validate(self) -> None:
        """Validate configuration values"""
        # Create data directory
        Path(self.storage.data_dir).mkdir(parents=True, exist_ok=True)

        # Check required settings
        if self.embedding.provider == "openai" and not self.embedding.api_key:
            logger.warning("OpenAI API key is not configured")

        if self.security.auth_enabled and not self.security.jwt_secret:
            raise ValueError("Authentication is enabled but JWT secret is not configured")

    def to_dict(self) -> Dict[str, Any]:
        """Get configuration in dictionary format"""
        return {
            "database": self.database.__dict__,
            "embedding": self.embedding.__dict__,
            "storage": self.storage.__dict__,
            "security": self.security.__dict__,
            "transport": self.transport.__dict__,
            "api": self.api.__dict__,
            "log_level": self.log_level,
            "debug_mode": self.debug_mode,
        }


def expand_environment_variables(text: str) -> str:
    """
    環境変数展開機能
    ${VAR_NAME} または $VAR_NAME 形式の環境変数を展開する
    """
    if not isinstance(text, str):
        return text

    # ${VAR_NAME} 形式の環境変数を展開
    def replace_env_var(match):
        var_name = match.group(1)
        return os.getenv(var_name, match.group(0))  # 見つからない場合は元のまま

    # ${VAR_NAME} パターンを置換
    result = re.sub(r"\$\{([A-Za-z_][A-ZaZ0-9_]*)\}", replace_env_var, text)

    return result


def expand_dict_env_vars(data: Any) -> Any:
    """
    辞書やリスト内の環境変数を再帰的に展開
    """
    if isinstance(data, dict):
        return {key: expand_dict_env_vars(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [expand_dict_env_vars(item) for item in data]
    elif isinstance(data, str):
        return expand_environment_variables(data)
    else:
        return data


class EnvironmentMapping:
    """Environment variable mapping configuration"""
    
    # 環境変数の統一マッピング定義
    ENV_MAPPINGS = {
        # ログとデバッグ設定
        "log_level": ["LOG_LEVEL", "MCP_LOG_LEVEL"],
        "debug_mode": ["DEBUG", "DEBUG_MODE"],
        
        # データベース設定
        "database.type": ["DB_TYPE"],
        "database.path": ["DB_PATH"],
        "database.host": ["DB_HOST"],
        "database.port": ["DB_PORT"],
        "database.database": ["DB_NAME"],
        "database.username": ["DB_USER"],
        "database.password": ["DB_PASSWORD"],
        
        # 埋め込み設定
        "embedding.provider": ["EMBEDDING_PROVIDER"],
        "embedding.model": ["EMBEDDING_MODEL"],
        "embedding.api_key": ["OPENAI_API_KEY", "EMBEDDING_API_KEY"],
        "embedding.cache_size": ["EMBEDDING_CACHE_SIZE"],
        "embedding.batch_size": ["EMBEDDING_BATCH_SIZE"],
        
        # ストレージ設定
        "storage.data_dir": ["DATA_DIR"],
        "storage.export_dir": ["EXPORT_DIR"],
        "storage.import_dir": ["IMPORT_DIR"],
        "storage.allow_absolute_paths": ["ALLOW_ABSOLUTE_PATHS"],
        "storage.max_export_size_mb": ["MAX_EXPORT_SIZE_MB"],
        "storage.max_import_size_mb": ["MAX_IMPORT_SIZE_MB"],
        
        # セキュリティ設定
        "security.auth_enabled": ["AUTH_ENABLED"],
        "security.api_key_required": ["API_KEY_REQUIRED"],
        "security.jwt_secret": ["JWT_SECRET"],
        
        # トランスポート設定
        "transport.http_host": ["HTTP_HOST"],
        "transport.http_port": ["HTTP_PORT"],
        "transport.sse_host": ["SSE_HOST"],
        "transport.sse_port": ["SSE_PORT"],
        "transport.stdio_enabled": ["STDIO_ENABLED"],
        "transport.http_enabled": ["HTTP_ENABLED"],
        "transport.sse_enabled": ["SSE_ENABLED"],
    }
    
    @classmethod
    def get_env_value(cls, config_key: str) -> Optional[str]:
        """環境変数から値を取得（優先順位考慮）"""
        env_keys = cls.ENV_MAPPINGS.get(config_key, [])
        for env_key in env_keys:
            value = os.getenv(env_key)
            if value is not None:
                return value
        return None
    
    @classmethod
    def set_env_value(cls, config_key: str, value: str) -> None:
        """設定値を対応する環境変数に設定"""
        env_keys = cls.ENV_MAPPINGS.get(config_key, [])
        for env_key in env_keys:
            os.environ[env_key] = value


class ConfigurationManager:
    """一元化された設定管理クラス"""
    
    def __init__(self):
        self.env_mapping = EnvironmentMapping()
    
    def load_configuration(self, config_path: Optional[str] = None, cli_args: Optional[dict] = None) -> "Config":
        """
        設定を一元的に読み込み・マージ
        
        優先順位: CLI引数 > 環境変数 > 設定ファイル > デフォルト値
        """
        # 1. デフォルト設定を作成
        config = Config()
        
        # 2. 設定ファイルから読み込み
        if config_path or self._find_config_file():
            file_path = config_path or self._find_config_file()
            if file_path:
                self._load_from_file(config, file_path)
        
        # 3. 環境変数で上書き
        self._apply_environment_overrides(config)
        
        # 4. CLI引数で最終上書き
        if cli_args:
            self._apply_cli_overrides(config, cli_args)
        
        # 5. 環境変数を設定に合わせて統一
        self._sync_environment_variables(config)
        
        # 6. バリデーション実行
        config._validate()
        
        return config
    
    def _find_config_file(self) -> Optional[str]:
        """設定ファイルを自動発見"""
        # 環境変数でのファイル指定
        env_config = os.getenv("MCP_CONFIG_FILE")
        if env_config and Path(env_config).exists():
            return env_config
        
        # 標準的な場所を検索
        candidates = [
            Path.cwd() / "config.json",
            Path.cwd().parent / "config.json",
            Path.cwd() / "config.yaml",
            Path.cwd() / "config.yml"
        ]
        
        for candidate in candidates:
            if candidate.exists():
                return str(candidate)
        
        return None
    
    def _load_from_file(self, config: "Config", file_path: str) -> None:
        """設定ファイルから読み込み"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                if file_path.endswith(('.yaml', '.yml')):
                    import yaml
                    config_data = yaml.safe_load(f)
                else:
                    config_data = json.load(f)
            
            # 環境変数展開
            config_data = expand_dict_env_vars(config_data)
            logger.info(f"Configuration loaded from {file_path}")
            
            # 設定をマージ
            self._merge_config_data(config, config_data)
            
        except Exception as e:
            logger.warning(f"Failed to load configuration file {file_path}: {e}")
    
    def _apply_environment_overrides(self, config: "Config") -> None:
        """環境変数による上書きを適用"""
        for config_key in EnvironmentMapping.ENV_MAPPINGS:
            env_value = EnvironmentMapping.get_env_value(config_key)
            if env_value is not None:
                self._set_config_value(config, config_key, env_value)
    
    def _apply_cli_overrides(self, config: "Config", cli_args: dict) -> None:
        """CLI引数による上書きを適用"""
        cli_mappings = {
            "log_level": "log_level",
            "debug": "debug_mode",
            "host": "transport.http_host", 
            "port": "transport.http_port",
            "transport": None  # 特別処理
        }
        
        for cli_key, config_key in cli_mappings.items():
            if cli_key in cli_args and cli_args[cli_key] is not None:
                if cli_key == "transport":
                    # トランスポートタイプの特別処理
                    self._set_transport_from_cli(config, cli_args[cli_key])
                elif config_key:
                    self._set_config_value(config, config_key, cli_args[cli_key])
    
    def _sync_environment_variables(self, config: "Config") -> None:
        """設定値を対応する環境変数に同期"""
        # 重要な設定を環境変数に反映
        EnvironmentMapping.set_env_value("log_level", config.log_level)
        
        if hasattr(config, 'embedding') and hasattr(config.embedding, 'api_key'):
            if config.embedding.api_key:
                EnvironmentMapping.set_env_value("embedding.api_key", config.embedding.api_key)
    
    def _set_config_value(self, config: "Config", key_path: str, value: str) -> None:
        """ドット記法で設定値をセット"""
        parts = key_path.split('.')
        obj = config
        
        # 最後の要素以外をたどる
        for part in parts[:-1]:
            if hasattr(obj, part):
                obj = getattr(obj, part)
            else:
                return
        
        # 最終的な属性に値を設定
        final_key = parts[-1]
        if hasattr(obj, final_key):
            # 型変換を実行
            converted_value = self._convert_value(getattr(obj, final_key), value)
            setattr(obj, final_key, converted_value)
    
    def _convert_value(self, current_value: Any, new_value: str) -> Any:
        """現在の値の型に基づいて新しい値を変換"""
        if isinstance(current_value, bool):
            return new_value.lower() in ("true", "1", "yes", "on")
        elif isinstance(current_value, int):
            return int(new_value)
        elif isinstance(current_value, float):
            return float(new_value)
        elif isinstance(current_value, list):
            return new_value.split(",") if new_value else []
        else:
            return new_value
    
    def _set_transport_from_cli(self, config: "Config", transport_type: str) -> None:
        """CLI引数のトランスポートタイプを設定"""
        config.transport.stdio_enabled = transport_type == "stdio"
        config.transport.http_enabled = transport_type == "http"
        config.transport.sse_enabled = transport_type == "sse"
    
    def _merge_config_data(self, config: "Config", config_data: Dict[str, Any]) -> None:
        """設定データをConfigオブジェクトにマージ"""
        for section, values in config_data.items():
            if section == "transport" and isinstance(values, dict):
                # TransportConfigの特別処理
                from .config import TransportConfig
                config.transport = TransportConfig(**values)
            elif hasattr(config, section) and isinstance(values, dict):
                section_obj = getattr(config, section)
                for key, value in values.items():
                    if hasattr(section_obj, key):
                        setattr(section_obj, key, value)
            elif hasattr(config, section):
                setattr(config, section, values)


# Global configuration instance - Singleton pattern
_global_config: Optional[Config] = None
_config_lock = threading.Lock()


def get_config() -> Config:
    """
    Get global configuration instance (Singleton pattern)

    Returns:
        Config: The global configuration instance

    Note:
        This ensures all parts of the application use the same configuration
        instance, preventing configuration drift and inconsistencies.
    """
    global _global_config

    # Double-checked locking pattern for thread safety
    if _global_config is None:
        with _config_lock:
            if _global_config is None:
                _global_config = Config.load()
                logger.info(
                    f"Initialized global Config singleton with api config: {hasattr(_global_config.api, 'default_response_level')}"
                )

    return _global_config


def set_config(config: Config) -> None:
    """
    Set global configuration instance

    Args:
        config: Configuration instance to set as global

    Note:
        This should be called during application initialization
        to ensure consistent configuration across all modules.
    """
    global _global_config
    with _config_lock:
        _global_config = config
        logger.info(f"Set global Config singleton with api config: {hasattr(config.api, 'default_response_level')}")


def initialize_config(config_path: Optional[str] = None) -> Config:
    """
    Initialize global configuration with specific config file

    Args:
        config_path: Path to configuration file (optional)

    Returns:
        Config: The initialized configuration instance

    Note:
        This should be called once during application startup
        to load configuration from the specified file path.
    """
    global _global_config
    with _config_lock:
        _global_config = Config.load(config_path)
        logger.info(f"Initialized global Config from {config_path or 'default locations'}")
        logger.info(f"API config loaded: {hasattr(_global_config.api, 'default_response_level')}")
        if hasattr(_global_config.api, "default_response_level"):
            logger.info(f"Default response level: {_global_config.api.default_response_level}")

    return _global_config
