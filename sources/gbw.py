# -*- coding: utf-8 -*-
"""
GBW Source - 国家标准信息公共服务平台 (openstd.samr.gov.cn)
Refactored to use proven gbw_download.py logic for efficiency
"""
import re
import requests
from pathlib import Path
from typing import List, Callable
from core.models import Standard

# Import the proven download logic
from sources.gbw_download import download_with_ocr, get_hcno

# Pre-compile regex patterns
_HTML_TAG_RE = re.compile(r'<[^>]+>')
_WHITESPACE_RE = re.compile(r'\s+')
_STD_CODE_SLASH_RE = re.compile(r'([A-Z])\s*/\s*([A-Z])')


class GBWSource:
    """GBW (国标委) Data Source - Optimized Implementation"""
    
    name = "GBW"
    
    def __init__(self):
        self.name = "GBW"
        self.base_url = "https://std.samr.gov.cn"  # For search API
        self.download_base = "http://c.gb688.cn"  # For download
        
        # Create session with optimized settings
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry
        
        self.session = requests.Session()
        self.session.trust_env = False  # Ignore system proxy
        self.session.proxies = {"http": None, "https": None}
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        
        # 增加强大的重试策略
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
            pool_connections=10,
            pool_maxsize=10
        )
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
    
    def _clean_text(self, text: str) -> str:
        """Clean XML tags from text, preserving inner content"""
        if not text:
            return ""
        cleaned = _HTML_TAG_RE.sub('', text)
        return cleaned.strip()
    
    def _parse_std_code(self, raw_code: str) -> str:
        """Parse standard code like '<sacinfo>GB</sacinfo>/<sacinfo>T</sacinfo> <sacinfo>46541-2025</sacinfo>' -> 'GB/T 46541-2025'"""
        if not raw_code:
            return ""
        
        # Remove all HTML tags and clean whitespace
        cleaned = _HTML_TAG_RE.sub('', raw_code)
        cleaned = _WHITESPACE_RE.sub(' ', cleaned).strip()
        
        # Fix spacing around slashes: "GB / T" -> "GB/T"
        cleaned = _STD_CODE_SLASH_RE.sub(r'\1/\2', cleaned)
        
        return cleaned
    
    def search(self, keyword: str, page: int = 1, page_size: int = 20, **kwargs) -> List[Standard]:
        """Search standards from GBW API"""
        try:
            return self._search_impl(keyword, page, page_size, **kwargs)
        except Exception as e:
            print(f"GBW search error: {e}")
            return []
    
    def _search_impl(self, keyword: str, page: int = 1, page_size: int = 20, **kwargs) -> List[Standard]:
        """Search implementation (internal method)"""
        url = f"{self.base_url}/gb/search/gbQueryPage"
        
        params = {
            "searchText": keyword,
            "page": page,
            "pageSize": page_size,
        }
        
        try:
            # 优化超时控制，使用较短的连接超时和读取超时
            resp = self.session.get(url, params=params, timeout=(5, 10))
            resp.raise_for_status()
            data = resp.json()
            
            if not data or "rows" not in data:
                return []
            
            results = []
            for row in data.get("rows", []):
                try:
                    # Parse standard code (field name is C_STD_CODE, not standardNo)
                    std_no = self._parse_std_code(row.get("C_STD_CODE", ""))
                    if not std_no:
                        continue
                    
                    # Extract metadata (field names differ from documentation)
                    name = self._clean_text(row.get("C_C_NAME", ""))
                    item_id = row.get("id", "")
                    status = self._clean_text(row.get("STATE", ""))
                    
                    # Heuristic: Current and upcoming standards usually have PDF preview/download
                    # Standard status in GBW: "现行", "即将实施", "废止", etc.
                    has_pdf_hint = status in ["现行", "即将实施"]
                    
                    # 过滤逻辑：只有当标准号或名称中包含关键词时才返回
                    # GBW 后台在结果不足时会返回不相关的“最新标准”
                    kw_lower = keyword.lower()
                    if kw_lower not in std_no.lower() and kw_lower not in name.lower() and kw_lower.replace("-", "") not in std_no.lower().replace("-", ""):
                        continue

                    # Create Standard object
                    standard = Standard(
                        std_no=std_no,
                        name=name,
                        status=status,
                        has_pdf=has_pdf_hint,
                        source_meta={
                            "id": item_id,
                            "status": status,
                            "publish_date": row.get("ISSUE_DATE", ""),  # 发布日期
                            "implement_date": row.get("ACT_DATE", ""),  # 实施日期
                            "nature": row.get("STD_NATURE", ""),  # 标准性质
                            "_has_pdf": has_pdf_hint,  # Store hint in meta for aggregator
                        },
                        sources=["GBW"]
                    )
                    
                    results.append(standard)
                    
                except Exception as e:
                    print(f"GBW: Error parsing row: {e}")
                    continue
            
            return results
            
        except Exception as e:
            print(f"GBW: Search request failed: {e}")
            return []
    
    def _get_hcno(self, item_id: str) -> str:
        """Get HCNO from detail page using proven logic"""
        try:
            return get_hcno(item_id)
        except Exception as e:
            print(f"GBW: Failed to get HCNO: {e}")
            return ""
    
    def has_pdf(self, item: Standard) -> bool:
        """
        Check if a standard has downloadable PDF by detecting download button and copyright restrictions.
        """
        try:
            # Extract or fetch HCNO
            hcno = item.source_meta.get("hcno") if isinstance(item.source_meta, dict) else None
            if not hcno:
                item_id = item.source_meta.get("id") if isinstance(item.source_meta, dict) else None
                if not item_id: return False
                hcno = self._get_hcno(item_id)
            
            if not hcno: return False
            
            # Check showGb on download base (c.gb688.cn) as it's the definitive source
            # We check both online and download types
            for gbw_type in ["online", "download"]:
                url = f"{self.download_base}/bzgk/gb/showGb?type={gbw_type}&hcno={hcno}"
                try:
                    resp = self.session.get(url, timeout=(5, 10))
                    if resp.status_code == 200:
                        html = resp.text.lower()
                        # Keywords representing "no text"
                        restricted_keywords = ["版权保护", "暂不提供在线阅读", "部分正在整理中", "采用了ISO", "采用了IEC", "国际国外组织的标准"]
                        if any(kw.lower() in html for kw in restricted_keywords):
                            return False
                        
                        # 检测下载或阅读按钮
                        positive_keywords = ["下载标准", "xz_btn", "在线预览", "yl_btn", "阅读标准"]
                        if any(kw.lower() in html for kw in positive_keywords):
                            return True
                except Exception:
                    continue
            
            return False
            
        except Exception as e:
            print(f"GBW: Error checking PDF availability: {e}")
            return False
    
    def download(self, item: Standard, output_dir: Path, emit: Callable = print) -> "DownloadResult":
        """
        Download a standard from GBW using proven OCR-based approach.
        """
        from sources.base import DownloadResult
        logs = []
        
        # Extract HCNO
        hcno = item.source_meta.get("hcno") if isinstance(item.source_meta, dict) else None
        if not hcno:
            item_id = item.source_meta.get("id") if isinstance(item.source_meta, dict) else None
            if item_id:
                emit("GBW: 从详情页获取 HCNO...")
                hcno = self._get_hcno(item_id)
        
        if not hcno:
            msg = "GBW: 无法获取 HCNO，下载失败"
            emit(msg)
            return DownloadResult.fail(msg, logs)
        
        # 预检详情页确认是否有下载权限（由 download_with_ocr 内部处理更准确）
        # 但我们可以在这里做一个快速的 has_pdf 检查来提前拦截
        if not self.has_pdf(item):
            msg = "GBW: 该标准受版权保护或不提供在线阅读/下载，已自动跳过。"
            emit(msg)
            return DownloadResult.fail(msg, logs)

        # Use proven download logic from gbw_download.py
        outfile = output_dir / item.filename()
        emit(f"GBW: 开始下载 {item.std_no}...")
        
        try:
            success = download_with_ocr(
                hcno=hcno,
                outfile=outfile,
                max_attempts=12,  # 12 attempts with dual OCR (PPLL + Baidu)
                logger=emit,
                session=self.session,
                verbose=False  # Keep logs concise
            )
            
            if success:
                emit(f"GBW: 下载成功 -> {outfile}")
                return DownloadResult.ok(outfile, logs)
            else:
                msg = "GBW: 下载失败（OCR 验证码识别失败或文件不可用）"
                emit(msg)
                return DownloadResult.fail(msg, logs)
                
        except Exception as e:
            msg = f"GBW: 下载异常: {e}"
            emit(msg)
            return DownloadResult.fail(msg, logs)

    
    def is_available(self, timeout: int = 6) -> bool:
        """Check if GBW service is accessible"""
        try:
            resp = self.session.get(
                f"{self.base_url}/gb/search/gbQueryPage",
                params={"searchText": "test", "page": 1, "pageSize": 1},
                timeout=timeout
            )
            return resp.status_code == 200
        except Exception:
            return False
