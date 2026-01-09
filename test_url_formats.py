#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试访问不同URL格式"""

import sys
import requests
sys.path.insert(0, '.')

from sources.gbw import GBWSource

gbw = GBWSource()

# 搜索获取HCNO
results = gbw.search("5711")
for std in results:
    if "2015" in std.std_no:
        item_id = std.source_meta.get('id', '')
        hcno = std.source_meta.get('hcno', '')
        
        print(f"标准: {std.std_no}")
        print(f"item_id: {item_id}")
        print(f"HCNO: {hcno}")
        print("\n" + "="*80)
        
        # 测试不同URL
        urls = [
            f"https://openstd.samr.gov.cn/bzgk/gb/newGbInfo?hcno={hcno}",
            f"https://std.samr.gov.cn/gb/search/gbDetailed?id={item_id}",
        ]
        
        for url in urls:
            print(f"\n访问: {url}")
            try:
                resp = gbw.session.get(url, timeout=10)
                if resp.status_code == 200:
                    resp.encoding = 'utf-8'
                    text = resp.text
                    print(f"状态码: {resp.status_code}")
                    print(f"页面长度: {len(text)}")
                    
                    # 检查关键词
                    keywords = [
                        "本系统暂不提供在线阅读",
                        "版权保护问题",
                        "购买正式标准出版物",
                        "联系中国标准出版社",
                    ]
                    
                    found = []
                    for kw in keywords:
                        if kw in text:
                            found.append(kw)
                    
                    if found:
                        print(f"✓ 找到黑名单关键词: {', '.join(found)}")
                    else:
                        print("✗ 未找到黑名单关键词")
                        
                        # 检查按钮
                        if 'openpdf' in text:
                            print("  但有 openpdf 标记")
                else:
                    print(f"状态码: {resp.status_code}")
            except Exception as e:
                print(f"错误: {e}")
        
        break
