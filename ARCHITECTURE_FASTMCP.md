# FastMCP Associative Memory Server - Architecture

## 1. System Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          LLM Client Layer                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │Claude Desktop│  │VS Code Ext  │  │Custom Client│  │MCP Inspector        │ │
│  │             │  │             │  │             │  │                     │ │
│  │   (STDIO)   │  │   (STDIO)   │  │   (STDIO)   │  │   (WebSocket)       │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────┬─────────────────┬─────────────────┬─────────────────┬─────────────────┘
      │ JSON-RPC        │ JSON-RPC        │ JSON-RPC        │ JSON-RPC
      │ over STDIO      │ over STDIO      │ over STDIO      │ over WebSocket
      │                 │                 │                 │
┌─────▼─────────────────▼─────────────────▼─────────────────▼─────────────────┐
│                       FastMCP Server Layer                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                        FastMCP Application                              │ │
│  │                                                                         │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐│ │
│  │  │   Tools     │  │  Resources  │  │   Prompts   │  │     Context     ││ │
│  │  │             │  │             │  │             │  │                 ││ │
│  │  │@app.tool()  │  │@app.resource│  │@app.prompt()│  │  Logging &      ││ │
│  │  │- 5 tools    │  │()           │  │- 2 prompts  │  │  Error Handling ││ │
│  │  │- Pydantic   │  │- 2 resources│  │- Templates  │  │                 ││ │
│  │  │- Validation │  │- Dynamic    │  │- Context    │  │                 ││ │
│  │  └─────────────┘  │- JSON       │  │- Aware      │  │                 ││ │
│  │                   └─────────────┘  └─────────────┘  └─────────────────┘│ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────┼─────────────────────────────────────────┘
                                  │
┌─────────────────────────────────┼─────────────────────────────────────────┐
│              Core Memory Layer  │                                         │
├─────────────────────────────────┼─────────────────────────────────────────┤
│  ┌─────────────────────────────┬┴───────────────────────────────────────┐ │
│  │     Memory Manager          │     Association Engine                 │ │
│  │ ┌─────────────────────────┐ │ ┌─────────────────────────────────────┐ │ │
│  │ │ - Store memories        │ │ │ - Semantic similarity               │ │ │
│  │ │ - Search by content     │ │ │ - Related memory discovery          │ │ │
│  │ │ - Domain management     │ │ │ - Graph relationships               │ │ │
│  │ │ - CRUD operations       │ │ │ - Embedding generation              │ │ │
│  │ │ - Metadata handling     │ │ │                                     │ │ │
│  │ └─────────────────────────┘ │ └─────────────────────────────────────┘ │ │
│  └─────────────────────────────┴─────────────────────────────────────────┘ │
└─────────────────────────────────┼─────────────────────────────────────────┘
                                  │
┌─────────────────────────────────┼─────────────────────────────────────────┐
│               Storage Layer     │                                         │
├─────────────────────────────────┼─────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │Vector Store │  │Metadata     │  │Graph Store  │  │Embedding Service    │ │
│  │             │  │Store        │  │             │  │                     │ │
│  │- ChromaDB   │  │- SQLite     │  │- NetworkX   │  │- OpenAI API         │ │
│  │- Embeddings │  │- Metadata   │  │- In-memory  │  │- Sentence Trans.    │ │
│  │- Similarity │  │- Relations  │  │- Associations│ │- text-embedding-    │ │
│  │- Persistence│  │- Domains    │  │- Temp only  │  │  ada-002           │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 2. FastMCP Application Architecture

### 2.1 Application Structure

```python
# FastMCP Application Entry Point
from fastmcp import FastMCP

app = FastMCP("Associative Memory")

# Tool definitions with decorators
@app.tool()
async def memory_store(ctx: Context, request: MemoryStoreRequest) -> MemoryResponse:
    """Store a new memory"""
    pass

@app.resource("memory_stats")
async def get_memory_stats(ctx: Context) -> dict:
    """Get memory statistics"""
    pass

@app.prompt("analyze_memories")
async def analyze_memories_prompt(ctx: Context, domain: str = "user") -> str:
    """Analyze memories for a domain"""
    pass
```

### 2.2 Tool Layer Design

#### 2.2.1 Tool Functions
**Responsibility**: Handle specific LLM tool requests

