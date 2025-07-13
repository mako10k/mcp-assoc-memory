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
- **MANDATORY: Run mypy before any modification** - Type checking prevents basic errors like import/class mismatches

### MCP Tool Development
- Each tool handler uses `mode`-based dispatch - always validate `mode` before branching
- Tool responses must follow MCP JSON-RPC spec with `success`, `message`, `error`, `data` fields
- Use `parameters` schema field for tools (not `inputSchema` except for legacy compatibility)
- On errors, return `data: {}` and use shared `errorResponse()` helper

### 🚨 **CRITICAL ERROR HANDLING MANDATE** 🚨
**ABSOLUTE PROHIBITION: No fallback mechanisms or error avoidance patterns**
- **NEVER implement fallback storage, fallback services, or alternative paths when core functionality fails**
- **ALWAYS fail fast with clear error messages when None is returned or core operations fail**
- **MANDATORY: Early None checks with immediate exception raising and detailed logging**
- **REQUIRED: All errors must be properly logged with full context and returned to client**
- **FORBIDDEN: Hiding problems behind try/except blocks without addressing root cause**
- **PRINCIPLE: Surface problems immediately to force proper diagnosis and fix**

Example of CORRECT error handling:
```python
result = await core_operation()
if result is None:
    error_msg = "core_operation returned None - indicates fundamental issue"
    logger.error(error_msg, extra={"operation": "core_operation", "context": context})
    raise RuntimeError(error_msg)
```

Example of FORBIDDEN pattern:
```python
try:
    result = await advanced_operation()
except Exception:
    result = fallback_operation()  # FORBIDDEN - hides the real problem
```

### 🚨 **TIMEOUT HANDLING MANDATE** 🚨
**ABSOLUTE PROHIBITION: Avoiding investigation due to timeouts**
- **NEVER simplify tests or change approaches solely because of timeouts**
- **ALWAYS extend timeout values for time-consuming operations that need investigation**
- **MANDATORY: Investigate the root cause of why operations take long or hang**
- **REQUIRED: Use appropriate timeout values (30-60s for complex operations, 120s+ for initialization)**
- **FORBIDDEN: Switching to "simpler tests" to avoid timeout issues**
- **PRINCIPLE: Time-consuming operations often reveal the real problems - investigate them fully**

Example of CORRECT timeout handling:
```python
# Extend timeout for complex initialization
result = await shell_execute(command, timeout_seconds=120)
# If it times out, investigate WHY it hangs, don't simplify the test
```

Example of FORBIDDEN pattern:
```python
# This times out, so let's try something simpler
try:
    complex_test(timeout=30)  # Times out
except TimeoutError:
    simple_test()  # FORBIDDEN - avoids the real issue
```

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

### � **Core Tools (Production API)**
- `#mcp_assocmemory_memory_search` - Comprehensive search (standard/diversified modes)
- `#mcp_assocmemory_memory_manage` - CRUD operations (get/update/delete)
- `#mcp_assocmemory_memory_sync` - Data synchronization (import/export)
- `#mcp_assocmemory_memory_store` - Store insights, solutions, and learnings
- `#mcp_assocmemory_memory_discover_associations` - Explore connections between concepts

### Recommended Usage Patterns
```bash
# Before feature work
#mcp_assocmemory_memory_search mode="standard" query="similar implementation patterns"

# During development  
#mcp_assocmemory_memory_store scope="work/decisions" content="architectural decision rationale"

# After completion
#mcp_assocmemory_memory_store scope="work/lessons" content="implementation gotchas and solutions"

# Creative exploration
#mcp_assocmemory_memory_search mode="diversified" query="creative solutions for testing"

# Data management
#mcp_assocmemory_memory_sync operation="export" scope="work" file_path="backup/sprint-2-work.json"
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

### 🔗 **Modern API Benefits**
- **Intuitive naming**: Natural, memorable tool names
- **Consistent patterns**: Unified parameter structures  
- **Reduced complexity**: Single interface for multi-mode operations
- **Production ready**: Clean, focused API surface

## ✅ Current Sprint Priorities

**🎉 API Modernization: COMPLETED**  
**🔄 Current Focus**: Production deployment and user onboarding  
**📅 Status**: 100% complete - API is production-ready

### ✅ **Completed**
- **API Modernization**: Clean, intuitive tool naming and interfaces
- **Legacy Removal**: All old/redundant tools removed for clarity
- **Documentation**: Complete update of all user-facing documentation

### 🚨 **High Priority**
- **Performance Optimization**: Query response time improvements
- **Enhanced Error Handling**: Better user feedback for edge cases

### 🟡 **Medium Priority**
- **Enhanced Search UX**: Scope suggestions, search statistics, and result metadata
- **Comprehensive Testing**: All tools integration testing

### 🟢 **Low Priority (Future Sprints)**
- **Diversified Search Algorithm**: Advanced diversity-based result filtering
- **Advanced Session Management**: Session templates, inheritance, and automatic cleanup

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
`run_in_terminal` ツールより MCPの`*_shell_execute` ツールを使ってください。
セキュリティガードに引っかかる場合や長時間の実行や端末実行が必要な場合は MCPの`*_terminal_create` ツールを使ってください


---

## � Asynchronous Backlog Management

**Workflow**: Efficient, non-blocking backlog management for continuous development

### For Users
1. **Add items**: Write new backlog items to `.github/copilot-backlog.md` using the specified format
2. **Continue working**: No need to wait for Copilot processing
3. **Review results**: Check associative memory for processed items using `#mcp_assocmemory_memory_search`

### For Copilot
1. **Check backlog**: Periodically read `.github/copilot-backlog.md` for new items
2. **Process items**: Store valid items in associative memory using scope `work/backlog/{priority}`
3. **Clean up**: Remove processed items from the backlog file
4. **Update sprint**: Integrate high-priority items into current sprint planning

### Benefits
- **Non-blocking**: Users can add items without interrupting current work
- **Organized**: All backlog items centralized in associative memory
- **Trackable**: Full history and relationships maintained through semantic associations
- **Flexible**: Supports urgent items and long-term planning

---

## �🔄 Maintenance Schedule

**Regular maintenance tasks:**
- **Weekly**: Review and update sprint priorities, process `.github/copilot-backlog.md`, clean up user requests section
- **Monthly**: Move detailed content to specialized documentation, update resource links, review backlog organization
- **Quarterly**: Review effectiveness of instructions, update based on GitHub best practices, archive completed sprint data

**For maintenance questions or updates, store decisions in associative memory using scope `work/documentation/copilot-instructions`**
