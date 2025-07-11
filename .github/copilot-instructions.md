# GitHub Copilot Instructions (MCP Associative Memory Project)

## ✅ Project Context

This project implements a memory-centered LLM assistant system using the Model Context Protocol (MCP).  
**Core requirement**: Associative memory functionality - semantic similarity search and automatic association discovery between memories.

## ✅ Essential Development Rules

### Code Quality
- **Always check actual implementation** before proposing changes - never assume
- **Use strict typing** - all inputs/outputs must follow defined types
- **Follow existing structure** - respect current file/module layout and naming conventions
- **Prefer reuse** - use existing utilities instead of reimplementing logic

### MCP Tool Development
- Each tool handler uses `mode`-based dispatch - always validate `mode` before branching
- Tool responses must follow MCP JSON-RPC spec with `success`, `message`, `error`, `data` fields
- Use `parameters` schema field for tools (not `inputSchema` except for legacy compatibility)
- On errors, return `data: {}` and use shared `errorResponse()` helper

### Code Language Standards
- **All source code in English** - comments, variables, error messages, docstrings
- **When modifying files**: Convert any encountered Japanese text to English
- **Exception**: User-facing content specifically for Japanese users

## ✅ Critical Operations

### Server Management
**Never use `run_in_terminal` for server management** - always use:
```bash
# Recommended method
./scripts/mcp_server_daemon.sh [start|stop|restart|status]

# Or VS Code tasks via Command Palette: "Tasks: Run Task"
```

### Terminal Bug Workaround
- **Issue**: `run_in_terminal` may not display output properly
- **Solution**: Use output redirection: `command 2>&1 | tee .copilot-temp/{task}-00001.log`
- **Verification**: Check log files in `.copilot-temp/` if output missing

## ✅ Associative Memory Integration

**Use MCP associative memory tools actively for development workflow:**

### Core Operations
- `#mcp_assocmemory_memory_store` - Store insights, solutions, and learnings
- `#mcp_assocmemory_memory_search` - Find related knowledge using semantic search
- `#mcp_assocmemory_memory_discover_associations` - Explore connections between concepts

### Recommended Usage Patterns
```bash
# Before feature work
#mcp_assocmemory_memory_search query="similar implementation patterns"

# During development  
#mcp_assocmemory_memory_store scope="work/decisions" content="architectural decision rationale"

# After completion
#mcp_assocmemory_memory_store scope="work/lessons" content="implementation gotchas and solutions"
```

### Scope Organization
```
work/
  ├── architecture/ - Design decisions and patterns
  ├── debugging/ - Problem investigation and solutions
  └── lessons/ - Implementation learnings

learning/
  ├── [technology]/ - Technical knowledge
  └── best-practices/ - Proven approaches
```

## ✅ Current Sprint Priorities

**High Priority**: Japanese search bug fix, registration response optimization  
**Medium Priority**: Tool consolidation, enhanced search UX  
**Low Priority**: Diversified search algorithm, advanced session management

**Note**: Full project status and detailed development tasks are stored in associative memory. Use `#mcp_assocmemory_memory_search` to find current progress and next priorities.

## ✅ Additional Resources

**Detailed guidelines moved to organized documentation:**
- **Developer workflow**: `development/workflow/DEVELOPER_GUIDELINES.md`
- **Architecture patterns**: `development/architecture/` directory
- **Technical considerations**: `development/technical/` directory
- **Project specifications**: `development/specifications/` directory

---

## 📝 User Requests Section

**This section is reserved for user-specific requests and temporary instructions.**

*Users can add project-specific guidance, temporary development focus areas, or special requirements here. This section should be regularly reviewed and cleaned up during maintenance cycles.*

<!-- User requests go here -->

---

## 🔄 Maintenance Schedule

**Regular maintenance tasks:**
- **Weekly**: Review and update sprint priorities, clean up user requests section
- **Monthly**: Move detailed content to specialized documentation, update resource links
- **Quarterly**: Review effectiveness of instructions, update based on GitHub best practices

**For maintenance questions or updates, store decisions in associative memory using scope `work/documentation/copilot-instructions`**
