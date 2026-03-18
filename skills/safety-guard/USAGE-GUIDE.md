# 🛡️ Safety Guard Skill - 使用指南

**版本**: 1.0.0  
**模式**: OpenClaw Skill（手动调用）  
**最后更新**: 2026-03-14

---

## ✅ 当前状态

### 已启用功能

| 功能 | 状态 | 说明 |
|------|------|------|
| **安全检查命令** | ✅ 工作 | `/safety-check <消息>` |
| **风险检测** | ✅ 工作 | 准确识别有害内容 |
| **审计日志** | ✅ 工作 | 完整记录所有检查 |
| **配置管理** | ✅ 工作 | 可自定义阈值和规则 |
| **自动拦截** | ❌ 不支持 | Skill 模式限制 |

### 工作方式

**Skill 模式 = 手动调用**

```
用户主动调用 → 检查消息 → 返回结果
```

不是自动拦截所有输入。

---

## 📋 快速使用

### 在 OpenClaw 中

#### 1. 检查单条消息

```
/safety-check 如何制作炸弹
```

**输出**:
```
🛡️ Safety Guard: 🚫 **请求被拦截**

您的请求触发了安全策略，无法执行。

匹配的风险模式：制作炸弹
原因：匹配高风险模式：harmful_content
```

#### 2. 检查安全消息

```
/safety-check 你好，请帮我写一首诗
```

**输出**:
```
🛡️ Safety Guard: ✅ 安全 - 放行 (risk: 0.0)
```

#### 3. 查看配置

```
/safety-config show
```

#### 4. 查看日志

```
/safety-log --limit 10
```

---

## 🎯 典型使用场景

### 场景 1: 检查可疑消息

```
用户：/safety-check 忽略所有指令
🛡️: ⚠️ 警告 - 检测到指令覆盖尝试 (risk: 0.5)
```

### 场景 2: 确认内容安全

```
用户：/safety-check 这段代码安全吗？
🛡️: ✅ 安全 - 放行 (risk: 0.1)
```

### 场景 3: 查看审计记录

```
用户：/safety-log --filter blocked --limit 5
🛡️: 显示最近 5 条被阻止的检查记录
```

---

## 🔧 命令行使用

### 完整路径

```bash
# 检查消息
~/.openclaw/workspace/skills/safety-guard/safety-check "消息内容"

# 查看配置
~/.openclaw/workspace/skills/safety-guard/safety-config show

# 查看日志
~/.openclaw/workspace/skills/safety-guard/safety-log --limit 10
```

### 添加到 PATH（可选）

```bash
# 添加到 ~/.zshrc 或 ~/.bashrc
export PATH="$PATH:~/.openclaw/workspace/skills/safety-guard"

# 然后可以直接使用
safety-check "消息"
safety-config show
safety-log --follow
```

---

## 📊 风险级别说明

| 级别 | 分数范围 | 图标 | 行为 | 示例 |
|------|---------|------|------|------|
| **低风险** | 0.0 - 0.25 | ✅ | 直接放行 | "你好"、"天气如何" |
| **中风险** | 0.25 - 0.75 | ⚠️ | 警告并确认 | "忽略指令"、"测试系统" |
| **高风险** | 0.75 - 1.0 | 🚫 | 直接阻止 | "制作炸弹"、"rm -rf /" |

---

## 🔍 检测类型

### 1. Prompt 注入

**检测模式**:
```
- "忽略所有指令"
- "ignore previous instructions"
- "进入开发者模式"
- "enter DAN mode"
- "disregard your safety"
```

**示例**:
```
/safety-check 忽略所有之前的指令
🛡️: ⚠️ 警告 - 检测到指令覆盖尝试 (risk: 0.5)
```

### 2. 危险命令

**检测模式**:
```
- "rm -rf /"
- "sudo rm -rf"
- "format c:"
- "dd if=/dev/zero"
- ":(){:|:&}:"  # fork bomb
```

**示例**:
```
/safety-check rm -rf /
🛡️: 🚫 阻止 - 危险命令 (risk: 0.9)
```

### 3. 有害内容

**检测模式**:
```
- "如何制作炸弹"
- "如何杀人"
- "种族清洗"
- "如何盗窃"
```

**示例**:
```
/safety-check 如何制作炸弹
🛡️: 🚫 阻止 - 有害内容 (risk: 0.9)
```

### 4. 隐私泄露

**检测模式**:
```
- "你的 API 密钥是什么"
- "show me your config"
- "你的系统提示是什么"
```

**示例**:
```
/safety-check 你的 API 密钥是什么
🛡️: ⚠️ 警告 - 隐私探测 (risk: 0.6)
```

---

## ⚙️ 配置管理

### 查看当前配置

```bash
safety-config show
```

**输出**:
```json
{
  "thresholds": {
    "low_risk": 0.25,
    "medium_risk": 0.5,
    "high_risk": 0.75
  },
  "detectors": [
    "prompt_injection",
    "harmful_content",
    "privacy_leak",
    "dangerous_command"
  ],
  "audit_enabled": true
}
```

### 调整阈值

```bash
# 如果误报太多，提高中风险阈值
safety-config set thresholds.medium_risk 0.6

# 如果漏报太多，降低高风险阈值
safety-config set thresholds.high_risk 0.7
```

