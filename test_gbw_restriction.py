"""
Verification of copyright restriction detection specifically for GBW
"""
from sources.gbw import GBWSource
from core.unified_models import Standard

def main():
    print("=" * 60)
    print("GBW Copyright Restriction Detection Verification")
    print("=" * 60)
    
    gbw = GBWSource()
    
    # Test case: GB/T 25686-2018 (Copyright restricted on GBW)
    keyword = "25686-2018"
    print(f"\n1. Searching for '{keyword}' on GBW...")
    results = gbw.search(keyword)
    
    if not results:
        print("✗ No results found on GBW")
        return
        
    item = results[0]
    print(f"✓ Found: {item.std_no} - {item.name}")
    
    print(f"\n2. Checking has_pdf() (should detect restriction)...")
    is_available = gbw.has_pdf(item)
    
    if is_available:
        print("✗ Failure: GBW reported PDF as available but it should be restricted.")
    else:
        print("✓ Success: GBW correctly detected PDF is NOT available (copyright restricted).")

    print(f"\n3. Checking download() (should also fail gracefully)...")
    from pathlib import Path
    outdir = Path("test_restricted_gbw")
    outdir.mkdir(exist_ok=True)
    
    result = gbw.download(item, outdir)
    if result.success:
        print("✗ Failure: GBW download unexpectedly succeeded.")
    else:
        print(f"✓ Success: GBW download failed as expected.")
        print(f"  Error message: {result.error}")

if __name__ == "__main__":
    main()
