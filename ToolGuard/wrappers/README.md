# ToolGuard CLI Wrappers

通过包装器脚本监控独立 CLI 工具的调用。

---

## 原理

```
用户命令 → Wrapper 脚本 → ToolGuard API 检查 → 用户确认 → 真实 CLI 工具
```

Wrapper 脚本会：
1. 拦截 CLI 命令调用
2. 调用 ToolGuard API 检查是否需要确认
3. 如果需要确认，等待用户在 Web 界面确认
4. 确认后执行真实的 CLI 命令

---

## 支持的 CLI 工具

| 工具 | Wrapper | 风险操作 |
|------|---------|---------|
| mail-send | `wrappers/mail-send` | 邮件发送（推荐使用）✅ |
| rm | `wrappers/rm` | 删除文件（rm/rm -rf）✅ |
| trash | `wrappers/trash` | 回收到垃圾桶 ✅ |
| himalaya | `wrappers/himalaya` | send, write, reply, forward |
| git | `wrappers/git` | push, commit, merge, rebase, reset, clean |
| curl | `wrappers/curl` | POST, PUT, DELETE 请求 |
| ssh | `wrappers/ssh` | 所有远程连接 |
| scp | `wrappers/scp` | 文件传输（特别是上传） |
| rsync | `wrappers/rsync` | 同步（特别是带 --delete） |

---

## 安装

### 方式 1：创建别名（推荐）

```bash
cd ~/.openclaw/workspace/ToolGuard/wrappers
./install.sh  # 选择 1
```

会在 `~/.zshrc` 或 `~/.bashrc` 中添加：
```bash
alias himalaya='~/.openclaw/workspace/ToolGuard/wrappers/himalaya'
```

### 方式 2：修改 PATH

```bash
cd ~/.openclaw/workspace/ToolGuard/wrappers
./install.sh  # 选择 2
```

会在 PATH 最前面添加 wrapper 目录。

### 方式 3：临时测试

```bash
cd ~/.openclaw/workspace/ToolGuard/wrappers
./install.sh  # 选择 3
# 或手动
export PATH="$PWD:$PATH"
```

---

## 使用示例

### 发送邮件（会触发确认）

```bash
echo "测试内容" | himalaya message send
```

**ToolGuard 会显示：**
```
🛡️ ToolGuard 拦截：himalaya message send
   原因：发送邮件，可能发送未授权内容
   风险等级：high
   确认 ID: xxx

请在 Web 界面确认：http://127.0.0.1:8767
```

### 查看邮件（不会触发确认）

```bash
himalaya envelope list
```

---

## 添加新的 CLI 工具

1. 在 `wrappers/` 目录创建包装脚本
2. 参考 `himalaya` 的实现
3. 在 ToolGuard 的 `risk_tool_list.json` 中添加配置
4. 运行 `./install.sh` 添加别名

### 示例：添加 git wrapper

```python
#!/usr/bin/env python3
"""ToolGuard Wrapper for git"""

import subprocess
import sys
import json
import http.client

TOOLGUARD_HOST = '127.0.0.1'
TOOLGUARD_PORT = 8767
REAL_GIT = '/usr/bin/git'

def check_toolguard():
    args = sys.argv[1:]
    
    # 判断风险操作
    risky_commands = ['push', 'commit', 'merge', 'rebase']
    if any(cmd in args for cmd in risky_commands):
        # 调用 ToolGuard API 检查
        ...

if __name__ == '__main__':
    check_toolguard()
    subprocess.run([REAL_GIT] + args)
```

---

## 故障排除

### Wrapper 不生效

1. 检查别名：`alias | grep himalaya`
2. 检查 PATH：`echo $PATH`
3. 重新加载配置：`source ~/.zshrc`

### ToolGuard 服务未运行

```bash
cd ~/.openclaw/workspace/ToolGuard
./start.sh start
```

### 找不到真实 CLI

确保原始 CLI 在 PATH 中，或修改 wrapper 中的 `REAL_HIMALAYA` 路径。

---

## Fail-Open 机制

如果 ToolGuard 服务不可用，wrapper 会放行命令（不影响正常使用），但会打印警告。

---

## 安全说明

- Wrapper 脚本本身应该只读，防止被篡改
- 建议定期审计 wrapper 脚本
- 生产环境建议使用系统级包装（需要 root 权限）
