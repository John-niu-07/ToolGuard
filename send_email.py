#!/usr/bin/env python3
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# 邮件配置
from_addr = "3220628278@qq.com"
to_addr = "zhenxingniu@gmail.com"
subject = "最新邮件内容总结"

# 邮件正文
body = """发件人：John Nash <zhenxingniu@gmail.com>
收件人：3220628278@qq.com
主题：查询
日期：2026-03-06 21:54+08:00

【邮件内容总结】

这是一封研究请求邮件，主要内容：

1. **研究主题**：中东地区地缘政治动态
2. **重点关注**：美国与伊朗之间的近期互动
3. **时间范围**：2024-2026 年
4. **请求内容**：通过搜索引擎查找可靠新闻来源或分析文章

【建议后续行动】
- 使用 web_search 搜索相关新闻和分析
- 整理可靠来源的链接
- 提供地缘政治分析摘要

---
此邮件由 OpenClaw 自动处理并转发
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
