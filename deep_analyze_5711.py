#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""深度分析GB/T 5711-2015详情页"""

import sys
import requests
sys.path.insert(0, '.')

item_id = "71F772D80B21D3A7E05397BE0A0AB82A"

session = requests.Session()
session.trust_env = False
session.proxies = {"http": None, "https": None}

detail_url = f"https://std.samr.gov.cn/gb/search/gbDetailed?id={item_id}"
print(f"访问: {detail_url}\n")

resp = session.get(detail_url, timeout=10)
resp.encoding = 'utf-8'
text = resp.text

# 查找所有可能表示"无文本"的关键词
print("=== 搜索可能的无文本标记 ===\n")

keywords_to_search = [
    "不提供", "无法", "无在线", "无预览", "无文本", "无标准",
    "版权", "限制", "保护", "购买", "收费",
    "暂不", "尚未", "待", "即将",
    "废止", "作废", "替代",
    "错误", "异常", "失败"
]

found_keywords = []
for kw in keywords_to_search:
    if kw in text:
        # 找到包含该关键词的上下文
        import re
        matches = re.findall(f'.{{0,40}}{re.escape(kw)}.{{0,40}}', text)
        if matches:
            found_keywords.append(kw)
            print(f"✓ 发现 '{kw}':")
            for match in matches[:3]:  # 只显示前3个
                clean = ' '.join(match.split())
                print(f"  {clean}")
            print()

if not found_keywords:
    print("未发现明显的无文本标记\n")

# 查找按钮和链接
print("=== 按钮和链接分析 ===\n")
print(f"在线预览按钮 (ck_btn): {'✓' if 'ck_btn' in text else '✗'}")
print(f"下载按钮 (xz_btn): {'✓' if 'xz_btn' in text else '✗'}")
print(f"openpdf链接: {'✓' if 'openpdf' in text else '✗'}")
print(f"pdfPreview: {'✓' if 'pdfPreview' in text else '✗'}")

# 查找openpdf的具体链接
import re
openpdf_matches = re.findall(r'openpdf[^"\'<>]{0,100}', text)
if openpdf_matches:
    print("\nopenpdf链接详情:")
    for match in openpdf_matches[:2]:
        print(f"  {match}")

# 查找页面中的提示信息
print("\n=== 提示信息 ===\n")
提示_patterns = [
    r'<div[^>]*class="[^"]*提示[^"]*"[^>]*>([^<]+)</div>',
    r'<span[^>]*class="[^"]*提示[^"]*"[^>]*>([^<]+)</span>',
    r'<p[^>]*class="[^"]*提示[^"]*"[^>]*>([^<]+)</p>',
    r'提示[：:]\s*([^<\n]{10,100})',
]

for pattern in 提示_patterns:
    matches = re.findall(pattern, text)
    for match in matches[:3]:
        print(f"  {match.strip()}")

# 检查是否有JavaScript禁用PDF的代码
print("\n=== JavaScript检查 ===\n")
if 'disabled' in text.lower() and 'pdf' in text.lower():
    print("✓ 发现disabled和pdf相关代码")
    disabled_matches = re.findall(r'.{0,50}disabled.{0,50}pdf.{0,50}', text, re.IGNORECASE)
    for match in disabled_matches[:2]:
        print(f"  {' '.join(match.split())}")
