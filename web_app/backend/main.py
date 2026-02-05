# -*- coding: utf-8 -*-
"""
FastAPI主应用
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import sys

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from web_app.backend.config import settings
from web_app.backend.adapters import ZBYAdapter, GBWAdapter, BYAdapter
from web_app.backend.services.search import SearchService
from web_app.backend.services.download import DownloadService
from web_app.backend.api import search, download, health

# 创建FastAPI应用
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="现代化的标准文献检索系统API",
    docs_url=settings.DOCS_URL,
    redoc_url="/api/redoc"
)

# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件目录，用于提供下载文件访问
from fastapi.staticfiles import StaticFiles
import os
import time
import logging
from fastapi import Request

# 配置后端日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api")

# 请求日志中间件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000
    logger.info(f"Method: {request.method} Path: {request.url.path} Status: {response.status_code} Time: {process_time:.2f}ms")
    return response

# 确保下载目录存在
if not os.path.exists(settings.DOWNLOAD_DIR):
    os.makedirs(settings.DOWNLOAD_DIR)

app.mount("/downloads", StaticFiles(directory=settings.DOWNLOAD_DIR), name="downloads")


# 初始化适配器
adapters = {}

if "ZBY" in settings.ENABLED_SOURCES:
    adapters["ZBY"] = ZBYAdapter(settings.DOWNLOAD_DIR)

if "GBW" in settings.ENABLED_SOURCES:
    adapters["GBW"] = GBWAdapter()

if "BY" in settings.ENABLED_SOURCES:
    adapters["BY"] = BYAdapter()


# 初始化服务
search_service_instance = SearchService(adapters)
download_service_instance = DownloadService(adapters)

# 注入服务到路由
search.set_search_service(search_service_instance)
download.set_download_service(download_service_instance)
health.set_adapters(adapters)

# 注册路由
app.include_router(search.router, prefix=settings.API_PREFIX)
app.include_router(download.router, prefix=settings.API_PREFIX)
app.include_router(health.router, prefix=settings.API_PREFIX)


@app.get("/")
async def root():
    """根路径"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": settings.DOCS_URL,
        "enabled_sources": list(adapters.keys())
    }


@app.get("/api")
async def api_info():
    """API信息"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "endpoints": {
            "search_all": f"{settings.API_PREFIX}/search/",
            "search_single": f"{settings.API_PREFIX}/search/{{source}}",
            "download": f"{settings.API_PREFIX}/download/{{source}}/{{std_no}}",
            "health": f"{settings.API_PREFIX}/health/",
            "docs": settings.DOCS_URL
        },
        "enabled_sources": list(adapters.keys())
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
