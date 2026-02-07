
import requests
import json

def debug_gbw_search():
    url = "http://c.gb688.cn/gb/search/gbQueryPage"
    params = {
        "searchText": "25686-2018",
        "page": 1,
        "pageSize": 10
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "http://c.gb688.cn/bzgk/gb/index"
    }
    
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            print(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            print(resp.text[:500])
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_gbw_search()
