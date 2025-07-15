# MCP Associative Memory Server - Specification

## 1. Project Overview

### 1.1 Purpose
Develop an MCP server that enables LLMs to efficiently store information and retrieve related content through associative memory using FastMCP 2.0.

### 1.2 Target Users
- Developers using LLMs
- Researchers building knowledge management systems
- Engineers creating AI assistants

### 1.3 Key Value Propositions
- **Semantic Search**: Search based on semantic similarity, not just keywords
- **Associative Memory**: Automatically retrieve related memories
- **Scope Organization**: Organize memories by hierarchical scopes for better structure
- **FastMCP Integration**: Built with FastMCP 2.0 best practices

## 2. Functional Requirements

### 2.1 Core Tools (FastMCP 2.0)

#### 2.1.1 memory_store
**Purpose**: Store new memory with content, scope, and metadata

**Parameters**:
```python
class MemoryStoreRequest(BaseModel):
    content: str = Field(description="Memory content to store")
    scope: str = Field(default="user/default", description="Memory scope (hierarchical path)")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")
```

**Response**:
```python
class MemoryResponse(BaseModel):
    success: bool
    memory_id: str
    scope: str
    content: str
    embedding_id: Optional[str] = None
    similarity_score: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None
```

#### 2.1.2 memory_search
**Purpose**: Search memories using semantic similarity

**Parameters**:
```python
class MemorySearchRequest(BaseModel):
    query: str = Field(description="Search query")
    scope: Optional[str] = Field(default=None, description="Target scope for search (supports hierarchy)")
    include_child_scopes: bool = Field(default=False, description="Include child scopes in search")
    limit: int = Field(default=10, ge=1, le=100, description="Maximum number of results")
```

**Response**: `List[MemoryResponse]`

#### 2.1.3 memory_get
**Purpose**: Retrieve specific memory by ID

**Parameters**:
```python
class MemoryGetRequest(BaseModel):
    memory_id: str = Field(description="Memory ID to retrieve")
```

**Response**: `MemoryResponse`

#### 2.1.4 memory_delete
**Purpose**: Delete memory by ID

**Parameters**:
```python
class MemoryDeleteRequest(BaseModel):
    memory_id: str = Field(description="Memory ID to delete")
```

**Response**:
```python
class DeleteResponse(BaseModel):
    success: bool
    message: str
    deleted_memory_id: str
```

#### 2.1.5 memory_list_all
**Purpose**: List all stored memories

**Parameters**: None

**Response**: `List[MemoryResponse]`

### 2.2 Resources

#### 2.2.1 memory_stats
**Purpose**: Provide memory statistics and scope information

**Response**:
```python
{
    "total_memories": int,
    "scopes": {
        "scope_path": {
            "count": int,
            "last_updated": str,
            "child_scopes": List[str]
        }
    },
    "storage_info": {
        "vector_store_size": int,
        "metadata_store_size": int
    },
    "active_sessions": List[str]
}
```

#### 2.2.2 scope_memories/{scope}
**Purpose**: Retrieve memories for a specific scope (supports hierarchy)

**Parameters**:
- `include_children`: Include child scope memories (query parameter)

**Response**: List of memories in the specified scope

### 2.3 Prompts

#### 2.3.1 analyze_memories
**Purpose**: Analyze memory patterns for a scope

**Parameters**:
```python
scope: str = Field(default="user/default", description="Target scope for analysis")
include_child_scopes: bool = Field(default=True, description="Include child scopes in analysis")
```

**Response**: Structured analysis prompt for LLM

#### 2.3.2 summarize_memory
**Purpose**: Generate summary for a specific memory

**Parameters**:
```python
memory_id: str = Field(description="Memory ID to summarize")
context_scope: str = Field(default="", description="Contextual scope for summary generation")
```

**Response**: Summary prompt for LLM

### 2.4 Scope Management Tools (Phase 2)

#### 2.4.1 scope_list
**Purpose**: List available scopes and their hierarchy

**Parameters**:
```python
class ScopeListRequest(BaseModel):
    parent_scope: Optional[str] = Field(default=None, description="Parent scope to list children")
    include_stats: bool = Field(default=True, description="Include memory count statistics")
    max_depth: int = Field(default=3, description="Maximum depth to traverse")
```

