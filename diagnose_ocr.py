"""
Diagnostic script to test GBW OCR configuration
"""
import sys
import requests
from pathlib import Path

# Test 1: Check PPLL OCR availability
print("=" * 60)
print("Test 1: PPLL OCR Availability")
print("=" * 60)

try:
    import numpy as np
    print(f"✓ NumPy version: {np.__version__}")
    if int(np.__version__.split('.')[0]) >= 2:
        print("  ⚠️ NumPy >= 2.0 detected, PPLL OCR will be skipped")
except Exception as e:
    print(f"✗ NumPy import failed: {e}")

try:
    import onnxruntime
    print(f"✓ onnxruntime available: {onnxruntime.__version__}")
except Exception as e:
    print(f"✗ onnxruntime import failed: {e}")

try:
    # Add ppllocr to path
    ppllocr_path = Path("ppllocr/ppllocr-main")
    if ppllocr_path.exists():
        sys.path.insert(0, str(ppllocr_path.absolute()))
        print(f"✓ Added to path: {ppllocr_path}")
    
    from ppllocr import OCR
    print("✓ ppllocr.OCR imported successfully")
    
    # Try to create instance
    ocr = OCR()
    print(f"✓ OCR instance created: {type(ocr)}")
    print(f"  Has classification method: {callable(getattr(ocr, 'classification', None))}")
    
except Exception as e:
    print(f"✗ ppllocr import/init failed: {e}")
    import traceback
    traceback.print_exc()

# Test 2: Check Baidu OCR
print("\n" + "=" * 60)
print("Test 2: Baidu OCR Availability")
print("=" * 60)

BAIDU_OCR_AK = "64hxUIMiToJXovvmVFNCOoUQ"
BAIDU_OCR_SK = "ps6RGIKaBprXgKRC2LYmZJK8sMLMV4GE"

try:
    # Get Baidu access token
    token_url = "https://aip.baidubce.com/oauth/2.0/token"
    params = {
        "grant_type": "client_credentials",
        "client_id": BAIDU_OCR_AK,
        "client_secret": BAIDU_OCR_SK
    }
    resp = requests.get(token_url, params=params, timeout=10)
    resp.raise_for_status()
    token_data = resp.json()
    
    if "access_token" in token_data:
        print(f"✓ Baidu OCR token obtained")
        print(f"  Token: {token_data['access_token'][:20]}...")
    else:
        print(f"✗ No access_token in response: {token_data}")
        
except Exception as e:
    print(f"✗ Baidu OCR token request failed: {e}")

# Test 3: Fetch a real captcha
print("\n" + "=" * 60)
print("Test 3: Fetch Real Captcha")
print("=" * 60)

try:
    import time
    BASE = "https://openstd.samr.gov.cn"
    CAPTCHA_URL = f"{BASE}/bzgk/gb/gc"
    
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    })
    
    # First visit show page to get cookies
    show_url = f"{BASE}/bzgk/gb/showGb?type=download&hcno=96019B083A5A59FC7F84895DFFE7500B"
    resp = session.get(show_url, timeout=15)
    print(f"✓ Show page status: {resp.status_code}")
    
    # Get captcha
    ts = int(time.time() * 1000)
    url = f"{CAPTCHA_URL}?_{ts}"
    resp = session.get(url, timeout=10)
    
    print(f"✓ Captcha status: {resp.status_code}")
    print(f"  Content-Type: {resp.headers.get('Content-Type')}")
    print(f"  Size: {len(resp.content)} bytes")
    
    # Check if it's an image
    if b"<html" in resp.content[:100].lower():
        print("  ✗ Response is HTML, not an image!")
        print(f"  First 200 chars: {resp.content[:200]}")
    else:
        print("  ✓ Response appears to be an image")
        
        # Save for inspection
        with open("test_captcha.jpg", "wb") as f:
            f.write(resp.content)
        print("  ✓ Saved to test_captcha.jpg")
        
except Exception as e:
    print(f"✗ Captcha fetch failed: {e}")
    import traceback
    traceback.print_exc()
