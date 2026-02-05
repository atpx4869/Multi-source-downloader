# -*- coding: utf-8 -*-
"""
全新主窗口 - 现代化设计，完全独立
"""

try:
    from PySide6 import QtCore, QtWidgets, QtGui
except ImportError:
    from PySide2 import QtCore, QtWidgets, QtGui


class ModernMainWindow(QtWidgets.QMainWindow):
    """现代化主窗口"""
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("标准文献检索系统 V2")
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)
        
        # 设置样式
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1a202c;
            }
        """)
        
        self.setup_ui()
    
    def setup_ui(self):
        """设置UI"""
        # 中心部件
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QtWidgets.QVBoxLayout(central_widget)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(24)
        
        # 顶部标题栏
        header = self.create_header()
        main_layout.addWidget(header)
        
        # 搜索区域
        search_area = self.create_search_area()
        main_layout.addWidget(search_area)
        
        # 数据源选择
        source_area = self.create_source_area()
        main_layout.addWidget(source_area)
        
        # 分隔线
        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setStyleSheet("background-color: #4a5568; max-height: 1px;")
        main_layout.addWidget(line)
        
        # 结果区域
        results_area = self.create_results_area()
        main_layout.addWidget(results_area, 1)
        
        # 日志区域
        log_area = self.create_log_area()
        main_layout.addWidget(log_area)
        
        # 底部操作栏
        bottom_bar = self.create_bottom_bar()
        main_layout.addWidget(bottom_bar)
    
    def create_header(self):
        """创建顶部标题"""
        header = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(header)
        layout.setContentsMargins(0, 0, 0, 0)
        
        title = QtWidgets.QLabel("🔍 标准文献检索系统")
        title.setStyleSheet("""
            font-size: 28px;
            font-weight: 700;
            color: #f7fafc;
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #667eea, stop:1 #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        """)
        layout.addWidget(title)
        
        layout.addStretch()
        
        # 版本标签
        version = QtWidgets.QLabel("V2.0")
        version.setStyleSheet("""
            font-size: 12px;
            color: #a0aec0;
            background-color: #2d3748;
            padding: 4px 12px;
            border-radius: 12px;
        """)
        layout.addWidget(version)
        
        return header
    
    def create_search_area(self):
        """创建搜索区域"""
        search_widget = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(search_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        
        # 搜索输入框
        self.search_input = QtWidgets.QLineEdit()
        self.search_input.setPlaceholderText("🔍  输入标准号或关键词搜索... (例如: GB/T 3324)")
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #2d3748;
                border: 3px solid #667eea;
                border-radius: 16px;
                padding: 16px 24px;
                font-size: 15px;
                color: #f7fafc;
                selection-background-color: #667eea;
            }
            QLineEdit:focus {
                border: 3px solid #5a67d8;
                background-color: #374151;
            }
        """)
        layout.addWidget(self.search_input, 1)
        
        # 搜索按钮
        search_btn = QtWidgets.QPushButton("搜索")
        search_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                color: white;
                border: none;
                border-radius: 14px;
                padding: 16px 40px;
                font-weight: 700;
                font-size: 15px;
                letter-spacing: 1px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #5a67d8, stop:1 #6b3fa0);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4c51bf, stop:1 #5a3589);
            }
        """)
        search_btn.setCursor(QtCore.Qt.PointingHandCursor)
        search_btn.clicked.connect(self.on_search)
        layout.addWidget(search_btn)
        
        return search_widget
    
    def create_source_area(self):
        """创建数据源选择区域"""
        source_widget = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(source_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)
        
        # 标题
        title = QtWidgets.QLabel("数据源:")
        title.setStyleSheet("""
            font-size: 14px;
            color: #e2e8f0;
            font-weight: 600;
        """)
        layout.addWidget(title)
        
        # 数据源复选框
        self.source_checkboxes = {}
        sources = [("ZBY", "ZBY 数据源"), ("GBW", "GBW 数据源"), ("BY", "BY 数据源")]
        
        for source_id, source_name in sources:
            checkbox = QtWidgets.QCheckBox(source_name)
            checkbox.setChecked(True)
            checkbox.setStyleSheet("""
                QCheckBox {
                    color: #f7fafc;
                    spacing: 10px;
                    font-size: 14px;
                }
                QCheckBox::indicator {
                    width: 22px;
                    height: 22px;
                    border-radius: 6px;
                }
                QCheckBox::indicator:unchecked {
                    background-color: #2d3748;
                    border: 2px solid #4a5568;
                }
                QCheckBox::indicator:unchecked:hover {
                    border-color: #667eea;
                }
                QCheckBox::indicator:checked {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #667eea, stop:1 #764ba2);
                    border: 2px solid #667eea;
                }
            """)
            self.source_checkboxes[source_id] = checkbox
            layout.addWidget(checkbox)
        
        layout.addStretch()
        
        return source_widget
    
    def create_results_area(self):
        """创建结果区域"""
        # 滚动区域
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                border: none;
                background: #2d3748;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background: #667eea;
                border-radius: 6px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background: #5a67d8;
            }
        """)
        
        # 结果容器
        results_container = QtWidgets.QWidget()
        self.results_layout = QtWidgets.QVBoxLayout(results_container)
        self.results_layout.setSpacing(16)
        self.results_layout.setContentsMargins(0, 0, 0, 0)
        
        # 添加示例卡片
        self.add_demo_cards()
        
        self.results_layout.addStretch()
        
        scroll.setWidget(results_container)
        return scroll
    
    def add_demo_cards(self):
        """添加演示卡片"""
        demo_data = [
            {
                'std_no': 'GB/T 3324-2017',
                'name': '木家具通用技术条件',
                'publish': '2017-05-12',
                'status': '现行',
            },
            {
                'std_no': 'GB/T 28001-2011',
                'name': '职业健康安全管理体系 要求',
                'publish': '2011-12-30',
                'status': '废止',
            },
            {
                'std_no': 'GB 50016-2014',
                'name': '建筑设计防火规范',
                'publish': '2014-08-27',
                'status': '现行',
            },
        ]
        
        for data in demo_data:
            card = self.create_result_card(data)
            self.results_layout.addWidget(card)
    
    def create_result_card(self, data):
        """创建结果卡片"""
        card = QtWidgets.QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #2d3748;
                border-radius: 16px;
                border: 1px solid #4a5568;
                padding: 20px;
            }
            QFrame:hover {
                background-color: #374151;
                border: 1px solid #667eea;
            }
        """)
        
        layout = QtWidgets.QVBoxLayout(card)
        layout.setSpacing(12)
        
        # 标准号
        std_no = QtWidgets.QLabel(data['std_no'])
        std_no.setStyleSheet("""
            font-size: 18px;
            font-weight: 700;
            color: #f7fafc;
        """)
        layout.addWidget(std_no)
        
        # 标准名称
        name = QtWidgets.QLabel(data['name'])
        name.setWordWrap(True)
        name.setStyleSheet("""
            font-size: 14px;
            color: #e2e8f0;
        """)
        layout.addWidget(name)
        
        # 信息行
        info_layout = QtWidgets.QHBoxLayout()
        
        # 发布日期
        date_label = QtWidgets.QLabel(f"📅 {data['publish']}")
        date_label.setStyleSheet("font-size: 12px; color: #a0aec0;")
        info_layout.addWidget(date_label)
        
        # 状态
        status_color = "#48bb78" if data['status'] == "现行" else "#f56565"
        status_label = QtWidgets.QLabel(f"● {data['status']}")
        status_label.setStyleSheet(f"font-size: 12px; color: {status_color}; font-weight: 600;")
        info_layout.addWidget(status_label)
        
        info_layout.addStretch()
        
        # 下载按钮
        download_btn = QtWidgets.QPushButton("下载")
        download_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                color: white;
                border: none;
                border-radius: 10px;
                padding: 8px 24px;
                font-weight: 600;
                font-size: 13px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #5a67d8, stop:1 #6b3fa0);
            }
        """)
        download_btn.setCursor(QtCore.Qt.PointingHandCursor)
        download_btn.clicked.connect(lambda: self.on_download(data))
        info_layout.addWidget(download_btn)
        
        layout.addLayout(info_layout)
        
        return card
    
    def create_log_area(self):
        """创建日志区域"""
        log_widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(log_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # 标题
        title = QtWidgets.QLabel("📜 实时日志")
        title.setStyleSheet("""
            font-size: 15px;
            color: #e2e8f0;
            font-weight: 600;
        """)
        layout.addWidget(title)
        
        # 日志文本框
        self.log_viewer = QtWidgets.QTextEdit()
        self.log_viewer.setReadOnly(True)
        self.log_viewer.setMaximumHeight(150)
        self.log_viewer.setStyleSheet("""
            QTextEdit {
                background-color: #171923;
                color: #e2e8f0;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 11px;
                padding: 12px;
                border: 1px solid #4a5568;
                border-radius: 10px;
            }
        """)
        layout.addWidget(self.log_viewer)
        
        # 添加欢迎日志
        self.append_log("✨ 欢迎使用标准文献检索系统 V2", 'success')
        self.append_log("💡 全新设计，更加现代化的界面", 'info')
        
        return log_widget
    
    def create_bottom_bar(self):
        """创建底部操作栏"""
        bottom = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(bottom)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        
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
                    border-radius: 10px;
                    padding: 12px 24px;
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
            layout.addWidget(btn)
        
        layout.addStretch()
        
        return bottom
    
    def append_log(self, message, level='info'):
        """添加日志"""
        colors = {
            'info': '#4299e1',
            'success': '#48bb78',
            'warning': '#ed8936',
            'error': '#f56565',
        }
        color = colors.get(level, '#e2e8f0')
        
        html = f'<span style="color: {color};">{message}</span>'
        self.log_viewer.append(html)
        
        # 自动滚动到底部
        scrollbar = self.log_viewer.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def on_search(self):
        """搜索"""
        keyword = self.search_input.text().strip()
        if keyword:
            self.append_log(f"🔍 开始搜索: {keyword}", 'info')
            # TODO: 实际搜索逻辑
        else:
            self.append_log("⚠️  请输入搜索关键词", 'warning')
    
    def on_download(self, data):
        """下载"""
        self.append_log(f"📥 开始下载: {data['std_no']}", 'info')
        # TODO: 实际下载逻辑
    
    def on_batch_download(self):
        """批量下载"""
        self.append_log("📦 批量下载功能", 'info')
    
    def on_export(self):
        """导出"""
        self.append_log("📤 导出Excel功能", 'info')
    
    def on_history(self):
        """历史"""
        self.append_log("📜 历史记录功能", 'info')
    
    def on_settings(self):
        """设置"""
        self.append_log("⚙️  设置功能", 'info')
    
    def showEvent(self, event):
        """显示事件 - 添加淡入动画"""
        super().showEvent(event)
        
        # 淡入动画
        self.setWindowOpacity(0)
        animation = QtCore.QPropertyAnimation(self, b"windowOpacity")
        animation.setDuration(400)
        animation.setStartValue(0)
        animation.setEndValue(1)
        animation.setEasingCurve(QtCore.QEasingCurve.OutCubic)
        animation.start(QtCore.QAbstractAnimation.DeleteWhenStopped)
