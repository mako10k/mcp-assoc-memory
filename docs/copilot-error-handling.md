# Copilot Contract Programming & Error Handling Details

## Contract Programming Principles
- **Design by Contract**: All functions must validate preconditions with assert statements
- **Fail-Fast Execution**: Stop immediately when contracts are violated
- **State Consistency**: Ensure object states match expected contracts
- **Transparent Operations**: All operations must be visible and auditable
- Never implement fallback mechanisms or hide errors.
- Always fail fast and log errors with full context.
- **CRITICAL**: Distinguish between appropriate and forbidden fallbacks.

## Contract Programming Implementation

### Required Assert Patterns
```python
# ✅ Memory Manager Contract
def process_memories(memory_manager, ctx):
    # Precondition validation
    assert memory_manager is not None, "Memory manager is required"
    assert hasattr(memory_manager, 'metadata_store'), f"Missing metadata_store: {type(memory_manager)}"
    assert ctx is not None, "Context object is required for operations"
    assert hasattr(ctx, 'info'), f"Context missing 'info' method: {type(ctx)}"
    assert hasattr(ctx, 'error'), f"Context missing 'error' method: {type(ctx)}"

# ✅ Data Structure Contract
def import_memory(memory_data, memory_id):
    # Required fields validation
    assert "content" in memory_data, f"Memory data missing required 'content' field: {memory_id}"
    assert "scope" in memory_data, f"Memory data missing required 'scope' field: {memory_id}"
    assert memory_data["content"], f"Memory content cannot be empty: {memory_id}"

# ✅ State Consistency Contract
def get_initialized_manager():
    if is_memory_manager_initialized():
        manager = get_memory_manager()
        assert manager is not None, "Manager initialized but returned None - critical state inconsistency"
        return manager
    return None
```

## Silent Fallback Prohibition
**What is a Silent Fallback?**
- Error handling that user doesn't notice
- Automatic substitution of failed operations
- AI-implemented workarounds without user consultation

**Examples of Forbidden Silent Fallbacks:**
```python
try:
    result = primary_operation()
except Exception:
    result = fallback_operation()  # FORBIDDEN - hides the real problem
    return result  # User never knows primary failed
```

### Contract Violations to Avoid
```python
# ❌ Forbidden: hasattr() with default values
def bad_get_metadata(memory):
    return memory.metadata if hasattr(memory, 'metadata') else {}

# ✅ Correct: Assert required attributes
def good_get_metadata(memory):
    assert hasattr(memory, 'metadata'), f"Memory object missing metadata: {type(memory)}"
    return memory.metadata

# ❌ Forbidden: try/except/pass pattern
def bad_get_manager():
    try:
        if is_initialized():
            return get_manager()
    except Exception:
        pass  # FORBIDDEN - silent error hiding
    return None

# ✅ Correct: Contract programming
def good_get_manager():
    if is_initialized():
        manager = get_manager()
        assert manager is not None, "Initialized but manager is None"
        return manager
    return None
```

## Appropriate vs Forbidden Fallbacks

### ✅ Appropriate Fallbacks (User-Approved, Transparent)
```python
# Explicit user consultation required
logger.warning("Primary service failed. Consulting user for fallback strategy...")
user_decision = await consult_user("Primary failed. Use fallback? (y/n)")
if user_decision:
    logger.info("User approved fallback to secondary service")
    result = fallback_operation()
else:
    raise RuntimeError("Primary operation failed, user declined fallback")
```

### ❌ Forbidden Fallbacks (AI-Decided, Silent)
```python
try:
    result = await advanced_operation()
except Exception:
    result = fallback_operation()  # FORBIDDEN - hides the real problem
```

## Implementation Examples from MCP Associative Memory

### ✅ Singleton Memory Manager Contract Implementation
```python
def get_memory_manager():
    """Get the singleton memory manager instance with contract validation."""
    global _memory_manager_instance
    
    if _memory_manager_instance is None:
        assert is_memory_manager_initialized(), "Memory manager not initialized but requested"
        raise RuntimeError("Memory manager not initialized - call initialize_memory_manager() first")
    
    # Contract: instance must exist if initialized
    assert _memory_manager_instance is not None, "Initialized but instance is None - critical state inconsistency"
    
    return _memory_manager_instance

def initialize_memory_manager(config: Config, ctx: LoggingContext):
    """Initialize memory manager with full contract validation."""
    global _memory_manager_instance, _is_initialized
    
    # Precondition contracts
    assert config is not None, "Config is required for memory manager initialization"
    assert ctx is not None, "Logging context is required for operations"
    
    if _is_initialized:
        assert _memory_manager_instance is not None, "Marked initialized but no instance exists"
        return _memory_manager_instance
```

### ✅ Import Function Contract Implementation
```python
async def import_memories(import_data, target_scope_prefix: Optional[str] = None):
    """Import memories with comprehensive contract validation."""
    # Input contracts
    assert import_data is not None, "Import data cannot be None"
    assert "memories" in import_data, "Import data must contain 'memories' field"
    
    memories = import_data["memories"]
    assert isinstance(memories, list), f"Memories must be a list, got {type(memories)}"
    
    # Memory manager contract
    memory_manager = get_or_create_memory_manager()
    assert memory_manager is not None, "Failed to get memory manager for import operation"
    
    for memory_data in memories:
        # Individual memory contracts
        assert "content" in memory_data, f"Memory missing required 'content' field"
        assert "scope" in memory_data, f"Memory missing required 'scope' field"
        assert memory_data["content"], f"Memory content cannot be empty"
```

## Correct Example
```python
result = await core_operation()
if result is None:
    error_msg = "core_operation returned None - indicates fundamental issue"
    logger.error(error_msg, extra={"operation": "core_operation", "context": context})
    raise RuntimeError(error_msg)
```

## Before vs After Contract Programming

### ❌ Before: Silent Fallback Pattern (FORBIDDEN)
```python
# From singleton_memory_manager.py (old implementation)
def get_memory_manager():
    global _memory_manager_instance
    try:
        if _is_initialized and _memory_manager_instance:
            return _memory_manager_instance
    except Exception:
        pass  # SILENT ERROR HIDING
    return None  # SILENT FAILURE
```

### ✅ After: Contract Programming Pattern (REQUIRED)
```python
# From singleton_memory_manager.py (new implementation)
def get_memory_manager():
    global _memory_manager_instance
    
    if _memory_manager_instance is None:
        assert is_memory_manager_initialized(), "Memory manager not initialized but requested"
        raise RuntimeError("Memory manager not initialized - call initialize_memory_manager() first")
    
    # Contract: instance must exist if initialized
    assert _memory_manager_instance is not None, "Initialized but instance is None - critical state inconsistency"
    
    return _memory_manager_instance
```

## FAQ
- Q: What if the SDK throws an unexpected exception?
  - A: Log the error with full context and raise immediately. Never fallback silently.
- Q: Should I ever suppress errors for user experience?
  - A: No. Always surface errors for diagnosis.
- Q: Can I implement fallbacks if they improve reliability?
  - A: Only with explicit user consultation and transparent implementation.

## Related (Timeout/Decision)
- If a timeout occurs, always investigate the root cause (see copilot-timeout.md).
- Never decide to fallback or retry without explicit user instruction (see copilot-decision.md).
