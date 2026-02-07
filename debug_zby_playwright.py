
import re
import time
from playwright.sync_api import sync_playwright

STD_ID = "443847"
BASE_URL = "https://bz.zhenggui.vip"
DETAIL_URL = f"{BASE_URL}/standardDetail?standardId={STD_ID}"

def debug_playwright():
    print(f"--- Debugging ZBY Playwright (Headed Mode) ---")
    print(f"Target URL: {DETAIL_URL}")
    
    with sync_playwright() as p:
        # Launch browser in HEADED mode so we can see what happens
        browser = p.chromium.launch(headless=False, args=["--no-sandbox"])
        context = browser.new_context()
        page = context.new_page()

        print("Browser launched. Navigating...")
        
        # Capture ALL requests to see what we might be missing
        def log_request(request):
            if "immdoc" in request.url or "resource.zhenggui.vip" in request.url:
                print(f"[MATCH] Found resource request: {request.url}")
            # Optional: print other API calls to find the metadata source
            if "bzy-api" in request.url and "Method" not in request.url: # Filter OPTIONS
                print(f"[API] {request.method} {request.url}")

        page.on("request", log_request)

        try:
            page.goto(DETAIL_URL, timeout=60000)
            print("Page loaded. Waiting for network activity...")
            
            # Wait for specific elements
            try:
                page.wait_for_selector("#aliyunPreview", timeout=20000)
                print("Element #aliyunPreview found.")
            except:
                print("TIMEOUT: #aliyunPreview not found.")

            # Scroll down to trigger lazy loading if needed
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            
            # Keep open for a bit
            print("Waiting 15 seconds for async requests...")
            time.sleep(15)
            
        except Exception as e:
            print(f"Error: {e}")
        finally:
            print("Closing browser...")
            browser.close()

if __name__ == "__main__":
    debug_playwright()
