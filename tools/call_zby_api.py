import requests, json
url = "https://login.bz.zhenggui.vip/bzy-api/org/std/search?nonce=TjPXsF60-ZlYb-pLx2-HskI-8qG64WMj6RGL_1765966111275&signature=b9830ec9b3dd380c832b174422e47874"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Content-Type": "application/json;charset=UTF-8",
    "Origin": "https://bz.zhenggui.vip",
    "Referer": "https://bz.zhenggui.vip/",
}
body = {
  "params":{
    "pageNo":1,
    "pageSize":10,
    "model":{
      "standardNum":None,
      "standardName":None,
      "standardType":None,
      "standardCls":None,
      "keyword":"3324",
      "forceEffective":"0",
      "standardStatus":None,
      "searchType":"1",
      "standardPubTimeType":"0"
    }
  },
  "token":"",
  "userId":"",
  "orgId":"",
  "time":"2025-12-17 18:08:31"
}
try:
    r = requests.post(url, headers=headers, json=body, timeout=15)
    print('STATUS:', r.status_code)
    text = r.text or ''
    print('LENGTH:', len(text))
    # try to print JSON prettified if possible
    try:
        j = r.json()
        import pprint
        pprint.pprint(j)
    except Exception:
        print('TEXT SNIPPET:')
        print(text[:2000])
except Exception as e:
    print('REQUEST ERROR:', e)
