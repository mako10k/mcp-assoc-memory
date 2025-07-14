# MCP Associative Memory Server - Complete API Reference (2025)

## 📖 Overview

The MCP Associative Memory Server provides a comprehensive suite of **10 MCP tools** for intelligent memory management and knowledge discovery. This document reflects the current production-ready API as of July 2025.

## 🧪 Testing Status
- **74/74 tests passing** (100% success rate)
- **Complete CI/CD pipeline** with security and quality gates
- **Production-ready** with comprehensive test coverage

## 🛠️ Available Tools

### 🧠 Core Memory Operations

#### 1. `memory_store` 
**💾 Store New Memory**

**Purpose**: Store new memories with optional automatic connection discovery and duplicate detection.

**Parameters**:
```json
{
  "request": {
    "content": "Your memory content here",
    "scope": "work/projects/example",
    "category": "programming",
    "tags": ["python", "fastapi"],
    "metadata": {"project": "mcp-server"},
    "allow_duplicates": false,
    "auto_associate": true,
    "duplicate_threshold": 0.85,
    "minimal_response": false
  }
}
```

**Auto-Association Control**:
- `auto_associate`: Boolean (default: true)
  - `true`: Automatically discover semantic connections with existing memories
  - `false`: Skip association discovery for faster storage (bulk operations)

**Duplicate Detection**:
- `duplicate_threshold`: Float (0.0-1.0) or null
  - `null` (default): No duplicate checking - allow any content
  - `0.85-0.95`: Standard duplicate prevention (recommended)
  - `0.95-1.0`: Strict - prevent only near-identical content
- `allow_duplicates`: Boolean (default: false)
  - `true`: Store even if duplicate detected (when threshold specified)
  - `false`: Reject storage if duplicate found

**Use Cases**:
- **Standard storage**: `auto_associate=true, duplicate_threshold=null` (default)
- **Bulk operations**: `auto_associate=false` (faster)
- **Duplicate prevention**: `duplicate_threshold=0.85`
- **Force storage**: `duplicate_threshold=0.85, allow_duplicates=true`
```

**Response**:
```json
{
  "success": true,
  "message": "Memory stored successfully: uuid-string",
  "data": {
    "memory_id": "uuid-string",
    "created_at": "2025-07-12T10:30:00Z",
    "scope": "work/projects/example",
    "duplicate_check_performed": true
  },
  "memory": {
    "id": "uuid-string",
    "content": "Your memory content here",
    "scope": "work/projects/example",
    "metadata": {"project": "mcp-server"},
    "tags": ["python", "fastapi"],
    "category": "programming",
    "created_at": "2025-07-12T10:30:00Z",
    "updated_at": "2025-07-12T10:30:00Z"
  },
  "associations_created": [],
  "duplicate_found": false
}
```

**Duplicate Detection Response**:
```json
{
  "success": false,
  "message": "Duplicate content detected (similarity: 0.947 >= 0.85)",
  "data": {"duplicate_threshold": 0.85},
  "memory": null,
  "associations_created": [],
  "duplicate_found": true,
  "duplicate_candidate": {
    "memory_id": "existing-uuid",
    "similarity_score": 0.947,
    "content_preview": "Similar existing content...",
    "scope": "work/projects/example",
    "created_at": "2025-07-11T15:20:00Z"
  }
}
```
```

---

#### 2. `memory_search`
**🔍 Unified Memory Search (Standard & Diversified)**

**Purpose**: Search memories using semantic similarity with optional diversity filtering.

**Parameters**:
```json
{
  "request": {
    "query": "Python async programming",
    "mode": "standard",
    "scope": "learning/programming",
    "include_child_scopes": false,
    "limit": 10,
    "similarity_threshold": 0.1,
    "include_associations": true,
    "diversity_threshold": 0.8,
    "expansion_factor": 2.5
  }
}
```

**Response**:
```json
{
  "results": [
    {
      "memory_id": "uuid-string",
      "content": "Async programming in Python...",
      "scope": "learning/programming/python",
      "similarity_score": 0.95,
      "tags": ["python", "async"],
      "category": "programming",
      "created_at": "2025-07-12T10:30:00Z",
      "metadata": {"difficulty": "intermediate"},
      "associations": [...]
    }
  ],
  "query": "Python async programming",
  "scope": "learning/programming",
  "total_found": 5,
  "similarity_threshold": 0.1,
  "search_metadata": {
    "scope_coverage": "exact",
    "fallback_used": false
  }
}
```

---

#### 3. `memory_manage`
**🔧 Unified Memory CRUD Operations**

**Purpose**: Get, update, or delete memories through a single unified interface.

