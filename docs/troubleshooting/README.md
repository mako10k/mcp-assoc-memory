# Troubleshooting Guide - MCP Associative Memory Server

## 🚨 Common Issues and Solutions

### Server Startup Issues

#### Problem: Server Won't Start
```bash
Error: "Address already in use: port 8000"
```

**Solutions:**
1. **Check for existing process:**
   ```bash
   lsof -i :8000
   # Kill existing process if found
   kill -9 [PID]
   ```

2. **Use alternative port:**
   ```bash
   # Modify config or set environment variable
   export MCP_PORT=8001
   python -m mcp_assoc_memory
   ```

3. **Use VS Code task:**
   ```
   Ctrl+Shift+P → "Tasks: Run Task" → "MCP Server: Restart"
   ```

#### Problem: Import Error on Startup
```bash
ImportError: No module named 'sentence_transformers'
```

**Solutions:**
1. **Install missing dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Verify Python version:**
   ```bash
   python --version  # Should be 3.8+
   ```

3. **Check virtual environment:**
   ```bash
   which python
   pip list | grep sentence-transformers
   ```

#### Problem: Database Initialization Failure
```bash
Error: "Could not initialize ChromaDB"
```

**Solutions:**
1. **Check data directory permissions:**
   ```bash
   ls -la data/
   chmod 755 data/
   ```

2. **Clear corrupted database:**
   ```bash
   rm -rf data/chroma_db/
   # Server will recreate on next start
   ```

3. **Use simple persistence fallback:**
   ```bash
   # Temporarily disable ChromaDB in config
   # Server will use JSON persistence
   ```

---

### Memory Operations Issues

#### Problem: Empty Search Results
```
Search returns no results despite knowing relevant memories exist
```

**Diagnosis:**
```instructions
List my recent memories to verify they exist
```

**Solutions:**
1. **Lower similarity threshold:**
   ```instructions
   Search for [topic] with similarity threshold 0.1
   ```

2. **Try broader search terms:**
   ```
   Instead of: "React useEffect dependency array"
   Try: "React hooks" or "useEffect"
   ```

3. **Check scope restrictions:**
   ```instructions
   Search for [topic] across all scopes
   ```

4. **Verify embedding service:**
   ```bash
   # Check server logs for embedding errors
   tail -f server.log | grep -i embedding
   ```

#### Problem: Cannot Store Memories
```
Memory storage fails silently or returns errors
```

**Diagnosis:**
```instructions
Store this simple test: "Test memory storage"
```

**Solutions:**
1. **Check server connection:**
   ```instructions
   Try: List recent memories
   ```

2. **Verify disk space:**
   ```bash
   df -h data/
   ```

3. **Check database lock:**
   ```bash
   lsof data/memory.db
   ```

4. **Reset to simple persistence:**
   ```bash
   # Backup current data
   cp data/memories.json data/memories_backup.json
   # Restart server - will reinitialize
   ```

#### Problem: Duplicate Detection Too Aggressive
```
System incorrectly identifies different memories as duplicates
```

**Solutions:**
1. **Lower similarity threshold:**
   ```instructions
   Store memory with similarity threshold 0.8 instead of 0.95
   ```

2. **Allow duplicates temporarily:**
   ```instructions
   Store memory with allow_duplicates=true
   ```

3. **Use different scopes:**
   ```instructions
   Store in different scope to avoid cross-scope duplicate detection
   ```

---

### Search and Discovery Issues

#### Problem: Poor Search Quality
```
Search results seem irrelevant or low quality
```

**Diagnosis Steps:**
1. **Check similarity scores:**
   ```instructions
   Search returns similarity scores - look for patterns
   ```

2. **Test with known content:**
   ```instructions
   Search for exact phrases from stored memories
   ```

**Solutions:**
1. **Adjust search strategy:**
   ```
   # Instead of exact phrases, use conceptual terms
   Good: "async programming patterns"
   Poor: "async function with await keyword"
   ```

2. **Increase result limit:**
   ```instructions
   Search with limit=20 to see more potential results
   ```

3. **Use association discovery:**
   ```instructions
   If you find one relevant memory, use discover_associations to find related ones
   ```

#### Problem: No Associations Found
```
Association discovery returns empty or poor results
```

