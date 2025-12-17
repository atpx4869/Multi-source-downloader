import re, requests
from urllib.parse import urljoin
base='https://bz.zhenggui.vip/'
urls=[
    'https://bz.zhenggui.vip/assets/index.0214bd45.js',
    'https://bz.zhenggui.vip/assets/polyfills-legacy.0d3d6c0f.js',
    'https://bz.zhenggui.vip/assets/index-legacy.35e4c9d8.js'
]
patterns=['/api/','searchText','/standardList','/search','fetch(','axios','/api/search']
for u in urls:
    try:
        r=requests.get(u, headers={"User-Agent":"Mozilla/5.0"}, timeout=15)
        txt=r.text or ''
        print('\nFETCHED',u,'LEN',len(txt))
        for pat in patterns:
            if pat in txt:
                idx=txt.find(pat)
                start=max(0,idx-80)
                end=min(len(txt),idx+120)
                print('PAT',pat, '... ', txt[start:end].replace('\n',' '))
    except Exception as e:
        print('ERR',u,e)
