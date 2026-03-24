---
name: auto-task-monitor
description: "ToolGuard 自动任务监控 - 在用户输入任务指令时自动启动任务监控"
metadata:
  {
    "openclaw":
      {
        "emoji": "📋",
        "events": ["message:received"],
        "install": [{ "id": "auto-task-monitor", "kind": "local", "label": "Local hook" }],
      },
  }
requires:
  bins:
    - "python3"
---

# ToolGuard 自动任务监控 Hook

在 OpenClaw 收到用户消息时，自动分析并启动任务监控。

## 功能

- **自动任务识别**: 检测用户消息中的任务指令
- **自动启动监控**: 识别到任务后自动启动 ToolGuard 任务监控
- **智能过滤**: 避免重复启动（已在监控中时不重复启动）

## 任务关键词

支持的 task 关键词：
- 邮件相关：发送邮件、查阅邮件、回复邮件、转发邮件
- 天气查询：查询天气、查看天气
- 文件操作：删除文件、创建文件、写入文件、上传文件、下载文件
- 代码管理：推送代码、提交代码、拉取代码
- 网络请求：搜索、查找、打开网页、访问网站
- 远程连接：ssh、连接、复制文件
- 系统管理：配置、设置、定时、cron

## 使用示例

**用户输入：**
```
发送天气预报邮件到 zhenxingniu06@gmail.com
```

**自动启动：**
```
📋 ToolGuard 自动任务监控已启动：发送天气预报邮件到 zhenxingniu06@gmail.com
   备选工具集：mail-send, himalaya, gog, message, web_search, web_fetch, exec
```

## 安装

```bash
cd ~/.openclaw/workspace/ToolGuard
openclaw hooks enable auto-task-monitor
```

## 禁用

```bash
openclaw hooks disable auto-task-monitor
```

## 测试

```bash
python3 src/auto_task_monitor.py "发送天气预报邮件到 test@example.com"
```