**Response**:
```python
class ScopeListResponse(BaseModel):
    scopes: List[Dict[str, Any]]  # List of scope info with hierarchy
    total_scopes: int
    structure: Dict[str, Any]  # Hierarchical structure representation
}
```

#### 2.4.2 scope_suggest
**Purpose**: Suggest appropriate scope based on content analysis

**Parameters**:
```python
class ScopeSuggestRequest(BaseModel):
    content: str = Field(description="Content to analyze for scope suggestion")
    current_scope: Optional[str] = Field(default=None, description="Current working scope for context")
    session_context: Optional[Dict[str, Any]] = Field(default=None, description="Session context hints")
```

**Response**:
```python
class ScopeSuggestResponse(BaseModel):
    suggested_scope: str
    confidence: float  # 0.0 to 1.0
    reasoning: str
    alternatives: List[Dict[str, Any]]  # Alternative scopes with reasons
}
```

#### 2.4.3 memory_move
**Purpose**: Move memory to different scope

**Parameters**:
```python
class MemoryMoveRequest(BaseModel):
    memory_id: str = Field(description="Memory ID to move")
    target_scope: str = Field(description="Target scope for the memory")
    update_associations: bool = Field(default=True, description="Update related memory associations")
```

**Response**:
```python
class MemoryMoveResponse(BaseModel):
    success: bool
    old_scope: str
    new_scope: str
    memory_id: str
    associations_updated: int
}
```

#### 2.4.4 session_manage
**Purpose**: Manage session scopes and lifecycle

**Parameters**:
```python
class SessionManageRequest(BaseModel):
    action: str = Field(description="Action: 'create', 'end', 'list', 'cleanup'")
    session_id: Optional[str] = Field(default=None, description="Client-provided session ID")
    session_scope: Optional[str] = Field(default=None, description="Full session scope path (e.g., 'session/chat-123')")
    context_hints: Optional[Dict[str, Any]] = Field(default=None, description="Context metadata from client")
    ttl_hours: Optional[int] = Field(default=24, description="Time-to-live in hours for session cleanup")
```

**Response**:
```python
class SessionManageResponse(BaseModel):
    action: str
    session_scope: Optional[str] = None
    active_sessions: List[Dict[str, Any]]
    cleaned_sessions: Optional[int] = None
    client_managed: bool = True  # Indicates sessions are client-driven
}
```

## 3. Memory Scopes

### 3.1 Scope Hierarchy Design
Scopes use hierarchical paths separated by "/" (slash) to organize memories:

**Examples**:
- `user/default` - Personal user memories (default)
- `user/preferences` - User preference settings
- `user/work` - Work-related personal memories
- `user/projects` - Personal project tracking
- `project/web-app` - Project-specific memories
- `project/web-app/auth` - Project feature-specific memories  
- `session/chat-20250709-001` - Client-provided session memories
- `session/current` - Active session memories
- `team/frontend` - Team-specific memories
- `team/フロントエンド` - Team memories in Japanese
- `org/policies` - Organization-level memories
- `個人/学習ノート` - Personal learning notes in Japanese

### 3.2 Scope Characteristics
- **Hierarchical Structure**: Support unlimited depth with performance constraints
- **Path-like Naming**: Uses "/" as separator (similar to file systems)
- **Flexible Organization**: No fixed meaning for hierarchy levels
- **Isolation**: Memories are isolated by scope unless explicitly searched across scopes
- **Inheritance**: Child scopes can inherit search context from parent scopes
- **Auto-Session Management**: Session scopes are automatically managed

### 3.3 Scope Types by Usage Pattern
- **Persistent Scopes**: `user/*`, `project/*`, `org/*` - Long-term storage
- **Session Scopes**: `session/*` - Temporary, client-managed
- **Collaborative Scopes**: `team/*`, `project/*` - Shared context
- **Personal Scopes**: `user/*` - Individual context

### 3.4 Session Scope Management
- **Client-Driven**: Session IDs are provided by client applications (Chat apps, etc.)
- **MCP Lifecycle Independence**: Session scope lifecycle is independent of MCP connection lifecycle
- **Flexible Naming**: Support both client-provided session IDs and auto-generated patterns
- **UTF-8 Support**: Full Unicode support for international scope names

