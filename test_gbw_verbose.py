"""
Test GBW download with verbose logging
"""
from pathlib import Path
from sources.gbw import GBWSource
from core.models import Standard

def main():
    source = GBWSource()
    
    # Mock Item with known HCNO
    item = Standard(
        std_no="GB/T 3324-2024",
        name="木家具通用技术条件",
        source_meta={
            "id": "25940C3CEF158A9AE06397BE0A0A525A",
            "hcno": "96019B083A5A59FC7F84895DFFE7500B"  # Provide HCNO directly
        },
        sources=["GBW"]
    )
    
    output_dir = Path("./test_gbw_verbose")
    output_dir.mkdir(exist_ok=True)
    
    print("Testing GBW download with verbose logging...")
    print(f"HCNO: {item.source_meta['hcno']}")
    
    # Import download_with_ocr directly to use verbose mode
    from sources.gbw_download import download_with_ocr
    
    outfile = output_dir / item.filename()
    success = download_with_ocr(
        hcno=item.source_meta['hcno'],
        outfile=outfile,
        max_attempts=3,  # Reduce attempts for faster testing
        logger=print,
        session=source.session,
        verbose=True  # Enable verbose logging
    )
    
    if success:
        print(f"\n✓ Download successful: {outfile}")
    else:
        print(f"\n✗ Download failed")

if __name__ == "__main__":
    main()
