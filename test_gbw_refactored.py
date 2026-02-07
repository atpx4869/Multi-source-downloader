"""
Test refactored GBW source implementation
"""
from pathlib import Path
from sources.gbw import GBWSource
from core.models import Standard

def main():
    source = GBWSource()
    
    # Test 1: Search
    print("=" * 60)
    print("Test 1: Search for GB/T 3324-2024")
    print("=" * 60)
    
    results = source.search("GB/T 3324-2024")
    
    if results:
        print(f"✓ Found {len(results)} result(s)")
        item = results[0]
        print(f"  标准号: {item.std_no}")
        print(f"  名称: {item.name}")
        print(f"  ID: {item.source_meta.get('id')}")
        print(f"  HCNO: {item.source_meta.get('hcno')}")
        print(f"  状态: {item.source_meta.get('status')}")
    else:
        print("✗ No results found")
        return
    
    # Test 2: Download
    print("\n" + "=" * 60)
    print("Test 2: Download GB/T 3324-2024")
    print("=" * 60)
    
    output_dir = Path("./test_gbw_refactored")
    output_dir.mkdir(exist_ok=True)
    
    path, logs = source.download(item, output_dir, emit=print)
    
    if path and path.exists():
        print(f"\n✓ Download successful!")
        print(f"  File: {path}")
        print(f"  Size: {path.stat().st_size:,} bytes")
    else:
        print(f"\n✗ Download failed")
        if logs:
            print("Logs:")
            for log in logs:
                print(f"  {log}")

if __name__ == "__main__":
    main()
