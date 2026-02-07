"""
Test script to check for download button on GBW detail page (no BS4)
"""
import requests
import re

def check_download_availability(hcno):
    """Check if a standard has downloadable PDF"""
    url = f"https://openstd.samr.gov.cn/bzgk/std/newGbInfo?hcno={hcno}"
    
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        html = resp.text
        
        # Look for download button with class="xz_btn"
        download_btn_pattern = r'<button[^>]*class="[^"]*xz_btn[^"]*"[^>]*>下载标准</button>'
        has_download = bool(re.search(download_btn_pattern, html))
        
        # Look for preview button
        preview_btn_pattern = r'<button[^>]*class="[^"]*ck_btn[^"]*"[^>]*>在线预览</button>'
        has_preview = bool(re.search(preview_btn_pattern, html))
        
        # Get status
        status_pattern = r'<span[^>]*class="[^"]*text-success[^"]*"[^>]*>\s*([^<]+)\s*</span>'
        status_match = re.search(status_pattern, html)
        status = status_match.group(1).strip() if status_match else "未知"
        
        print(f"HCNO: {hcno}")
        print(f"URL: {url}")
        print(f"状态: {status}")
        print(f"预览按钮: {'✓' if has_preview else '✗'}")
        print(f"下载按钮: {'✓' if has_download else '✗'}")
        
        return has_download
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

# Test with known standards
print("=" * 60)
print("Test 1: GB/T 3324-2024 (现行 - should have download)")
print("=" * 60)
has_pdf_1 = check_download_availability("96019B083A5A59FC7F84895DFFE7500B")

print("\n" + "=" * 60)
print("Test 2: Find an old/obsolete standard without download")
print("=" * 60)
# Try to find a standard that's obsolete
from sources.gbw import GBWSource
source = GBWSource()
results = source.search("GB/T 3324-2008")  # Old version, likely obsolete
if results:
    print(f"Found: {results[0].std_no} - {results[0].name}")
    print(f"Status: {results[0].source_meta.get('status', 'N/A')}")
