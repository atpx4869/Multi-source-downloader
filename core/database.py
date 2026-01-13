# -*- coding: utf-8 -*-
"""
数据库管理模块 - SQLite
负责任务队列、历史记录、缓存索引的持久化存储
"""
import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any
from contextlib import contextmanager
import threading


class Database:
    """SQLite 数据库管理器"""
    
    def __init__(self, db_path: str = "data/app.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._local = threading.local()
        self._init_database()
    
    def _get_connection(self):
        """获取线程本地连接"""
        if not hasattr(self._local, 'conn') or self._local.conn is None:
            self._local.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
            self._local.conn.row_factory = sqlite3.Row
        return self._local.conn
    
    @contextmanager
    def get_cursor(self):
        """上下文管理器：自动提交或回滚"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cursor.close()
    
    def _init_database(self):
        """初始化数据库表结构"""
        with self.get_cursor() as cursor:
            # 下载任务队列表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS download_tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT UNIQUE NOT NULL,
                    std_no TEXT NOT NULL,
                    std_name TEXT,
                    status TEXT DEFAULT 'pending',
                    priority INTEGER DEFAULT 5,
                    source TEXT,
                    retry_count INTEGER DEFAULT 0,
                    max_retries INTEGER DEFAULT 3,
                    error_msg TEXT,
                    created_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                    started_time DATETIME,
                    completed_time DATETIME,
                    file_path TEXT,
                    metadata TEXT
                )
            """)
            
            # 索引
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_task_status 
                ON download_tasks(status)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_task_priority 
                ON download_tasks(priority DESC, created_time ASC)
            """)
            
            # 搜索历史表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS search_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    keyword TEXT NOT NULL,
                    sources TEXT,
                    result_count INTEGER,
                    search_time DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_search_keyword 
                ON search_history(keyword)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_search_time 
                ON search_history(search_time DESC)
            """)
            
            # 下载历史表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS download_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    std_no TEXT NOT NULL,
                    std_no_normalized TEXT,
                    std_name TEXT,
                    source TEXT,
                    file_path TEXT,
                    file_size INTEGER,
                    download_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'success'
                )
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_download_std_no 
                ON download_history(std_no_normalized)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_download_time 
                ON download_history(download_time DESC)
            """)
            
            # 缓存索引表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cache_index (
                    std_no_normalized TEXT PRIMARY KEY,
                    std_no_original TEXT,
                    std_name TEXT,
                    has_local_file BOOLEAN DEFAULT 0,
                    local_path TEXT,
                    sources TEXT,
                    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT
                )
            """)
    
    # ==================== 任务队列操作 ====================
    
    def add_task(self, task_data: Dict[str, Any]) -> int:
        """添加下载任务"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO download_tasks 
                (task_id, std_no, std_name, status, priority, source, max_retries, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                task_data['task_id'],
                task_data['std_no'],
                task_data.get('std_name', ''),
                task_data.get('status', 'pending'),
                task_data.get('priority', 5),
                task_data.get('source', ''),
                task_data.get('max_retries', 3),
                json.dumps(task_data.get('metadata', {}))
            ))
            return cursor.lastrowid
    
    def update_task(self, task_id: str, updates: Dict[str, Any]):
        """更新任务信息"""
        set_clauses = []
        values = []
        
        for key, value in updates.items():
            if key == 'metadata':
                value = json.dumps(value)
            set_clauses.append(f"{key} = ?")
            values.append(value)
        
        values.append(task_id)
        
        with self.get_cursor() as cursor:
            cursor.execute(f"""
                UPDATE download_tasks 
                SET {', '.join(set_clauses)}
                WHERE task_id = ?
            """, values)
    
    def get_task(self, task_id: str) -> Optional[Dict]:
        """获取任务详情"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT * FROM download_tasks WHERE task_id = ?
            """, (task_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_tasks_by_status(self, status: str) -> List[Dict]:
        """按状态获取任务列表"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT * FROM download_tasks 
                WHERE status = ?
                ORDER BY priority DESC, created_time ASC
            """, (status,))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_all_tasks(self) -> List[Dict]:
        """获取所有任务"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT * FROM download_tasks 
                ORDER BY 
                    CASE status
                        WHEN 'running' THEN 1
                        WHEN 'pending' THEN 2
                        WHEN 'paused' THEN 3
                        WHEN 'failed' THEN 4
                        WHEN 'completed' THEN 5
                        ELSE 6
                    END,
                    priority DESC,
                    created_time ASC
            """)
            return [dict(row) for row in cursor.fetchall()]
    
    def delete_task(self, task_id: str):
        """删除任务"""
        with self.get_cursor() as cursor:
            cursor.execute("DELETE FROM download_tasks WHERE task_id = ?", (task_id,))
    
    def clear_completed_tasks(self):
        """清空已完成任务"""
        with self.get_cursor() as cursor:
            cursor.execute("DELETE FROM download_tasks WHERE status = 'completed'")
    
    def get_task_statistics(self) -> Dict[str, int]:
        """获取任务统计信息"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT status, COUNT(*) as count 
                FROM download_tasks 
                GROUP BY status
            """)
            stats = {row['status']: row['count'] for row in cursor.fetchall()}
            
            cursor.execute("SELECT COUNT(*) as total FROM download_tasks")
            stats['total'] = cursor.fetchone()['total']
            
            return stats
    
    # ==================== 搜索历史操作 ====================
    
    def add_search_history(self, keyword: str, sources: List[str], result_count: int):
        """添加搜索历史"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO search_history (keyword, sources, result_count)
                VALUES (?, ?, ?)
            """, (keyword, ','.join(sources), result_count))
    
    def get_search_history(self, limit: int = 50) -> List[Dict]:
        """获取搜索历史"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT * FROM search_history 
                ORDER BY search_time DESC 
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]
    
    def search_history_by_keyword(self, keyword: str, limit: int = 20) -> List[Dict]:
        """按关键词搜索历史"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT * FROM search_history 
                WHERE keyword LIKE ?
                ORDER BY search_time DESC 
                LIMIT ?
            """, (f"%{keyword}%", limit))
            return [dict(row) for row in cursor.fetchall()]
    
    def delete_search_history(self, keyword: str) -> bool:
        """删除特定关键词的搜索历史"""
        try:
            with self.get_cursor() as cursor:
                cursor.execute("""
                    DELETE FROM search_history 
                    WHERE keyword = ?
                """, (keyword,))
                return cursor.rowcount > 0
        except Exception as e:
            print(f"删除搜索历史失败: {e}")
            return False
    
    def clear_search_history(self, days: int = 30):
        """清空搜索历史（超过指定天数）"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                DELETE FROM search_history 
                WHERE search_time < datetime('now', ? || ' days')
            """, (f"-{days}",))
    
    # ==================== 下载历史操作 ====================
    
    def add_download_history(self, std_no: str, std_no_normalized: str, std_name: str,
                            source: str, file_path: str, file_size: int = 0, status: str = 'success'):
        """添加下载历史"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO download_history 
                (std_no, std_no_normalized, std_name, source, file_path, file_size, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (std_no, std_no_normalized, std_name, source, file_path, file_size, status))
    
    def get_download_history(self, limit: int = 100) -> List[Dict]:
        """获取下载历史"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT * FROM download_history 
                ORDER BY download_time DESC 
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]
    
    def find_downloaded_file(self, std_no_normalized: str) -> Optional[Dict]:
        """查找已下载的文件"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT * FROM download_history 
                WHERE std_no_normalized = ? AND status = 'success'
                ORDER BY download_time DESC 
                LIMIT 1
            """, (std_no_normalized,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def clear_download_history(self, days: int = 90):
        """清空下载历史（保留文件）"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                DELETE FROM download_history 
                WHERE download_time < datetime('now', ? || ' days')
            """, (f"-{days}",))
    
    # ==================== 缓存索引操作 ====================
    
    def update_cache_index(self, std_no_normalized: str, std_no_original: str,
                          std_name: str, local_path: str = None, sources: List[str] = None):
        """更新缓存索引"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                INSERT OR REPLACE INTO cache_index 
                (std_no_normalized, std_no_original, std_name, has_local_file, local_path, sources, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                std_no_normalized,
                std_no_original,
                std_name,
                1 if local_path else 0,
                local_path,
                ','.join(sources) if sources else ''
            ))
    
    def get_cache_index(self, std_no_normalized: str) -> Optional[Dict]:
        """获取缓存索引"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT * FROM cache_index WHERE std_no_normalized = ?
            """, (std_no_normalized,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def clear_invalid_cache(self):
        """清除无效缓存（文件不存在）"""
        with self.get_cursor() as cursor:
            cursor.execute("SELECT * FROM cache_index WHERE has_local_file = 1")
            rows = cursor.fetchall()
            
            deleted_count = 0
            for row in rows:
                if row['local_path'] and not Path(row['local_path']).exists():
                    cursor.execute("""
                        DELETE FROM cache_index WHERE std_no_normalized = ?
                    """, (row['std_no_normalized'],))
                    deleted_count += 1
            
            return deleted_count
    
    def get_cache_statistics(self) -> Dict[str, Any]:
        """获取缓存统计"""
        with self.get_cursor() as cursor:
            cursor.execute("SELECT COUNT(*) as total FROM cache_index")
            total = cursor.fetchone()['total']
            
            cursor.execute("""
                SELECT COUNT(*) as count FROM cache_index WHERE has_local_file = 1
            """)
            with_file = cursor.fetchone()['count']
            
            cursor.execute("""
                SELECT COUNT(*) as count FROM search_history
            """)
            search_count = cursor.fetchone()['count']
            
            cursor.execute("""
                SELECT COUNT(*) as count FROM download_history
            """)
            download_count = cursor.fetchone()['count']
            
            return {
                'cache_total': total,
                'cache_with_file': with_file,
                'search_history_count': search_count,
                'download_history_count': download_count
            }
    
    def close(self):
        """关闭数据库连接"""
        if hasattr(self._local, 'conn') and self._local.conn:
            self._local.conn.close()
            self._local.conn = None


# 全局数据库实例
_db_instance = None


def get_database() -> Database:
    """获取全局数据库实例"""
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
    return _db_instance
