# Memory Export Functionality Bug

## Bug Summary
`memory_sync` export operation returns 0 exported memories despite confirmed memory existence in the system.

## Environment
- **MCP Associative Memory Version**: v0.1.2+
- **Python Version**: 3.x
- **Operating System**: Linux
- **Date Discovered**: 2025-07-16

## Problem Description

### What Happened
- Executed `mcp_assocmemory_memory_sync` with `operation="export"`
- Function returned `{"exported_count": 0, "file_path": "backup/memory-export-2025-07-16-full.json"}`
- However, `mcp_assocmemory_memory_list_all` confirms 43 memories exist in the system

### Expected Behavior
Export operation should successfully export all 43 existing memories to the specified file.

### Actual Behavior
Export operation returns 0 exported memories, creating empty or near-empty export files.

## Reproduction Steps

1. Ensure system contains multiple memories (verify with `memory_list_all`)
2. Execute `memory_sync` with `operation="export"`
3. Observe returned `exported_count` is 0 despite existing memories
4. Check export file size is minimal (~200 bytes instead of expected KB)

## Evidence

### System State Verification
```json
// memory_list_all results
{
  "total_count": 43,
  "memories": [/* 43 memory objects */]
}
```

### Export Operation Results
```json
// First export attempt
{
  "exported_count": 0,
  "file_path": "backup/memory-export-2025-07-16-full.json"
}

// Second export attempt with compression
{
  "exported_count": 0,
  "export_size": 200
}
```

## Impact Assessment

- **Severity**: High
- **Impact**: Core backup functionality is non-functional
- **Risk**: Data loss potential if system corruption occurs
- **User Experience**: Cannot perform essential data backups

## Workaround
Manual backup using `memory_list_all` and file creation:
1. Use `memory_list_all` to retrieve all memories
2. Manually save results to JSON file
3. Successful backup achieved this way

## Investigation Suggestions

1. **Export Implementation**: Check `src/mcp_assoc_memory/tools/export_tools.py`
2. **Database Query**: Verify export operation's memory retrieval logic
3. **Scope Filtering**: Test if export works with specific scope filters
4. **File I/O**: Validate export file writing operations
5. **Memory Manager Integration**: Check connection between export and storage layers

## Additional Context

- System successfully operates for all other memory operations (store, search, list)
- Manual backup confirmed all data integrity
- Issue appears isolated to export functionality only
- No error messages or exceptions thrown during export

## Files Affected
- `src/mcp_assoc_memory/tools/export_tools.py` (likely)
- Memory export/sync functionality
- Backup/restore operations

## Priority
**High** - Essential backup functionality is broken, posing data loss risk.
