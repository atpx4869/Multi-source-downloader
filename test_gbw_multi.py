#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试GBW中多个标准的has_pdf判定"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

from sources.gbw import GBWSource

try:
    gbw = GBWSource()
    
    test_keywords = ["GB/T 5711", "GB/T 3324"]
    
    for keyword in test_keywords:
        print(f"\n搜索: {keyword}")
        print("-" * 60)
        results = gbw.search(keyword)
        
        if results:
            for item in results[:3]:  # 只显示前3个
                print(f"标准号: {item.std_no}")
                print(f"  名称: {item.name}")
                print(f"  状态: {item.status}")
                print(f"  有文本: {item.has_pdf}")
                print()
        else:
            print("未找到结果\n")
        
except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()