```python
# Tool: memory_store
@app.tool()
async def memory_store(
    ctx: Context, 
    request: MemoryStoreRequest
) -> MemoryResponse:
    """Store a new memory with content, domain, and metadata"""
    
    # Validation handled by Pydantic
    # Business logic implementation
    # Error handling with structured responses
    # Context logging for debugging
```

**Features**:
- Pydantic model validation
- Type safety and IDE support
- Automatic parameter documentation
- Structured error responses
- Context-aware logging

#### 2.2.2 Resource Functions
**Responsibility**: Provide dynamic data access

```python
# Resource: memory_stats
@app.resource("memory_stats")
async def get_memory_stats(ctx: Context) -> dict:
    """Provide memory statistics and domain information"""
    
    return {
        "total_memories": count,
        "domains": domain_stats,
        "storage_info": storage_info
    }
```

**Features**:
- Dynamic content generation
- JSON-structured responses
- Real-time data access
- Domain-specific information

#### 2.2.3 Prompt Functions
**Responsibility**: Generate LLM interaction templates

```python
# Prompt: analyze_memories
@app.prompt("analyze_memories")
async def analyze_memories_prompt(
    ctx: Context, 
    domain: str = "user"
) -> str:
    """Generate analysis prompt for memory domain"""
    
    memories = await get_domain_memories(domain)
    return generate_analysis_template(memories)
```

**Features**:
- Template-based prompt generation
- Context-aware content
- Dynamic parameter support
- LLM-optimized formatting

## 3. Core Memory Layer

### 3.1 Memory Manager
**Responsibility**: High-level memory operations

```python
class MemoryManager:
    def __init__(self, vector_store, metadata_store, graph_store):
        self.vector_store = vector_store
        self.metadata_store = metadata_store
        self.graph_store = graph_store
    
    async def store_memory(self, content: str, domain: str, metadata: dict) -> str:
        """Store memory with embedding and metadata"""
        
    async def search_memories(self, query: str, domain: str, limit: int) -> List[Memory]:
        """Search memories by semantic similarity"""
        
    async def get_memory(self, memory_id: str) -> Memory:
        """Retrieve specific memory by ID"""
        
    async def delete_memory(self, memory_id: str) -> bool:
        """Delete memory and related data"""
```

### 3.2 Association Engine
**Responsibility**: Semantic relationships and similarity

```python
class AssociationEngine:
    def __init__(self, embedding_service, similarity_threshold=0.7):
        self.embedding_service = embedding_service
        self.threshold = similarity_threshold
    
    async def find_similar_memories(self, query: str, domain: str) -> List[Memory]:
        """Find semantically similar memories"""
        
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text content"""
        
    def calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calculate cosine similarity between embeddings"""
```

## 4. Storage Layer

### 4.1 Vector Store (ChromaDB)
**Responsibility**: Embedding storage and similarity search

```python
class VectorStore:
    def __init__(self, persist_directory: str):
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.collection = self.client.get_or_create_collection("memories")
    
    async def store_embedding(self, memory_id: str, embedding: List[float], metadata: dict):
        """Store embedding with metadata"""
        
    async def search_similar(self, query_embedding: List[float], limit: int) -> List[dict]:
        """Search for similar embeddings"""
        
    async def delete_embedding(self, memory_id: str):
        """Delete embedding by memory ID"""
```

### 4.2 Metadata Store (SQLite)
**Responsibility**: Memory metadata and relationships

```python
class MetadataStore:
    def __init__(self, database_path: str):
        self.db_path = database_path
        self.init_database()
    
    async def store_memory_metadata(self, memory_id: str, content: str, domain: str, metadata: dict):
        """Store memory metadata"""
        
    async def get_memory_metadata(self, memory_id: str) -> dict:
        """Retrieve memory metadata"""
        
    async def list_domain_memories(self, domain: str) -> List[dict]:
        """List all memories in domain"""
        
    async def get_memory_stats(self) -> dict:
        """Get memory statistics"""
```

### 4.3 Graph Store (NetworkX)
**Responsibility**: Memory associations (in-memory)

```python
class GraphStore:
    def __init__(self):
        self.graph = nx.Graph()
    
    def add_memory_node(self, memory_id: str, attributes: dict):
        """Add memory as graph node"""
        
    def add_association(self, memory_id1: str, memory_id2: str, weight: float):
        """Add association between memories"""
        
    def get_related_memories(self, memory_id: str, depth: int = 2) -> List[str]:
        """Get related memories through graph traversal"""
```

