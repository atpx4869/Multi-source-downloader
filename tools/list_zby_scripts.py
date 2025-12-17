import re, requests
from urllib.parse import urljoin
base='https://bz.zhenggui.vip/'
r=requests.get(base, headers={"User-Agent":"Mozilla/5.0"}, timeout=8)
html=r.text or ''
scripts = re.findall(r'<script[^>]+src=["\']([^"\']+)["\']', html, re.I)
for s in scripts:
    print(urljoin(base,s))
