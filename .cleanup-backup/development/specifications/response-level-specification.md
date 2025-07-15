# Response Level Specification - MCP Associative Memory

## 📋 Overview

This specification defines the unified response level system for all MCP tools in the Associative Memory Server. The system provides three levels of response detail to optimize LLM context usage while maintaining operational efficiency.

## 🎯 Design Principles

### Core Principles
1. **Token Efficiency**: Minimize response tokens while maintaining functionality
2. **Operational Continuity**: Include necessary information for workflow progression
3. **No Redundancy**: Exclude information that can be inferred from request parameters
4. **Consistent Interface**: Unified parameter across all tools

### Response Levels

| Level | Purpose | Token Strategy | Use Cases |
|-------|---------|----------------|-----------|
| `minimal` | Success confirmation | Absolute minimum | Bulk operations, automation |
| `standard` | Balanced workflow | Next-operation ready | Interactive use, normal operations |
| `full` | Complete information | Maximum detail | Debugging, analysis, exploration |

## 🔧 Technical Specification

### Common Parameter

```python
response_level: ResponseLevel = Field(
    default=ResponseLevel.STANDARD,
    description=(
        "Response detail level:\n"
        "• minimal: Success status + essential IDs only (minimal tokens)\n"
        "• standard: Balanced info for workflow continuity + content previews\n" 
        "• full: Complete data + metadata + associations (maximum detail)"
    )
)
```

### Response Level Enum

```python
class ResponseLevel(Enum):
    MINIMAL = "minimal"
    STANDARD = "standard" 
    FULL = "full"
```

## 📊 Tool-Specific Response Specifications

### memory_store

| Level | Response Content |
|-------|------------------|
| **minimal** | `{success, memory_id}` |
| **standard** | `{success, memory_id, scope, associations_count}` |
| **full** | `{success, memory_id, scope, memory_object, associations_details, duplicate_analysis}` |

**Token Estimates:**
- minimal: ~20 tokens
- standard: ~80 tokens  
- full: ~300-500 tokens

### memory_search

| Level | Response Content |
|-------|------------------|
| **minimal** | `{success, total_count}` |
| **standard** | `{success, total_count, results: [{id, scope, content_preview(50)}]}` |
| **full** | `{success, total_count, results: [complete_memory_objects], search_metadata}` |

**Token Estimates:**
- minimal: ~15 tokens
- standard: ~100-200 tokens (depends on result count)
- full: ~500-2000 tokens (depends on content size)

### memory_manage (get)

| Level | Response Content |
|-------|------------------|
| **minimal** | `{success, exists: boolean}` |
| **standard** | `{success, memory: {id, scope, content_preview(100)}}` |
| **full** | `{success, memory: complete_object, associations, metadata}` |

### memory_manage (update/delete)

| Level | Response Content |
|-------|------------------|
| **minimal** | `{success}` |
| **standard** | `{success, affected_count, summary}` |
| **full** | `{success, affected_items, change_details}` |

### memory_discover_associations

| Level | Response Content |
|-------|------------------|
| **minimal** | `{success, association_count}` |
| **standard** | `{success, associations: [{target_id, strength, preview(50)}]}` |
| **full** | `{success, associations: [complete_objects], discovery_metadata}` |

### memory_move

| Level | Response Content |
|-------|------------------|
| **minimal** | `{success}` |
| **standard** | `{success, moved_count, target_scope}` |
| **full** | `{success, moved_items: [ids], source_scope, target_scope}` |

### memory_list_all

| Level | Response Content |
|-------|------------------|
| **minimal** | `{success, total_count}` |
| **standard** | `{success, total_count, memories: [{id, scope, preview(30)}]}` |
| **full** | `{success, memories: [complete_objects], pagination_info}` |

### memory_sync (export/import)

| Level | Response Content |
|-------|------------------|
| **minimal** | `{success, operation_type}` |
| **standard** | `{success, operation_type, item_count, file_path}` |
| **full** | `{success, operation_type, detailed_summary, file_info, processing_stats}` |

### scope_list

| Level | Response Content |
|-------|------------------|
| **minimal** | `{success, scope_count}` |
| **standard** | `{success, scopes: [{name, memory_count}]}` |
| **full** | `{success, scopes: [complete_hierarchy], statistics}` |

### scope_suggest

| Level | Response Content |
|-------|------------------|
| **minimal** | `{success, suggested_scope}` |
| **standard** | `{success, suggested_scope, confidence, alternatives[3]}` |
| **full** | `{success, suggestion_analysis, all_alternatives, reasoning}` |

### session_manage

| Level | Response Content |
|-------|------------------|
| **minimal** | `{success, session_id}` (create), `{success}` (other) |
| **standard** | `{success, session_info, action_summary}` |
| **full** | `{success, session_details, affected_memories, cleanup_stats}` |

## 🔨 Implementation Strategy

### Phase 1: Foundation (Day 1)
1. Create common models and utilities
2. Remove existing Config-based response level
3. Implement response builder helpers
4. Create foundation tests

### Phase 2: Tool Implementation (Days 2-3)
1. Add response_level parameter to all tools
2. Implement level-specific response logic
3. Update tool descriptions
4. Create tool-specific tests

### Phase 3: Integration & Testing (Day 4)
1. Integration testing
2. Performance verification
3. Documentation updates
4. Final test execution

## 🧪 Testing Strategy

### Unit Tests
- Response level enum functionality
- Common parameter validation
- Response builder utilities
- Content truncation functions

### Integration Tests
- Tool parameter inheritance
- Level-specific response generation
- Token count verification
- Workflow continuity tests

### Performance Tests
- Response generation time
- Memory usage comparison
- Token count measurements
- LLM context efficiency

## 📈 Success Metrics

### Token Efficiency
- minimal: <50 tokens per response
- standard: <200 tokens per response
- full: Comprehensive but optimized

### Operational Metrics
- Reduced tool call chains for standard operations
- Maintained functionality across all levels
- Consistent response format across tools

### User Experience
- Clear level descriptions
- Predictable response patterns
- Workflow optimization support

## 🔄 Migration Plan

### Backward Compatibility
- Default to `standard` level (current behavior)
- Graceful handling of missing parameter
- Gradual rollout across tools

### Configuration Migration
- Remove `api.default_response_level` from Config
- Update tool parameter schemas
- Update API documentation

## 📝 Usage Examples

### Minimal Level (Automation)
```python
# Bulk storage operation
for item in bulk_data:
    response = memory_store(
        content=item.content,
        response_level="minimal"
    )
    # Only gets: {success: true, memory_id: "abc123"}
```

### Standard Level (Interactive)
```python
# Normal workflow
response = memory_search(
    query="Python patterns",
    response_level="standard"  # default
)
# Gets: {success: true, total_count: 5, results: [{id, scope, preview}...]}
```

### Full Level (Analysis)
```python
# Detailed exploration
response = memory_discover_associations(
    memory_id="abc123",
    response_level="full"
)
# Gets: Complete association objects + metadata + discovery details
```

## 🚨 Important Notes

### Performance Considerations
- Full level may significantly increase response times
- Consider pagination for large result sets
- Monitor token usage in production

### Development Guidelines
- Always test all three levels
- Ensure minimal level provides sufficient workflow continuity
- Document level-specific behavior clearly

### Future Enhancements
- Dynamic level adjustment based on context size
- Custom level definitions for specific use cases
- Automatic optimization suggestions
