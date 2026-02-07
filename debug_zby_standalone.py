
import sys
import os
import json
import logging
import requests
from pathlib import Path

# Ensure sources can be imported
sys.path.append(os.getcwd())

from sources.zby_http import search_via_api

def debug_zby_search(keyword="GB/T 3324-2017"):
    print(f"--- Debugging ZBY Search for keyword: {keyword} ---")
    
    # 1. Search
    print(f"\n[1] Calling search_via_api...")
    session = requests.Session()
    # Mock browser headers
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Referer": "https://bz.zhenggui.vip",
        "Origin": "https://bz.zhenggui.vip"
    })
    
    try:
        results = search_via_api(keyword, session=session, timeout=10)
        print(f"Search returned {len(results)} raw rows.")
    except Exception as e:
        print(f"Search failed: {e}")
        return

    if not results:
        print("No results found.")
        return

    # 2. Inspect First Result
    first_row = results[0]
    print("\n[2] Inspecting First Result Metadata:")
    print(json.dumps(first_row, indent=2, ensure_ascii=False))
    
    # Check for standardId
    std_id = first_row.get('standardId')
    print(f"\nExtracted standardId: {std_id}")
    
    if not std_id:
        print("WARNING: standardId is missing!")
        # Check other potential ID fields
        potential_ids = {k: v for k, v in first_row.items() if 'id' in k.lower()}
        print(f"Other potential ID fields: {potential_ids}")

if __name__ == "__main__":
    import urllib3
    urllib3.disable_warnings()
    debug_zby_search()
