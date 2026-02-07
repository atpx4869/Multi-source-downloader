"""
Test has_pdf method for GBW source
"""
from sources.gbw import GBWSource

def main():
    source = GBWSource()
    
    # Test 1: Current standard (should have PDF)
    print("=" * 60)
    print("Test 1: GB/T 3324-2024 (现行)")
    print("=" * 60)
    results = source.search("3324-2024")
    if results:
        item = results[0]
        print(f"标准号: {item.std_no}")
        print(f"名称: {item.name}")
        print(f"状态: {item.source_meta.get('status', 'N/A')}")
        
        has_pdf = source.has_pdf(item)
        print(f"有PDF: {'✓' if has_pdf else '✗'}")
    
    # Test 2: Obsolete standard (likely no PDF)
    print("\n" + "=" * 60)
    print("Test 2: GB/T 3324-2008 (废止)")
    print("=" * 60)
    results = source.search("3324-2008")
    if results:
        item = results[0]
        print(f"标准号: {item.std_no}")
        print(f"名称: {item.name}")
        print(f"状态: {item.source_meta.get('status', 'N/A')}")
        
        has_pdf = source.has_pdf(item)
        print(f"有PDF: {'✓' if has_pdf else '✗'}")
    
    # Test 3: Another current standard
    print("\n" + "=" * 60)
    print("Test 3: GB/T 3325-2024 (现行)")
    print("=" * 60)
    results = source.search("3325-2024")
    if results:
        item = results[0]
        print(f"标准号: {item.std_no}")
        print(f"名称: {item.name}")
        print(f"状态: {item.source_meta.get('status', 'N/A')}")
        
        has_pdf = source.has_pdf(item)
        print(f"有PDF: {'✓' if has_pdf else '✗'}")

if __name__ == "__main__":
    main()
