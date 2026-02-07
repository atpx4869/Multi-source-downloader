
import re
import time
import requests
from playwright.sync_api import sync_playwright

STD_ID = "441181"
BASE_URL = "https://bz.zhenggui.vip"
API_BASE = "https://login.bz.zhenggui.vip/bzy-api"

def get_uuid_via_playwright(std_id):
    print(f"--- Step 1: Extract UUID via Playwright (std_id={std_id}) ---")
    
    # 1. Launch Browser
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        context = browser.new_context()
        page = context.new_page()
        
        # 2. Setup Request Interception
        found = {"uuid": None}
        def capture_req(r):
            if "bzy-api" in r.url and r.method == "POST":
                try:
                    print(f"[API REQ] {r.url} -> Data: {r.post_data}")
                except:
                    pass
            
            if "immdoc" in r.url and "/doc/" in r.url:
                 # existing logic for UUID
                 m = re.search(r'immdoc/([a-zA-Z0-9-]+)/doc', r.url)
                 if m:
                     print(f"[SUCCESS] Caught UUID request: {r.url}")
                     found["uuid"] = m.group(1)

        def capture_resp(r):
            if "bzy-api" in r.url and r.status == 200:
                try:
                    data = r.json()
                    print(f"[API DEBUG] {r.url} -> Keys: {list(data.keys()) if isinstance(data, dict) else 'List'}")
                    # Check if 'data' contains title
                    if isinstance(data, dict) and "data" in data:
                        inner = data["data"]
                        if isinstance(inner, dict):
                             print(f"  -> Data keys: {list(inner.keys())}")
                             if "chineseName" in inner: print(f"  -> Title: {inner['chineseName']}")
                        elif isinstance(inner, list) and len(inner) > 0:
                             print(f"  -> List[0] keys: {list(inner[0].keys())}")
                except:
                    pass

        page.on("request", capture_req)
        page.on("response", capture_resp)
        
        # 3. Navigate
        url = f"{BASE_URL}/standardDetail?standardId={std_id}&docStatus=0"
        print(f"Navigating to {url}...")
        try:
            page.goto(url, timeout=60000)
            
            # 4. Scroll to trigger lazy loading
            print("Scrolling to trigger resources...")
            for _ in range(5):
                page.mouse.wheel(0, 1000)
                time.sleep(1)
            
            # 5. Wait for Magic
            for i in range(30):
                if found["uuid"]: 
                    break
                time.sleep(1)
                print(f"Waiting... {i+1}s")
                
        except Exception as e:
            print(f"Navigation error: {e}")
        finally:
            browser.close()
            
    return found["uuid"]


# --- Step 2: Concurrent Download Logic (Copied & Simplified from zby_utils.py) ---
import shutil
import concurrent.futures
from pathlib import Path
import img2pdf

def download_images_concurrently(uuid, output_file="downloads/GB_T_3324-2017.pdf"):
    print(f"\n--- Step 2: Concurrent Download (UUID={uuid}) ---")
    
    # Setup
    output_dir = Path("downloads")
    temp_dir = output_dir / "zby_test_temp"
    if temp_dir.exists(): shutil.rmtree(temp_dir)
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0"})
    
    # Download Function
    def download_page(page_num):
        url = f"https://resource.zhenggui.vip/immdoc/{uuid}/doc/I/{page_num}"
        for _ in range(3): # 3 Retries
            try:
                r = session.get(url, timeout=15, verify=False)
                if r.status_code == 200:
                    out = temp_dir / f"{page_num:04d}.jpg"
                    with open(out, 'wb') as f: f.write(r.content)
                    return page_num, str(out)
                elif r.status_code == 404:
                    return page_num, None # End of doc
                time.sleep(1)
            except:
                time.sleep(1)
        return page_num, None

    # Execution Loop
    imgs = []
    page = 1
    batch_size = 20
    max_pages = 500 # Safety limit
    
    while page < max_pages:
        print(f"Downloading batch: {page} to {page+batch_size}...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = {executor.submit(download_page, p): p for p in range(page, page + batch_size)}
            
            batch_results = {}
            for f in concurrent.futures.as_completed(futures):
                p, path = f.result()
                batch_results[p] = path
            
            # Check results
            found_end = False
            for p in range(page, page + batch_size):
                if batch_results.get(p):
                    imgs.append(batch_results[p])
                else:
                    found_end = True # Stop if any page missing (assumption: sequential)
                    break
            
            if found_end:
                break
            page += batch_size

    # PDF Conversion
    if imgs:
        print(f"Downloaded {len(imgs)} pages. Converting to PDF...")
        imgs.sort()
        with open(output_file, "wb") as f:
            f.write(img2pdf.convert(imgs))
        print(f"[SUCCESS] PDF saved to {output_file}")
        shutil.rmtree(temp_dir)
        return True
    else:
        print("[FAILURE] No images downloaded.")
        return False

if __name__ == "__main__":
    import urllib3
    urllib3.disable_warnings()
    
    # 1. Get UUID
    uuid = get_uuid_via_playwright(STD_ID)
    
    # 2. Download
    if uuid:
        print(f"\n[INTERMEDIATE] Extracted UUID: {uuid}")
        download_images_concurrently(uuid)
    else:
        print(f"\n[FAILURE] Could not extract UUID.")
