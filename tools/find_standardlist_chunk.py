import requests
urls=['https://bz.zhenggui.vip/assets/index.0214bd45.js','https://bz.zhenggui.vip/assets/index-legacy.35e4c9d8.js']
for u in urls:
    r=requests.get(u, headers={"User-Agent":"Mozilla/5.0"}, timeout=20)
    txt=r.text
    idx=txt.find('standardList')
    if idx!=-1:
        start=max(0,idx-80)
        end=min(len(txt), idx+200)
        print('\nFILE',u)
        print(txt[start:end].replace('\n',' '))
    else:
        print('not found in',u)
