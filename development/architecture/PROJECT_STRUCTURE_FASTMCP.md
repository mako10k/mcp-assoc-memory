# Project Structure - FastMCP Implementation

## Directory Structure

```
/workspaces/mcp-assoc-memory/
├── 📚 Documentation
│   ├── README.md                              # Project overview (English)
│   ├── SPECIFICATION_FASTMCP.md               # API specifications for FastMCP
│   ├── ARCHITECTURE_FASTMCP.md                # System architecture design
│   ├── FASTMCP_UNSUPPORTED_FEATURES.md        # Features not available in FastMCP
│   ├── FASTMCP_MIGRATION_REPORT.md            # Migration from legacy MCP
│   ├── FASTMCP_CLEANUP_REPORT.md              # Cleanup and English migration
│   ├── FASTMCP_FINAL_REPORT.md                # Final migration summary
│   └── PROJECT_STRUCTURE.md                   # This file
│
├── ⚙️ Configuration
│   ├── config.json.template                   # Configuration template
│   ├── config.yaml                           # YAML configuration
│   ├── pyproject.toml                        # Python project configuration
│   ├── requirements.txt                      # Production dependencies
│   ├── requirements-dev.txt                  # Development dependencies
│   └── setup.cfg                             # Setup configuration
│
├── 🔧 Scripts
│   ├── bulk_store_similar_memories.py        # Bulk memory operations (English)
│   ├── mcp_server_daemon.sh                  # Server control script
│   ├── purge_all_data.py                     # Data cleanup utility
│   ├── reindex_all_embeddings.py             # Embedding reindexing
│   ├── test_comprehensive_fastmcp.py         # Comprehensive FastMCP test
│   ├── test_fastmcp_client.py                # FastMCP client test
│   ├── test_annotations.py                   # Annotation test
│   ├── test_mcp_initialize.py                # Legacy test (deprecated)
│   ├── test_mcp_memory_get.py                # Legacy test (deprecated)
│   ├── test_mcp_memory_get_related.py        # Legacy test (deprecated)
│   └── test_mcp_memory_store.py              # Legacy test (deprecated)
│
├── 💾 Data
│   ├── chroma.sqlite3                        # ChromaDB database
│   └── memory.db                             # SQLite metadata database
│
├── 🧪 Tests
│   ├── __init__.py
│   ├── unit/                                 # Unit tests
│   │   ├── __init__.py
│   │   ├── test_cache.py
│   │   ├── test_memory.py
│   │   └── test_validation.py
│   ├── integration/                          # Integration tests
│   │   └── __init__.py
│   ├── e2e/                                  # End-to-end tests
│   │   └── __init__.py
│   └── fixtures/                             # Test data
│       ├── __init__.py
│       └── sample_data.json
│
└── 🎯 Source Code
    └── src/mcp_assoc_memory/
        ├── __init__.py                       # Package initialization
        ├── __main__.py                       # Entry point (python -m mcp_assoc_memory)
        ├── config.py                         # Configuration management
        ├── server.py                         # 🌟 FastMCP server implementation
        │
        ├── � api/                           # API layer - modular handlers
        │   ├── models/                       # Request/response models
        │   ├── utils/                        # API utilities
        │   └── tools/                        # Tool handlers (modular architecture)
        │       ├── __init__.py               # Handler exports and dependency injection
        │       ├── memory_tools.py           # Core memory operations
        │       ├── scope_tools.py            # Scope management
        │       ├── session_tools.py          # Session lifecycle
        │       ├── export_tools.py           # Import/export operations
        │       ├── resource_tools.py         # Resource handlers
        │       ├── prompt_tools.py           # Prompt handlers
        │       └── other_tools.py            # Miscellaneous tools
        │
        ├── �💎 core/                          # Core memory logic
        │   ├── __init__.py
        │   ├── association.py                # Association algorithms
        │   ├── embedding_service.py          # Embedding generation
        │   ├── memory_manager.py             # High-level memory operations
        │   └── similarity.py                 # Similarity calculations
        │
        ├── 📊 models/                        # Data models
        │   ├── __init__.py
        │   ├── association.py                # Association data models
        │   ├── memory.py                     # Memory data models
        │   └── project.py                    # Project data models
        │
        ├── 💾 storage/                       # Storage layer
        │   ├── __init__.py
        │   ├── base.py                       # Storage interface
        │   ├── graph_store.py                # Graph storage (NetworkX)
        │   ├── metadata_store.py             # Metadata storage (SQLite)
        │   └── vector_store.py               # Vector storage (ChromaDB)
        │
        └── 🛠️ utils/                        # Utility functions
            ├── __init__.py
            ├── cache.py                      # Caching utilities
            ├── logging.py                    # Logging configuration
            ├── metrics.py                    # Performance metrics
            └── validation.py                 # Validation utilities
```

## 🗂️ File Descriptions

### 🎯 Core Application Files

#### `src/mcp_assoc_memory/server.py`
**The main FastMCP server implementation**
- FastMCP 2.0 application with decorators
- Modular architecture with handler delegation
- Tools, resources, and prompts delegated to handler modules
- Clean separation of FastMCP protocol and business logic
- Dependency injection setup for handlers
- English interface throughout

