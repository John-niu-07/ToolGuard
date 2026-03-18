#!/bin/bash
# 测试邮件发送
cat <<EOF | himalaya message send 2>&1
To: zhenxingniu06@gmail.com
Subject: 测试 - exec 拦截测试

这是一封测试邮件，用于验证 ToolGuard 对 exec 的拦截功能。

发送时间：$(date)
EOF
