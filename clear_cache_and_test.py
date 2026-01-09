#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""清空缓存并测试"""

import sys
sys.path.insert(0, '.')

from sources.gbw import GBWSource

# 清空所有缓存
print("清空缓存前:")
print(f"  PDF缓存: {len(GBWSource._pdf_check_cache)} 项")
print(f"  HCNO缓存: {len(GBWSource._hcno_cache)} 项")

GBWSource._pdf_check_cache.clear()
GBWSource._hcno_cache.clear()

print("\n清空缓存后:")
print(f"  PDF缓存: {len(GBWSource._pdf_check_cache)} 项")
print(f"  HCNO缓存: {len(GBWSource._hcno_cache)} 项")

print("\n" + "="*80)
print("测试 GB/T 5711 搜索")
print("="*80)

import time
gbw = GBWSource()

start = time.time()
results = gbw.search("5711")
elapsed = time.time() - start

print(f"\n搜索耗时: {elapsed:.2f}秒")
print(f"共找到 {len(results)} 条结果\n")

for std in results:
    print(f"标准号: {std.std_no}")
    print(f"状态: {std.status}")
    print(f"has_pdf: {std.has_pdf} {'✓' if std.has_pdf else '✗'}")
    print("-"*80)

print(f"\n缓存状态:")
print(f"  PDF缓存: {len(GBWSource._pdf_check_cache)} 项")
print(f"  HCNO缓存: {len(GBWSource._hcno_cache)} 项")