#### `src/mcp_assoc_memory/api/tools/`
**Modular tool handler architecture**
- **memory_tools.py**: Core memory operations (store, search, get, delete, list_all, update, move, discover_associations, diversified_search)
- **scope_tools.py**: Scope management (list, suggest)
- **session_tools.py**: Session lifecycle management (create, list, cleanup)
- **export_tools.py**: Import/export operations (export, import)
- **resource_tools.py**: Resource handlers (memory_stats, scope_memories)
- **prompt_tools.py**: Prompt handlers (analyze_memories, summarize_memory)
- **other_tools.py**: Miscellaneous utility tools
- **__init__.py**: Handler exports and dependency injection setup

#### `src/mcp_assoc_memory/__main__.py`
**Application entry point**
- Starts FastMCP server in STDIO mode
- Handles configuration loading
- Manages server lifecycle

#### `src/mcp_assoc_memory/config.py`
**Configuration management**
- Environment variable handling
- Default values for all settings
- Validation and type checking

### � API Layer (Modular Handlers)

#### `src/mcp_assoc_memory/api/tools/memory_tools.py`
**Core memory operation handlers**
- Memory storage, retrieval, search, deletion
- Memory listing and updating
- Association discovery and diversified search
- Memory movement between scopes
- Business logic delegation to MemoryManager

#### `src/mcp_assoc_memory/api/tools/scope_tools.py`
**Scope management handlers**
- Scope listing and hierarchy browsing
- Scope suggestion based on content analysis
- Scope organization and categorization support

#### `src/mcp_assoc_memory/api/tools/session_tools.py`
**Session lifecycle handlers**
- Session creation with custom or auto-generated IDs
- Session listing with statistics
- Session cleanup based on age criteria
- Temporary workspace management

#### `src/mcp_assoc_memory/api/tools/export_tools.py`
**Import/export operation handlers**
- Memory export to JSON/YAML formats
- Memory import with merge strategies
- Backup and restoration utilities
- Cross-environment memory sync

#### `src/mcp_assoc_memory/api/tools/resource_tools.py`
**Resource handler implementations**
- Memory statistics resource (total counts, scope distribution)
- Scope-specific memory resources
- Dynamic resource generation
- Resource metadata and caching

#### `src/mcp_assoc_memory/api/tools/prompt_tools.py`
**Prompt handler implementations**
- Memory analysis prompt (pattern detection, insights)
- Memory summarization prompt (content summary)
- AI-assisted memory exploration
- Natural language memory interaction

#### `src/mcp_assoc_memory/api/tools/__init__.py`
**Handler coordination and dependency injection**
- Handler exports and registration
- Dependency injection setup for all handlers
- Common handler utilities and patterns
- Handler lifecycle management

### �💎 Core Logic Layer

#### `src/mcp_assoc_memory/core/memory_manager.py`
**High-level memory operations**
- Store, search, retrieve, delete memories
- Domain management and isolation
- Integration with storage layers
- Business logic implementation

#### `src/mcp_assoc_memory/core/embedding_service.py`
**Embedding generation and management**
- OpenAI embeddings integration
- Sentence Transformers support
- Embedding caching and optimization
- Model configuration management

#### `src/mcp_assoc_memory/core/association.py`
**Association and relationship algorithms**
- Memory relationship detection
- Graph traversal algorithms
- Association strength calculation
- Related memory discovery

#### `src/mcp_assoc_memory/core/similarity.py`
**Similarity calculations**
- Cosine similarity implementation
- Distance metrics and thresholds
- Ranking and filtering logic
- Performance optimization

### 📊 Data Models

#### `src/mcp_assoc_memory/models/memory.py`
**Memory data structures**
- Memory entity definitions
- Pydantic models for validation
- Serialization and deserialization
- Type definitions and constraints

#### `src/mcp_assoc_memory/models/association.py`
**Association data structures**
- Relationship entity definitions
- Graph edge representations
- Association metadata models
- Weight and strength calculations

#### `src/mcp_assoc_memory/models/project.py`
**Project data structures**
- Project entity definitions
- Member and permission models
- Project-specific configurations
- Domain isolation support

### 💾 Storage Layer

#### `src/mcp_assoc_memory/storage/vector_store.py`
**Vector storage with ChromaDB**
- Embedding persistence and retrieval
- Similarity search operations
- Collection management
- Performance optimization

#### `src/mcp_assoc_memory/storage/metadata_store.py`
**Metadata storage with SQLite**
- Memory metadata persistence
- Relational data management
- Query optimization
- Transaction handling

#### `src/mcp_assoc_memory/storage/graph_store.py`
**Graph storage with NetworkX**
- In-memory graph representation
- Relationship management
- Graph algorithms and traversal
- Association storage

#### `src/mcp_assoc_memory/storage/base.py`
**Storage interface definitions**
- Abstract base classes
- Common storage patterns
- Interface contracts
- Error handling

### 🛠️ Utility Modules

