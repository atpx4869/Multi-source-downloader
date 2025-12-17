# -*- coding: utf-8 -*-
"""
ZBY adapter - prefer user-provided implementation if available, else fall back to Playwright backup.
This module exposes `ZBYSource` class compatible with AggregatedDownloader.
"""
from pathlib import Path
from typing import List

from core.models import Standard, natural_key, sanitize_filename


try:
    # Try to use user's StandardDownloader-based implementation (if available in environment)
    from standard_downloader import StandardDownloader  # type: ignore

    class ZBYSource:
        name = "ZBY"
        priority = 3

        def __init__(self, output_dir: Path | str = "downloads"):
            self.output_dir = Path(output_dir)
            self.client = StandardDownloader(output_dir=self.output_dir)

        def search(self, keyword: str, **kwargs) -> List[Standard]:
            data = self.client.search(keyword, **kwargs)
            rows = data.get("rows") or []
            items: List[Standard] = []
            for r in rows:
                items.append(
                    Standard(
                        std_no=(r.get("standardNum") or "").strip(),
                        name=(r.get("standardName") or "").strip(),
                        publish=(r.get("standardPubTime") or "")[:10],
                        implement=(r.get("standardUsefulDate") or "")[:10],
                        status=str(r.get("standardStatus") or ""),
                        has_pdf=bool(r.get("hasPdf")),
                        source_meta=r,
                        sources=["ZBY"],
                    )
                )
            items.sort(key=lambda x: natural_key(x.std_no))
            return items

        def download(self, item: Standard, outdir: Path) -> Path | None:
            outdir.mkdir(parents=True, exist_ok=True)
            try:
                self.client.output_dir = Path(outdir)
            except Exception:
                pass
            pdf_path = self.client.download_standard(item.source_meta)
            return Path(pdf_path) if pdf_path else None

except Exception:
    # Fall back to Playwright-based implementation
    from .zby_playwright import ZBYSource  # type: ignore


