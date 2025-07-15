# Response Level Migration Guide

## 🆕 New Feature: Response Level Control

**Version:** July 2025  
**Status:** Production Ready ✅  
**Backward Compatibility:** 100% - No breaking changes

## 📋 Overview

All 10 MCP tools now support intelligent response detail control through the `response_level` parameter. This feature provides:

- **Token optimization** for cost-effective LLM interactions
- **Flexible detail levels** for different use cases
- **Backward compatibility** with existing integrations

## 🚀 Quick Start

### Add Response Level to Any Tool
```python
# Before (still works - defaults to "standard")
memory_store(content="Meeting notes", scope="work/meetings")

# After (optional parameter for optimization)
memory_store(content="Meeting notes", scope="work/meetings", response_level="minimal")
```

### Three Available Levels

1. **`"minimal"`** - Essential information only (~50 tokens)
2. **`"standard"`** - Balanced detail (default - same as before)
3. **`"full"`** - Comprehensive information with all metadata

## 🔄 Migration Steps

### Step 1: No Action Required
Your existing code continues to work unchanged. All tools default to `"standard"` level, providing the same responses as before.

### Step 2: Optimize for Your Use Case (Optional)

#### For Bulk Operations or Status Checks
```python
# Use minimal for better performance
for item in bulk_data:
    memory_store(content=item, response_level="minimal")
```

#### For Interactive Workflows
```python
# Use standard (default) for normal operations
result = memory_search(query="project ideas")  # Same as before
```

#### For Debugging or Analysis
```python
# Use full for comprehensive information
result = memory_search(query="complex topic", response_level="full")
print(result["search_metadata"])  # Additional debug info
```

## 📊 Response Comparison

### memory_store Examples

#### Minimal Response
```json
{
  "success": true,
  "message": "Memory stored successfully: abc123",
  "memory_id": "abc123"
}
```

#### Standard Response (Default)
```json
{
  "success": true,
  "message": "Memory stored successfully: abc123", 
  "memory_id": "abc123",
  "scope": "work/projects",
  "associations_count": 2,
  "created_at": "2025-07-15T08:00:00.000Z"
}
```

#### Full Response
```json
{
  "success": true,
  "message": "Memory stored successfully: abc123",
  "memory_id": "abc123", 
  "scope": "work/projects",
  "associations_count": 2,
  "created_at": "2025-07-15T08:00:00.000Z",
  "memory": {
    "id": "abc123",
    "content": "Full content here...",
    "scope": "work/projects",
    "metadata": {...},
    "tags": [...],
    "category": "...",
    "created_at": "2025-07-15T08:00:00.000Z",
    "updated_at": "2025-07-15T08:00:00.000Z"
  },
  "duplicate_analysis": {
    "duplicate_check_performed": false,
    "threshold_used": null
  }
}
```

## 🎯 Best Practices

### Choose the Right Level

| Use Case | Recommended Level | Reason |
|----------|------------------|--------|
| Bulk data import | `minimal` | Fastest, lowest token usage |
| Interactive exploration | `standard` | Balanced info for next actions |
| Status monitoring | `minimal` | Quick success/failure checks |
| Workflow automation | `standard` | Sufficient context for decisions |
| Debugging issues | `full` | Complete information for analysis |
| Data analysis | `full` | All metadata and associations |

### Performance Optimization

```python
# Efficient bulk operations
results = []
for item in large_dataset:
    result = memory_store(
        content=item["content"],
        scope=item["scope"],
        response_level="minimal"  # Saves tokens
    )
    results.append(result["memory_id"])

# Detailed analysis when needed
detailed = memory_manage(
    operation="get",
    memory_id=results[0],
    response_level="full"  # Get complete info
)
```

## 🔧 Tool-Specific Features

### memory_search
- **Minimal**: Basic results with IDs and scores
- **Standard**: Includes content previews and metadata
- **Full**: Complete memory objects and search analytics

### scope_suggest  
- **Minimal**: Single suggestion only
- **Standard**: Includes reasoning and alternatives
- **Full**: Detailed analysis metadata and confidence scores

### memory_discover_associations
- **Minimal**: Association count and basic info
- **Standard**: Related memory previews
- **Full**: Complete association analysis and similarity matrix

## ❓ FAQ

### Q: Will this break my existing code?
**A:** No. All existing code continues to work unchanged. The `response_level` parameter is optional and defaults to `"standard"` (same behavior as before).

### Q: What's the performance impact?
**A:** Minimal overhead (<100ms) for level processing. Significant token savings with `"minimal"` level.

### Q: Can I mix levels in the same workflow?
**A:** Yes! Use different levels for different operations based on your needs.

### Q: Is this available in all tools?
**A:** Yes, all 10 MCP tools support response levels with consistent behavior.

## 🚀 Next Steps

1. **Keep using your existing code** - No changes required
2. **Experiment with levels** - Try `minimal` for bulk operations
3. **Optimize gradually** - Add response levels where they provide value
4. **Monitor token usage** - Track savings with minimal level

## 📞 Support

For questions or issues:
- Check the [API Reference](./API_REFERENCE_2025.md) for detailed examples
- See [Best Practices](../user-guide/BEST_PRACTICES.md) for optimization tips
- Review [Troubleshooting](../troubleshooting/README.md) for common issues
