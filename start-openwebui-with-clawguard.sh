#!/bin/bash
# Open WebUI Startup Script with ClawGuard Integration

set -e

echo "🚀 Starting Open WebUI with ClawGuard Safety Shield..."
echo ""

# Configuration - MUST be set BEFORE starting Open WebUI
export ENABLE_CLAWGUARD=true
export CLAWGUARD_API_URL=http://localhost:8000
export CLAWGUARD_TIMEOUT_SECONDS=5
export CLAWGUARD_BLOCK_ON_ERROR=true
export CLAWGUARD_CHECK_RESPONSES=false

# Export to child processes
export OPENWEBUI_CLAWGUARD_ENABLED=true

echo "⚙️  Environment Variables:"
echo "   ENABLE_CLAWGUARD=$ENABLE_CLAWGUARD"
echo "   CLAWGUARD_API_URL=$CLAWGUARD_API_URL"
echo "   CLAWGUARD_TIMEOUT_SECONDS=$CLAWGUARD_TIMEOUT_SECONDS"
echo "   CLAWGUARD_BLOCK_ON_ERROR=$CLAWGUARD_BLOCK_ON_ERROR"
echo ""

# Check if ClawGuard service is running
if curl -s http://localhost:8000/health >/dev/null 2>&1; then
    echo "✅ ClawGuard service is running"
else
    echo "⚠️  Warning: ClawGuard service is not running on port 8000"
    echo "   Please start it first: cd /opt/homebrew/lib/python3.11/site-packages/open_webui/clawguard && python3.11 server.py"
    echo ""
fi

# Start Open WebUI
echo "📡 Starting Open WebUI on port 8080..."
nohup /opt/homebrew/bin/open-webui serve --host 0.0.0.0 --port 8080 > /tmp/openwebui.log 2>&1 &
OPENWEBUI_PID=$!
echo $OPENWEBUI_PID > /tmp/openwebui.pid

echo "⏳ Waiting for Open WebUI to start..."
sleep 10

# Check if started successfully
if curl -s http://localhost:8080/api/version >/dev/null 2>&1; then
    echo "✅ Open WebUI started successfully (PID: $OPENWEBUI_PID)"
    echo ""
    echo "📋 Services:"
    echo "   - Open WebUI: http://localhost:8080"
    echo "   - ClawGuard:  http://localhost:8000"
    echo ""
    echo "📝 Logs:"
    echo "   tail -f /tmp/openwebui.log"
    echo ""
    echo "🛑 Stop:"
    echo "   kill $OPENWEBUI_PID"
else
    echo "❌ Failed to start Open WebUI"
    echo "Check logs: tail -20 /tmp/openwebui.log"
    exit 1
fi
