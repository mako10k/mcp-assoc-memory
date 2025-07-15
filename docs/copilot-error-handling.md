# Copilot Error Handling Details

## Principles
- Never implement fallback mechanisms or hide errors.
- Always fail fast and log errors with full context.

## Correct Example
```python
result = await core_operation()
if result is None:
    error_msg = "core_operation returned None - indicates fundamental issue"
    logger.error(error_msg, extra={"operation": "core_operation", "context": context})
    raise RuntimeError(error_msg)
```

## Forbidden Example
```python
try:
    result = await advanced_operation()
except Exception:
    result = fallback_operation()  # FORBIDDEN - hides the real problem
```

## FAQ
- Q: What if the SDK throws an unexpected exception?
  - A: Log the error with full context and raise immediately. Never fallback silently.
- Q: Should I ever suppress errors for user experience?
  - A: No. Always surface errors for diagnosis.

## Related (Timeout/Decision)
- If a timeout occurs, always investigate the root cause (see copilot-timeout.md).
- Never decide to fallback or retry without explicit user instruction (see copilot-decision.md).
