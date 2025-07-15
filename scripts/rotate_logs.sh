#!/bin/bash
# Log rotation script for MCP Associative Memory Server
# Keeps 3 generations of log files

LOG_DIR="./logs"
MAX_SIZE_MB=10  # Rotate when log exceeds 10MB
MAX_GENERATIONS=3

rotate_log_file() {
    local log_file="$1"
    local base_name=$(basename "$log_file" .log)
    local dir_name=$(dirname "$log_file")
    
    if [[ ! -f "$log_file" ]]; then
        echo "Log file $log_file does not exist"
        return 0
    fi
    
    # Check file size (in MB)
    local file_size_mb=$(du -m "$log_file" | cut -f1)
    
    if [[ $file_size_mb -lt $MAX_SIZE_MB ]]; then
        echo "Log file $log_file ($file_size_mb MB) is under threshold ($MAX_SIZE_MB MB)"
        return 0
    fi
    
    echo "Rotating log file $log_file ($file_size_mb MB)"
    
    # Remove oldest generation if it exists
    if [[ -f "$dir_name/${base_name}.log.$MAX_GENERATIONS.gz" ]]; then
        rm "$dir_name/${base_name}.log.$MAX_GENERATIONS.gz"
        echo "Removed oldest generation: ${base_name}.log.$MAX_GENERATIONS.gz"
    fi
    
    # Shift existing generations
    for ((i=MAX_GENERATIONS-1; i>=1; i--)); do
        if [[ -f "$dir_name/${base_name}.log.$i.gz" ]]; then
            mv "$dir_name/${base_name}.log.$i.gz" "$dir_name/${base_name}.log.$((i+1)).gz"
            echo "Moved ${base_name}.log.$i.gz -> ${base_name}.log.$((i+1)).gz"
        fi
    done
    
    # Compress and move current log to .1
    gzip -c "$log_file" > "$dir_name/${base_name}.log.1.gz"
    echo "Compressed current log to ${base_name}.log.1.gz"
    
    # Truncate current log file (keep it for continued logging)
    > "$log_file"
    echo "Truncated current log file $log_file"
    
    echo "Log rotation completed for $log_file"
}

main() {
    echo "=== Log Rotation Started $(date) ==="
    
    # Create logs directory if it doesn't exist
    mkdir -p "$LOG_DIR"
    
    # Rotate main server log
    rotate_log_file "$LOG_DIR/mcp_server.log"
    
    # Rotate test server log if it exists
    if [[ -f "$LOG_DIR/mcp_test_server.log" ]]; then
        rotate_log_file "$LOG_DIR/mcp_test_server.log"
    fi
    
    # Show current log status
    echo ""
    echo "Current log files:"
    ls -lh "$LOG_DIR"/*.log* 2>/dev/null || echo "No log files found"
    
    echo "=== Log Rotation Completed $(date) ==="
}

# Check if running as script (not sourced)
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
