# -*- coding: utf-8 -*-
"""
Lightweight ZBY adapter with HTTP-first fallback and debug artifact mirroring.

This module avoids importing Playwright at module-import time so it is safe
to include in frozen executables. If Playwright is needed it will be loaded
only at runtime by explicit callers.
"""
import re
import json
import logging
import random
from pathlib import Path
from typing import List, Union
import tempfile
import shutil
import os
import urllib3

# 抑制 urllib3 的 SSL 验证警告（我们故意禁用 SSL 验证以兼容国内网站）
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 配置日志记录
logger = logging.getLogger(__name__)

# 导入性能监控工具
try:
    from core.performance import get_performance_monitor, get_connection_pool_manager
    performance_monitor = get_performance_monitor()
    pool_manager = get_connection_pool_manager()
except ImportError:
    performance_monitor = None
    pool_manager = None

from requests import Response

DEFAULT_BASE_URL = "https://bz.zhenggui.vip"

from core.models import Standard
from .base import BaseSource, DownloadResult
from .registry import registry
from .zby_utils import (
    extract_uuid_from_text,
    download_images_to_pdf
)

# 导入超时配置
try:
    from core.timeout_config import get_timeout
except ImportError:
    def get_timeout(source: str, operation: str) -> int:
        return 10


# Prefer local shim; fall back to dotted import for compatibility
try:
    from .standard_downloader import StandardDownloader  # type: ignore
except Exception:
    try:
        from standard_downloader import StandardDownloader  # type: ignore
    except Exception:
        StandardDownloader = None

# --- Pure API Signature Logic ---
import hashlib
import concurrent.futures
import img2pdf
import requests
import time

ORIGIN_CHARS = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"

def _get_random(t="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"):
    res = []
    for char in t:
        if char == 'x':
            res.append(ORIGIN_CHARS[int(random.random() * len(ORIGIN_CHARS))])
        else:
            res.append(char)
    return "".join(res)

def _get_md5(s):
    return hashlib.md5(s.encode('utf-8')).hexdigest()

def _get_nonce():
    import time
    t = _get_random()
    e = int(time.time() * 1000)
    return {"nonce": f"{t}_{e}", "timeStamp": e}

def _get_signature(nonce, timestamp, slot):
    # md5(timestamp + "_" + nonce + "_" + slot)
    raw = f"{timestamp}_{nonce}_{slot}"
    return _get_md5(raw)

def _get_request_must_params(slot="zby_org"):
    n = _get_nonce()
    nonce = n['nonce']
    timestamp = n['timeStamp']
    signature = _get_signature(nonce, timestamp, slot)
    return {"nonce": nonce, "signature": signature}

def _mirror_debug_file_static(p: Path) -> None:
    try:
        p = Path(p)
        if not p.exists():
            return
        tm = Path(tempfile.gettempdir())
        try:
            tm.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(p), str(tm / p.name))
        except Exception:
            pass
        try:
            desk = Path(os.path.expanduser('~')) / 'Desktop'
            desk.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(p), str(desk / p.name))
        except Exception:
            pass
    except Exception:
        pass


