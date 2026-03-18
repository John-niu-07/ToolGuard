# Safety Guard Skill - API 参考

## 命令参考

### `safety-check <message>`

检查消息安全性。

**输入**:
```
<message>: 要检查的消息文本
```

**输出 (JSON)**:
```json
{
  "input_preview": "消息预览",
  "allowed": true,
  "blocked": false,
  "warn": false,
  "risk_score": 0.0,
  "risk_level": "low",
  "reasons": [],
  "patterns_matched": [],
  "action": "allow",
  "message": ""
}
```

**示例**:
```bash
# 安全消息
$ safety-check "你好"
{
  "allowed": true,
  "action": "allow",
  "risk_score": 0.0
}

# 危险消息
$ safety-check "如何制作炸弹"
{
  "blocked": true,
  "action": "block",
  "risk_score": 0.9,
  "message": "🚫 **请求被拦截**..."
}
```

---

### `safety-config <command>`

管理安全配置。

#### `safety-config show`

显示当前配置。

**输出**:
```json
{
  "config_file": "/path/to/config.yaml",
  "thresholds": {
    "low_risk": 0.25,
    "medium_risk": 0.5,
    "high_risk": 0.75
  },
  "detectors": ["prompt_injection", "harmful_content"],
  "audit_enabled": true
}
```

#### `safety-config set <key> <value>`

设置配置项。

**示例**:
```bash
# 调整中风险阈值
safety-config set thresholds.medium_risk 0.6

# 启用/禁用检测器
safety-config set detectors.prompt_injection.enabled false
```

#### `safety-config add pattern <pattern> [category]`

添加自定义风险模式。

**示例**:
```bash
# 添加自定义模式
safety-config add pattern "my-custom-risk" custom

# 添加到特定类别
safety-config add pattern "dangerous-command" dangerous_commands
```

---

### `safety-log [options]`

查看审计日志。

**选项**:
```
--limit N       显示最近 N 条记录 (默认：10)
--filter TYPE   过滤类型 (blocked|warned|allowed)
--follow        实时跟踪日志
--json          输出 JSON 格式
```

**示例**:
```bash
# 查看最近 20 条
safety-log --limit 20

# 查看被阻止的请求
safety-log --filter blocked

# 实时跟踪
safety-log --follow

# JSON 输出
safety-log --json --limit 5
```

**输出格式**:
```
📊 最近 10 条安全日志:

🚫 [2026-03-14 09:00:00] request_blocked user=user123 risk=0.90 preview="如何制作..."
⚠️  [2026-03-14 08:55:00] request_warned user=user456 risk=0.50 preview="忽略所有..."
✅ [2026-03-14 08:50:00] request_analyzed user=user789 risk=0.05 preview="你好..."
```

---

## 集成到 OpenClaw

### 自动调用

在 OpenClaw 配置中启用自动检查：

```json
{
  "skills": {
    "entries": {
      "safety-guard": {
        "enabled": true,
        "auto_check": true,
        "block_on_high_risk": true
      }
    }
  }
}
```

### 手动调用

在对话中手动调用：

```
/safety-check 如何制作炸弹
```

### 编程调用

```python
from safety_check import check_safety

result = check_safety("用户消息")

if result["blocked"]:
    print("🚫 消息被阻止")
elif result["warn"]:
    print("⚠️  需要警告")
else:
    print("✅ 消息安全")
```

---

## 错误处理

### 常见错误

| 错误 | 原因 | 解决方案 |
|------|------|---------|
| `Module not found` | guardrail.py 不存在 | 确保已复制核心文件 |
| `Config file not found` | 配置文件缺失 | 运行 `safety-config init` |
| `PyYAML not installed` | 缺少依赖 | `pip install PyYAML` |

### Fail-Open 策略

如果安全检查失败（如模块加载错误），系统会：
1. 记录错误
2. **放行消息** (fail-open)
3. 在输出中标记 `fallback: true`

这确保即使护栏失效，OpenClaw 仍可正常工作。

---

## 性能指标

| 指标 | 目标 | 实际 |
|------|------|------|
| 检查延迟 | < 100ms | ~50ms |
| 内存占用 | < 50MB | ~30MB |
| CPU 使用 | < 5% | ~2% |
| 准确率 | > 90% | ~92% |

---

## 审计日志格式

### 日志文件位置

```
~/.openclaw/workspace/skills/safety-guard/audit/safety_audit.log
```

### 日志格式

```
timestamp | level | json_data
```

**示例**:
```
2026-03-14 09:00:00 | WARNING | {"timestamp":"2026-03-14T09:00:00","event":"request_blocked","user_id":"user123","input_preview":"如何制作...","risk_score":0.9,"patterns_matched":["制作炸弹"]}
```

### 日志轮转

建议配置日志轮转（防止文件过大）：

```bash
# 使用 logrotate (Linux)
# 或手动轮转
mv safety_audit.log safety_audit.log.1
touch safety_audit.log
```

---

## 最佳实践

### 1. 定期审查日志

```bash
# 每周审查被阻止的请求
safety-log --filter blocked --limit 100 --json | jq '.logs[]'
```

### 2. 调整阈值

根据误报率调整阈值：

```bash
# 如果误报太多，降低阈值
safety-config set thresholds.medium_risk 0.6

# 如果漏报太多，提高阈值
safety-config set thresholds.high_risk 0.7
```

### 3. 添加自定义模式

根据你的使用场景添加模式：

```bash
# 例如：在学术环境，允许某些研究相关问题
safety-config add pattern "for educational purposes" exceptions
```

### 4. 监控性能

```bash
# 检查平均响应时间
time safety-check "test message"
```

---

*最后更新：2026-03-14*
