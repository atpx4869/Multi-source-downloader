# -*- coding: utf-8 -*-
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import time
import requests

from core.unified_models import Standard, natural_key
from core.aggregated_downloader import SourceHealth

class HttpAggregatedDownloader:
    """基于 HTTP API 的下载器替代品"""
    
    def __init__(self, output_dir: str = "downloads", enable_sources: Optional[List[str]] = None, base_url: str = "http://127.0.0.1:8000/api"):
        self.output_dir = Path(output_dir)
        self.enable_sources = [s.upper() for s in (enable_sources or ["GBW", "BY", "ZBY"])]
        self.base_url = base_url
        
        # 兼容旧版的 sources 属性
        class DummySource:
            def __init__(self, name):
                self.name = name
        self.sources = [DummySource(s) for s in self.enable_sources]
        
    def check_source_health(self, force: bool = False) -> Dict[str, SourceHealth]:
        health_dict = {}
        try:
            resp = requests.get(f"{self.base_url}/health", timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                sources_list = data.get("sources", [])
                for info in sources_list:
                    name = info.get("name", "")
                    name_upper = name.upper()
                    if name_upper in self.enable_sources:
                        h = SourceHealth(name_upper)
                        h.available = info.get("available", False)
                        h.error = info.get("error", "")
                        h.response_time = info.get("response_time", 0.0) / 1000.0
                        h.last_check = info.get("last_check", time.time())
                        health_dict[name_upper] = h
        except Exception as e:
            for s in self.enable_sources:
                h = SourceHealth(s)
                h.error = f"API 连接失败: {e}"
                health_dict[s] = h
        return health_dict
        
    def search(self, keyword: str, parallel: bool = True, **kwargs) -> List[Standard]:
        try:
            resp = requests.get(
                f"{self.base_url}/search/", 
                params={"q": keyword, "limit": 100, "timeout": 15},
                timeout=20
            )
            if resp.status_code == 200:
                data = resp.json()
                all_items = []
                for source_name, src_data in data.items():
                    if source_name.upper() not in self.enable_sources:
                        continue
                    items = src_data.get("items", [])
                    for it in items:
                        std = Standard(
                            std_no=it.get("std_no", ""),
                            name=it.get("name", ""),
                            publish_date=it.get("publish_date", ""),
                            implement_date=it.get("implement_date", ""),
                            status=it.get("status", ""),
                            has_pdf=it.get("has_pdf", False),
                            sources=[source_name.upper()],
                            source_meta={source_name.upper(): it.get("source_meta", {})}
                        )
                        all_items.append(std)
                
                # Merge items
                merged_map = {}
                for std in all_items:
                    key = re.sub(r"[\s/\-–—_:：]+", "", std.std_no or "").lower()
                    if key in merged_map:
                        cur = merged_map[key]
                        if std.sources[0] not in cur.sources:
                            cur.sources.append(std.sources[0])
                        cur.has_pdf = cur.has_pdf or std.has_pdf
                        if len(std.name or "") > len(cur.name or ""):
                            cur.name = std.name
                        if std.publish and not cur.publish:
                            cur.publish = std.publish
                        if std.implement and not cur.implement:
                            cur.implement = std.implement
                        if std.status and not cur.status:
                            cur.status = std.status
                        if not isinstance(cur.source_meta, dict):
                            cur.source_meta = {}
                        cur.source_meta[std.sources[0]] = std.source_meta.get(std.sources[0], {})
                    else:
                        merged_map[key] = std
                
                results = list(merged_map.values())
                results.sort(key=lambda x: natural_key(x.std_no))
                return results
            return []
        except Exception as e:
            print(f"HTTP Search Error: {e}")
            return []
            
    def search_single_source(self, source_name: str, keyword: str) -> List[Standard]:
        try:
            resp = requests.get(
                f"{self.base_url}/search/{source_name.lower()}", 
                params={"q": keyword, "limit": 100, "timeout": 15},
                timeout=20
            )
            if resp.status_code == 200:
                data = resp.json()
                items = data.get("items", [])
                all_items = []
                for it in items:
                    std = Standard(
                        std_no=it.get("std_no", ""),
                        name=it.get("name", ""),
                        publish_date=it.get("publish_date", ""),
                        implement_date=it.get("implement_date", ""),
                        status=it.get("status", ""),
                        has_pdf=it.get("has_pdf", False),
                        sources=[source_name.upper()],
                        source_meta={source_name.upper(): it.get("source_meta", {})}
                    )
                    all_items.append(std)
                return all_items
            return []
        except Exception as e:
            print(f"HTTP Search Single Error: {e}")
            return []
            
    def download(self, item: Standard, log_cb=None, prefer_order: Optional[List[str]] = None) -> tuple:
        logs = []
        def emit(msg):
            logs.append(msg)
            if log_cb:
                log_cb(msg)
                
        emit(f"开始通过 HTTP API 下载: {item.std_no}")
        
        order = prefer_order or ["BY", "GBW", "ZBY"]
        available_sources = [s for s in order if s in (item.sources or []) and s in self.enable_sources]
        if not available_sources:
            available_sources = [s for s in (item.sources or []) if s in self.enable_sources]
            
        if not available_sources:
            emit("没有可用的下载源")
            return None, logs
            
        for src in available_sources:
            emit(f"{src}: 正在请求远程下载...")
            try:
                resp = requests.post(
                    f"{self.base_url}/download/{src}/{item.std_no}",
                    params={"output_dir": str(self.output_dir)},
                    timeout=60
                )
                if resp.status_code == 200:
                    data = resp.json()
                    remote_logs = data.get("logs", [])
                    for l in remote_logs:
                        emit(f"[REMOTE] {l}")
                    
                    if data.get("status") == "success" and data.get("file_path"):
                        emit(f"{src}: 下载成功 -> {data.get('file_path')}")
                        return data.get("file_path"), logs
                    else:
                        emit(f"{src}: 下载失败 -> {data.get('error', '未知错误')}")
                else:
                    emit(f"{src}: API 返回错误状态码 {resp.status_code}")
            except Exception as e:
                emit(f"{src}: 请求异常 -> {e}")
                
        emit("所有来源均未成功")
        return None, logs
