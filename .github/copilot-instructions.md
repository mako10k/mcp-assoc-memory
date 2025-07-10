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
- 🌐 **Code Language**: All source code should be in English (comments, docstrings, variable names, error messages).
- 🔄 **Internationalization**: When modifying code, convert any encountered Japanese text to English.
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

## ✅ Server Management Guidelines

### 🖥️ Server Start/Stop Operations

**Use these methods for server lifecycle management:**

1. **Daemon Script (Recommended)**:
   ```bash
   # Start server
   ./scripts/mcp_server_daemon.sh start
   
   # Stop server
   ./scripts/mcp_server_daemon.sh stop
   
   # Restart server
   ./scripts/mcp_server_daemon.sh restart
   
   # Check status
   ./scripts/mcp_server_daemon.sh status
   ```

2. **VS Code Tasks**:
   - Use VS Code's built-in task runner for development
   - Access via Command Palette: "Tasks: Run Task"

### 📝 Log Management

- **Server logs**: `logs/mcp_server.log`
- **Real-time monitoring**: `tail -f logs/mcp_server.log`
- **Log rotation**: Handled automatically by the daemon script

### ⚠️ Important Rules

- **Never use `run_in_terminal` for server management** - always use daemon script or VS Code tasks
- **Check server status** before making changes: `./scripts/mcp_server_daemon.sh status`
- **Monitor logs** after changes to verify successful operation
- **Use graceful restart** when updating configuration or code

---

## 📋 Current Project Status & Next Steps

**� Note**: Current project status and development tasks are now stored in the associative memory system. Use memory search to find current progress, completed tasks, and next priorities.

### Quick Context (Updated: 2025-07-10)
- **FastMCP 2.0 migration**: ✅ Complete
- **Associative memory features**: ✅ Restored (embedding-based search, similarity calculation)
- **Core architecture**: ✅ Integrated (MemoryManager, EmbeddingService, ChromaVectorStore)
- **User documentation**: ✅ Complete (Quick Start, Best Practices, API Reference, Examples, Troubleshooting)
- **Development reference**: ✅ Organized in development/ directory

**Important**: This project's core requirement is **associative memory functionality** - semantic similarity search and automatic association discovery between memories. Always maintain these capabilities.

## ✅ Terminal and Output Handling

**Note**: When using terminal commands, be aware of potential output display issues:

- **Terminal Output Bug**: The `run_in_terminal` tool may sometimes not display output properly
- **Workaround**: For critical commands, use output redirection: `command 2>&1 | tee /workspaces/mcp-assoc-memory/.copilot-temp/{task_name}-00001.log`
- **Alternative**: Use `script` command for complex scenarios that need full terminal emulation
- **Verification**: If terminal output appears empty, check the generated log files in `.copilot-temp/` directory
- **Best Practice**: Always verify command execution results through file system checks or direct file reading when output is missing
- **File Naming**: Use simple task names with 5-digit sequence numbers (e.g., `chroma-test-00001.log`), always ending with `.log`

## 📝 Note on Instruction Organization

This section was added to consolidate user-provided instructions. All relevant guidance has been integrated into the appropriate sections above to maintain consistency and clarity for LLM interactions.

## 📝 Note on Instruction Organization

For detailed developer guidelines including knowledge management workflow, library-first approach, and log file maintenance, see:
- **[development/workflow/DEVELOPER_GUIDELINES.md](../development/workflow/DEVELOPER_GUIDELINES.md)** - Developer workflow and best practices
- **[development/knowledge/diversified-search-algorithm.md](../development/knowledge/diversified-search-algorithm.md)** - Future search algorithm enhancements

---

## 🧠 MCP Associative Memory Integration (#AssocMemory)

**This project provides a complete associative memory system via MCP tools. Use these tools to enhance development workflow, knowledge management, and problem-solving.**

### 📚 Available Memory Tools

