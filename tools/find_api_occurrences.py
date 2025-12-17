from urllib.parse import urljoin
import requests

urls=[
    'https://bz.zhenggui.vip/assets/index.0214bd45.js',
    'https://bz.zhenggui.vip/assets/index-legacy.35e4c9d8.js'
]
for u in urls:
    r=requests.get(u, headers={"User-Agent":"Mozilla/5.0"}, timeout=20)
    txt=r.text
    i=0
    occ=0
    while True:
        idx=txt.find('/api', i)
        if idx==-1:
            break
        occ+=1
        start=max(0, idx-80)
        end=min(len(txt), idx+120)
        print('\nFILE',u,'OCC',occ,'IDX',idx)
        print(txt[start:end].replace('\n',' '))
        i=idx+4
print('\nDONE')
