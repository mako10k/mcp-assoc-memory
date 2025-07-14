#!/bin/bash
# MCP Associative Memory Server Daemon Control Script
# Usage: ./scripts/mcp_server_daemon.sh {start|stop|restart|status}


APP_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON=python3
PID_FILE="$APP_DIR/logs/mcp_server.pid"
LOG_FILE="$APP_DIR/logs/mcp_server.log"

export PYTHONPATH="$APP_DIR/src:$PYTHONPATH"
start() {
    if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
        echo "MCP server is already running (PID: $(cat $PID_FILE))"
        exit 1
    fi
    echo "Starting MCP server..."
    cd "$APP_DIR"
    
    # Ensure logs directory exists
    mkdir -p "$(dirname "$LOG_FILE")"
    
    # Check if log rotation is needed before starting
    if [ -f "$LOG_FILE" ]; then
        log_size_mb=$(du -m "$LOG_FILE" | cut -f1)
        if [ "$log_size_mb" -ge 10 ]; then
            echo "Log file is large ($log_size_mb MB), rotating before start..."
            "$APP_DIR/scripts/rotate_logs.sh" >/dev/null 2>&1
        fi
    fi
    
    # Log startup attempt
    echo "========================================================================================" >> "$LOG_FILE"
    echo "$(date '+%Y-%m-%d %H:%M:%S') [DAEMON] Starting MCP server..." >> "$LOG_FILE"
    echo "$(date '+%Y-%m-%d %H:%M:%S') [DAEMON] Working directory: $(pwd)" >> "$LOG_FILE"
    echo "$(date '+%Y-%m-%d %H:%M:%S') [DAEMON] PYTHONPATH: $PYTHONPATH" >> "$LOG_FILE"
    echo "$(date '+%Y-%m-%d %H:%M:%S') [DAEMON] Python executable: $PYTHON" >> "$LOG_FILE"
    
    # Start MCP server (single entry point: server.py)
    CONFIG_ARG="--config $APP_DIR/config.json"
    
    # Test syntax and imports first - capture any immediate errors
    echo "$(date '+%Y-%m-%d %H:%M:%S') [DAEMON] Testing Python syntax and imports..." >> "$LOG_FILE"
    if ! $PYTHON -c "import src.mcp_assoc_memory.server" >> "$LOG_FILE" 2>&1; then
        echo "$(date '+%Y-%m-%d %H:%M:%S') [DAEMON] ERROR: Failed to import server module" >> "$LOG_FILE"
        echo "FAILED: Import test failed. Check logs/mcp_server.log for details."
        exit 1
    fi
    echo "$(date '+%Y-%m-%d %H:%M:%S') [DAEMON] Import test successful" >> "$LOG_FILE"
    
    # Start server with enhanced error capture
    echo "$(date '+%Y-%m-%d %H:%M:%S') [DAEMON] Launching server process..." >> "$LOG_FILE"
    nohup $PYTHON -m mcp_assoc_memory.server $CONFIG_ARG >> "$LOG_FILE" 2>&1 &
    SERVER_PID=$!
    echo $SERVER_PID > "$PID_FILE"
    
    # Wait a moment and check if process is still running
    sleep 3
    if kill -0 $SERVER_PID 2>/dev/null; then
        echo "$(date '+%Y-%m-%d %H:%M:%S') [DAEMON] Server started successfully (PID: $SERVER_PID)" >> "$LOG_FILE"
        echo "Started successfully (PID: $SERVER_PID)"
    else
        echo "$(date '+%Y-%m-%d %H:%M:%S') [DAEMON] ERROR: Server process died immediately after startup" >> "$LOG_FILE"
        rm -f "$PID_FILE"
        echo "FAILED: Server died immediately. Check logs/mcp_server.log for details."
        exit 1
    fi
}

stop() {
    if [ ! -f "$PID_FILE" ]; then
        echo "MCP server is not running"
        exit 1
    fi
    PID=$(cat "$PID_FILE")
    if kill -0 $PID 2>/dev/null; then
        echo "Stopping MCP server..."
        kill $PID
        
        # Wait for process to actually stop (max 10 seconds)
        for i in {1..10}; do
            if ! kill -0 $PID 2>/dev/null; then
                break
            fi
            sleep 1
        done
        
        # Force kill if still running
        if kill -0 $PID 2>/dev/null; then
            echo "Process didn't stop gracefully, force killing..."
            kill -9 $PID
            sleep 2
        fi
        
        rm -f "$PID_FILE"
        echo "Stopped successfully"
    else
        echo "MCP server process does not exist (removing PID file only)"
        rm -f "$PID_FILE"
        echo "PID file removed"
    fi
}

restart() {
    stop
    sleep 1
    start
}

status() {
    if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
        echo "MCP server is running (PID: $(cat $PID_FILE))"
    else
        echo "MCP server is stopped"
    fi
}

case "$1" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        restart
        ;;
    status)
        status
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status}"
        exit 1
        ;;
esac
