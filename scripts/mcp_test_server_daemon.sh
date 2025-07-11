#!/bin/bash
# Test environment server daemon script
# Manages MCP associative memory server for testing on port 8001

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
CONFIG_FILE="$PROJECT_ROOT/config-test.json"
PID_FILE="$PROJECT_ROOT/logs/mcp_test_server.pid"
LOG_FILE="$PROJECT_ROOT/logs/mcp_test_server.log"

# Ensure logs directory exists
mkdir -p "$PROJECT_ROOT/logs"

# Export test configuration
export MCP_CONFIG_FILE="$CONFIG_FILE"

start_server() {
    if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
        echo "Test server is already running (PID: $(cat "$PID_FILE"))"
        return 1
    fi
    
    echo "Starting MCP test server on port 8001..."
    cd "$PROJECT_ROOT"
    
    # Start server with test config
    MCP_CONFIG_FILE="$CONFIG_FILE" python -m src.mcp_assoc_memory.server > "$LOG_FILE" 2>&1 &
    SERVER_PID=$!
    
    echo $SERVER_PID > "$PID_FILE"
    
    # Wait a moment to check if server started successfully
    sleep 2
    if kill -0 $SERVER_PID 2>/dev/null; then
        echo "Test server started successfully (PID: $SERVER_PID)"
        echo "Port: 8001"
        echo "Config: $CONFIG_FILE"
        echo "Logs: $LOG_FILE"
        return 0
    else
        echo "Failed to start test server"
        rm -f "$PID_FILE"
        return 1
    fi
}

stop_server() {
    if [ ! -f "$PID_FILE" ]; then
        echo "Test server is not running"
        return 1
    fi
    
    PID=$(cat "$PID_FILE")
    if kill -0 $PID 2>/dev/null; then
        echo "Stopping test server (PID: $PID)..."
        kill $PID
        
        # Wait for graceful shutdown
        for i in {1..10}; do
            if ! kill -0 $PID 2>/dev/null; then
                break
            fi
            sleep 1
        done
        
        # Force kill if still running
        if kill -0 $PID 2>/dev/null; then
            echo "Force killing test server..."
            kill -9 $PID
        fi
        
        rm -f "$PID_FILE"
        echo "Test server stopped"
    else
        echo "Test server process not found, cleaning up PID file"
        rm -f "$PID_FILE"
    fi
    return 0
}

restart_server() {
    echo "Restarting test server..."
    stop_server
    sleep 1
    start_server
}

status_server() {
    if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
        PID=$(cat "$PID_FILE")
        echo "Test server is running (PID: $PID)"
        echo "Port: 8001"
        echo "Config: $CONFIG_FILE"
        echo "Logs: $LOG_FILE"
        
        # Check if port is actually listening
        if netstat -ln 2>/dev/null | grep -q ":8001 "; then
            echo "Port 8001 is listening"
        else
            echo "Warning: Port 8001 is not listening"
        fi
        return 0
    else
        echo "Test server is not running"
        return 1
    fi
}

case "$1" in
    start)
        start_server
        ;;
    stop)
        stop_server
        ;;
    restart)
        restart_server
        ;;
    status)
        status_server
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status}"
        echo ""
        echo "Test Environment Server Management"
        echo "  start   - Start test server on port 8001"
        echo "  stop    - Stop test server"
        echo "  restart - Restart test server"
        echo "  status  - Check test server status"
        echo ""
        echo "Test Config: $CONFIG_FILE"
        echo "Production server remains on port 8000"
        exit 1
        ;;
esac

exit $?
