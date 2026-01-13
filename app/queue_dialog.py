# -*- coding: utf-8 -*-
"""
下载队列管理界面
"""
import os
from pathlib import Path
from datetime import datetime

try:
    from PySide6 import QtCore, QtWidgets, QtGui
    PYSIDE_VER = 6
except ImportError:
    from PySide2 import QtCore, QtWidgets, QtGui
    PYSIDE_VER = 2

from core.download_queue import get_queue_manager, DownloadTask, TaskStatus
import ui_styles


class QueueDialog(QtWidgets.QDialog):
    """下载队列管理对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.queue_manager = get_queue_manager()
        
        self.setWindowTitle("📥 下载队列管理")
        self.setMinimumSize(900, 600)
        self.setStyleSheet(ui_styles.DIALOG_STYLE)
        
        # 定时刷新
        self.refresh_timer = QtCore.QTimer()
        self.refresh_timer.timeout.connect(self.refresh_task_list)
        self.refresh_timer.start(1000)  # 每秒刷新
        
        self.setup_ui()
        self.refresh_task_list()
    
    def setup_ui(self):
        """构建界面"""
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 标题栏
        title = QtWidgets.QLabel("📥 下载队列管理")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #333;")
        layout.addWidget(title)
        
        # 工具栏
        toolbar = self.create_toolbar()
        layout.addLayout(toolbar)
        
        # 任务列表
        self.task_table = QtWidgets.QTableWidget()
        self.task_table.setColumnCount(8)
        self.task_table.setHorizontalHeaderLabels([
            "标准号", "标准名称", "状态", "优先级", "来源", "重试", "创建时间", "操作"
        ])
        
        # 设置列宽
        self.task_table.setColumnWidth(0, 120)
        self.task_table.setColumnWidth(1, 250)
        self.task_table.setColumnWidth(2, 80)
        self.task_table.setColumnWidth(3, 60)
        self.task_table.setColumnWidth(4, 60)
        self.task_table.setColumnWidth(5, 60)
        self.task_table.setColumnWidth(6, 140)
        self.task_table.setColumnWidth(7, 120)
        
        self.task_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.task_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.task_table.setAlternatingRowColors(True)
        self.task_table.verticalHeader().setVisible(False)
        
        layout.addWidget(self.task_table)
        
        # 统计信息栏
        self.stats_label = QtWidgets.QLabel()
        self.stats_label.setStyleSheet("""
            QLabel {
                background-color: #f8f9fa;
                padding: 10px;
                border-radius: 5px;
                font-size: 13px;
                color: #666;
            }
        """)
        layout.addWidget(self.stats_label)
        
        # 底部按钮
        btn_layout = QtWidgets.QHBoxLayout()
        btn_layout.addStretch()
        
        close_btn = QtWidgets.QPushButton("关闭")
        close_btn.setFixedWidth(100)
        close_btn.setStyleSheet(ui_styles.BTN_SECONDARY_STYLE)
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        
        layout.addLayout(btn_layout)
    
    def create_toolbar(self) -> QtWidgets.QHBoxLayout:
        """创建工具栏"""
        toolbar = QtWidgets.QHBoxLayout()
        
        # 暂停全部
        pause_all_btn = QtWidgets.QPushButton("⏸ 暂停全部")
        pause_all_btn.clicked.connect(self.pause_all_tasks)
        toolbar.addWidget(pause_all_btn)
        
        # 继续全部
        resume_all_btn = QtWidgets.QPushButton("▶ 继续全部")
        resume_all_btn.clicked.connect(self.resume_all_tasks)
        toolbar.addWidget(resume_all_btn)
        
        # 重试失败
        retry_failed_btn = QtWidgets.QPushButton("🔄 重试失败")
        retry_failed_btn.clicked.connect(self.retry_all_failed)
        toolbar.addWidget(retry_failed_btn)
        
        # 清空完成
        clear_completed_btn = QtWidgets.QPushButton("🗑 清空完成")
        clear_completed_btn.clicked.connect(self.clear_completed_tasks)
        toolbar.addWidget(clear_completed_btn)
        
        toolbar.addStretch()
        
        # 刷新按钮
        refresh_btn = QtWidgets.QPushButton("🔄 刷新")
        refresh_btn.clicked.connect(self.refresh_task_list)
        toolbar.addWidget(refresh_btn)
        
        # 应用统一样式
        for i in range(toolbar.count()):
            widget = toolbar.itemAt(i).widget()
            if isinstance(widget, QtWidgets.QPushButton):
                widget.setStyleSheet(ui_styles.BTN_SECONDARY_STYLE)
                widget.setFixedHeight(32)
                widget.setCursor(QtCore.Qt.PointingHandCursor)
        
        return toolbar
    
    def refresh_task_list(self):
        """刷新任务列表"""
        tasks = self.queue_manager.get_all_tasks()
        
        self.task_table.setRowCount(0)
        
        for task in tasks:
            row = self.task_table.rowCount()
            self.task_table.insertRow(row)
            
            # 标准号
            self.task_table.setItem(row, 0, QtWidgets.QTableWidgetItem(task.std_no))
            
            # 标准名称
            name_item = QtWidgets.QTableWidgetItem(task.std_name or "")
            name_item.setToolTip(task.std_name or "")
            self.task_table.setItem(row, 1, name_item)
            
            # 状态（带颜色）
            status_item = self.create_status_item(task.status)
            self.task_table.setItem(row, 2, status_item)
            
            # 优先级
            priority_item = QtWidgets.QTableWidgetItem(str(task.priority))
            priority_item.setTextAlignment(QtCore.Qt.AlignCenter)
            self.task_table.setItem(row, 3, priority_item)
            
            # 来源
            self.task_table.setItem(row, 4, QtWidgets.QTableWidgetItem(task.source))
            
            # 重试次数
            retry_text = f"{task.retry_count}/{task.max_retries}"
            retry_item = QtWidgets.QTableWidgetItem(retry_text)
            retry_item.setTextAlignment(QtCore.Qt.AlignCenter)
            self.task_table.setItem(row, 5, retry_item)
            
            # 创建时间
            try:
                create_time = datetime.fromisoformat(task.created_time)
                time_str = create_time.strftime("%m-%d %H:%M:%S")
            except:
                time_str = task.created_time[:16] if task.created_time else ""
            self.task_table.setItem(row, 6, QtWidgets.QTableWidgetItem(time_str))
            
            # 操作按钮
            action_widget = self.create_action_buttons(task)
            self.task_table.setCellWidget(row, 7, action_widget)
        
        # 更新统计信息
        self.update_statistics()
    
    def create_status_item(self, status: str) -> QtWidgets.QTableWidgetItem:
        """创建带颜色的状态项"""
        status_map = {
            TaskStatus.PENDING.value: ("等待", "#FFA500"),
            TaskStatus.RUNNING.value: ("运行中", "#007BFF"),
            TaskStatus.PAUSED.value: ("已暂停", "#6C757D"),
            TaskStatus.COMPLETED.value: ("完成", "#28A745"),
            TaskStatus.FAILED.value: ("失败", "#DC3545"),
            TaskStatus.CANCELLED.value: ("已取消", "#6C757D"),
        }
        
        text, color = status_map.get(status, (status, "#000"))
        item = QtWidgets.QTableWidgetItem(text)
        item.setForeground(QtGui.QColor(color))
        item.setTextAlignment(QtCore.Qt.AlignCenter)
        
        font = item.font()
        font.setBold(True)
        item.setFont(font)
        
        return item
    
    def create_action_buttons(self, task: DownloadTask) -> QtWidgets.QWidget:
        """创建操作按钮"""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(widget)
        layout.setContentsMargins(5, 2, 5, 2)
        layout.setSpacing(5)
        
        status = task.status
        
        if status == TaskStatus.PENDING.value or status == TaskStatus.RUNNING.value:
            # 暂停按钮
            pause_btn = QtWidgets.QPushButton("⏸")
            pause_btn.setFixedSize(30, 26)
            pause_btn.setToolTip("暂停")
            pause_btn.clicked.connect(lambda: self.pause_task(task.task_id))
            layout.addWidget(pause_btn)
        
        elif status == TaskStatus.PAUSED.value:
            # 继续按钮
            resume_btn = QtWidgets.QPushButton("▶")
            resume_btn.setFixedSize(30, 26)
            resume_btn.setToolTip("继续")
            resume_btn.clicked.connect(lambda: self.resume_task(task.task_id))
            layout.addWidget(resume_btn)
        
        elif status == TaskStatus.FAILED.value:
            # 重试按钮
            retry_btn = QtWidgets.QPushButton("🔄")
            retry_btn.setFixedSize(30, 26)
            retry_btn.setToolTip("重试")
            retry_btn.clicked.connect(lambda: self.retry_task(task.task_id))
            layout.addWidget(retry_btn)
        
        elif status == TaskStatus.COMPLETED.value:
            # 打开文件按钮
            if task.file_path and Path(task.file_path).exists():
                open_btn = QtWidgets.QPushButton("📄")
                open_btn.setFixedSize(30, 26)
                open_btn.setToolTip("打开文件")
                open_btn.clicked.connect(lambda: self.open_file(task.file_path))
                layout.addWidget(open_btn)
        
        # 取消/删除按钮（所有状态都有）
        delete_btn = QtWidgets.QPushButton("❌")
        delete_btn.setFixedSize(30, 26)
        delete_btn.setToolTip("删除")
        delete_btn.clicked.connect(lambda: self.delete_task(task.task_id))
        layout.addWidget(delete_btn)
        
        layout.addStretch()
        
        # 应用样式
        for i in range(layout.count()):
            item = layout.itemAt(i)
            if item and item.widget() and isinstance(item.widget(), QtWidgets.QPushButton):
                item.widget().setStyleSheet("""
                    QPushButton {
                        background-color: #f8f9fa;
                        border: 1px solid #dee2e6;
                        border-radius: 3px;
                        font-size: 12px;
                    }
                    QPushButton:hover {
                        background-color: #e9ecef;
                    }
                """)
                item.widget().setCursor(QtCore.Qt.PointingHandCursor)
        
        return widget
    
    def pause_task(self, task_id: str):
        """暂停任务"""
        if self.queue_manager.pause_task(task_id):
            self.refresh_task_list()
    
    def resume_task(self, task_id: str):
        """继续任务"""
        if self.queue_manager.resume_task(task_id):
            self.refresh_task_list()
    
    def retry_task(self, task_id: str):
        """重试任务"""
        if self.queue_manager.retry_task(task_id):
            self.refresh_task_list()
    
    def delete_task(self, task_id: str):
        """删除任务"""
        reply = QtWidgets.QMessageBox.question(
            self, "确认删除", "确定要删除这个任务吗？",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )
        if reply == QtWidgets.QMessageBox.Yes:
            self.queue_manager.delete_task(task_id)
            self.refresh_task_list()
    
    def open_file(self, file_path: str):
        """打开文件"""
        try:
            os.startfile(file_path)
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "错误", f"无法打开文件:\n{e}")
    
    def pause_all_tasks(self):
        """暂停所有任务"""
        tasks = self.queue_manager.get_all_tasks()
        count = 0
        for task in tasks:
            if task.status in [TaskStatus.PENDING.value, TaskStatus.RUNNING.value]:
                if self.queue_manager.pause_task(task.task_id):
                    count += 1
        self.refresh_task_list()
        QtWidgets.QMessageBox.information(self, "完成", f"已暂停 {count} 个任务")
    
    def resume_all_tasks(self):
        """继续所有任务"""
        tasks = self.queue_manager.get_all_tasks()
        count = 0
        for task in tasks:
            if task.status == TaskStatus.PAUSED.value:
                if self.queue_manager.resume_task(task.task_id):
                    count += 1
        self.refresh_task_list()
        QtWidgets.QMessageBox.information(self, "完成", f"已恢复 {count} 个任务")
    
    def retry_all_failed(self):
        """重试所有失败任务"""
        count = self.queue_manager.retry_all_failed()
        self.refresh_task_list()
        QtWidgets.QMessageBox.information(self, "完成", f"已重试 {count} 个失败任务")
    
    def clear_completed_tasks(self):
        """清空已完成任务"""
        reply = QtWidgets.QMessageBox.question(
            self, "确认清空", "确定要清空所有已完成的任务吗？",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )
        if reply == QtWidgets.QMessageBox.Yes:
            self.queue_manager.clear_completed()
            self.refresh_task_list()
    
    def update_statistics(self):
        """更新统计信息"""
        stats = self.queue_manager.get_statistics()
        
        total = stats.get('total', 0)
        pending = stats.get('pending', 0)
        running = stats.get('running', 0)
        paused = stats.get('paused', 0)
        completed = stats.get('completed', 0)
        failed = stats.get('failed', 0)
        active_workers = stats.get('active_workers', 0)
        
        text = (
            f"📊 统计：总任务 {total} | "
            f"运行中 {running} | 等待 {pending} | 暂停 {paused} | "
            f"完成 {completed} | 失败 {failed} | "
            f"Worker {active_workers}/{self.queue_manager.max_workers}"
        )
        
        self.stats_label.setText(text)
    
    def closeEvent(self, event):
        """关闭事件"""
        self.refresh_timer.stop()
        super().closeEvent(event)
