from typing import Any, Dict, List, Optional
import requests

API_URL_DEFAULT = "https://login.bz.zhenggui.vip/bzy-api/org/std/search"


def search_via_api(keyword: str, page: int = 1, page_size: int = 20, session: Optional[requests.Session] = None, api_url: str = API_URL_DEFAULT) -> List[Dict[str, Any]]:
    """Query ZBY JSON API and return list of rows (dicts).

    Returns empty list on failure.
    """
    sess = session or requests.Session()
    headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://bz.zhenggui.vip", "Origin": "https://bz.zhenggui.vip"}
    body = {
        "params": {
            "pageNo": int(page),
            "pageSize": int(page_size),
            "model": {
                "standardNum": None,
                "standardName": None,
                "standardType": None,
                "standardCls": None,
                "keyword": keyword,
                "forceEffective": "0",
                "standardStatus": None,
                "searchType": "1",
                "standardPubTimeType": "0",
            },
        },
        "token": "",
        "userId": "",
        "orgId": "",
        "time": "",
    }
    try:
        r = sess.post(api_url, headers={**headers, "Content-Type": "application/json;charset=UTF-8"}, json=body, timeout=10)
        if r.status_code != 200:
            return []
        j = r.json()
        if isinstance(j, dict):
            data = j.get('data') or j.get('result') or {}
            rows = None
            if isinstance(data, dict):
                rows = data.get('rows')
            if rows is None and isinstance(j.get('rows'), list):
                rows = j.get('rows')
            if isinstance(rows, list):
                return rows
        return []
    except Exception:
        return []
