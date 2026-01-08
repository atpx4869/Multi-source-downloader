# -*- coding: utf-8 -*-
"""
Lightweight ZBY adapter with HTTP-first fallback and debug artifact mirroring.

This module avoids importing Playwright at module-import time so it is safe
to include in frozen executables. If Playwright is needed it will be loaded
only at runtime by explicit callers.
"""
from http.cookiejar import Cookie
from http.cookiejar import Cookie
from http.cookiejar import Cookie
from pathlib import Path
from typing import Dict, Dict, Dict, Dict, List, Union
import re
import tempfile
import shutil
import os

from requests import Response

from requests import Response

from sources.zby_playwright import ZBYSource

from requests import Response

from sources.zby_playwright import ZBYSource

from requests import Response

from requests import Response

from requests import Response

from requests import Response

from requests import Response

from requests import Response

DEFAULT_BASE_URL = "https://bz.zhenggui.vip"

from core.models import Standard


# Prefer local shim; fall back to dotted import for compatibility
try:
    from .standard_downloader import StandardDownloader  # type: ignore
except Exception:
    try:
        from standard_downloader import StandardDownloader  # type: ignore
    except Exception:
        StandardDownloader = None


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
            desk: Path = Path(os.path.expanduser('~')) / 'Desktop'
            desk.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(p), str(desk / p.name))
        except Exception:
            pass
    except Exception:
        pass


