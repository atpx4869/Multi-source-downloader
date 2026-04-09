# -*- coding: utf-8 -*-
"""
搜索服务 - 统一的搜索逻辑，消除代码重复
"""
import asyncio
import time
from typing import Dict, List, Optional
from pathlib import Path
import sys

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from web_app.backend.adapters.base import BaseAdapter
from web_app.backend.models.responses import SearchResponse
from web_app.backend.config import settings


class SearchService:
    """搜索服务 - 管理所有数据源的搜索"""
    
    def __init__(self, adapters: Dict[str, BaseAdapter]):
        """
        初始化搜索服务
        
        Args:
            adapters: 数据源适配器字典 {source_name: adapter}
        """
        self.adapters = adapters
    
    async def search_single(
        self, 
        source: str, 
        query: str, 
        limit: int = None,
        timeout: int = None
    ) -> SearchResponse:
        """
        在单个数据源中搜索
        
        Args:
            source: 数据源名称
            query: 搜索关键词
            limit: 最大结果数
            timeout: 超时时间（秒）
            
        Returns:
            SearchResponse: 搜索响应
        """
        if limit is None:
            limit = settings.SEARCH_LIMIT
        if timeout is None:
            timeout = settings.SEARCH_TIMEOUT
        
        start_time = time.time()
        
        adapter = self.adapters.get(source)
        if not adapter:
            return SearchResponse(
                source=source,
                query=query,
                count=0,
                items=[],
                error=f"数据源 {source} 不可用",
                elapsed_time=time.time() - start_time
            )
        
        try:
            # 使用asyncio.wait_for实现超时
            items = await asyncio.wait_for(
                adapter.search(query, limit),
                timeout=timeout
            )
            
            return SearchResponse(
                source=source,
                query=query,
                count=len(items),
                items=items,
                elapsed_time=time.time() - start_time
            )
            
        except asyncio.TimeoutError:
            return SearchResponse(
                source=source,
                query=query,
                count=0,
                items=[],
                error=f"搜索超时（{timeout}秒）",
                elapsed_time=time.time() - start_time
            )
        except Exception as e:
            return SearchResponse(
                source=source,
                query=query,
                count=0,
                items=[],
                error=str(e),
                elapsed_time=time.time() - start_time
            )
    
    async def search_all(
        self,
        query: str,
        sources: Optional[List[str]] = None,
        limit: int = None,
        timeout: int = None
    ) -> Dict[str, SearchResponse]:
        """
        在所有数据源中并发搜索
        
        Args:
            query: 搜索关键词
            sources: 指定的数据源列表（None表示全部）
            limit: 每个源的最大结果数
            timeout: 每个源的超时时间
            
        Returns:
            Dict[str, SearchResponse]: {source_name: response}
        """
        # 确定要搜索的数据源
        if sources is None:
            sources = list(self.adapters.keys())
        else:
            # 过滤掉不可用的源
            sources = [s for s in sources if s in self.adapters]
        
        # 并发搜索所有源
        tasks = [
            self.search_single(source, query, limit, timeout)
            for source in sources
        ]
        
        results = await asyncio.gather(*tasks)
        
        # 构建结果字典
        return {
            source: result 
            for source, result in zip(sources, results)
        }
    
    async def search_first_available(
        self,
        query: str,
        limit: int = None,
        timeout: int = None
    ) -> Optional[SearchResponse]:
        """
        按优先级搜索，返回第一个成功的结果
        
        Args:
            query: 搜索关键词
            limit: 最大结果数
            timeout: 超时时间
            
        Returns:
            Optional[SearchResponse]: 第一个成功的响应，或None
        """
        # 按优先级排序
        sources = sorted(
            self.adapters.keys(),
            key=lambda s: settings.SOURCE_PRIORITY.index(s) 
                if s in settings.SOURCE_PRIORITY else 999
        )
        
        for source in sources:
            response = await self.search_single(source, query, limit, timeout)
            if response.count > 0 and not response.error:
                return response
        
        return None
