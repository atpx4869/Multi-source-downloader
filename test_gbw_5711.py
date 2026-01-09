#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试GB/T 5711-2015的PDF检测"""

import sys
sys.path.insert(0, '.')

from sources.gbw import GBWSource

gbw = GBWSource()

print("="*80)
print("测试 GB/T 5711-2015")
print("="*80)

# 搜索5711
results = gbw.search("5711")

print(f"\n共找到 {len(results)} 条结果\n")

for std in results:
    if "2015" in std.std_no:
        print(f"标准号: {std.std_no}")
        print(f"状态: {std.status}")
        print(f"has_pdf: {std.has_pdf}")
        print(f"item_id: {std.source_meta.get('id', 'N/A')}")
        
        # 再次单独测试_check_pdf_available
        item_id = std.source_meta.get('id', '')
        if item_id:
            print(f"\n单独测试 _check_pdf_available('{item_id}')...")
            result = gbw._check_pdf_available(item_id)
            print(f"返回值: {result}")
            
            # 检查缓存
            if item_id in gbw._pdf_check_cache:
                print(f"缓存值: {gbw._pdf_check_cache[item_id]}")
        
        print("-"*80)
