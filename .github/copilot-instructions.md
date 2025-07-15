## ✅ Context Preservation and Forgetting Mitigation

- Periodically record conversation history and key context using `#mcp_assocmemory_memory_store` to associative memory.
- Minimize use of Copilot's summarization features to avoid context loss.
- Important conversation history must also be recorded to a file (see file design in project docs).
- After summarization or context loss, always refer to associative memory and restore context only after explicit user instruction.


# GitHub Copilot Instructions (MCP Associative Memory Project)

> **LLM-First Principle:**
> This file is for LLM-based AI assistants only. All structure and content must prioritize unambiguous parsing and operational clarity for LLMs. Human readability is secondary.



## ✅ Essential Rules (Summary)
- Always check actual implementation before proposing changes
- Use strict typing for all inputs/outputs
- Follow existing structure and naming conventions
- Prefer reuse of existing utilities
- Run mypy before any modification
- All source code in English (except user-facing Japanese)
- Never make independent decisions on branching issues; always consult user
- All implementations must follow the official MCP SDK and its conventions
- All Copilot/AI assistants must always refer to this file as the primary source of operational rules and project instructions
- No action should be taken that contradicts this file


## ✅ Essential Development Rules
- Always check actual implementation before proposing changes
- Use strict typing for all inputs/outputs
- Follow existing structure and naming conventions
- Prefer reuse of existing utilities
- Run mypy before any modification
- All source code in English (except user-facing Japanese)
- Never make independent decisions on branching issues; always consult user

## ✅ MCP Tool Development
- Use mode-based dispatch; always validate mode before branching
- All implementations must follow the official MCP SDK and its conventions
- Use parameters schema field for tools
- On errors, use shared errorResponse() helper as defined in SDK

## ✅ LLM/AI Assistant Operational Rule
- All Copilot/AI assistants must always refer to this .github/copilot-instructions.md file as the primary source of operational rules and project instructions
- No action should be taken that contradicts this file

## ✅ Critical Operations


### Server Management & Terminal Operations
**Never use `run_in_terminal` for server or terminal management.**
Always use `#mcp_shellserver_shell_execute` or `#mcp_shellserver_terminal_create` for all server and terminal operations.

Recommended:
```bash
# Server management
./scripts/mcp_server_daemon.sh [start|stop|restart|status]
# Or use VS Code "Tasks: Run Task"
# For terminal operations and command execution
# Always use #mcp_shellserver_shell_execute or #mcp_shellserver_terminal_create
```

### Terminal Bug Workaround
- **Issue**: `run_in_terminal` may not display output properly
- **Solution**: Use output redirection: `command 2>&1 | tee .copilot-temp/{task}-00001.log`
- **Verification**: Check log files in `.copilot-temp/` if output missing

## ✅ Associative Memory Integration

**Use MCP associative memory tools actively for development workflow:**

### � **Core Tools (Production API)**
- `#mcp_assocmemory_memory_search` - Comprehensive search (standard/diversified modes)
- `#mcp_assocmemory_memory_manage` - CRUD operations (get/update/delete)

### Error Handling Mandate
- Never implement fallback mechanisms or hide errors
- Always fail fast and log errors with full context
- See details and examples: [docs/copilot-error-handling.md](../docs/copilot-error-handling.md)

work/

### Timeout Handling Mandate
- Never avoid investigation due to timeouts; always investigate root cause
- Always use appropriate timeout values for complex operations
- See details and examples: [docs/copilot-timeout.md](../docs/copilot-timeout.md)

- **Legacy Removal**: All old/redundant tools removed for clarity

### Code Language Standards
- All source code in English (except user-facing Japanese)
- When modifying, convert any Japanese text to English

- **Performance Optimization**: Query response time improvements

### Decision Making Limitations
- Never make independent decisions on branching issues; always consult user
- Always ask for guidance when uncertainty exists
- See details and examples: [docs/copilot-decision.md](../docs/copilot-decision.md)

### 2. File Reference Management
- Store file references in the metadata field of associative memory, e.g.:
  metadata: {
    "file_ref": "/data/important_history/decision-20250715.md",
    "summary": "Design policy decision",
    "tags": ["architecture", "decision"]

## ✅ Usage: When to Reference Detail Files

- For error handling: see [docs/copilot-error-handling.md](../docs/copilot-error-handling.md)
- For timeout handling: see [docs/copilot-timeout.md](../docs/copilot-timeout.md)
- For decision making: see [docs/copilot-decision.md](../docs/copilot-decision.md)
- For SDK/tool usage: see [docs/copilot-sdk.md](../docs/copilot-sdk.md)

Refer to each detail file only when the corresponding context or user request requires it. Do not load all detail files by default.

