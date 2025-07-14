# MCP Associative Memory Server Log Rotation Configuration

## Automatic Log Rotation

This project includes log rotation functionality to prevent log files from growing too large.

### Configuration

- **Maximum log size**: 10MB (configurable in `scripts/rotate_logs.sh`)
- **Maximum generations**: 3 (keeps current + 3 compressed backups)
- **Compression**: gzip (.gz format)

### Files Rotated

- `logs/mcp_server.log` - Main server log
- `logs/mcp_test_server.log` - Test server log (if exists)

### Manual Rotation

You can manually rotate logs using:

```bash
# Command line
./scripts/rotate_logs.sh

# VS Code Task
# Use Command Palette: "Tasks: Run Task" → "Logs: Rotate Log Files"
```

### Automatic Rotation

To set up automatic rotation, add a cron job:

```bash
# Edit crontab
crontab -e

# Add line to rotate logs daily at 2 AM
0 2 * * * /path/to/mcp-assoc-memory/scripts/rotate_logs.sh

# Or rotate when logs get large (check every hour)
0 * * * * /path/to/mcp-assoc-memory/scripts/rotate_logs.sh
```

### Log Files After Rotation

```
logs/
├── mcp_server.log          # Current log (active)
├── mcp_server.log.1.gz     # Previous log (compressed)
├── mcp_server.log.2.gz     # Second previous log
└── mcp_server.log.3.gz     # Third previous log (oldest kept)
```

### Benefits

1. **Disk Space Management**: Prevents logs from consuming excessive disk space
2. **Performance**: Smaller active log files improve I/O performance
3. **Debugging**: Maintains history while keeping recent logs accessible
4. **Automation**: Set-and-forget log management

### Viewing Compressed Logs

```bash
# View compressed log content
zcat logs/mcp_server.log.1.gz | head -20

# Search in compressed logs
zgrep "ERROR" logs/mcp_server.log.*.gz

# Extract specific compressed log
gunzip -c logs/mcp_server.log.1.gz > /tmp/old_server.log
```
