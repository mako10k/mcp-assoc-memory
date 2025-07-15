---
name: Response Level Implementation Issue
about: Fix response level functionality in unified response processing
title: '[BUG] Response level configuration not properly applied in API responses'
labels: bug, enhancement, api
assignees: ''
---

## 🐛 Problem Description

The unified response processing system correctly reads the configuration (`level=full`) but the actual response format is not being applied. The `to_response_dict` method in response classes is not being called properly.

## 🔍 Current Status

### ✅ Working Components
- **Config Singleton**: Successfully implemented with thread-safe pattern
- **Configuration Loading**: `config.json` is correctly loaded with `default_response_level: "full"`
- **Response Processing**: Logs show `level=full, size=114` indicating correct level detection
- **Similar Memory Search**: Fixed `similarity_threshold` parameter error

### ❌ Broken Components
- **Response Format**: Still returning basic format instead of full response
- **to_response_dict Call**: Debug messages show method is not being invoked
- **Duplicate Candidates**: Not displayed despite full level configuration

## 🎯 Expected Behavior

### Memory Store Response Levels

#### Minimal
```json
{
  "success": true,
  "memory_id": "...",
  "created_at": "..."
}
```

#### Standard
```json
{
  "success": true,
  "memory_id": "...",
  "created_at": "...",
  "duplicate_candidates": ["id1", "id2", "id3"]
}
```

#### Full
```json
{
  "success": true,
  "memory_id": "...",
  "created_at": "...",
  "duplicate_candidates": [
    {
      "memory_id": "...",
      "similarity_score": 0.97,
      "content_preview": "First 100 characters...",
      "metadata": {...}
    }
  ],
  "associations_created": [...]
}
```

### Memory Search Response Levels

- **Standard/Full**: Content truncated to 100 characters
- **Minimal**: Basic query and count only

## 🔧 Investigation Needed

1. **Response Processing Flow**: Verify `process_tool_response()` calls `response.to_response_dict(level)`
2. **Method Invocation**: Debug why `MemoryStoreResponse.to_response_dict()` is not called
3. **Level Determination**: Confirm response level is correctly passed through the processing chain

## 🚨 Root Cause Analysis

The issue appears to be in the response processing pipeline between:
- `memory_tools.py` → `process_tool_response()` → `MemoryStoreResponse.to_response_dict()`

## 📝 Implementation Requirements

- [ ] Fix response processing to call `to_response_dict(level)`
- [ ] Implement content truncation for search responses (100 chars)
- [ ] Add duplicate candidate detection with 95%+ similarity
- [ ] Remove `_metadata` from responses per user request
- [ ] Test all response levels (minimal, standard, full)

## 🧪 Test Cases

```bash
# Test memory store with full response
mcp_assocmemory_memory_store '{"content": "test", "minimal_response": false}'

# Test search with content truncation
mcp_assocmemory_memory_search '{"query": "test", "limit": 3}'
```

## 📊 Priority: High

This blocks the completion of the response optimization feature and affects API usability.

## 🏷️ Labels

- `bug`: Response processing not working as configured
- `enhancement`: New response level functionality
- `api`: Core API functionality affected
- `config`: Configuration-related issue
