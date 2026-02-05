# -*- coding: utf-8 -*-
"""
UI 样式定义模块 - 现代深色主题
深色模式，适合长时间使用，减少眼睛疲劳
"""

# ==================== 颜色定义 - 深色主题 ====================
# 主色调：科技蓝紫渐变
PRIMARY_COLOR = "#667eea"        # 主色（紫蓝）
PRIMARY_HOVER = "#5a67d8"        # 主色悬停
PRIMARY_PRESS = "#4c51bf"        # 主色按下
ACCENT_COLOR = "#48bb78"         # 强调色（绿）
ACCENT_HOVER = "#38a169"         # 强调色悬停

# 背景色系
BG_DARK = "#1a202c"              # 深色背景
BG_DARKER = "#171923"            # 更深背景
BG_CARD = "#2d3748"              # 卡片背景
BG_HOVER = "#4a5568"             # 悬停背景

# 边框和分隔线
BORDER_COLOR = "#4a5568"         # 边框色
BORDER_LIGHT = "#718096"         # 浅边框

# 文字色系
TEXT_PRIMARY = "#f7fafc"         # 主文字（白）
TEXT_SECONDARY = "#e2e8f0"       # 次要文字
TEXT_MUTED = "#a0aec0"           # 弱化文字
TEXT_DISABLED = "#718096"        # 禁用文字

# 状态色
SUCCESS_COLOR = "#48bb78"        # 成功（绿）
ERROR_COLOR = "#f56565"          # 错误（红）
WARNING_COLOR = "#ed8936"        # 警告（橙）
INFO_COLOR = "#4299e1"           # 信息（蓝）

# ==================== 按钮样式 ====================
BTN_PRIMARY_STYLE = f"""
    QPushButton {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {PRIMARY_COLOR}, stop:1 #764ba2);
        color: {TEXT_PRIMARY};
        border: none;
        border-radius: 8px;
        font-weight: 600;
        padding: 10px 24px;
        font-size: 13px;
        letter-spacing: 0.5px;
    }}
    QPushButton:hover {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {PRIMARY_HOVER}, stop:1 #6b3fa0);
        transform: translateY(-2px);
    }}
    QPushButton:pressed {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {PRIMARY_PRESS}, stop:1 #5a3589);
    }}
    QPushButton:disabled {{
        background: {BG_HOVER};
        color: {TEXT_DISABLED};
    }}
"""

BTN_SECONDARY_STYLE = f"""
    QPushButton {{
        background-color: transparent;
        color: {TEXT_SECONDARY};
        border: 2px solid {BORDER_COLOR};
        border-radius: 8px;
        font-weight: 500;
        padding: 10px 24px;
        font-size: 13px;
    }}
    QPushButton:hover {{
        background-color: {BG_HOVER};
        border-color: {BORDER_LIGHT};
        color: {TEXT_PRIMARY};
    }}
    QPushButton:pressed {{
        background-color: {BG_CARD};
    }}
"""

BTN_SUCCESS_STYLE = f"""
    QPushButton {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {ACCENT_COLOR}, stop:1 #38b2ac);
        color: {TEXT_PRIMARY};
        border: none;
        border-radius: 8px;
        font-weight: 600;
        padding: 10px 24px;
        font-size: 13px;
    }}
    QPushButton:hover {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {ACCENT_HOVER}, stop:1 #319795);
    }}
"""

# ==================== 输入框样式 ====================
INPUT_STYLE = f"""
    QLineEdit {{
        background-color: {BG_CARD};
        border: 2px solid {BORDER_COLOR};
        border-radius: 8px;
        padding: 12px 16px;
        font-size: 13px;
        color: {TEXT_PRIMARY};
        selection-background-color: {PRIMARY_COLOR};
    }}
    QLineEdit:focus {{
        border: 2px solid {PRIMARY_COLOR};
        background-color: {BG_HOVER};
    }}
    QLineEdit:hover {{
        border-color: {BORDER_LIGHT};
    }}
"""

SEARCH_STYLE = f"""
    QLineEdit {{
        background-color: {BG_CARD};
        border: 2px solid {PRIMARY_COLOR};
        border-radius: 10px;
        padding: 14px 20px;
        font-size: 14px;
        color: {TEXT_PRIMARY};
        selection-background-color: {PRIMARY_COLOR};
    }}
    QLineEdit:focus {{
        border: 2px solid {PRIMARY_HOVER};
        background-color: {BG_HOVER};
    }}
"""

# ==================== 表格样式 ====================
TABLE_STYLE = f"""
    QTableWidget {{
        background-color: {BG_CARD};
        gridline-color: {BORDER_COLOR};
        border: 1px solid {BORDER_COLOR};
        border-radius: 8px;
        color: {TEXT_PRIMARY};
    }}
    QTableWidget::item {{
        padding: 8px 12px;
        color: {TEXT_PRIMARY};
        background-color: transparent;
        border-bottom: 1px solid {BORDER_COLOR};
    }}
    QTableWidget::item:selected {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {PRIMARY_COLOR}, stop:1 #764ba2);
        color: {TEXT_PRIMARY};
    }}
    QTableWidget::item:hover {{
        background-color: {BG_HOVER};
    }}
    QTableWidget::item:alternate {{
        background-color: {BG_DARKER};
    }}
"""