#### Core Memory Operations
- **#mcp_assocmemory_memory_store**: Store insights, learnings, and important information
- **#mcp_assocmemory_memory_search**: Find related memories using semantic search
- **#mcp_assocmemory_memory_get**: Retrieve detailed memory information
- **#mcp_assocmemory_memory_discover_associations**: Explore memory connections

#### Organization & Management
- **#mcp_assocmemory_scope_list**: Browse memory organization structure
- **#mcp_assocmemory_scope_suggest**: Get scope recommendations for content
- **#mcp_assocmemory_memory_move**: Reorganize memories into better categories
- **#mcp_assocmemory_session_manage**: Manage temporary working sessions

#### Utility Operations
- **#mcp_assocmemory_memory_list_all**: Browse complete memory collection
- **#mcp_assocmemory_memory_delete**: Remove unwanted memories

### 🎯 Integration Strategies

#### 1. Development Workflow Enhancement
```instructions
When implementing features or fixing bugs:
- Store problem analysis: Use #mcp_assocmemory_memory_store with scope "work/problems"
- Save solution patterns: Store successful approaches in "work/solutions" 
- Document lessons learned: Use "learning/development/[technology]" scopes
- Find similar issues: Use #mcp_assocmemory_memory_search before starting work
```

#### 2. Knowledge Management
```instructions
For building institutional knowledge:
- Store architectural decisions in "work/architecture" scope
- Document API patterns in "learning/api-design" scope  
- Save debugging insights in "work/debugging/[component]" scope
- Use #mcp_assocmemory_memory_discover_associations to connect related concepts
```

#### 3. Code Review & Documentation
```instructions
During code reviews and documentation:
- Store code quality insights in "work/code-quality" scope
- Document performance optimizations in "work/performance" scope
- Save security considerations in "work/security" scope
- Use #mcp_assocmemory_scope_suggest to categorize new insights automatically
```

#### 4. Project Context Management
```instructions
For project continuity:
- Create session: #mcp_assocmemory_session_manage with action="create"
- Store session context: Use "session/[project-name]" scope for temporary notes
- Resume work: #mcp_assocmemory_memory_search within session scope
- Cleanup: Use session_manage with action="cleanup" when project completes
```

### 💡 Best Practices for Memory Usage

#### Content Storage Strategy
- **Be specific**: Store concrete examples, not abstract concepts
- **Include context**: Add metadata about when/why information was relevant
- **Use consistent scoping**: Follow hierarchical patterns (e.g., "work/project/component")
- **Store solutions AND problems**: Don't just save what worked, save what didn't

#### Search Strategy
- **Start broad**: Use high-level terms first, then narrow down
- **Use semantic search**: The system understands concepts, not just keywords
- **Explore associations**: Use discover_associations to find unexpected connections
- **Iterate on scope**: Start with general scope, then focus on specific areas

#### Organization Patterns
```
Recommended scope hierarchy:
work/
  ├── projects/[name]/
  ├── architecture/
  ├── debugging/
  ├── code-review/
  └── meetings/

learning/
  ├── [technology]/
  ├── patterns/
  ├── best-practices/
  └── troubleshooting/

personal/
  ├── ideas/
  ├── goals/
  └── reflections/
```

### 🔄 Workflow Integration Examples

#### Example 1: Bug Investigation Workflow
```instructions
1. Search existing knowledge: #mcp_assocmemory_memory_search query="[error-description]"
2. Store investigation findings: #mcp_assocmemory_memory_store in "work/debugging/[component]"
3. Find related issues: #mcp_assocmemory_memory_discover_associations on stored memory
4. Document solution: Store resolution in "work/solutions/[component]"
```

#### Example 2: Feature Development Workflow
```instructions
1. Store requirements: #mcp_assocmemory_memory_store in "work/projects/[name]/requirements"
2. Research similar features: #mcp_assocmemory_memory_search for related implementations
3. Document design decisions: Store in "work/projects/[name]/design"
4. Link implementation notes: Use associations to connect design with implementation
```