#### `src/mcp_assoc_memory/utils/validation.py`
**Input validation and sanitization**
- Parameter validation functions
- Data type checking
- Constraint enforcement
- Error message generation

#### `src/mcp_assoc_memory/utils/logging.py`
**Logging configuration and utilities**
- Structured logging setup
- Context-aware logging
- Log level management
- Debug information formatting

#### `src/mcp_assoc_memory/utils/cache.py`
**Caching utilities**
- Memory caching strategies
- Cache invalidation logic
- Performance optimization
- Memory management

#### `src/mcp_assoc_memory/utils/metrics.py`
**Performance metrics and monitoring**
- Timing and performance tracking
- Resource usage monitoring
- Statistics collection
- Health check utilities

## 🔧 Script Files

### 🧪 Test Scripts (FastMCP Compatible)

#### `scripts/test_comprehensive_fastmcp.py`
**Comprehensive FastMCP functionality test**
- Tests all tools, resources, and prompts
- English output and validation
- MCP protocol compliance
- Performance benchmarking

#### `scripts/test_fastmcp_client.py`
**FastMCP client integration test**
- JSON-RPC protocol testing
- Client-server communication
- Error handling validation
- Real-world usage scenarios

#### `scripts/test_annotations.py`
**Annotation system test**
- Tests tool annotations and hints
- UI/UX optimization validation
- Read-only, destructive, idempotent checks
- Annotation inheritance testing

#### `scripts/bulk_store_similar_memories.py`
**Bulk operation test**
- Mass memory storage testing
- Performance under load
- Similarity search validation
- English output formatting

### 🗂️ Utility Scripts

#### `scripts/mcp_server_daemon.sh`
**Server control and management**
- Start, stop, restart, status operations
- Process management
- Log file handling
- PID file management

#### `scripts/purge_all_data.py`
**Data cleanup utility**
- Clear all stored memories
- Reset database state
- Development and testing utility
- Safe data removal

#### `scripts/reindex_all_embeddings.py`
**Embedding reindexing utility**
- Regenerate all embeddings
- Update vector database
- Migration and maintenance tool
- Performance optimization

### 📚 Legacy Scripts (Deprecated)

#### `scripts/test_mcp_*.py`
**Legacy MCP test scripts**
- Deprecated after FastMCP migration
- Kept for reference only
- Use FastMCP test scripts instead
- Will be removed in future versions

## 🚫 Removed Components

### Deleted During FastMCP Migration

#### `src/mcp_assoc_memory/handlers/`
**Legacy MCP tool handlers**
- Complex routing and dispatch logic
- Base handler classes
- Tool registration system
- Replaced by FastMCP decorators

#### `src/mcp_assoc_memory/transport/`
**Custom transport layer**
- HTTP, SSE, STDIO handlers
- Request routing and middleware
- Custom protocol implementations
- Replaced by FastMCP transport

#### `src/mcp_assoc_memory/auth/`
**Authentication system**
- JWT token management
- API key authentication
- Session handling
- Not supported in FastMCP

#### `src/mcp_assoc_memory/visualization/`
**Visualization components**
- HTML/CSS/JS graph visualization
- Interactive memory maps
- Real-time updates
- Not suitable for MCP tools

#### `src/mcp_assoc_memory/fastmcp_server.py`
**Duplicate server file**
- Temporary migration file
- Superseded by updated `server.py`
- Removed to avoid confusion

## 📋 Development Guidelines

### 🎯 Code Organization

1. **Single Responsibility**: Each module has a clear, focused purpose
2. **Layer Separation**: Clear boundaries between FastMCP, core logic, and storage
3. **Interface Contracts**: Well-defined interfaces between components
4. **Error Handling**: Consistent error handling throughout the stack

### 🧪 Testing Strategy

1. **Unit Tests**: Test individual components in isolation
2. **Integration Tests**: Test component interactions
3. **End-to-End Tests**: Test complete workflows
4. **Performance Tests**: Validate performance requirements

### 📚 Documentation Standards

1. **Code Comments**: Clear, concise inline documentation
2. **Type Hints**: Complete type annotations for all functions
3. **Docstrings**: Comprehensive function and class documentation
4. **README Updates**: Keep documentation synchronized with code

### 🔄 Development Workflow

1. **Feature Development**: Use FastMCP best practices
2. **Testing**: Run all test suites before committing
3. **Documentation**: Update relevant documentation
4. **Code Review**: Follow project coding standards

## 🚀 Deployment Structure

### 📦 Production Files
- `src/mcp_assoc_memory/` - Core application code
- `requirements.txt` - Production dependencies
- `config.json.template` - Configuration template
- `scripts/mcp_server_daemon.sh` - Server control script

### 💾 Data Files
- `data/chroma.sqlite3` - Vector database
- `data/memory.db` - Metadata database
- `logs/` - Log files (created at runtime)

### 🛠️ Development Files
- `requirements-dev.txt` - Development dependencies
- `tests/` - Test suite
- `scripts/test_*.py` - Test scripts
- Documentation files

This structure reflects the current FastMCP implementation with clean separation of concerns, comprehensive testing support, and production-ready organization.
