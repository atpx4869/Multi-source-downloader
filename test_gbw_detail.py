#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""检查GB/T 5711-2015的详情页内容"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

import requests

item_id = "71F772D80B21D3A7E05397BE0A0AB82A"
detail_url = f"https://std.samr.gov.cn/gb/search/gbDetailed?id={item_id}"

try:
    print(f"获取详情页: {detail_url}\n")
    resp = requests.get(detail_url, timeout=10)
    resp.encoding = 'utf-8'
    
    # 检查关键词
    keywords = [
        "本系统暂不提供在线阅读",
        "版权保护问题",
        "涉及版权保护",
        "暂不提供",
        "无预览权限",
        "不提供下载"
    ]
    
    print("检查版权限制关键词:")
    for kw in keywords:
        if kw in resp.text:
            print(f"  ✓ 找到: {kw}")
        else:
            print(f"  ✗ 未找到: {kw}")
    
    # 搜索PDF相关
    print("\n检查PDF相关内容:")
    if 'pdf' in resp.text.lower():
        print("  ✓ 页面包含 'pdf' 关键词")
        # 找出包含pdf的行
        for line in resp.text.split('\n'):
            if 'pdf' in line.lower() and len(line) < 200:
                print(f"    -> {line.strip()[:150]}")
    else:
        print("  ✗ 页面不包含 'pdf' 关键词")
    
    # 搜索下载按钮
    print("\n检查下载按钮:")
    if '下载' in resp.text or 'download' in resp.text.lower():
        print("  ✓ 页面包含下载相关内容")
    else:
        print("  ✗ 页面不包含下载相关内容")
        
except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()