**Solutions:**
1. **Check memory content quality:**
   - Ensure memories have rich, descriptive content
   - Avoid very short or cryptic memories

2. **Increase association limit:**
   ```instructions
   Discover associations with limit=20 and similarity_threshold=0.1
   ```

3. **Build association foundation:**
   ```instructions
   Store related memories in same session to build connections
   ```

---

### Organization and Management Issues

#### Problem: Scope Confusion
```
Memories end up in wrong scopes or scope hierarchy is messy
```

**Solutions:**
1. **Use scope suggestions:**
   ```instructions
   Get scope suggestion for this content before storing
   ```

2. **Reorganize with memory_move:**
   ```instructions
   Move these memories to better organized scope
   ```

3. **Review scope hierarchy:**
   ```instructions
   List all scopes to see current organization
   ```

4. **Establish naming conventions:**
   ```
   work/projects/[project-name]/[component]
   learning/[technology]/[subtopic]
   personal/[category]
   ```

#### Problem: Too Many Memories to Navigate
```
Memory collection becomes overwhelming
```

**Solutions:**
1. **Use scoped searching:**
   ```instructions
   Search within specific scope: work/current-project
   ```

2. **Regular cleanup:**
   ```instructions
   List memories in test/ scope for potential cleanup
   ```

3. **Session management:**
   ```instructions
   Clean up old session memories older than 30 days
   ```

4. **Export and archive:**
   ```instructions
   Export completed project memories before starting new ones
   ```

---

### Export/Import Issues

#### Problem: Export Fails
```
Memory export returns errors or creates empty files
```

**Diagnosis:**
```instructions
Try exporting small scope first: test
```

**Solutions:**
1. **Check file permissions:**
   ```bash
   ls -la data/exports/
   chmod 755 data/exports/
   ```

2. **Try direct data export:**
   ```instructions
   Export without file_path to get data directly
   ```

3. **Export smaller chunks:**
   ```instructions
   Export specific scopes instead of all memories
   ```

#### Problem: Import Fails or Corrupts Data
```
Import operation fails or creates inconsistent state
```

**Solutions:**
1. **Validate import data:**
   ```instructions
   Import with validate_data=true to check structure
   ```

2. **Use safe merge strategy:**
   ```instructions
   Import with merge_strategy="skip_duplicates"
   ```

3. **Test with small dataset:**
   ```bash
   # Create small test export first
   # Verify import works before importing large datasets
   ```

4. **Backup before import:**
   ```instructions
   Export current memories before importing new ones
   ```

---

### Performance Issues

#### Problem: Slow Search Response
```
Search operations take too long to complete
```

**Solutions:**
1. **Reduce search scope:**
   ```instructions
   Search within specific scope instead of all memories
   ```

2. **Lower result limit:**
   ```instructions
   Search with limit=5 instead of default 10
   ```

3. **Check embedding service:**
   ```bash
   # Monitor CPU/memory usage during search
   htop
   ```

4. **Restart server periodically:**
   ```bash
   # VS Code task or manual restart
   python -m mcp_assoc_memory
   ```

#### Problem: High Memory Usage
```
Server consumes excessive RAM
```

**Solutions:**
1. **Check memory count:**
   ```instructions
   List total memory count across all scopes
   ```

2. **Clean up old sessions:**
   ```instructions
   Clean up session memories older than 7 days
   ```

3. **Export and remove old data:**
   ```instructions
   Export old project memories, then delete them
   ```

4. **Restart server to clear caches:**
   ```bash
   # Fresh start clears embedding caches
   ```

---

### GitHub Copilot Integration Issues

#### Problem: Copilot Can't Access MCP Tools
```
Copilot responds with "I don't have access to memory tools"
```

**Solutions:**
1. **Check MCP server status:**
   ```bash
   curl http://localhost:8000/mcp/tools/list
   ```

2. **Verify VS Code MCP configuration:**
   ```json
   // .vscode/mcp.json should contain:
   {
     "servers": {
       "AssocMemory": {
         "url": "http://localhost:8000/mcp/"
       }
     }
   }
   ```

3. **Restart VS Code and server:**
   ```bash
   # Close VS Code, restart server, reopen VS Code
   ```

#### Problem: Tool Calls Fail
```
Copilot tries to use tools but gets errors
```

