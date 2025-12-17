from pathlib import Path
import sys
import traceback
import os

# ensure project root is on sys.path
proj = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(proj))

from sources.zby import ZBYSource
from core.models import Standard

s = ZBYSource(output_dir=Path('downloads'))
item = Standard(std_no='GBT13324-2006', name='热处理设备术语', has_pdf=True, source_meta={'ZBY': {'standardNum': 'GBT13324-2006'}}, sources=['ZBY'])
print('Playwright available:', getattr(s, '_playwright_available', False))
try:
    res = s.download(item, Path('downloads'), log_cb=print)
    print('Result:', res)
except Exception:
    traceback.print_exc()
