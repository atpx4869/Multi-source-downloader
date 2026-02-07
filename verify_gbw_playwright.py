
import sys
import os
import logging
from pathlib import Path

sys.path.insert(0, os.getcwd())

# Setup logging
logging.basicConfig(level=logging.INFO)

from sources.gbw import GBWSource
from core.models import Standard
import time

def main():
    source = GBWSource()
    source.allow_playwright = True 
    
    # Monkeypatch the _download_by_hcno to save the HTML it receives
    original_func = source._download_by_hcno
    
    def debug_download(hcno, resp_text, cookies, output_dir, item, emit, logs):
        print(f"DEBUG: Saving pw_debug.html (Length: {len(resp_text)})")
        with open("pw_debug.html", "w", encoding="utf-8") as f:
            f.write(resp_text)
        return original_func(hcno, resp_text, cookies, output_dir, item, emit, logs)
        
    source._download_by_hcno = debug_download
    
    # Mock Item
    # GB/T 3324-2024
    item = Standard(
        std_no="GB/T 3324-2024",
        name="木家具通用技术条件",
        source_meta={
            "id": "25940C3CEF158A9AE06397BE0A0A525A", 
            "hcno": "96019B083A5A59FC7F84895DFFE7500B"
        },
        sources=["GBW"]
    )
    
    out_dir = Path("gbw_pw_test")
    out_dir.mkdir(exist_ok=True)
    
    print("Testing GBWSource.download()...")
    # This will try requests first (which we know fails) then Playwright
    # passing a source_meta with hcno triggers download logic
    
    result = source.download(item, out_dir)
    
    if result.success:
        print(f"[SUCCESS] Downloaded to: {result.file_path}")
    else:
        print(f"[FAILURE] Error: {result.error}")
        print("Logs:")
        for log in result.logs:
            print(f"  {log}")

if __name__ == "__main__":
    main()
