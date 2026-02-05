# -*- coding: utf-8 -*-
"""
下载服务
"""
import time
from typing import Optional, Dict
from pathlib import Path
import sys

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from web_app.backend.adapters.base import BaseAdapter
from web_app.backend.models.responses import DownloadResponse
from web_app.backend.config import settings


class DownloadService:
    """下载服务"""
    
    def __init__(self, adapters: Dict[str, BaseAdapter]):
        self.adapters = adapters
    
    async def download(
        self,
        source: str,
        std_no: str,
        output_dir: Optional[str] = None
    ) -> DownloadResponse:
        """
        从指定数据源下载标准
        
        Args:
            source: 数据源名称
            std_no: 标准编号
            output_dir: 输出目录
            
        Returns:
            DownloadResponse: 下载响应
        """
        if output_dir is None:
            output_dir = settings.DOWNLOAD_DIR
        
        start_time = time.time()
        
        adapter = self.adapters.get(source)
        if not adapter:
            return DownloadResponse(
                source=source,
                std_no=std_no,
                status="error",
                error=f"数据源 {source} 不可用",
                elapsed_time=time.time() - start_time
            )
        
        # 缓存优化：检查本地是否已存在文件
        output_path = Path(output_dir)
        # 尝试查找可能的文件名（标准号可能包含特殊字符）
        safe_std_no = std_no.replace('/', '-').replace('\\', '-')
        possible_files = list(output_path.glob(f"*{safe_std_no}*.pdf"))
        
        if possible_files:
            # 找到缓存文件，直接返回
            cached_file = possible_files[0]
            return DownloadResponse(
                source=source,
                std_no=std_no,
                status="success",
                file_path=str(cached_file),
                filename=cached_file.name,
                file_size=cached_file.stat().st_size,
                logs=[f"使用缓存文件: {cached_file.name}"],
                elapsed_time=time.time() - start_time
            )
        
        # 缓存未命中，执行下载
        try:
            filepath, logs = await adapter.download(std_no, output_dir)
            
            if filepath:
                file_path_obj = Path(filepath)
                return DownloadResponse(
                    source=source,
                    std_no=std_no,
                    status="success",
                    file_path=str(filepath),
                    filename=file_path_obj.name,
                    file_size=file_path_obj.stat().st_size if file_path_obj.exists() else 0,
                    logs=logs,
                    elapsed_time=time.time() - start_time
                )
            else:
                return DownloadResponse(
                    source=source,
                    std_no=std_no,
                    status="failed",
                    error="下载失败",
                    logs=logs,
                    elapsed_time=time.time() - start_time
                )
                
        except Exception as e:
            return DownloadResponse(
                source=source,
                std_no=std_no,
                status="error",
                error=str(e),
                elapsed_time=time.time() - start_time
            )
    
    async def download_first_available(
        self,
        std_no: str,
        output_dir: Optional[str] = None
    ) -> DownloadResponse:
        """
        按优先级尝试下载，返回第一个成功的
        
        Args:
            std_no: 标准编号
            output_dir: 输出目录
            
        Returns:
            DownloadResponse: 下载响应
        """
        sources = sorted(
            self.adapters.keys(),
            key=lambda s: settings.SOURCE_PRIORITY.index(s)
                if s in settings.SOURCE_PRIORITY else 999
        )
        
        for source in sources:
            response = await self.download(source, std_no, output_dir)
            if response.status == "success":
                return response
        
        # 所有源都失败
        return DownloadResponse(
            source="ALL",
            std_no=std_no,
            status="failed",
            error="所有数据源都下载失败",
            elapsed_time=0.0
        )
