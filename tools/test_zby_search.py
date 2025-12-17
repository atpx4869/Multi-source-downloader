from pathlib import Path
import sys
repo = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo))

from sources.zby import ZBYSource

s = ZBYSource()
print('base_url:', s.base_url)
print('allow_playwright:', s.allow_playwright)
print('is_available():', s.is_available())

try:
    items = s.search('测试', page_size=5)
    print('found:', len(items))
    for i, it in enumerate(items, 1):
        try:
            print(i, getattr(it, 'std_no', None), getattr(it, 'name', None), getattr(it, 'source_meta', None))
        except Exception as e:
            print('item print error', e)
except Exception as e:
    print('search error:', e)
