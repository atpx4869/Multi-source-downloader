# -*- coding: utf-8 -*-
"""Bulk/parallel AggregatedDownloader tests for multiple keywords."""
import sys
from pathlib import Path
import concurrent.futures
import traceback

root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root))

from core.aggregated_downloader import AggregatedDownloader


KEYWORDS = [
    "GB/T 3324",
    "GB/T 33240",
    "GB/T 33241",
    "木家具",
    "胶乳制品",
]


def run_keyword(kw: str):
    out = Path('downloads')
    ad = AggregatedDownloader(output_dir=str(out))
    try:
        results = ad.search(kw, page=1, page_size=5)
        summary = []
        for it in results[:3]:
            path, logs = ad.download(it)
            summary.append((it.display_label(), bool(path), str(path) if path else None, logs[:3]))
        return kw, summary
    except Exception:
        return kw, traceback.format_exc()


def main():
    print('Starting bulk tests...')
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
        futures = [ex.submit(run_keyword, kw) for kw in KEYWORDS]
        for fut in concurrent.futures.as_completed(futures):
            kw, result = fut.result()
            print('---', kw)
            if isinstance(result, list):
                for label, ok, path, logs in result:
                    print(label, 'ok' if ok else 'fail', path)
                    for l in logs:
                        print('  -', l)
            else:
                print('Error:', result)


if __name__ == '__main__':
    main()
