# Configuration Guide - MCP Associative Memory Server

This guide covers the centralized configuration management system introduced in v0.1.5, including setup, environment variables, and troubleshooting.

## 🏗️ Configuration Architecture

The MCP Associative Memory Server uses a **centralized configuration management system** with clear precedence rules and comprehensive environment variable support.

### Priority Order (Highest to Lowest)
1. **CLI Arguments** - Direct command line parameters
2. **Environment Variables** - System/container environment
3. **Configuration File** - JSON configuration file
4. **Default Values** - Built-in fallback values

## 📋 Quick Setup

### 1. Basic Setup
```bash
# Copy example configuration
cp config.example.json config.json

# Set OpenAI API key (if using OpenAI embeddings)
export OPENAI_API_KEY="sk-your-actual-api-key-here"

# Start server
python -m mcp_assoc_memory.server --config config.json
```

### 2. VS Code Integration
Create or update `.vscode/mcp.json`:
```json
{
  "servers": {
    "AssocMemory": {
      "command": "python3",
      "args": ["-m", "mcp_assoc_memory.server", "--config", "config.json"],
      "cwd": "${workspaceFolder}",
      "env": {
        "PYTHONPATH": "${workspaceFolder}/src",
        "LOG_LEVEL": "INFO",
        "MCP_LOG_LEVEL": "INFO"
      },
      "type": "stdio"
    }
  }
}
```

## ⚙️ Configuration Sections

### Core Settings
```json
{
  "log_level": "INFO",           // DEBUG, INFO, WARNING, ERROR, CRITICAL
  "debug_mode": false           // Enable debug features
}
```

### Database Configuration
```json
{
  "database": {
    "type": "sqlite",           // sqlite, postgresql
    "path": "data/memory.db",   // SQLite file path
    "host": "localhost",        // PostgreSQL host
    "port": 5432,              // PostgreSQL port
    "database": "mcp_memory",   // PostgreSQL database name
    "username": "",            // PostgreSQL username
    "password": ""             // PostgreSQL password
  }
}
```

### Embedding Configuration
```json
{
  "embedding": {
    "provider": "openai",                    // openai, local, sentence_transformer
    "api_key": "${OPENAI_API_KEY}",        // API key (supports env var expansion)
    "model": "text-embedding-3-small",     // Embedding model
    "cache_size": 1000,                    // Embedding cache size
    "batch_size": 100                      // Batch processing size
  }
}
```

**Supported Providers:**
- **`openai`**: OpenAI text-embedding models (requires API key)
- **`local`**: SentenceTransformers (local processing, no API key needed)
- **`sentence_transformer`**: Alias for local processing

### Storage Configuration
```json
{
  "storage": {
    "data_dir": "data",                    // Base data directory
    "vector_store_type": "chromadb",       // chromadb, faiss, local
    "graph_store_type": "networkx",        // networkx, neo4j
    "backup_enabled": true,                // Enable automatic backups
    "backup_interval_hours": 24,           // Backup interval
    "export_dir": "data/exports",          // Export directory
    "import_dir": "data/imports",          // Import directory
    "allow_absolute_paths": false,         // Allow absolute file paths
    "max_export_size_mb": 100,             // Maximum export file size
    "max_import_size_mb": 100              // Maximum import file size
  }
}
```

### Transport Configuration
```json
{
  "transport": {
    "stdio_enabled": true,      // STDIO transport (recommended for MCP)
    "http_enabled": false,      // HTTP API transport
    "sse_enabled": false,       // Server-Sent Events transport
    "http_host": "localhost",   // HTTP bind address
    "http_port": 3006,         // HTTP port
    "sse_host": "localhost",    // SSE bind address
    "sse_port": 8001,          // SSE port
    "cors_origins": ["*"]       // CORS allowed origins
  }
}
```

### Security Configuration
```json
{
  "security": {
    "auth_enabled": false,                      // Enable authentication
    "api_key_required": false,                  // Require API key
    "jwt_secret": "",                          // JWT signing secret
    "session_timeout_minutes": 60,             // Session timeout
    "rate_limit_requests_per_minute": 100      // Rate limiting
  }
}
```

### API Configuration
```json
{
  "api": {
    "enable_response_metadata": false,     // Include metadata in responses
    "enable_audit_trail": false,           // Enable audit logging
    "force_minimal_metadata": false,       // Force minimal responses
    "minimal_response_max_size": 1024,     // Minimal response size limit
    "remove_null_values": true,            // Clean null values from responses
    "enable_response_caching": false,      // Enable response caching
    "cache_ttl_seconds": 300               // Cache TTL
  }
}
```

## 🌍 Environment Variables

### Core Environment Variables
| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `LOG_LEVEL` | Logging level | `INFO` | `DEBUG` |
| `MCP_LOG_LEVEL` | MCP-specific logging | Auto-synced with `LOG_LEVEL` | `INFO` |
| `DEBUG` | Debug mode | `false` | `true` |

### Database Environment Variables
| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `DB_TYPE` | Database type | `sqlite` | `postgresql` |
| `DB_PATH` | SQLite file path | `data/memory.db` | `./memory.db` |
| `DB_HOST` | PostgreSQL host | `localhost` | `db.example.com` |
| `DB_PORT` | PostgreSQL port | `5432` | `5432` |
| `DB_NAME` | PostgreSQL database | `mcp_memory` | `production_memory` |
| `DB_USER` | PostgreSQL username | - | `mcp_user` |
| `DB_PASSWORD` | PostgreSQL password | - | `secure_password` |

### Embedding Environment Variables
| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `EMBEDDING_PROVIDER` | Embedding provider | `openai` | `local` |
| `EMBEDDING_MODEL` | Embedding model | Provider-specific | `text-embedding-3-small` |
| `OPENAI_API_KEY` | OpenAI API key | - | `sk-proj-...` |

