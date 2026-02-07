import hashlib
import time
import random
import requests
import json
import urllib3
import re

urllib3.disable_warnings()

# --- Reversed JS Logic ---

ORIGIN_CHARS = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"

def get_random(t="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"):
    res = []
    for char in t:
        if char == 'x':
            res.append(ORIGIN_CHARS[int(random.random() * len(ORIGIN_CHARS))])
        else:
            res.append(char)
    return "".join(res)

def get_md5(s):
    return hashlib.md5(s.encode('utf-8')).hexdigest()

def get_nonce():
    t = get_random()
    e = int(time.time() * 1000)
    return {"nonce": f"{t}_{e}", "timeStamp": e}

def get_signature(nonce, timestamp, slot):
    raw = f"{timestamp}_{nonce}_{slot}"
    return get_md5(raw)

def get_request_must_params(slot="zby_org"):
    n = get_nonce()
    nonce = n['nonce']
    timestamp = n['timeStamp']
    signature = get_signature(nonce, timestamp, slot)
    return {"nonce": nonce, "signature": signature}

def test_api(std_id):
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Content-Type": "application/json;charset=UTF-8",
        "Origin": "https://bz.zhenggui.vip",
        "Referer": f"https://bz.zhenggui.vip/standardDetail?standardId={std_id}&docStatus=0"
    })
    session.verify = False
    
    endpoints = [
        "/bzy-api/org/std/resource",
        "/bzy-api/org/std/preview",
        "/bzy-api/org/standard/getPdfList",
        "/bzy-api/org/std/getDetail"
    ]
    
    # Common payload
    payload = {
        "params": str(std_id),
        "token": "",
        "userId": "",
        "orgId": ""
    }
    
    # Also test another payload structure
    payload_obj = {
        "params": {
            "standardId": str(std_id)
        },
        "token": "",
        "userId": "",
        "orgId": ""
    }
    
    for ep in endpoints:
        url = f"https://login.bz.zhenggui.vip{ep}"
        query_params = get_request_must_params("zby_org")
        
        print(f"\n--- Testing Endpoint: {ep} ---")
        try:
            # Try both payload types
            for p in [payload, payload_obj]:
                print(f"Testing with payload type: {'string' if isinstance(p['params'], str) else 'object'}")
                r = session.post(url, params=query_params, json=p, timeout=10)
                if r.status_code == 200:
                    data = r.json()
                    if data.get("data") and (isinstance(data["data"], list) and len(data["data"]) > 0 or isinstance(data["data"], dict) and data["data"]):
                        print(f"[FOUND DATA] {ep}")
                        print(json.dumps(data, indent=2, ensure_ascii=False))
                        break
                    else:
                        print(f"Status: {r.status_code}, data is empty")
                else:
                    print(f"Status: {r.status_code}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    # Test with failing ID (GB/T 10357.4-2023)
    test_api(528255)
