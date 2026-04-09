import requests
from core.http_aggregated_downloader import HttpAggregatedDownloader
d = HttpAggregatedDownloader(enable_sources=["GBW"])
print("Search Single Source GBW...")
items = d.search_single_source("GBW", "GB/T 3324")
for it in items:
    print(it.std_no, it.name)

print("\nSearch All...")
res = d.search("GB/T 3324")
for it in res:
    print(it.std_no, it.name)
