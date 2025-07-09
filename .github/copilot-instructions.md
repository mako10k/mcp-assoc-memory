# GitHub Copilot Instructions (MCP Projects)

## ✅ Overview

This project implements a memory-centered LLM assistant system using the Model Context Protocol (MCP).  
Tools, memory management, and domain-aware knowledge access are key parts of the architecture.

Copilot should follow the rules below when generating or modifying code in this repository.

---

## ✅ General Rules

- 🔍 **Always refer to actual implementation**, not assumptions. Check code before proposing changes.
- 🧱 **Use strict typing**: all inputs and outputs must follow the defined types.
- 📄 **Respect existing structure**: follow the current file/module layout and naming conventions.
- 🔁 **Prefer reuse**: Do not reimplement normalization, validation, or formatting logic — use utilities if they exist.
- ⚠️ **Do not guess** CLI flags, config structure, or environment variables — check usage in entrypoints or config loaders.
- ✅ If unsure, suggest a verification method (e.g. "Check how Config is loaded in main.ts").

---

## ✅ When Handling MCP Tools

- Each tool handler uses a `mode`-based dispatch. Always validate `mode` before branching.
- On errors, always return `data: {}` or a known-safe structure. Avoid `undefined` values.
- Tool responses must follow the MCP JSON-RPC spec:
  ```json
  {
    "success": true | false,
    "message": "...",
    "error": "...",
    "data": {}
  }
  ```
- `parameters` is the correct schema field for tools — **not** `inputSchema` (except for legacy Inspector compatibility).

---

## ✅ Style and Project Conventions

- 🧪 Tests: Use Jest or the built-in test framework. Organize in `tests/unit/` or `tests/integration/`.
- 🧾 Typing: Use strict, JSON-compatible types. Avoid `any` unless explicitly required.
- 📁 Directory structure:
  ```
  src/
    ├── core/        # Logic (memory, projects, similarity, etc.)
    ├── transport/   # HTTP/STDIO/SSE servers
    ├── handlers/    # Tool implementations
    ├── types/       # Schema definitions
    ├── utils/       # Shared helpers
  ```

---

## ✅ Error Handling Guidelines

- Use a shared `errorResponse()` helper for all tool errors.
- Always include a defined `data` field in responses.
- Do not return raw exceptions; extract message and type.

Example:

```ts
return errorResponse("VALIDATION_ERROR", "Missing 'content' field", { content: "" });
```

---

## ✅ CI Expectations

- All code must pass type checking, linting, and unit tests before merge.
- Coverage should remain above 80% for core modules.
- Copilot should suggest tests alongside new code if none exist.

---

## ✅ Prompt Design for Copilot

If code behavior seems unclear, prompt Copilot with:

```
- What type does this function expect?
- What existing utilities handle X?
- Where is config loaded in this project?
- What should a valid tool response look like?
```

---

## 🧩 Tips

- MCP Inspector requires `inputSchema` only for older versions — default to `parameters` and mirror it if needed.
- Always test changes using a real `tools/call` or `tools/list` JSON-RPC request, not just code shape.

---

## 📋 Current Project Status & Next Steps

**🔗 For detailed current status and immediate todos, see: [CURRENT_STATUS_AND_TODO.md](../CURRENT_STATUS_AND_TODO.md)**

### Quick Context (Updated: 2025-07-09)
- **FastMCP 2.0 migration**: ✅ Complete
- **Associative memory features**: ✅ Restored (embedding-based search, similarity calculation)
- **Core architecture**: ✅ Integrated (MemoryManager, EmbeddingService, ChromaVectorStore)
- **Next priority**: 🔧 Dependency verification, initialization stabilization, basic testing

**Important**: This project's core requirement is **associative memory functionality** - semantic similarity search and automatic association discovery between memories. Always maintain these capabilities.
