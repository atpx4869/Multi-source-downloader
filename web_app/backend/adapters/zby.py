# -*- coding: utf-8 -*-
"""
ZBY数据源适配器
"""
import asyncio
from typing import List, Tuple
from pathlib import Path
import sys

# 添加项目根目录
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from web_app.backend.adapters.base import BaseAdapter
from web_app.backend.models.responses import StandardModel


class ZBYAdapter(BaseAdapter):
    """ZBY数据源适配器"""
    
    source_name = "ZBY"
    
    def __init__(self, output_dir: str = "downloads"):
        self.output_dir = output_dir
        self._source = None
        self._init_error = None
        self._initialize()
    
    def _initialize(self):
        """初始化ZBY源"""
        try:
            from sources.zby import ZBYSource
            self._source = ZBYSource(self.output_dir)
        except Exception as e:
            self._init_error = str(e)
    
    async def search(self, query: str, limit: int = 100) -> List[StandardModel]:
        """搜索标准"""
        if not self._source:
            raise Exception(f"ZBY源未初始化: {self._init_error}")
        
        # 在线程池中运行同步代码
        loop = asyncio.get_event_loop()
        standards = await loop.run_in_executor(
            None, 
            self._source.search, 
            query
        )
        
        # 转换为Pydantic模型
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
                replace_std=std.replace_std,
                sources=std.sources if std.sources else [self.source_name],
                source_meta=std.source_meta
            )
            results.append(model)
        
        return results
    
    async def download(self, std_no: str, output_dir: str) -> Tuple[str, List[str]]:
        """下载标准"""
        if not self._source:
            raise Exception(f"ZBY源未初始化: {self._init_error}")
        
        # 内部函数用于在线程池中执行同步下载
        def _download_task():
            # 首先搜索获取完整的 Standard 对象（包含 source_meta）
            try:
                search_results = self._source.search(std_no)
                if not search_results:
                    return None, [f"未找到标准: {std_no}"]
                
                # 使用第一个搜索结果（最匹配的）
                item = search_results[0]
            except Exception as e:
                return None, [f"搜索失败: {str(e)}"]
            
            # 调用 ZBYSource.download(item, outdir)
            # 注意: 它返回 DownloadResult 对象
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
            # 简单搜索测试
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self._source.search,
                "GB"
            )
            return True
        except:
            return False
