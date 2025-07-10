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
    # Start MCP server (recommended: python -m mcp_assoc_memory ...)
    CONFIG_ARG="--config $APP_DIR/config.json"

    nohup $PYTHON -m mcp_assoc_memory $CONFIG_ARG >> "$LOG_FILE" 2>&1 &
    echo $! > "$PID_FILE"
    echo "Started successfully (PID: $(cat $PID_FILE))"
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