### 3.5 Scope Naming Rules and Constraints
- **Character Support**: Full UTF-8/Unicode support for international characters
- **Separator**: Forward slash "/" for hierarchy (similar to file paths)
- **Length Limits**: 
  - Total scope path: Max 255 characters
  - Individual scope segment: Max 50 characters
- **Reserved Patterns**: 
  - Cannot start with "." (dot) - reserved for system scopes
  - Cannot contain ".." (double dot) - reserved for relative references
- **Case Sensitivity**: Case-sensitive scope names (recommended: lowercase with hyphens)
- **Examples**:
  - ✅ Valid: `user/default`, `project/ウェブアプリ`, `team/frontend-dev`, `個人/学習`
  - ❌ Invalid: `user/../admin`, `.system/hidden`, `very-long-scope-name-that-exceeds-fifty-characters-limit`

### 3.6 Search Behavior and Performance
- **Child Scope Search**: Default OFF for better performance and semantic precision
- **Explicit Expansion**: Use `include_child_scopes=true` when hierarchical search is needed
- **Search Order**: When child scopes included, searches from specific to general
- **Performance Impact**: Child scope inclusion can significantly increase search time with deep hierarchies

## 4. Technical Specifications

### 4.1 Storage Architecture
- **Vector Store**: ChromaDB for embedding storage and similarity search
- **Metadata Store**: SQLite for memory metadata and relationships
- **Graph Store**: NetworkX for memory associations (in-memory)

### 4.2 Embedding Model
- **Default**: OpenAI Embeddings (text-embedding-ada-002)
- **Alternative**: Sentence Transformers (configurable)
- **Dimensions**: 1536 (OpenAI) or model-specific

### 4.3 Similarity Search
- **Algorithm**: Cosine similarity
- **Default Threshold**: 0.7
- **Maximum Results**: 100 (configurable, default 10)

## 5. FastMCP Implementation Details

### 5.1 Tool Definitions
- Uses `@app.tool()` decorators
- Pydantic models for request/response validation
- Type annotations for all parameters
- Structured error handling

### 5.2 Resource Definitions
- Uses `@app.resource()` decorators
- Dynamic content generation
- Structured data formats

### 5.3 Prompt Definitions
- Uses `@app.prompt()` decorators
- Template-based prompt generation
- Context-aware content

### 5.4 Context Logging
- Structured logging with context information
- Debug information for development
- Error tracking and reporting

## 6. Error Handling

### 6.1 Error Types
- **ValidationError**: Invalid input parameters
- **NotFoundError**: Memory not found
- **StorageError**: Database operation failures
- **EmbeddingError**: Embedding generation failures

### 6.2 Error Response Format
```python
{
    "success": false,
    "error": "ERROR_TYPE",
    "message": "Human-readable error message",
    "details": {...}  # Optional additional details
}
```

## 7. Configuration

### 7.1 Environment Variables
- `OPENAI_API_KEY`: Required for OpenAI embeddings
- `MCP_LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `CHROMA_PERSIST_DIRECTORY`: ChromaDB persistence directory
- `SQLITE_DATABASE_PATH`: SQLite database file path

### 7.2 Default Values
- Memory scope: "user/default"
- Search limit: 10
- Similarity threshold: 0.7
- Embedding model: text-embedding-ada-002
- Max scope depth: 10 levels
- Session timeout: 1 hour

## 8. Limitations and Constraints

### 8.1 FastMCP Limitations
- No built-in authentication system
- No custom transport layer support
- Request-response pattern only (no streaming)
- Single-process architecture

### 8.2 Current Implementation Constraints
- In-memory graph storage (not persistent)
- No advanced search filters (tags, time range)
- No batch operations
- No real-time updates
- No user management or sessions

## 9. Future Enhancements

### 9.1 Planned Features
- Persistent graph storage
- Advanced search filters
- Batch memory operations
- Performance optimizations

### 9.2 External Integrations
- Visualization tools for memory graphs
- Backup and recovery systems
- Monitoring and analytics
- Multi-model embedding support

## 10. Testing and Validation

### 10.1 Test Coverage
- Unit tests for core functionality
- Integration tests for MCP protocol
- End-to-end tests for client interaction
- Performance tests for large datasets

### 10.2 Validation Criteria
- Response time < 1 second for basic operations
- Memory search accuracy > 90%
- System stability under load
- Data integrity and consistency
