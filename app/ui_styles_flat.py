# -*- coding: utf-8 -*-
"""
UI 样式定义模块 - 现代扁平化主题
清新简洁的扁平化设计，色彩明快
"""

# ==================== 颜色定义 - 扁平化主题 ====================
# 主色调：活力橙
PRIMARY_COLOR = "#ff6b6b"        # 主色（珊瑚红）
PRIMARY_HOVER = "#ee5a52"        # 主色悬停
PRIMARY_PRESS = "#d63031"        # 主色按下
ACCENT_COLOR = "#4ecdc4"         # 强调色（青绿）
ACCENT_HOVER = "#45b7af"         # 强调色悬停

# 背景色系
BG_COLOR = "#f8f9fa"             # 主背景（极浅灰）
BG_CARD = "#ffffff"              # 卡片背景（白）
BG_HOVER = "#e9ecef"             # 悬停背景
BG_ACTIVE = "#dee2e6"            # 激活背景

# 边框和分隔线
BORDER_COLOR = "#dee2e6"         # 边框色
BORDER_LIGHT = "#e9ecef"         # 浅边框

# 文字色系
TEXT_PRIMARY = "#2d3436"         # 主文字（深灰）
TEXT_SECONDARY = "#636e72"       # 次要文字
TEXT_MUTED = "#b2bec3"           # 弱化文字
TEXT_DISABLED = "#dfe6e9"        # 禁用文字

# 状态色
SUCCESS_COLOR = "#00b894"        # 成功（绿）
ERROR_COLOR = "#d63031"          # 错误（红）
WARNING_COLOR = "#fdcb6e"        # 警告（黄）
INFO_COLOR = "#74b9ff"           # 信息（蓝）

# ==================== 按钮样式 ====================
BTN_PRIMARY_STYLE = f"""
    QPushButton {{
        background-color: {PRIMARY_COLOR};
        color: white;
        border: none;
        border-radius: 12px;
        font-weight: 600;
        padding: 12px 28px;
        font-size: 13px;
        letter-spacing: 0.3px;
    }}
    QPushButton:hover {{
        background-color: {PRIMARY_HOVER};
        padding: 12px 30px;
    }}
    QPushButton:pressed {{
        background-color: {PRIMARY_PRESS};
    }}
    QPushButton:disabled {{
        background-color: {BG_HOVER};
        color: {TEXT_DISABLED};
    }}
"""

BTN_SECONDARY_STYLE = f"""
    QPushButton {{
        background-color: {BG_CARD};
        color: {TEXT_PRIMARY};
        border: 2px solid {BORDER_COLOR};
        border-radius: 12px;
        font-weight: 500;
        padding: 12px 28px;
        font-size: 13px;
    }}
    QPushButton:hover {{
        background-color: {BG_HOVER};
        border-color: {PRIMARY_COLOR};
        color: {PRIMARY_COLOR};
    }}
    QPushButton:pressed {{
        background-color: {BG_ACTIVE};
    }}
"""

BTN_SUCCESS_STYLE = f"""
    QPushButton {{
        background-color: {ACCENT_COLOR};
        color: white;
        border: none;
        border-radius: 12px;
        font-weight: 600;
        padding: 12px 28px;
        font-size: 13px;
    }}
    QPushButton:hover {{
        background-color: {ACCENT_HOVER};
    }}
"""

# ==================== 输入框样式 ====================
INPUT_STYLE = f"""
    QLineEdit {{
        background-color: {BG_CARD};
        border: 2px solid {BORDER_COLOR};
        border-radius: 10px;
        padding: 12px 16px;
        font-size: 13px;
        color: {TEXT_PRIMARY};
        selection-background-color: {PRIMARY_COLOR};
    }}
    QLineEdit:focus {{
        border: 2px solid {PRIMARY_COLOR};
        background-color: white;
    }}
    QLineEdit:hover {{
        border-color: {PRIMARY_HOVER};
    }}
"""

SEARCH_STYLE = f"""
    QLineEdit {{
        background-color: {BG_CARD};
        border: 3px solid {PRIMARY_COLOR};
        border-radius: 14px;
        padding: 14px 20px;
        font-size: 14px;
        color: {TEXT_PRIMARY};
        selection-background-color: {PRIMARY_COLOR};
    }}
    QLineEdit:focus {{
        border: 3px solid {PRIMARY_HOVER};
        background-color: white;
    }}
"""

# ==================== 表格样式 ====================
TABLE_STYLE = f"""
    QTableWidget {{
        background-color: {BG_CARD};
        gridline-color: {BORDER_LIGHT};
        border: 2px solid {BORDER_COLOR};
        border-radius: 12px;
        color: {TEXT_PRIMARY};
    }}
    QTableWidget::item {{
        padding: 10px 14px;
        color: {TEXT_PRIMARY};
        background-color: transparent;
        border-bottom: 1px solid {BORDER_LIGHT};
    }}
    QTableWidget::item:selected {{
        background-color: {PRIMARY_COLOR};
        color: white;
    }}
    QTableWidget::item:hover {{
        background-color: {BG_HOVER};
    }}
    QTableWidget::item:alternate {{
        background-color: {BG_COLOR};
    }}
"""

