#!/bin/bash
# MCP Associative Memory Server Daemon Control Script
# Usage: ./scripts/mcp_server_daemon.sh {start|stop|restart|status}

APP_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON=python3
SERVER_MODULE="mcp_assoc_memory.server"
PID_FILE="$APP_DIR/logs/mcp_server.pid"
LOG_FILE="$APP_DIR/logs/mcp_server.log"

start() {
    if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
        echo "MCPサーバは既に起動しています (PID: $(cat $PID_FILE))"
        exit 1
    fi
    echo "MCPサーバを起動します..."
    cd "$APP_DIR"
    # 環境変数でトランスポート/ポートを指定してください（--transport/--port引数は未対応）
    export HTTP_ENABLED=true
    export HTTP_PORT=3006
    export STDIO_ENABLED=false

    nohup $PYTHON -m $SERVER_MODULE >> "$LOG_FILE" 2>&1 &
    echo $! > "$PID_FILE"
    echo "起動しました (PID: $(cat $PID_FILE))"
}

stop() {
    if [ ! -f "$PID_FILE" ] || ! kill -0 $(cat "$PID_FILE") 2>/dev/null; then
        echo "MCPサーバは起動していません"
        exit 1
    fi
    echo "MCPサーバを停止します..."
    kill $(cat "$PID_FILE")
    rm -f "$PID_FILE"
    echo "停止しました"
}

restart() {
    stop
    sleep 1
    start
}

status() {
    if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
        echo "MCPサーバは稼働中です (PID: $(cat $PID_FILE))"
    else
        echo "MCPサーバは停止しています"
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
