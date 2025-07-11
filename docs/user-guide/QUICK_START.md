# MCP Associative Memory Server - Quick Start Guide

## 🚀 Get Started in 5 Minutes

The MCP Associative Memory Server is an intelligent memory system that helps you store, search, and discover connections between your thoughts, notes, and knowledge. This guide will get you up and running quickly.

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
Use GitHub Copilot to store a memory:

```instructions
Store this thought: "FastAPI is excellent for building APIs because of its automatic validation and documentation generation"
```

### Search for Memories
```instructions
Find memories about API development
```

### Discover Related Memories
```instructions
Show me memories related to web frameworks
```

## 🎯 Essential Commands (GitHub Copilot)

| What You Want | Say to Copilot |
|---------------|----------------|
| Store knowledge | "Remember this: [your content]" |
| Find related info | "Find memories about [topic]" |
| Explore connections | "Show me what's related to [concept]" |
| Organize memories | "Move these memories to [category]" |
| Export/backup | "Export my memories" |
| Session work | "Create a session for [project]" |
| Diversified search | "Find diverse memories about [topic]" |

## 🗂️ Understanding Scopes

Memories are organized in hierarchical scopes:

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

## 🏃‍♂️ Session Management

### Working Sessions
Create isolated workspaces for temporary work:

```instructions
Create a session for debugging the API issue
```

### Session Cleanup
```instructions
Clean up sessions older than 7 days
```

Sessions are perfect for:
- Project-specific debugging
- Temporary research
- Meeting notes that expire
- Experimental ideas

## 🔍 Search Tips

### Effective Search Queries
- **Specific**: "React component lifecycle methods"
- **Conceptual**: "error handling patterns"
- **Problem-based**: "database connection issues"

### Advanced Search Options

#### Diversified Search
For creative exploration and avoiding echo chambers:
```instructions
Find diverse memories about machine learning optimization
```

Benefits:
- Prevents redundant similar results
- Promotes creative thinking
- Discovers unexpected connections

#### Focused Search
For specific information retrieval:
```instructions
Find memories about Python async patterns
```

### Understanding Results
- Results include similarity scores (0.0-1.0)
- Higher scores = more relevant
- Threshold of 0.1 filters obvious noise
- GitHub Copilot intelligently interprets relevance

## 🧠 Association Discovery

The system automatically finds connections between memories:

```instructions
# After storing several programming memories
Discover associations for this memory about React hooks
```

This reveals unexpected connections and helps with:
- Creative problem solving
- Knowledge synthesis  
- Learning reinforcement

## 📤 Export & Backup

### Quick Export
```instructions
Export my work memories to a file
```

### Cross-Environment Sync
```instructions
Export all memories for backup
```

### Import from Backup
```instructions
Import memories from backup file
```

### Advanced Export Options
- **Scope-specific**: Export only work or learning memories
- **Compressed**: Large datasets with gzip compression
- **Direct transfer**: Export data for immediate import elsewhere

Files are saved to `data/exports/` by default.

### Merge Strategies
When importing, choose how to handle duplicates:
- **Skip duplicates** (default): Keep existing, ignore imports
- **Overwrite**: Replace existing with imported versions
- **Create versions**: Preserve both local and imported

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