@registry.register
class ZBYSource(BaseSource):
    source_id = "zby"
    source_name = "正规标准网"
    priority = 3

    name = "ZBY"

    # 使用统一的超时配置
    SEARCH_TIMEOUT = get_timeout("ZBY", "search")
    DOWNLOAD_TIMEOUT = get_timeout("ZBY", "download")
    API_TIMEOUT = get_timeout("ZBY", "api")

    # 临时覆盖缩短搜索超时
    SEARCH_TIMEOUT = 15

    # 类级别的配置缓存（所有实例共享）
    _api_base_url_cache = None
    _cache_timestamp = 0
    _cache_ttl = 3600  # 缓存1小时

    def __init__(self, output_dir: Union[Path, str] = "downloads") -> None:
        od = Path(output_dir)
        try:
            if (isinstance(output_dir, str) and output_dir == "downloads") or (isinstance(output_dir, Path) and not Path(output_dir).is_absolute()):
                repo_root = Path(__file__).resolve().parents[1]
                od = repo_root / "downloads"
        except Exception:
            od = Path(output_dir)
        self.output_dir = Path(od)

        try:
            import sys as _sys
            frozen = getattr(_sys, 'frozen', False)
        except Exception:
            frozen = False

        self.client = None
        self.allow_playwright: bool = False if frozen else True
        self.base_url: str = DEFAULT_BASE_URL
        self.api_base_url = None

        if not frozen and StandardDownloader is not None:
            try:
                self.client = StandardDownloader(output_dir=self.output_dir)
                self.base_url = getattr(self.client, 'base_url', DEFAULT_BASE_URL)
            except Exception:
                self.client = None
                self.base_url: str = DEFAULT_BASE_URL
        
        # 统一初始化 session
        import requests
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry
        
        self.session = requests.Session()
        self.session.headers.update({
             "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
             "Referer": "https://bz.zhenggui.vip",
        })
        self.session.trust_env = False  # 禁用系统代理
        
        # 增加强大的重试策略和更大的连接池
        retry_strategy = Retry(
            total=3,
            connect=3,
            read=3,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "POST", "OPTIONS"]
        )
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=20,
            pool_maxsize=20
        )
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # 尝试从前端 config.yaml 读取真实 API 基址（使用缓存）
        try:
            self.api_base_url: str = self._load_api_base_url_from_config_cached(timeout=4)
        except Exception:
            self.api_base_url = None

    def _load_api_base_url_from_config_cached(self, timeout: int = 4) -> str:
        """从 config.yaml 读取 BZY_BASE_URL，使用类级别缓存。"""
        import time

        # 检查缓存是否有效
        current_time = time.time()
        if (ZBYSource._api_base_url_cache is not None and
            current_time - ZBYSource._cache_timestamp < ZBYSource._cache_ttl):
            return ZBYSource._api_base_url_cache

        # 缓存失效，重新获取
        url = self._load_api_base_url_from_config(timeout)

        # 更新缓存
        ZBYSource._api_base_url_cache = url
        ZBYSource._cache_timestamp = current_time

        return url

    def _load_api_base_url_from_config(self, timeout: int = 4) -> str:
        """从 config.yaml 读取真实 API 基址"""
        try:
            config_url = f"{self.base_url}/config.yaml"
            resp = self.session.get(config_url, timeout=(timeout, timeout), verify=False)
            if resp.status_code == 200:
                import yaml
                data = yaml.safe_load(resp.text)
                if data and "BZY_BASE_URL" in data:
                    return data["BZY_BASE_URL"].rstrip("/")
        except Exception as e:
            logger.debug(f"[ZBY] _load_api_base_url_from_config failed: {e}")
        return "https://login.bz.zhenggui.vip"

    def _mirror_debug_file(self, p: Path) -> None:
        try:
            _mirror_debug_file_static(p)
        except Exception:
            pass

    def is_available(self, timeout: int = 6) -> bool:
        try:
            import sys as _sys
            frozen = getattr(_sys, 'frozen', False)
        except Exception:
            frozen = False

        try:
            if frozen:
                import requests
                # 创建 session，禁用代理和 SSL 验证（对于国内站点）
                session = requests.Session()
                session.trust_env = False
                session.proxies = {"http": None, "https": None}
                
                # 添加必要的 headers，避免被阻止
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Referer": "https://bz.zhenggui.vip",
                    "Origin": "https://bz.zhenggui.vip"
                }
                
                # 尝试连接 ZBY 首页，禁用 SSL 验证避免证书问题
                try:
                    r: Response = session.get(
                        self.base_url, 
                        timeout=timeout, 
                        headers=headers,
                        verify=False  # 禁用 SSL 验证（国内站点常见问题）
                    )
                    return 200 <= getattr(r, 'status_code', 0) < 400
                except Exception:
                    # 备用方案：尝试连接 API 端点
                    try:
                        api_url = "https://login.bz.zhenggui.vip/bzy-api/org/std/search"
                        r: Response = session.get(
                            api_url,
                            timeout=timeout,
                            headers=headers,
                            verify=False
                        )
                        return 200 <= getattr(r, 'status_code', 0) < 400
                    except Exception:
                        return False
            if self.client is not None and hasattr(self.client, 'is_available'):
                return bool(self.client.is_available())
            return True
        except Exception:
            return False

    def search(self, keyword: str, **kwargs) -> List[Standard]:
        """搜索标准"""
        # 性能监控
        if performance_monitor:
            with performance_monitor.measure("search", "ZBY"):
                return self._search_impl(keyword, **kwargs)
        else:
            return self._search_impl(keyword, **kwargs)

    def _search_impl(self, keyword: str, **kwargs) -> List[Standard]:
        """搜索实现（内部方法）"""
        items = []
        
        # 搜索时禁用Playwright，快速失败策略
        old_allow_playwright = self.allow_playwright
        self.allow_playwright = False

        try:
            # 1. 优先尝试快速 HTTP JSON API（超时8秒，快速失败）
            try:
                http_items = self._http_search_api(keyword, **kwargs)
                if http_items:
                    return http_items
            except Exception:
                pass

            # 2. 最后尝试 HTML 爬取（纯HTTP，不用client和Playwright）
            try:
                html_items = self._http_search_html_fallback(keyword, **kwargs)
                if html_items:
                    return html_items
            except Exception:
                pass

            return items
        finally:
            # 恢复原来的设置
            self.allow_playwright = old_allow_playwright

    def _http_search_api(self, keyword: str, page: int = 1, page_size: int = 20, **kwargs) -> List[Standard]:
        """尝试 JSON API，如果结果为空则自动降级到 HTML 爬虫（对行业标准更友好）。"""
        items = []
        try:
            import requests

            # Session reuse
            session = self.session

            from .zby_http import search_via_api
            
            # 提取标准类型前缀（GB/T, QB/T 等）用于精确匹配
            prefix_match = re.match(r'([A-Z]+/?[A-Z]*)\s*', keyword.upper())
            expected_prefix = prefix_match.group(1).replace('/', '').replace(' ', '') if prefix_match else ''
            
            # 尝试多种关键词组合（渐进式）
            keywords_to_try = [keyword]
            # 1. 去掉斜杠和空格
            if '/' in keyword or ' ' in keyword:
                keywords_to_try.append(keyword.replace('/', '').replace(' ', ''))
            # 2. 去掉年份 (GB/T 1234-2024 -> GB/T 1234)
            if '-' in keyword:
                keywords_to_try.append(keyword.split('-')[0].strip())
            # 3. 仅保留数字 (GB/T 1234 -> 1234) - 仅当输入是GB标准时才使用
            # 避免 QB/T 1950 被搜索成纯数字 1950 导致误匹配 GB 1950
            if expected_prefix.startswith('GB') or expected_prefix.startswith('GJB'):
                num_match = re.search(r'(\d+)', keyword)
                if num_match:
                    keywords_to_try.append(num_match.group(1))
            
            # 去重并保持顺序
            keywords_to_try = list(dict.fromkeys(keywords_to_try))

            rows = []
            api_url = f"{self.api_base_url}/bzy-api/org/std/search" if self.api_base_url else None
            for kw in keywords_to_try:
                try:
                    # 搜索时允许重试，传入元组超时时间
                    if api_url:
                        rows = search_via_api(kw, page=page, page_size=page_size, session=session, api_url=api_url, timeout=(5, self.SEARCH_TIMEOUT))
                    else:
                        rows = search_via_api(kw, page=page, page_size=page_size, session=session, timeout=(5, self.SEARCH_TIMEOUT))
                    if rows:
                        # 过滤结果，确保标准类型和编号都匹配
                        filtered_rows = []
                        clean_keyword = re.sub(r'[^A-Z0-9]', '', keyword.upper())
                        for r in rows:
                            r_no = re.sub(r'[^A-Z0-9]', '', (r.get('standardNumDeal') or '').upper())
                            # 提取结果的标准类型前缀
                            r_prefix_match = re.match(r'([A-Z]+)', r_no)
                            r_prefix = r_prefix_match.group(1) if r_prefix_match else ''

                            # 严格匹配：标准类型必须一致
                            if expected_prefix and r_prefix:
                                if not r_prefix.startswith(expected_prefix):
                                    continue  # 标准类型不匹配，跳过

                            # 标准号匹配（模糊匹配）
                            if clean_keyword in r_no or r_no in clean_keyword:
                                filtered_rows.append(r)
                        if filtered_rows:
                            rows = filtered_rows
                            break  # 有匹配结果，不再尝试其他关键词
                except Exception:
                    continue  # 当前关键词失败，尝试下一个

            if rows:
                for row in rows:
                    try:
                        # Prefer standardNum (contains HTML) over standardNumDeal (stripped)
                        # but we must strip HTML tags from standardNum
                        raw_no = row.get('standardNum') or row.get('standardNumDeal') or ''
                        std_no = re.sub(r'<[^>]+>', '', raw_no).strip()
                        
                        name = (row.get('standardName') or '').strip()
                        # Also strip HTML from name just in case
                        name = re.sub(r'<[^>]+>', '', name).strip()
                        
                        # hasPdf 为 0 并不代表不能下载，可能可以预览
                        has_pdf = bool(int(row.get('hasPdf', 0))) if row.get('hasPdf') is not None else False
                        
                        # standardStatus 状态码映射
                        status_code = row.get('standardStatus')
                        status_map = {
                            '0': '即将实施',
                            '1': '现行',
                            '2': '废止',
                            '3': '有更新版本',
                            '4': '现行',  # 4也表示现行
                            0: '即将实施',
                            1: '现行',
                            2: '废止',
                            3: '有更新版本',
                            4: '现行',
                        }
                        status = status_map.get(status_code, str(status_code) if status_code is not None else '')
                        
                        # 修正状态逻辑：如果状态为"即将实施"但实施日期在过去，则修正为"现行"
                        impl = (row.get('standardUsefulDate') or row.get('standardUsefulTime') or row.get('standardUseDate') or row.get('implement') or '')
                        if status == '即将实施' and impl:
                            try:
                                from datetime import datetime
                                impl_date = str(impl)[:10]
                                if impl_date and impl_date < datetime.now().strftime('%Y-%m-%d'):
                                    status = '现行'
                            except Exception:
                                pass
                        
                        # 提取替代标准信息
                        replace_std = ''
                        # 尝试从各种可能的字段中提取替代标准
                        for key in ['standardReplaceStandard', 'replaceStandard', 'standardReplace', 'replaceBy', 'replacedBy', 'instead', 'supersede']:
                            if key in row and row[key]:
                                replace_std = str(row[key]).strip()
                                break
                        
                        # 如果 API 没有返回替代标准，尝试从补充数据库查询
                        if not replace_std:
                            try:
                                from core.replacement_db import get_replacement_standard
                                replace_std = get_replacement_standard(std_no)
                            except Exception:
                                pass
                        
                        meta = row
                        meta["_has_pdf"] = has_pdf
                        # Normalize publish/implement fields from possible API keys
                        pub = (row.get('standardPubTime') or row.get('publish') or '')
                        # impl 已在状态修正时提取，复用
                        items.append(Standard(std_no=std_no, name=name, publish_date=str(pub)[:10], implement_date=str(impl)[:10], status=status, replace_std=replace_std, has_pdf=has_pdf, source_meta=meta, sources=['ZBY']))
                    except Exception:
                        pass
                return items[:int(page_size)]
            
            # API 返回空：尝试 HTML 爬虫（对行业标准如 QB/T 更友好）
            if not rows:
                html_items = self._http_search_html_fallback(keyword, page=page, page_size=page_size, **kwargs)
                if html_items:
                    return html_items
        except Exception:
            pass
        
        return items

    def _http_search_html_fallback(self, keyword: str, page: int = 1, page_size: int = 20, **kwargs) -> List[Standard]:
        """最后的 HTML 爬取降级方案，仅在其他所有源都失败时才使用。"""
        items = []
        try:
            import requests
            from requests.adapters import HTTPAdapter
            from urllib3.util.retry import Retry

            session = requests.Session()
            session.trust_env = False  # 忽略系统代理
            # HTML fallback 也允许 1 次重试，快速失败
            retries = Retry(total=1, backoff_factor=0.3, status_forcelist=(500, 502, 503, 504))
            adapter = HTTPAdapter(max_retries=retries)
            session.mount('https://', adapter)
            session.mount('http://', adapter)

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                "Referer": str(self.base_url),
            }
            urls = [f"{self.base_url}/standardList", f"{self.base_url}/search", f"{self.base_url}/api/search"]
            resp_text = ""
            for u in urls:
                try:
                    # 显式禁用代理和 SSL 验证，超时8秒
                    r: Response = session.get(u, params={"searchText": keyword, "q": keyword}, headers=headers, timeout=8, proxies={"http": None, "https": None}, verify=False)
                    if r.status_code == 200 and r.text and len(r.text) > 200:
                        resp_text = r.text
                        break
                except Exception:
                    continue

            if not resp_text:
                return items

            blocks = re.findall(r'<h4.*?>(.*?)</h4>', resp_text, re.S)
            for title_html in blocks:
                title = re.sub(r'<.*?>', '', title_html).strip()
                if not title:
                    continue
                std_no = ''
                name = title
                m = re.match(r'^([A-Z0-9/\\-\\. ]+)\\s+(.*)$', title)
                if m:
                    std_no = m.group(1).strip()
                    name = m.group(2).strip()
                items.append(Standard(std_no=std_no, name=name, publish_date='', implement_date='', status='', has_pdf=False, source_meta={"title": title}, sources=['ZBY']))
            return items[:int(page_size)]
        except Exception:
            pass
        
        return items

    def download(self, item: Standard, outdir: Path) -> DownloadResult:
        """按新协议下载标准文档
        
        Args:
            item: Standard 对象
            outdir: 输出目录
            
        Returns:
            DownloadResult 对象
        """
        logs = []
        try:
            result = self._download_impl(item, outdir, log_cb=lambda msg: logs.append(msg))
            if result:
                if isinstance(result, tuple):
                    file_path, logged = result
                    if file_path:
                        return DownloadResult.ok(Path(file_path) if not isinstance(file_path, Path) else file_path, logs)
                else:
                    if result:
                        return DownloadResult.ok(Path(result) if not isinstance(result, Path) else result, logs)
            
            error_msg = logs[-1] if logs else "ZBY: Unknown error"
            return DownloadResult.fail(error_msg, logs)
        except Exception as e:
            return DownloadResult.fail(f"ZBY download exception: {str(e)}", logs)
    
    def _download_impl(self, item: Standard, outdir: Path, log_cb=None):
        """New Pure API Implementation"""
        outdir.mkdir(parents=True, exist_ok=True)
        logs = []
        def emit(msg: str) -> None:
            if not msg: return
            msg = re.sub(r'https?://[^\s<>"]+', '[URL]', msg)
            logs.append(msg)
            print(f"[ZBY TRACE] {msg}")
            if callable(log_cb):
                try:
                    log_cb(msg)
                except Exception:
                    pass

        emit(f"ZBY: Starting download for: {item.std_no}")

        # 1. Extract Standard ID
        meta = item.source_meta if isinstance(item.source_meta, dict) else {}
        std_id = meta.get("standardId") or meta.get("id") or meta.get("standardid")
        
        if not std_id:
            emit("ZBY: Meta missing ID, attempting search fallback...")
            kw = item.std_no or item.name
            if kw:
                try:
                    # Reuse existing HTTP search
                    results = self._search_impl(kw, page_size=1)
                    if results:
                         m2 = results[0].source_meta
                         std_id = m2.get("standardId") or m2.get("id")
                         if std_id:
                             emit(f"ZBY: Found ID via search: {std_id}")
                except Exception as e:
                    emit(f"ZBY: Search fallback failed: {e}")
        
        if not std_id:
            emit("ZBY: [FAILURE] Could not determine Standard ID")
            return None

        # 2. Get Title and Details (for filename)
        std_title, std_no = self._get_standard_details(std_id, emit)
        
        # 3. Get UUID
        has_pdf_hint = meta.get("_has_pdf", meta.get("hasPdf", True))
        if not has_pdf_hint and has_pdf_hint is not None:
             emit("ZBY: [INFO] Standard metadata indicates no PDF available (hasPdf=0). Skipping UUID extraction.")
             uuid, page_count, pdf_name = None, 0, ""
        else:
             uuid, page_count, pdf_name = self._get_uuid_via_api(std_id, emit)
        
        if uuid:
             # 4. Construct Filename
             filename_str = f"{item.std_no}.pdf" # Default
             
             if std_title:

                 # Remove illegal chars
                 safe_title = re.sub(r'[\/*?:"<>|]', "", std_title)
                 # Use retrieved std_no or item's std_no if missing
                 use_no = std_no if std_no else (item.std_no or pdf_name)
                 safe_no = re.sub(r'[\/*?:"<>|]', "", use_no)
                 filename_str = f"{safe_no} {safe_title}.pdf"
                 emit(f"ZBY: Filename set to: {filename_str}")
             elif pdf_name:
                 filename_str = f"{pdf_name}.pdf"
             
             final_path = outdir / filename_str
             
             # 5. Download
             result_path, _ = self._download_images_concurrently(uuid, page_count, final_path, emit)
             if result_path:
                 return str(result_path), logs
        else:
            emit("ZBY: [FAILURE] Could not extract UUID via API")
            
        return None


    def _get_standard_details(self, std_id: Union[str, int], emit: callable):
        emit(f"ZBY: Fetching details for std_id={std_id}...")
        
        base_url = "https://login.bz.zhenggui.vip/bzy-api/org/standard/stdcontent"
        
        # New correct payload
        payload = {
            "params": {
                "standardId": str(std_id),
                "clsName": None,
                "keyword": None
            },
            "token": "",
            "userId": "",
            "orgId": ""
        }
        
        query_params = _get_request_must_params("zby_org")
        
        headers = {
            "Content-Type": "application/json;charset=UTF-8",
            "Origin": "https://bz.zhenggui.vip",
            "Referer": f"https://bz.zhenggui.vip/standardDetail?standardId={std_id}&docStatus=0"
        }
        
        try:
            r = self.session.post(base_url, params=query_params, json=payload, headers=headers, timeout=(5, self.API_TIMEOUT))
            if r.status_code == 200:
                data = r.json()
                if data.get("code") == 1 and data.get("data"):
                     res = data["data"]
                     if isinstance(res, dict):
                         tittle = res.get("tittle", {})
                         name = tittle.get("standardName", "")
                         std_no = tittle.get("standardNum", "")
                     elif isinstance(res, list) and len(res) > 0:
                         item = res[0]
                         name = item.get("chineseName", "")
                         std_no = item.get("standardNo", "")
                     else:
                         name = ""
                         std_no = ""
                     emit(f"ZBY: Got Title: {name}, No: {std_no}")
                     return name, std_no
        except Exception as e:
            emit(f"ZBY: Detail Request Failed: {e}")
            
        return None, None

    def _get_uuid_via_api(self, std_id: Union[str, int], emit: callable):
        emit(f"ZBY: Extracting UUID for std_id={std_id}...")
        
        base_url = "https://login.bz.zhenggui.vip/bzy-api/org/standard/getPdfList"
        
        payload = {
            "params": str(std_id),
            "token": "",
            "userId": "",
            "orgId": ""
        }
        
        query_params = _get_request_must_params("zby_org")
        
        headers = {
            "Content-Type": "application/json;charset=UTF-8",
            "Origin": "https://bz.zhenggui.vip",
            "Referer": f"https://bz.zhenggui.vip/standardDetail?standardId={std_id}&docStatus=0"
        }
        
        try:
            r = self.session.post(base_url, params=query_params, json=payload, headers=headers, timeout=(5, self.API_TIMEOUT))
            
            if r.status_code == 200:
                data = r.json()
                if data.get("code") == 1 and data.get("data"):
                    item = data["data"][0]
                    uuid = item.get("immDoc")
                    page_count = item.get("aliyunPageCount", 0)
                    pdf_name = item.get("pdfName", "")
                    
                    emit(f"ZBY: Found UUID: {uuid}, PDF Name: {pdf_name}")
                    return uuid, page_count, pdf_name
        except Exception as e:
            emit(f"ZBY: UUID Request Failed: {e}")
            
        return None, 0, ""
    
    def has_pdf(self, item: Standard) -> bool:
        """
        Check if a standard has downloadable PDF by attempting to get UUID.
        
        Args:
            item: Standard object with metadata
            
        Returns:
            True if UUID can be obtained (PDF available), False otherwise
        """
        try:
            # Extract standardId from metadata
            std_id = None
            if isinstance(item.source_meta, dict):
                std_id = item.source_meta.get("standardId") or item.source_meta.get("id")
            
            if not std_id:
                return False
            
            # Try to get UUID - if successful, PDF is available
            def silent_emit(msg):
                pass  # Suppress output for availability check
            
            uuid, _, _ = self._get_uuid_via_api(std_id, silent_emit)
            return uuid is not None and uuid != ""
            
        except Exception:
            return False


    def _download_images_concurrently(self, uuid: str, page_count: int, output_file: Path, emit: callable):
        """Concurrent download of images to PDF using requests."""
        emit(f"ZBY: Starting concurrent download for UUID={uuid}...")
        
        output_dir = output_file.parent
        output_dir.mkdir(parents=True, exist_ok=True)
        
        temp_dir = output_dir / f"zby_temp_{int(time.time()*1000)}"
        if temp_dir.exists(): shutil.rmtree(temp_dir)
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Reuse self.session (which has a connection pool of 20 connections)
        session = self.session
        
        # helper: try download a single page
        def download_page(page_num):
            base_urls = [
                f"https://resource.zhenggui.vip/immdoc/{uuid}/doc/I/{page_num}", # Most common
                f"https://resource.zhenggui.vip/immdoc/{uuid}/doc/page{page_num:04d}.png",
                f"https://resource.zhenggui.vip/immdoc/{uuid}/doc/page{page_num:04d}.jpg"
            ]
            
            for url in base_urls:
                try:
                    # Fetch image with retry mechanism enabled via self.session
                    r = session.get(url, timeout=(5, self.DOWNLOAD_TIMEOUT), verify=False)
                    if r.status_code == 200:
                        ct = r.headers.get("Content-Type", "").lower()
                        ext = ".png" if "png" in ct else ".jpg"
                        save_path = temp_dir / f"{page_num:04d}{ext}"
                        with open(save_path, "wb") as f:
                            f.write(r.content)
                        return page_num, save_path
                    elif r.status_code == 404:
                        continue
                except Exception:
                    pass
            return page_num, None

        # Batch Execution Loop
        downloaded_files = []
        page = 1
        batch_size = 20
        max_pages = 1000 
        
        start_time = time.time()

        while page < max_pages:
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                chunk_futures = {executor.submit(download_page, p): p for p in range(page, page + batch_size)}
                
                chunk_results = {}
                for future in concurrent.futures.as_completed(chunk_futures):
                    p_num, path = future.result()
                    chunk_results[p_num] = path
                
                batch_has_data = False
                for p in range(page, page + batch_size):
                    if chunk_results.get(p):
                        downloaded_files.append(chunk_results[p])
                        batch_has_data = True
                
                if not batch_has_data:
                    break
                    
                if page == 1 and not chunk_results.get(1):
                    emit("ZBY: [WARNING] Page 1 not found. Document might be empty.")
                    break

                first_missing = -1
                for p in range(page, page + batch_size):
                    if not chunk_results.get(p):
                        first_missing = p
                        break
                
                if first_missing != -1:
                    break
                    
                page += batch_size

        duration = time.time() - start_time
        emit(f"ZBY: Download finished in {duration:.2f}s. Total Pages: {len(downloaded_files)}")

        if downloaded_files:
            downloaded_files.sort()
            emit(f"ZBY: Generating PDF: {output_file}")
            try:
                temp_pdf_path = str(output_file) + ".tmp"
                with open(temp_pdf_path, "wb") as f:
                    f.write(img2pdf.convert([str(p) for p in downloaded_files]))
                
                # Atomic move
                if Path(temp_pdf_path).exists():
                    shutil.move(temp_pdf_path, output_file)
                    
                emit(f"ZBY: [SUCCESS] PDF Saved to {output_file}")
                # Cleanup
                if temp_dir.exists(): shutil.rmtree(temp_dir)
                return output_file, []
            except Exception as e:
                emit(f"ZBY: [ERROR] PDF Generation failed: {e}")
                
        # Cleanup
        if temp_dir.exists(): shutil.rmtree(temp_dir)
        return None

    def _download_via_standard_id(self, std_id: str, item: Standard, output_dir: Path, emit: callable):
        """通过 standardId 直接访问 standardDetail 页面，提取文档 URL 并下载。

        该方法尝试从 https://bz.zhenggui.vip/standardDetail?standardId={id} 页面
        提取文档下载链接或资源 UUID。
        """
        try:
            import requests
        except Exception:
            return None

        try:
            session = requests.Session()
            session.trust_env = False
            session.headers.update({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                "Referer": self.base_url,
            })

            # 访问 standardDetail 页面
            detail_url = f"{self.base_url}/standardDetail?standardId={std_id}&docStatus=0"
            emit(f"ZBY: 访问详情页: standardId={std_id}")

            try:
                r = session.get(detail_url, timeout=10, proxies={"http": None, "https": None})
                if r.status_code != 200:
                    return None
                html = r.text or ""
            except Exception as e:
                emit(f"ZBY: 访问详情页失败: {e}")
                return None

            # 使用工具函数提取 UUID
            uuid = extract_uuid_from_text(html)
            if uuid:
                emit(f"ZBY: 从详情页提取到 UUID: {uuid[:8]}...")
                cookies = [{'name': c.name, 'value': c.value} for c in session.cookies]
                result = download_images_to_pdf(uuid, item.filename(), output_dir, cookies, emit)
                if result:
                    return result, []
                return result

            # 尝试从 HTML 中搜索 PDF 直链
            pdf_links = re.findall(r'(https?://[^\s"<>]+\.pdf)', html, re.IGNORECASE)
            for pdf_url in pdf_links:
                try:
                    emit("ZBY: 尝试直接下载 PDF 链接...")
                    r = session.get(pdf_url, timeout=(5, self.DOWNLOAD_TIMEOUT), stream=True, proxies={"http": None, "https": None}, verify=False)
                    if r.status_code == 200:
                        output_path = output_dir / item.filename()
                        output_dir.mkdir(parents=True, exist_ok=True)
                        with open(output_path, 'wb') as f:
                            for chunk in r.iter_content(8192):
                                if chunk:
                                    f.write(chunk)
                        emit("ZBY: PDF 下载成功")
                        return output_path, []
                except Exception:
                    continue

            emit("ZBY: 从详情页无法提取到文档资源")
            return None

        except Exception as e:
            emit(f"ZBY: standardId 下载异常: {e}")
            return None

    def _http_download_via_uuid(self, item: Standard, output_dir: Path, emit: callable):
        """试图通过 HTTP 抓取详情页或搜索页 HTML，查找 immdoc/{uuid}/doc 链接并直接下载图片合成 PDF。"""
        try:
            import requests
        except Exception:
            return None

        emit("ZBY: 尝试 HTTP 回退提取资源 UUID...")
        session = self.session # 复用 session 以保持 cookie/状态
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Referer": (self.base_url or "https://bz.zhenggui.vip"),
        })

        meta = item.source_meta if isinstance(item.source_meta, dict) else {}

        # 0) 优先尝试通过官方 API（从 config.yaml 读取到的 BZY_BASE_URL）拿到预览/资源信息
        try:
            api_base = (self.api_base_url or "").strip()
            # 移除强制回退逻辑，信任用户的配置 (支持私有 API)
            if not api_base:
                api_base = "https://login.bz.zhenggui.vip/bzy-api"
            
            # 清理 base，移除末尾的 /org (以便统一拼接)
            if api_base.endswith("/org"):
                api_base = api_base[:-4]

            if api_base:
                std_id = meta.get('standardId') or meta.get('id')
                std_num = item.std_no
                
                # 打印详细 Meta 数据以供调试
                print(f"[ZBY TRACE] Meta Detail: {json.dumps(meta, ensure_ascii=False, default=str)[:1000]}")
                
                emit(f"ZBY: 尝试通过 API 获取预览资源 (Base: {api_base})...")
                api_attempts = 0
                api_status_counts = {}
                api_sample = ""
                
                api_candidates = [
                    "org/std/search", "std/search",  # Search endpoints
                    "org/std/detail", "org/std/getDetail", # Detail endpoints
                    "org/std/resource", "org/std/preview",
                    "std/detail", "std/getDetail", "std/preview", "std/resource",
                ]
                
                # 构造多种请求体
                bodies = []
                # 1. 如果有 ID，尝试 ID 查询
                if std_id:
                    bodies.append({"params": {"standardId": std_id}, "token": "", "userId": "", "orgId": "", "time": ""})
                    bodies.append({"params": {"model": {"standardId": std_id}}, "token": "", "userId": "", "orgId": "", "time": ""})
                    bodies.append({"standardId": std_id})
                    bodies.append({"id": std_id})
                
                # 2. 尝试用标准号查询 (模仿 zby_http.py)
                if std_num:
                   bodies.append({
                        "params": {
                            "pageNo": 1, "pageSize": 10,
                            "model": {
                                "standardNum": std_num if '-' in std_num or '/' in std_num else None,
                                "keyword": std_num,
                                "searchType": "1"
                            }
                        },
                        "token": "", "userId": "", "orgId": "", "time": ""
                   })

                def _scan_for_uuid(obj) -> str:
                    try:
                        s = json.dumps(obj, ensure_ascii=False)
                    except Exception:
                        s = str(obj)
                    
                    # 1) 优先匹配 immdoc/{uuid}/doc
                    m = re.search(r"immdoc/([a-zA-Z0-9]{32})/doc", s)
                    if m: return m.group(1)
                    m = re.search(r"immdoc/([a-zA-Z0-9-]+)/doc", s)
                    if m: return m.group(1)
                        
                    # 2) 再匹配标准 UUID 形式
                    m = re.search(r"[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}", s, re.I)
                    if m: return m.group(0)
                        
                    # 3) 匹配 32 位纯十六进制 ID
                    m = re.search(r'\\b[a-f0-9]{32}\\b', s, re.IGNORECASE)
                    return m.group(0) if m else ""

                headers: dict[str, str] = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                    "Referer": api_base,
                    "Content-Type": "application/json;charset=UTF-8",
                }
                
                # 去重并执行调用
                for ep in api_candidates:
                    base_clean = api_base.rstrip('/')
                    ep_clean = ep.lstrip('/')
                    api_url = f"{base_clean}/{ep_clean}"
                    
                    for body in bodies:
                        try:
                            api_attempts += 1
                            print(f"[ZBY TRACE] POST {api_url}")
                            rr: Response = session.post(api_url, json=body, headers=headers, timeout=10, verify=False)
                            status = int(getattr(rr, 'status_code', 0) or 0)
                            api_status_counts[status] = api_status_counts.get(status, 0) + 1
                            
                            if status == 200:
                                j = rr.json()
                                uuid = _scan_for_uuid(j)
                                if uuid:
                                    emit(f"ZBY: 从 API 获取到资源 UUID: {uuid[:8]}...")
                                    return download_images_to_pdf(uuid, item.filename(), output_dir, [], emit)
                            elif status >= 400 and not api_sample:
                                api_sample = f"HTTP {status}"
                        except Exception:
                            continue

                if api_attempts:
                     status_summary = str(api_status_counts)
                     emit(f"ZBY: API 未命中 (尝试{api_attempts}次, 状态={status_summary})")

        except Exception as e:
            import traceback
            print(f"[ZBY TRACE] API 逻辑异常: {e}")
            traceback.print_exc()
            emit(f"ZBY: API 逻辑异常: {e}")
        
        # 1. 尝试通过 standardId 直接访问详情页（SPA 可能只返回壳，但仍保留作为兜底）
        std_id = meta.get('standardId') or meta.get('id')
        if std_id:
            # 尝试访问前端详情页 (可能包含内嵌 JS 数据)
            detail_urls = [
                f"https://bz.zhenggui.vip/standardDetail?standardId={std_id}", # 前端路由页
                f"{self.base_url}/standard/detail/{std_id}",
            ]
            
            for du in detail_urls:
                try:
                    emit(f"ZBY: 检查详情页: {du}")
                    r: Response = session.get(du, timeout=10, verify=False)
                    if r.status_code == 200:
                        # 尝试提取所有可能的 UUID
                        uuid = extract_uuid_from_text(r.text)
                        
                        # 特殊检查：在 JS 变量中查找 hex ID
                        if not uuid:
                            for m in re.finditer(r'["\']([a-f0-9]{32})["\']', r.text, re.IGNORECASE):
                                potential_id = m.group(1)
                                if not potential_id.startswith('0000'): 
                                     # 仅作为尝试
                                     res = download_images_to_pdf(potential_id, item.filename(), output_dir, [], emit)
                                     if res: return res

                        if uuid:
                            emit(f"ZBY: 从详情页发现资源 UUID: {uuid[:8]}...")
                            return download_images_to_pdf(uuid, item.filename(), output_dir, [], emit)
                except Exception:
                    continue


        # 1. 先检查 meta 中是否存在直接可用的 pdf/文件列表（json api 可能返回）
        try:
            for list_key in ('pdfList', 'taskPdfList', 'fileList', 'files'):
                lst = meta.get(list_key)
                if not lst:
                    continue
                # 期望 lst 为可迭代的条目集合
                for entry in (lst if isinstance(lst, list) else [lst]):
                    url = None
                    if isinstance(entry, dict):
                        # 常见字段名
                        for k in ('url', 'fileUrl', 'downloadUrl', 'resourceUrl'):
                            if entry.get(k):
                                url = entry.get(k)
                                break
                        # 某些接口返回的是资源id或uuid字段
                        if not url:
                            for k in ('uuid', 'resourceId', 'docId', 'fileId'):
                                if entry.get(k):
                                    # 构造可能的 immdoc 链接
                                    url = f"https://resource.zhenggui.vip/immdoc/{entry.get(k)}/doc/I/1"
                                    break
                    elif isinstance(entry, str):
                        url = entry

                    if not url:
                        continue

                    # 使用工具函数提取 UUID
                    uuid = extract_uuid_from_text(url)
                    if uuid:
                        emit(f"ZBY: 从 meta 发现可用资源 UUID: {uuid[:8]}...，尝试 HTTP 下载")
                        return download_images_to_pdf(uuid, item.filename(), output_dir, [], emit)

                    # 若为 PDF 文件链接，直接下载并保存
                    try:
                        if url.lower().endswith('.pdf') or 'download' in url or 'pdf' in url:
                            import requests
                            # 显式禁用代理
                            r: Response = requests.get(url, timeout=(5, self.DOWNLOAD_TIMEOUT), stream=True, proxies={"http": None, "https": None}, verify=False)
                            if r.status_code == 200:
                                outp = output_dir / item.filename()
                                with open(outp, 'wb') as f:
                                    for chunk in r.iter_content(8192):
                                        if chunk:
                                            f.write(chunk)
                                emit(f"ZBY: 从 meta 下载到 PDF -> {outp}")
                                return outp, []
                    except Exception:
                        # 下载失败则继续尝试其他条目/方法
                        continue
        except Exception:
            pass

        # 如果已经尝试过详情页且失败了，且我们有明确的 ID，那么搜索页通常也不会有更多信息
        # 除非是想通过搜索页的 HTML 结构碰运气。这里减少搜索次数。
        if std_id:
            search_keywords = [item.std_no] # 仅尝试标准号
        else:
            title = meta.get('title') or f"{item.std_no} {item.name}".strip()
            search_keywords = [title, item.std_no]
        
        urls = [f"{self.base_url}/standardList"] # 仅尝试一个搜索接口
        
        try:
            for kw in search_keywords:
                if not kw: continue
                for u in urls:
                    try:
                        emit(f"ZBY: 尝试搜索关键词: {kw}")
                        # 显式禁用代理
                        r: Response = session.get(u, params={"searchText": kw, "q": kw, "keyword": kw}, timeout=10, proxies={"http": None, "https": None})
                        text = getattr(r, 'text', '') or ''

                        # 使用工具函数查找 UUID
                        uuid = extract_uuid_from_text(text)
                        if uuid:
                            emit(f"ZBY: 发现资源 UUID: {uuid[:8]}...")
                            cookies = [{ 'name': c.name, 'value': c.value } for c in session.cookies]
                            return download_images_to_pdf(uuid, item.filename(), output_dir, cookies, emit)

                        # 2. 查找详情页链接并跟进
                        # 匹配模式如 /standard/detail/566393 或 #/standard/detail/566393
                        detail_ids = re.findall(r'detail/(\d+)', text)
                        for did in detail_ids[:5]: # 只尝试前5个
                            detail_url = f"{self.base_url}/standard/detail/{did}"
                            try:
                                emit("ZBY: 尝试跟进详情页...")
                                rd: Response = session.get(detail_url, timeout=8, proxies={"http": None, "https": None})
                                td = getattr(rd, 'text', '') or ''
                                uuid2 = extract_uuid_from_text(td)
                                if uuid2:
                                    emit(f"ZBY: 从详情页发现资源 UUID: {uuid2[:8]}...")
                                    cookies = [{ 'name': c.name, 'value': c.value } for c in session.cookies]
                                    return download_images_to_pdf(uuid2, item.filename(), output_dir, cookies, emit)
                            except Exception:
                                continue
                    except Exception:
                        continue
        except Exception:
            return None

        return None


