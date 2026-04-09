# -*- coding: utf-8 -*-
"""
现代化UI演示程序
展示所有现代化组件的使用方法
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from PySide6 import QtCore, QtWidgets, QtGui
except ImportError:
    from PySide2 import QtCore, QtWidgets

from app.modern_widgets import (
    ResultCard, ModernSearchBar, 
    SourceSelector, ModernLogViewer
)
from app.animations import AnimationManager


class ModernUIDemo(QtWidgets.QMainWindow):
    """现代化UI演示窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("现代化UI演示 - 标准文献检索系统")
        self.setMinimumSize(1000, 700)
        self.resize(1200, 800)  # 设置初始大小
        
        # 设置深色背景
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1a202c;
            }
        """)
        
        self.setup_ui()
    
    def setup_ui(self):
        """设置UI"""
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QtWidgets.QVBoxLayout(central_widget)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(20)
        
        # 顶部标题
        title = QtWidgets.QLabel("🔍 标准文献检索系统")
        title.setStyleSheet("""
            font-size: 24px;
            font-weight: 700;
            color: #f7fafc;
            margin-bottom: 10px;
        """)
        main_layout.addWidget(title)
        
        # 搜索栏
        self.search_bar = ModernSearchBar()
        self.search_bar.search_triggered.connect(self.on_search)
        main_layout.addWidget(self.search_bar)
        
        # 数据源选择
        self.source_selector = SourceSelector()
        self.source_selector.sources_changed.connect(self.on_sources_changed)
        main_layout.addWidget(self.source_selector)
        
        # 分隔线
        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setStyleSheet("background-color: #4a5568; max-height: 1px;")
        main_layout.addWidget(line)
        
        # 结果区域（滚动）
        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)
        
        scroll_content = QtWidgets.QWidget()
        self.results_layout = QtWidgets.QVBoxLayout(scroll_content)
        self.results_layout.setSpacing(16)
        self.results_layout.setContentsMargins(0, 0, 0, 0)
        
        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area, 1)
        
        # 日志区域
        log_label = QtWidgets.QLabel("📜 实时日志")
        log_label.setStyleSheet("font-size: 14px; color: #e2e8f0; font-weight: 600;")
        main_layout.addWidget(log_label)
        
        self.log_viewer = ModernLogViewer()
        self.log_viewer.setMaximumHeight(150)
        main_layout.addWidget(self.log_viewer)
        
        # 底部操作栏
        bottom_bar = QtWidgets.QWidget()
        bottom_layout = QtWidgets.QHBoxLayout(bottom_bar)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.setSpacing(12)
        
        # 操作按钮
        buttons = [
            ("批量下载", self.on_batch_download),
            ("导出Excel", self.on_export),
            ("历史记录", self.on_history),
            ("设置", self.on_settings),
        ]
        
        for btn_text, callback in buttons:
            btn = QtWidgets.QPushButton(btn_text)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: #e2e8f0;
                    border: 2px solid #4a5568;
                    border-radius: 8px;
                    padding: 10px 20px;
                    font-size: 13px;
                    font-weight: 500;
                }
                QPushButton:hover {
                    background-color: #374151;
                    border-color: #718096;
                    color: #f7fafc;
                }
            """)
            btn.setCursor(QtCore.Qt.PointingHandCursor)
            btn.clicked.connect(callback)
            bottom_layout.addWidget(btn)
        
        bottom_layout.addStretch()
        main_layout.addWidget(bottom_bar)
        
        # 添加示例数据
        self.add_demo_results()
        
        # 欢迎日志
        self.log_viewer.append_log("✨ 欢迎使用现代化UI演示", 'success')
        self.log_viewer.append_log("💡 这是一个全新设计的界面原型", 'info')
    
    def add_demo_results(self):
        """添加演示结果"""
        demo_data = [
            {
                'std_no': 'GB/T 3324-2017',
                'name': '木家具通用技术条件',
                'publish': '2017-05-12',
                'status': '现行',
                'sources': ['ZBY', 'GBW'],
            },
            {
                'std_no': 'GB/T 28001-2011',
                'name': '职业健康安全管理体系 要求',
                'publish': '2011-12-30',
                'status': '废止',
                'sources': ['BY'],
            },
            {
                'std_no': 'GB 50016-2014',
                'name': '建筑设计防火规范',
                'publish': '2014-08-27',
                'status': '现行',
                'sources': ['ZBY', 'GBW', 'BY'],
            },
        ]
        
        for data in demo_data:
            card = ResultCard(data)
            card.download_clicked.connect(self.on_download)
            self.results_layout.addWidget(card)
            
            # 添加淡入动画
            AnimationManager.fade_in(card, duration=300)
        
        self.results_layout.addStretch()
    
    def on_search(self, keyword):
        """搜索"""
        self.log_viewer.append_log(f"🔍 开始搜索: {keyword}", 'info')
        self.log_viewer.append_log(f"📡 使用数据源: {', '.join(self.source_selector.get_selected_sources())}", 'info')
        
        # 模拟搜索
        QtCore.QTimer.singleShot(1000, lambda: self.log_viewer.append_log("✅ 找到 3 条结果", 'success'))
    
    def on_sources_changed(self, sources):
        """数据源变化"""
        self.log_viewer.append_log(f"⚙️  数据源已更新: {', '.join(sources)}", 'info')
    
    def on_download(self, data):
        """下载"""
        self.log_viewer.append_log(f"📥 开始下载: {data.get('std_no')}", 'info')
        QtCore.QTimer.singleShot(1500, lambda: self.log_viewer.append_log("✅ 下载完成", 'success'))
    
    def on_batch_download(self):
        """批量下载"""
        self.log_viewer.append_log("📦 批量下载功能", 'info')
    
    def on_export(self):
        """导出"""
        self.log_viewer.append_log("📤 导出Excel功能", 'info')
    
    def on_history(self):
        """历史"""
        self.log_viewer.append_log("📜 历史记录功能", 'info')
    
    def on_settings(self):
        """设置"""
        self.log_viewer.append_log("⚙️  设置功能", 'info')


def main():
    """主函数"""
    app = QtWidgets.QApplication(sys.argv)
    
    # 设置应用样式
    app.setStyle('Fusion')
    
    window = ModernUIDemo()
    
    # 显示窗口
    window.show()
    
    # 确保窗口在最前面并激活
    window.raise_()
    window.activateWindow()
    
    # 淡入动画
    AnimationManager.fade_in(window, duration=400)
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