**Solutions:**
1. **Check tool syntax:**
   ```
   # Ensure tool calls use proper JSON structure
   # Check API reference for correct parameters
   ```

2. **Verify server logs:**
   ```bash
   tail -f server.log | grep -i error
   ```

3. **Test with simple operations:**
   ```instructions
   Start with basic operations like "store a test memory"
   ```

---

### Data Recovery and Backup

#### Problem: Data Loss or Corruption
```
Memories are missing or database appears corrupted
```

**Recovery Steps:**
1. **Check backup files:**
   ```bash
   ls -la data/exports/
   # Look for recent export files
   ```

2. **Check simple persistence backup:**
   ```bash
   ls -la data/memories.json
   # May contain recent data if ChromaDB failed
   ```

3. **Recover from recent export:**
   ```instructions
   Import from most recent export file
   ```

4. **Gradual database rebuild:**
   ```bash
   # Remove corrupted database
   rm -rf data/chroma_db/
   # Restart server
   # Re-import from backups
   ```

---

## 🔧 Diagnostic Commands

### Health Check Sequence
```bash
# 1. Server status
curl -s http://localhost:8000/mcp/tools/list | head -10

# 2. Data directory check
ls -la data/

# 3. Memory count check
```
```instructions
List total memories across all scopes
```

# 4. Simple operation test
```instructions
Store this test: "Diagnostic test memory"
```

# 5. Search test
```instructions
Search for "diagnostic test"
```

### System Information
```bash
# Python environment
python --version
pip list | grep -E "(sentence|chroma|fastapi)"

# System resources
free -h
df -h data/

# Network connectivity
netstat -tlnp | grep 8000
```

---

## 📊 Monitoring and Maintenance

### Regular Health Checks

#### Weekly (5 minutes)
- Verify server startup
- Test basic memory operations
- Check disk usage
- Review error logs

#### Monthly (15 minutes)
- Export important memories
- Clean up test/temporary data
- Review scope organization
- Update dependencies if needed

### Preventive Measures

1. **Regular exports:**
   ```instructions
   Weekly: Export work memories
   Monthly: Export all memories
   ```

2. **Scope hygiene:**
   ```instructions
   Monthly: Review and reorganize scopes
   ```

3. **Session cleanup:**
   ```instructions
   Weekly: Clean up old session data
   ```

4. **Server maintenance:**
   ```bash
   # Monthly restart for fresh state
   # Clear logs if they become too large
   ```

### Log Analysis
```bash
# Check for common error patterns
grep -i error server.log | tail -20
grep -i "embedding" server.log | tail -10
grep -i "chroma" server.log | tail -10

# Monitor performance
grep -i "slow" server.log
grep -i "timeout" server.log
```

---

## 🆘 Emergency Recovery

### Complete System Reset
```bash
# 1. Backup current state
cp -r data/ data_backup_$(date +%Y%m%d_%H%M%S)/

# 2. Export what you can
```
```instructions
Export all memories to emergency backup
```

# 3. Reset database
```bash
rm -rf data/chroma_db/
rm -f data/memory.db

# 4. Restart server
python -m mcp_assoc_memory

# 5. Re-import critical data
```
```instructions
Import from emergency backup with skip_duplicates strategy
```

### Partial Recovery Strategies

#### Database Corruption
1. Try simple persistence mode
2. Export recoverable data
3. Rebuild with clean database
4. Re-import preserved data

#### Embedding Service Issues
1. Restart server to reload models
2. Clear embedding cache
3. Test with simple content
4. Gradually restore complex operations

---

**For issues not covered here, check the [API Reference](../api-reference/README.md) for detailed parameter options, or create an issue in the project repository with relevant log excerpts and system information.**

---

### Configuration Issues

#### Problem: Pydantic Validation Errors
```bash
CRITICAL: 1 validation error for Settings
log_level
  Input should be 'DEBUG', 'INFO', 'WARNING', 'ERROR' or 'CRITICAL' [type=literal_error, input_value='info', input_type=str]
```

**Root Cause:** Log level values must be uppercase.

**Solutions:**
1. **Check environment variables:**
   ```bash
   echo $LOG_LEVEL
   echo $MCP_LOG_LEVEL
   # Should be uppercase: INFO, DEBUG, etc.
   ```

