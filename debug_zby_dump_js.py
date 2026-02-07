from playwright.sync_api import sync_playwright
from pathlib import Path
import os
import urllib.parse

# Setup
STD_ID = "443847" # GB/T 3324-2017
BASE_URL = "https://bz.zhenggui.vip"
OUTPUT_DIR = Path("debug_js_dump")
OUTPUT_DIR.mkdir(exist_ok=True)

def dump_js():
    print("--- Dumping JS Files ---")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Intercept and save JS
        def handle_response(response):
            if response.request.resource_type == "script":
                url = response.url
                if "zhenggui.vip" in url: # Only target first-party JS
                    try:
                        filename = os.path.basename(urllib.parse.urlparse(url).path)
                        if not filename.endswith(".js"): filename += ".js"
                        
                        # Add counter to avoid collisions or empty names
                        if not filename or filename == ".js":
                            filename = f"script_{hash(url)}.js"
                            
                        save_path = OUTPUT_DIR / filename
                        with open(save_path, "wb") as f:
                            f.write(response.body())
                        print(f"[SAVED] {filename} from {url}")
                    except Exception as e:
                        print(f"[ERROR] Failed to save {url}: {e}")

        page.on("response", handle_response)
        
        # Navigate
        url = f"{BASE_URL}/standardDetail?standardId={STD_ID}&docStatus=0"
        print(f"Navigating to {url}...")
        page.goto(url, timeout=60000)
        page.wait_for_load_state("networkidle")
        
        browser.close()
    
    print(f"--- Dump Complete. Files saved to {OUTPUT_DIR.absolute()} ---")

if __name__ == "__main__":
    dump_js()