**Parameters**:
```json
{
  "request": {
    "operation": "get",
    "memory_id": "uuid-string",
    "include_associations": true,
    "content": "Updated content",
    "category": "new-category",
    "tags": ["new", "tags"],
    "metadata": {"updated": true},
    "scope": "new/scope",
    "preserve_associations": true
  }
}
```

**Operations**:
- `"get"`: Retrieve memory by ID
- `"update"`: Modify existing memory content/metadata
- `"delete"`: Remove memory permanently

---

#### 4. `memory_sync`
**🔄 Unified Import/Export Operations**

**Purpose**: Handle data synchronization (import/export) through a single interface.

**Parameters**:
```json
{
  "request": {
    "operation": "export",
    "scope": "work",
    "file_path": "backup/memories-2025-07-12.json",
    "include_associations": true,
    "export_format": "json",
    "compression": false,
    "import_data": null,
    "merge_strategy": "skip_duplicates",
    "validate_data": true
  }
}
```

**Operations**:
- `"export"`: Backup memories to file or get data directly
- `"import"`: Restore memories from file or direct data

---

#### 5. `memory_list_all`
**📋 Browse All Memories with Pagination**

**Purpose**: Retrieve all stored memories with pagination support for system administration.

**Parameters**:
```json
{
  "page": 1,
  "per_page": 10
}
```

---

#### 6. `memory_discover_associations`
**🧠 Explore Memory Connections**

**Purpose**: Discover semantic relationships between memories for knowledge exploration.

**Parameters**:
```json
{
  "memory_id": "uuid-string",
  "similarity_threshold": 0.7,
  "limit": 10
}
```

---

#### 7. `memory_move`
**📦 Reorganize Memory Scopes**

**Purpose**: Move memories between scopes for better organization.

**Parameters**:
```json
{
  "request": {
    "memory_ids": ["uuid-1", "uuid-2"],
    "target_scope": "work/projects/new-project"
  }
}
```

---

### 🗂️ Scope Management

#### 8. `scope_list`
**🗂️ Browse Scope Hierarchy**

**Purpose**: Display hierarchical organization of memory scopes with counts.

**Parameters**:
```json
{
  "request": {
    "parent_scope": "work",
    "include_memory_counts": true
  }
}
```

---

#### 9. `scope_suggest`
**🎯 Smart Scope Recommendations**

**Purpose**: AI-powered scope suggestions for optimal content organization.

**Parameters**:
```json
{
  "request": {
    "content": "Python FastAPI implementation details",
    "current_scope": "work/projects"
  }
}
```

---

### ⏱️ Session Management

#### 10. `session_manage`
**⏱️ Session Lifecycle Management**

**Purpose**: Create, list, and clean up temporary memory sessions.

**Parameters**:
```json
{
  "request": {
    "action": "create",
    "session_id": "project-alpha-session",
    "max_age_days": 7
  }
}
```

**Actions**:
- `"create"`: Create new session scope
- `"list"`: List all active sessions
- `"cleanup"`: Remove old sessions based on age

---

## 🚀 Usage Examples

### Quick Start
```bash
# Store a memory
memory_store: {"request": {"content": "FastAPI is great for APIs", "scope": "learning/web"}}

# Search for it
memory_search: {"request": {"query": "FastAPI APIs", "limit": 5}}

# Discover connections
memory_discover_associations: {"memory_id": "returned-id", "limit": 5}
```

### Workflow Integration
```bash
# 1. Create working session
session_manage: {"request": {"action": "create", "session_id": "debug-session"}}

# 2. Store investigation notes
memory_store: {"request": {"content": "Bug in API authentication", "scope": "session/debug-session"}}

# 3. Search for related issues
memory_search: {"request": {"query": "authentication bug", "scope": "work"}}

# 4. Export findings
memory_sync: {"request": {"operation": "export", "scope": "session/debug-session"}}

# 5. Clean up when done
session_manage: {"request": {"action": "cleanup", "max_age_days": 1}}
```

## 🔧 Integration Notes

### VS Code Integration
All tools are available through GitHub Copilot in VS Code. Use natural language instructions like:
- "Store this code snippet in my learning scope"
- "Find memories about error handling"
- "Export my work memories to a backup file"

### Error Handling
All tools follow consistent error response patterns:
```json
{
  "error": "Error description",
  "results": [],
  "data": {}
}
```

### Performance
- **Search**: Optimized with ChromaDB vector similarity
- **Storage**: Automatic duplicate detection
- **Memory**: Efficient metadata indexing
- **Associations**: Lazy loading for performance

## 📊 System Status

- **Current Version**: 2025.07 (Production)
- **API Stability**: Stable (breaking changes will be versioned)
- **Test Coverage**: 74 tests, 100% pass rate
- **Performance**: Sub-second response times
- **Security**: Bandit scanned, dependency verified

---

*This reference reflects the production API as tested in July 2025. For the latest updates, see the development documentation.*
