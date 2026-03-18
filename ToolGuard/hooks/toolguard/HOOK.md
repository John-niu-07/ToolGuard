---
name: toolguard
description: "ToolGuard - OpenClaw 工具调用监控系统，拦截危险工具调用并请求用户确认"
metadata:
  {
    "openclaw":
      {
        "emoji": "🛡️",
        "events": ["tool:call"],
        "install": [{ "id": "toolguard", "kind": "local", "label": "Local hook" }],
      },
  }
requires:
  bins:
    - "node"
---

# ToolGuard Hook

OpenClaw 工具调用监控 Hook - 在工具调用前拦截并请求用户确认。

## 功能

- **危险工具拦截** - 拦截 risk tool 列表中定义的危险工具
- **用户确认机制** - 在危险工具调用前请求用户确认
- **审计日志** - 完整记录所有工具调用和确认
- **风险等级** - 根据风险等级设置不同的超时时间

## 配置

编辑 `~/.openclaw/workspace/ToolGuard/config/risk_tool_list.json` 调整危险工具列表。

## 服务管理

```bash
cd ~/.openclaw/workspace/ToolGuard
./start.sh start   # 启动
./start.sh stop    # 停止
./start.sh status  # 状态
```

## Web 管理界面

访问 http://127.0.0.1:8767 查看待确认请求和审计日志。

## Fail-Open

如果 ToolGuard 服务不可用，工具调用会被放行（不影响正常使用）。
