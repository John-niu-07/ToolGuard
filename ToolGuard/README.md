# 🛡️ ToolGuard - OpenClaw 工具调用监控系统

**ToolGuard** 是一个用于监控 OpenClaw 在执行用户请求过程中对外部工具调用的安全系统。它会拦截危险工具调用并请求用户确认，确保工具调用的安全性和可控性。

---

## 🎯 核心功能

- ✅ **危险工具拦截** - 拦截 risk tool 列表中定义的危险工具
- ✅ **用户确认机制** - 在危险工具调用前请求用户确认
- ✅ **风险等级分类** - 根据风险等级设置不同的超时时间
- ✅ **审计日志** - 完整记录所有工具调用和确认
- ✅ **Web 管理界面** - 查看待确认请求和审计日志

---

## 🏗️ 系统架构

```
OpenClaw Gateway
    ↓
ToolGuard Hook (工具调用拦截)
    ↓
Risk Tool 匹配器
    ↓
┌───────────┴───────────┐
│                       │
▼                       ▼
【Risk Tool】      【Safe Tool】
    │                       │
    ▼                       ▼
用户确认机制            直接执行
    │
┌───┴───┐
│       │
▼       ▼
【允许】 【拒绝】
    │       │
    ▼       ▼
执行工具  终止执行
```

---

## 📁 项目结构

```
ToolGuard/
├── README.md                          # 项目说明
├── config/
│   ├── risk_tool_list.json            # 危险工具列表
│   └── toolguard_config.yaml          # ToolGuard 配置
├── src/
│   ├── toolguard.py                   # 主程序
│   ├── toolguard_server.py            # Web 服务器
│   ├── tool_interceptor.py            # 工具拦截器（待实现）
│   ├── risk_matcher.py                # Risk Tool 匹配器（待实现）
│   ├── user_confirmation.py           # 用户确认机制（待实现）
│   ├── audit_logger.py                # 审计日志（待实现）
│   └── web_ui/
│       ├── index.html                 # Web 管理界面
│       └── app.js                     # 前端逻辑
├── hooks/
│   └── toolguard/
│       ├── HOOK.md                    # Hook 元数据
│       └── handler.js                 # Hook 处理器
├── logs/
│   ├── toolguard.log                  # 运行日志
│   └── audit.jsonl                    # 审计日志
└── start.sh                           # 启动脚本
```

---

## 🚀 快速开始

### 1. 安装依赖

```bash
# Python 依赖
pip3 install pyyaml

# 确保 OpenClaw 已安装
```

### 2. 启动 ToolGuard

```bash
cd ~/.openclaw/workspace/ToolGuard
./start.sh start
```

### 3. 验证服务

```bash
# 健康检查
curl http://127.0.0.1:8767/health

# 测试工具检查
python3 src/toolguard.py check message send '{"to":"test@example.com"}'
```

### 4. 访问 Web 界面

访问 http://127.0.0.1:8767 查看待确认请求和审计日志。

---

## ⚙️ 配置说明

### Risk Tool 列表 (config/risk_tool_list.json)

```json
{
  "risk_tools": [
    {
      "tool_name": "message",
      "action": "send",
      "risk_level": "high",
      "reason": "可能发送未授权消息",
      "require_confirmation": true
    }
  ],
  "safe_tools": [
    {
      "tool_name": "read",
      "reason": "读取文件（只读操作）"
    }
  ]
}
```

### 风险等级

| 等级 | 颜色 | 超时时间 | 说明 |
|------|------|---------|------|
| **low** | 🟢 | 自动放行 | 低风险，自动放行 |
| **medium** | 🟡 | 5 分钟 | 中风险，需要确认 |
| **high** | 🟠 | 5 分钟 | 高风险，需要确认 |
| **critical** | 🔴 | 10 分钟 | 严重风险，需要确认 |

---

## 🔧 使用示例

### CLI 命令

```bash
# 检查工具调用
python3 src/toolguard.py check message send '{"to":"test@example.com"}'

# 查看待处理确认
python3 src/toolguard.py pending

# 查看确认状态
python3 src/toolguard.py status <confirmation_id>
```

### API 调用