TABLE_HEADER_STYLE = f"""
    QHeaderView::section {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 {BG_HOVER}, stop:1 {BG_CARD});
        color: {TEXT_PRIMARY};
        padding: 10px 12px;
        border: none;
        border-right: 1px solid {BORDER_COLOR};
        border-bottom: 2px solid {PRIMARY_COLOR};
        font-weight: 600;
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}
    QHeaderView::section:hover {{
        background-color: {BG_HOVER};
    }}
"""

# ==================== 对话框样式 ====================
DIALOG_STYLE = f"""
    QDialog {{
        background-color: {BG_DARK};
    }}
    QLabel {{
        color: {TEXT_PRIMARY};
    }}
"""

# ==================== 日志框样式 ====================
LOG_STYLE = f"""
    QTextEdit {{
        background-color: {BG_DARKER};
        color: {TEXT_SECONDARY};
        font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
        font-size: 11px;
        padding: 12px;
        border: 1px solid {BORDER_COLOR};
        border-radius: 8px;
        line-height: 1.6;
    }}
"""

# ==================== 进度条样式 ====================
PROGRESS_STYLE = f"""
    QProgressBar {{
        border: none;
        border-radius: 8px;
        text-align: center;
        background-color: {BG_CARD};
        color: {TEXT_PRIMARY};
        font-weight: 600;
        height: 24px;
    }}
    QProgressBar::chunk {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {PRIMARY_COLOR}, stop:1 #764ba2);
        border-radius: 7px;
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
        width: 20px;
        height: 20px;
        border-radius: 4px;
    }}
    QCheckBox::indicator:unchecked {{
        background-color: {BG_CARD};
        border: 2px solid {BORDER_COLOR};
    }}
    QCheckBox::indicator:unchecked:hover {{
        border-color: {PRIMARY_COLOR};
    }}
    QCheckBox::indicator:checked {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {PRIMARY_COLOR}, stop:1 #764ba2);
        border: 2px solid {PRIMARY_COLOR};
    }}
"""

# ==================== 主窗口样式 ====================
MAIN_WINDOW_STYLE = f"""
    QMainWindow {{
        background-color: {BG_DARK};
    }}
"""

# ==================== 标签页样式 ====================
TAB_STYLE = f"""
    QTabWidget::pane {{
        border: 1px solid {BORDER_COLOR};
        border-radius: 8px;
        background-color: {BG_CARD};
    }}
    QTabBar::tab {{
        background-color: {BG_CARD};
        border: 1px solid {BORDER_COLOR};
        padding: 12px 24px;
        margin-right: 4px;
        color: {TEXT_SECONDARY};
        border-top-left-radius: 8px;
        border-top-right-radius: 8px;
        font-weight: 500;
    }}
    QTabBar::tab:selected {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {PRIMARY_COLOR}, stop:1 #764ba2);
        color: {TEXT_PRIMARY};
        border: 1px solid {PRIMARY_COLOR};
        font-weight: 600;
    }}
    QTabBar::tab:hover {{
        background-color: {BG_HOVER};
        color: {TEXT_PRIMARY};
    }}
"""

# ==================== 分组框样式 ====================
BUTTON_GROUP_STYLE = f"""
    QGroupBox {{
        border: 2px solid {BORDER_COLOR};
        border-radius: 8px;
        margin-top: 12px;
        padding-top: 12px;
        color: {TEXT_PRIMARY};
        font-weight: 600;
        background-color: {BG_CARD};
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 12px;
        padding: 0 8px;
        color: {PRIMARY_COLOR};
        font-size: 13px;
    }}
"""

# ==================== 下拉框样式 ====================
COMBO_STYLE = f"""
    QComboBox {{
        background-color: {BG_CARD};
        border: 2px solid {BORDER_COLOR};
        border-radius: 8px;
        padding: 8px 12px;
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
        border-left: 5px solid transparent;
        border-right: 5px solid transparent;
        border-top: 6px solid {TEXT_SECONDARY};
    }}
    QComboBox QAbstractItemView {{
        background-color: {BG_CARD};
        border: 1px solid {BORDER_COLOR};
        selection-background-color: {PRIMARY_COLOR};
        color: {TEXT_PRIMARY};
    }}
"""

# ==================== 滚动条样式 ====================
SCROLLBAR_STYLE = f"""
    QScrollBar:vertical {{
        border: none;
        background: {BG_CARD};
        width: 12px;
        border-radius: 6px;
    }}
    QScrollBar::handle:vertical {{
        background: {BORDER_LIGHT};
        border-radius: 6px;
        min-height: 30px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {PRIMARY_COLOR};
    }}
    QScrollBar::sub-line:vertical, QScrollBar::add-line:vertical {{
        border: none;
        background: none;
    }}
    QScrollBar:horizontal {{
        border: none;
        background: {BG_CARD};
        height: 12px;
        border-radius: 6px;
    }}
    QScrollBar::handle:horizontal {{
        background: {BORDER_LIGHT};
        border-radius: 6px;
        min-width: 30px;
    }}
    QScrollBar::handle:horizontal:hover {{
        background: {PRIMARY_COLOR};
    }}
"""

# ==================== 工具提示样式 ====================
TOOLTIP_STYLE = f"""
    QToolTip {{
        background-color: {BG_DARKER};
        color: {TEXT_PRIMARY};
        border: 1px solid {PRIMARY_COLOR};
        border-radius: 6px;
        padding: 8px 12px;
        font-size: 12px;
    }}
"""

# ==================== 缓存复选框样式 ====================
CACHE_CHECKBOX_STYLE = CHECKBOX_STYLE
