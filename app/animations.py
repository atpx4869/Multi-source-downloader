# -*- coding: utf-8 -*-
"""
动画系统 - 为UI组件提供流畅的动画效果
"""

try:
    from PySide6 import QtCore, QtWidgets
except ImportError:
    from PySide2 import QtCore, QtWidgets


class AnimationManager:
    """动画管理器 - 提供各种常用动画效果"""
    
    @staticmethod
    def fade_in(widget, duration=300, on_finished=None):
        """淡入动画"""
        animation = QtCore.QPropertyAnimation(widget, b"windowOpacity")
        animation.setDuration(duration)
        animation.setStartValue(0.0)
        animation.setEndValue(1.0)
        animation.setEasingCurve(QtCore.QEasingCurve.OutCubic)
        if on_finished:
            animation.finished.connect(on_finished)
        animation.start(QtCore.QAbstractAnimation.DeleteWhenStopped)
        return animation
    
    @staticmethod
    def fade_out(widget, duration=300, on_finished=None):
        """淡出动画"""
        animation = QtCore.QPropertyAnimation(widget, b"windowOpacity")
        animation.setDuration(duration)
        animation.setStartValue(1.0)
        animation.setEndValue(0.0)
        animation.setEasingCurve(QtCore.QEasingCurve.InCubic)
        if on_finished:
            animation.finished.connect(on_finished)
        animation.start(QtCore.QAbstractAnimation.DeleteWhenStopped)
        return animation
    
    @staticmethod
    def slide_in(widget, direction='left', duration=400, distance=50):
        """滑入动画
        
        Args:
            direction: 'left', 'right', 'top', 'bottom'
        """
        current_pos = widget.pos()
        
        if direction == 'left':
            start_pos = QtCore.QPoint(current_pos.x() - distance, current_pos.y())
        elif direction == 'right':
            start_pos = QtCore.QPoint(current_pos.x() + distance, current_pos.y())
        elif direction == 'top':
            start_pos = QtCore.QPoint(current_pos.x(), current_pos.y() - distance)
        else:  # bottom
            start_pos = QtCore.QPoint(current_pos.x(), current_pos.y() + distance)
        
        widget.move(start_pos)
        
        animation = QtCore.QPropertyAnimation(widget, b"pos")
        animation.setDuration(duration)
        animation.setStartValue(start_pos)
        animation.setEndValue(current_pos)
        animation.setEasingCurve(QtCore.QEasingCurve.OutQuart)
        animation.start(QtCore.QAbstractAnimation.DeleteWhenStopped)
        return animation
    
    @staticmethod
    def shake(widget, intensity=10, duration=500):
        """抖动动画 - 用于错误提示"""
        original_pos = widget.pos()
        
        animation = QtCore.QSequentialAnimationGroup()
        
        # 创建多个小幅度移动
        for i in range(4):
            # 向右
            anim1 = QtCore.QPropertyAnimation(widget, b"pos")
            anim1.setDuration(duration // 8)
            anim1.setEndValue(original_pos + QtCore.QPoint(intensity, 0))
            animation.addAnimation(anim1)
            
            # 向左
            anim2 = QtCore.QPropertyAnimation(widget, b"pos")
            anim2.setDuration(duration // 8)
            anim2.setEndValue(original_pos - QtCore.QPoint(intensity, 0))
            animation.addAnimation(anim2)
            
            intensity = int(intensity * 0.7)  # 逐渐减弱
        
        # 回到原位
        anim_final = QtCore.QPropertyAnimation(widget, b"pos")
        anim_final.setDuration(duration // 8)
        anim_final.setEndValue(original_pos)
        animation.addAnimation(anim_final)
        
        animation.start(QtCore.QAbstractAnimation.DeleteWhenStopped)
        return animation
    
    @staticmethod
    def bounce(widget, height=20, duration=600):
        """弹跳动画"""
        original_pos = widget.pos()
        
        animation = QtCore.QSequentialAnimationGroup()
        
        # 上升
        anim_up = QtCore.QPropertyAnimation(widget, b"pos")
        anim_up.setDuration(duration // 3)
        anim_up.setEndValue(original_pos - QtCore.QPoint(0, height))
        anim_up.setEasingCurve(QtCore.QEasingCurve.OutQuad)
        animation.addAnimation(anim_up)
        
        # 下降
        anim_down = QtCore.QPropertyAnimation(widget, b"pos")
        anim_down.setDuration(duration // 3)
        anim_down.setEndValue(original_pos)
        anim_down.setEasingCurve(QtCore.QEasingCurve.InQuad)
        animation.addAnimation(anim_down)
        
        # 小弹跳
        anim_small_up = QtCore.QPropertyAnimation(widget, b"pos")
        anim_small_up.setDuration(duration // 6)
        anim_small_up.setEndValue(original_pos - QtCore.QPoint(0, height // 3))
        animation.addAnimation(anim_small_up)
        
        anim_settle = QtCore.QPropertyAnimation(widget, b"pos")
        anim_settle.setDuration(duration // 6)
        anim_settle.setEndValue(original_pos)
        animation.addAnimation(anim_settle)
        
        animation.start(QtCore.QAbstractAnimation.DeleteWhenStopped)
        return animation
    
    @staticmethod
    def scale(widget, start_scale=0.8, end_scale=1.0, duration=300):
        """缩放动画 - 需要QGraphicsEffect支持"""
        # 注意：Qt的QWidget不直接支持scale属性
        # 这里提供一个简化版本，使用resize
        original_size = widget.size()
        start_size = QtCore.QSize(
            int(original_size.width() * start_scale),
            int(original_size.height() * start_scale)
        )
        
        animation = QtCore.QPropertyAnimation(widget, b"size")
        animation.setDuration(duration)
        animation.setStartValue(start_size)
        animation.setEndValue(original_size)
        animation.setEasingCurve(QtCore.QEasingCurve.OutBack)
        animation.start(QtCore.QAbstractAnimation.DeleteWhenStopped)
        return animation
    
    @staticmethod
    def pulse(widget, duration=1000, min_opacity=0.5, max_opacity=1.0):
        """脉冲动画 - 循环淡入淡出"""
        animation = QtCore.QPropertyAnimation(widget, b"windowOpacity")
        animation.setDuration(duration)
        animation.setStartValue(max_opacity)
        animation.setKeyValueAt(0.5, min_opacity)
        animation.setEndValue(max_opacity)
        animation.setLoopCount(-1)  # 无限循环
        animation.setEasingCurve(QtCore.QEasingCurve.InOutSine)
        animation.start(QtCore.QAbstractAnimation.DeleteWhenStopped)
        return animation


class LoadingSpinner(QtWidgets.QWidget):
    """加载旋转动画组件"""
    
    def __init__(self, parent=None, size=40, color="#667eea"):
        super().__init__(parent)
        self.size = size
        self.color = color
        self.angle = 0
        
        self.setFixedSize(size, size)
        
        # 旋转动画
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.rotate)
        
    def start(self):
        """开始旋转"""
        self.timer.start(50)  # 每50ms更新一次
        self.show()
    
    def stop(self):
        """停止旋转"""
        self.timer.stop()
        self.hide()
    
    def rotate(self):
        """旋转更新"""
        self.angle = (self.angle + 10) % 360
        self.update()
    
    def paintEvent(self, event):
        """绘制旋转圆环"""
        from PySide6.QtGui import QPainter, QPen, QColor
        from PySide6.QtCore import Qt
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 设置画笔
        pen = QPen(QColor(self.color))
        pen.setWidth(4)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        
        # 绘制圆弧
        rect = self.rect().adjusted(5, 5, -5, -5)
        painter.drawArc(rect, self.angle * 16, 120 * 16)


class ProgressiveLoader(QtWidgets.QWidget):
    """渐进式加载动画 - 显示加载进度"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.progress = 0
        self.setFixedHeight(4)
        
        # 进度动画
        self.animation = QtCore.QPropertyAnimation(self, b"progress")
        self.animation.setDuration(2000)
        self.animation.setStartValue(0)
        self.animation.setEndValue(100)
        self.animation.setEasingCurve(QtCore.QEasingCurve.InOutQuad)
    
    def get_progress(self):
        return self._progress
    
    def set_progress(self, value):
        self._progress = value
        self.update()
    
    progress = QtCore.Property(int, get_progress, set_progress)
    
    def start(self):
        """开始加载动画"""
        self.animation.start()
        self.show()
    
    def stop(self):
        """停止加载"""
        self.animation.stop()
        self.hide()
    
    def paintEvent(self, event):
        """绘制进度条"""
        from PySide6.QtGui import QPainter, QLinearGradient, QColor
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 创建渐变
        gradient = QLinearGradient(0, 0, self.width(), 0)
        gradient.setColorAt(0, QColor("#667eea"))
        gradient.setColorAt(1, QColor("#764ba2"))
        
        # 绘制进度
        width = int(self.width() * self.progress / 100)
        painter.fillRect(0, 0, width, self.height(), gradient)


class AnimatedButton(QtWidgets.QPushButton):
    """带动画效果的按钮"""
    
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setCursor(QtCore.Qt.PointingHandCursor)
        self._scale = 1.0
    
    def enterEvent(self, event):
        """鼠标进入 - 放大"""
        super().enterEvent(event)
        self.animate_scale(1.05, 150)
    
    def leaveEvent(self, event):
        """鼠标离开 - 恢复"""
        super().leaveEvent(event)
        self.animate_scale(1.0, 150)
    
    def animate_scale(self, target_scale, duration):
        """缩放动画"""
        # 简化版：通过调整字体大小模拟缩放
        current_font = self.font()
        base_size = 13
        target_size = int(base_size * target_scale)
        
        current_font.setPointSize(target_size)
        self.setFont(current_font)
