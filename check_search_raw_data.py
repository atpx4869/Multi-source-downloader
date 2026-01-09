#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""检查搜索API返回的原始数据"""

import sys
import requests
sys.path.insert(0, '.')

from sources.http_search import call_api, find_rows

session = requests.Session()
session.trust_env = False
session.proxies = {"http": None, "https": None}

search_url = "https://std.samr.gov.cn/gb/search/gbQueryPage"
params = {
    "searchText": "5711",
    "pageNumber": 1,
    "pageSize": 20
}

print("搜索API: ", search_url)
print("参数:", params)
print("\n" + "="*80 + "\n")

j = call_api(session, 'GET', search_url, params=params, timeout=15)
rows = find_rows(j)

for row in rows:
    std_code = row.get("C_STD_CODE", "")
    if "5711-2015" in std_code:
        print("找到GB/T 5711-2015的原始数据：\n")
        import json
        print(json.dumps(row, indent=2, ensure_ascii=False))
        break
