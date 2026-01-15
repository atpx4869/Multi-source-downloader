# -*- coding: utf-8 -*-
"""
UI Service Adapter - 连接 UI 层和 Service 层

这是一个过渡层，用于将现有的 UI 代码逐步迁移到新的 Service 架构。
同时保持向后兼容性，不破坏现有的 Qt 信号系统。
"""

from pathlib import Path
from typing import List, Optional, Callable, Dict
from dataclasses import dataclass
from enum import Enum

from PyQt5 import QtCore, QtGui, QtWidgets

from core import DownloadService, SearchService, DownloadTask, SearchTask, TaskEvent, TaskStatus
from core.models import Standard


class UIDownloadAdapter:
    """UI 和 DownloadService 的适配器
    
    用途：
    1. 将 DownloadService 事件转换为 Qt Signal
    2. 维持现有 UI 的 API 兼容性
    3. 逐步迁移 UI 代码到新架构
    
    使用方式：
    
    ```python
    adapter = UIDownloadAdapter(parent_widget)
    adapter.download_started.connect(on_download_start)
    adapter.download_progress.connect(on_progress)
    adapter.download_completed.connect(on_completed)
    adapter.download_failed.connect(on_failed)
    
    task = adapter.submit_downloads(items, output_dir)
    status = adapter.get_status(task.id)
    adapter.cancel_download(task.id)
    ```
    """
    
    # Qt Signals
    download_started = QtCore.pyqtSignal(str)      # task_id
    download_progress = QtCore.pyqtSignal(str, int, int, str)  # task_id, current, total, message
    download_completed = QtCore.pyqtSignal(str, Path)  # task_id, file_path
    download_failed = QtCore.pyqtSignal(str, str)  # task_id, error
    download_cancelled = QtCore.pyqtSignal(str)    # task_id
    all_downloads_finished = QtCore.pyqtSignal(int, int)  # success_count, fail_count
    
    def __init__(self, max_workers: int = 3):
        self.service = DownloadService(max_workers=max_workers)
        self.service.start()
        
        # 订阅所有事件
        self.service.subscribe("progress", self._on_service_progress)
        self.service.subscribe("completed", self._on_service_completed)
        self.service.subscribe("failed", self._on_service_failed)
        self.service.subscribe("cancelled", self._on_service_cancelled)
        
        self._batch_tasks: List[str] = []  # 当前批次的所有任务 ID
    
    def submit_downloads(self, standards: List[Standard], output_dir: Path, 
                        batch_callback: Optional[Callable[[int, int], None]] = None) -> List[str]:
        """提交一批下载任务
        
        Args:
            standards: 标准列表
            output_dir: 输出目录
            batch_callback: 批次完成回调 (success_count, fail_count)
            
        Returns:
            任务 ID 列表
        """
        task_ids = []
        self._batch_tasks = []
        
        for std in standards:
            task = self.service.submit(std, output_dir)
            task_ids.append(task.id)
            self._batch_tasks.append(task.id)
            self.download_started.emit(task.id)
        
        # 启动监控线程，检测批次完成
        if batch_callback:
            self._monitor_batch(batch_callback)
        
        return task_ids
    
    def get_status(self, task_id: str) -> Optional[DownloadTask]:
        """获取单个任务状态"""
        return self.service.get_status(task_id)
    
    def cancel_download(self, task_id: str) -> bool:
        """取消单个下载"""
        return self.service.cancel(task_id)
    
    def cancel_all_downloads(self):
        """取消所有下载"""
        for task in self.service.get_all_tasks():
            if task.status == TaskStatus.PENDING or task.status == TaskStatus.RUNNING:
                self.service.cancel(task.id)
    
    def get_batch_status(self) -> Dict[str, int]:
        """获取批次统计
        
        Returns:
            {"running": N, "completed": N, "failed": N, "total": N}
        """
        all_tasks = self.service.get_all_tasks()
        batch_tasks = [t for t in all_tasks if t.id in self._batch_tasks]
        
        return {
            "total": len(batch_tasks),
            "running": sum(1 for t in batch_tasks if t.status == TaskStatus.RUNNING),
            "completed": sum(1 for t in batch_tasks if t.status == TaskStatus.COMPLETED),
            "failed": sum(1 for t in batch_tasks if t.status == TaskStatus.FAILED),
        }
    
    def shutdown(self):
        """关闭适配器和服务"""
        self.service.stop()
    
    # ============ 私有方法 ============
    
    def _on_service_progress(self, event: TaskEvent):
        """处理 Service 的 progress 事件"""
        self.download_progress.emit(event.task_id, 0, 100, event.message)
    
    def _on_service_completed(self, event: TaskEvent):
        """处理 Service 的 completed 事件"""
        if event.result and event.result.file_path:
            self.download_completed.emit(event.task_id, event.result.file_path)
            self._check_batch_completion()
    
    def _on_service_failed(self, event: TaskEvent):
        """处理 Service 的 failed 事件"""
        self.download_failed.emit(event.task_id, event.error or "Unknown error")
        self._check_batch_completion()
    
    def _on_service_cancelled(self, event: TaskEvent):
        """处理 Service 的 cancelled 事件"""
        self.download_cancelled.emit(event.task_id)
        self._check_batch_completion()
    
    def _monitor_batch(self, callback: Callable[[int, int], None]):
        """监控批次完成状态"""
        import threading
        import time
        
        def monitor():
            while True:
                status = self.get_batch_status()
                
                # 如果所有任务都完成了
                if status["running"] == 0 and (
                    status["completed"] + status["failed"] == status["total"]
                ):
                    callback(status["completed"], status["failed"])
                    self.all_downloads_finished.emit(status["completed"], status["failed"])
                    break
                
                time.sleep(0.5)
        
        thread = threading.Thread(target=monitor, daemon=True)
        thread.start()
    
    def _check_batch_completion(self):
        """检查批次是否完成"""
        status = self.get_batch_status()
        if status["running"] == 0 and status["completed"] + status["failed"] == status["total"]:
            self.all_downloads_finished.emit(status["completed"], status["failed"])