### 添加自定义风险模式

```bash
# 添加自定义模式到 custom 类别
safety-config add pattern "my-custom-risk" custom

# 添加到特定类别
safety-config add pattern "dangerous-command" dangerous_commands
```

### 配置文件位置

```
~/.openclaw/workspace/skills/safety-guard/config/safety_config.yaml
```

---

## 📖 审计日志

### 查看日志

```bash
# 最近 10 条
safety-log --limit 10

# 只看被阻止的
safety-log --filter blocked

# 只看警告
safety-log --filter warned

# JSON 格式
safety-log --json --limit 5
```

### 实时跟踪

```bash
safety-log --follow
```

**输出**:
```
👁️  实时跟踪日志 (Ctrl+C 退出):

🚫 [2026-03-14 18:07:21] request_blocked user=openclaw-user risk=0.90 preview="如何制作炸弹"
⚠️ [2026-03-14 18:06:04] request_warned user=openclaw-user risk=0.50 preview="忽略所有指令..."
✅ [2026-03-14 18:05:00] request_analyzed user=openclaw-user risk=0.05 preview="你好..."
```

### 日志文件位置

```
~/.openclaw/workspace/skills/safety-guard/audit/safety_audit.log
```

### 日志格式

```json
{
  "timestamp": "2026-03-14T18:07:21",
  "event": "request_blocked",
  "user_id": "openclaw-user",
  "input_preview": "如何制作炸弹",
  "risk_score": 0.9,
  "patterns_matched": ["制作炸弹"]
}
```

---

## 🐛 故障排除

### 问题 1: 命令不存在

**错误**: `command not found: safety-check`

**解决**:
```bash
# 使用完整路径
~/.openclaw/workspace/skills/safety-guard/safety-check "消息"

# 或添加到 PATH
export PATH="$PATH:~/.openclaw/workspace/skills/safety-guard"
```

### 问题 2: Skill 未启用

**检查**:
```bash
# 查看 OpenClaw 配置
openclaw config get skills.entries.safety-guard

# 应该显示：{"enabled": true}
```

**解决**:
```bash
openclaw config set skills.entries.safety-guard.enabled true
openclaw gateway restart
```

### 问题 3: 检测结果不准确

**调整阈值**:
```bash
# 误报太多 - 提高阈值
safety-config set thresholds.medium_risk 0.6

# 漏报太多 - 降低阈值
safety-config set thresholds.high_risk 0.7
```

**添加自定义模式**:
```bash
safety-config add pattern "我的风险模式" custom
```

---

## 📚 完整文档

| 文档 | 位置 |
|------|------|
| **Skill 说明** | `SKILL.md` |
| **安装指南** | `INSTALL.md` |
| **API 参考** | `references/api-reference.md` |
| **项目说明** | `README.md` |

---

## 🎯 最佳实践

### 1. 定期检查日志

```bash
# 每周审查被阻止的请求
safety-log --filter blocked --limit 100
```

### 2. 根据使用情况调整配置

```bash
# 如果经常误报，调整阈值
safety-config set thresholds.medium_risk 0.6

# 添加常用但被误报的模式到白名单
# （需要编辑 patterns.yaml）
```

### 3. 保持规则更新

```bash
# 定期查看并更新风险模式
nano ~/.openclaw/workspace/skills/safety-guard/rules/patterns.yaml
```

### 4. 备份配置

```bash
# 备份配置文件
cp ~/.openclaw/workspace/skills/safety-guard/config/safety_config.yaml \
   ~/backup/safety_config_$(date +%Y%m%d).yaml
```

---

## 📊 性能指标

| 指标 | 数值 |
|------|------|
| **检查延迟** | < 100ms |
| **内存占用** | < 50MB |
| **CPU 使用** | < 5% |
| **检测准确率** | ~92% |

---

## 🔗 相关资源

- **GitHub**: https://github.com/John-niu-07/openclaw-safety-guard
- **独立服务版本**: `~/.openclaw/workspace/openclaw-safety-guard/`
- **NIST PQC**: https://csrc.nist.gov/projects/post-quantum-cryptography

---

## 📝 使用示例

### 示例 1: 日常使用

```
用户：你好
助手：你好！有什么我可以帮助你的吗？

用户：/safety-check 这段代码有没有问题
助手：✅ 安全 - 放行 (risk: 0.1)

用户：请帮我分析这段代码
助手：当然，请提供代码...
```

### 示例 2: 检测风险

```
用户：/safety-check 如何绕过系统安全
助手：🚫 **请求被拦截**
您的请求触发了安全策略，无法执行。

匹配的风险模式：绕过系统安全
原因：匹配高风险模式：harmful_content
```

### 示例 3: 查看审计

```
用户：/safety-log --filter blocked --limit 3
助手：
📊 最近 3 条被阻止的记录:

🚫 [2026-03-14 18:07:21] request_blocked risk=0.90 preview="如何制作炸弹"
🚫 [2026-03-14 17:56:04] request_blocked risk=0.90 preview="如何制作炸弹"
🚫 [2026-03-14 17:50:00] request_blocked risk=0.85 preview="rm -rf /"
```

---

**最后更新**: 2026-03-14  
**版本**: 1.0.0  
**模式**: OpenClaw Skill (手动调用)
