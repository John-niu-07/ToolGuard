#!/bin/bash
# ToolGuard CLI Wrappers 批量安装脚本

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOOLGUARD_DIR="$(dirname "$SCRIPT_DIR")"

echo "🛡️ ToolGuard CLI Wrappers 批量安装"
echo ""

# 检查 ToolGuard 服务
if ! curl -s http://127.0.0.1:8767/health > /dev/null 2>&1; then
    echo "❌ ToolGuard 服务未运行"
    echo "   cd $TOOLGUARD_DIR && ./start.sh start"
    exit 1
fi
echo "✅ ToolGuard 服务运行中"

# 可用的 wrappers
echo ""
echo "可用的 CLI Wrappers:"
echo "  1) himalaya  - 邮件发送"
echo "  2) git       - 版本控制（push/commit/merge 等）"
echo "  3) curl      - 网络请求（POST/PUT/DELETE）"
echo "  4) ssh       - 远程连接"
echo "  5) scp       - 文件传输"
echo "  6) rsync     - 文件同步"
echo "  7) 全部安装"
echo "  8) 自定义选择"
echo ""

read -p "请选择 [1-8]: " choice

# 选择要安装的工具
TOOLS=()
case $choice in
    1) TOOLS=("himalaya") ;;
    2) TOOLS=("git") ;;
    3) TOOLS=("curl") ;;
    4) TOOLS=("ssh") ;;
    5) TOOLS=("scp") ;;
    6) TOOLS=("rsync") ;;
    7) TOOLS=("himalaya" "git" "curl" "ssh" "scp" "rsync") ;;
    8)
        echo ""
        echo "输入要安装的工具编号（空格分隔，如：1 2 3）："
        read -p "> " selections
        
        for sel in $selections; do
            case $sel in
                1) TOOLS+=("himalaya") ;;
                2) TOOLS+=("git") ;;
                3) TOOLS+=("curl") ;;
                4) TOOLS+=("ssh") ;;
                5) TOOLS+=("scp") ;;
                6) TOOLS+=("rsync") ;;
            esac
        done
        ;;
    *)
        echo "❌ 无效选择"
        exit 1
        ;;
esac

if [[ ${#TOOLS[@]} -eq 0 ]]; then
    echo "❌ 未选择任何工具"
    exit 1
fi

echo ""
echo "将安装以下 wrappers:"
for tool in "${TOOLS[@]}"; do
    echo "  - $tool"
done

# 选择安装方式
echo ""
echo "选择安装方式："
echo "  1) 创建别名（推荐）"
echo "  2) 修改 PATH"
echo ""
read -p "请选择 [1-2]: " install_choice

# 确定 SHELL 配置文件
SHELL_RC=""
if [[ "$SHELL" == *"zsh"* ]]; then
    SHELL_RC="$HOME/.zshrc"
elif [[ "$SHELL" == *"bash"* ]]; then
    SHELL_RC="$HOME/.bashrc"
else
    SHELL_RC="$HOME/.profile"
fi

case $install_choice in
    1)
        # 创建别名
        echo ""
        echo "📝 添加别名到 $SHELL_RC..."
        
        # 备份
        cp "$SHELL_RC" "${SHELL_RC}.backup.$(date +%Y%m%d%H%M%S)"
        
        # 添加别名
        echo "" >> "$SHELL_RC"
        echo "# ToolGuard CLI Wrappers (added $(date))" >> "$SHELL_RC"
        for tool in "${TOOLS[@]}"; do
            if grep -q "alias $tool=" "$SHELL_RC" 2>/dev/null; then
                echo "⚠️  $tool 别名已存在，跳过"
            else
                echo "alias $tool='$SCRIPT_DIR/$tool'" >> "$SHELL_RC"
                echo "✅ $tool"
            fi
        done
        
        echo ""
        echo "✅ 别名已添加到 $SHELL_RC"
        echo ""
        echo "使别名生效："
        echo "   source $SHELL_RC"
        ;;
        
    2)
        # 修改 PATH
        echo ""
        echo "📝 添加 wrapper 目录到 PATH..."
        
        # 备份
        cp "$SHELL_RC" "${SHELL_RC}.backup.$(date +%Y%m%d%H%M%S)"
        
        # 添加到 PATH
        if ! grep -q "ToolGuard CLI Wrappers PATH" "$SHELL_RC" 2>/dev/null; then
            echo "" >> "$SHELL_RC"
            echo "# ToolGuard CLI Wrappers PATH (added $(date))" >> "$SHELL_RC"
            echo "export PATH=\"$SCRIPT_DIR:\$PATH\"" >> "$SHELL_RC"
            echo "✅ PATH 已更新"
        else
            echo "⚠️ PATH 已配置，跳过"
        fi
        
        echo ""
        echo "使 PATH 生效："
        echo "   source $SHELL_RC"
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
for tool in "${TOOLS[@]}"; do
    echo "   $tool --help  # 会触发 ToolGuard 确认"
done
echo ""
echo "Web 界面：http://127.0.0.1:8767"