#### Example 3: Learning & Research Workflow
```instructions
1. Suggest scope: #mcp_assocmemory_scope_suggest for new learning content
2. Store learning notes: Use suggested scope or "learning/[topic]"
3. Connect concepts: #mcp_assocmemory_memory_discover_associations between topics
4. Review knowledge: #mcp_assocmemory_memory_search to reinforce learning
```

### ⚠️ Memory Usage Guidelines

#### Do Use Memory For:
- ✅ Debugging insights and solution patterns
- ✅ Architectural decisions and trade-offs
- ✅ Performance optimization techniques
- ✅ Security considerations and best practices
- ✅ API design patterns and examples
- ✅ Project-specific knowledge and context

#### Don't Use Memory For:
- ❌ Sensitive information (credentials, personal data)
- ❌ Large code dumps (store patterns and insights instead)
- ❌ Temporary debugging output (use session scope for these)
- ❌ Version-specific details that quickly become outdated

### 🚀 Advanced Usage Patterns

#### Cross-Project Knowledge Transfer
```instructions
When starting similar projects:
1. Search for patterns: #mcp_assocmemory_memory_search across "work/patterns"
2. Find architectural decisions: Search "work/architecture" for similar challenges
3. Discover connections: Use associations to find unexpected relevant knowledge
```

#### Collaborative Knowledge Building
```instructions
For team knowledge sharing:
1. Store team insights in shared scope patterns
2. Use consistent categorization via #mcp_assocmemory_scope_suggest
3. Build knowledge graphs through association discovery
4. Regular cleanup via #mcp_assocmemory_session_manage
```

#### Continuous Learning Integration
```instructions
For ongoing skill development:
1. Store daily learnings in "learning/daily/[date]" scope
2. Weekly review: Search and associate related learnings
3. Monthly consolidation: Move valuable insights to permanent scopes
4. Quarterly cleanup: Archive or reorganize outdated information
```

### 🎯 Quick Reference Commands

```bash
# Store important insight
#mcp_assocmemory_memory_store with scope="work/insights" 

# Find related knowledge
#mcp_assocmemory_memory_search query="[your-question]"

# Explore connections
#mcp_assocmemory_memory_discover_associations memory_id="[found-memory-id]"

# Get scope suggestion
#mcp_assocmemory_scope_suggest content="[your-content]"

# Browse organization
#mcp_assocmemory_scope_list parent_scope="work"

# Start project session
#mcp_assocmemory_session_manage action="create" session_id="[project-name]"
```

**Remember**: The associative memory system is designed to augment your development workflow. Use it actively to build institutional knowledge, find connections between concepts, and accelerate problem-solving through accumulated wisdom.

---

## 🌐 Internationalization Guidelines

**This project follows international coding standards with English as the primary language.**

### Code Language Standards
- **Source Code**: All code must be written in English
  - Variable names, function names, class names
  - Comments and docstrings
  - Error messages and log messages
  - Constants and configuration values

### During Development
- **🔄 Active Conversion**: When modifying any file, convert encountered Japanese text to English
- **📝 Documentation**: Prioritize English documentation for international accessibility
- **🚫 No Mixed Languages**: Avoid mixing Japanese and English within the same file/module

### Conversion Priority
1. **High Priority**: Source code (`.py`, `.js`, `.ts` files)
2. **Medium Priority**: Configuration files (`config.py`, `pyproject.toml`)
3. **Low Priority**: Documentation files (can be translated gradually)

### Examples of Required Changes
```python
# ❌ Avoid (Japanese)
def 記憶を保存(content: str) -> Memory:
    """記憶をストレージに保存する"""
    logger.error(f"保存エラー: {e}")

# ✅ Preferred (English)
def store_memory(content: str) -> Memory:
    """Store memory to storage"""
    logger.error(f"Storage error: {e}")
```

### Exception Cases
- **Legacy Documentation**: Existing Japanese documentation can be preserved temporarily
- **User-Facing Content**: Content specifically intended for Japanese users
- **Test Data**: Sample content in tests may remain in Japanese if testing internationalization

---