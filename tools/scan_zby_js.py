import re
import requests
from urllib.parse import urljoin

base = 'https://bz.zhenggui.vip/'
r = requests.get(base, headers={"User-Agent":"Mozilla/5.0"}, timeout=8)
html = r.text or ''
print('root len', len(html))

scripts = re.findall(r'<script[^>]+src=["\']([^"\']+)["\']', html, re.I)
print('found scripts:', scripts)

candidates = set()
for s in scripts:
    url = urljoin(base, s)
    try:
        rr = requests.get(url, headers={"User-Agent":"Mozilla/5.0"}, timeout=8)
        txt = rr.text or ''
        for pat in ['/api/', 'search', 'standardList', 'get', 'post', 'fetch(', 'axios']:
            if pat in txt:
                idx = txt.find(pat)
                start = max(0, idx-80)
                end = min(len(txt), idx+120)
                snippet = txt[start:end].replace('\n',' ')
                candidates.add((url, pat, snippet))
    except Exception as e:
        print('err fetching', url, e)

for c in candidates:
    print('\nURL:', c[0])
    print('PAT:', c[1])
    print('SNIP:', c[2])
