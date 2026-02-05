# -*- coding: utf-8 -*-
"""
基础数据源适配器 - 定义统一接口
"""
from abc import ABC, abstractmethod
from typing import List, Tuple
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from web_app.backend.models.responses import StandardModel


class BaseAdapter(ABC):
    """基础数据源适配器"""
    
    source_name: str = "BASE"
    
    @abstractmethod
    async def search(self, query: str, limit: int = 100) -> List[StandardModel]:
        """
        搜索标准
        
        Args:
            query: 搜索关键词
            limit: 最大结果数
            
        Returns:
            List[StandardModel]: 标准列表
        """
        pass
    
    @abstractmethod
    async def download(self, std_no: str, output_dir: str) -> Tuple[str, List[str]]:
        """
        下载标准
        
        Args:
            std_no: 标准编号
            output_dir: 输出目录
            
        Returns:
            tuple[str, List[str]]: (文件路径, 日志列表)
        """
        pass
    
    @abstractmethod
    async def check_health(self) -> bool:
        """
        检查数据源健康状态
        
        Returns:
            bool: 是否健康
        """
        pass
    
    def __repr__(self):
        return f"{self.__class__.__name__}({self.source_name})"
