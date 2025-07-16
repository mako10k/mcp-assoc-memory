# Copilot Error Handling Details

## Principles
- Never implement fallback mechanisms or hide errors.
- Always fail fast and log errors with full context.
- **CRITICAL**: Distinguish between appropriate and forbidden fallbacks.

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

## Correct Example
```python
result = await core_operation()
if result is None:
    error_msg = "core_operation returned None - indicates fundamental issue"
    logger.error(error_msg, extra={"operation": "core_operation", "context": context})
    raise RuntimeError(error_msg)
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
