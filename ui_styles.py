# UI 样式常量，供 desktop_app.py 使用

DIALOG_STYLE = """
/* 更淡雅的整体背景，提升控件在白/浅色行上的对比度 */
QDialog { background-color: #f5f7fa; }
"""

BTN_PRIMARY_STYLE = """
QPushButton {
    background-color: #3498db;
    color: white;
    border: none;
    border-radius: 3px;
    padding: 6px 12px;
    font-weight: bold;
}
QPushButton:hover { background-color: #346edb; }
QPushButton:pressed { background-color: #3445db; }
"""

BTN_ACCENT_STYLE = """
QPushButton {
    background-color: #51cf66;
    color: white;
    border: none;
    border-radius: 3px;
    padding: 6px 8px;
    font-weight: bold;
    font-size: 10px;
}
QPushButton:hover { background-color: #37b24d; }
QPushButton:pressed { background-color: #2f8a3d; }
"""

INPUT_STYLE = """
QLineEdit {
    border: 1px solid #3498db;
    border-radius: 3px;
    padding: 6px;
    font-size: 11px;
    background-color: white;
    color: #333;
}
QLineEdit:focus { border: 2px solid #3445db; background-color: white; color: #333; }
"""

TABLE_HEADER_STYLE = """
QHeaderView::section {
    /* 调淡表头背景为淡雅浅蓝，文字用深蓝色以保持可读性 */
    background-color: #e9eef8;
    color: #3445db;
    font-weight: bold;
    padding: 6px;
    border: 1px solid #d7e0f4;
}
"""

TABLE_STYLE = """
/* 表格整体使用更柔和的底色，表项使用透明背景以呈现底色或交替行色 */
QTableWidget, QTableView {
    gridline-color: #e6ebf1;
    background-color: #f5f7fa;
    alternate-background-color: #f8fbff;
}
QTableWidget::item, QTableView::item { padding: 6px; border: 1px solid #eef3f7; background-color: transparent; color: #333; }
QTableWidget::item:selected, QTableView::item:selected { background-color: #3498db; color: white; }

# 更明显的复选框视觉差异：未选中为白底灰边，选中为实心绿色
/* 未选中：透明方形，带浅灰边； 选中：蓝色实心方形（无圆角） */
QTableWidget::indicator:unchecked, QTableView::indicator:unchecked {
    background-color: transparent;
    border: 2px solid #cfcfcf;
    width: 18px;
    height: 18px;
    margin: 2px;
    border-radius: 0px;
}

QTableWidget::indicator:checked, QTableView::indicator:checked {
    background-color: #3498db;
    border: 2px solid #3498db;
    width: 18px;
    height: 18px;
    margin: 2px;
    border-radius: 0px;
}
QScrollBar:vertical { background-color: #f0f0f0; width: 12px; margin: 0px; border: none; }
QScrollBar::handle:vertical { background-color: #3498db; min-height: 20px; border-radius: 6px; }
QScrollBar::handle:vertical:hover { background-color: #346edb; }
QScrollBar::handle:vertical:pressed { background-color: #3445db; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
QScrollBar:horizontal { background-color: #f0f0f0; height: 12px; margin: 0px; border: none; }
QScrollBar::handle:horizontal { background-color: #3498db; min-width: 20px; border-radius: 6px; }
QScrollBar::handle:horizontal:hover { background-color: #346edb; }
QScrollBar::handle:horizontal:pressed { background-color: #3445db; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0px; }
"""

CHECKBOX_STYLE = """
/* 使用内联 SVG 绘制方形指示器以便精确控制边框（白边）与填充 */
QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 0px;
}

/* 未选中：透明方形，但边框颜色加深以便区分 */
QCheckBox::indicator:unchecked {
    background: transparent;
    border: none;
    image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='18' height='18'><rect x='1' y='1' width='16' height='16' fill='none' stroke='%238a8f95' stroke-width='2'/></svg>");
}

/* 选中：蓝色实心方形，外有白色描边以增强对比 */
QCheckBox::indicator:checked {
    background: transparent;
    border: none;
    image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='18' height='18'><rect x='0.5' y='0.5' width='17' height='17' fill='%233498db' stroke='%23ffffff' stroke-width='2'/></svg>");
}

/* 表头复选框采用相同的图像样式以保持一致 */
QHeaderView QCheckBox::indicator { width: 18px; height: 18px; }
QHeaderView QCheckBox::indicator:unchecked { image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='18' height='18'><rect x='1' y='1' width='16' height='16' fill='none' stroke='%238a8f95' stroke-width='2'/></svg>"); }
QHeaderView QCheckBox::indicator:checked { image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='18' height='18'><rect x='0.5' y='0.5' width='17' height='17' fill='%233498db' stroke='%23ffffff' stroke-width='2'/></svg>"); }
"""
