# MCP Associative Memory Server - API Reference

## 📖 Complete Tool Documentation

This reference covers all available MCP tools for the Associative Memory Server. Each tool is designed for specific use cases in memory management and knowledge discovery.

## 🧠 Core Memory Operations

### memory_store
**Store new memories with automatic association discovery**

```json
{
  "tool": "memory_store",
  "parameters": {
    "request": {
      "content": "Your memory content here",
      "scope": "work/projects/example",
      "category": "programming", 
      "tags": ["python", "fastapi"],
      "metadata": {"project": "mcp-server"},
      "allow_duplicates": false,
      "auto_associate": true,
      "similarity_threshold": 0.95
    }
  }
}
```

**Parameters:**
- `content` (required): The memory content to store
- `scope` (optional): Hierarchical organization path (default: "user/default")
- `category` (optional): Memory category for classification
- `tags` (optional): Array of tags for labeling
- `metadata` (optional): Additional key-value data
- `allow_duplicates` (optional): Allow storing similar content (default: false)
- `auto_associate` (optional): Enable automatic association discovery (default: true)
- `similarity_threshold` (optional): Duplicate detection threshold (default: 0.95)

**Response:**
```json
{
  "memory_id": "uuid-string",
  "content": "stored content",
  "scope": "work/projects/example",
  "created_at": "2025-07-10T05:30:00.000Z",
  "is_duplicate": false,
  "associations": ["related-memory-id-1", "related-memory-id-2"]
}
```

**Use Cases:**
- Store insights and learnings
- Capture meeting notes
- Save problem solutions
- Document decisions

---

### memory_search
**Semantic search across memories using natural language**

```json
{
  "tool": "memory_search", 
  "parameters": {
    "request": {
      "query": "Python async programming patterns",
      "scope": "learning/programming",
      "limit": 10,
      "similarity_threshold": 0.1,
      "include_associations": true,
      "include_child_scopes": false
    }
  }
}
```

**Parameters:**
- `query` (required): Natural language search query
- `scope` (optional): Limit search to specific scope
- `limit` (optional): Maximum results to return (default: 10, max: 100)
- `similarity_threshold` (optional): Minimum similarity score (default: 0.1)
- `include_associations` (optional): Include related memories (default: true)
- `include_child_scopes` (optional): Search child scopes (default: false)

**Response:**
```json
{
  "memories": [
    {
      "memory_id": "uuid",
      "content": "Memory content",
      "scope": "learning/programming/python",
      "similarity_score": 0.87,
      "associations": [...]
    }
  ],
  "total_found": 15,
  "search_scope": "learning/programming"
}
```

**Search Tips:**
- Use conceptual terms rather than exact phrases
- Start with similarity_threshold=0.1 for comprehensive results
- LLM interprets similarity scores to judge relevance
- Higher scores indicate stronger relevance

---

### memory_get
**Retrieve detailed information about a specific memory**

```json
{
  "tool": "memory_get",
  "parameters": {
    "memory_id": "uuid-string",
    "include_associations": true
  }
}
```

**Parameters:**
- `memory_id` (required): The unique identifier of the memory
- `include_associations` (optional): Include related memories (default: true)

**Response:**
```json
{
  "memory_id": "uuid",
  "content": "Full memory content",
  "scope": "work/projects/example",
  "metadata": {...},
  "tags": [...],
  "category": "programming",
  "created_at": "2025-07-10T05:30:00.000Z",
  "associations": [
    {
      "memory_id": "related-uuid",
      "content": "Related memory content",
      "similarity_score": 0.76
    }
  ]
}
```

---

### memory_update
**Modify existing memory content and metadata**

```json
{
  "tool": "memory_update",
  "parameters": {
    "request": {
      "memory_id": "uuid-string",
      "content": "Updated content",
      "scope": "new/scope/path",
      "tags": ["updated", "tags"],
      "category": "new-category",
      "metadata": {"updated": "2025-07-10"},
      "preserve_associations": true
    }
  }
}
```

