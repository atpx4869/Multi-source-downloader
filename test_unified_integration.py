"""
Final verification of unified API output and integration
"""
from pathlib import Path
from core.aggregated_downloader import AggregatedDownloader
import json

def main():
    print("=" * 60)
    print("Aggregated Downloader Unified API Test")
    print("=" * 60)
    
    # Initialize downloader
    downloader = AggregatedDownloader(output_dir="test_unified_output")
    
    # Check source health
    print("\n1. Checking source health...")
    health = downloader.check_source_health(force=True)
    for name, h in health.items():
        print(f"  {h}")
    
    # Perform a broad search
    keyword = "3324-2024"
    print(f"\n2. Searching for '{keyword}' across all sources...")
    results = downloader.search(keyword)
    
    if not results:
        print("✗ No results found")
        return
    
    print(f"✓ Found {len(results)} aggregated result(s)")
    
    for i, item in enumerate(results[:3], 1):
        print(f"\n[{i}] {item.std_no} - {item.name}")
        print(f"    Sources: {item.sources}")
        print(f"    Status: {item.status}")
        print(f"    Combined has_pdf: {'✓' if item.has_pdf else '✗'}")
        
        # Verify source_meta structure
        print("    Source specific info:")
        for src_name in item.sources:
            smeta = item.source_meta.get(src_name, {})
            shas_pdf = smeta.get("_has_pdf", "N/A")
            print(f"      - {src_name}: _has_pdf={shas_pdf}")
            
    # Try download (prioritizing GBW for this test)
    if results:
        item = results[0]
        print(f"\n3. Attempting download for {item.std_no}...")
        path, logs = downloader.download(item)
        
        if path:
            print(f"✓ Download success: {path}")
        else:
            print("✗ Download failed")
            for log in logs:
                print(f"  {log}")

if __name__ == "__main__":
    main()
