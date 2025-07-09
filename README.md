# MCP Associative Memory Server

A Model Context Protocol (MCP) server implementing associative memory for LLMs using FastMCP 2.0.

## Overview

This project provides an MCP server that enables LLMs to efficiently store information and retrieve related content through associative memory. The system combines vector embeddings with graph structures to create memory systems similar to human associative memory.

## Key Features

- **Memory Storage**: Store text information as vector embeddings organized by domains
- **Semantic Search**: Advanced memory retrieval based on semantic similarity
- **Related Memory**: Retrieve associated memories through graph relationships
- **Memory Management**: Basic memory operations (store, search, get, delete)
- **Domain Organization**: Organize memories by domains (user, project, global, session)
- **Vector Similarity**: Efficient similarity search using embeddings

## MCP Tools (FastMCP 2.0)

The server provides **5 core tools** using FastMCP 2.0 best practices:

1. **`memory_store`** - Store new memory with content, domain, and metadata
2. **`memory_search`** - Search memories using semantic similarity
3. **`memory_get`** - Retrieve specific memory by ID
4. **`memory_delete`** - Delete memory by ID
5. **`memory_list_all`** - List all stored memories

## MCP Resources

- **`memory_stats`** - Memory statistics and domain information
- **`domain_memories/{domain}`** - Memories for specific domain

## MCP Prompts

- **`analyze_memories`** - Analyze memory patterns for a domain
- **`summarize_memory`** - Generate summary for a specific memory

## Unsupported Features

For features removed during FastMCP migration, see [FASTMCP_UNSUPPORTED_FEATURES.md](FASTMCP_UNSUPPORTED_FEATURES.md).

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

🤖 **AI Development Agent**: [AGENT.md](AGENT.md)  
📋 **GitHub Copilot Rules**: [.github/copilot-instructions.md](.github/copilot-instructions.md)  
⚡ **FastMCP Migration**: [FASTMCP_FINAL_REPORT.md](FASTMCP_FINAL_REPORT.md)

### Documentation

- **[Unsupported Features](FASTMCP_UNSUPPORTED_FEATURES.md)** - Features not available in FastMCP
- **[Migration Report](FASTMCP_MIGRATION_REPORT.md)** - FastMCP migration details
- **[Specification](SPECIFICATION.md)** - API specifications and feature details
- **[Architecture](ARCHITECTURE.md)** - System design and components
- **[Project Structure](PROJECT_STRUCTURE.md)** - Directory structure and file organization

### Contributing

1. Check [development guidelines](.github/copilot-instructions.md) before contributing
2. Update relevant documentation when making changes
3. Follow FastMCP 2.0 best practices for tool implementation

## License

MIT License


