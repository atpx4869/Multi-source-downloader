#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试GBW中GB/T 5711的搜索结果"""

from sources.gbw import GBWSource
from core.models import Standard

try:
    gbw = GBWSource()
    
    # 搜索GB/T 5711
    print("🔍 正在GBW中搜索: GB/T 5711...")
    results = gbw.search("GB/T 5711")
    
    if results:
        print(f"\n✅ 找到 {len(results)} 条结果:\n")
        for i, item in enumerate(results, 1):
            print(f"{i}. {item.std_no}")
            print(f"   名称: {item.name}")
            print(f"   有PDF: {item.has_pdf}")
            print(f"   发布: {item.publish}")
            print(f"   实施: {item.implement}")
            print(f"   状态: {item.status}")
            print(f"   来源Meta: {item.source_meta}")
            print()
            
            # 尝试下载该标准
            if isinstance(item, Standard):
                print(f"   尝试从GBW下载...")
                try:
                    path, logs = gbw.download(item, "downloads")
                    if path:
                        print(f"   ✅ 下载成功: {path}")
                    else:
                        print(f"   ❌ 下载失败")
                        if logs:
                            for log in logs[-5:]:
                                print(f"      ↳ {log}")
                except Exception as e:
                    print(f"   ❌ 下载异常: {e}")
            print()
    else:
        print("❌ 未找到任何结果")
        
except Exception as e:
    print(f"❌ 错误: {e}")
    import traceback
    traceback.print_exc()
