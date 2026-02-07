"""
Verification of copyright restriction detection
"""
from core.aggregated_downloader import AggregatedDownloader
from core.unified_models import Standard

def main():
    print("=" * 60)
    print("Copyright Restriction Detection Verification")
    print("=" * 60)
    
    downloader = AggregatedDownloader(output_dir="test_restricted")
    
    # Test case: GB/T 25686-2018 (Copyright restricted)
    keyword = "25686-2018"
    print(f"\n1. Searching for '{keyword}'...")
    results = downloader.search(keyword)
    
    if not results:
        print("✗ No results found")
        return
        
    item = results[0]
    print(f"✓ Found: {item.std_no} - {item.name}")
    print(f"  Search Hint has_pdf: {item.has_pdf} (Expected True based on 'Current' status)")
    
    print(f"\n2. Attempting download (should skip based on real-time check)...")
    path, logs = downloader.download(item)
    
    if path:
        print(f"✗ Unexpected Success: {path}")
    else:
        print("✓ Expected Skip/Failure")
        # Check logs for the specific message
        skip_msg_found = any("详情页确认无 PDF（可能受版权保护" in log for log in logs)
        if skip_msg_found:
            print("✓ Found skip message in logs")
        else:
            print("✗ Skip message not found in logs")
            
        for log in logs:
            print(f"  {log}")

if __name__ == "__main__":
    main()