**Parameters:**
- `memory_id` (required): ID of memory to update
- `content` (optional): New content for the memory
- `scope` (optional): New scope for organization
- `tags` (optional): New tags array
- `category` (optional): New category
- `metadata` (optional): New metadata object
- `preserve_associations` (optional): Keep existing associations (default: true)

**Note:** Only specify fields you want to change. Unspecified fields remain unchanged.

---

### memory_delete
**Permanently remove unwanted memories**

```json
{
  "tool": "memory_delete",
  "parameters": {
    "memory_id": "uuid-string"
  }
}
```

**Parameters:**
- `memory_id` (required): ID of memory to delete

**⚠️ Warning:** Deletion is permanent and cannot be undone.

---

## 🔍 Discovery and Analysis

### memory_discover_associations
**Find memories semantically related to a specific memory**

```json
{
  "tool": "memory_discover_associations",
  "parameters": {
    "memory_id": "uuid-string",
    "limit": 15,
    "similarity_threshold": 0.1
  }
}
```

**Parameters:**
- `memory_id` (required): Memory to find associations for
- `limit` (optional): Maximum associations to discover (default: 10, max: 50)  
- `similarity_threshold` (optional): Minimum similarity for inclusion (default: 0.1)

**Response:**
```json
{
  "source_memory": {
    "memory_id": "uuid",
    "content": "Source memory content"
  },
  "associations": [
    {
      "memory_id": "related-uuid",
      "content": "Related memory content", 
      "similarity_score": 0.68,
      "association_type": "semantic"
    }
  ],
  "discovery_stats": {
    "total_candidates": 50,
    "filtered_results": 15,
    "avg_similarity": 0.45
  }
}
```

**Use Cases:**
- Creative problem solving
- Knowledge synthesis
- Learning reinforcement
- Unexpected connection discovery

---

## 🗂️ Organization and Management

### scope_list
**Browse hierarchical memory organization structure**

```json
{
  "tool": "scope_list",
  "parameters": {
    "request": {
      "parent_scope": "work",
      "include_memory_counts": true
    }
  }
}
```

**Parameters:**
- `parent_scope` (optional): Filter to specific scope hierarchy
- `include_memory_counts` (optional): Include memory statistics (default: true)

**Response:**
```json
{
  "scopes": [
    {
      "scope": "work/projects",
      "memory_count": 25,
      "child_scopes": ["work/projects/mcp-server", "work/projects/web-app"],
      "depth": 2
    }
  ],
  "total_scopes": 12,
  "hierarchy_depth": 4
}
```

---

### scope_suggest
**Get AI-powered scope recommendations for content**

```json
{
  "tool": "scope_suggest",
  "parameters": {
    "request": {
      "content": "Meeting notes from standup discussion about API performance",
      "current_scope": "work/meetings"
    }
  }
}
```

**Parameters:**
- `content` (required): Content to analyze for categorization
- `current_scope` (optional): Current context for better suggestions

**Response:**
```json
{
  "suggested_scope": "work/meetings/standup",
  "confidence": 0.89,
  "alternatives": [
    {
      "scope": "work/performance",
      "confidence": 0.72,
      "reasoning": "Content mentions API performance optimization"
    }
  ],
  "analysis": {
    "detected_keywords": ["meeting", "standup", "api", "performance"],
    "suggested_category": "meeting",
    "content_type": "notes"
  }
}
```

---

### memory_move
**Reorganize memories into better organizational structure**

```json
{
  "tool": "memory_move",
  "parameters": {
    "request": {
      "memory_ids": ["uuid1", "uuid2", "uuid3"],
      "target_scope": "work/projects/mcp-improvements"
    }
  }
}
```

**Parameters:**
- `memory_ids` (required): Array of memory IDs to move
- `target_scope` (required): Destination scope path

