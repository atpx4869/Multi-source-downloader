import time
from core.http_aggregated_downloader import HttpAggregatedDownloader
from app.desktop_app_impl import start_backend_server

start_backend_server()
time.sleep(2)
d = HttpAggregatedDownloader()
print("Health:", d.check_source_health())
res = d.search("GB/T 3324", parallel=True)
print("Search results:", len(res))
if res:
    print(res[0])
