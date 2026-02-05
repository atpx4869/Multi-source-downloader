# -*- coding: utf-8 -*-
"""
全新密码对话框 - 现代化设计，完全独立
"""

try:
    from PySide6 import QtCore, QtWidgets, QtGui
    PYSIDE_VER = 6
except ImportError:
    from PySide2 import QtCore, QtWidgets, QtGui
    PYSIDE_VER = 2


class ModernPasswordDialog(QtWidgets.QDialog):
    """现代化密码对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 无边框对话框
        self.setWindowFlags(QtCore.Qt.Dialog | QtCore.Qt.FramelessWindowHint)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        
        self.setFixedSize(400, 300)
        self.password = None
        
        self.setup_ui()
        self.center_on_screen()
    
    def setup_ui(self):
        """设置UI"""
        # 主布局
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # 背景容器
        container = QtWidgets.QFrame()
        container.setObjectName("container")
        container.setStyleSheet("""
            QFrame#container {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2d3748, stop:1 #1a202c);
                border: 2px solid #667eea;
                border-radius: 20px;
            }
        """)
        
        container_layout = QtWidgets.QVBoxLayout(container)
        container_layout.setContentsMargins(40, 40, 40, 40)
        container_layout.setSpacing(20)
        
        # 图标
        icon_label = QtWidgets.QLabel("🔒")
        icon_label.setAlignment(QtCore.Qt.AlignCenter)
        icon_label.setStyleSheet("""
            font-size: 48px;
            margin-bottom: 10px;
        """)
        container_layout.addWidget(icon_label)
        
        # 标题
        title = QtWidgets.QLabel("请输入密码")
        title.setAlignment(QtCore.Qt.AlignCenter)
        title.setStyleSheet("""
            font-size: 18px;
            font-weight: 700;
            color: #f7fafc;
            margin-bottom: 10px;
        """)
        container_layout.addWidget(title)
        
        # 密码输入框
        self.password_input = QtWidgets.QLineEdit()
        self.password_input.setEchoMode(QtWidgets.QLineEdit.Password)
        self.password_input.setPlaceholderText("输入密码...")
        self.password_input.setStyleSheet("""
            QLineEdit {
                background-color: #374151;
                border: 2px solid #4a5568;
                border-radius: 12px;
                padding: 14px 18px;
                font-size: 14px;
                color: #f7fafc;
                selection-background-color: #667eea;
            }
            QLineEdit:focus {
                border: 2px solid #667eea;
                background-color: #4a5568;
            }
        """)
        self.password_input.returnPressed.connect(self.on_submit)
        container_layout.addWidget(self.password_input)
        
        # 错误提示
        self.error_label = QtWidgets.QLabel("")
        self.error_label.setAlignment(QtCore.Qt.AlignCenter)
        self.error_label.setStyleSheet("""
            color: #f56565;
            font-size: 12px;
            min-height: 20px;
        """)
        self.error_label.hide()
        container_layout.addWidget(self.error_label)
        
        # 按钮
        btn_layout = QtWidgets.QHBoxLayout()
        btn_layout.setSpacing(12)
        
        # 取消按钮
        cancel_btn = QtWidgets.QPushButton("取消")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #e2e8f0;
                border: 2px solid #4a5568;
                border-radius: 10px;
                padding: 12px 24px;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #374151;
                border-color: #718096;
            }
        """)
        cancel_btn.setCursor(QtCore.Qt.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        # 确认按钮
        submit_btn = QtWidgets.QPushButton("确认")
        submit_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                color: white;
                border: none;
                border-radius: 10px;
                padding: 12px 24px;
                font-size: 13px;
                font-weight: 700;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #5a67d8, stop:1 #6b3fa0);
            }
        """)
        submit_btn.setCursor(QtCore.Qt.PointingHandCursor)
        submit_btn.clicked.connect(self.on_submit)
        btn_layout.addWidget(submit_btn)
        
        container_layout.addLayout(btn_layout)
        
        main_layout.addWidget(container)
        
        # 聚焦到输入框
        QtCore.QTimer.singleShot(100, self.password_input.setFocus)
    
    def center_on_screen(self):
        """居中显示"""
        if PYSIDE_VER == 6:
            screen = QtGui.QGuiApplication.primaryScreen().geometry()
        else:
            screen = QtWidgets.QApplication.desktop().screenGeometry()
        
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)
    
    def on_submit(self):
        """提交密码"""
        password = self.password_input.text().strip()
        
        if not password:
            self.show_error("请输入密码")
            self.shake_animation()
            return
        
        # 验证密码（这里使用简单验证，实际应该从配置读取）
        if password == "123456":  # 默认密码
            self.password = password
            self.accept()
        else:
            self.show_error("密码错误，请重试")
            self.shake_animation()
            self.password_input.clear()
            self.password_input.setFocus()
    
    def show_error(self, message):
        """显示错误信息"""
        self.error_label.setText(message)
        self.error_label.show()
        
        # 3秒后自动隐藏
        QtCore.QTimer.singleShot(3000, self.error_label.hide)
    
    def shake_animation(self):
        """抖动动画"""
        original_pos = self.pos()
        
        animation = QtCore.QSequentialAnimationGroup(self)
        
        for i in range(3):
            # 向右
            anim1 = QtCore.QPropertyAnimation(self, b"pos")
            anim1.setDuration(50)
            anim1.setEndValue(original_pos + QtCore.QPoint(10, 0))
            animation.addAnimation(anim1)
            
            # 向左
            anim2 = QtCore.QPropertyAnimation(self, b"pos")
            anim2.setDuration(50)
            anim2.setEndValue(original_pos - QtCore.QPoint(10, 0))
            animation.addAnimation(anim2)
        
        # 回到原位
        anim_final = QtCore.QPropertyAnimation(self, b"pos")
        anim_final.setDuration(50)
        anim_final.setEndValue(original_pos)
        animation.addAnimation(anim_final)
        
        animation.start(QtCore.QAbstractAnimation.DeleteWhenStopped)
    
    def showEvent(self, event):
        """显示事件 - 添加淡入动画"""
        super().showEvent(event)
        
        # 淡入动画
        self.setWindowOpacity(0)
        animation = QtCore.QPropertyAnimation(self, b"windowOpacity")
        animation.setDuration(300)
        animation.setStartValue(0)
        animation.setEndValue(1)
        animation.setEasingCurve(QtCore.QEasingCurve.OutCubic)
        animation.start(QtCore.QAbstractAnimation.DeleteWhenStopped)
    
    @staticmethod
    def get_password(parent=None):
        """静态方法获取密码"""
        dialog = ModernPasswordDialog(parent)
        result = dialog.exec()
        
        if result == QtWidgets.QDialog.Accepted:
            return dialog.password
        return None


# 测试代码
if __name__ == '__main__':
    import sys
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle('Fusion')
    
    password = ModernPasswordDialog.get_password()
    if password:
        print(f"密码验证成功: {password}")
    else:
        print("用户取消")
    
    sys.exit(0)
