# -*- coding: utf-8 -*-
"""
GBW Source - 国家标准信息公共服务平台 (std.samr.gov.cn)
"""
import re
import requests
from pathlib import Path
from typing import List, Callable

from core.models import Standard


class GBWSource:
    """GBW (国标委) Data Source"""
    
    def __init__(self):
        self.name = "GBW"
        self.priority = 1
        self.base_url = "https://std.samr.gov.cn"
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
    
    def _clean_text(self, text: str) -> str:
        """Clean XML tags from text, preserving inner content"""
        if not text:
            return ""
        # Remove tags but keep inner text
        cleaned = re.sub(r'<[^>]+>', '', text)
        return cleaned.strip()
    
    def _parse_std_code(self, raw_code: str) -> str:
        """Parse standard code like 'GB/T <sacinfo>33260.3-2018</sacinfo>' -> 'GB/T 33260.3-2018'"""
        if not raw_code:
            return ""
        # Extract prefix (GB/T, GB, etc.)
        prefix_match = re.match(r'^([A-Z]+(?:/[A-Z]+)?)\s*', raw_code)
        prefix = prefix_match.group(1) if prefix_match else ""
        
        # Extract number from sacinfo tag or directly
        sacinfo_match = re.search(r'<sacinfo>([^<]+)</sacinfo>', raw_code)
        if sacinfo_match:
            number = sacinfo_match.group(1)
        else:
            # Remove prefix and clean
            number = self._clean_text(raw_code)
            if prefix and number.startswith(prefix):
                number = number[len(prefix):].strip()
        
        return f"{prefix} {number}".strip() if prefix else number
    
    def search(self, keyword: str, page: int = 1, page_size: int = 20, **kwargs) -> List[Standard]:
        """Search standards from GBW API"""
        items = []
        try:
            search_url = f"{self.base_url}/gb/search/gbQueryPage"
            params = {
                "searchText": keyword,
                "pageNum": page,
                "pageSize": page_size
            }
            
            resp = self.session.get(search_url, params=params, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                rows = data.get("rows", [])
                
                for row in rows:
                    # Parse standard code properly
                    std_code = self._parse_std_code(row.get("C_STD_CODE", ""))
                    std_name = self._clean_text(row.get("C_C_NAME", ""))
                    
                    # Check if PDF is available (current or upcoming standards have PDF)
                    status = row.get("STATE", "")
                    has_pdf = "现行" in status or "即将实施" in status
                    
                    std = Standard(
                        std_no=std_code,
                        name=std_name,
                        publish=row.get("ISSUE_DATE", ""),
                        implement=row.get("ACT_DATE", ""),
                        status=status,
                        has_pdf=has_pdf,
                        source_meta={
                            "id": row.get("id", ""),
                            "hcno": row.get("HCNO", "")
                        },
                        sources=["GBW"]
                    )
                    items.append(std)
                    
        except Exception as e:
            print(f"GBW search error: {e}")
        
        return items
    
    def _get_hcno(self, item_id: str) -> str:
        """Get HCNO from detail page"""
        try:
            detail_url = f"{self.base_url}/gb/search/gbDetailed?id={item_id}"
            resp = self.session.get(detail_url, timeout=10)
            match = re.search(r'hcno=([A-F0-9]{32})', resp.text)
            if match:
                return match.group(1)
        except:
            pass
        return ""
    
    def download(self, item: Standard, output_dir: Path, log_cb: Callable[[str], None] = None) -> tuple[Path | None, list[str]]:
        """Download PDF from GBW - requires browser automation for captcha"""
        logs = []
        
        def emit(msg: str):
            logs.append(msg)
            if log_cb:
                log_cb(msg)
        
        try:
            meta = item.source_meta
            item_id = meta.get("id", "") if isinstance(meta, dict) else ""
            
            if not item_id:
                emit("GBW: 未找到标准ID")
                return None, logs
            
            # Get HCNO
            emit("GBW: 获取下载链接...")
            hcno = self._get_hcno(item_id)
            
            if not hcno:
                emit("GBW: 无法获取HCNO，该标准可能仅提供目录")
                return None, logs
            
            emit(f"GBW: 找到HCNO: {hcno[:8]}...")
            emit("GBW: 此源需要验证码，将尝试其他来源")
            
            # GBW download requires playwright and OCR for captcha
            return None, logs
            
        except Exception as e:
            emit(f"GBW: 下载错误: {e}")
            return None, logs

            if match:
                return match.group(1)
        except:
            pass
        return ""
    
    def download(self, item: Standard, output_dir: Path, log_cb: Callable[[str], None] = None) -> tuple[Path | None, list[str]]:
        """Download PDF from GBW - requires browser automation for captcha"""
        logs = []

        def emit(msg: str):
            logs.append(msg)
            if log_cb:
                log_cb(msg)

        emit("GBW: 尝试使用浏览器自动化处理验证码...")

        # Check Playwright availability
        try:
            from playwright.sync_api import sync_playwright
            playwright_available = True
        except Exception:
            playwright_available = False

        # Check OCR availability
        ocr = None
        try:
            from ppllocr import OCR
            try:
                ocr = OCR()
            except Exception as e:
                emit(f"GBW: OCR 模型加载失败: {e}")
                ocr = None
        except Exception:
            emit("GBW: 未找到 ppllocr OCR 库，无法自动识别验证码")
            ocr = None

        if not playwright_available:
            emit("GBW: Playwright 未安装，无法自动处理验证码")
            return None, logs

        try:
            meta = item.source_meta
            item_id = meta.get("id", "") if isinstance(meta, dict) else ""
            if not item_id:
                emit("GBW: 未找到标准ID")
                return None, logs

            detail_url = f"{self.base_url}/gb/search/gbDetailed?id={item_id}"

            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context()
                page = context.new_page()

                emit(f"GBW: 打开详情页面 {detail_url}")
                page.goto(detail_url)
                page.wait_for_load_state("networkidle")

                # 尝试定位验证码图片与输入框
                captcha_img = None
                try:
                    # 常见选择器：img[src*="captcha"], img#captcha
                    captcha_img = page.query_selector('img[src*="captcha"])')
                except Exception:
                    captcha_img = None

                if not captcha_img:
                    # 备用查找：查找包含 '验证码' 的标签附近的 img
                    try:
                        elems = page.query_selector_all("img")
                        for el in elems:
                            alt = el.get_attribute('alt') or ''
                            src = el.get_attribute('src') or ''
                            if '验证码' in alt or 'captcha' in src.lower() or 'validate' in src.lower():
                                captcha_img = el
                                break
                    except Exception:
                        captcha_img = None

                if not captcha_img:
                    emit("GBW: 页面上未检测到验证码图片，尝试直接抓取 HCNO")
                    # 如果没有验证码，尝试通过请求获取 hcno
                    cookies = {c['name']: c['value'] for c in context.cookies()}
                    browser.close()
                    # 使用已有 session cookies 获取页面内容
                    resp = self.session.get(detail_url, cookies=cookies, timeout=10)
                    match = re.search(r'hcno=([A-F0-9]{32})', resp.text)
                    if match:
                        hcno = match.group(1)
                        emit(f"GBW: 找到 HCNO: {hcno[:8]}...")
                        return None, logs
                    emit("GBW: 未能获取 HCNO")
                    return None, logs

                # 获取图片 URL
                src = captcha_img.get_attribute('src')
                if src.startswith('data:'):
                    # base64 image
                    import base64
                    header, b64 = src.split(',', 1)
                    img_bytes = base64.b64decode(b64)
                else:
                    # 通过 playwright 的 request 获取图片以携带相同上下文（cookie）
                    try:
                        # 获取绝对URL
                        img_url = src if src.startswith('http') else (self.base_url + src)
                        # 转换 context cookies 到 requests cookies
                        cookies = {c['name']: c['value'] for c in context.cookies()}
                        r = self.session.get(img_url, cookies=cookies, timeout=10)
                        img_bytes = r.content
                    except Exception as e:
                        emit(f"GBW: 下载验证码图片失败: {e}")
                        browser.close()
                        return None, logs

                emit("GBW: 已获取验证码图片，开始 OCR 识别")
                if ocr:
                    try:
                        code = ocr.classification(img_bytes)
                        code = code.strip()
                        emit(f"GBW: OCR 识别结果: {code}")
                    except Exception as e:
                        emit(f"GBW: OCR 识别失败: {e}")
                        code = ''
                else:
                    code = ''

                if not code:
                    emit("GBW: 无法识别验证码，请在浏览器中手动处理")
                    browser.close()
                    return None, logs

                # 填写验证码并提交（尝试常见输入框和按钮）
                try:
                    # 尝试找到输入框
                    input_el = page.query_selector('input[type="text"]') or page.query_selector('input')
                    if input_el:
                        input_el.fill(code)
                    # 找到提交按钮
                    btn = page.query_selector('button[type="submit"]') or page.query_selector('button')
                    if btn:
                        btn.click()
                    else:
                        # 触发回车
                        input_el.press('Enter')
                except Exception:
                    pass

                # 等待页面刷新并获取 cookies
                try:
                    page.wait_for_load_state('networkidle', timeout=5000)
                except Exception:
                    pass

                cookies = {c['name']: c['value'] for c in context.cookies()}
                browser.close()

                # 使用 requests 获取页面，查找 hcno
                resp = self.session.get(detail_url, cookies=cookies, timeout=10)
                match = re.search(r'hcno=([A-F0-9]{32})', resp.text)
                if match:
                    hcno = match.group(1)
                    emit(f"GBW: 验证成功，获取 HCNO: {hcno[:8]}...")
                    # 进一步下载可在此实现（需要确认下载接口）；当前返回成功信息
                    return None, logs
                else:
                    emit("GBW: 验证后仍未找到 HCNO，可能识别错误或页面流程不同")
                    return None, logs

        except Exception as e:
            emit(f"GBW: CAPTCHA 处理失败: {e}")
            return None, logs
