# -*- coding: utf-8 -*-
"""
ZBY 工具模块 - 提取公共功能
"""
import re
import shutil
from pathlib import Path
from typing import Optional, List, Dict
import logging

logger = logging.getLogger(__name__)


def extract_uuid_from_text(text: str) -> Optional[str]:
    """
    从文本中提取资源 UUID

    支持多种格式：
    1. immdoc/{uuid}/doc 格式
    2. 标准 UUID 格式（8-4-4-4-12）

    Args:
        text: 要搜索的文本

    Returns:
        提取到的 UUID，如果未找到则返回 None
    """
    if not text:
        return None

    # 优先匹配 immdoc/{uuid}/doc 格式 (URL 路径)
    match = re.search(r'immdoc/([a-zA-Z0-9]{32})/doc', text)
    if match:
        return match.group(1)

    # 兼容旧格式 immdoc/{uuid}/doc (带短横线)
    match = re.search(r'immdoc/([a-zA-Z0-9-]+)/doc', text)
    if match:
        return match.group(1)

    # 备选：匹配标准 UUID 格式
    match = re.search(r'[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}', text, re.IGNORECASE)
    if match:
        return match.group(0)

    # 备选：匹配 32 位纯十六进制 ID (如 60b0afbe9d9c425698e9b91995922d28)
    match = re.search(r'\b[a-f0-9]{32}\b', text, re.IGNORECASE)
    if match:
        return match.group(0)

    return None


def extract_all_uuids_from_text(text: str) -> List[str]:
    """
    从文本中提取所有可能的 UUID

    Args:
        text: 要搜索的文本

    Returns:
        UUID 列表
    """
    if not text:
        return []

    uuids = []

    # 提取所有 immdoc/{uuid}/doc 格式
    for match in re.finditer(r'immdoc/([a-zA-Z0-9-]+)/doc', text):
        uuids.append(match.group(1))

    # 提取所有标准 UUID 格式
    for match in re.finditer(r'[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}', text, re.IGNORECASE):
        uuid = match.group(0)
        if uuid not in uuids:  # 去重
            uuids.append(uuid)

    return uuids


def download_images_to_pdf(
    uuid: str,
    filename: str,
    output_dir: Path,
    cookies: Optional[List[Dict]] = None,
    emit: Optional[callable] = None
) -> Optional[Path]:
    """
    通过资源 UUID 下载分页图片并合成 PDF

    Args:
        uuid: 资源 UUID
        filename: 输出文件名
        output_dir: 输出目录
        cookies: Cookie 列表（格式：[{'name': ..., 'value': ...}]）
        emit: 日志回调函数

    Returns:
        成功时返回 PDF 文件路径，失败时返回 None
    """
    try:
        import requests
        import img2pdf
    except ImportError as e:
        if emit:
            emit(f"ZBY: 缺少必要的库: {e}")
        return None

    def log(msg: str):
        print(f"[ZBY DEBUG] {msg}")  # 强制输出到终端
        if emit:
            emit(msg)
        logger.info(msg)

    try:
        uuid = (uuid or "").strip()
        if not uuid:
            return None

        log(f"ZBY: 获取到UUID: {uuid[:8]}..., 开始下载")

        # 创建临时目录
        temp_dir = output_dir / "zby_temp"
        try:
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
        except Exception:
            pass
        temp_dir.mkdir(parents=True, exist_ok=True)

        # 转换 cookies 格式
        cookies_dict = {}
        try:
            for c in (cookies or []):
                if isinstance(c, dict) and c.get('name'):
                    cookies_dict[str(c.get('name'))] = str(c.get('value') or '')
        except Exception:
            cookies_dict = {}

        # 创建 session
        session = requests.Session()
        session.trust_env = False
        # 设置连接池大小
        adapter = requests.adapters.HTTPAdapter(pool_connections=20, pool_maxsize=20)
        session.mount('https://', adapter)
        session.mount('http://', adapter)

        imgs = []
        import concurrent.futures

        def download_page(page_num):
            retries = 3
            backoff = 1.0  # 初始退避 1 秒
            
            for attempt in range(retries):
                try:
                    url = f"https://resource.zhenggui.vip/immdoc/{uuid}/doc/I/{page_num}"
                    resp = session.get(
                        url,
                        cookies=cookies_dict,
                        timeout=15,
                        proxies={"http": None, "https": None}
                    )
                    
                    if resp.status_code == 200 and resp.content:
                        img_path = temp_dir / f"{page_num:04d}.jpg"
                        with open(img_path, 'wb') as f:
                            f.write(resp.content)
                        return page_num, str(img_path)
                    
                    # 详细记录非200状态码
                    log(f"ZBY DEBUG: Page {page_num} attempt {attempt+1}/{retries} failed. Status: {resp.status_code}")
                    
                    # 如果遇到 429 Too Many Requests，增加等待时间
                    if resp.status_code == 429:
                        wait_time = backoff * 2
                        log(f"ZBY DEBUG: 触发限流(429)，等待 {wait_time}s...")
                        time.sleep(wait_time)
                        
                except Exception as e:
                    # 记录具体的异常信息
                    log(f"ZBY DEBUG: Page {page_num} attempt {attempt+1}/{retries} exception: {str(e)}")
                
                # 指数退避等待（如果是最后一次尝试则不等待）
                if attempt < retries - 1:
                    import time
                    import random
                    sleep_time = backoff * (2 ** attempt) + random.uniform(0, 1)
                    # log(f"ZBY DEBUG: Retrying page {page_num} in {sleep_time:.2f}s...")
                    time.sleep(sleep_time)
            
            log(f"ZBY ERROR: Page {page_num} failed after {retries} attempts.")
            return page_num, None

        # 批量并发下载
        batch_size = 20
        current_page = 1
        max_pages = 1000
        all_downloaded = True
        
        while current_page <= max_pages:
            end_page = current_page + batch_size
            log(f"ZBY: 正在下载第 {current_page}-{end_page-1} 页...")
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                futures = {executor.submit(download_page, p): p for p in range(current_page, end_page)}
                
                # 收集本批次结果
                batch_results = {}
                for future in concurrent.futures.as_completed(futures):
                    p, path = future.result()
                    batch_results[p] = path
            
            # 检查本批次是否全部成功
            # 注意：如果中间某页失败，说明文档结束
            found_end = False
            for p in range(current_page, end_page):
                if batch_results.get(p):
                    imgs.append(batch_results[p])
                else:
                    # 发现某一页下载失败，认为文档结束
                    found_end = True
                    break
            
            if found_end:
                break
                
            current_page += batch_size

        # 合成 PDF
        imgs.sort() # 确保按文件名排序
        if imgs:
            log(f"ZBY: 共 {len(imgs)} 页，正在合成PDF...")
            output_path = output_dir / filename
            with open(output_path, "wb") as f:
                f.write(img2pdf.convert(imgs))
            log("ZBY: PDF生成成功")

            # 清理临时文件
            try:
                shutil.rmtree(temp_dir)
            except Exception:
                pass

            return output_path

        log("ZBY: 未下载到任何页面")
        return None

    except Exception as e:
        if emit:
            emit(f"ZBY: 下载图片异常: {e}")
        logger.exception("ZBY download_images_to_pdf error")
        return None


def sanitize_log_message(msg: str) -> str:
    """
    清理日志消息，隐藏敏感信息（如 URL）

    Args:
        msg: 原始日志消息

    Returns:
        清理后的日志消息
    """
    if not msg:
        return msg

    # 隐藏所有网址
    msg = re.sub(r'https?://[^\s<>"]+', '[URL]', msg)

    return msg
