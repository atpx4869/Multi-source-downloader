import requests
from urllib.parse import urljoin
base='https://bz.zhenggui.vip'
chunks=['/assets/standardList.157749fd.js','/assets/standardList-legacy.8ae72ab8.js']
patterns=['fetch(','axios.get','axios.post','/search','/api','/standardList','searchText','q=']
for c in chunks:
    url=urljoin(base,c)
    try:
        r=requests.get(url, headers={"User-Agent":"Mozilla/5.0"}, timeout=20)
        txt=r.text
        print('\nCHUNK',url,'LEN',len(txt))
        for pat in patterns:
            if pat in txt:
                idx=txt.find(pat)
                start=max(0,idx-80)
                end=min(len(txt), idx+200)
                print('PAT',pat,'->',txt[start:end].replace('\n',' '))
    except Exception as e:
        print('ERR',url,e)
