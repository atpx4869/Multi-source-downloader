# -*- coding: utf-8 -*-
"""Run AggregatedDownloader search + download end-to-end for GBW and ZBY."""
import sys
from pathlib import Path
import traceback

root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root))

from core.aggregated_downloader import AggregatedDownloader


def main():
    kw = 'GB/T 3324'
    out = Path('downloads')
    out.mkdir(exist_ok=True)
    ad = AggregatedDownloader(output_dir=str(out))
    print('Available sources:', [s.name for s in ad.sources])
    print('Health cache:', {k: str(v) for k, v in ad.health_cache.items()})

    try:
        print(f"Searching for '{kw}'...")
        results = ad.search(kw, page=1, page_size=10)
        print(f'Found {len(results)} combined results')
        for i, it in enumerate(results[:10], 1):
            print(i, it.std_no, it.name, 'has_pdf=' + str(it.has_pdf), 'sources=' + ','.join(it.sources))

        # Try download first 3 items
        for idx, it in enumerate(results[:3], 1):
            print('\n--- Attempt download', idx, it.display_label())
            path, logs = ad.download(it)
            print('Result path:', path)
            for l in logs:
                print('-', l)

    except Exception:
        traceback.print_exc()


if __name__ == '__main__':
    main()
