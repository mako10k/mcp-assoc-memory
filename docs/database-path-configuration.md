# Database Output Path Configuration

This document explains the workspace pollution avoidance features implemented in MCP Associative Memory Server.

## Problem Statement

Previously, the server stored database files in a `data` directory within the workspace, which could "pollute" the workspace with data files. This was problematic for:

- Clean workspace management
- Containerized deployments
- Development environments
- Version control (though `.gitignore` helped)

## Solution Overview

The server now uses OS-appropriate user data directories by default, while maintaining full backward compatibility and configuration flexibility.

## Default Behavior

### New Default Paths

Instead of storing in workspace `data/` directory, the server now uses:

- **Linux**: `~/.local/share/mcp-assoc-memory/`
- **macOS**: `~/Library/Application Support/mcp-assoc-memory/`
- **Windows**: `%APPDATA%/mcp-assoc-memory/`

### Specific File Locations

| Component | Old Default | New Default |
|-----------|-------------|-------------|
| SQLite Database | `data/memory.db` | `~/.local/share/mcp-assoc-memory/memory.db` |
| ChromaDB | `data/chroma_db/` | `~/.local/share/mcp-assoc-memory/chroma_db/` |
| Data Directory | `data/` | `~/.local/share/mcp-assoc-memory/` |
| Graph Store | `data/memory_graph.pkl` | `~/.local/share/mcp-assoc-memory/memory_graph.pkl` |
| Exports | `data/exports/` | `~/.local/share/mcp-assoc-memory/exports/` |
| Imports | `data/imports/` | `~/.local/share/mcp-assoc-memory/imports/` |

## Configuration Options

### Environment Variables

Override default paths using environment variables:

```bash
# Override specific paths
export MCP_DATABASE_PATH="/custom/path/memory.db"
export MCP_CHROMA_PATH="/custom/path/chroma_db"
export MCP_DATA_DIR="/custom/data/directory"
export MCP_GRAPH_PATH="/custom/path/graph.pkl"

# Legacy environment variables still work
export DB_PATH="/custom/path/memory.db"
export DATA_DIR="/custom/data/directory"
```

### Configuration File

In `config.json`:

```json
{
  "database": {
    "path": "/custom/path/memory.db"
  },
  "storage": {
    "data_dir": "/custom/data/directory"
  }
}
```

### Automatic Path Resolution

The system intelligently resolves paths:

1. **Absolute paths**: Used as-is (no change in behavior)
2. **Workspace data paths**: Converted to user data directory
   - `data/memory.db` → `~/.local/share/mcp-assoc-memory/memory.db`
   - `./data/chroma_db` → `~/.local/share/mcp-assoc-memory/chroma_db`
3. **Other relative paths**: Default to user data directory
4. **Environment overrides**: Take highest priority

## Backward Compatibility

The system maintains full backward compatibility:

- **Existing absolute paths**: Continue to work unchanged
- **Explicit workspace paths**: Can be forced by using absolute paths like `/path/to/workspace/data/memory.db`
- **Configuration files**: Existing configurations continue to work
- **Legacy environment variables**: `DB_PATH`, `DATA_DIR` still supported

## Migration Guide

### No Action Required

For most users, no action is required. The server will automatically:

1. Create new user data directories on first run
2. Use the new non-polluting defaults
3. Work seamlessly with existing configurations

### Explicit Workspace Usage

To continue using workspace paths (old behavior):

**Option 1: Environment Variables**
```bash
export MCP_DATA_DIR="./data"
export MCP_DATABASE_PATH="./data/memory.db"
```

**Option 2: Configuration File**
```json
{
  "database": {
    "path": "./data/memory.db"
  },
  "storage": {
    "data_dir": "./data"
  }
}
```

**Option 3: Absolute Paths**
```bash
export MCP_DATA_DIR="/full/path/to/workspace/data"
```

### Custom Data Locations

To use completely custom paths:

```bash
# Example: Store in /var/lib for system service
export MCP_DATA_DIR="/var/lib/mcp-assoc-memory"

# Example: Store in user's Documents
export MCP_DATA_DIR="$HOME/Documents/MCP-Data"

# Example: Store in temporary directory
export MCP_DATA_DIR="/tmp/mcp-test-data"
```

## Benefits

### Workspace Cleanliness
- No database files in project directory
- Cleaner version control
- Easier workspace management

### OS Integration
- Follows platform conventions
- Proper user data isolation
- Better system integration

### Flexibility
- Environment variable overrides
- Configuration file support
- Backward compatibility

### Security
- User-scoped data storage
- No root directory pollution
- Predictable permission model

## Technical Implementation

The implementation uses:

- `pathlib.Path` for cross-platform path handling
- Platform detection for OS-specific defaults
- XDG Base Directory Specification (Linux)
- Standard Application Support directories (macOS/Windows)
- Environment variable expansion
- Smart path resolution logic

## Testing

To verify the new behavior:

```bash
# Run the included test script
python test_paths.py

# Check actual paths being used
python -c "
from mcp_assoc_memory.config import Config
config = Config()
print(f'Database: {config.database.path}')
print(f'Data dir: {config.storage.data_dir}')
"
```

## Examples

### Development Environment
```bash
# Use workspace data for development
export MCP_DATA_DIR="./dev-data"
```

### Production Deployment
```bash
# Use system data directory
export MCP_DATA_DIR="/var/lib/mcp-assoc-memory"
```

### User Installation
```bash
# Default behavior - uses ~/.local/share/mcp-assoc-memory/
# No configuration needed
```

### Containerized Deployment
```bash
# Mount external volume
export MCP_DATA_DIR="/data"
# docker run -v mcp-data:/data ...
```

This implementation provides workspace pollution avoidance while maintaining maximum flexibility and backward compatibility.