2. **Update VS Code MCP configuration:**
   ```json
   // .vscode/mcp.json
   {
     "servers": {
       "AssocMemory": {
         "env": {
           "LOG_LEVEL": "INFO",        // ✅ Correct: uppercase
           "MCP_LOG_LEVEL": "INFO"     // ✅ Correct: uppercase
         }
       }
     }
   }
   ```

3. **Check configuration file:**
   ```json
   // config.json
   {
     "log_level": "INFO"  // ✅ Correct: uppercase
   }
   ```

#### Problem: OpenAI API Key Format Errors
```bash
CRITICAL: Invalid OpenAI API key format: Your API K... (must start with 'sk-' or 'sk-proj-')
```

**Solutions:**
1. **Verify API key format:**
   ```bash
   # Correct formats
   export OPENAI_API_KEY="sk-proj-..."  # New format
   export OPENAI_API_KEY="sk-..."       # Legacy format
   
   # Check current value (masked)
   echo $OPENAI_API_KEY | cut -c1-10
   ```

2. **Check configuration file expansion:**
   ```json
   // config.json
   {
     "embedding": {
       "api_key": "${OPENAI_API_KEY}"  // Environment variable expansion
     }
   }
   ```

3. **Test environment variable:**
   ```bash
   python3 -c "import os; print('Key set:', bool(os.getenv('OPENAI_API_KEY')))"
   ```

#### Problem: Configuration File Not Found
```bash
WARNING: Failed to load configuration file: [Errno 2] No such file or directory: 'config.json'
```

**Solutions:**
1. **Create configuration file:**
   ```bash
   cp config.example.json config.json
   # Edit config.json with your settings
   ```

2. **Check file location:**
   ```bash
   ls -la config.json
   # Must be in server working directory
   ```

3. **Use absolute path:**
   ```bash
   python -m mcp_assoc_memory.server --config /absolute/path/to/config.json
   ```

#### Problem: Environment Variables Not Applied
```bash
# Set LOG_LEVEL=DEBUG but server still uses INFO
```

**Diagnosis:**
1. **Check variable precedence:**
   ```bash
   # Priority: CLI > Environment > File > Defaults
   echo "ENV LOG_LEVEL: $LOG_LEVEL"
   grep log_level config.json
   ```

2. **Test configuration loading:**
   ```python
   import os
   os.environ['LOG_LEVEL'] = 'DEBUG'
   from mcp_assoc_memory.config import ConfigurationManager
   manager = ConfigurationManager()
   config = manager.load_configuration('config.json')
   print(f"Final log_level: {config.log_level}")
   ```

**Solutions:**
1. **Verify environment variable names:**
   ```bash
   # Supported variables (see docs/CONFIGURATION.md)
   export LOG_LEVEL=DEBUG
   export MCP_LOG_LEVEL=DEBUG
   export EMBEDDING_PROVIDER=local
   ```

2. **Check VS Code environment:**
   ```json
   // .vscode/mcp.json
   {
     "servers": {
       "AssocMemory": {
         "env": {
           "PYTHONPATH": "${workspaceFolder}/src",
           "LOG_LEVEL": "DEBUG"  // Ensure this is set
         }
       }
     }
   }
   ```

#### Problem: Invalid Configuration Values
```bash
ValueError: Invalid provider 'invalid_provider'. Must be 'openai', 'local', or 'sentence_transformer'
```

**Solutions:**
1. **Check supported values:**
   ```json
   // Valid embedding providers
   "provider": "openai"              // OpenAI embeddings
   "provider": "local"               // Local SentenceTransformers
   "provider": "sentence_transformer" // Alias for local
   ```

2. **Validate transport settings:**
   ```json
   // Valid transport configuration
   "transport": {
     "stdio_enabled": true,   // For VS Code/MCP clients
     "http_enabled": false,   // For HTTP API
     "sse_enabled": false     // For Server-Sent Events
   }
   ```

3. **Test configuration:**
   ```bash
   python3 -c "
   from mcp_assoc_memory.config import ConfigurationManager
   manager = ConfigurationManager()
   config = manager.load_configuration('config.json')
   print('✅ Configuration valid')
   "
   ```

---
