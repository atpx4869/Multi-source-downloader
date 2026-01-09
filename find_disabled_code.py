#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""查找disabled相关的JavaScript代码"""

import sys
import requests
import re
sys.path.insert(0, '.')

item_id = "71F772D80B21D3A7E05397BE0A0AB82A"

session = requests.Session()
session.trust_env = False
session.proxies = {"http": None, "https": None}

detail_url = f"https://std.samr.gov.cn/gb/search/gbDetailed?id={item_id}"
resp = session.get(detail_url, timeout=10)
resp.encoding = 'utf-8'
text = resp.text

print("=== 查找disabled和openpdf相关代码 ===\n")

# 搜索包含disabled和openpdf的代码块
matches = re.findall(r'.{0,200}(?:disabled|disable).{0,200}(?:openpdf|pdf|预览|下载).{0,200}', text, re.IGNORECASE)
for i, match in enumerate(matches[:5], 1):
    clean = ' '.join(match.split())
    print(f"{i}. {clean}\n")

print("\n=== 查找openpdf函数调用 ===\n")
openpdf_calls = re.findall(r'openpdf\([^)]*\)', text, re.IGNORECASE)
for call in openpdf_calls[:5]:
    print(f"  {call}")

print("\n=== 查找PDF相关的条件判断 ===\n")
if_patterns = re.findall(r'if\s*\([^)]*(?:pdf|openpdf|预览)[^)]*\)\s*\{[^}]{0,200}\}', text, re.IGNORECASE)
for i, pattern in enumerate(if_patterns[:3], 1):
    clean = ' '.join(pattern.split())
    print(f"{i}. {clean}\n")

# 查找是否有HCNO为空的判断
print("\n=== 查找HCNO相关判断 ===\n")
hcno_matches = re.findall(r'.{0,100}HCNO.{0,100}', text)
for match in hcno_matches[:5]:
    clean = ' '.join(match.split())
    if 'null' in clean.lower() or 'empty' in clean.lower() or '空' in clean or '==' in clean:
        print(f"  {clean}")

# 查找侧边栏按钮相关
print("\n=== 查找侧边栏PDF按钮 ===\n")
sidebar_matches = re.findall(r'sidebar-btn[^<]{0,200}', text)
for match in sidebar_matches[:8]:
    clean = ' '.join(match.split())
    if 'pdf' in clean.lower() or 'open' in clean.lower():
        print(f"  {clean}")
