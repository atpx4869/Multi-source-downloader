# -*- coding: utf-8 -*-
"""
Pydantic响应模型 - 类型安全的API响应
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class StandardModel(BaseModel):
    """标准信息模型"""
    std_no: str = Field(..., description="标准编号")
    name: str = Field(..., description="标准名称")
    source: str = Field(..., description="数据源")
    has_pdf: bool = Field(default=False, description="是否有PDF")
    publish_date: Optional[str] = Field(None, description="发布日期")
    implement_date: Optional[str] = Field(None, description="实施日期")
    status: Optional[str] = Field(None, description="状态（现行/废止）")
    replace_std: Optional[str] = Field(None, description="替代标准")
    
    class Config:
        json_schema_extra = {
            "example": {
                "std_no": "GB/T 3324-2017",
                "name": "木家具通用技术条件",
                "source": "ZBY",
                "has_pdf": True,
                "publish_date": "2017-05-12",
                "status": "现行"
            }
        }


class SearchResponse(BaseModel):
    """搜索响应模型"""
    source: str = Field(..., description="数据源")
    query: str = Field(..., description="搜索关键词")
    count: int = Field(..., description="结果数量")
    items: List[StandardModel] = Field(default_factory=list, description="搜索结果")
    error: Optional[str] = Field(None, description="错误信息")
    elapsed_time: float = Field(..., description="耗时（秒）")


class DownloadResponse(BaseModel):
    """下载响应模型"""
    source: str = Field(..., description="数据源")
    std_no: str = Field(..., description="标准编号")
    status: str = Field(..., description="状态: success/failed/error")
    file_path: Optional[str] = Field(None, description="文件路径")
    filename: Optional[str] = Field(None, description="文件名")
    file_size: int = Field(default=0, description="文件大小（字节）")
    error: Optional[str] = Field(None, description="错误信息")
    logs: List[str] = Field(default_factory=list, description="日志")
    elapsed_time: float = Field(..., description="耗时（秒）")


class SourceHealth(BaseModel):
    """数据源健康状态"""
    name: str = Field(..., description="数据源名称")
    available: bool = Field(..., description="是否可用")
    response_time: float = Field(..., description="响应时间（毫秒）")
    error: Optional[str] = Field(None, description="错误信息")
    last_check: float = Field(..., description="最后检查时间戳")


class HealthResponse(BaseModel):
    """健康检查响应"""
    sources: List[SourceHealth] = Field(default_factory=list, description="各源状态")
    healthy: bool = Field(..., description="整体是否健康")
    timestamp: float = Field(..., description="检查时间戳")


class ErrorResponse(BaseModel):
    """错误响应"""
    error: str = Field(..., description="错误信息")
    detail: Optional[str] = Field(None, description="详细信息")
    timestamp: float = Field(default_factory=lambda: datetime.now().timestamp())
