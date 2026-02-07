# -*- coding: utf-8 -*-
import hashlib
import time
import random
import requests
import json
import urllib3
import re
from pathlib import Path

urllib3.disable_warnings()

# --- 1. Reversed Signature Logic ---
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

def search_api(kw):
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0",
        "Content-Type": "application/json;charset=UTF-8",
        "Referer": "https://bz.zhenggui.vip",
    })
    url = "https://login.bz.zhenggui.vip/bzy-api/org/std/search"
    body = {
        "params": {
            "pageNo": 1,
            "pageSize": 20,
            "model": {
                "keyword": kw,
                "forceEffective": "0",
            },
        },
        "token": "", "userId": "", "orgId": "", "time": "",
    }
    query_params = get_request_must_params("zby_org")
    r = session.post(url, params=query_params, json=body, timeout=10)
    if r.status_code == 200:
        return r.json()
    return None

if __name__ == "__main__":
    kw = "GB/T 10357.4-2023"
    res = search_api(kw)
    print(json.dumps(res, indent=2, ensure_ascii=False))
