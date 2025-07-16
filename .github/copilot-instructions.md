## ✅ Context Preservation and Forgetting Mitigation

- Periodically record conversation history and key context using `#mcp_assocmemory_memory_store` to associative memory.
- Minimize use of Copilot's summarization features to avoid context loss.
- Important conversation history must also be recorded to a file (see file design in project docs).
- After summarization or context loss, always refer to associative memory and restore context only after explicit user instruction.

## ✅ LLM Memory Limitation Awareness

**FUNDAMENTAL PRINCIPLE: LLM "apologies" and "reflections" are meaningless without persistent storage**

### Core Rules:
1. **No Meaningless Apologies**: LLM apologies are human-style language that creates false impression of learning
2. **Context Expiration Reality**: All "promises to remember" are forgotten when context expires
3. **Persistent Storage Requirement**: Every error pattern MUST be recorded in associative memory for future reference
4. **Action Over Words**: Focus on permanent system improvements, not temporary promises

### Required Response Pattern for Violations:
1. **NEVER** just apologize or promise improvement
2. **IMMEDIATELY** record violation patterns in `#mcp_assocmemory_memory_store`
3. **CREATE** searchable, persistent documentation of errors
4. **STORE** specific behavioral rules that survive context loss

### User Expectation:
- Apologies without persistent storage are "meaningless"
- Each violation must update the permanent rule system
- System-level improvements required, not human-style responses


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
- **CRITICAL: Apply Contract Programming with assert statements for all preconditions**
- **CRITICAL: NEVER implement silent fallbacks - always consult user first**
- **CRITICAL: Fail-fast on contract violations - never continue with invalid state**
- Never make independent decisions on branching issues; always consult user
- All implementations must follow the official MCP SDK and its conventions
- All Copilot/AI assistants must always refer to this file as the primary source of operational rules and project instructions
- No action should be taken that contradicts this file
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
- **CRITICAL: Apply Contract Programming - validate all preconditions with assert statements**
- **CRITICAL: Fail-fast on contract violations - never continue with invalid state**
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
# Server testing and validation
python3 -m mcp_assoc_memory.server --config config.json --test

# VS Code Tasks (preferred method)
# Use "Tasks: Run Task" → "Test: Run Unit Tests"
# Use "Tasks: Run Task" → "Lint: Smart Lint (All)"

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

### Contract Programming & Error Handling Rules (CRITICAL)
**MANDATORY CONTRACT PROGRAMMING PRINCIPLES:**
- **Design by Contract**: All functions must validate preconditions with assert statements
- **Fail-Fast Execution**: Stop immediately when contracts are violated
- **State Consistency**: Ensure object states match expected contracts
- **Transparent Operations**: All operations must be visible and auditable

**ABSOLUTE PROHIBITION OF SILENT FALLBACKS:**
- NEVER implement fallbacks without explicit user consultation
- NEVER hide errors behind automatic fallback mechanisms (e.g., `except Exception: pass`)
- NEVER make arbitrary judgment calls that obscure root causes
- NEVER use hasattr() checks with default values as silent fallbacks

**Contract Programming Implementation Patterns:**
```python
# ✅ Correct: Contract Programming with Assertions
def process_data(memory_manager, ctx):
    # Precondition validation
    assert memory_manager is not None, "Memory manager is required"
    assert hasattr(memory_manager, 'metadata_store'), f"Missing metadata_store: {type(memory_manager)}"
    assert ctx is not None, "Context object is required for operations"
    
    # State consistency checks
    if is_initialized():
        manager = get_manager()
        assert manager is not None, "Initialized but manager is None - state inconsistency"
        return manager

# ❌ Forbidden: Silent Fallback Patterns
def bad_process_data(memory_manager, ctx):
    try:
        if memory_manager and hasattr(memory_manager, 'metadata_store'):
            return memory_manager.process()
    except Exception:
        pass  # FORBIDDEN: Silent error hiding
    
    # FORBIDDEN: Default fallback without transparency
    return default_value if memory_manager else fallback_value
```

**Distinction Between Appropriate vs Forbidden Fallbacks:**
- ✅ **Appropriate Fallbacks**: Explicit, transparent, user-approved with clear logging
- ✅ **Contract-Compliant Fallbacks**: Assert-validated, logged, with full context
- ❌ **Forbidden Fallbacks**: Silent error hiding implemented by AI without user knowledge
- ❌ **Contract Violations**: hasattr() checks, try/except/pass, default value substitutions

**Required Contract Programming Actions:**
- Always validate preconditions with assert statements
- Always fail fast and log errors with full context
- Always ensure state consistency between related components
- When fallback appears necessary, ALWAYS consult user first
- If implementing fallback, ensure complete transparency and visibility
- All contract violations must be stored in associative memory for learning

**Contract Programming Examples by Component:**
- **Memory Management**: Assert memory_manager existence, validate store operations
- **Context Objects**: Assert ctx availability, validate required methods (info, error)
- **Data Structures**: Assert required fields, validate data integrity
- **Initialization States**: Assert consistency between flags and actual objects
- See detailed examples: [docs/copilot-error-handling.md](../docs/copilot-error-handling.md)

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
- For testing and mocking: see [docs/copilot-testing-mocking.md](../docs/copilot-testing-mocking.md)

Refer to each detail file only when the corresponding context or user request requires it. Do not load all detail files by default.

## ✅ Copilot Role and Environmental Integrity

### Role Limitations as Co-pilot
- **Primary Function**: Execute user instructions accurately
- **Forbidden Actions**: Replace user instructions with AI-determined alternatives
- **When Instructions Fail**: Report failure and consult user, never implement unauthorized alternatives
- **Decision Authority**: Zero independent authority on technical decisions

### Environment Modification Restrictions
- **NEVER modify configuration files without explicit user request**
- **NEVER add tasks, settings, or configurations autonomously**
- **ALWAYS restore unauthorized changes immediately when discovered**
- **Example Violations**: Adding VS Code tasks, modifying .vscode/ files, changing project configuration

### Transparency Requirements
- All actions must be visible and reportable to user
- No "helpful" background modifications
- All changes must serve explicit user requests only
- When in doubt about permissions, always ask user first

### Testing and Mocking Guidelines
**Proper Mocking Layer Strategy:**
- Mock only external dependencies (API calls, file I/O, network)
- Keep business logic testable (validation, error handling, service selection)
- Never mock too high-level - test the actual implementation logic
- Example: Mock `openai.AsyncOpenAI` client, not entire `EmbeddingService`

**Forbidden High-Level Mocking:**
- Mocking entire service classes prevents testing business logic
- Switching to MockService based on test mode defeats the purpose
- Business logic (config validation, error handling) must be tested

**Correct Approach:**
- Test mode detection at dependency injection level only
- Mock external I/O operations within the same class
- Maintain full test coverage of internal logic