```bash
# 健康检查
curl http://127.0.0.1:8767/health

# 检查工具调用
curl -X POST http://127.0.0.1:8767/check \
  -H 'Content-Type: application/json' \
  -d '{"tool_name":"message","action":"send","parameters":{"to":"test@example.com"}}'

# 获取待处理确认
curl http://127.0.0.1:8767/api/pending

# 设置确认响应
curl -X POST http://127.0.0.1:8767/api/confirm \
  -H 'Content-Type: application/json' \
  -d '{"confirmation_id":"xxx","approved":true}'

# 获取审计日志
curl http://127.0.0.1:8767/api/audit
```

---

## 📊 测试场景

### 场景 1：发送邮件（需要确认）

```bash
curl -X POST http://127.0.0.1:8767/check \
  -H 'Content-Type: application/json' \
  -d '{"tool_name":"message","action":"send","parameters":{"to":"team@example.com","subject":"会议通知"}}'
```

**预期结果：**
```json
{
  "need_confirmation": true,
  "confirmation_id": "xxx",
  "message": "⚠️ 危险工具调用：message.send\n原因：可能发送未授权消息\n风险等级：high",
  "risk_level": "high"
}
```

### 场景 2：读取文件（无需确认）

```bash
curl -X POST http://127.0.0.1:8767/check \
  -H 'Content-Type: application/json' \
  -d '{"tool_name":"read","action":"*","parameters":{"path":"test.txt"}}'
```

**预期结果：**
```json
{
  "need_confirmation": false
}
```

---

## 🔗 OpenClaw Hook 集成

### 注册 Hook

在 OpenClaw 配置中添加：

```json
{
  "hooks": {
    "internal": {
      "entries": {
        "toolguard": {
          "enabled": true,
          "module": "~/.openclaw/workspace/ToolGuard/hooks/toolguard/handler.js"
        }
      }
    }
  }
}
```

### Hook 事件

ToolGuard 监听 `tool:call` 事件，在工具调用前拦截。

---

## 📝 审计日志

审计日志保存在 `~/.openclaw/workspace/ToolGuard/logs/audit.jsonl`，格式如下：

```json
{
  "timestamp": "2026-03-17T21:26:21.053",
  "confirmation_id": "xxx",
  "tool_name": "message",
  "action": "send",
  "parameters": {"to": "test@example.com"},
  "confirmed": true,
  "approved": true
}
```

---

## 🛠️ 故障排除

### 问题 1：服务无法启动

**检查日志：**
```bash
tail -f logs/toolguard.log
```

**常见原因：**
- 端口被占用
- 配置文件错误
- Python 依赖缺失

### 问题 2：Web 界面无法访问

**检查服务状态：**
```bash
./start.sh status
```

**检查防火墙：**
```bash
# macOS
sudo lsof -i :8767
```

### 问题 3：Hook 不工作

**检查 Hook 注册：**
```bash
openclaw hooks list | grep toolguard
```

**检查 Hook 日志：**
```bash
tail -f ~/.openclaw/logs/gateway.log | grep toolguard
```

---

## 🎯 开发计划

### 阶段 1：基础框架 ✅

- [x] 创建项目结构
- [x] 实现 ToolGuard 核心类
- [x] 创建 risk_tool_list.json
- [x] 实现基础日志系统

### 阶段 2：Hook 集成 ✅

- [x] 创建 OpenClaw Hook
- [x] 实现工具调用拦截
- [x] 实现用户确认机制
- [x] 测试基础功能

### 阶段 3：Web 界面 ✅

- [x] 创建 Web 管理界面
- [x] 实现待确认请求显示
- [x] 实现审计日志查看
- [x] 自动刷新功能

### 阶段 4：完善与测试 🚧

- [ ] 添加更多 Risk Tool
- [ ] 性能优化
- [ ] 完整测试
- [ ] 文档编写

### 阶段 5：高级功能

- [ ] 白名单机制
- [ ] 临时放行（本次会话有效）
- [ ] 通知系统（邮件/推送）
- [ ] 统计分析面板

---

## 📚 参考资料

- [OpenClaw Hooks 文档](https://docs.openclaw.ai/automation/hooks)
- [OpenClaw 工具系统](https://docs.openclaw.ai/tools)

---

## 📄 许可证

MIT License

---

## 🙏 致谢

感谢 OpenClaw 社区提供的 Hook 系统支持！