**Response:**
```json
{
  "moved_count": 3,
  "failed_moves": [],
  "target_scope": "work/projects/mcp-improvements",
  "moved_memories": [
    {
      "memory_id": "uuid1",
      "old_scope": "work/general",
      "new_scope": "work/projects/mcp-improvements"
    }
  ]
}
```

---

### memory_list_all
**Browse complete memory collection with pagination**

```json
{
  "tool": "memory_list_all",
  "parameters": {
    "page": 1,
    "per_page": 25
  }
}
```

**Parameters:**
- `page` (optional): Page number for pagination (default: 1)
- `per_page` (optional): Items per page (default: 10, max: 100)

**Response:**
```json
{
  "memories": [...],
  "pagination": {
    "page": 1,
    "per_page": 25,
    "total_items": 150,
    "total_pages": 6,
    "has_next": true,
    "has_prev": false
  }
}
```

---

## 📦 Import/Export Operations

### memory_export
**Export memories for backup or cross-environment sync**

```json
{
  "tool": "memory_export",
  "parameters": {
    "request": {
      "scope": "work",
      "file_path": "backup-2025-07-10.json",
      "export_format": "json",
      "compression": false,
      "include_associations": true
    }
  }
}
```

**Parameters:**
- `scope` (optional): Scope to export (null = all memories)
- `file_path` (optional): Server-side file path (null = return data directly)
- `export_format` (optional): Export format "json" or "yaml" (default: "json")
- `compression` (optional): Enable gzip compression (default: false)
- `include_associations` (optional): Include relationship data (default: true)

**Response (File Export):**
```json
{
  "success": true,
  "exported_count": 25,
  "export_scope": "work",
  "file_path": "data/exports/backup-2025-07-10.json",
  "export_size": 15420,
  "compression_used": false
}
```

**Response (Direct Data):**
```json
{
  "success": true,
  "exported_count": 25,
  "export_data": "{ ... json data ... }",
  "export_size": 15420
}
```

---

### memory_import
**Import memories from backup files or direct data**

```json
{
  "tool": "memory_import",
  "parameters": {
    "request": {
      "file_path": "backup-2025-07-10.json",
      "merge_strategy": "skip_duplicates",
      "target_scope_prefix": "imported/",
      "validate_data": true
    }
  }
}
```

**Parameters:**
- `file_path` (optional): Server-side file to import (null = use import_data)
- `import_data` (optional): Direct JSON data string
- `merge_strategy` (optional): How to handle duplicates:
  - `"skip_duplicates"`: Keep existing, skip imports (safe default)
  - `"overwrite"`: Replace existing with imported data
  - `"create_versions"`: Create new versions of duplicates
  - `"merge_metadata"`: Combine metadata while keeping content
- `target_scope_prefix` (optional): Prefix for imported memory scopes
- `validate_data` (optional): Validate structure before import (default: true)

**Response:**
```json
{
  "success": true,
  "imported_count": 20,
  "skipped_count": 5,
  "overwritten_count": 0,
  "import_source": "file:backup-2025-07-10.json",
  "merge_strategy_used": "skip_duplicates",
  "validation_errors": [],
  "imported_scopes": ["imported/work/projects", "imported/learning"]
}
```

---

## 🔄 Session Management

### session_manage
**Manage temporary memory sessions for project isolation**

```json
{
  "tool": "session_manage",
  "parameters": {
    "request": {
      "action": "create",
      "session_id": "mcp-development-session",
      "max_age_days": 7
    }
  }
}
```

**Parameters:**
- `action` (required): Session operation:
  - `"create"`: Create new session scope
  - `"list"`: List all active sessions
  - `"cleanup"`: Remove old sessions
- `session_id` (optional): Custom session identifier (auto-generated if not provided)
- `max_age_days` (optional): Age threshold for cleanup operations (default: 7)

**Response (Create):**
```json
{
  "action": "create",
  "session_id": "mcp-development-session",
  "session_scope": "session/mcp-development-session",
  "created_at": "2025-07-10T05:30:00.000Z"
}
```

