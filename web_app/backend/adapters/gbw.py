# -*- coding: utf-8 -*-
"""
GBW数据源适配器
"""
import asyncio
from typing import List, Tuple
from pathlib import Path
import sys

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from web_app.backend.adapters.base import BaseAdapter
from web_app.backend.models.responses import StandardModel


class GBWAdapter(BaseAdapter):
    """GBW数据源适配器"""
    
    source_name = "GBW"
    
    def __init__(self):
        self._source = None
        self._init_error = None
        self._initialize()
    
    def _initialize(self):
        """初始化GBW源"""
        try:
            from sources.gbw import GBWSource
            self._source = GBWSource()
        except Exception as e:
            self._init_error = str(e)
    
    async def search(self, query: str, limit: int = 100) -> List[StandardModel]:
        """搜索标准"""
        if not self._source:
            raise Exception(f"GBW源未初始化: {self._init_error}")
        
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
            raise Exception(f"GBW源未初始化: {self._init_error}")
        
        def _download_task():
            from core.models import Standard
            # GBW需要source_meta中的id和hcno才能下载，但这里我们只有std_no
            # 幸运的是GBWSource._download_impl会先检查hcno，如果缺失会尝试通过_get_hcno(item_id)获取
            # 如果我们连item_id都没有，GBWSource.download可能会失败
            # 这里的改进方案是：如果我们没有meta信息，先调用 search 获取一下
            # 但为了简单起见，我们先尝试直接构造，看看GBWSource是否够智能
            # 查看源码发现 GBWSource._download_impl 需要 item.source_meta.get("id")
            # 所以如果直接构造空 meta 的 item，下载可能会失败
            
            # 尝试先搜索以获取元数据
            try:
                search_results = self._source.search(std_no, page_size=1)
                item = search_results[0] if search_results else None
            except:
                item = None
                
            if not item:
                # 如果搜索失败，尝试构造一个基本的，期望GBWSource能处理(虽然源码显示它需要ID)
                item = Standard(std_no=std_no, name=std_no, source="GBW", sources=["GBW"])
            
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
