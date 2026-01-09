#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试GBW中GB/T 5711的搜索"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

from sources.gbw import GBWSource

try:
    gbw = GBWSource()
    
    # 搜索GB/T 5711
    print("正在GBW中搜索: GB/T 5711...")
    results = gbw.search("GB/T 5711")
    
    if results:
        print(f"\n找到 {len(results)} 条结果:\n")
        for i, item in enumerate(results, 1):
            print(f"{i}. {item.std_no}")
            print(f"   名称: {item.name}")
            print(f"   有PDF: {item.has_pdf}")
            print(f"   来源Meta: {item.source_meta}")
            
except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()
