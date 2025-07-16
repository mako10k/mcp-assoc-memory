# Memory Export Bug - Root Cause Analysis

## Issue: Export returns 0 memories despite 43 memories existing

### Root Cause
**Data Source Mismatch**: Export function accesses wrong storage layer

### Technical Details

#### Current Implementation Problem
```python
# In export_tools.py line 33-34
for memory_data in memory_storage.values():
    # memory_storage comes from simple_persistence.py
```

#### Issue Analysis
1. **Export accesses**: `memory_storage` from `simple_persistence.py` (file-based JSON storage)
2. **Actual data stored in**: SQLite database via `MemoryManagerCore`
3. **Result**: Export sees empty/outdated simple storage, misses real data

#### Evidence
- `memory_list_all` works correctly (uses proper database access)
- Export returns 0 (uses wrong storage layer)
- All 43 memories are in SQLite database, not in simple JSON storage

### Technical Root Cause
Export functionality was implemented to use FastMCP's simple persistence layer instead of the actual memory manager database. This creates a complete disconnect between where data is stored (SQLite) and where export looks for it (JSON file).

### Required Fix
Export function must access the same storage layer as other memory operations:
1. Use `MemoryManagerCore` instance
2. Access SQLite metadata store directly
3. Query same database as `memory_list_all`

### Files Requiring Changes
- `src/mcp_assoc_memory/api/tools/export_tools.py` (primary fix)
- Ensure export uses same storage as `memory_tools.py`

### Priority: Critical
Essential backup functionality completely non-functional due to architectural mismatch.
