#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""查看GB/T 5711-2015详情页内容"""

import sys
import requests
sys.path.insert(0, '.')

item_id = "71F772D80B21D3A7E05397BE0A0AB82A"

session = requests.Session()
session.trust_env = False
session.proxies = {"http": None, "https": None}

for base in ["https://std.samr.gov.cn", "https://openstd.samr.gov.cn"]:
    detail_url = f"{base}/gb/search/gbDetailed?id={item_id}"
    print(f"\n访问: {detail_url}")
    
    resp = session.get(detail_url, timeout=10)
    if resp.status_code != 200:
        print(f"状态码: {resp.status_code}")
        continue
    
    resp.encoding = 'utf-8'
    text = resp.text
    
    print(f"\n页面长度: {len(text)} 字符")
    
    # 检查关键标记
    print("\n=== 关键标记检测 ===")
    print(f"ck_btn: {'✓' if 'ck_btn' in text else '✗'}")
    print(f"xz_btn: {'✓' if 'xz_btn' in text else '✗'}")
    print(f"openpdf: {'✓' if 'openpdf' in text else '✗'}")
    print(f"pdfPreview: {'✓' if 'pdfPreview' in text else '✗'}")
    
    # 检查黑名单关键词
    print("\n=== 黑名单关键词检测 ===")
    keywords = [
        "本系统暂不提供在线阅读",
        "版权保护问题",
        "涉及版权保护",
        "暂不提供",
        "无预览权限",
        "不提供下载",
        "购买正式出版物",
        "需要购买",
        "已下架",
        "您所查询的标准系统尚未收录",
        "将在发布后20个工作日内公开",
        "陆续完成公开",
        "标准废止"
    ]
    
    for kw in keywords:
        if kw in text:
            print(f"✓ 发现: {kw}")
    
    # 查找"废止"相关内容
    print("\n=== 搜索'废止'关键词 ===")
    import re
    废止_matches = re.findall(r'.{0,30}废止.{0,30}', text)
    for match in 废止_matches[:5]:
        print(f"  {match.strip()}")
    
    # 查找状态相关
    print("\n=== 搜索状态标记 ===")
    状态_matches = re.findall(r'标准状态[：:].{0,50}', text)
    for match in 状态_matches:
        print(f"  {match.strip()}")
    
    break
