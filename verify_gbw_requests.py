
import sys
import os
import requests
import json
import time
from pathlib import Path
sys.path.insert(0, os.getcwd())

from sources.gbw import GBWSource

def main():
    source = GBWSource()
    
    # 1. Search
    keyword = "GB/T 3324-2024" 
    print(f"Searching for {keyword}...")
    items = source.search(keyword)
    
    if not items:
        print("No items found.")
        return

    item = items[0]
    print(f"Found: {item.std_no} - {item.name}")
    print(f"Meta: {item.source_meta}")
    
    hcno = item.source_meta.get("hcno")
    if not hcno:
        print("HCNO not in meta, fetching...")
        hcno = source._get_hcno(item.source_meta.get("id"))
        print(f"Got HCNO: {hcno}")
        
    if not hcno:
        print("Failed to get HCNO.")
        return
        
    # 2. Check info API
    url = f"https://openstd.samr.gov.cn/bzgk/gb/newGbInfo?hcno={hcno}"
    print(f"Checking Info API: {url}")
    try:
        r = requests.get(url, timeout=10, verify=False)
        print(f"Status: {r.status_code}")
        print(f"Response: {r.text[:2000]}") # Print first 2000 chars
    except Exception as e:
        print(f"Info API failed: {e}")

    # 3. Test openstd base and inspect cookie/content
    new_base = "https://openstd.samr.gov.cn"
    show_url = f"{new_base}/bzgk/gb/showGb?type=online&hcno={hcno}"
    print(f"Testing new show_url: {show_url}")
    
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
    
    try:
        r = session.get(show_url, timeout=10, verify=False)
        print(f"Status: {r.status_code}")
        print(f"Final URL: {r.url}")  # Check for redirect
        print(f"Cookies: {session.cookies.get_dict()}")
        
        # Check if we are on the right page
        with open("show_debug.html", "wb") as f:
            f.write(r.content)
        print("Saved show_debug.html")

        if "标准号" in r.text or "在线预览" in r.text or "Code" in r.text:
            print("Page content looks correct.")
        else:
            print("Page content SUSPICIOUS.")

        if r.status_code == 200:
            print("openstd working! We should use this base.")
            
        # NOW try to fetch captcha with THIS session
        captcha_url = f"{new_base}/bzgk/gb/gc?_{int(time.time()*1000)}"
        print(f"Fetching captcha with session...")
        r_cap = session.get(captcha_url, headers={"Referer": show_url}, verify=False)
        print(f"Captcha Content-Type: {r_cap.headers.get('Content-Type')}")
        if 'image' in r_cap.headers.get('Content-Type', ''):
             print("Captcha IS AN IMAGE!")
        else:
             print("Captcha is NOT an image.")
             
    except Exception as e:
        print(f"openstd failed: {e}")

    # 4. Attempt Download (Pure Requests)
    from sources.gbw_download import download_with_ocr
    # Monkeypatch BASE in sys.modules if possible, or just print result 
    import sources.gbw_download
    sources.gbw_download.BASE = "https://openstd.samr.gov.cn"
    sources.gbw_download.CAPTCHA_URL = f"{new_base}/bzgk/gb/gc"
    sources.gbw_download.VERIFY_URL = f"{new_base}/bzgk/gb/verifyCode"
    sources.gbw_download.VIEW_URL = f"{new_base}/bzgk/gb/viewGb"

    out_path = Path("gbw_test.pdf")
    print(f"Attempting download_with_ocr to {out_path} with NEW BASE...")
    
    session = requests.Session()
    # Mock headers as in gbw_download.py
    session.headers.update({"User-Agent": "Mozilla/5.0"})
    
    success = download_with_ocr(hcno, out_path, session=session, verbose=True)
    if success:
        print("Download SUCCESS via openstd!")
    else:
        print("Download FAILED via openstd.")

if __name__ == "__main__":
    main()
