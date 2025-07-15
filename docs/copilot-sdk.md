# Copilot MCP SDK/Tool Usage Details

## Principles
- All implementations must follow the official MCP SDK and its conventions.
- Use mode-based dispatch; always validate mode before branching.
- Use parameters schema field for tools.
- On errors, use shared errorResponse() helper as defined in SDK.

## Example: Mode-based Dispatch
```python
def handle_tool(mode, params):
    if mode == "search":
        return search_handler(params)
    elif mode == "manage":
        return manage_handler(params)
    else:
        return errorResponse("Invalid mode")
```

## FAQ
- Q: Can I bypass SDK conventions for speed?
  - A: No. Always follow SDK and project rules.
- Q: What if SDK and project rules conflict?
  - A: Consult the user for a decision (see copilot-decision.md).

## Related (Error/Timeout/Decision)
- For error handling, see copilot-error-handling.md.
- For timeout handling, see copilot-timeout.md.
- For decision making, see copilot-decision.md.