### Storage Environment Variables
| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `DATA_DIR` | Base data directory | `data` | `/app/data` |
| `EXPORT_DIR` | Export directory | `data/exports` | `/backups/exports` |
| `IMPORT_DIR` | Import directory | `data/imports` | `/data/imports` |
| `ALLOW_ABSOLUTE_PATHS` | Allow absolute paths | `false` | `true` |
| `MAX_EXPORT_SIZE_MB` | Max export size | `100` | `500` |
| `MAX_IMPORT_SIZE_MB` | Max import size | `100` | `500` |

### Transport Environment Variables
| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `HTTP_HOST` | HTTP bind address | `localhost` | `0.0.0.0` |
| `HTTP_PORT` | HTTP port | `3006` | `8080` |
| `SSE_HOST` | SSE bind address | `localhost` | `0.0.0.0` |
| `SSE_PORT` | SSE port | `8001` | `8001` |

### Security Environment Variables
| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `AUTH_ENABLED` | Enable authentication | `false` | `true` |
| `API_KEY_REQUIRED` | Require API key | `false` | `true` |
| `JWT_SECRET` | JWT signing secret | - | `your-secret-key` |

## 🔧 Environment Variable Expansion

The configuration system supports environment variable expansion in string values:

```json
{
  "embedding": {
    "api_key": "${OPENAI_API_KEY}",
    "model": "${EMBEDDING_MODEL:-text-embedding-3-small}"
  },
  "storage": {
    "data_dir": "${DATA_DIR:-data}"
  }
}
```

**Syntax:**
- `${VAR_NAME}`: Required variable (fails if not set)
- `${VAR_NAME:-default}`: Optional variable with default value

## 🚀 Deployment Examples

### Docker Environment
```bash
# Environment file (.env)
LOG_LEVEL=INFO
OPENAI_API_KEY=sk-your-key
DATA_DIR=/app/data
HTTP_HOST=0.0.0.0
HTTP_PORT=8080

# Docker run
docker run -d \
  --env-file .env \
  -v ./data:/app/data \
  -p 8080:8080 \
  mcp-assoc-memory:latest
```

### Kubernetes ConfigMap
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: mcp-config
data:
  LOG_LEVEL: "INFO"
  EMBEDDING_PROVIDER: "openai"
  DATA_DIR: "/app/data"
  HTTP_HOST: "0.0.0.0"
  HTTP_PORT: "8080"
```

### Production Configuration
```json
{
  "log_level": "WARNING",
  "embedding": {
    "provider": "openai",
    "api_key": "${OPENAI_API_KEY}",
    "cache_size": 5000
  },
  "storage": {
    "data_dir": "/app/data",
    "backup_enabled": true,
    "backup_interval_hours": 6
  },
  "transport": {
    "stdio_enabled": false,
    "http_enabled": true,
    "http_host": "0.0.0.0",
    "http_port": 8080
  },
  "security": {
    "auth_enabled": true,
    "api_key_required": true,
    "rate_limit_requests_per_minute": 1000
  }
}
```

## 🐛 Troubleshooting

### Common Configuration Issues

#### 1. Pydantic Validation Errors
```
CRITICAL: 1 validation error for Settings
log_level
  Input should be 'DEBUG', 'INFO', 'WARNING', 'ERROR' or 'CRITICAL'
```

**Solution**: Ensure `log_level` uses uppercase values:
```bash
# Correct
export LOG_LEVEL=INFO

# Incorrect
export LOG_LEVEL=info
```

#### 2. OpenAI API Key Format Errors
```
CRITICAL: Invalid OpenAI API key format
```

**Solution**: Verify API key format:
```bash
# Correct formats
export OPENAI_API_KEY="sk-proj-..."  # New format
export OPENAI_API_KEY="sk-..."       # Legacy format

# Remove any quotes or extra characters
```

#### 3. Missing Configuration File
```
WARNING: Failed to load configuration file: [Errno 2] No such file or directory
```

**Solution**: Create configuration file:
```bash
cp config.example.json config.json
# Edit config.json with your settings
```

#### 4. Environment Variable Not Recognized
```
WARNING: Unknown environment variable: INVALID_VAR
```

**Solution**: Check [environment variable list](#environment-variables) for supported variables.

### Configuration Validation

Test your configuration:
```python
# Quick validation script
import sys
sys.path.insert(0, 'src')
from mcp_assoc_memory.config import ConfigurationManager
import os

# Set test environment variables
os.environ['LOG_LEVEL'] = 'DEBUG'
os.environ['EMBEDDING_PROVIDER'] = 'local'

# Load and validate configuration
manager = ConfigurationManager()
config = manager.load_configuration('config.json')

print(f'✅ Configuration loaded successfully')
print(f'Log Level: {config.log_level}')
print(f'Embedding Provider: {config.embedding.provider}')
print(f'Data Directory: {config.storage.data_dir}')
```

### Debug Configuration Loading

Enable debug logging to trace configuration loading:
```bash
LOG_LEVEL=DEBUG python -m mcp_assoc_memory.server --config config.json
```

This will show:
- Configuration file loading process
- Environment variable processing
- Validation results
- Final configuration values

## 📚 Related Documentation

- **[Installation Guide](../README.md#installation)** - Setup and installation
- **[API Reference](docs/api-reference/README.md)** - Tool documentation
- **[Troubleshooting](docs/troubleshooting/README.md)** - Common issues and solutions
- **[Development Guide](development/README.md)** - Development setup

---

**Note**: This centralized configuration system was introduced in v0.1.5 to improve maintainability and resolve Pydantic validation issues. For older versions, refer to the legacy configuration documentation.
