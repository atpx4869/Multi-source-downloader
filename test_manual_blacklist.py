#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""手动测试：将GB/T 5711-2015加入缓存黑名单"""

import sys
sys.path.insert(0, '.')

from sources.gbw import GBWSource

# 手动加入黑名单
item_id = "71F772D80B21D3A7E05397BE0A0AB82A"
GBWSource._pdf_check_cache[item_id] = False

print(f"✓ 已将 {item_id} 加入缓存黑名单\n")
print("现在搜索5711，应该显示无文本...\n")

# 搜索测试
gbw = GBWSource()
results = gbw.search("5711")

for std in results:
    if "2015" in std.std_no:
        print(f"标准号: {std.std_no}")
        print(f"状态: {std.status}")
        print(f"has_pdf: {std.has_pdf}")
        print(f"来源: GBW")
        
        if not std.has_pdf:
            print("\n✅ 成功！已标记为无文本")
        else:
            print("\n❌ 失败！仍显示有文本")
        break
