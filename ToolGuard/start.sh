#!/bin/bash
# ToolGuard 启动脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/src/toolguard_server.py"
PID_FILE="$SCRIPT_DIR/toolguard.pid"
LOG_FILE="$SCRIPT_DIR/logs/toolguard.log"

# 确保日志目录存在
mkdir -p "$SCRIPT_DIR/logs"

start() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p $PID > /dev/null 2>&1; then
            echo "ℹ️  ToolGuard 已经在运行 (PID: $PID)"
            return 1
        else
            rm -f "$PID_FILE"
        fi
    fi
    
    echo "🚀 启动 ToolGuard Server..."
    
    # 启动服务
    cd "$SCRIPT_DIR"
    nohup python3 "$PYTHON_SCRIPT" > "$LOG_FILE" 2>&1 &
    PID=$!
    echo $PID > "$PID_FILE"
    
    sleep 2
    
    if ps -p $PID > /dev/null 2>&1; then
        echo "✅ ToolGuard 启动成功 (PID: $PID)"
        echo ""
        echo "📊 服务信息:"
        echo "   地址：http://127.0.0.1:8767"
        echo "   健康检查：http://127.0.0.1:8767/health"
        echo "   日志：$LOG_FILE"
        echo ""
        echo "📝 测试命令:"
        echo "   curl http://127.0.0.1:8767/health"
        echo "   python3 src/toolguard.py check message send '{\"to\":\"test@example.com\"}'"
        return 0
    else
        echo "❌ ToolGuard 启动失败"
        echo "查看日志：tail -f $LOG_FILE"
        return 1
    fi
}

stop() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p $PID > /dev/null 2>&1; then
            echo "🛑 停止 ToolGuard (PID: $PID)..."
            kill $PID
            rm -f "$PID_FILE"
            sleep 1
            echo "✅ ToolGuard 已停止"
            return 0
        else
            rm -f "$PID_FILE"
            echo "ℹ️  ToolGuard 未运行"
            return 1
        fi
    else
        echo "ℹ️  ToolGuard 未运行 (PID 文件不存在)"
        return 1
    fi
}

restart() {
    stop
    sleep 1
    start
}

status() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p $PID > /dev/null 2>&1; then
            echo "✅ ToolGuard 运行中 (PID: $PID)"
            return 0
        else
            echo "❌ ToolGuard 未运行 (进程不存在)"
            return 1
        fi
    else
        echo "❌ ToolGuard 未运行 (PID 文件不存在)"
        return 1
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
        echo "用法：$0 {start|stop|restart|status}"
        exit 1
        ;;
esac