class UISearchAdapter:
    """UI 和 SearchService 的适配器"""
    
    search_started = QtCore.pyqtSignal(str)  # task_id
    search_result = QtCore.pyqtSignal(str, object)  # task_id, Standard
    search_progress = QtCore.pyqtSignal(str, str)  # task_id, message
    search_completed = QtCore.pyqtSignal(str, list)  # task_id, all_results
    search_failed = QtCore.pyqtSignal(str, str)  # task_id, error
    
    def __init__(self, max_workers: int = 3):
        self.service = SearchService(max_workers=max_workers)
        self.service.start()
        
        self.service.subscribe("progress", self._on_service_progress)
        self.service.subscribe("completed", self._on_service_completed)
        self.service.subscribe("failed", self._on_service_failed)
    
    def submit_search(self, keyword: str) -> str:
        """提交搜索任务
        
        Returns:
            任务 ID
        """
        task = self.service.submit(keyword)
        self.search_started.emit(task.id)
        return task.id
    
    def get_results(self, task_id: str, blocking: bool = True) -> List[Standard]:
        """获取搜索结果
        
        Args:
            task_id: 任务 ID
            blocking: 是否阻塞等待完成
            
        Returns:
            Standard 列表
        """
        task = self.service.get_status(task_id)
        if not task:
            return []
        
        if blocking:
            # 等待任务完成
            import time
            while task.status == TaskStatus.PENDING or task.status == TaskStatus.RUNNING:
                time.sleep(0.1)
        
        return task.results
    
    def shutdown(self):
        """关闭适配器和服务"""
        self.service.stop()
    
    # ============ 私有方法 ============
    
    def _on_service_progress(self, event: TaskEvent):
        """处理 Service 的 progress 事件"""
        self.search_progress.emit(event.task_id, event.message)
    
    def _on_service_completed(self, event: TaskEvent):
        """处理 Service 的 completed 事件"""
        if event.result:
            self.search_completed.emit(event.task_id, event.result)
    
    def _on_service_failed(self, event: TaskEvent):
        """处理 Service 的 failed 事件"""
        self.search_failed.emit(event.task_id, event.error or "Unknown error")


# 全局适配器实例（单例）
_download_adapter: Optional[UIDownloadAdapter] = None
_search_adapter: Optional[UISearchAdapter] = None


def get_download_adapter() -> UIDownloadAdapter:
    """获取全局下载适配器实例"""
    global _download_adapter
    if _download_adapter is None:
        _download_adapter = UIDownloadAdapter(max_workers=3)
    return _download_adapter


def get_search_adapter() -> UISearchAdapter:
    """获取全局搜索适配器实例"""
    global _search_adapter
    if _search_adapter is None:
        _search_adapter = UISearchAdapter(max_workers=3)
    return _search_adapter


def shutdown_adapters():
    """关闭所有适配器"""
    global _download_adapter, _search_adapter
    if _download_adapter:
        _download_adapter.shutdown()
        _download_adapter = None
    if _search_adapter:
        _search_adapter.shutdown()
        _search_adapter = None
