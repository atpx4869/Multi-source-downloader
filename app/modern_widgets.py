# -*- coding: utf-8 -*-
"""
现代化UI组件库
提供卡片、搜索栏、浮动按钮等现代化组件
"""

try:
    from PySide6 import QtCore, QtWidgets, QtGui
except ImportError:
    from PySide2 import QtCore, QtWidgets, QtGui


class ModernCard(QtWidgets.QFrame):
    """现代化卡片组件 - 带圆角、阴影、悬停效果"""
    
    clicked = QtCore.Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.setCursor(QtCore.Qt.PointingHandCursor)
        
        # 设置样式
        self.setStyleSheet("""
            ModernCard {
                background-color: #2d3748;
                border-radius: 16px;
                border: 1px solid #4a5568;
                padding: 16px;
            }
            ModernCard:hover {
                background-color: #374151;
                border: 1px solid #667eea;
            }
        """)
        
        # 主布局
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.setContentsMargins(16, 16, 16, 16)
        self.main_layout.setSpacing(12)
    
    def mousePressEvent(self, event):
        """点击事件"""
        if event.button() == QtCore.Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)
    
    def add_widget(self, widget):
        """添加组件到卡片"""
        self.main_layout.addWidget(widget)


class ResultCard(ModernCard):
    """搜索结果卡片 - 显示标准信息"""
    
    download_clicked = QtCore.Signal(object)  # 发送Standard对象
    
    def __init__(self, standard_data, parent=None):
        super().__init__(parent)
        self.standard_data = standard_data
        self.setup_ui()
    
    def setup_ui(self):
        """设置UI"""
        # 标准号 - 大标题
        title_label = QtWidgets.QLabel(self.standard_data.get('std_no', '未知'))
        title_label.setStyleSheet("""
            font-size: 16px;
            font-weight: 700;
            color: #f7fafc;
            margin-bottom: 4px;
        """)
        self.add_widget(title_label)
        
        # 标准名称
        name_label = QtWidgets.QLabel(self.standard_data.get('name', ''))
        name_label.setWordWrap(True)
        name_label.setStyleSheet("""
            font-size: 13px;
            color: #e2e8f0;
            margin-bottom: 8px;
        """)
        self.add_widget(name_label)
        
        # 信息行
        info_layout = QtWidgets.QHBoxLayout()
        
        # 发布日期
        if self.standard_data.get('publish'):
            date_label = QtWidgets.QLabel(f"📅 {self.standard_data['publish']}")
            date_label.setStyleSheet("font-size: 11px; color: #a0aec0;")
            info_layout.addWidget(date_label)
        
        # 状态
        if self.standard_data.get('status'):
            status = self.standard_data['status']
            status_color = "#48bb78" if status == "现行" else "#f56565"
            status_label = QtWidgets.QLabel(f"● {status}")
            status_label.setStyleSheet(f"font-size: 11px; color: {status_color}; font-weight: 600;")
            info_layout.addWidget(status_label)
        
        info_layout.addStretch()
        self.main_layout.addLayout(info_layout)
        
        # 数据源标签
        if self.standard_data.get('sources'):
            sources_text = "📥 " + ", ".join(self.standard_data['sources'])
            sources_label = QtWidgets.QLabel(sources_text)
            sources_label.setStyleSheet("""
                font-size: 10px;
                color: #718096;
                background-color: #1a202c;
                padding: 4px 8px;
                border-radius: 4px;
            """)
            self.add_widget(sources_label)
        
        # 下载按钮
        download_btn = QtWidgets.QPushButton("下载")
        download_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 20px;
                font-weight: 600;
                font-size: 12px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #5a67d8, stop:1 #6b3fa0);
            }
        """)
        download_btn.setCursor(QtCore.Qt.PointingHandCursor)
        download_btn.clicked.connect(lambda: self.download_clicked.emit(self.standard_data))
        self.add_widget(download_btn)


class ModernSearchBar(QtWidgets.QWidget):
    """现代化搜索栏 - 大号圆角，带图标"""
    
    search_triggered = QtCore.Signal(str)  # 发送搜索关键词
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """设置UI"""
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        
        # 搜索输入框
        self.search_input = QtWidgets.QLineEdit()
        self.search_input.setPlaceholderText("🔍  输入标准号或关键词搜索...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #2d3748;
                border: 2px solid #667eea;
                border-radius: 14px;
                padding: 14px 20px;
                font-size: 14px;
                color: #f7fafc;
                selection-background-color: #667eea;
            }
            QLineEdit:focus {
                border: 2px solid #5a67d8;
                background-color: #374151;
            }
        """)
        self.search_input.returnPressed.connect(self.on_search)
        layout.addWidget(self.search_input, 1)
        
        # 搜索按钮
        self.search_btn = QtWidgets.QPushButton("搜索")
        self.search_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                color: white;
                border: none;
                border-radius: 12px;
                padding: 14px 32px;
                font-weight: 700;
                font-size: 14px;
                letter-spacing: 0.5px;
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
        self.search_btn.setCursor(QtCore.Qt.PointingHandCursor)
        self.search_btn.clicked.connect(self.on_search)
        layout.addWidget(self.search_btn)
    
    def on_search(self):
        """触发搜索"""
        keyword = self.search_input.text().strip()
        if keyword:
            self.search_triggered.emit(keyword)
    
    def get_keyword(self):
        """获取搜索关键词"""
        return self.search_input.text().strip()
    
    def clear(self):
        """清空搜索框"""
        self.search_input.clear()