class ZBYSource:
    name: str = "ZBY"
    priority = 3

    def __init__(self, output_dir: Union[Path, str] = "downloads") -> None:
        od = Path(output_dir)
        try:
            if (isinstance(output_dir, str) and output_dir == "downloads") or (isinstance(output_dir, Path) and not Path(output_dir).is_absolute()):
                repo_root: Path = Path(__file__).resolve().parents[1]
                od: Path = repo_root / "downloads"
        except Exception:
            od = Path(output_dir)
        self.output_dir = Path(od)

        try:
            import sys as _sys
            frozen: re.Any | bool = getattr(_sys, 'frozen', False)
        except Exception:
            frozen = False

        self.client = None
        self.allow_playwright: bool = False if frozen else True
        self.base_url: str = DEFAULT_BASE_URL
        self.api_base_url = None

        if not frozen and StandardDownloader is not None:
            try:
                self.client = StandardDownloader(output_dir=self.output_dir)
                self.base_url: re.Any | str = getattr(self.client, 'base_url', DEFAULT_BASE_URL)
            except Exception:
                self.client = None
                self.base_url: str = DEFAULT_BASE_URL

        # 尝试从前端 config.yaml 读取真实 API 基址（无需额外依赖）
        try:
            self.api_base_url: str = self._load_api_base_url_from_config(timeout=4)
        except Exception:
            self.api_base_url = None

    def _load_api_base_url_from_config(self, timeout: int = 4) -> str:
        """从 https://bz.zhenggui.vip/config.yaml 读取 BZY_BASE_URL。

        config.yaml 内容很简单，这里用正则解析，避免引入 PyYAML。
        """
        try:
            import requests
        except Exception:
            return ""
        try:
            url: str = f"{DEFAULT_BASE_URL}/config.yaml"
            s = requests.Session()
            s.trust_env = False
            r: Response = s.get(url, timeout=timeout, proxies={"http": None, "https": None})
            if getattr(r, 'status_code', 0) != 200:
                return ""
            text: str = r.text or ""
            m: re.Match[str] | None = re.search(r"BZY_BASE_URL:\s*['\"]([^'\"]+)['\"]", text)
            if not m:
                return ""
            return (m.group(1) or "").strip()
        except Exception:
            return ""

    def _mirror_debug_file(self, p: Path) -> None:
        try:
            _mirror_debug_file_static(p)
        except Exception:
            pass

    def is_available(self, timeout: int = 6) -> bool:
        try:
            import sys as _sys
            frozen: re.Any | bool = getattr(_sys, 'frozen', False)
        except Exception:
            frozen = False

        try:
            if frozen:
                import requests
                # 显式禁用代理，避免系统代理干扰
                r: Response = requests.get(self.base_url, timeout=timeout, proxies={"http": None, "https": None})
                return 200 <= getattr(r, 'status_code', 0) < 400
            if self.client is not None and hasattr(self.client, 'is_available'):
                return bool(self.client.is_available())
            return True
        except Exception:
            return False

    def search(self, keyword: str, **kwargs) -> List[Standard]:
        items: List[Standard] = []

        # First try client implementation (if available)
        if self.client is not None:
            try:
                rows: List[re.Any] = self.client.search(keyword, **kwargs)
                if rows:
                    return rows
            except Exception:
                pass

        # HTTP fallback
        try:
            http_items: List[Standard] = self._http_search(keyword, **kwargs)
            if http_items:
                return http_items
        except Exception:
            pass

        # Playwright fallback (only when allowed)
        if self.allow_playwright:
            try:
                from .zby_playwright import ZBYSource as PWZBYSource  # type: ignore
                pw: ZBYSource = PWZBYSource(self.output_dir)
                return pw.search(keyword, **kwargs)
            except Exception:
                pass

        return items

    def _http_search(self, keyword: str, page: int = 1, page_size: int = 20, **kwargs) -> List[Standard]:
        items: List[Standard] = []
        try:
            import requests
            from requests.adapters import HTTPAdapter
            from urllib3.util.retry import Retry

            session = requests.Session()
            session.trust_env = False  # 忽略系统代理
            retries = Retry(total=2, backoff_factor=0.3, status_forcelist=(500, 502, 503, 504))
            adapter = HTTPAdapter(max_retries=retries)
            session.mount('https://', adapter)
            session.mount('http://', adapter)

            # Try JSON API first via helper
            try:
                from .zby_http import search_via_api
                
                # 尝试多种关键词组合
                keywords_to_try: List[str] = [keyword]
                # 1. 去掉斜杠和空格
                if '/' in keyword or ' ' in keyword:
                    keywords_to_try.append(keyword.replace('/', '').replace(' ', ''))
                # 2. 去掉年份 (GB/T 1234-2024 -> GB/T 1234)
                if '-' in keyword:
                    keywords_to_try.append(keyword.split('-')[0].strip())
                # 3. 仅保留数字 (GB/T 1234 -> 1234)
                num_match: re.Match[str] | None = re.search(r'(\d+)', keyword)
                if num_match:
                    keywords_to_try.append(num_match.group(1))
                
                # 去重并保持顺序
                keywords_to_try: List[str] = list(dict.fromkeys(keywords_to_try))
                
                rows = []
                for kw: str in keywords_to_try:
                    try:
                        rows: List[Dict[str, Any]] = search_via_api(kw, page=page, page_size=page_size, session=session)
                        if rows:
                            # 过滤结果，确保标准号匹配（模糊匹配）
                            filtered_rows = []
                            clean_keyword: str = re.sub(r'[^A-Z0-9]', '', keyword.upper())
                            for r: Dict[str, Any] in rows:
                                r_no: str = re.sub(r'[^A-Z0-9]', '', (r.get('standardNumDeal') or '').upper())
                                if clean_keyword in r_no or r_no in clean_keyword:
                                    filtered_rows.append(r)
                            if filtered_rows:
                                rows = filtered_rows
                                break
                    except Exception:
                        continue
                
                if rows:
                    for row: Dict[str, Any] in rows:
                        try:
                            # Prefer standardNum (contains HTML) over standardNumDeal (stripped)
                            # but we must strip HTML tags from standardNum
                            raw_no: re.Any | str = row.get('standardNum') or row.get('standardNumDeal') or ''
                            std_no: str = re.sub(r'<[^>]+>', '', raw_no).strip()
                            
                            name: str | re.Any = (row.get('standardName') or '').strip()
                            # Also strip HTML from name just in case
                            name: str = re.sub(r'<[^>]+>', '', name).strip()
                            
                            # hasPdf 为 0 并不代表不能下载，可能可以预览
                            has_pdf: bool = bool(int(row.get('hasPdf', 0))) if row.get('hasPdf') is not None else False
                            # standardStatus is provided as numeric code by the backend; map to human-readable labels
                            from .status_map import map_status
                            status: str = map_status(row.get('standardStatus'))
                            meta: Dict[str, Any] = row
                            # Normalize publish/implement fields from possible API keys
                            pub: re.Any | str = (row.get('standardPubTime') or row.get('publish') or '')
                            impl: re.Any | str = (row.get('standardUsefulDate') or row.get('standardUsefulTime') or row.get('standardUseDate') or row.get('implement') or '')
                            items.append(Standard(std_no=std_no, name=name, publish=str(pub)[:10], implement=str(impl)[:10], status=status, has_pdf=has_pdf, source_meta=meta, sources=['ZBY']))
                        except Exception:
                            pass
                    return items[:int(page_size)]
            except Exception:
                pass

            # HTML fallback (existing behavior)
            urls: List[str] = [f"{self.base_url}/standardList", f"{self.base_url}/search", f"{self.base_url}/api/search"]
            resp_text: str = ""
            for u: str in urls:
                try:
                    # 显式禁用代理
                    r: Response = session.get(u, params={"searchText": keyword, "q": keyword}, headers=headers, timeout=6, proxies={"http": None, "https": None})
                    if r.status_code == 200 and r.text and len(r.text) > 200:
                        resp_text: str = r.text
                        break
                except Exception:
                    continue

            if not resp_text:
                return items

            blocks: List[re.Any] = re.findall(r'<h4.*?>(.*?)</h4>', resp_text, re.S)
            for title_html in blocks:
                title: str = re.sub(r'<.*?>', '', title_html).strip()
                if not title:
                    continue
                std_no: str = ''
                name: str = title
                m: re.Match[str] | None = re.match(r'^([A-Z0-9/\\-\\. ]+)\\s+(.*)$', title)
                if m:
                    std_no: str | re.Any = m.group(1).strip()
                    name: str | re.Any = m.group(2).strip()
                items.append(Standard(std_no=std_no, name=name, publish='', implement='', status='', has_pdf=False, source_meta={"title": title}, sources=['ZBY']))
            return items[:int(page_size)]
        except Exception:
            return items

    def download(self, item: Standard, outdir: Path, log_cb=None):
        """下载标准。签名兼容两种调用方式：
        - download(item, outdir, log_cb=callable)  -> (Path|None, list[str])
        - download(item, outdir) -> Path|None
        返回 (path, logs) 或直接 path/None（兼容旧实现）。
        """
        outdir.mkdir(parents=True, exist_ok=True)
        logs = []
        def emit(msg: str) -> None:
            if not msg:
                return
            # 涉及保密，脱敏处理：隐藏所有网址
            msg = re.sub(r'https?://[^\s<>"]+', '[URL]', msg)
            
            logs.append(msg)
            if callable(log_cb):
                try:
                    log_cb(msg)
                except Exception:
                    pass

        # 若 meta 过于精简（仅有 title/has_pdf），尝试用 HTTP 搜索补充 standardId 等字段，便于后续下载
        try:
            meta = item.source_meta if isinstance(item.source_meta, dict) else {}
            has_id: bool = any(k in meta for k: str in ("standardId", "id", "standardid"))
            if not has_id:
                kw: str = item.std_no or item.name
                if kw:
                    http_items: List[Standard] = self._http_search(kw, page_size=3)
                    for hi: Standard in http_items:
                        m2 = hi.source_meta if isinstance(hi.source_meta, dict) else {}
                        if any(k in m2 for k: str in ("standardId", "id", "standardid")):
                            item = hi
                            break
        except Exception:
            pass

        # Prefer client implementation when available
        if self.client is not None and hasattr(self.client, 'download_standard'):
            try:
                path: Path | None = self.client.download_standard(item.source_meta)
                p: Path | None = Path(path) if path else None
                if p:
                    if callable(log_cb):
                        return p, logs
                    return p
                # client 存在但返回空：不要在这里终止，继续走 HTTP/Playwright 回退
                emit("ZBY: client.download_standard 返回空，尝试 HTTP 回退")
            except Exception as e: Exception:
                emit(f"ZBY: client.download_standard 异常: {e}")

        # 新增：若 meta 中有 standardId，尝试直接调用 standardDetail 页面获取文档
        try:
            meta = item.source_meta if isinstance(item.source_meta, dict) else {}
            std_id = meta.get("standardId") or meta.get("id") or meta.get("standardid")
            if std_id:
                emit(f"ZBY: 尝试通过 standardId ({std_id}) 直接获取文档...")
                http_try = self._download_via_standard_id(std_id, item, outdir, emit)
                if http_try is not None:
                    return http_try
        except Exception as e:
            emit(f"ZBY: standardId 直接获取失败: {e}")

        # 一步：尝试通过 HTTP 直接从详情页提取资源 UUID 并下载（无需 Playwright）
        try:
            http_try = self._http_download_via_uuid(item, outdir, emit)
            if http_try is not None:
                return http_try
        except Exception as e: Exception:
            emit(f"ZBY: HTTP 回退提取 UUID 失败: {e}")

        if self.allow_playwright:
            try:
                from .zby_playwright import ZBYSource as PWZBYSource  # type: ignore
                pw: ZBYSource = PWZBYSource(output_dir=outdir)
                try:
                    result = pw.download(item, outdir, log_cb=log_cb)
                except TypeError:
                    result = pw.download(item, outdir)
                # 确保返回格式一致
                if isinstance(result, tuple):
                    return result
                else:
                    if callable(log_cb):
                        return (Path(result) if result else None, logs)
                    return Path(result) if result else None
            except Exception as e: Exception:
                emit(f"ZBY: Playwright 回落失败: {e}")

        emit("ZBY: 无法下载（缺少 StandardDownloader 且 Playwright 不可用或失败）")
        if callable(log_cb):
            return None, logs
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
            
            # 尝试从 HTML 中提取多种可能的 UUID/下载链接
            # 1) 直接匹配 immdoc/{uuid}/doc
            m = re.search(r'immdoc/([a-zA-Z0-9-]+)/doc', html)
            if m:
                uuid = m.group(1)
                emit(f"ZBY: 从详情页提取到 UUID: {uuid[:8]}...")
                cookies = [{'name': c.name, 'value': c.value} for c in session.cookies]
                return self._download_images(uuid, item.filename(), output_dir, cookies, emit)
            
            # 2) 尝试匹配任何 UUID 格式
            uuids = re.findall(r'[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}', html)
            for uuid in uuids:
                emit(f"ZBY: 尝试提取到的 UUID: {uuid[:8]}...")
                cookies = [{'name': c.name, 'value': c.value} for c in session.cookies]
                res = self._download_images(uuid, item.filename(), output_dir, cookies, emit)
                if res:
                    return res
            
            # 3) 尝试从 HTML 中搜索 PDF 直链
            pdf_links = re.findall(r'(https?://[^\s"<>]+\.pdf)', html, re.IGNORECASE)
            for pdf_url in pdf_links:
                try:
                    emit(f"ZBY: 尝试直接下载 PDF 链接...")
                    r = session.get(pdf_url, timeout=20, stream=True, proxies={"http": None, "https": None})
                    if r.status_code == 200:
                        output_path = output_dir / item.filename()
                        output_dir.mkdir(parents=True, exist_ok=True)
                        with open(output_path, 'wb') as f:
                            for chunk in r.iter_content(8192):
                                if chunk:
                                    f.write(chunk)
                        emit(f"ZBY: PDF 下载成功")
                        if callable(emit):
                            return output_path, []
                        return output_path
                except Exception:
                    continue
            
            emit(f"ZBY: 从详情页无法提取到文档资源")
            return None
            
        except Exception as e:
            emit(f"ZBY: standardId 下载异常: {e}")
            return None

    def _download_images(self, uuid: str, filename: str, output_dir: Path, cookies: list, emit: callable):
        """通过资源 UUID 下载分页图片并合成 PDF。

        该逻辑不依赖 Playwright，仅需 requests + img2pdf。
        """
        try:
            import requests
        except Exception:
            emit("ZBY: requests 不可用，无法下载")
            return None

        try:
            import img2pdf
        except Exception:
            emit("ZBY: 缺少 img2pdf，无法合成 PDF")
            return None

        try:
            uuid = (uuid or "").strip()
            if not uuid:
                return None
            emit(f"ZBY: 获取到UUID: {uuid[:8]}..., 开始下载")

            temp_dir: Path = output_dir / "zby_temp"
            try:
                if temp_dir.exists():
                    shutil.rmtree(temp_dir)
            except Exception:
                pass
            temp_dir.mkdir(parents=True, exist_ok=True)

            # cookies: list[{'name':..., 'value':...}] -> dict
            cookies_dict = {}
            try:
                for c in (cookies or []):
                    if isinstance(c, dict) and c.get('name'):
                        cookies_dict[str(c.get('name'))] = str(c.get('value') or '')
            except Exception:
                cookies_dict = {}

            session = requests.Session()
            session.trust_env = False

            imgs = []
            page_num = 1
            while True:
                try:
                    url: str = f"https://resource.zhenggui.vip/immdoc/{uuid}/doc/I/{page_num}"
                    r: Response = session.get(url, cookies=cookies_dict, timeout=15, proxies={"http": None, "https": None})
                    if getattr(r, 'status_code', 0) != 200 or not getattr(r, 'content', b''):
                        break
                    img_path: Path = temp_dir / f"{page_num:04d}.jpg"
                    with open(img_path, 'wb') as f: os.BufferedWriter:
                        f.write(r.content)
                    imgs.append(str(img_path))
                    if page_num % 5 == 0:
                        emit(f"ZBY: 已下载 {page_num} 页")
                    page_num += 1
                except Exception as e: Exception:
                    emit(f"ZBY: 第 {page_num} 页下载失败: {e}")
                    break

            if imgs:
                emit(f"ZBY: 共 {len(imgs)} 页，正在合成PDF...")
                output_path: Path = output_dir / filename
                with open(output_path, "wb") as f: os.BufferedWriter:
                    f.write(img2pdf.convert(imgs))
                emit("ZBY: PDF生成成功")
                try:
                    shutil.rmtree(temp_dir)
                except Exception:
                    pass
                return output_path, []

            emit("ZBY: 未下载到任何页面")
            return None
        except Exception as e: Exception:
            emit(f"ZBY: _download_images 异常: {e}")
            return None

    def _http_download_via_uuid(self, item: Standard, output_dir: Path, emit: callable):
        """试图通过 HTTP 抓取详情页或搜索页 HTML，查找 immdoc/{uuid}/doc 链接并直接下载图片合成 PDF。"""
        try:
            import requests
        except Exception:
            return None

        emit("ZBY: 尝试 HTTP 回退提取资源 UUID...")
        session = requests.Session()
        session.trust_env = False  # 禁用系统代理
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Referer": self.base_url,
        })

        meta = item.source_meta if isinstance(item.source_meta, dict) else {}

        # 0) 优先尝试通过官方 API（从 config.yaml 读取到的 BZY_BASE_URL）拿到预览/资源信息
        try:
            api_base: str = (self.api_base_url or "").strip()
            if api_base:
                std_id = meta.get('standardId') or meta.get('id')
                if std_id:
                    emit("ZBY: 尝试通过 API 获取预览资源...")
                    api_attempts = 0
                    api_status_counts = {}
                    api_sample: str = ""
                    api_candidates: List[str] = [
                        "std/detail",
                        "std/getDetail",
                        "std/detailInfo",
                        "std/getStdDetail",
                        "std/preview",
                        "std/previewInfo",
                        "std/getPreview",
                        "std/getAliyunPreview",
                        "std/getDocInfo",
                        "std/resource",
                        "std/getResource",
                    ]
                    bodies = [
                        {"params": {"standardId": std_id}, "token": "", "userId": "", "orgId": "", "time": ""},
                        {"params": {"model": {"standardId": std_id}}, "token": "", "userId": "", "orgId": "", "time": ""},
                        {"standardId": std_id},
                        {"id": std_id},
                    ]

                    def _scan_for_uuid(obj) -> str:
                        try:
                            import json as _json
                            s: str = _json.dumps(obj, ensure_ascii=False)
                        except Exception:
                            s = str(obj)
                        # 1) 优先匹配 immdoc/{uuid}/doc
                        m: re.Match[str] | None = re.search(r"immdoc/([a-zA-Z0-9-]+)/doc", s)
                        if m:
                            return m.group(1)
                        # 2) 再匹配标准 UUID 形式
                        m: re.Match[str] | None = re.search(r"[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}", s, re.I)
                        return m.group(0) if m else ""

                    headers: dict[str, str] = {
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                        "Referer": DEFAULT_BASE_URL,
                        "Origin": DEFAULT_BASE_URL,
                        "Content-Type": "application/json;charset=UTF-8",
                    }
                    for ep: str in api_candidates:
                        api_url: str = api_base.rstrip('/') + '/' + ep.lstrip('/')
                        for body in bodies:
                            try:
                                api_attempts += 1
                                rr: Response = session.post(api_url, json=body, headers=headers, timeout=10, proxies={"http": None, "https": None})
                                status = int(getattr(rr, 'status_code', 0) or 0)
                                api_status_counts[status] = api_status_counts.get(status, 0) + 1
                                if status >= 400:
                                    if not api_sample:
                                        text: str | re.Any = (getattr(rr, 'text', '') or '').strip().replace('\n', ' ')
                                        api_sample: str = f"HTTP {status} {ep} {text[:160]}".strip()
                                    continue
                                ct: str = (rr.headers.get('Content-Type') or '').lower()
                                if 'json' not in ct and not (rr.text and rr.text.strip().startswith('{')):
                                    continue
                                j = rr.json()
                                uuid: str = _scan_for_uuid(j)
                                if uuid:
                                    emit(f"ZBY: 从 API 获取到资源 UUID: {uuid[:8]}...")
                                    return self._download_images(uuid, item.filename(), output_dir, [], emit)
                                if not api_sample and isinstance(j, dict):
                                    code = j.get('code') if 'code' in j else j.get('status')
                                    msg = j.get('msg') if 'msg' in j else j.get('message')
                                    if code is not None or msg:
                                        api_sample: str = f"code={code} msg={str(msg)[:160]}".strip()
                            except Exception:
                                continue

                    if api_attempts:
                        try:
                            status_summary: str = '/'.join([f"{k}:{api_status_counts[k]}" for k in sorted(api_status_counts.keys())])
                        except Exception:
                            status_summary = str(api_status_counts)
                        sample_txt: str = f"，示例: {api_sample}" if api_sample else ""
                        emit(f"ZBY: API 未命中 UUID（base=[URL]，尝试{api_attempts}次，HTTP={status_summary}{sample_txt}）")
        except Exception:
            pass
        
        # 1. 尝试通过 standardId 直接访问详情页（SPA 可能只返回壳，但仍保留作为兜底）
        std_id = meta.get('standardId') or meta.get('id')
        if std_id:
            detail_urls: List[str] = [
                f"{self.base_url}/standard/detail/{std_id}",
                f"{self.base_url}/#/standard/detail/{std_id}",
            ]
            for du: str in detail_urls:
                try:
                    emit(f"ZBY: 检查详情页...")
                    r: Response = session.get(du, timeout=8, proxies={"http": None, "https": None})
                    if r.status_code == 200:
                        # 尝试从 HTML 中提取 UUID
                        m: re.Match[str] | None = re.search(r'immdoc/([a-zA-Z0-9-]+)/doc', r.text)
                        if m:
                            uuid: str | re.Any = m.group(1)
                            emit(f"ZBY: 从详情页发现资源 UUID: {uuid[:8]}...")
                            cookies = [{ 'name': c.name, 'value': c.value } for c: Cookie in session.cookies]
                            return self._download_images(uuid, item.filename(), output_dir, cookies, emit)
                        
                        # 尝试从 HTML 中提取任何看起来像 UUID 的字符串
                        uuids: List[re.Any] = re.findall(r'[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}', r.text)
                        for uid in uuids:
                            emit(f"ZBY: 尝试提取到的 UUID: {uid[:8]}...")
                            res = self._download_images(uid, item.filename(), output_dir, [], emit)
                            if res: return res
                except Exception:
                    continue

        # 1. 先检查 meta 中是否存在直接可用的 pdf/文件列表（json api 可能返回）
        try:
            for list_key: str in ('pdfList', 'taskPdfList', 'fileList', 'files'):
                lst = meta.get(list_key)
                if not lst:
                    continue
                # 期望 lst 为可迭代的条目集合
                for entry in (lst if isinstance(lst, list) else [lst]):
                    url = None
                    if isinstance(entry, dict):
                        # 常见字段名
                        for k: str in ('url', 'fileUrl', 'downloadUrl', 'resourceUrl'):
                            if entry.get(k):
                                url = entry.get(k)
                                break
                        # 某些接口返回的是资源id或uuid字段
                        if not url:
                            for k: str in ('uuid', 'resourceId', 'docId', 'fileId'):
                                if entry.get(k):
                                    # 构造可能的 immdoc 链接
                                    url: str = f"https://resource.zhenggui.vip/immdoc/{entry.get(k)}/doc/I/1"
                                    break
                    elif isinstance(entry, str):
                        url: str = entry

                    if not url:
                        continue

                    # 若链接中包含 immdoc，尝试提取 uuid 并用现有 _download_images
                    m: re.Match[str] | None = re.search(r'immdoc/([a-zA-Z0-9-]+)/doc', url)
                    if m:
                        uuid: str | re.Any = m.group(1)
                        cookies = []
                        emit(f"ZBY: 从 meta 发现可用资源 UUID: {uuid[:8]}...，尝试 HTTP 下载")
                        return self._download_images(uuid, item.filename(), output_dir, cookies, emit)

                    # 若为 PDF 文件链接，直接下载并保存
                    try:
                        if url.lower().endswith('.pdf') or 'download' in url or 'pdf' in url:
                            import requests
                            # 显式禁用代理
                            r: Response = requests.get(url, timeout=20, stream=True, proxies={"http": None, "https": None})
                            if r.status_code == 200:
                                outp: Path = output_dir / item.filename()
                                with open(outp, 'wb') as f: os.BufferedWriter:
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
            search_keywords: List[str] = [item.std_no] # 仅尝试标准号
        else:
            title = meta.get('title') or f"{item.std_no} {item.name}".strip()
            search_keywords = [title, item.std_no]
        
        urls: List[str] = [f"{self.base_url}/standardList"] # 仅尝试一个搜索接口
        
        try:
            for kw in search_keywords:
                if not kw: continue
                for u: str in urls:
                    try:
                        emit(f"ZBY: 尝试搜索关键词: {kw}")
                        # 显式禁用代理
                        r: Response = session.get(u, params={"searchText": kw, "q": kw, "keyword": kw}, timeout=10, proxies={"http": None, "https": None})
                        text: re.Any | str = getattr(r, 'text', '') or ''
                        
                        # 1. 查找 immdoc 链接
                        m: re.Match[str] | None = re.search(r'immdoc/([a-zA-Z0-9-]+)/doc', text)
                        if m:
                            uuid: str | re.Any = m.group(1)
                            emit(f"ZBY: 发现资源 UUID: {uuid[:8]}...")
                            cookies = [{ 'name': c.name, 'value': c.value } for c: Cookie in session.cookies]
                            return self._download_images(uuid, item.filename(), output_dir, cookies, emit)
                        
                        # 2. 查找详情页链接并跟进
                        # 匹配模式如 /standard/detail/566393 或 #/standard/detail/566393
                        detail_ids: List[re.Any] = re.findall(r'detail/(\d+)', text)
                        for did in detail_ids[:5]: # 只尝试前5个
                            detail_url: str = f"{self.base_url}/standard/detail/{did}"
                            try:
                                emit(f"ZBY: 尝试跟进详情页...")
                                rd: Response = session.get(detail_url, timeout=8, proxies={"http": None, "https": None})
                                td: re.Any | str = getattr(rd, 'text', '') or ''
                                m2: re.Match[str] | None = re.search(r'immdoc/([a-zA-Z0-9-]+)/doc', td)
                                if m2:
                                    uuid: str | re.Any = m2.group(1)
                                    emit(f"ZBY: 从详情页发现资源 UUID: {uuid[:8]}...")
                                    cookies = [{ 'name': c.name, 'value': c.value } for c: Cookie in session.cookies]
                                    return self._download_images(uuid, item.filename(), output_dir, cookies, emit)
                            except Exception:
                                continue
                    except Exception:
                        continue
        except Exception:
            return None

        return None


