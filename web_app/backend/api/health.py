# -*- coding: utf-8 -*-
"""
健康检查API路由
"""
from fastapi import APIRouter
import time
from pathlib import Path
import sys

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from web_app.backend.models.responses import HealthResponse, SourceHealth

router = APIRouter(prefix="/health", tags=["健康检查"])

# 全局适配器
adapters = None


def set_adapters(adapter_dict):
    """设置适配器"""
    global adapters
    adapters = adapter_dict


@router.get("/", response_model=HealthResponse)
async def check_health():
    """
    检查所有数据源的健康状态
    
    返回每个数据源的可用性和响应时间
    """
    if not adapters:
        return HealthResponse(
            sources=[],
            healthy=False,
            timestamp=time.time()
        )
    
    sources_health = []
    
    for name, adapter in adapters.items():
        start_time = time.time()
        try:
            is_healthy = await adapter.check_health()
            response_time = (time.time() - start_time) * 1000  # 转换为毫秒
            
            sources_health.append(SourceHealth(
                name=name,
                available=is_healthy,
                response_time=response_time,
                last_check=time.time()
            ))
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            sources_health.append(SourceHealth(
                name=name,
                available=False,
                response_time=response_time,
                error=str(e),
                last_check=time.time()
            ))
    
    return HealthResponse(
        sources=sources_health,
        healthy=all(s.available for s in sources_health),
        timestamp=time.time()
    )


@router.get("/ping")
async def ping():
    """简单的ping检查"""
    return {"status": "ok", "timestamp": time.time()}
