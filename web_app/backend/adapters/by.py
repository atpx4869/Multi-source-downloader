# -*- coding: utf-8 -*-
"""
BY数据源适配器
"""
import asyncio
from typing import List, Tuple
from pathlib import Path
import sys

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from web_app.backend.adapters.base import BaseAdapter
from web_app.backend.models.responses import StandardModel


class BYAdapter(BaseAdapter):
    """BY数据源适配器"""
    
    source_name = "BY"
    
    def __init__(self):
        self._source = None
        self._init_error = None
        self._initialize()
    
    def _initialize(self):
        """初始化BY源"""
        try:
            from sources.by import BYSource
            self._source = BYSource()
        except Exception as e:
            self._init_error = str(e)
    
    async def search(self, query: str, limit: int = 100) -> List[StandardModel]:
        """搜索标准"""
        if not self._source:
            raise Exception(f"BY源未初始化: {self._init_error}")
        
        loop = asyncio.get_event_loop()
        standards = await loop.run_in_executor(None, self._source.search, query)
        
        results = []
        for std in standards[:limit]:
            model = StandardModel(
                std_no=std.std_no,
                name=std.name,
                source=self.source_name,
                has_pdf=std.has_pdf,
                publish_date=std.publish,
                implement_date=std.implement,
                status=std.status,
                replace_std=std.replace_std
            )
            results.append(model)
        
        return results
    
    async def download(self, std_no: str, output_dir: str) -> Tuple[str, List[str]]:
        """下载标准"""
        if not self._source:
            raise Exception(f"BY源未初始化: {self._init_error}")
        
        def _download_task():
            from core.models import Standard
            # BYSource 需要 source_meta 来获取 siid 或 pdf_path
            # 先进行搜索获取元数据
            try:
                search_results = self._source.search(std_no, page_size=1)
                item = search_results[0] if search_results else None
            except:
                item = None
            
            if not item:
                # 如果搜索不到，可能无法下载，但还是构造一个尝试
                item = Standard(std_no=std_no, name=std_no, source="BY", sources=["BY"])
            
            result = self._source.download(item, Path(output_dir))
            
            if result and result.success:
                return str(result.file_path), result.logs
            else:
                logs = result.logs if result else []
                if result and result.error and result.error not in logs:
                    logs.append(f"错误: {result.error}")
                return None, logs
        
        loop = asyncio.get_event_loop()
        filepath, download_logs = await loop.run_in_executor(None, _download_task)
        
        return filepath, download_logs
    
    async def check_health(self) -> bool:
        """检查健康状态"""
        if not self._source:
            return False
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._source.search, "GB")
            return True
        except:
            return False
