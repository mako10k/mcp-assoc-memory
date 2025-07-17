# Changelog

All notable changes to the MCP Associative Memory Server will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.5] - 2025-07-17

### Added
- **Centralized Configuration Management**: New `ConfigurationManager` class for unified config handling
- **Comprehensive Environment Variable Support**: 30+ environment variables for complete deployment flexibility
- **Environment Variable Expansion**: Support for `${VAR}` and `${VAR:-default}` syntax in config files
- **Configuration Documentation**: Complete setup guide in `docs/CONFIGURATION.md`
- **Enhanced VS Code Integration**: Improved `.vscode/mcp.json` with required environment variables

### Fixed
- **Pydantic Validation Errors**: Resolved `log_level` case sensitivity issues
- **Scattered Configuration Logic**: Consolidated from multiple files into centralized system
- **Missing Environment Variables**: Added comprehensive mapping for all configuration options
- **Configuration Precedence**: Clear priority order (CLI > Env > File > Defaults)

### Enhanced
- **Troubleshooting Documentation**: Extended configuration troubleshooting in docs
- **Error Messages**: Improved validation error reporting with actionable guidance
- **Development Experience**: Simplified configuration for local development
- **Deployment Support**: Production-ready configuration examples

### Technical
- Environment variable auto-synchronization (LOG_LEVEL ↔ MCP_LOG_LEVEL)
- Type-safe configuration processing with validation
- Removed duplicate environment variable handling
- Configuration validation with detailed error reporting

### Breaking Changes
- Configuration file precedence may change behavior if relying on previous implicit defaults
- Some environment variable names standardized (see migration guide in docs)

## [0.1.4] - 2025-07-16

### Added
- **Embedding Provider Auto-Detection**: Automatically selects OpenAI or local embeddings based on API key availability
- **User-Friendly Provider Names**: "local" as alias for "sentence_transformer" provider
- **Embedding Compatibility Validation**: Prevents data corruption when switching embedding providers
- **Backward Compatibility**: Existing installations detect provider changes and show appropriate warnings

### Enhanced
- **Configuration Flexibility**: No longer requires OpenAI API key for local-only installations
- **Error Handling**: Clear error messages when attempting incompatible provider changes
- **Provider Switching**: Safe transitions between embedding providers with validation

### Technical
- Contract programming implementation with assert statements for robust error handling
- Provider normalization in embedding service creation
- Compatibility checking integrated into server initialization

## [1.1.0] - 2025-07-15

### Added
- **Response Level Control**: All 10 MCP tools now support intelligent response detail control
  - `minimal`: Essential info only (~50 tokens)
  - `standard`: Balanced detail (default)
  - `full`: Comprehensive information
- **ResponseBuilder**: Centralized utility for consistent response generation
- **Token Optimization**: Aggressive optimization for efficient communication
- **Migration Guide**: Complete documentation for response_level adoption

### Changed
- **API Enhancement**: All tool parameters now support response_level
- **Performance**: Improved response generation efficiency
- **Documentation**: Updated all API references and user guides

### Fixed
- **Type Safety**: Complete mypy compliance across all modules
- **Test Coverage**: Enhanced test suite with response level validation
- **Backward Compatibility**: Zero breaking changes to existing functionality

## [1.0.0] - 2025-07-10

### Added
- **Core MCP Tools**: 10 comprehensive memory management tools
  - `memory_store`: Store memories with auto-association
  - `memory_search`: Semantic search with standard/diversified modes
  - `memory_manage`: Unified CRUD operations (get/update/delete)
  - `memory_sync`: Import/export operations
  - `memory_list_all`: Browse all memories with pagination
  - `memory_discover_associations`: Explore memory connections
  - `memory_move`: Reorganize memory scopes
  - `scope_list`: Browse hierarchical organization
  - `scope_suggest`: AI-powered scope recommendations
  - `session_manage`: Session lifecycle management

### Technical Foundation
- **FastMCP Framework**: High-performance MCP server implementation
- **ChromaDB Integration**: Vector database for semantic similarity
- **SQLite Storage**: Reliable metadata and relationship storage
- **Type Safety**: Complete Pydantic and mypy validation
- **Comprehensive Testing**: 74+ tests with CI/CD pipeline

### Features
- **Associative Memory**: Automatic discovery of semantic connections
- **Hierarchical Organization**: Scope-based memory categorization
- **Session Management**: Temporary workspace isolation
- **Import/Export**: Data synchronization across environments
- **Production Ready**: Docker deployment with monitoring

## [0.9.0] - 2025-07-05

### Added
- Initial MCP server implementation
- Basic memory storage and retrieval
- Proof of concept for associative memory

### Technical
- FastMCP framework integration
- ChromaDB vector storage setup
- Basic tool definitions

---

## Version History Notes

- **v1.1.0**: Response level optimization and production hardening
- **v1.0.0**: Feature-complete associative memory system
- **v0.9.0**: Initial prototype and foundation

For detailed technical changes, see the Git commit history and development documentation.