**Response (List):**
```json
{
  "action": "list", 
  "sessions": [
    {
      "session_id": "mcp-development-session",
      "scope": "session/mcp-development-session",
      "memory_count": 15,
      "created_at": "2025-07-10T05:30:00.000Z",
      "age_days": 2
    }
  ],
  "total_sessions": 3
}
```

**Response (Cleanup):**
```json
{
  "action": "cleanup",
  "removed_sessions": 2,
  "freed_memories": 28,
  "max_age_days": 7
}
```

---

## 🔧 Error Handling

### Common Error Responses

**Validation Error:**
```json
{
  "success": false,
  "error": "VALIDATION_ERROR",
  "message": "Required field 'content' is missing",
  "data": {}
}
```

**Not Found Error:**
```json
{
  "success": false,
  "error": "MEMORY_NOT_FOUND", 
  "message": "Memory with ID 'invalid-uuid' not found",
  "data": {"memory_id": "invalid-uuid"}
}
```

**Storage Error:**
```json
{
  "success": false,
  "error": "STORAGE_ERROR",
  "message": "Failed to save memory to storage",
  "data": {"retry_suggested": true}
}
```

### Error Categories
- **VALIDATION_ERROR**: Invalid parameters or data format
- **MEMORY_NOT_FOUND**: Requested memory doesn't exist
- **STORAGE_ERROR**: Database or storage system issues
- **SEARCH_ERROR**: Search engine or embedding service issues
- **EXPORT_ERROR**: File system or export operation issues
- **IMPORT_ERROR**: Import validation or processing failures

---

## 💡 Usage Examples

### Workflow Integration
```javascript
// Store a learning
await memory_store({
  content: "Learned that React useCallback should only be used when referential equality matters for child component optimization",
  scope: "learning/react/performance",
  tags: ["react", "hooks", "performance", "useCallback"],
  category: "programming"
});

// Search before solving a problem  
const results = await memory_search({
  query: "React performance optimization hooks",
  scope: "learning/react"
});

// Discover related concepts
const associations = await memory_discover_associations({
  memory_id: "uuid-of-performance-memory",
  limit: 10
});
```

### Project Organization
```javascript
// Set up project scope
await memory_store({
  content: "Starting new e-commerce platform project with React, Node.js, and PostgreSQL",
  scope: "work/projects/ecommerce-platform",
  category: "project-start"
});

// Store architecture decisions
await memory_store({
  content: "Chose Redux Toolkit over Context API for state management due to complex state interactions and time-travel debugging needs",
  scope: "work/projects/ecommerce-platform/architecture", 
  tags: ["redux", "state-management", "architecture"],
  metadata: {"decision_date": "2025-07-10", "stakeholders": ["team-lead", "senior-dev"]}
});
```

### Knowledge Export
```javascript
// Export project knowledge for documentation
const projectExport = await memory_export({
  scope: "work/projects/ecommerce-platform",
  file_path: "ecommerce-project-knowledge.json",
  include_associations: true
});

// Cross-environment sync
const allWorkMemories = await memory_export({
  scope: "work", 
  compression: true
  // Returns data directly for transfer
});
```

---

## 🎯 Performance Considerations

### Optimization Tips
- **Batch operations** when storing multiple related memories
- **Use specific scopes** for faster searching
- **Regular exports** help maintain performance
- **Session cleanup** prevents accumulation of temporary data
- **Reasonable limits** in search and discovery operations

### Scale Guidelines
- **Memory count**: Tested with 1000+ memories per scope
- **Search performance**: Sub-second response for most queries
- **Association discovery**: Efficient up to 10K+ total memories
- **Export/Import**: Handles MB-sized data transfers

---

**For more information, see:**
- [Quick Start Guide](../user-guide/QUICK_START.md)
- [Best Practices](../user-guide/BEST_PRACTICES.md)
- [Troubleshooting Guide](../troubleshooting/README.md)
