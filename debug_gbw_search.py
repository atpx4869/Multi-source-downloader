
import sys
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sources.gbw import GBWSource

def debug_gbw_source_search():
    keyword = "3325"
    gbw = GBWSource()
    
    print(f"Searching for '{keyword}' using GBWSource class...")
    results = gbw.search(keyword)
    
    print(f"Returned results count: {len(results)}")
    for i, res in enumerate(results):
        print(f"Result {i+1}: {res.std_no} | {res.name}")

if __name__ == "__main__":
    debug_gbw_source_search()