### 4.4 Embedding Service
**Responsibility**: Text-to-embedding conversion

```python
class EmbeddingService:
    def __init__(self, model_name: str = "text-embedding-ada-002"):
        self.model_name = model_name
        self.client = openai.OpenAI()
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using OpenAI API"""
        
    def get_embedding_dimension(self) -> int:
        """Get embedding dimension for the model"""
```

## 5. Data Flow

### 5.1 Memory Store Flow
```
1. LLM Client → FastMCP Tool (memory_store)
2. FastMCP → Pydantic Validation
3. Tool → Memory Manager
4. Memory Manager → Embedding Service (generate embedding)
5. Memory Manager → Vector Store (store embedding)
6. Memory Manager → Metadata Store (store metadata)
7. Memory Manager → Graph Store (add node)
8. Tool → Response to Client
```

### 5.2 Memory Search Flow
```
1. LLM Client → FastMCP Tool (memory_search)
2. Tool → Memory Manager
3. Memory Manager → Embedding Service (query embedding)
4. Memory Manager → Vector Store (similarity search)
5. Memory Manager → Metadata Store (enrich results)
6. Tool → Response to Client
```

### 5.3 Resource Access Flow
```
1. LLM Client → FastMCP Resource
2. Resource → Memory Manager
3. Memory Manager → Storage Layer (aggregate data)
4. Resource → JSON Response to Client
```

## 6. Configuration and Dependencies

### 6.1 Environment Configuration
```python
# Required environment variables
OPENAI_API_KEY = "sk-..."           # OpenAI API access
MCP_LOG_LEVEL = "INFO"              # Logging level
CHROMA_PERSIST_DIRECTORY = "./data" # ChromaDB persistence
SQLITE_DATABASE_PATH = "./data/memory.db" # SQLite database
```

### 6.2 Dependency Management
```python
# Core dependencies
fastmcp >= 0.2.0        # FastMCP framework
pydantic >= 2.0.0       # Data validation
chromadb >= 0.4.0       # Vector database
openai >= 1.0.0         # Embedding service
networkx >= 3.0         # Graph operations
sqlite3 (built-in)      # Metadata storage
```

## 7. Error Handling and Logging

### 7.1 Error Handling Strategy
```python
# Structured error responses
class MemoryError(Exception):
    def __init__(self, error_type: str, message: str, details: dict = None):
        self.error_type = error_type
        self.message = message
        self.details = details or {}

# Tool error handling
try:
    result = await memory_manager.store_memory(content, domain, metadata)
    return MemoryResponse(success=True, **result)
except MemoryError as e:
    ctx.logger.error(f"Memory operation failed: {e.message}")
    return MemoryResponse(
        success=False,
        error=e.error_type,
        message=e.message,
        details=e.details
    )
```

### 7.2 Context Logging
```python
# Context-aware logging in tools
@app.tool()
async def memory_store(ctx: Context, request: MemoryStoreRequest) -> MemoryResponse:
    ctx.logger.info(f"Storing memory in domain: {request.domain}")
    ctx.logger.debug(f"Memory content length: {len(request.content)}")
    
    try:
        # Implementation
        ctx.logger.info(f"Memory stored successfully: {memory_id}")
        return response
    except Exception as e:
        ctx.logger.error(f"Memory store failed: {str(e)}")
        raise
```

## 8. Performance Considerations

### 8.1 Optimization Strategies
- **Embedding Caching**: Cache frequently used embeddings
- **Connection Pooling**: Reuse database connections
- **Batch Operations**: Process multiple operations efficiently
- **Lazy Loading**: Load data only when needed

### 8.2 Scalability Limits
- **In-memory Graph**: Limited by available RAM
- **SQLite**: Single-writer limitation
- **Embedding API**: Rate limits and costs
- **STDIO Transport**: Single client at a time

## 9. Security and Reliability

### 9.1 Security Measures
- **Input Validation**: Pydantic model validation
- **SQL Injection Prevention**: Parameterized queries
- **API Key Security**: Environment variable storage
- **Error Information**: Sanitized error messages

### 9.2 Reliability Features
- **Data Persistence**: ChromaDB and SQLite persistence
- **Transaction Safety**: Atomic operations where possible
- **Error Recovery**: Graceful error handling
- **Resource Cleanup**: Proper connection management
