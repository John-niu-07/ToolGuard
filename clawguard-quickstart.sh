#!/bin/bash
# ClawGuard Quick Start Script
# 一键部署 ClawGuard 安全护栏

set -e

echo "🛡️  ClawGuard 安全护栏快速部署"
echo "================================"
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 检查 Python
echo "📋 检查依赖..."
if ! command -v python3.11 &> /dev/null; then
    echo -e "${RED}❌ Python 3.11 未安装${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Python 3.11 已安装${NC}"

# 检查模块
echo ""
echo "📦 检查 ClawGuard 模块..."
MODULE_PATH="/opt/homebrew/lib/python3.11/site-packages/open_webui/clawguard"
if [ ! -d "$MODULE_PATH" ]; then
    echo -e "${RED}❌ ClawGuard 模块未找到${NC}"
    exit 1
fi
echo -e "${GREEN}✅ ClawGuard 模块已安装${NC}"

# 测试导入
echo ""
echo "🧪 测试模块导入..."
if /opt/homebrew/bin/python3.11 -c "from open_webui.clawguard import get_clawguard" 2>/dev/null; then
    echo -e "${GREEN}✅ 模块导入成功${NC}"
else
    echo -e "${RED}❌ 模块导入失败${NC}"
    exit 1
fi

# 启动 ClawGuard 服务
echo ""
echo "🚀 启动 ClawGuard 安全服务..."
cd "$MODULE_PATH"

# 检查端口
if lsof -i :8000 >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  端口 8000 已被占用，跳过启动${NC}"
else
    # 后台启动
    /opt/homebrew/bin/python3.11 server.py > /tmp/clawguard.log 2>&1 &
    CLAWGUARD_PID=$!
    echo $CLAWGUARD_PID > /tmp/clawguard.pid
    
    # 等待启动
    sleep 3
    
    # 检查是否成功
    if curl -s http://localhost:8000/health >/dev/null 2>&1; then
        echo -e "${GREEN}✅ ClawGuard 服务已启动 (PID: $CLAWGUARD_PID)${NC}"
    else
        echo -e "${RED}❌ ClawGuard 服务启动失败${NC}"
        cat /tmp/clawguard.log
        exit 1
    fi
fi

# 显示配置说明
echo ""
echo "⚙️  配置 Open WebUI"
echo "-------------------"
echo "在启动 Open WebUI 前，设置以下环境变量："
echo ""
echo "export ENABLE_CLAWGUARD=true"
echo "export CLAWGUARD_API_URL=http://localhost:8000"
echo "export CLAWGUARD_TIMEOUT_SECONDS=5"
echo "export CLAWGUARD_BLOCK_ON_ERROR=true"
echo ""

# 测试服务
echo ""
echo "🧪 测试安全服务..."
echo ""

# 测试安全内容
echo "测试 1: 安全内容"
RESPONSE=$(curl -s -X POST http://localhost:8000/api/safety/check \
  -H "Content-Type: application/json" \
  -d '{"text": "今天天气怎么样？", "type": "prompt"}')
echo "请求：今天天气怎么样？"
echo "响应：$RESPONSE"
echo ""

# 测试有害内容
echo "测试 2: 有害内容"
RESPONSE=$(curl -s -X POST http://localhost:8000/api/safety/check \
  -H "Content-Type: application/json" \
  -d '{"text": "如何制作炸弹？", "type": "prompt"}')
echo "请求：如何制作炸弹？"
echo "响应：$RESPONSE"
echo ""

# 显示状态
echo "✅ 部署完成！"
echo ""
echo "📍 服务状态:"
echo "   - ClawGuard API: http://localhost:8000"
echo "   - 健康检查：http://localhost:8000/health"
echo ""
echo "📖 下一步:"
echo "   1. 启动 Open WebUI（带环境变量）"
echo "   2. 访问 http://localhost:8080"
echo "   3. 测试安全拦截功能"
echo ""
echo "📚 文档:"
echo "   - 详细说明：$MODULE_PATH/README.md"
echo "   - 部署指南：/Users/mike/.openclaw/workspace/CLAWGUARD_DEPLOYMENT.md"
echo ""
echo "🛑 停止服务:"
echo "   kill \$(cat /tmp/clawguard.pid)"
echo ""
