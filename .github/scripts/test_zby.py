# -*- coding: utf-8 -*-
"""Simple test for sources.ZBYSource: search and optional download."""
import sys
from pathlib import Path
# add workspace root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from sources.zby import ZBYSource


def main():
    s = ZBYSource(output_dir=Path('downloads'))
    print('Playwright available:', s._playwright_available)
    rows = s.search('GB/T 3324', page=1, page_size=5)
    print(f'Found {len(rows)} items')
    for i, it in enumerate(rows[:5], 1):
        print(i, it.std_no, it.name, 'has_pdf=' + str(it.has_pdf))
    if rows:
        first = rows[0]
        print('Attempting download of first item...')
        out, logs = s.download(first, Path('downloads'))
        print('Download result:', out)
        for l in logs:
            print('-', l)


if __name__ == '__main__':
    main()
