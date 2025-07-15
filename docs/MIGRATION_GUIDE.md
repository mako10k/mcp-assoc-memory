# Response Level Migration Guide

## 📖 Overview

This guide helps you migrate from the legacy API to the new **response_level** parameter system introduced in July 2025. The new system provides better token efficiency and response control across all MCP tools.

## 🔄 What Changed

### Before (Legacy API)
```json
// Old approach - no response control
{
  "request": {
    "content": "My memory content",
    "minimal_response": true  // Only available on some tools
  }
}
```

### After (2025 API)
```json
// New unified approach - available on ALL tools
{
  "request": {
    "content": "My memory content", 
    "response_level": "minimal"  // "minimal" | "standard" | "full"
  }
}
```

## ✅ Migration Steps

### 1. Replace Legacy Parameters

#### Old Parameters (Remove These)
- `minimal_response: true/false` → Use `response_level: "minimal"/"standard"`
- Any tool-specific response control → Use unified `response_level`

#### New Parameter (Add This)
- `response_level: "minimal" | "standard" | "full"`

### 2. Update Your Workflows

#### Token-Conscious Operations
```json
// OLD: Limited to specific tools
{"minimal_response": true}

// NEW: Available on ALL 10 tools  
{"response_level": "minimal"}
```

#### Standard Operations (Default)
```json
// OLD: Default behavior (no parameter)
{}

// NEW: Explicit control (optional - "standard" is default)
{"response_level": "standard"}
```

#### Detailed Analysis
```json
// OLD: No unified way to get full details
{"include_associations": true, "include_metadata": true}

// NEW: Simple and consistent
{"response_level": "full"}
```

## 🛠️ Tool-Specific Changes

### All 10 Tools Now Support
Every MCP tool now accepts `response_level`:

1. `memory_store`
2. `memory_search` 
3. `memory_manage`
4. `memory_discover_associations`
5. `memory_move`
6. `memory_sync`
7. `scope_list`
8. `scope_suggest`
9. `session_manage`
10. `memory_list_all`

### Response Level Behavior

#### Minimal Level
- **Purpose**: Essential data only (<50 tokens avg)
- **Contains**: Success status, core IDs, basic counts
- **Use case**: Bulk operations, token efficiency

#### Standard Level (Default)
- **Purpose**: Balanced information for workflow continuity
- **Contains**: Content previews, basic metadata, operation results  
- **Use case**: Interactive work, regular operations

#### Full Level
- **Purpose**: Complete detailed information
- **Contains**: Full content, associations, comprehensive metadata
- **Use case**: Analysis, research, debugging

## 📝 Migration Examples

### Memory Storage
```json
// OLD
{
  "request": {
    "content": "Project notes",
    "minimal_response": true
  }
}

// NEW  
{
  "request": {
    "content": "Project notes",
    "response_level": "minimal"
  }
}
```

### Memory Search
```json
// OLD
{
  "request": {
    "query": "Python tips"
  }
}

// NEW (explicit control)
{
  "request": {
    "query": "Python tips",
    "response_level": "standard"  // Or "minimal"/"full"
  }
}
```

### Association Discovery
```json
// OLD (limited control)
{
  "request": {
    "memory_id": "abc123",
    "include_details": true
  }
}

// NEW (unified control)
{
  "request": {
    "memory_id": "abc123", 
    "response_level": "full"
  }
}
```

## ⚡ Performance Benefits

### Token Efficiency
- **Minimal responses**: 50%+ token reduction
- **Selective detail**: Choose information level based on need
- **Batch operations**: Faster processing with minimal responses

### Response Times  
- **Faster minimal responses**: Less data processing and transfer
- **Cached standard responses**: Optimized for common use cases
- **Rich full responses**: Complete context when needed

## 🧪 Testing Your Migration

### Validation Steps
1. **Replace legacy parameters** with `response_level`
2. **Test each response level** for your use cases
3. **Measure token improvements** in your workflows
4. **Verify functionality** matches your expectations

### Test Commands
```bash
# Test minimal responses
memory_store content="test" response_level="minimal"

# Test standard responses (default)
memory_search query="test" response_level="standard"

# Test full responses
memory_discover_associations memory_id="test" response_level="full"
```

## 🚨 Breaking Changes

### None!
- **Backward compatible**: Existing code continues to work
- **Default behavior**: Unchanged (equivalent to "standard" level)
- **Legacy parameters**: Gracefully handled where they existed

### Deprecation Timeline
- **Legacy parameters**: Still supported but deprecated
- **Recommended**: Migrate to `response_level` for consistency
- **Future**: Legacy parameters may be removed in future versions

## ❓ FAQ

### Q: Do I need to update all my tools at once?
**A**: No, migration can be gradual. Tools without `response_level` use "standard" behavior.

### Q: What if I don't specify response_level?
**A**: The default is "standard" which matches current behavior.

### Q: Will minimal responses break my workflows? 
**A**: No, minimal responses include all essential data. Test with your specific use case.

### Q: How much token savings can I expect?
**A**: 50%+ reduction with minimal responses, varies by tool and content.

### Q: Are there any performance costs?
**A**: No, response building adds <100ms overhead and actually improves performance for minimal responses.

## 📞 Support

### Getting Help
- **Issues**: Report via GitHub Issues
- **Questions**: Check documentation or create discussion
- **Best Practices**: See docs/user-guide/BEST_PRACTICES.md

### Additional Resources  
- **API Reference**: Complete parameter documentation
- **User Guide**: Response level usage patterns
- **Performance Guide**: Optimization recommendations
