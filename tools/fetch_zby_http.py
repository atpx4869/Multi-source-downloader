import requests

base = 'https://bz.zhenggui.vip'
paths = ['/standardList', '/search', '/api/search', '/']
headers = {"User-Agent": "Mozilla/5.0", "Referer": base}
q = '测试'
for p in paths:
    url = base.rstrip('/') + p
    try:
        r = requests.get(url, params={"searchText": q, "q": q}, headers=headers, timeout=8)
        txt = r.text or ''
        print('URL:', url)
        print('STATUS:', r.status_code)
        print('LEN:', len(txt))
        print('SNIPPET:')
        print(txt[:1000])
        print('-' * 80)
    except Exception as e:
        print('URL:', url, 'ERROR:', e)
        print('-' * 80)