class FloatingActionButton(QtWidgets.QPushButton):
    """浮动操作按钮 - 圆形，带阴影"""
    
    def __init__(self, icon_text="", parent=None):
        super().__init__(icon_text, parent)
        self.setFixedSize(56, 56)
        self.setCursor(QtCore.Qt.PointingHandCursor)
        
        self.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                color: white;
                border: none;
                border-radius: 28px;
                font-size: 20px;
                font-weight: bold;
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


class SourceSelector(QtWidgets.QWidget):
    """数据源选择器 - 复选框组"""
    
    sources_changed = QtCore.Signal(list)  # 发送选中的源列表
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.checkboxes = {}
        self.setup_ui()
    
    def setup_ui(self):
        """设置UI"""
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        
        # 标题
        title = QtWidgets.QLabel("数据源选择:")
        title.setStyleSheet("font-size: 13px; color: #e2e8f0; font-weight: 600;")
        layout.addWidget(title)
        
        # 数据源复选框
        sources = [
            ("ZBY", "ZBY 数据源", True),
            ("GBW", "GBW 数据源", True),
            ("BY", "BY 数据源", True),
        ]
        
        for source_id, source_name, checked in sources:
            checkbox = QtWidgets.QCheckBox(source_name)
            checkbox.setChecked(checked)
            checkbox.setStyleSheet("""
                QCheckBox {
                    color: #f7fafc;
                    spacing: 8px;
                    font-size: 13px;
                }
                QCheckBox::indicator {
                    width: 20px;
                    height: 20px;
                    border-radius: 4px;
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
            checkbox.stateChanged.connect(self.on_source_changed)
            self.checkboxes[source_id] = checkbox
            layout.addWidget(checkbox)
        
        layout.addStretch()
    
    def on_source_changed(self):
        """源选择变化"""
        selected = [
            source_id for source_id, checkbox in self.checkboxes.items()
            if checkbox.isChecked()
        ]
        self.sources_changed.emit(selected)
    
    def get_selected_sources(self):
        """获取选中的源"""
        return [
            source_id for source_id, checkbox in self.checkboxes.items()
            if checkbox.isChecked()
        ]


class ModernLogViewer(QtWidgets.QTextEdit):
    """现代化日志查看器"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setStyleSheet("""
            QTextEdit {
                background-color: #171923;
                color: #e2e8f0;
                font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
                font-size: 11px;
                padding: 12px;
                border: 1px solid #4a5568;
                border-radius: 8px;
                line-height: 1.6;
            }
        """)
    
    def append_log(self, message, level='info'):
        """添加日志，带颜色"""
        colors = {
            'info': '#4299e1',
            'success': '#48bb78',
            'warning': '#ed8936',
            'error': '#f56565',
        }
        color = colors.get(level, '#e2e8f0')
        
        html = f'<span style="color: {color};">{message}</span>'
        self.append(html)
        
        # 自动滚动到底部
        scrollbar = self.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())


class StatusBadge(QtWidgets.QLabel):
    """状态徽章 - 小圆点+文字"""
    
    def __init__(self, text="", status='info', parent=None):
        super().__init__(text, parent)
        self.set_status(status)
    
    def set_status(self, status):
        """设置状态"""
        colors = {
            'success': '#48bb78',
            'error': '#f56565',
            'warning': '#ed8936',
            'info': '#4299e1',
        }
        color = colors.get(status, '#a0aec0')
        
        self.setStyleSheet(f"""
            QLabel {{
                color: {color};
                font-size: 11px;
                font-weight: 600;
                padding: 4px 10px;
                background-color: rgba({int(color[1:3], 16)}, {int(color[3:5], 16)}, {int(color[5:7], 16)}, 0.1);
                border-radius: 12px;
            }}
        """)
