#!/bin/bash
# ToolGuard CLI Wrappers 安装脚本

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOOLGUARD_DIR="$(dirname "$SCRIPT_DIR")"

echo "🛡️ ToolGuard CLI Wrappers 安装程序"
echo ""

# 检查 ToolGuard 服务
if ! curl -s http://127.0.0.1:8767/health > /dev/null 2>&1; then
    echo "❌ ToolGuard 服务未运行，请先启动："
    echo "   cd $TOOLGUARD_DIR && ./start.sh start"
    exit 1
fi
echo "✅ ToolGuard 服务运行中"

# 选择安装方式
echo ""
echo "选择安装方式："
echo "  1) 创建别名（推荐，安全）"
echo "  2) 替换 PATH（全局生效）"
echo "  3) 仅测试当前会话"
echo ""
read -p "请选择 [1-3]: " choice

case $choice in
    1)
        # 创建别名
        echo ""
        echo "📝 将别名添加到你的 shell 配置文件..."
        
        SHELL_RC=""
        if [[ "$SHELL" == *"zsh"* ]]; then
            SHELL_RC="$HOME/.zshrc"
        elif [[ "$SHELL" == *"bash"* ]]; then
            SHELL_RC="$HOME/.bashrc"
        else
            SHELL_RC="$HOME/.profile"
        fi
        
        echo ""
        echo "# ToolGuard CLI Wrappers" >> "$SHELL_RC"
        echo "alias himalaya='$SCRIPT_DIR/himalaya'" >> "$SHELL_RC"
        
        echo "✅ 已添加到 $SHELL_RC"
        echo ""
        echo "请运行以下命令使别名生效："
        echo "   source $SHELL_RC"
        echo ""
        echo "或重启终端"
        ;;
        
    2)
        # 替换 PATH
        echo ""
        echo "📝 将 wrapper 目录添加到 PATH..."
        
        # 备份原始 himalaya
        REAL_HIMALAYA=$(which himalaya 2>/dev/null || echo "")
        if [[ -n "$REAL_HIMALAYA" && ! -f "/usr/local/bin/himalaya.real" ]]; then
            echo "📦 备份原始 himalaya: $REAL_HIMALAYA"
            sudo cp "$REAL_HIMALAYA" "/usr/local/bin/himalaya.real"
        fi
        
        # 添加到 PATH
        SHELL_RC=""
        if [[ "$SHELL" == *"zsh"* ]]; then
            SHELL_RC="$HOME/.zshrc"
        elif [[ "$SHELL" == *"bash"* ]]; then
            SHELL_RC="$HOME/.bashrc"
        else
            SHELL_RC="$HOME/.profile"
        fi
        
        echo ""
        echo "# ToolGuard CLI Wrappers PATH" >> "$SHELL_RC"
        echo "export PATH=\"$SCRIPT_DIR:\$PATH\"" >> "$SHELL_RC"
        
        echo "✅ 已添加到 $SHELL_RC"
        echo ""
        echo "请运行以下命令使 PATH 生效："
        echo "   source $SHELL_RC"
        ;;
        
    3)
        # 仅测试
        echo ""
        echo "📝 仅在当前会话生效..."
        export PATH="$SCRIPT_DIR:$PATH"
        echo "✅ 当前终端可以使用 wrapper 了"
        echo ""
        echo "测试：himalaya --help"
        ;;
        
    *)
        echo "❌ 无效选择"
        exit 1
        ;;
esac

echo ""
echo "🎉 安装完成！"
echo ""
echo "测试命令："
echo "   himalaya message send  # 会触发 ToolGuard 确认"
echo ""
echo "Web 界面：http://127.0.0.1:8767"
