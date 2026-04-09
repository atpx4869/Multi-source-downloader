# -*- coding: utf-8 -*-
"""
搜索API路由
"""
from fastapi import APIRouter, Query, HTTPException
from typing import List, Optional
from pathlib import Path
import sys

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from web_app.backend.models.responses import SearchResponse

router = APIRouter(prefix="/search", tags=["搜索"])

# 全局服务实例（将在main.py中注入）
search_service = None


def set_search_service(service):
    """设置搜索服务实例"""
    global search_service
    search_service = service


@router.get("/", response_model=dict)
async def search_all_sources(
    q: str = Query(..., description="搜索关键词", min_length=1),
    sources: Optional[List[str]] = Query(None, description="指定数据源（ZBY/GBW/BY）"),
    limit: Optional[int] = Query(100, description="每个源的最大结果数", ge=1, le=500),
    timeout: Optional[int] = Query(30, description="超时时间（秒）", ge=1, le=60)
):
    """
    在所有或指定数据源中搜索标准
    
    - **q**: 搜索关键词（标准号或名称）
    - **sources**: 可选，指定要搜索的数据源列表
    - **limit**: 每个源返回的最大结果数
    - **timeout**: 每个源的超时时间
    
    返回格式：
    ```json
    {
        "ZBY": {
            "source": "ZBY",
            "query": "GB/T 3324",
            "count": 10,
            "items": [...],
            "elapsed_time": 1.23
        },
        ...
    }
    ```
    """
    if not search_service:
        raise HTTPException(status_code=500, detail="搜索服务未初始化")
    
    results = await search_service.search_all(q, sources, limit, timeout)
    
    # 转换为字典
    return {
        source: response.model_dump()
        for source, response in results.items()
    }


@router.get("/{source}", response_model=SearchResponse)
async def search_single_source(
    source: str,
    q: str = Query(..., description="搜索关键词", min_length=1),
    limit: Optional[int] = Query(100, description="最大结果数", ge=1, le=500),
    timeout: Optional[int] = Query(30, description="超时时间（秒）", ge=1, le=60)
):
    """
    在指定数据源中搜索
    
    - **source**: 数据源名称（ZBY/GBW/BY）
    - **q**: 搜索关键词
    - **limit**: 最大结果数
    - **timeout**: 超时时间
    """
    if not search_service:
        raise HTTPException(status_code=500, detail="搜索服务未初始化")
    
    return await search_service.search_single(source, q, limit, timeout)


@router.get("/first/available", response_model=SearchResponse)
async def search_first_available(
    q: str = Query(..., description="搜索关键词", min_length=1),
    limit: Optional[int] = Query(100, description="最大结果数", ge=1, le=500),
    timeout: Optional[int] = Query(30, description="超时时间（秒）", ge=1, le=60)
):
    """
    按优先级搜索，返回第一个成功的结果
    
    优先级顺序：GBW > BY > ZBY
    """
    if not search_service:
        raise HTTPException(status_code=500, detail="搜索服务未初始化")
    
    result = await search_service.search_first_available(q, limit, timeout)
    
    if not result:
        raise HTTPException(status_code=404, detail="所有数据源都搜索失败")
    
    return result
