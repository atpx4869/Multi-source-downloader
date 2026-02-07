"""
Test GBW with GB/T 3325-2024
"""
from pathlib import Path
from sources.gbw import GBWSource

def main():
    source = GBWSource()
    
    print("=" * 60)
    print("Test: Search and Download GB/T 3325-2024")
    print("=" * 60)
    
    # Search
    print("\n1. Searching...")
    results = source.search("3325-2024")
    
    if not results:
        print("✗ No results found")
        return
    
    print(f"✓ Found {len(results)} result(s)")
    for item in results:
        print(f"  标准号: {item.std_no}")
        print(f"  名称: {item.name}")
        print(f"  ID: {item.source_meta.get('id', 'N/A')}")
        print(f"  状态: {item.source_meta.get('status', 'N/A')}")
    
    # Download first result
    print("\n2. Downloading...")
    item = results[0]
    
    output_dir = Path("./test_gbw_3325")
    output_dir.mkdir(exist_ok=True)
    
    success = source.download(item, output_dir)
    
    if success:
        outfile = output_dir / item.filename()
        if outfile.exists():
            size = outfile.stat().st_size
            print(f"\n✓ Download successful!")
            print(f"  File: {outfile}")
            print(f"  Size: {size:,} bytes")
        else:
            print(f"\n✗ File not found: {outfile}")
    else:
        print(f"\n✗ Download failed")

if __name__ == "__main__":
    main()
