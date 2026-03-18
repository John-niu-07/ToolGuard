#!/usr/bin/env python3
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# 邮件配置
from_addr = "3220628278@qq.com"
to_addr = "zhenxingniu@gmail.com"
subject = "近三天邮件摘要"

# 邮件摘要内容
body = """【近三天邮件摘要】

共收到 2 封未读邮件：

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📧 邮件 1
• 发件人：Niu Zhen Xing <zhenxingniu06@gmail.com>
• 主题：咨询邮件
• 日期：2026-03-11 01:46-07:00
• 内容：
  测试：
  Extension Gateway    ws://127.0.0.1:18789 或 http://127.0.0.1:18789
  Gateway Token    2ed7a6a45f04ba97751538312b16effc41bccf4c42865ea5

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📧 邮件 2
• 发件人：John Nash <zhenxingniu@gmail.com>
• 主题：testing
• 日期：2026-03-11 16:41+08:00
• 内容：
  测试：
  Extension Gateway    ws://127.0.0.1:18789 或 http://127.0.0.1:18789
  Gateway Token    2ed7a6a45f04ba97751538312b16effc41bccf4c42865ea5

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

【摘要说明】
• 时间范围：2026-03-09 至 2026-03-11（近三天）
• 邮件总数：2 封
• 主要发件人：Niu Zhen Xing、John Nash
• 内容类型：测试邮件（OpenClaw 配置信息）

---
此邮件由 OpenClaw 自动处理并生成
"""

# 创建邮件
msg = MIMEMultipart()
msg['From'] = from_addr
msg['To'] = to_addr
msg['Subject'] = subject
msg.attach(MIMEText(body, 'plain', 'utf-8'))

# 发送邮件
try:
    server = smtplib.SMTP_SSL("smtp.qq.com", 465)
    server.login("3220628278@qq.com", "iyfskbhwqiqwdedb")
    server.sendmail(from_addr, to_addr, msg.as_string())
    server.quit()
    print("邮件发送成功！")
except Exception as e:
    print(f"发送失败：{e}")
