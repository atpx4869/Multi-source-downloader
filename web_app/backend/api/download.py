# -*- coding: utf-8 -*-
"""
下载API路由
"""
from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from pathlib import Path
import sys

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from web_app.backend.models.responses import DownloadResponse

router = APIRouter(prefix="/download", tags=["下载"])

# 全局服务实例
download_service = None


def set_download_service(service):
    """设置下载服务实例"""
    global download_service
    download_service = service


@router.post("/{source}/{std_no:path}", response_model=DownloadResponse)
async def download_from_source(
    source: str,
    std_no: str,
    output_dir: Optional[str] = Query(None, description="输出目录")
):
    """
    从指定数据源下载标准
    
    - **source**: 数据源名称（ZBY/GBW/BY）
    - **std_no**: 标准编号（支持包含斜杠的标准号，如 GB/T 3324-2017）
    - **output_dir**: 可选，输出目录
    """
    if not download_service:
        raise HTTPException(status_code=500, detail="下载服务未初始化")
    
    return await download_service.download(source, std_no, output_dir)


@router.post("/first/{std_no:path}", response_model=DownloadResponse)
async def download_first_available(
    std_no: str,
    output_dir: Optional[str] = Query(None, description="输出目录")
):
    """
    按优先级尝试下载，返回第一个成功的
    
    - **std_no**: 标准编号（支持包含斜杠的标准号）
    - **output_dir**: 可选，输出目录
    
    优先级顺序：GBW > BY > ZBY
    """
    if not download_service:
        raise HTTPException(status_code=500, detail="下载服务未初始化")
    
    return await download_service.download_first_available(std_no, output_dir)


@router.get("/check-cache/{std_no:path}")
async def check_cache(std_no: str):
    """
    检查文件是否已缓存
    
    - **std_no**: 标准编号
    
    返回: {"cached": true/false, "filename": "文件名" (如果存在)}
    """
    from web_app.backend.config import settings
    import logging
    
    logger = logging.getLogger(__name__)
    
    output_path = Path(settings.DOWNLOAD_DIR)
    safe_std_no = std_no.replace('/', '-').replace('\\', '-')
    
    logger.info(f"检查缓存: std_no={std_no}, safe_std_no={safe_std_no}, output_path={output_path}")
    
    possible_files = list(output_path.glob(f"*{safe_std_no}*.pdf"))
    
    logger.info(f"找到文件: {[f.name for f in possible_files]}")
    
    if possible_files:
        result = {
            "cached": True,
            "filename": possible_files[0].name
        }
        logger.info(f"返回结果: {result}")
        return result
    else:
        result = {
            "cached": False,
            "filename": None
        }
        logger.info(f"返回结果: {result}")
        return result

