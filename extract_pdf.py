#!/usr/bin/env python3
"""
提取 PDF 内容并翻译成中文
"""

import sys
sys.path.insert(0, '/Users/mike/.openclaw/workspace/openclaw-safety-guard/venv/lib/python3.14/site-packages')

from pypdf import PdfReader
import os

pdf_path = '/Users/mike/.openclaw/workspace/hint-mlwe-paper.pdf'
output_path = '/Users/mike/.openclaw/workspace/hint-mlwe-paper-zh.txt'

print("正在读取 PDF...")
reader = PdfReader(pdf_path)

print(f"总页数：{len(reader.pages)}")

# 提取前 5 页（摘要和引言）
extracted_text = []

for i, page in enumerate(reader.pages[:5]):
    text = page.extract_text()
    extracted_text.append(f"=== 第 {i+1} 页 ===\n{text}")
    print(f"已提取第 {i+1} 页")

# 保存提取的文本
with open(output_path, 'w', encoding='utf-8') as f:
    f.write("\n\n".join(extracted_text))

print(f"\n提取完成！保存到：{output_path}")
print(f"文件大小：{os.path.getsize(output_path)} bytes")
