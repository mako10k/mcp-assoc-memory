# Copilot Timeout Handling Details

## Principles
- Never avoid investigation due to timeouts; always investigate root cause.
- Always use appropriate timeout values for complex operations.

## Correct Example
```python
# Extend timeout for complex initialization
result = await shell_execute(command, timeout_seconds=120)
# If it times out, investigate WHY it hangs, don't simplify the test
```

## Forbidden Example
```python
# This times out, so let's try something simpler
try:
    complex_test(timeout=30)  # Times out
except TimeoutError:
    simple_test()  # FORBIDDEN - avoids the real issue
```

## FAQ
- Q: How should I set timeout values?
  - A: Use 30-60s for complex ops, 120s+ for initialization. Never reduce just to avoid errors.
- Q: What if a timeout keeps happening?
  - A: Investigate the underlying cause, do not switch to a simpler test.

## Related (Error/Decision)
- If a timeout leads to an error, follow error handling rules (see copilot-error-handling.md).
- Never change test strategy due to timeouts without user approval (see copilot-decision.md).
