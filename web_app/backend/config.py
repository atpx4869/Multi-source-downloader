# -*- coding: utf-8 -*-
"""
配置管理 - 使用Pydantic Settings
"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """应用配置"""
    
    # 应用信息
    APP_NAME: str = "标准文献检索系统"
    APP_VERSION: str = "2.0.0"
    
    # API配置
    API_PREFIX: str = "/api"
    DOCS_URL: str = "/api/docs"
    
    # CORS配置
    CORS_ORIGINS: List[str] = ["*"]
    
    # 搜索配置
    SEARCH_TIMEOUT: int = 20
    SEARCH_LIMIT: int = 100
    
    # 下载配置
    DOWNLOAD_DIR: str = "downloads"
    
    # 数据源优先级
    SOURCE_PRIORITY: List[str] = ["GBW", "BY", "ZBY"]
    
    # 启用的数据源
    ENABLED_SOURCES: List[str] = ["ZBY", "GBW", "BY"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# 全局配置实例
settings = Settings()
