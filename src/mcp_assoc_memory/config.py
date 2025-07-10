"""
Configuration management module
Manages environment variables and default values
"""

import json
import logging
import os
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
    provider: str = "openai"  # openai, sentence_transformers, local
    model: str = "text-embedding-3-small"
    api_key: str = ""
    cache_size: int = 1000
    batch_size: int = 100


@dataclass
class StorageConfig:
    """Storage configuration"""
    data_dir: str = "data"
    vector_store_type: str = "chromadb"  # chromadb, faiss, local
    graph_store_type: str = "networkx"  # networkx, neo4j
    backup_enabled: bool = True
    backup_interval_hours: int = 24


@dataclass
class SecurityConfig:
    """Security configuration"""
    auth_enabled: bool = False
    api_key_required: bool = False
    jwt_secret: str = ""
    session_timeout_minutes: int = 60
    rate_limit_requests_per_minute: int = 100


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

    log_level: str = "INFO"
    debug_mode: bool = False

    @classmethod
    def load(
        cls,
        config_path: Optional[str] = None,
        cli_args: Optional[dict] = None
    ) -> "Config":
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
            # Auto-discover config.json in current and parent directories
            default_path = Path.cwd() / "config.json"
            parent_path = Path.cwd().parent / "config.json"
            if default_path.exists():
                config_file = str(default_path)
            elif parent_path.exists():
                config_file = str(parent_path)

        print(f"[DEBUG] config_file resolved: {config_file}")
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

    def _load_from_env(self):
        """Load configuration from environment variables"""
        # Database configuration
        self.database.type = os.getenv("DB_TYPE", self.database.type)
        self.database.path = os.getenv("DB_PATH", self.database.path)
        self.database.host = os.getenv("DB_HOST", self.database.host)
        self.database.port = int(os.getenv("DB_PORT", str(self.database.port)))
        self.database.database = os.getenv("DB_NAME", self.database.database)
        self.database.username = os.getenv("DB_USER", self.database.username)
        self.database.password = os.getenv(
            "DB_PASSWORD", self.database.password)

        # Embedding configuration
        self.embedding.provider = os.getenv(
            "EMBEDDING_PROVIDER", self.embedding.provider)
        self.embedding.model = os.getenv(
            "EMBEDDING_MODEL", self.embedding.model)
        self.embedding.api_key = os.getenv(
            "OPENAI_API_KEY", self.embedding.api_key)

        # Storage configuration
        self.storage.data_dir = os.getenv("DATA_DIR", self.storage.data_dir)

        # Security configuration
        self.security.auth_enabled = os.getenv(
            "AUTH_ENABLED", "false").lower() == "true"
        self.security.api_key_required = os.getenv(
            "API_KEY_REQUIRED", "false").lower() == "true"
        self.security.jwt_secret = os.getenv(
            "JWT_SECRET", self.security.jwt_secret)

        # Transport configuration
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

        # Other settings
        self.log_level = os.getenv("LOG_LEVEL", self.log_level)
        self.debug_mode = os.getenv("DEBUG", "false").lower() == "true"

    def _load_from_file(self, config_path: str):
        """Load configuration from file"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)

            print(f"[DEBUG] config.json loaded: {config_data}")
            # Merge configuration (file takes priority)
            self._merge_config(config_data)
            print(f"[DEBUG] after merge: http_host={self.transport.http_host}, http_port={self.transport.http_port}, http_enabled={getattr(self.transport, 'http_enabled', None)}")

        except Exception as e:
            logger.warning(f"Failed to load configuration file: {e}")

    def _merge_config(self, config_data: Dict[str, Any]):
        """Merge configuration data (transport uses dataclass regeneration for strict reflection)"""
        print(f"[DEBUG] _merge_config input: {config_data}")
        for section, values in config_data.items():
            if section == "transport" and isinstance(values, dict):
                # TransportConfig only: dict → dataclass regeneration
                self.transport = TransportConfig(**values)
                print(f"[DEBUG] after TransportConfig dataclass: {self.transport}")
            elif hasattr(self, section) and isinstance(values, dict):
                section_obj = getattr(self, section)
                for key, value in values.items():
                    if hasattr(section_obj, key):
                        setattr(section_obj, key, value)

    def _validate(self):
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
            "log_level": self.log_level,
            "debug_mode": self.debug_mode,
        }


# Global configuration instance
_global_config = None


def get_config() -> Dict[str, Any]:
    """Get global configuration"""
    global _global_config
    if _global_config is None:
        _global_config = Config.load()
    return _global_config.to_dict()


def set_config(config: Config) -> None:
    """Set global configuration"""
    global _global_config
    _global_config = config
