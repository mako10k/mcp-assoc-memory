[![CI](https://github.com/mako10k/mcp-assoc-memory/actions/workflows/ci.yml/badge.svg)](https://github.com/mako10k/mcp-assoc-memory/actions)
[![Coverage](https://img.shields.io/badge/coverage-100%25-brightgreen)](./htmlcov/index.html)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![PyPI](https://img.shields.io/pypi/v/mcp-assoc-memory.svg)](https://pypi.org/project/mcp-assoc-memory/)

# MCP Associative Memory Server

🧠 **Production-Ready Intelligent Memory System** - Store, search, and discover knowledge connections using the Model Context Protocol (MCP) with **74/74 tests passing** and **complete CI/CD pipeline**.

## 🏆 Production Status (July 2025)

**✅ ENTERPRISE-READY:**
- **74/74 tests passing** (100% success rate)
- **Complete CI/CD pipeline** with security and quality gates
- **10 MCP tools** for comprehensive memory management
- **Sub-second performance** with optimized vector search
- **Docker containerized** for production deployment

## 🌟 Overview

Transform your development workflow with an AI-powered memory system that:
- **Stores insights** from your daily work and learning
- **Finds related knowledge** when you need it most  
- **Discovers unexpected connections** between ideas
- **Organizes knowledge** in intuitive hierarchical scopes
- **Syncs across environments** for seamless workflow integration

Built with **FastMCP 2.0** for modern LLM integration, optimized for **GitHub Copilot** workflows.

## ✨ Key Features

### 🧠 **Intelligent Memory Operations**
- **Semantic Search**: Find relevant memories using natural language queries
- **Association Discovery**: Automatically discover connections between concepts
- **Complete CRUD**: Create, Read, Update, Delete with full lifecycle management
- **Smart Organization**: Hierarchical scopes with auto-categorization

### 🔍 **Advanced Discovery**
- **Top-K Search**: Optimized threshold (0.1) with LLM-guided relevance judgment
- **Cross-Scope Associations**: Find connections across different knowledge scopes
- **Similarity Scoring**: Transparent relevance metrics for intelligent filtering
- **Creative Connections**: Discover unexpected relationships for innovation

### 🗂️ **Powerful Organization**
- **Hierarchical Scopes**: `work/projects/name`, `learning/technology`, `personal/ideas`
- **Flexible Categorization**: Tags, metadata, and automatic scope suggestions
- **Session Management**: Temporary workspaces for project isolation
- **Memory Movement**: Reorganize knowledge as understanding evolves

### 🔄 **Cross-Environment Sync**
- **Export/Import**: Backup and restore memories across development environments
- **Multiple Formats**: JSON, YAML with compression support
- **Merge Strategies**: Handle duplicates intelligently during sync
- **Git Workflow**: Integrate memory backup into version control processes

### 🛠️ **Developer Experience**
- **GitHub Copilot Integration**: Natural language memory operations
- **VS Code Tasks**: One-click server management and maintenance
- **Real-time Association**: Automatic relationship discovery during storage
- **Performance Optimized**: Sub-second search across thousands of memories
- **Response Level Control**: Minimal, standard, or full detail responses for optimal token usage

### ⚡ **Smart Response Levels**
Control response detail and token usage with three intelligent levels:

- **`minimal`**: Essential information only (~50 tokens) - Perfect for status checks and basic operations
- **`standard`**: Balanced detail for workflow continuity (default) - Optimal for most use cases  
- **`full`**: Comprehensive data including metadata, associations, and analysis - Ideal for debugging and detailed exploration

**Example Usage:**
```python
# Quick status check
memory_store(content="meeting notes", response_level="minimal")
# Returns: {"success": true, "message": "Memory stored", "memory_id": "..."}

# Full debugging info
memory_search(query="project ideas", response_level="full") 
# Returns: Complete results with similarity scores, metadata, associations
```

## 🎯 Complete MCP Tool Suite

### 🚀 **Modern API (10 Clean Tools)**

### Core Operations (Primary API)
- **`memory_store`** - Store new memories with auto-association
- **`memory_search`** - Unified search with standard and diversified modes
- **`memory_manage`** - Get, update, and delete memory operations  
- **`memory_sync`** - Import and export memories for backup/sync

### Discovery and Analysis
- **`memory_discover_associations`** - Find semantically related memories
- **`memory_list_all`** - Browse complete memory collection with pagination

### Organization Management  
- **`scope_list`** - Browse hierarchical memory organization
- **`scope_suggest`** - AI-powered scope recommendations
- **`memory_move`** - Reorganize memories into better categories

### Session Management
- **`session_manage`** - Create, list, and cleanup temporary working sessions

### 🎯 **Clean, Modern API**
All tools use intuitive, natural names with powerful unified interfaces for better developer experience.

## 📚 Comprehensive Documentation

### 🚀 **[Quick Start Guide](docs/user-guide/QUICK_START.md)**
Get up and running in 5 minutes with essential commands and patterns.

### 💡 **[Best Practices](docs/user-guide/BEST_PRACTICES.md)**  
Comprehensive guide to optimizing your associative memory workflow.

### 🔧 **[API Reference](docs/api-reference/README.md)**
Complete technical documentation for all MCP tools and parameters.

### 🏢 **[Real-World Examples](docs/examples/README.md)**
Practical usage patterns for developers, teams, and organizations.

### 🆘 **[Troubleshooting Guide](docs/troubleshooting/README.md)**
Solutions for common issues and system maintenance procedures.

### 📊 **[Sample Data](examples/sample-data/README.md)**
Ready-to-import memory dataset with 28 curated memories demonstrating system capabilities.

## 🚀 **[Complete Documentation →](docs/README.md)**

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   LLM Client    │────│  FastMCP Server │────│  Memory Store   │
│                 │    │                 │    │                 │
│ - Claude        │    │ - @app.tool()   │    │ - ChromaDB      │
│ - ChatGPT       │    │ - @app.resource()│   │ - SQLite        │
│ - Custom LLM    │    │ - @app.prompt() │    │ - NetworkX      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Technology Stack

- **Language**: Python 3.11+
- **MCP Framework**: FastMCP 2.0
- **Vector Database**: ChromaDB
- **Embedding Model**: OpenAI Embeddings / Sentence Transformers  
- **Graph Database**: NetworkX (in-memory)
- **Storage**: SQLite (metadata)

## Installation & Usage

For detailed setup instructions, see `docs/installation.md`.

## Server Startup

### Direct STDIO Mode (Recommended)

**Standard MCP startup method:**

```bash
python -m mcp_assoc_memory.server --config config.json
```

The server operates in **STDIO mode** for direct MCP client integration. This is the recommended approach for VS Code Copilot and other MCP clients.

### Configuration

The server uses a centralized configuration management system that supports multiple configuration sources with clear precedence:

**Priority Order**: CLI arguments > Environment variables > Configuration file > Defaults

#### Quick Setup
1. Copy `config.example.json` to `config.json`
2. Set your OpenAI API key: `export OPENAI_API_KEY="sk-your-key"`
3. Start the server: `python -m mcp_assoc_memory.server --config config.json`

#### Configuration Sources

**Configuration File** (`config.json`):
```json
{
  "log_level": "INFO",
  "embedding": {
    "provider": "openai",
    "api_key": "${OPENAI_API_KEY}",
    "model": "text-embedding-3-small"
  },
  "transport": {
    "stdio_enabled": true,
    "http_enabled": false
  }
}
```

**Environment Variables**:
- `OPENAI_API_KEY`: OpenAI API key for embeddings
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `MCP_LOG_LEVEL`: MCP-specific logging (auto-synced with LOG_LEVEL)
- `EMBEDDING_PROVIDER`: Override embedding provider (openai, local, sentence_transformer)
- `DATA_DIR`: Override data directory location

**VS Code Integration** (`.vscode/mcp.json`):
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

## 🛠️ Installation (PyPI, pipx, GitHub)

### Recommended: PyPI
```bash
pip install mcp-assoc-memory
```

### pipx (isolated global install)
```bash
pipx install mcp-assoc-memory
```

### GitHub (latest/dev version)
```bash
pip install git+https://github.com/mako10k/mcp-assoc-memory.git
# or
pipx install git+https://github.com/mako10k/mcp-assoc-memory.git
```


### Start the server (after install)
```bash
python -m mcp_assoc_memory.server --config config.json
```

- Configure via `.vscode/mcp.json` for VS Code Copilot integration
- MCPクライアントや自動検出ツール（Claude Desktop Extensions, FastMCP, Cursor等）からも自動認識されます。
- Dockerイメージも近日公開予定。

---

## Developer Information


### Development Guidelines

🤖 **AI Development Agent**: [development/workflow/AGENT.md](development/workflow/AGENT.md)  
📋 **GitHub Copilot Rules**: [.github/copilot-instructions.md](.github/copilot-instructions.md)  
🔄 **Development Workflow**: [development/workflow/DEVELOPER_GUIDELINES.md](development/workflow/DEVELOPER_GUIDELINES.md)

---

## ✅ Quality Status

All code passes **mypy (type check)**, **flake8 (lint)**, and **pytest (unit/integration tests)** as of July 2025.  
CI/CD pipeline enforces these checks for every commit.

### Technical Reference

- **[System Architecture](development/architecture/)** - Architecture and structure documentation
- **[Technical Specifications](development/specifications/)** - API specs and feature details
- **[Security & Configuration](development/security/)** - Authentication and transport configuration
- **[Knowledge Base](development/knowledge/)** - Curated development knowledge
- **[Complete Development Docs →](development/README.md)**

### Contributing

1. Check [development guidelines](development/workflow/DEVELOPER_GUIDELINES.md) before contributing
2. Review [architecture documentation](development/architecture/) for system understanding
3. Follow [GitHub Copilot instructions](.github/copilot-instructions.md) for AI-assisted development
4. Update relevant documentation when making changes

## 🚀 Quick Start

### 1. Clone the repository
```bash
git clone https://github.com/mako10k/mcp-assoc-memory.git
cd mcp-assoc-memory
```

### 2. Set up your environment
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 4. Run tests and linting
```bash
python scripts/smart_lint.py
pytest tests/ -v
```

### 5. Start the MCP server
```bash
python -m mcp_assoc_memory.server --config config.json
```

For Docker users:
```bash
docker-compose up --build
```

---

## License

MIT License


