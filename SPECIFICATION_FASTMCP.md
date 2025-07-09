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
- **Domain Organization**: Organize memories by domains for better structure
- **FastMCP Integration**: Built with FastMCP 2.0 best practices

## 2. Functional Requirements

### 2.1 Core Tools (FastMCP 2.0)

#### 2.1.1 memory_store
**Purpose**: Store new memory with content, domain, and metadata

**Parameters**:
```python
class MemoryStoreRequest(BaseModel):
    content: str = Field(description="Memory content to store")
    domain: str = Field(default="user", description="Memory domain")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")
```

**Response**:
```python
class MemoryResponse(BaseModel):
    success: bool
    memory_id: str
    domain: str
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
    domain: Optional[str] = Field(default=None, description="Target domain for search")
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
**Purpose**: Provide memory statistics and domain information

**Response**:
```python
{
    "total_memories": int,
    "domains": {
        "domain_name": {
            "count": int,
            "last_updated": str
        }
    },
    "storage_info": {
        "vector_store_size": int,
        "metadata_store_size": int
    }
}
```

#### 2.2.2 domain_memories/{domain}
**Purpose**: Retrieve memories for a specific domain

**Response**: List of memories in the specified domain

### 2.3 Prompts

#### 2.3.1 analyze_memories
**Purpose**: Analyze memory patterns for a domain

**Parameters**:
```python
domain: str = Field(default="user", description="Target domain for analysis")
```

**Response**: Structured analysis prompt for LLM

#### 2.3.2 summarize_memory
**Purpose**: Generate summary for a specific memory

**Parameters**:
```python
memory_id: str = Field(description="Memory ID to summarize")
```

**Response**: Summary prompt for LLM

## 3. Memory Domains

### 3.1 Supported Domains
- **user**: Personal user memories (default)
- **project**: Project-specific memories
- **global**: Shared global memories
- **session**: Temporary session memories

### 3.2 Domain Characteristics
- **Isolation**: Memories are isolated by domain
- **Search Scope**: Search can target specific domains
- **Persistence**: All domains except session are persistent

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
- Memory domain: "user"
- Search limit: 10
- Similarity threshold: 0.7
- Embedding model: text-embedding-ada-002

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
