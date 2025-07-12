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

### Recommended: FastMCP Server

Start the MCP server using **`python -m mcp_assoc_memory`**:

```bash
python3 -m mcp_assoc_memory
```

The server starts in STDIO mode by default for MCP client integration.

### Environment Variables

- `OPENAI_API_KEY`: Required for OpenAI embeddings
- `MCP_LOG_LEVEL`: Set logging level (DEBUG, INFO, WARNING, ERROR)

### Server Control Scripts

- Start:   `./scripts/mcp_server_daemon.sh start`
- Stop:    `./scripts/mcp_server_daemon.sh stop`  
- Restart: `./scripts/mcp_server_daemon.sh restart`
- Status:  `./scripts/mcp_server_daemon.sh status`

### Logs & PID Files

- Logs: `logs/mcp_server.log`
- PID:  `logs/mcp_server.pid`

## Developer Information

### Development Guidelines

🤖 **AI Development Agent**: [development/workflow/AGENT.md](development/workflow/AGENT.md)  
📋 **GitHub Copilot Rules**: [.github/copilot-instructions.md](.github/copilot-instructions.md)  
🔄 **Development Workflow**: [development/workflow/DEVELOPER_GUIDELINES.md](development/workflow/DEVELOPER_GUIDELINES.md)

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

## License

MIT License


