# -*- coding: utf-8 -*-
"""
缓存管理模块
支持分层缓存、智能去重、自动清理
"""
import json
import re
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import threading

from core.database import get_database


def normalize_std_no(std_no: str) -> str:
    """标准化标准号
    
    GB/T 1234-2020 → gbt12342020
    GB 5678.1-2019 → gb567812019
    """
    if not std_no:
        return ""
    # 去除空格、横杠、斜杠、点
    normalized = re.sub(r'[\s\-/\.]', '', std_no)
    return normalized.lower()


class CacheManager:
    """缓存管理器"""
    
    def __init__(self, cache_dir: str = "cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # 子目录
        self.search_cache_dir = self.cache_dir / "search"
        self.download_cache_dir = self.cache_dir / "downloads"
        self.search_cache_dir.mkdir(exist_ok=True)
        self.download_cache_dir.mkdir(exist_ok=True)
        
        self.db = get_database()
        
        # 内存缓存（LRU策略）
        self._memory_cache: Dict[str, Any] = {}
        self._cache_order: List[str] = []  # 用于 LRU 排序
        self._max_memory_cache = 1000
        self._lock = threading.Lock()
        
        # 缓存配置
        self.search_cache_days = 7  # 搜索结果缓存7天
        self.auto_clean_enabled = True
    
    # ==================== 内存缓存操作 ====================
    
    def _add_to_memory(self, key: str, value: Any):
        """添加到内存缓存（LRU）"""
        with self._lock:
            if key in self._memory_cache:
                # 已存在，移到末尾
                self._cache_order.remove(key)
            elif len(self._memory_cache) >= self._max_memory_cache:
                # 达到上限，移除最旧的
                oldest = self._cache_order.pop(0)
                del self._memory_cache[oldest]
            
            self._memory_cache[key] = value
            self._cache_order.append(key)
    
    def _get_from_memory(self, key: str) -> Optional[Any]:
        """从内存缓存获取"""
        with self._lock:
            if key in self._memory_cache:
                # 更新访问顺序
                self._cache_order.remove(key)
                self._cache_order.append(key)
                return self._memory_cache[key]
        return None
    
    def clear_memory_cache(self):
        """清空内存缓存"""
        with self._lock:
            self._memory_cache.clear()
            self._cache_order.clear()
    
    # ==================== 搜索缓存 ====================
    
    def _get_search_cache_key(self, keyword: str, sources: List[str], page: int = 1) -> str:
        """生成搜索缓存键"""
        sources_str = '_'.join(sorted(sources))
        key_str = f"{keyword}_{sources_str}_p{page}"
        # 使用 MD5 缩短文件名
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get_search_cache(self, keyword: str, sources: List[str], page: int = 1) -> Optional[List[Dict]]:
        """获取搜索缓存"""
        cache_key = self._get_search_cache_key(keyword, sources, page)
        
        # 1. 检查内存缓存
        memory_result = self._get_from_memory(f"search_{cache_key}")
        if memory_result:
            return memory_result
        
        # 2. 检查文件缓存
        cache_file = self.search_cache_dir / f"{cache_key}.json"
        if cache_file.exists():
            try:
                data = json.loads(cache_file.read_text(encoding='utf-8'))
                
                # 检查是否过期
                cache_time = datetime.fromisoformat(data['cache_time'])
                if datetime.now() - cache_time < timedelta(days=self.search_cache_days):
                    results = data['results']
                    # 加入内存缓存
                    self._add_to_memory(f"search_{cache_key}", results)
                    return results
                else:
                    # 过期，删除文件
                    cache_file.unlink()
            except Exception as e:
                print(f"读取搜索缓存失败: {e}")
        
        return None
    
    def save_search_cache(self, keyword: str, sources: List[str], page: int, results: List[Dict]):
        """保存搜索缓存"""
        cache_key = self._get_search_cache_key(keyword, sources, page)
        
        # 保存到内存
        self._add_to_memory(f"search_{cache_key}", results)
        
        # 保存到文件
        cache_file = self.search_cache_dir / f"{cache_key}.json"
        try:
            data = {
                'keyword': keyword,
                'sources': sources,
                'page': page,
                'cache_time': datetime.now().isoformat(),
                'results': results
            }
            cache_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
        except Exception as e:
            print(f"保存搜索缓存失败: {e}")
        
        # 记录到数据库
        try:
            self.db.add_search_history(keyword, sources, len(results))
        except Exception as e:
            print(f"记录搜索历史失败: {e}")
    
    def clear_search_cache(self, days: int = None):
        """清空搜索缓存"""
        if days is None:
            # 清空所有
            for file in self.search_cache_dir.glob("*.json"):
                file.unlink()
        else:
            # 清空超过指定天数的
            cutoff_time = datetime.now() - timedelta(days=days)
            for file in self.search_cache_dir.glob("*.json"):
                try:
                    data = json.loads(file.read_text(encoding='utf-8'))
                    cache_time = datetime.fromisoformat(data['cache_time'])
                    if cache_time < cutoff_time:
                        file.unlink()
                except Exception:
                    pass
        
        # 清空数据库记录
        if days:
            self.db.clear_search_history(days)
    
    # ==================== 下载缓存与去重 ====================
    
    def check_downloaded(self, std_no: str) -> Optional[str]:
        """检查标准号是否已下载，返回文件路径"""
        std_no_norm = normalize_std_no(std_no)
        
        # 1. 检查内存缓存
        memory_key = f"download_{std_no_norm}"
        memory_result = self._get_from_memory(memory_key)
        if memory_result and Path(memory_result).exists():
            return memory_result
        
        # 2. 检查数据库
        cache_index = self.db.get_cache_index(std_no_norm)
        if cache_index and cache_index['has_local_file']:
            file_path = cache_index['local_path']
            if file_path and Path(file_path).exists():
                # 加入内存缓存
                self._add_to_memory(memory_key, file_path)
                return file_path
        
        # 3. 检查下载历史
        download_record = self.db.find_downloaded_file(std_no_norm)
        if download_record:
            file_path = download_record['file_path']
            if file_path and Path(file_path).exists():
                # 更新缓存索引
                self.db.update_cache_index(
                    std_no_norm, 
                    download_record['std_no'],
                    download_record['std_name'],
                    file_path,
                    [download_record['source']]
                )
                # 加入内存缓存
                self._add_to_memory(memory_key, file_path)
                return file_path
        
        return None
    
    def save_download_record(self, std_no: str, std_name: str, source: str,
                            file_path: str, file_size: int = 0):
        """保存下载记录"""
        std_no_norm = normalize_std_no(std_no)
        
        # 保存到内存缓存
        self._add_to_memory(f"download_{std_no_norm}", file_path)
        
        # 保存到数据库
        try:
            # 下载历史
            self.db.add_download_history(
                std_no, std_no_norm, std_name, source,
                file_path, file_size, 'success'
            )
            
            # 缓存索引
            self.db.update_cache_index(
                std_no_norm, std_no, std_name, file_path, [source]
            )
        except Exception as e:
            print(f"保存下载记录失败: {e}")
        
        # 保存元数据文件
        try:
            metadata_file = self.download_cache_dir / f"{std_no_norm}.json"
            metadata = {
                'std_no': std_no,
                'std_no_normalized': std_no_norm,
                'std_name': std_name,
                'source': source,
                'file_path': file_path,
                'file_size': file_size,
                'download_time': datetime.now().isoformat()
            }
            metadata_file.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding='utf-8')
        except Exception as e:
            print(f"保存下载元数据失败: {e}")
    
    def get_download_metadata(self, std_no: str) -> Optional[Dict]:
        """获取下载元数据"""
        std_no_norm = normalize_std_no(std_no)
        metadata_file = self.download_cache_dir / f"{std_no_norm}.json"
        
        if metadata_file.exists():
            try:
                return json.loads(metadata_file.read_text(encoding='utf-8'))
            except Exception as e:
                print(f"读取下载元数据失败: {e}")
        
        return None
    
    # ==================== 历史记录 ====================
    
    def get_search_history(self, limit: int = 50) -> List[Dict]:
        """获取搜索历史"""
        return self.db.get_search_history(limit)
    
    def get_download_history(self, limit: int = 100) -> List[Dict]:
        """获取下载历史"""
        return self.db.get_download_history(limit)
    
    def search_history_by_keyword(self, keyword: str, limit: int = 20) -> List[Dict]:
        """按关键词搜索历史"""
        return self.db.search_history_by_keyword(keyword, limit)
    
    # ==================== 缓存清理 ====================
    
    def clear_invalid_cache(self) -> int:
        """清除无效缓存（文件不存在）"""
        # 清理数据库中的无效记录
        deleted_count = self.db.clear_invalid_cache()
        
        # 清理元数据文件
        for metadata_file in self.download_cache_dir.glob("*.json"):
            try:
                metadata = json.loads(metadata_file.read_text(encoding='utf-8'))
                file_path = metadata.get('file_path')
                if file_path and not Path(file_path).exists():
                    metadata_file.unlink()
                    deleted_count += 1
            except Exception:
                pass
        
        return deleted_count
    
    def get_cache_size(self) -> Dict[str, Any]:
        """获取缓存大小统计"""
        def get_dir_size(path: Path) -> int:
            """递归计算目录大小"""
            total = 0
            for item in path.rglob('*'):
                if item.is_file():
                    total += item.stat().st_size
            return total
        
        search_size = get_dir_size(self.search_cache_dir)
        download_size = get_dir_size(self.download_cache_dir)
        
        return {
            'search_cache_mb': round(search_size / 1024 / 1024, 2),
            'download_cache_mb': round(download_size / 1024 / 1024, 2),
            'total_mb': round((search_size + download_size) / 1024 / 1024, 2),
            'search_file_count': len(list(self.search_cache_dir.glob("*.json"))),
            'download_file_count': len(list(self.download_cache_dir.glob("*.json")))
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        stats = self.db.get_cache_statistics()
        size_stats = self.get_cache_size()
        
        return {
            **stats,
            **size_stats,
            'memory_cache_size': len(self._memory_cache)
        }
    
    def auto_clean(self):
        """自动清理（根据配置）"""
        if not self.auto_clean_enabled:
            return
        
        # 清理过期搜索缓存
        self.clear_search_cache(days=self.search_cache_days)
        
        # 清理无效缓存
        self.clear_invalid_cache()
        
        # 限制内存缓存大小
        if len(self._memory_cache) > self._max_memory_cache:
            with self._lock:
                to_remove = len(self._memory_cache) - self._max_memory_cache
                for _ in range(to_remove):
                    if self._cache_order:
                        oldest = self._cache_order.pop(0)
                        del self._memory_cache[oldest]


# 全局缓存管理器实例
_cache_manager: Optional[CacheManager] = None


def get_cache_manager() -> CacheManager:
    """获取全局缓存管理器实例"""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager
