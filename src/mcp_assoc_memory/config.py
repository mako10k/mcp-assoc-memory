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
from typing import Any, Dict, List, Optional

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
        Load configuration (CLI > environment variables > config.json > defaults)
        Specification:
          1. If CLI args specify --config, prioritize that path
          2. If not specified, auto-discover ./config.json
          3. If not found, use environment variables/defaults
        """
        config = cls()

        # Load from environment variables
        config._load_from_env()

        # Determine config file path
        config_file = None
        if config_path:
            # Explicitly specified by CLI
            if Path(config_path).exists():
                config_file = config_path
        else:
            # Check environment variable first (for test/alternate configs)
            env_config = os.getenv("MCP_CONFIG_FILE")
            if env_config and Path(env_config).exists():
                config_file = env_config
            else:
                # Auto-discover config.json in current and parent directories
                default_path = Path.cwd() / "config.json"
                parent_path = Path.cwd().parent / "config.json"
                if default_path.exists():
                    config_file = str(default_path)
                elif parent_path.exists():
                    config_file = str(parent_path)

        if config_file:
            config._load_from_file(config_file)

        # Override with CLI arguments
        if cli_args:
            # Reflect transport, port, host, log_level, etc.
            if "log_level" in cli_args and cli_args["log_level"]:
                config.log_level = cli_args["log_level"]
            if "host" in cli_args and cli_args["host"]:
                config.transport.http_host = cli_args["host"]
            if "port" in cli_args and cli_args["port"]:
                config.transport.http_port = cli_args["port"]
            if "transport" in cli_args and cli_args["transport"]:
                # Only enable valid transports to True
                t = cli_args["transport"]
                config.transport.stdio_enabled = t == "stdio"
                config.transport.http_enabled = t == "http"
                config.transport.sse_enabled = t == "sse"

        # Validation
        config._validate()

        return config

    def _load_from_env(self) -> None:
        """Load configuration from environment variables"""
        # Database configuration
        self.database.type = os.getenv("DB_TYPE", self.database.type)
        self.database.path = os.getenv("DB_PATH", self.database.path)
        self.database.host = os.getenv("DB_HOST", self.database.host)
        self.database.port = int(os.getenv("DB_PORT", str(self.database.port)))
        self.database.database = os.getenv("DB_NAME", self.database.database)
        self.database.username = os.getenv("DB_USER", self.database.username)
        self.database.password = os.getenv("DB_PASSWORD", self.database.password)

        # Embedding configuration
        self.embedding.provider = os.getenv("EMBEDDING_PROVIDER", self.embedding.provider)
        self.embedding.model = os.getenv("EMBEDDING_MODEL", self.embedding.model)
        self.embedding.api_key = os.getenv("OPENAI_API_KEY", self.embedding.api_key)

        # Storage configuration
        self.storage.data_dir = os.getenv("DATA_DIR", self.storage.data_dir)
        self.storage.export_dir = os.getenv("EXPORT_DIR", self.storage.export_dir)
        self.storage.import_dir = os.getenv("IMPORT_DIR", self.storage.import_dir)
        self.storage.allow_absolute_paths = os.getenv("ALLOW_ABSOLUTE_PATHS", "false").lower() == "true"
        self.storage.max_export_size_mb = int(os.getenv("MAX_EXPORT_SIZE_MB", str(self.storage.max_export_size_mb)))
        self.storage.max_import_size_mb = int(os.getenv("MAX_IMPORT_SIZE_MB", str(self.storage.max_import_size_mb)))

        # Security configuration
        self.security.auth_enabled = os.getenv("AUTH_ENABLED", "false").lower() == "true"
        self.security.api_key_required = os.getenv("API_KEY_REQUIRED", "false").lower() == "true"
        self.security.jwt_secret = os.getenv("JWT_SECRET", self.security.jwt_secret)

        # Transport configuration
        self.transport.http_host = os.getenv("HTTP_HOST", self.transport.http_host)
        self.transport.http_port = int(os.getenv("HTTP_PORT", str(self.transport.http_port)))
        self.transport.sse_host = os.getenv("SSE_HOST", self.transport.sse_host)
        self.transport.sse_port = int(os.getenv("SSE_PORT", str(self.transport.sse_port)))

        # Other settings
        self.log_level = os.getenv("LOG_LEVEL", self.log_level)
        self.debug_mode = os.getenv("DEBUG", "false").lower() == "true"

        # Expand environment variables in all string settings
        self.database = expand_dict_env_vars(self.database)
        self.embedding = expand_dict_env_vars(self.embedding)
        self.storage = expand_dict_env_vars(self.storage)
        self.security = expand_dict_env_vars(self.security)
        self.transport = expand_dict_env_vars(self.transport)
        self.api = expand_dict_env_vars(self.api)

    def _load_from_file(self, config_path: str) -> None:
        """Load configuration from file"""
        try:
            with open(config_path, "r", encoding="utf-8") as f:
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
