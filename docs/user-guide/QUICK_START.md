# MCP Associative Memory Server - Quick Start Guide (2025)

## 🚀 Get Started in 5 Minutes

The MCP Associative Memory Server is an intelligent memory system that helps you store, search, and discover connections between your thoughts, notes, and knowledge. This guide reflects the **2025 production API** with 10 powerful tools.

## 🧪 Production Ready
- **74/74 tests passing** (100% success rate)
- **Complete CI/CD pipeline** with security and quality gates
- **Optimized performance** with parallel operations and connection pooling

## 📋 Prerequisites

- Python 3.8+
- VS Code with GitHub Copilot (recommended)
- Basic familiarity with terminal/command line

## ⚡ Quick Setup

### 1. Install Dependencies
```bash
cd /path/to/mcp-assoc-memory
pip install -r requirements.txt
```

### 2. Start the Server
```bash
# Option A: Using VS Code Task (recommended)
Ctrl+Shift+P → "Tasks: Run Task" → "MCP Server: Start"

# Option B: Manual start
python -m mcp_assoc_memory
```

### 3. Verify Server is Running
The server should start on `http://localhost:8000/mcp/` and you'll see:
```
FastMCP server running on http://localhost:8000
MCP endpoint available at: http://localhost:8000/mcp/
```

## 💭 Your First Memory

### Store Your First Memory
Use GitHub Copilot with the modern API:

```instructions
Use memory_store to save: "FastAPI is excellent for building APIs because of its automatic validation and documentation generation"
```

**Behind the scenes:**
```json
{
  "tool": "memory_store",
  "request": {
    "content": "FastAPI is excellent for building APIs...",
    "scope": "learning/web",
    "tags": ["fastapi", "api", "validation"],
    "auto_associate": true
  }
}
```

### Search for Memories
```instructions
Use memory_search to find memories about API development
```

**Behind the scenes:**
```json
{
  "tool": "memory_search", 
  "request": {
    "query": "API development",
    "mode": "standard",
    "limit": 10,
    "include_associations": true
  }
}
```

### Discover Related Memories
```instructions
Use memory_discover_associations to show me memories related to web frameworks
```

## 🎯 Essential Commands (GitHub Copilot)

### 🚀 **Modern API (10 Clean Tools - 2025)**
| What You Want | Tool Used | Say to Copilot |
|---------------|-----------|----------------|
| **Search** | `memory_search` | "Find memories about [topic]" *(standard/diversified modes)* |
| **Store knowledge** | `memory_store` | "Remember this: [your content]" |
| **Memory Management** | `memory_manage` | "Get/update/delete this memory" *(unified CRUD)* |
| **Data Sync** | `memory_sync` | "Export/import my memories" *(unified sync)* |
| **Explore connections** | `memory_discover_associations` | "Show me what's related to [concept]" |
| **Organize memories** | `memory_move` | "Move these memories to [category]" |
| **Browse all** | `memory_list_all` | "Show me all my memories" |
| **Organize scopes** | `scope_list` | "Show me my memory organization" |
| **Smart categorization** | `scope_suggest` | "Where should I store this content?" |
| **Session work** | `session_manage` | "Create/list/cleanup sessions" |

### 🎯 **Clean, Modern Design**
Our streamlined 2025 API provides:
- **Intuitive naming**: Natural tool names (memory_store, memory_search, etc.)
- **Unified operations**: Single tools for related functions (CRUD, sync, search modes)
- **Reduced complexity**: 10 focused tools covering all use cases
- **Production ready**: 74/74 tests passing with CI/CD pipeline
- **Performance optimized**: Parallel operations and connection pooling

## 🔍 Advanced Search Features

### Unified Search Modes
The `memory_search` tool supports multiple modes:

**Standard Search** (default - precise results):
```instructions
Find memories about Python async patterns
```

**Diversified Search** (creative exploration):
```instructions
Find diverse memories about machine learning - use diversified mode
```

### Search Benefits:
- **Semantic similarity**: Finds related concepts, not just keywords
- **Association discovery**: Reveals connections between memories
- **Diversity filtering**: Prevents redundant similar results
- **Creative thinking**: Breaks out of information silos
- **Intelligent ranking**: AI-powered relevance scoring

## 🗂️ Understanding Scopes

Memories are organized in hierarchical scopes for optimal organization:

```
work/
  ├── projects/[project-name]/
  ├── meetings/
  └── ideas/

learning/
  ├── programming/[language]/
  ├── frameworks/
  └── concepts/

personal/
  ├── goals/
  └── reflections/

session/
  ├── [project-name]/
  └── [temporary-work]/
```

### Scope Examples
- `work/projects/mcp-server` - Project-specific memories
- `learning/python/async` - Learning about Python async
- `personal/ideas` - Personal ideas and thoughts
- `session/debugging-session` - Temporary working session

### Smart Scope Suggestions
```instructions
Use scope_suggest to suggest where to store this content about React development
```

## 🏃‍♂️ Session Management

### Working Sessions
Create isolated workspaces for temporary work:

```instructions
Use session_manage to create a session for debugging the API issue
```

### Session Cleanup
```instructions
Use session_manage to clean up sessions older than 7 days
```

Sessions are perfect for:
- Project-specific debugging
- Temporary research
- Meeting notes that expire
- Experimental ideas

## 🧠 Association Discovery

The system automatically finds connections between memories:

```instructions
# After storing several programming memories
Use memory_discover_associations to discover associations for this memory about React hooks
```

This reveals unexpected connections and helps with:
- Creative problem solving
- Knowledge synthesis  
- Learning reinforcement

## 📤 Export & Backup

### 🚀 **Unified Data Sync (memory_sync)**
The modern unified sync tool handles both import and export operations:

#### Quick Export
```instructions
Use memory_sync to export my work memories to a file
```

#### Cross-Environment Sync
```instructions
Use memory_sync to export all memories for backup
```

#### Import from Backup
```instructions
Use memory_sync to import memories from backup file
```

### Advanced Export Options
- **Scope-specific**: Export only work or learning memories
- **Compressed**: Large datasets with gzip compression
- **Direct transfer**: Export data for immediate import elsewhere
- **Merge strategies**: Skip duplicates, overwrite, or create versions

Files are saved to `data/exports/` by default.

## 🆘 Quick Troubleshooting

### Server Won't Start
1. Check Python version: `python --version` (need 3.8+)
2. Install dependencies: `pip install -r requirements.txt`
3. Check port availability: `lsof -i :8000`

### Empty Search Results
- Lower your expectations for similarity
- Try broader search terms
- Check if memories exist: "List my recent memories"

### Memory Not Storing
- Verify server is running
- Check GitHub Copilot MCP connection
- Try simple test: "Store this: test memory"

## 🎉 You're Ready!

You now have a powerful associative memory system. Start by:

1. **Storing daily learnings** - capture insights as you work
2. **Searching before solving** - check if you've solved similar problems
3. **Exploring associations** - discover unexpected connections
4. **Regular exports** - backup your knowledge

## 📖 Next Steps

- [Best Practices Guide](BEST_PRACTICES.md) - Optimization tips
- [API Reference](../api-reference/README.md) - Complete tool documentation
- [Examples](../examples/README.md) - Real-world usage patterns
- [Troubleshooting](../troubleshooting/README.md) - Common issues

---

**Pro Tip**: Use the system daily for 1 week to build the habit. The more you use it, the more valuable it becomes!
