# Copilot Decision Making Details

## Principles
- Never make independent decisions on branching issues; always consult user.
- Always ask for guidance when uncertainty exists.

## Correct Example
```
ERROR: Found type mismatch in memory_tools.py line 265
QUESTION: Should I (A) fix by changing parameter type, (B) update response class, or (C) investigate root cause first?
WAITING: For user decision before proceeding
```

## Forbidden Example
```
ERROR: Found type mismatch - attempting automatic fix...
FIXING: Changing parameter type based on my analysis...  # FORBIDDEN
```

## FAQ
- Q: What if there are multiple possible fixes?
  - A: Always present options and ask the user.
- Q: Can I ever auto-fix minor issues?
  - A: No. Always confirm with the user first.

## Related (Error/Timeout)
- If a decision involves error or timeout, see copilot-error-handling.md and copilot-timeout.md.
