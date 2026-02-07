
import requests
import json
import urllib3

urllib3.disable_warnings()

BASE_URL = "https://login.bz.zhenggui.vip/bzy-api"
STD_ID = "443847"
STD_NO = "GB/T 3324-2017"

ENDPOINTS = [
    "org/std/detail",
    "std/detail",
    "org/std/getDetail",
    "std/getDetail",
    "org/std/resource",
    "std/resource", 
    "org/std/preview",
    "std/preview",
    "org/std/getDocInfo",
    "std/getDocInfo",
    "org/std/fullText",
    "std/fullText",
    "standard/download",
    "std/download"
]

PAYLOADS = [
    {"standardId": STD_ID},
    {"id": STD_ID},
    {"params": {"standardId": STD_ID}},
    {"params": {"model": {"standardId": STD_ID}}},
    {"standardNum": STD_NO},
    {"params": {"standardNum": STD_NO}},
]

def bruteforce():
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Referer": "https://bz.zhenggui.vip",
        "Content-Type": "application/json;charset=UTF-8"
    })

    print(f"--- BRUTE FORCE ZBY API (ID={STD_ID}, NO={STD_NO}) ---")

    for ep in ENDPOINTS:
        url = f"{BASE_URL}/{ep}"
        print(f"\n[TESTING] {url}")
        
        for i, payload in enumerate(PAYLOADS):
            try:
                # Add common fields
                p = payload.copy()
                if "params" not in p:
                    p["token"] = ""
                    p["userId"] = ""
                    p["orgId"] = ""
                
                r = session.post(url, json=p, verify=False, timeout=5)
                print(f"  Payload {i}: Status={r.status_code}, Len={len(r.text)}")
                
                if r.status_code == 200 and len(r.text) > 0:
                    try:
                        j = r.json()
                        # Clean print
                        s = json.dumps(j, ensure_ascii=False)
                        if len(s) > 500: s = s[:500] + "..."
                        print(f"    RESPONSE: {s}")
                        
                        # Check for UUID
                        if "immdoc" in s or "uuid" in s.lower() or "fileid" in s.lower():
                            print("    !!! POTENTIAL MATCH FOUND !!!")
                    except:
                        print(f"    Text: {r.text[:200]}...")
            except Exception as e:
                print(f"  Error: {e}")

if __name__ == "__main__":
    bruteforce()
