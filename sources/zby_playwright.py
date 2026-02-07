# -*- coding: utf-8 -*-
"""
ZBY Source - Playwright-based implementation (CLEAN REWRITE)
"""
import re
import time
import requests
import shutil
import img2pdf
from pathlib import Path
from typing import List, Callable, Optional, Union
from .zby_utils import download_images_to_pdf
from core.models import Standard

class ZBYSource:
	"""ZBY (智标云) Data Source - Hybrid Playwright Scraper"""
    
	def __init__(self, output_dir: Optional[Path] = None):
		self.name = "ZBY"
		self.priority = 3
		self.output_dir = output_dir or Path("downloads")
		self.base_url = "https://bz.zhenggui.vip"
		self.session = requests.Session()
		self.session.trust_env = False
		self.session.headers.update({
			"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
			"Referer": "https://bz.zhenggui.vip/"
		})
		self._playwright_available = False
		try:
			from playwright.sync_api import sync_playwright
			self._playwright_available = True
		except ImportError:
			pass

	def is_available(self, timeout: int = 6) -> bool:
		try:
			r = self.session.get(self.base_url, timeout=timeout, proxies={"http": None, "https": None})
			return 200 <= r.status_code < 400
		except Exception:
			return False

	def search(self, keyword: str, page: int = 1, page_size: int = 20, **kwargs) -> List[Standard]:
		# Playwright search is not prioritized, but kept for legacy
		return [] 

	def download(self, item: Standard, output_dir: Path, log_cb: Callable[[str], None] = None) -> tuple:
		logs = []
		def emit(msg: str):
			if not msg: return
			msg = re.sub(r'https?://[^\s<>"]+', '[URL]', msg)
			logs.append(msg)
			if log_cb: log_cb(msg)

		if not self._playwright_available:
			emit("ZBY: Playwright 未安装，无法下载")
			return None, logs

		try:
			from playwright.sync_api import sync_playwright
			
			meta = item.source_meta if isinstance(item.source_meta, dict) else {}
			std_id = meta.get("standardId") or meta.get("id") or meta.get("standardid")
			
			if not std_id:
				emit("ZBY: 缺少 standardId，Playwright 无法定位")
				return None, logs

			emit(f"ZBY: 启动 Playwright 嗅探资源 (ID={std_id})...")
			
			with sync_playwright() as p:
				browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
				context = browser.new_context()
				page = context.new_page()
				
				# 1. 监听 UUID 请求
				found = {"uuid": None}
				def capture_req(r):
					if "immdoc" in r.url and "/doc/" in r.url:
						m = re.search(r'immdoc/([a-zA-Z0-9-]+)/doc', r.url)
						if m:
							found["uuid"] = m.group(1)
				
				page.on("request", capture_req)
				
				# 2. 访问详情页
				try:
					detail_url = f"{self.base_url}/standardDetail?standardId={std_id}&docStatus=0"
					page.goto(detail_url, timeout=45000)
					
					# 3. 等待并滚动触发资源加载
					emit("ZBY: 页面加载完成，滚动以触发资源...")
					try:
						# 尝试定位预览区域 (根据用户反馈是 #aliyunPreview 或内部滚动条)
						preview = page.wait_for_selector("#aliyunPreview", timeout=15000)
						if preview:
							preview.hover()
							# 针对预览区域滚动
							for _ in range(5):
								page.mouse.wheel(0, 500)
								time.sleep(0.5)
					except Exception:
						emit("ZBY: 预览区定位超时，使用全局滚动尝试")
						for _ in range(5):
							page.mouse.wheel(0, 1000)
							time.sleep(0.5)

					# 4. 等待捕获结果
					for i in range(20):
						if found["uuid"]: break
						time.sleep(0.5)
						
				except Exception as e:
					emit(f"ZBY: 页面访问或滚动异常: {e}")
				
				cookies_list = context.cookies()
				browser.close()
				
				# 5. 执行并发下载
				if found["uuid"]:
					emit(f"ZBY: 成功嗅探到 UUID: {found['uuid'][:8]}...")
					path = download_images_to_pdf(found["uuid"], item.filename(), output_dir, cookies_list, emit)
					return path, logs
				else:
					emit("ZBY: 未能抓取到 UUID")
					return None, logs
					
		except Exception as e:
			emit(f"ZBY: Playwright 流程异常: {e}")
			return None, logs