TABLE_HEADER_STYLE = f"""
    QHeaderView::section {{
        background-color: {BG_HOVER};
        color: {TEXT_PRIMARY};
        padding: 12px 14px;
        border: none;
        border-right: 1px solid {BORDER_COLOR};
        border-bottom: 3px solid {PRIMARY_COLOR};
        font-weight: 700;
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }}
    QHeaderView::section:hover {{
        background-color: {BG_ACTIVE};
    }}
"""

# ==================== 对话框样式 ====================
DIALOG_STYLE = f"""
    QDialog {{
        background-color: {BG_COLOR};
    }}
    QLabel {{
        color: {TEXT_PRIMARY};
    }}
"""

# ==================== 日志框样式 ====================
LOG_STYLE = f"""
    QTextEdit {{
        background-color: {BG_CARD};
        color: {TEXT_SECONDARY};
        font-family: 'Consolas', 'Monaco', monospace;
        font-size: 11px;
        padding: 12px;
        border: 2px solid {BORDER_COLOR};
        border-radius: 12px;
        line-height: 1.6;
    }}
"""

# ==================== 进度条样式 ====================
PROGRESS_STYLE = f"""
    QProgressBar {{
        border: none;
        border-radius: 10px;
        text-align: center;
        background-color: {BG_HOVER};
        color: {TEXT_PRIMARY};
        font-weight: 600;
        height: 20px;
    }}
    QProgressBar::chunk {{
        background-color: {PRIMARY_COLOR};
        border-radius: 9px;
    }}
"""

# ==================== 复选框样式 ====================
CHECKBOX_STYLE = f"""
    QCheckBox {{
        color: {TEXT_PRIMARY};
        spacing: 8px;
        font-size: 13px;
    }}
    QCheckBox::indicator {{
        width: 22px;
        height: 22px;
        border-radius: 6px;
    }}
    QCheckBox::indicator:unchecked {{
        background-color: {BG_CARD};
        border: 2px solid {BORDER_COLOR};
    }}
    QCheckBox::indicator:unchecked:hover {{
        border-color: {PRIMARY_COLOR};
        background-color: {BG_HOVER};
    }}
    QCheckBox::indicator:checked {{
        background-color: {PRIMARY_COLOR};
        border: 2px solid {PRIMARY_COLOR};
    }}
"""

# ==================== 主窗口样式 ====================
MAIN_WINDOW_STYLE = f"""
    QMainWindow {{
        background-color: {BG_COLOR};
    }}
"""

# ==================== 标签页样式 ====================
TAB_STYLE = f"""
    QTabWidget::pane {{
        border: 2px solid {BORDER_COLOR};
        border-radius: 12px;
        background-color: {BG_CARD};
    }}
    QTabBar::tab {{
        background-color: {BG_HOVER};
        border: none;
        padding: 12px 28px;
        margin-right: 6px;
        color: {TEXT_SECONDARY};
        border-top-left-radius: 12px;
        border-top-right-radius: 12px;
        font-weight: 500;
    }}
    QTabBar::tab:selected {{
        background-color: {PRIMARY_COLOR};
        color: white;
        font-weight: 700;
    }}
    QTabBar::tab:hover {{
        background-color: {PRIMARY_HOVER};
        color: white;
    }}
"""

# ==================== 分组框样式 ====================
BUTTON_GROUP_STYLE = f"""
    QGroupBox {{
        border: 2px solid {BORDER_COLOR};
        border-radius: 12px;
        margin-top: 14px;
        padding-top: 14px;
        color: {TEXT_PRIMARY};
        font-weight: 600;
        background-color: {BG_CARD};
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 16px;
        padding: 0 10px;
        color: {PRIMARY_COLOR};
        font-size: 14px;
        font-weight: 700;
    }}
"""

# ==================== 下拉框样式 ====================
COMBO_STYLE = f"""
    QComboBox {{
        background-color: {BG_CARD};
        border: 2px solid {BORDER_COLOR};
        border-radius: 10px;
        padding: 10px 14px;
        color: {TEXT_PRIMARY};
        font-size: 13px;
    }}
    QComboBox:hover {{
        border-color: {PRIMARY_COLOR};
    }}
    QComboBox::drop-down {{
        border: none;
        width: 30px;
    }}
    QComboBox::down-arrow {{
        image: none;
        border-left: 6px solid transparent;
        border-right: 6px solid transparent;
        border-top: 7px solid {TEXT_SECONDARY};
    }}
    QComboBox QAbstractItemView {{
        background-color: {BG_CARD};
        border: 2px solid {BORDER_COLOR};
        border-radius: 8px;
        selection-background-color: {PRIMARY_COLOR};
        color: {TEXT_PRIMARY};
    }}
"""

# ==================== 滚动条样式 ====================
SCROLLBAR_STYLE = f"""
    QScrollBar:vertical {{
        border: none;
        background: {BG_HOVER};
        width: 14px;
        border-radius: 7px;
    }}
    QScrollBar::handle:vertical {{
        background: {PRIMARY_COLOR};
        border-radius: 7px;
        min-height: 30px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {PRIMARY_HOVER};
    }}
    QScrollBar::sub-line:vertical, QScrollBar::add-line:vertical {{
        border: none;
        background: none;
    }}
"""

# ==================== 缓存复选框样式 ====================
CACHE_CHECKBOX_STYLE = CHECKBOX_STYLE
