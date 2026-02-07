
import requests
import re

def debug_restriction_detection():
    # GB/T 25686-2018 hcno
    hcno = "AEE9AE24536847F4D1C1EC9F171ACA80"
    
    bases = [
        "http://c.gb688.cn",
        "https://openstd.samr.gov.cn"
    ]
    
    paths = [
        "/bzgk/gb/newGbInfo",
        "/bzgk/std/newGbInfo",
        "/bzgk/gb/showGb",
        "/bzgk/std/showGb"
    ]
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://std.samr.gov.cn/"
    }
    
    for base in bases:
        for path in paths:
            url = f"{base}{path}?hcno={hcno}"
            print(f"\nChecking: {url}")
            try:
                resp = requests.get(url, headers=headers, timeout=10)
                print(f"Status: {resp.status_code}")
                if resp.status_code == 200:
                    text = resp.text
                    print(f"Length: {len(text)}")
                    if "版权保护" in text:
                        print("FOUND: '版权保护'")
                    if "在线阅读服务" in text:
                        print("FOUND: '在线阅读服务'")
                    if "下载标准" in text:
                        print("FOUND: '下载标准'")
                    if "xz_btn" in text:
                        print("FOUND: 'xz_btn'")
                else:
                    print(f"Error Body: {resp.text[:100]}")
            except Exception as e:
                print(f"Error: {e}")

if __name__ == "__main__":
    debug_restriction_detection()
