#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
诊断 QB/T 行业标准查询问题
"""
import sys
import time
import re

# Add project root to path
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from sources.zby import ZBYSource
from sources.zby_http import search_via_api
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# 测试标准号
test_standards = [
    "QB/T 2724-2005",
    "QB/T 4672-2014",
    "QB/T 4671-2014",
    "QB/T 5353-2018",
    "QB/T 5157-2017",
]

def setup_session():
    """创建会话"""
    session = requests.Session()
    session.trust_env = False
    retries = Retry(total=2, backoff_factor=0.3, status_forcelist=(500, 502, 503, 504))
    adapter = HTTPAdapter(max_retries=retries)
    session.mount('https://', adapter)
    session.mount('http://', adapter)
    return session

print("=" * 80)
print("🔍 QB/T 行业标准诊断")
print("=" * 80)

session = setup_session()

for std_no in test_standards:
    print(f"\n{'─' * 80}")
    print(f"📋 测试: {std_no}")
    print(f"{'─' * 80}")
    
    # 尝试多种关键词
    keywords_to_try = [std_no]
    if '/' in std_no or ' ' in std_no:
        keywords_to_try.append(std_no.replace('/', '').replace(' ', ''))
    if '-' in std_no:
        keywords_to_try.append(std_no.split('-')[0].strip())
    num_match = re.search(r'(\d+)', std_no)
    if num_match:
        keywords_to_try.append(num_match.group(1))
    
    keywords_to_try = list(dict.fromkeys(keywords_to_try))
    
    print(f"  尝试的关键词: {keywords_to_try}")
    
    for kw in keywords_to_try:
        print(f"\n  🔎 关键词: {kw}")
        try:
            rows = search_via_api(kw, page=1, page_size=20, session=session)
            print(f"     API 返回行数: {len(rows)}")
            
            if rows:
                # 检查过滤逻辑
                clean_keyword = re.sub(r'[^A-Z0-9]', '', kw.upper())
                print(f"     清理后关键词: {clean_keyword}")
                
                for i, row in enumerate(rows[:5]):  # 只显示前5个
                    raw_no = row.get('standardNumDeal') or row.get('standardNum') or ''
                    std_no_from_api = re.sub(r'<[^>]+>', '', raw_no).strip()
                    clean_api_no = re.sub(r'[^A-Z0-9]', '', std_no_from_api.upper())
                    
                    match = clean_keyword in clean_api_no or clean_api_no in clean_keyword
                    match_symbol = "✓" if match else "✗"
                    
                    name = row.get('standardName') or ''
                    print(f"       [{i+1}] {match_symbol} {std_no_from_api[:20]:20} | {clean_api_no[:15]:15} | {name[:30]}")
            
            time.sleep(0.5)  # 避免限流
        except Exception as e:
            print(f"     ❌ API 异常: {e}")
            break

print("\n" + "=" * 80)
print("测试完成")
print("=" * 80)
